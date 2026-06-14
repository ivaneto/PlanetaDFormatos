"""Página base reutilizable para herramientas de tipo
"selecciona archivo → procesa → guarda".

Centraliza el selector de archivo, el arrastrar-y-soltar, la validación, el
diálogo de guardado, la ejecución EN UN HILO (para no congelar la interfaz),
la barra de estado, el **procesamiento por lotes** opcional y el ofrecimiento
de visualizar el resultado.

Una subclase normalmente solo necesita declarar unos pocos atributos y
sobrescribir ``run``:

    class MiHerramienta(SimpleToolPage):
        title = "Mi Herramienta"
        accept_ext = (".pdf",)
        out_ext = ".pdf"

        def run(self, in_path, out_path):
            MiLogica.procesar(in_path, out_path)
"""
import os
import threading
from tkinter import filedialog
from app.gui.components import dialogs as messagebox

import customtkinter as ctk

from app.gui.pages.base_page import BasePage
from app.gui.theme import Theme


class SimpleToolPage(BasePage):
    # --- Configuración (sobrescribible por subclases) ---
    title = "Herramienta"
    description = ""
    select_text = "Seleccionar archivo"
    button_text = "Procesar"
    processing_text = "Procesando..."

    accept_ext = (".pdf",)                       # extensiones aceptadas (DnD/selección)
    in_filetypes = [("Archivos PDF", "*.pdf")]   # filtros del diálogo de apertura
    out_ext = ".pdf"                             # extensión por defecto de salida
    out_filetypes = [("Archivos PDF", "*.pdf")]  # filtros del diálogo de guardado

    offer_view = True                            # ofrecer abrir el resultado en el visor
    allow_batch = True                           # permitir procesar varios archivos
    success_msg = "¡Operación completada con éxito!"
    fail_msg = "No se pudo completar la operación."

    # ------------------------------------------------------------------
    def run(self, in_path, out_path):
        """Lógica de la herramienta. Sobrescribir en la subclase.

        Puede devolver ``False`` para indicar fallo controlado; cualquier
        otro valor (incluido ``None``) se considera éxito. Las excepciones se
        capturan y se muestran automáticamente.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    def create_widgets(self):
        self.selected_files = []   # lista de rutas (1 = modo simple)
        self.batch = ctk.BooleanVar(value=False)

        header = ctk.CTkLabel(self.content_frame, text=self.title,
                              font=(Theme.FONT_FAMILY, 24, "bold"), text_color=Theme.TEXT_MAIN)
        header.pack(pady=20)

        if self.description:
            ctk.CTkLabel(self.content_frame, text=self.description, wraplength=800,
                         font=(Theme.FONT_FAMILY, 14), text_color=Theme.TEXT_MUTED,
                         justify="center").pack(pady=(0, 15), padx=40)

        select_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        select_frame.pack(pady=10)

        self.file_label = ctk.CTkLabel(select_frame, text="Ningún archivo seleccionado", width=300,
                                       font=(Theme.FONT_FAMILY, 14), text_color=Theme.TEXT_MUTED)
        self.file_label.pack(side="left", padx=10)

        ctk.CTkButton(select_frame, text=self.select_text, command=self.select_file,
                      fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER,
                      font=(Theme.FONT_FAMILY, 14)).pack(side="left")

        if self.allow_batch:
            ctk.CTkCheckBox(self.content_frame, text="Procesar varios archivos (lote)",
                            variable=self.batch, command=self._on_batch_toggle,
                            fg_color=Theme.PRIMARY, text_color=Theme.TEXT_MAIN).pack(pady=(4, 0))

        self.action_btn = ctk.CTkButton(self.content_frame, text=self.button_text, command=self._start,
                                        fg_color=Theme.SUCCESS, hover_color=Theme.SUCCESS_HOVER,
                                        font=(Theme.FONT_FAMILY, 16, "bold"))
        self.action_btn.pack(pady=20)

        self.progress = ctk.CTkProgressBar(self.content_frame, width=320)
        self.progress.set(0)

        self.status_label = ctk.CTkLabel(self.content_frame, text="",
                                         font=(Theme.FONT_FAMILY, 13), text_color=Theme.TEXT_MAIN)
        self.status_label.pack(pady=10)

        self.enable_dnd()

    def _on_batch_toggle(self):
        # Al cambiar de modo se limpia la selección para evitar ambigüedad.
        self.selected_files = []
        self.file_label.configure(text="Ningún archivo seleccionado")

    # ------------------------------------------------------------------
    def handle_dropped_files(self, files):
        matched = [f for f in files if f.lower().endswith(self.accept_ext)]
        if not matched:
            return False
        if self.batch.get():
            self.selected_files = matched
        else:
            self.selected_files = [matched[0]]
        self._update_file_label()
        return True

    def select_file(self):
        if self.batch.get():
            names = filedialog.askopenfilenames(title=self.select_text, filetypes=self.in_filetypes)
            if names:
                self.selected_files = list(names)
        else:
            name = filedialog.askopenfilename(title=self.select_text, filetypes=self.in_filetypes)
            if name:
                self.selected_files = [name]
        self._update_file_label()

    def _update_file_label(self):
        n = len(self.selected_files)
        if n == 0:
            self.file_label.configure(text="Ningún archivo seleccionado")
        elif n == 1:
            self.file_label.configure(text=os.path.basename(self.selected_files[0]))
        else:
            self.file_label.configure(text=f"{n} archivos seleccionados")

    # ------------------------------------------------------------------
    def _start(self):
        valid = [f for f in self.selected_files if os.path.exists(f)]
        if not valid:
            messagebox.showwarning("Advertencia", "¡Selecciona un archivo válido primero!")
            return

        if self.batch.get() and len(valid) > 1:
            out_dir = filedialog.askdirectory(title="Carpeta de salida para los archivos procesados")
            if not out_dir:
                return
            jobs = [(f, os.path.join(out_dir, os.path.splitext(os.path.basename(f))[0] + self.out_ext))
                    for f in valid]
        else:
            output_path = filedialog.asksaveasfilename(defaultextension=self.out_ext,
                                                       filetypes=self.out_filetypes)
            if not output_path:
                return
            jobs = [(valid[0], output_path)]

        self.action_btn.configure(state="disabled", text=self.processing_text)
        self.progress.pack(pady=(0, 6))
        self.progress.set(0)
        self.status_label.configure(text="Procesando, por favor espere...")
        threading.Thread(target=self._work, args=(jobs,), daemon=True).start()

    def _work(self, jobs):
        total = len(jobs)
        ok_count = 0
        errors = []
        for i, (in_path, out_path) in enumerate(jobs):
            try:
                result = self.run(in_path, out_path)
                if result is not False:
                    ok_count += 1
                else:
                    errors.append(os.path.basename(in_path))
            except Exception as e:
                errors.append(f"{os.path.basename(in_path)}: {e}")
            self.ui(lambda v=(i + 1) / total: self.progress.set(v))
            self.ui(lambda i=i: self.status_label.configure(text=f"Procesando {i+1} / {total}..."))

        last_out = jobs[-1][1] if jobs else None
        self.ui(lambda: self._done(ok_count, total, errors, last_out))

    def _done(self, ok_count, total, errors, last_out):
        self.action_btn.configure(state="normal", text=self.button_text)
        self.progress.pack_forget()

        if ok_count == 0:
            self.status_label.configure(text="Ocurrió un error.")
            messagebox.showerror("Error", "\n".join(errors) if errors else self.fail_msg)
            return

        if total == 1:
            self.status_label.configure(text="✓ " + self.success_msg)
            if self.offer_view and self.out_ext == ".pdf" and last_out:
                if messagebox.askyesno("Éxito", f"{self.success_msg}\n¿Desea visualizar el resultado?"):
                    from app.gui.pages.visualization_page import VisualizationPage
                    self.controller.show_page(VisualizationPage)
                    self.controller.current_page.load_pdf(last_out)
            else:
                messagebox.showinfo("Éxito", self.success_msg)
        else:
            self.status_label.configure(text=f"✓ {ok_count}/{total} archivos procesados.")
            msg = f"Se procesaron {ok_count} de {total} archivos."
            if errors:
                msg += "\n\nCon errores:\n" + "\n".join(errors[:8])
            messagebox.showinfo("Lote completado", msg)

        self.selected_files = []
        self.file_label.configure(text="Ningún archivo seleccionado")

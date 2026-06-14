import customtkinter as ctk
from tkinter import filedialog
from app.gui.components import dialogs as messagebox
from app.gui.pages.base_page import BasePage
from app.core.pdf_ops import PDFOperations
import os
import threading

from app.gui.theme import Theme


def _human_size(num_bytes):
    for unit in ("B", "KB", "MB", "GB"):
        if num_bytes < 1024 or unit == "GB":
            return f"{num_bytes:.0f} {unit}" if unit == "B" else f"{num_bytes/1.0:.1f} {unit}"
        num_bytes /= 1024.0


class CompressPage(BasePage):
    def create_widgets(self):
        self.selected_file = None

        # Header
        header = ctk.CTkLabel(self.content_frame, text="Comprimir PDF", font=(Theme.FONT_FAMILY, 24, "bold"), text_color=Theme.TEXT_MAIN)
        header.pack(pady=20)

        # File Selection
        select_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        select_frame.pack(pady=10)

        self.file_label = ctk.CTkLabel(select_frame, text="Ningún archivo seleccionado", width=300, font=(Theme.FONT_FAMILY, 14), text_color=Theme.TEXT_MUTED)
        self.file_label.pack(side="left", padx=10)

        ctk.CTkButton(select_frame, text="Seleccionar PDF", command=self.select_file,
                      fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER, font=(Theme.FONT_FAMILY, 14)).pack(side="left")

        # Compression level
        level_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        level_frame.pack(pady=10)
        ctk.CTkLabel(level_frame, text="Nivel de compresión:", text_color=Theme.TEXT_MAIN).pack(side="left", padx=10)

        self.level_map = {
            "Máxima (menor tamaño)": "low",
            "Equilibrada": "medium",
            "Mínima (mejor calidad)": "high",
        }
        self.level_display = ctk.StringVar(value="Equilibrada")
        ctk.CTkComboBox(level_frame, values=list(self.level_map.keys()), variable=self.level_display,
                        fg_color=Theme.SURFACE, text_color=Theme.TEXT_MAIN, button_color=Theme.PRIMARY, width=240).pack(side="left", padx=10)

        # Compress Button
        self.btn_compress = ctk.CTkButton(self.content_frame, text="Comprimir PDF", command=self.compress_file,
                                          fg_color=Theme.SUCCESS, hover_color=Theme.SUCCESS_HOVER, font=(Theme.FONT_FAMILY, 16, "bold"))
        self.btn_compress.pack(pady=20)

        # Status / result
        self.status_label = ctk.CTkLabel(self.content_frame, text="", font=(Theme.FONT_FAMILY, 13), text_color=Theme.TEXT_MAIN)
        self.status_label.pack(pady=10)

        self.enable_dnd()

    def handle_dropped_files(self, files):
        for f in files:
            if f.lower().endswith('.pdf'):
                self.selected_file = f
                self.file_label.configure(text=os.path.basename(f))
                return True
        return False

    def select_file(self):
        filename = filedialog.askopenfilename(title="Seleccionar archivo PDF", filetypes=[("Archivos PDF", "*.pdf")])
        if filename:
            self.selected_file = filename
            self.file_label.configure(text=os.path.basename(filename))

    def compress_file(self):
        if not self.selected_file:
            messagebox.showwarning("Advertencia", "¡Ningún archivo seleccionado!")
            return

        output_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Archivos PDF", "*.pdf")]
        )
        if not output_path:
            return

        level = self.level_map.get(self.level_display.get(), "medium")
        self.btn_compress.configure(state="disabled", text="Comprimiendo...")
        self.status_label.configure(text="Procesando, por favor espere...")

        threading.Thread(target=self._compress_thread, args=(output_path, level), daemon=True).start()

    def _compress_thread(self, output_path, level):
        try:
            orig, new = PDFOperations.compress_pdf(self.selected_file, output_path, level=level)
            self.ui(lambda: self._done(True, orig=orig, new=new))
        except Exception as e:
            msg = str(e)
            self.ui(lambda: self._done(False, error=msg))

    def _done(self, success, orig=0, new=0, error=None):
        self.btn_compress.configure(state="normal", text="Comprimir PDF")
        if success:
            reduction = (1 - new / orig) * 100 if orig else 0
            self.status_label.configure(
                text=f"✓ {_human_size(orig)} → {_human_size(new)}  ({reduction:.0f}% menos)"
            )
            messagebox.showinfo("Éxito", "¡PDF comprimido con éxito!")
            self.selected_file = None
            self.file_label.configure(text="Ningún archivo seleccionado")
        else:
            self.status_label.configure(text="Ocurrió un error.")
            messagebox.showerror("Error", f"Ocurrió un error: {error}")

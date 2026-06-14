import customtkinter as ctk
from tkinter import filedialog
from app.gui.components import dialogs as messagebox
from app.gui.pages.base_page import BasePage
from app.core.pdf_ops import PDFOperations
import os

from app.gui.theme import Theme


class PageNumbersPage(BasePage):
    def create_widgets(self):
        self.selected_file = None

        # Header
        header = ctk.CTkLabel(self.content_frame, text="Añadir Números de Página", font=(Theme.FONT_FAMILY, 24, "bold"), text_color=Theme.TEXT_MAIN)
        header.pack(pady=20)

        # File Selection
        select_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        select_frame.pack(pady=10)

        self.file_label = ctk.CTkLabel(select_frame, text="Ningún archivo seleccionado", width=300, font=(Theme.FONT_FAMILY, 14), text_color=Theme.TEXT_MUTED)
        self.file_label.pack(side="left", padx=10)

        ctk.CTkButton(select_frame, text="Seleccionar PDF", command=self.select_file,
                      fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER, font=(Theme.FONT_FAMILY, 14)).pack(side="left")

        # Options card
        opts = ctk.CTkFrame(self.content_frame, fg_color=Theme.SURFACE, corner_radius=12)
        opts.pack(pady=15, padx=40, fill="x")

        # Position
        pos_frame = ctk.CTkFrame(opts, fg_color="transparent")
        pos_frame.pack(pady=(15, 5), padx=20, fill="x")
        ctk.CTkLabel(pos_frame, text="Posición:", width=120, anchor="w", text_color=Theme.TEXT_MAIN).pack(side="left")
        self.pos_map = {
            "Inferior Derecha": "bottom-right",
            "Inferior Centro": "bottom-center",
            "Inferior Izquierda": "bottom-left",
            "Superior Derecha": "top-right",
            "Superior Centro": "top-center",
            "Superior Izquierda": "top-left",
        }
        self.display_pos = ctk.StringVar(value="Inferior Derecha")
        ctk.CTkComboBox(pos_frame, values=list(self.pos_map.keys()), variable=self.display_pos,
                        fg_color=Theme.SURFACE_2, text_color=Theme.TEXT_MAIN, button_color=Theme.PRIMARY, width=200).pack(side="left", padx=10)

        # Format
        fmt_frame = ctk.CTkFrame(opts, fg_color="transparent")
        fmt_frame.pack(pady=5, padx=20, fill="x")
        ctk.CTkLabel(fmt_frame, text="Formato:", width=120, anchor="w", text_color=Theme.TEXT_MAIN).pack(side="left")
        self.fmt_map = {
            "1, 2, 3...": "{n}",
            "Página 1": "Página {n}",
            "1 de N": "{n} de {total}",
            "- 1 -": "- {n} -",
        }
        self.display_fmt = ctk.StringVar(value="1, 2, 3...")
        ctk.CTkComboBox(fmt_frame, values=list(self.fmt_map.keys()), variable=self.display_fmt,
                        fg_color=Theme.SURFACE_2, text_color=Theme.TEXT_MAIN, button_color=Theme.PRIMARY, width=200).pack(side="left", padx=10)

        # Skip first
        self.skip_first = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(opts, text="No numerar la primera página (portada)", variable=self.skip_first,
                        fg_color=Theme.PRIMARY, text_color=Theme.TEXT_MAIN).pack(pady=(5, 15), padx=20, anchor="w")

        # Action Buttons (Preview + Apply)
        btn_row = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        btn_row.pack(pady=20)
        ctk.CTkButton(btn_row, text="👁 Vista previa", command=self.preview_numbers,
                      fg_color="transparent", border_width=1, border_color=Theme.PRIMARY,
                      text_color=Theme.PRIMARY, hover_color=Theme.ACCENT_SOFT,
                      font=(Theme.FONT_FAMILY, 14)).pack(side="left", padx=8)
        ctk.CTkButton(btn_row, text="Añadir Número de Página", command=self.apply_numbers,
                      fg_color=Theme.SUCCESS, hover_color=Theme.SUCCESS_HOVER, font=(Theme.FONT_FAMILY, 16, "bold")).pack(side="left", padx=8)

        self.enable_dnd()

    def preview_numbers(self):
        if not self.selected_file:
            messagebox.showwarning("Advertencia", "¡Ningún archivo seleccionado!")
            return
        import tempfile, os
        tmp = os.path.join(tempfile.gettempdir(), "preview_page_numbers.pdf")
        try:
            internal_pos = self.pos_map.get(self.display_pos.get(), "bottom-right")
            fmt = self.fmt_map.get(self.display_fmt.get(), "{n}")
            PDFOperations.add_page_numbers(
                self.selected_file, tmp, position=internal_pos,
                fmt=fmt, skip_first=self.skip_first.get()
            )
            from app.gui.pages.visualization_page import VisualizationPage
            self.controller.show_page(VisualizationPage)
            self.controller.current_page.load_pdf(tmp)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar la vista previa: {e}")

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

    def apply_numbers(self):
        if not self.selected_file:
            messagebox.showwarning("Advertencia", "¡Ningún archivo seleccionado!")
            return

        output_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Archivos PDF", "*.pdf")]
        )
        if not output_path:
            return

        try:
            internal_pos = self.pos_map.get(self.display_pos.get(), "bottom-right")
            fmt = self.fmt_map.get(self.display_fmt.get(), "{n}")
            PDFOperations.add_page_numbers(
                self.selected_file, output_path, position=internal_pos,
                fmt=fmt, skip_first=self.skip_first.get()
            )

            if messagebox.askyesno("Éxito", "Números de página añadidos. ¿Desea visualizar el PDF?"):
                from app.gui.pages.visualization_page import VisualizationPage
                self.controller.show_page(VisualizationPage)
                self.controller.current_page.load_pdf(output_path)

            self.selected_file = None
            self.file_label.configure(text="Ningún archivo seleccionado")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error: {str(e)}")

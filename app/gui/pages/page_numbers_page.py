import customtkinter as ctk
from tkinter import filedialog, messagebox
from app.gui.pages.base_page import BasePage
from app.core.pdf_ops import PDFOperations
import os

from app.gui.theme import Theme

class PageNumbersPage(BasePage):
    def create_widgets(self):
        self.selected_file = None
        self.position = ctk.StringVar(value="bottom-right")
        
        # Header
        header = ctk.CTkLabel(self.content_frame, text="Añadir Números de Página", font=(Theme.FONT_FAMILY, 24, "bold"), text_color=Theme.TEXT_MAIN)
        header.pack(pady=20)
        
        # File Selection
        select_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        select_frame.pack(pady=10)
        
        self.file_label = ctk.CTkLabel(select_frame, text="Ningún archivo seleccionado", width=300, font=(Theme.FONT_FAMILY, 14), text_color="gray")
        self.file_label.pack(side="left", padx=10)
        
        ctk.CTkButton(select_frame, text="Seleccionar PDF", command=self.select_file,
                      fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER, font=(Theme.FONT_FAMILY, 14)).pack(side="left")
        
        # Position Selection
        pos_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        pos_frame.pack(pady=10)
        ctk.CTkLabel(pos_frame, text="Posición:", text_color=Theme.TEXT_MAIN).pack(side="left", padx=10)
        
        self.pos_map = {
            "Inferior Derecha": "bottom-right",
            "Inferior Centro": "bottom-center",
            "Inferior Izquierda": "bottom-left"
        }
        self.display_pos = ctk.StringVar(value="Inferior Derecha")
        
        ctk.CTkComboBox(pos_frame, values=list(self.pos_map.keys()), variable=self.display_pos,
                        fg_color="white", text_color=Theme.TEXT_MAIN, button_color=Theme.PRIMARY).pack(side="left", padx=10)
        
        # Apply Button
        ctk.CTkButton(self.content_frame, text="Añadir Número de Página", command=self.apply_numbers, 
                      fg_color="#2CC985", hover_color="#0C955A", font=(Theme.FONT_FAMILY, 16, "bold")).pack(pady=20)
        
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
            
    def apply_numbers(self):
        if not self.selected_file:
            messagebox.showwarning("Advertencia", "¡Ningún archivo seleccionado!")
            return
            
        output_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Archivos PDF", "*.pdf")]
        )
        
        if output_path:
            try:
                internal_pos = self.pos_map.get(self.display_pos.get(), "bottom-right")
                PDFOperations.add_page_numbers(self.selected_file, output_path, internal_pos)
                
                if messagebox.askyesno("Éxito", "Números de página añadidos. ¿Desea visualizar el PDF?"):
                    from app.gui.pages.visualization_page import VisualizationPage
                    self.controller.show_page(VisualizationPage)
                    self.controller.current_page.load_pdf(output_path)
                
                self.selected_file = None
                self.file_label.configure(text="Ningún archivo seleccionado")
            except Exception as e:
                messagebox.showerror("Error", f"Ocurrió un error: {str(e)}")

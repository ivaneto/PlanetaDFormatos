"""
Word a PDF
Codigo simple
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
from app.gui.pages.base_page import BasePage
from app.core.converters import Converter
import os

from app.gui.theme import Theme

class Word2PdfPage(BasePage):
    def create_widgets(self):
        self.selected_file = None
        
        # Encabezado
        header = ctk.CTkLabel(self.content_frame, text="Word a PDF", font=(Theme.FONT_FAMILY, 24, "bold"), text_color=Theme.TEXT_MAIN)
        header.pack(pady=20)
        
        # Selección de archivo
        select_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        select_frame.pack(pady=10)
        
        self.file_label = ctk.CTkLabel(select_frame, text="Ningún archivo seleccionado", width=300, font=(Theme.FONT_FAMILY, 14), text_color="gray")
        self.file_label.pack(side="left", padx=10)
        
        ctk.CTkButton(select_frame, text="Seleccionar archivo Word", command=self.select_file,
                      fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER, font=(Theme.FONT_FAMILY, 14)).pack(side="left")
        
        # Botón de conversión
        ctk.CTkButton(self.content_frame, text="Convertir a PDF", command=self.convert_file, 
                      fg_color="#2CC985", hover_color="#0C955A", font=(Theme.FONT_FAMILY, 16, "bold")).pack(pady=20)
        
        self.enable_dnd()

    def handle_dropped_files(self, files):
        for f in files:
            if f.lower().endswith(('.docx', '.doc')):
                self.selected_file = f
                self.file_label.configure(text=os.path.basename(f))
                return True
        return False
        
    def select_file(self):
        filename = filedialog.askopenfilename(
            title="Seleccionar archivo Word",
            filetypes=[("Archivos Word", "*.docx *.doc")]
        )
        if filename:
            self.selected_file = filename
            self.file_label.configure(text=os.path.basename(filename))
            
    def convert_file(self):
        if not self.selected_file:
            messagebox.showwarning("Advertencia", "¡Ningún archivo seleccionado!")
            return
            
        output_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Archivos PDF", "*.pdf")]
        )
        
        if output_path:
            try:
                Converter.word_to_pdf(self.selected_file, output_path)
                messagebox.showinfo("Éxito", "¡PDF creado con éxito!")
                self.selected_file = None
                self.file_label.configure(text="Ningún archivo seleccionado")
            except Exception as e:
                messagebox.showerror("Error", f"Ocurrió un error: {str(e)}")

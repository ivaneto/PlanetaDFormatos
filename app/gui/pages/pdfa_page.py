import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from app.gui.pages.base_page import BasePage
from app.core.pdf_editor import PDFEditorBackend
from app.gui.theme import Theme
import os

class PdfaPage(BasePage):
    def create_widgets(self):
        self.backend = PDFEditorBackend()
        self.full_input_path = ""
        self.input_pdf = tk.StringVar()

        # Encabezado
        header = ctk.CTkLabel(self.content_frame, text="Convertir a PDF/A", font=(Theme.FONT_FAMILY, 24, "bold"), text_color=Theme.TEXT_MAIN)
        header.pack(pady=20)
        
        # Descripción
        desc_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        desc_frame.pack(fill="x", padx=40, pady=10)
        desc_lbl = ctk.CTkLabel(desc_frame, text="Optimiza el archivo para la preservación a largo plazo (Estándar de Archivo).\nIncrusta fuentes, elimina cifrado y agrega metadatos de compatibilidad.",
                                font=(Theme.FONT_FAMILY, 14), text_color=Theme.TEXT_MAIN, wraplength=800)
        desc_lbl.pack()

        # Marco de Contenido Principal
        content_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Selección de PDF de Entrada
        input_frame = ctk.CTkFrame(content_frame, fg_color="white", corner_radius=10)
        input_frame.pack(fill="x", pady=20, padx=20)
        
        ctk.CTkLabel(input_frame, text="PDF de Entrada:", font=(Theme.FONT_FAMILY, 14, "bold"), text_color=Theme.TEXT_MAIN).pack(side="left", padx=20, pady=20)
        
        self.file_label = ctk.CTkLabel(input_frame, text="Ningún archivo seleccionado", width=300, font=(Theme.FONT_FAMILY, 14), text_color="gray")
        self.file_label.pack(side="left", padx=10, fill="x", expand=True)

        ctk.CTkButton(input_frame, text="Explorar...", command=self.browse_pdf, width=120, height=40,
                      fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER, font=(Theme.FONT_FAMILY, 14, "bold")).pack(side="left", padx=20, pady=20)

        # Botón de Acción
        ctk.CTkButton(self.content_frame, text="Convertir a PDF/A", command=self.convert_pdfa, 
                      fg_color=Theme.SUCCESS, hover_color="#0C955A", font=(Theme.FONT_FAMILY, 18, "bold"), width=250, height=50).pack(pady=40)
        
        self.enable_dnd()

    def handle_dropped_files(self, files):
        for f in files:
            if f.lower().endswith('.pdf'):
                self.full_input_path = f
                self.file_label.configure(text=os.path.basename(f), text_color=Theme.TEXT_MAIN)
                return True
        return False

    def browse_pdf(self):
        filename = filedialog.askopenfilename(filetypes=[("Archivos PDF", "*.pdf")])
        if filename:
            self.full_input_path = filename
            self.file_label.configure(text=os.path.basename(filename), text_color=Theme.TEXT_MAIN)

    def convert_pdfa(self):
        input_path = self.full_input_path
        if not input_path or not os.path.exists(input_path):
            messagebox.showwarning("Advertencia", "Por favor seleccione un archivo PDF válido.")
            return

        output_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("Archivos PDF", "*.pdf")])
        if not output_path:
            return
            
        try:
           success = self.backend.convert_to_pdfa(input_path, output_path)
           if success:
               messagebox.showinfo("Éxito", "El PDF ha sido convertido a formato de archivo (PDF/A).")
               self.full_input_path = ""
               self.file_label.configure(text="Ningún archivo seleccionado", text_color="gray")
           else:
               messagebox.showerror("Error", "Ocurrió un error en la conversión.")
               
        except Exception as e:
            messagebox.showerror("Error", f"Error inesperado: {str(e)}")

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
from app.gui.components import dialogs as messagebox
from app.gui.pages.base_page import BasePage
from app.core.pdf_editor import PDFEditorBackend
from app.gui.theme import Theme
import os

class MetadataPage(BasePage):
    def create_widgets(self):
        self.backend = PDFEditorBackend()
        self.full_input_path = ""
        self.input_pdf = tk.StringVar()
        
        # Variables de Metadatos
        self.title_var = tk.StringVar()
        self.author_var = tk.StringVar()
        self.subject_var = tk.StringVar()
        self.keywords_var = tk.StringVar()
        self.creator_var = tk.StringVar()
        self.producer_var = tk.StringVar()
        self.created_var = tk.StringVar()
        self.modified_var = tk.StringVar()

        # Encabezado
        header = ctk.CTkLabel(self.content_frame, text="Editar Metadatos", font=(Theme.FONT_FAMILY, 24, "bold"), text_color=Theme.TEXT_MAIN)
        header.pack(pady=20)
        
        # Descripción
        desc_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        desc_frame.pack(fill="x", padx=40, pady=10)
        desc_lbl = ctk.CTkLabel(desc_frame, text="Visualiza y edita la información oculta de tu archivo PDF (Título, Autor, Asunto, etc.).",
                                font=(Theme.FONT_FAMILY, 14), text_color=Theme.TEXT_MAIN)
        desc_lbl.pack()

        # Contenido Principal Desplazable
        content_frame = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Selección de PDF de Entrada
        input_frame = ctk.CTkFrame(content_frame, fg_color=Theme.SURFACE, corner_radius=10)
        input_frame.pack(fill="x", pady=10, padx=20)
        
        ctk.CTkLabel(input_frame, text="PDF de Entrada:", font=(Theme.FONT_FAMILY, 14, "bold"), text_color=Theme.TEXT_MAIN).pack(side="left", padx=20, pady=20)
        
        self.file_label = ctk.CTkLabel(input_frame, text="Ningún archivo seleccionado", width=300, font=(Theme.FONT_FAMILY, 14), text_color=Theme.TEXT_MUTED)
        self.file_label.pack(side="left", padx=10, fill="x", expand=True)

        ctk.CTkButton(input_frame, text="Explorar...", command=self.browse_pdf, width=100,
                      fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER).pack(side="left", padx=20, pady=20)

        # Sección del Formulario
        form_frame = ctk.CTkFrame(content_frame, fg_color=Theme.SURFACE, corner_radius=10)
        form_frame.pack(fill="x", pady=10, padx=20)
        
        ctk.CTkLabel(form_frame, text="Información del Documento", font=(Theme.FONT_FAMILY, 16, "bold"), text_color=Theme.TEXT_MAIN).pack(pady=10, padx=20, anchor="w")
        
        self.create_entry(form_frame, "Título:", self.title_var)
        self.create_entry(form_frame, "Autor:", self.author_var)
        self.create_entry(form_frame, "Asunto:", self.subject_var)
        self.create_entry(form_frame, "Palabras Clave:", self.keywords_var)
        self.create_entry(form_frame, "Aplicación (Creator):", self.creator_var)
        self.create_entry(form_frame, "Productor PDF:", self.producer_var)
        self.create_entry(form_frame, "Fecha Creación:", self.created_var)
        self.create_entry(form_frame, "Fecha Modificación:", self.modified_var)
        
        ctk.CTkLabel(form_frame, text="* Las fechas deben seguir el formato PDF estándar si se editan manualmente (D:YYYYMMDD...).", 
                     font=(Theme.FONT_FAMILY, 12, "italic"), text_color=Theme.TEXT_MUTED).pack(pady=10, padx=20, anchor="w")

        # Botón de Acción
        ctk.CTkButton(self.content_frame, text="Guardar Metadatos", command=self.save_metadata, 
                      fg_color=Theme.SUCCESS, hover_color=Theme.SUCCESS_HOVER, font=(Theme.FONT_FAMILY, 18, "bold"), width=250, height=50).pack(pady=20)
        
        self.enable_dnd()

    def create_entry(self, parent, label_text, variable):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(row, text=label_text, width=150, anchor="w", text_color=Theme.TEXT_MAIN).pack(side="left")
        ctk.CTkEntry(row, textvariable=variable, width=400).pack(side="left", fill="x", expand=True)

    def handle_dropped_files(self, files):
        for f in files:
            if f.lower().endswith('.pdf'):
                self.load_pdf(f)
                return True
        return False

    def browse_pdf(self):
        filename = filedialog.askopenfilename(filetypes=[("Archivos PDF", "*.pdf")])
        if filename:
            self.load_pdf(filename)
            
    def load_pdf(self, path):
        self.full_input_path = path
        self.file_label.configure(text=os.path.basename(path), text_color=Theme.TEXT_MAIN)
        
        # Cargar metadatos
        meta = self.backend.get_metadata(path)
        if meta:
            self.title_var.set(meta.get('title') or '')
            self.author_var.set(meta.get('author') or '')
            self.subject_var.set(meta.get('subject') or '')
            self.keywords_var.set(meta.get('keywords') or '')
            self.creator_var.set(meta.get('creator') or '')
            self.producer_var.set(meta.get('producer') or '')
            self.created_var.set(meta.get('creationDate') or '')
            self.modified_var.set(meta.get('modDate') or '')
        else:
            self.clear_fields()

    def clear_fields(self):
        vars = [self.title_var, self.author_var, self.subject_var, self.keywords_var, 
                self.creator_var, self.producer_var, self.created_var, self.modified_var]
        for v in vars: v.set("")

    def save_metadata(self):
        input_path = self.full_input_path
        if not input_path or not os.path.exists(input_path):
            messagebox.showwarning("Advertencia", "Por favor cargue un archivo PDF primero.")
            return

        output_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("Archivos PDF", "*.pdf")])
        if not output_path:
            return
            
        metadata = {
            'title': self.title_var.get(),
            'author': self.author_var.get(),
            'subject': self.subject_var.get(),
            'keywords': self.keywords_var.get(),
            'creator': self.creator_var.get(),
            'producer': self.producer_var.get(),
            'creationDate': self.created_var.get(),
            'modDate': self.modified_var.get()
        }
            
        try:
           success = self.backend.save_metadata(input_path, output_path, metadata)
           if success:
               messagebox.showinfo("Éxito", "Los metadatos se han actualizado exitosamente.")
               self.full_input_path = ""
               self.file_label.configure(text="Ningún archivo seleccionado", text_color=Theme.TEXT_MUTED)
               self.clear_fields()
           else:
               messagebox.showerror("Error", "Ocurrió un error al guardar los metadatos.")
               
        except Exception as e:
            messagebox.showerror("Error", f"Error inesperado: {str(e)}")

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from app.gui.pages.base_page import BasePage
from app.core.converters import Converter
import os
from app.gui.components.file_list_frame import FileListFrame

from app.gui.theme import Theme

class Img2PdfPage(BasePage):
    def create_widgets(self):
        self.content_frame.grid_columnconfigure(0, weight=0)
        self.content_frame.grid_columnconfigure(1, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        # Panel de control
        self.controls_frame = ctk.CTkFrame(self.content_frame, width=280, corner_radius=15, fg_color="white")
        self.controls_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.controls_frame.grid_propagate(False)
        
        self.file_list = FileListFrame(self.content_frame, title="Imágenes Seleccionadas")
        self.file_list.grid(row=0, column=1, sticky="nsew", padx=(0, 20), pady=20)
        
        # --- Contenido de los controles ---
        
        # Título
        ctk.CTkLabel(self.controls_frame, text="Opciones de Imagen", 
                     font=(Theme.FONT_FAMILY, 20, "bold"), text_color=Theme.TEXT_MAIN).pack(pady=(30, 20), padx=20, anchor="w")
        
        self.btn_add = ctk.CTkButton(self.controls_frame, text="+ Añadir Imágenes", command=self.add_images, 
                                   height=50, font=(Theme.FONT_FAMILY, 15, "bold"),
                                   fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER)
        self.btn_add.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkFrame(self.controls_frame, height=2, fg_color=("gray80", "gray30")).pack(pady=20, padx=20, fill="x")
        
        # Info
        info_label = ctk.CTkLabel(self.controls_frame, text="Selecciona imágenes (JPG, PNG) para convertirlas en un solo archivo PDF. Puedes arrastrarlas dentro del campo para cambiar el orden de las imágenes.",
                                text_color="gray", wraplength=240, justify="left", font=(Theme.FONT_FAMILY, 12))
        info_label.pack(pady=10, padx=20, anchor="w")
        
        ctk.CTkLabel(self.controls_frame, text="").pack(fill="y", expand=True)
        
        # Boton para limpiar la lista
        self.btn_clear = ctk.CTkButton(self.controls_frame, text="Limpiar Lista", command=self.clear_images, 
                                     fg_color="transparent", border_width=2, border_color="gray", text_color="gray", 
                                     height=40, hover_color="#EEEEEE")
        self.btn_clear.pack(pady=10, padx=20, fill="x")
        
        # Boton para convertir
        self.btn_convert = ctk.CTkButton(self.controls_frame, text="Convertir a PDF", command=self.convert_images, 
                                     fg_color="#2CC985", hover_color="#0C955A", text_color="white",
                                     height=60, font=(Theme.FONT_FAMILY, 18, "bold"))
        self.btn_convert.pack(pady=(10, 30), padx=20, fill="x")
        
        self.enable_dnd()

    def handle_dropped_files(self, files):
        handled = False
        for f in files:
            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                self.file_list.add_file(f)
                handled = True
        return handled

    def add_images(self):
        filenames = filedialog.askopenfilenames(
            title="Seleccionar Imágenes",
            filetypes=[("Imágenes", "*.jpg *.jpeg *.png *.bmp")]
        )
        for f in filenames:
            self.file_list.add_file(f)

    def clear_images(self):
        self.file_list.clear_files()
        
    def convert_images(self):
        files = self.file_list.get_files()
        if not files:
            messagebox.showwarning("Advertencia", "¡Ninguna imagen seleccionada!")
            return
            
        output_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Archivos PDF", "*.pdf")]
        )
        
        if output_path:
            try:
                Converter.images_to_pdf(files, output_path)
                
                if messagebox.askyesno("Éxito", "PDF creado con éxito. ¿Desea visualizarlo?"):
                    from app.gui.pages.visualization_page import VisualizationPage
                    self.controller.show_page(VisualizationPage)
                    self.controller.current_page.load_pdf(output_path)
                
                self.clear_images()
            except Exception as e:
                messagebox.showerror("Error", f"Ocurrió un error: {str(e)}")

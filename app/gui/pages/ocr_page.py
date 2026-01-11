import customtkinter as ctk
from tkinter import filedialog, messagebox
from app.gui.pages.base_page import BasePage
from app.core.converters import Converter
import os
import threading

from app.gui.theme import Theme

class OCRPage(BasePage):
    def create_widgets(self):
        self.selected_file = None
        
        # Encabezado
        header = ctk.CTkLabel(self.content_frame, text="OCR (Reconocimiento Óptico de Caracteres)", font=(Theme.FONT_FAMILY, 24, "bold"), text_color=Theme.TEXT_MAIN)
        header.pack(pady=20)
        
        description = ctk.CTkLabel(self.content_frame, text="Convierte PDFs escaneados en archivos PDF con texto buscable.", font=(Theme.FONT_FAMILY, 14), text_color="gray")
        description.pack(pady=(0, 20))
        
        # Selección de archivo
        select_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        select_frame.pack(pady=10)
        
        self.file_label = ctk.CTkLabel(select_frame, text="Ningún archivo seleccionado", width=300, font=(Theme.FONT_FAMILY, 14), text_color="gray")
        self.file_label.pack(side="left", padx=10)
        
        ctk.CTkButton(select_frame, text="Seleccionar PDF Escaneado", command=self.select_file,
                      fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER, font=(Theme.FONT_FAMILY, 14)).pack(side="left")
        
        # Opciones (Idioma) - Entrada simple por ahora
        options_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        options_frame.pack(pady=10)
        
        ctk.CTkLabel(options_frame, text="Idiomas (ej. 'eng', 'spa', 'eng+spa'):", font=(Theme.FONT_FAMILY, 14)).pack(side="left", padx=10)
        self.lang_entry = ctk.CTkEntry(options_frame, width=150)
        self.lang_entry.pack(side="left")
        self.lang_entry.insert(0, "spa+eng")
        
        # Botón de conversión
        self.btn_convert = ctk.CTkButton(self.content_frame, text="Iniciar OCR", command=self.start_conversion, 
                      fg_color="#2CC985", hover_color="#0C955A", font=(Theme.FONT_FAMILY, 16, "bold"))
        self.btn_convert.pack(pady=20)
        
        # Etiqueta de estado
        self.status_label = ctk.CTkLabel(self.content_frame, text="", font=(Theme.FONT_FAMILY, 12), text_color=Theme.TEXT_MAIN)
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
        filename = filedialog.askopenfilename(
            title="Seleccionar archivo PDF",
            filetypes=[("Archivos PDF", "*.pdf")]
        )
        if filename:
            self.selected_file = filename
            self.file_label.configure(text=os.path.basename(filename))

    def start_conversion(self):
        if not self.selected_file:
            messagebox.showwarning("Advertencia", "¡Ningún archivo seleccionado!")
            return
            
        output_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Archivos PDF", "*.pdf")]
        )
        
        if output_path:
            # Ejecutar en un hilo separado para no congelar la IU
            self.btn_convert.configure(state="disabled", text="Procesando...")
            self.status_label.configure(text="Procesando... Esto puede tardar un poco dependiendo del tamaño del archivo.")
            
            lang_val = self.lang_entry.get()
            thread = threading.Thread(target=self.convert_file_thread, args=(output_path, lang_val))
            thread.daemon = True
            thread.start()

    def convert_file_thread(self, output_path, lang):
        try:
            # lang se pasa como argumento
            Converter.apply_ocr(self.selected_file, output_path, lang=lang)
            self.after(0, lambda: self.conversion_complete(True, output_path=output_path))
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            print(f"Error OCR: {tb}") # Imprimir en la consola para depuración
            error_message = f"{type(e).__name__}: {str(e)}" # Capture the exception message
            self.after(0, lambda: self.conversion_complete(False, error_message))

    def conversion_complete(self, success, error_msg=None, output_path=None):
        self.btn_convert.configure(state="normal", text="Iniciar OCR")
        if success:
            self.status_label.configure(text="¡OCR Completado con Éxito!")
            
            if messagebox.askyesno("Éxito", "PDF con OCR creado. ¿Desea visualizarlo?"):
                from app.gui.pages.visualization_page import VisualizationPage
                self.controller.show_page(VisualizationPage)
                self.controller.current_page.load_pdf(output_path)
            
            self.selected_file = None
            self.file_label.configure(text="Ningún archivo seleccionado")
        else:
            self.status_label.configure(text="Ocurrió un error.")
            messagebox.showerror("Error", f"Ocurrió un error: {error_msg}")

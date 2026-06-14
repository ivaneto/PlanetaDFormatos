import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from app.gui.pages.base_page import BasePage
from app.core.pdf_ops import PDFManager

from app.gui.theme import Theme

class WatermarkPage(BasePage):
    def create_widgets(self):
        self.input_pdf = tk.StringVar()
        self.watermark_type = tk.StringVar(value="text")
        self.watermark_text = tk.StringVar()
        self.watermark_image = tk.StringVar()
        self.opacity = tk.DoubleVar(value=0.5)
        self.rotation = tk.StringVar(value="45")

        # Header
        header = ctk.CTkLabel(self.content_frame, text="Añadir Marca de Agua", font=(Theme.FONT_FAMILY, 24, "bold"), text_color=Theme.TEXT_MAIN)
        header.pack(pady=20)

        # Main Content Frame
        content_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20)

        # Input PDF Selection
        input_frame = ctk.CTkFrame(content_frame, fg_color="white", corner_radius=10)
        input_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(input_frame, text="PDF de Entrada:", font=(Theme.FONT_FAMILY, 14), text_color=Theme.TEXT_MAIN).pack(side="left", padx=10)
        
        ctk.CTkEntry(input_frame, textvariable=self.input_pdf, state="readonly", width=300).pack(side="left", fill="x", expand=True, padx=5, pady=10)
        ctk.CTkButton(input_frame, text="Explorar", command=self.browse_pdf, width=100,
                      fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER).pack(side="left", padx=10, pady=10)

        # Watermark Settings
        settings_frame = ctk.CTkFrame(content_frame, fg_color="white", corner_radius=10)
        settings_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(settings_frame, text="Configuración de la Marca de Agua", font=(Theme.FONT_FAMILY, 16, "bold"), text_color=Theme.TEXT_MAIN).pack(pady=10)

        # Type Selection
        type_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        type_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(type_frame, text="Tipo:", text_color=Theme.TEXT_MAIN).pack(side="left", padx=10)
        ctk.CTkRadioButton(type_frame, text="Texto", variable=self.watermark_type, value="text", command=self.toggle_inputs,
                           fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER).pack(side="left", padx=10)
        ctk.CTkRadioButton(type_frame, text="Imagen", variable=self.watermark_type, value="image", command=self.toggle_inputs,
                           fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER).pack(side="left", padx=10)

        # Text Entry
        self.text_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        ctk.CTkLabel(self.text_frame, text="Texto:", text_color=Theme.TEXT_MAIN).pack(side="left", padx=10)
        ctk.CTkEntry(self.text_frame, textvariable=self.watermark_text).pack(side="left", fill="x", expand=True, padx=5)

        # Image Entry
        self.image_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        ctk.CTkLabel(self.image_frame, text="Imagen:", text_color=Theme.TEXT_MAIN).pack(side="left", padx=10)
        ctk.CTkEntry(self.image_frame, textvariable=self.watermark_image, state="readonly").pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(self.image_frame, text="Explorar", command=self.browse_image, width=80,
                      fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER).pack(side="left", padx=5)

        # Common Options
        options_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        options_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(options_frame, text="Opacidad:", text_color=Theme.TEXT_MAIN).pack(side="left", padx=10)
        ctk.CTkSlider(options_frame, from_=0.1, to=1.0, variable=self.opacity, button_color=Theme.PRIMARY, progress_color=Theme.PRIMARY).pack(side="left", fill="x", expand=True, padx=5)
        
        ctk.CTkLabel(options_frame, text="Rotación:", text_color=Theme.TEXT_MAIN).pack(side="left", padx=(10, 0))
        ctk.CTkEntry(options_frame, textvariable=self.rotation, width=60).pack(side="left", padx=5)

        # Apply Button
        ctk.CTkButton(self.content_frame, text="Aplicar Marca de Agua", command=self.apply_watermark, 
                      fg_color="#2CC985", hover_color="#0C955A", font=(Theme.FONT_FAMILY, 16, "bold")).pack(pady=20)
        
        self.enable_dnd()

        self.toggle_inputs()

    def handle_dropped_files(self, files):
        handled = False
        for f in files:
            if f.lower().endswith('.pdf'):
                self.input_pdf.set(f)
                handled = True
            elif f.lower().endswith(('.png', '.jpg', '.jpeg')):
                self.watermark_image.set(f)
                self.watermark_type.set("image")
                self.toggle_inputs()
                handled = True
        return handled

    def toggle_inputs(self):
        # Reset to ensure correct order and visibility
        self.text_frame.pack_forget()
        self.image_frame.pack_forget()
        
        if self.watermark_type.get() == "text":
            self.text_frame.pack(fill="x", padx=5, pady=5)
        else:
            self.image_frame.pack(fill="x", padx=5, pady=5)

    def browse_pdf(self):
        filename = filedialog.askopenfilename(filetypes=[("Archivos PDF", "*.pdf")])
        if filename:
            self.input_pdf.set(filename)

    def browse_image(self):
        filename = filedialog.askopenfilename(filetypes=[("Imágenes", "*.png;*.jpg;*.jpeg")])
        if filename:
            self.watermark_image.set(filename)

    def apply_watermark(self):
        if not self.input_pdf.get():
            messagebox.showwarning("Advertencia", "¡Por favor, seleccione un PDF de entrada!")
            return

        output_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("Archivos PDF", "*.pdf")])
        if not output_path:
            return

        try:
            text = self.watermark_text.get() if self.watermark_type.get() == "text" else None
            image = self.watermark_image.get() if self.watermark_type.get() == "image" else None

            if self.watermark_type.get() == "text" and not text:
                messagebox.showwarning("Advertencia", "¡Por favor, ingrese el texto de la marca de agua!")
                return
            if self.watermark_type.get() == "image" and not image:
                messagebox.showwarning("Advertencia", "¡Por favor, seleccione una imagen para la marca de agua!")
                return

            PDFManager.add_watermark(
                self.input_pdf.get(),
                output_path,
                watermark_text=text,
                watermark_image=image,
                opacity=self.opacity.get(),
                rotation=int(self.rotation.get())
            )
            
            if messagebox.askyesno("Éxito", "Marca de agua aplicada. ¿Desea visualizar el PDF?"):
                from app.gui.pages.visualization_page import VisualizationPage
                self.controller.show_page(VisualizationPage)
                self.controller.current_page.load_pdf(output_path)

        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error: {str(e)}")

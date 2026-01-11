import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import fitz
from PIL import Image
import os
import threading

from app.gui.pages.base_page import BasePage
from app.gui.theme import Theme
from app.core.form_handler import FormHandler

class FormFillerPage(BasePage):
    def create_widgets(self):
        # Barra de herramientas superior
        self.toolbar_frame = ctk.CTkFrame(self.content_frame, height=50)
        self.toolbar_frame.pack(fill="x", padx=10, pady=5)
        
        self.btn_load = ctk.CTkButton(self.toolbar_frame, text="Abrir PDF", command=self.select_file, 
                                      fg_color=Theme.PRIMARY)
        self.btn_load.pack(side="left", padx=10, pady=10)
        
        self.lbl_file = ctk.CTkLabel(self.toolbar_frame, text="Ningún archivo seleccionado", text_color="gray")
        self.lbl_file.pack(side="left", padx=10)
        
        self.btn_save = ctk.CTkButton(self.toolbar_frame, text="Guardar PDF", command=self.save_pdf, 
                                      fg_color="#2CC985", hover_color="#0C955A", state="disabled")
        self.btn_save.pack(side="right", padx=10, pady=10)
        
        # Área principal con desplazamiento
        self.main_scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color="gray90")
        self.main_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Estado interno
        self.pdf_path = None
        self.input_widgets = {}
        self.preview_images = []
        self.scale_factor = 1.0
        self.render_scale = 1.25 

    def select_file(self):
        f = filedialog.askopenfilename(filetypes=[("Archivos PDF", "*.pdf")])
        if f:
            self.load_pdf(f)

    def load_pdf(self, path):
        self.pdf_path = path
        self.lbl_file.configure(text=os.path.basename(path))
        self.btn_save.configure(state="normal")
        
        # Limpiar anteriores
        for w in self.main_scroll.winfo_children():
            w.destroy()
        self.input_widgets.clear()
        self.preview_images.clear()
        
        # Iniciar el procesamiento en segundo plano
        threading.Thread(target=self._process_pdf_background, args=(path,), daemon=True).start()

    def _process_pdf_background(self, path):
        fields_data = FormHandler.extract_fields(path)
        
        # Organizar los campos por página
        fields_by_page = {}
        for f in fields_data:
            p = f['page']
            if p not in fields_by_page:
                fields_by_page[p] = []
            fields_by_page[p].append(f)
        page_images = []
        try:
            doc = fitz.open(path)
            for page_num, page in enumerate(doc):
                pix = page.get_pixmap(matrix=fitz.Matrix(self.render_scale, self.render_scale))
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                page_images.append((page_num, img, pix.width, pix.height))
            doc.close()
        except Exception as e:
            print(f"Render Error: {e}")
            
        self.after(0, lambda: self._update_ui_with_pages(page_images, fields_by_page))

    def _update_ui_with_pages(self, page_images, fields_by_page):
        for page_num, pil_img, w, h in page_images:
            # Crear CTkImage 
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(w, h))
            self.preview_images.append(ctk_img)
            
            # Contenedor de página
            page_frame = ctk.CTkFrame(self.main_scroll, width=w, height=h, fg_color="transparent")
            page_frame.pack(pady=10)
            
            page_frame.pack_propagate(False) 
            
            # Imagen de fondo
            bg_label = ctk.CTkLabel(page_frame, text="", image=ctk_img, width=0, height=0)
            bg_label.place(x=0, y=0)
            
            # Superposiciones (Overlays)
            if page_num in fields_by_page:
                for field in fields_by_page[page_num]:
                    self.create_overlay_widget(page_frame, field)

    def create_overlay_widget(self, parent_frame, field):
        rect = field['rect']
        x0, y0, x1, y1 = rect
        
        # Aplicar escala
        sx0 = x0 * self.render_scale
        sy0 = y0 * self.render_scale
        sx1 = x1 * self.render_scale
        sy1 = y1 * self.render_scale
        
        width = sx1 - sx0
        height = sy1 - sy0
        
        # Verificación de widget válido
        if width < 10 or height < 10:
             print(f"Widget {param} es muy pequeño: {width}x{height}")

        ftype = field['type']
        val = field['value']
        param = field['param']
        
        # Decidir widget
        widget = None
        
        if ftype == "Checkbox":
            box_size = min(int(width), int(height), 24)
            
            var = ctk.BooleanVar(value=bool(val))
            widget = ctk.CTkCheckBox(parent_frame, text="", variable=var, 
                                     width=int(width), height=int(height),
                                     checkbox_width=box_size, checkbox_height=box_size,
                                     bg_color="transparent", border_width=2)
            widget.lift() # Forzar que esté arriba
            self.input_widgets[param] = var

        elif ftype == "RadioButton":
            if param in self.input_widgets:
                var = self.input_widgets[param]
            else:
                var = ctk.StringVar(value=str(val) if val else "")
                self.input_widgets[param] = var
            
            on_val = field.get("on_value", "Yes")
            box_size = min(int(width), int(height), 24)
            
            widget = ctk.CTkRadioButton(parent_frame, text="", variable=var, value=on_val,
                                        width=int(width), height=int(height),
                                        radiobutton_width=box_size, radiobutton_height=box_size,
                                        bg_color="transparent")
            widget.lift()
            
        elif ftype in ["ComboBox", "ListBox"]:
            var = ctk.StringVar(value=str(val) if val else "")
            try:
                choices = [str(c) for c in field.get('choices', [])]
            except:
                choices = []
            widget = ctk.CTkComboBox(parent_frame, variable=var, values=choices, 
                                     width=int(width), height=int(height))
            self.input_widgets[param] = var
            
        else:
            var = ctk.StringVar(value=str(val) if val else "")
            widget = ctk.CTkEntry(parent_frame, textvariable=var, width=int(width), height=int(height),
                                  border_width=1, corner_radius=0, fg_color="#F0F0F0", border_color="#CCCCCC") 
            self.input_widgets[param] = var
            
        if widget:
            widget.place(x=sx0, y=sy0)
            print(f"Placed {ftype} '{param}' at {sx0},{sy0} size {width}x{height}")

    def save_pdf(self):
        if not self.pdf_path:
            return
            
        output_path = filedialog.asksaveasfilename(filetypes=[("Archivos PDF", "*.pdf")], defaultextension=".pdf")
        if not output_path:
            return
            
        # Recopilar datos
        data_to_fill = {}
        for name, widget_var in self.input_widgets.items():
            data_to_fill[name] = widget_var.get()
            
        try:
            FormHandler.fill_pdf(self.pdf_path, data_to_fill, output_path)
            messagebox.showinfo("Éxito", "Formulario guardado correctamente.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

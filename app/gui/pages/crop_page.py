import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, Canvas
from app.gui.components import dialogs as messagebox
import fitz  # PyMuPDF
from PIL import Image, ImageTk
from app.gui.pages.base_page import BasePage
from app.gui.theme import Theme
from app.core.pdf_ops import PDFOperations
import os

class CropPage(BasePage):
    def create_widgets(self):
        self.pdf_path = None
        self.doc = None
        self.current_page_num = 0
        self.total_pages = 0
        self.tk_image = None
        self.scale = None 
        
        self.page_crops = {}
        
        self.crop_delete_map = {} 
        
        self.start_x = None
        self.start_y = None
        self.rect_id = None
        
        # Izquierda (Controles), Derecha (Vista Previa)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Marco de Controles
        self.controls_frame = ctk.CTkFrame(self.content_frame, width=250, corner_radius=8, fg_color=Theme.CARD_BG_N3)
        self.controls_frame.pack(side="left", fill="y")
        
        # Encabezado
        ctk.CTkLabel(self.controls_frame, text="Recorte personalizado", font=(Theme.FONT_FAMILY, 20, "bold")).pack(pady=20, padx=10)
        
        # Botón de Abrir
        ctk.CTkButton(self.controls_frame, text="Abrir PDF", command=self.select_file).pack(pady=10, padx=20, fill="x")
        
        # Navegación de Páginas
        nav_frame = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        nav_frame.pack(pady=10, fill="x")
        
        self.btn_prev = ctk.CTkButton(nav_frame, text="<", width=30, command=self.prev_page, state="disabled")
        self.btn_prev.pack(side="left", padx=10)
        
        self.lbl_page = ctk.CTkLabel(nav_frame, text="0 / 0")
        self.lbl_page.pack(side="left", expand=True)
        
        self.btn_next = ctk.CTkButton(nav_frame, text=">", width=30, command=self.next_page, state="disabled")
        self.btn_next.pack(side="right", padx=10)
        
        # Ir a la Página
        goto_frame = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        goto_frame.pack(pady=5, fill="x")
        
        self.entry_goto = ctk.CTkEntry(goto_frame, placeholder_text="Ir a", width=60)
        self.entry_goto.pack(side="left", padx=(20, 5))
        self.entry_goto.bind("<Return>", self.goto_page)
        
        btn_goto = ctk.CTkButton(goto_frame, text="Ir", width=40, command=self.goto_page)
        btn_goto.pack(side="left", padx=5)
        
        # Controles de Zoom
        zoom_frame = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        zoom_frame.pack(pady=10, fill="x")
        
        ctk.CTkLabel(zoom_frame, text="Zoom:", font=(Theme.FONT_FAMILY, 14)).pack(side="top", padx=20)
        ctk.CTkButton(zoom_frame, text="+", command=self.zoom_in, width=60).pack(side="left", padx=20)
        ctk.CTkButton(zoom_frame, text="-", command=self.zoom_out, width=60).pack(side="right", padx=20)
        
        # Estado
        self.lbl_status = ctk.CTkLabel(self.controls_frame, text="Páginas Recortadas: 0", font=(Theme.FONT_FAMILY, 14))
        self.lbl_status.pack(pady=20)
        
        self.action_var = tk.StringVar(value="cropped_pdf")
        
        action_frame = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        action_frame.pack(pady=10, fill="x", padx=10)
        
        ctk.CTkRadioButton(action_frame, text="PDF Recortado", variable=self.action_var, value="cropped_pdf").pack(anchor="w", pady=5)
        ctk.CTkRadioButton(action_frame, text="PDF Completo con Recortes", variable=self.action_var, value="full_pdf").pack(anchor="w", pady=5)
        ctk.CTkRadioButton(action_frame, text="Generar Imágenes", variable=self.action_var, value="images").pack(anchor="w", pady=5)
        
        # Botón de Proceso
        self.btn_process = ctk.CTkButton(self.controls_frame, text="Crear", command=self.process_action, state="disabled", fg_color=Theme.PRIMARY, width=120)
        self.btn_process.pack(pady=20, padx=20)
        
        # Botones de Limpiar
        clear_frame = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        clear_frame.pack(pady=10, fill="x", padx=10)
        
        self.btn_clear_page = ctk.CTkButton(clear_frame, text="Limpiar Página", command=self.clear_current_crop, state="disabled", fg_color="#FF5555", width=80)
        self.btn_clear_page.pack(side="left", padx=5, expand=True)

        self.btn_clear_all = ctk.CTkButton(clear_frame, text="Limpiar Todo", command=self.clear_all_crops, state="disabled", fg_color="#FF5555", width=80)
        self.btn_clear_all.pack(side="right", padx=5, expand=True)

        # Marco de Vista Previa
        self.preview_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.preview_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        self.canvas_container = ctk.CTkFrame(self.preview_frame, fg_color="#E0E0E0")
        self.canvas_container.pack(fill="both", expand=True)

        # Barras de desplazamiento
        self.v_scroll = tk.Scrollbar(self.canvas_container, orient="vertical")
        self.h_scroll = tk.Scrollbar(self.canvas_container, orient="horizontal")

        self.canvas = Canvas(self.canvas_container, bg="gray", highlightthickness=0,
                             xscrollcommand=self.h_scroll.set, yscrollcommand=self.v_scroll.set)
        
        self.v_scroll.config(command=self.canvas.yview)
        self.h_scroll.config(command=self.canvas.xview)

        self.v_scroll.pack(side="right", fill="y")
        self.h_scroll.pack(side="bottom", fill="x")
        self.canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        
        self.enable_dnd()

    def handle_dropped_files(self, files):
        for f in files:
            if f.lower().endswith('.pdf'):
                self.load_pdf(f)
                return True
        return False

    def select_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Archivos PDF", "*.pdf")])
        if filename:
            self.load_pdf(filename)

    def load_pdf(self, path):
        try:
            if self.doc:
                self.doc.close()
            self.doc = fitz.open(path)
            self.pdf_path = path
            self.total_pages = len(self.doc)
            self.current_page_num = 0
            self.page_crops = {} # Restablecer recortes
            self.update_status()
            self.show_page(0)
            self.update_nav_buttons()
            self.btn_process.configure(state="disabled")
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar PDF: {e}")

    def show_page(self, page_num):
        if not self.doc: return
        
        page = self.doc[page_num]
        
        # Renderizar
        canvas_width = self.canvas_container.winfo_width()
        canvas_height = self.canvas_container.winfo_height()
        if canvas_width < 10: canvas_width = 600
        if canvas_height < 10: canvas_height = 800
        
        rect = page.rect
        scale_w = (canvas_width - 30) / rect.width
        scale_h = (canvas_height - 30) / rect.height
        
        if self.scale is None:
             self.scale = min(scale_w, scale_h, 2.0) * 0.9

        mat = fitz.Matrix(self.scale, self.scale)
        pix = page.get_pixmap(matrix=mat)
        
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        self.tk_image = ImageTk.PhotoImage(img)
        
        self.canvas.delete("all")
        
        x_centered = (canvas_width - pix.width) // 2
        y_centered = (canvas_height - pix.height) // 2
        self.image_offset_x = x_centered
        self.image_offset_y = y_centered
        
        self.canvas.create_image(x_centered, y_centered, image=self.tk_image, anchor="nw")
        
        # Actualizar región de desplazamiento (scrollregion)
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        
        self.lbl_page.configure(text=f"{page_num + 1} / {self.total_pages}")
        
        # Dibujar recortes existentes si los hay
        if page_num in self.page_crops:
            self.draw_existing_crops(self.page_crops[page_num])
            self.btn_clear_page.configure(state="normal")
        else:
            self.btn_clear_page.configure(state="disabled")

    def draw_existing_crops(self, crop_list):
        self.crop_delete_map = {}
        
        for idx, crop_box in enumerate(crop_list):
            pdf_x0, pdf_y0, pdf_x1, pdf_y1 = crop_box
            page = self.doc[self.current_page_num]
            rot = page.rotation
            cb = page.cropbox
            
            # Lógica de mapeo
            p0 = fitz.Point(pdf_x0, pdf_y0) 
            p1 = fitz.Point(pdf_x1, pdf_y1) 
            
            # Lógica para manejar la rotación y el mapeo del lienzo
            ox, oy = cb.x0, cb.y0
            r = fitz.Rect(crop_box)
            m = fitz.Matrix(rot)
            
            cb_quad = cb.quad
            cb_rot = cb_quad.transform(m).rect
            
            shift_x = -cb_rot.x0
            shift_y = -cb_rot.y0
            
            tm = fitz.Matrix(rot)
            r_rot = r.transform(tm)
            r_shifted = r_rot + (shift_x, shift_y, shift_x, shift_y)
            
            # Escala y desplazamiento
            vx0 = r_shifted.x0 * self.scale
            vy0 = r_shifted.y0 * self.scale
            vx1 = r_shifted.x1 * self.scale
            vy1 = r_shifted.y1 * self.scale
            
            x0 = vx0 + self.image_offset_x
            y0 = vy0 + self.image_offset_y
            x1 = vx1 + self.image_offset_x
            y1 = vy1 + self.image_offset_y
            
            # Dibujar Rectángulo
            self.canvas.create_rectangle(x0, y0, x1, y1, outline="red", width=2, dash=(4, 4), tags="saved_crop")
            
            # Dibujar Botón de Borrar (X)
            left = min(x0, x1)
            top = min(y0, y1)
            
            # Tamaño del botón
            bs = 14
            btn_x = left
            btn_y = top - bs
            if btn_y < 0: btn_y = top
            # Etiqueta para el botón
            tag_name = f"del_{idx}"
            
            btn_id = self.canvas.create_rectangle(btn_x, btn_y, btn_x+bs, btn_y+bs, fill="red", outline="white", tags=tag_name)
            self.canvas.create_line(btn_x, btn_y, btn_x+bs, btn_y+bs, fill="white", width=2, tags=tag_name)
            self.canvas.create_line(btn_x+bs, btn_y, btn_x, btn_y+bs, fill="white", width=2, tags=tag_name)
            self.canvas.tag_bind(tag_name, "<ButtonPress-1>", lambda e, i=idx: self.delete_crop(i))

    def prev_page(self):
        if self.current_page_num > 0:
            self.current_page_num -= 1
            self.show_page(self.current_page_num)
            self.update_nav_buttons()

    def next_page(self):
        if self.current_page_num < self.total_pages - 1:
            self.current_page_num += 1
            self.show_page(self.current_page_num)
            self.update_nav_buttons()

    def goto_page(self, event=None):
        if not self.doc: return
        try:
            val = self.entry_goto.get()
            if not val: return
            page_num = int(val) - 1
            if 0 <= page_num < self.total_pages:
                self.current_page_num = page_num
                self.show_page(self.current_page_num)
                self.update_nav_buttons()
            else:
                 messagebox.showwarning("Advertencia", f"La página debe estar entre 1 y {self.total_pages}")
        except ValueError:
             messagebox.showwarning("Advertencia", "Número de página inválido")

    def update_nav_buttons(self):
        self.btn_prev.configure(state="normal" if self.current_page_num > 0 else "disabled")
        self.btn_next.configure(state="normal" if self.current_page_num < self.total_pages - 1 else "disabled")

    def zoom_in(self):
        if self.scale is None: return
        self.scale *= 1.2
        self.show_page(self.current_page_num)
        
    def zoom_out(self):
        if self.scale is None: return
        self.scale *= 0.8
        self.show_page(self.current_page_num)

    def delete_crop(self, index):
        if self.current_page_num in self.page_crops:
            crops = self.page_crops[self.current_page_num]
            if 0 <= index < len(crops):
                crops.pop(index)
                if not crops:
                    del self.page_crops[self.current_page_num]
                self.show_page(self.current_page_num)
                self.update_status()

    def on_mouse_down(self, event):
        if not self.doc: return
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        self.canvas.delete("crop_rect")
        if self.rect_id:
            self.canvas.delete(self.rect_id)
            self.rect_id = None

    def on_mouse_drag(self, event):
        if not self.doc or self.start_x is None: return
        
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        
        if self.rect_id:
            self.canvas.coords(self.rect_id, self.start_x, self.start_y, cx, cy)
        else:
            self.rect_id = self.canvas.create_rectangle(self.start_x, self.start_y, cx, cy, outline="red", width=2, dash=(4, 4))

    def on_mouse_up(self, event):
        if not self.doc or self.start_x is None: return
        
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        
        # Calcular coordenadas
        x0 = min(self.start_x, cx)
        y0 = min(self.start_y, cy)
        x1 = max(self.start_x, cx)
        y1 = max(self.start_y, cy)
        
        if abs(x1 - x0) < 10 or abs(y1 - y0) < 10:
             self.canvas.delete(self.rect_id)
             self.rect_id = None
             return

        # Puntos del Lienzo
        cx0, cy0 = x0, y0
        cx1, cy1 = x1, y1
        
        # Quitar desplazamiento
        px0 = (cx0 - self.image_offset_x) / self.scale
        py0 = (cy0 - self.image_offset_y) / self.scale
        px1 = (cx1 - self.image_offset_x) / self.scale
        py1 = (cy1 - self.image_offset_y) / self.scale
        
        page = self.doc[self.current_page_num]
        
        # Usar un Punto para transformar
        p0 = fitz.Point(px0, py0)
        p1 = fitz.Point(px1, py1)
        
        # Crear un rectángulo genérico a partir de puntos para manejar las esquinas
        r_pix = fitz.Rect(p0, p1)
        
        # Obtener rotación
        rot = page.rotation

        mat = fitz.Matrix(rot) # Matriz de rotación
        
        cb = page.cropbox # Este es el cuadro de coordenadas PDF que estamos viendo.
        
        # Si la rotación es 0:
        pdf_x0 = px0 + cb.x0
        pdf_y0 = py0 + cb.y0
        pdf_x1 = px1 + cb.x0
        pdf_y1 = py1 + cb.y0
        
        final_rect = fitz.Rect(pdf_x0, pdf_y0, pdf_x1, pdf_y1)
        
        if rot != 0:
             w = cb.width
             h = cb.height
             
             if rot == 90:
                 pass
             
             # Dimensiones Visuales
             vw = (px1 - px0) # Ancho de la selección
             vh = (py1 - py0)
             
             # Porcentajes de la PÁGINA (Visual)
             # Tamaño de Página Visual (Sin Escala)
             if rot % 180 == 0:
                 v_page_w = cb.width
                 v_page_h = cb.height
             else:
                 v_page_w = cb.height
                 v_page_h = cb.width
             
             # Normalizar p0, p1
             nx0, ny0 = px0/v_page_w, py0/v_page_h
             nx1, ny1 = px1/v_page_w, py1/v_page_h
             
             if rot == 90:
                 m = fitz.Matrix(-rot)                 
                 pass

             if rot == 90:
                 corners = [
                     (px0, py0), (px1, py0), (px1, py1), (px0, py1)
                 ]
                 
                 pdf_points = []
                 for (vx, vy) in corners:
                     if rot == 90:
                         nx = vy
                         ny = v_page_w - vx
                     elif rot == 180:
                         nx = v_page_w - vx
                         ny = v_page_h - vy
                     elif rot == 270:
                         nx = v_page_h - vy
                         ny = vx
                     
                     pdf_points.append((nx + cb.x0, ny + cb.y0))
                 
                 xs = [p[0] for p in pdf_points]
                 ys = [p[1] for p in pdf_points]
                 final_rect = fitz.Rect(min(xs), min(ys), max(xs), max(ys))
             
        
        if self.current_page_num not in self.page_crops:
             self.page_crops[self.current_page_num] = []
             
        # Comprobar límite
        if len(self.page_crops[self.current_page_num]) >= 4:
             messagebox.showwarning("Límite Alcanzado", "Máximo de 4 recortes por página.")
             self.canvas.delete(self.rect_id)
             self.rect_id = None
             return

        self.page_crops[self.current_page_num].append((final_rect.x0, final_rect.y0, final_rect.x1, final_rect.y1))
        
        self.update_status()
        self.btn_clear_page.configure(state="normal")
        
        self.canvas.delete(self.rect_id)
        self.rect_id = None
        self.show_page(self.current_page_num)

    def clear_current_crop(self):
        if self.current_page_num in self.page_crops:
            del self.page_crops[self.current_page_num]
            self.update_status()
            self.show_page(self.current_page_num)

    def clear_all_crops(self):
        if messagebox.askyesno("Confirmar", "¿Está seguro de que desea limpiar todos los recortes?"):
            self.page_crops = {}
            self.update_status()
            self.show_page(self.current_page_num)

    def process_action(self):
        action = self.action_var.get()
        if action == "cropped_pdf":
            self.generate_pdf()
        elif action == "full_pdf":
            self.save_full_pdf()
        elif action == "images":
            self.generate_images()
            
    def update_status(self):
        count = sum(len(crops) for crops in self.page_crops.values())
        self.lbl_status.configure(text=f"Recortes Totales: {count}")
        state = "normal" if count > 0 else "disabled"
        self.btn_process.configure(state=state)
        self.btn_clear_all.configure(state=state)

    def generate_pdf(self):
        if not self.page_crops: return
        
        output_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("Archivos PDF", "*.pdf")])
        if not output_path: return
        
        try:
            PDFOperations.create_cropped_pdf(self.pdf_path, output_path, self.page_crops)
            messagebox.showinfo("Éxito", f"¡Se creó el PDF con {len(self.page_crops)} páginas!")
        except Exception as e:
            messagebox.showerror("Error", f"Error al crear PDF: {e}")

    def generate_images(self):
        if not self.page_crops: return
        
        output_dir = filedialog.askdirectory()
        if not output_dir: return

        try:
             # Iterar y guardar
             count = 0
             for page_idx, crops in self.page_crops.items():
                 page = self.doc[page_idx]
                 
                 original_crop = page.cropbox
                 
                 for i, crop in enumerate(crops):
                     # Establecer el cropbox al área deseada
                     page.set_cropbox(fitz.Rect(crop))
                     mat = fitz.Matrix(2, 2) 
                     
                     # Renderizar
                     pix = page.get_pixmap(matrix=mat)
                     page.set_cropbox(original_crop)
                     
                     # Guardar
                     base = os.path.basename(self.pdf_path).replace(".pdf", "")
                     name = f"{base}_page_{page_idx+1}_crop_{i+1}.png"
                     path = os.path.join(output_dir, name)
                     pix.save(path)
                     count += 1
                  
             messagebox.showinfo("Éxito", f"Se generaron {count} imágenes exitosamente.")
             
        except Exception as e:
             messagebox.showerror("Error", f"Error al generar imágenes: {e}")

    def save_full_pdf(self):
        if not self.page_crops: return
        
        output_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("Archivos PDF", "*.pdf")])
        if not output_path: return
        
        try:
            PDFOperations.apply_crops_to_pdf(self.pdf_path, output_path, self.page_crops)
            messagebox.showinfo("Éxito", "¡PDF completo guardado con los recortes aplicados!")
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar PDF: {e}")

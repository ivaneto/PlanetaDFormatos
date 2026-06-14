import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, Canvas
from app.gui.components import dialogs as messagebox
from app.gui.pages.base_page import BasePage
from app.gui.components.file_list_frame import FileListFrame
from app.gui.theme import Theme
from app.core.signer import PDFSigner
from app.core.pdf_editor import PDFEditorBackend
from PIL import Image, ImageTk, ImageDraw
import os
import tempfile
import fitz # PyMuPDF
import io

import uuid

class PDFViewerFrame(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.pdf_path = None
        self.doc = None
        self.current_page_idx = 0
        self.zoom_level = 1.0
        self.signatures = [] 
        self.selected_sig_id = None
        self.active_mode = None 
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.initial_resize_state = {} 
        
        self.create_widgets() 
        
    def create_widgets(self):
        # Barra de herramientas
        self.toolbar = ctk.CTkFrame(self, height=40, fg_color="transparent")
        self.toolbar.pack(fill="x", padx=5, pady=5)
        
        self.btn_prev = ctk.CTkButton(self.toolbar, text="<", width=30, command=self.prev_page)
        self.btn_prev.pack(side="left", padx=5)
        
        self.lbl_page = ctk.CTkLabel(self.toolbar, text="Página: 0/0")
        self.lbl_page.pack(side="left", padx=5)
        
        self.btn_next = ctk.CTkButton(self.toolbar, text=">", width=30, command=self.next_page)
        self.btn_next.pack(side="left", padx=5)
        
        # Controles de Zoom
        self.btn_zoom_out = ctk.CTkButton(self.toolbar, text="-", width=30, command=self.zoom_out)
        self.btn_zoom_out.pack(side="right", padx=5)
        
        self.lbl_zoom = ctk.CTkLabel(self.toolbar, text="100%")
        self.lbl_zoom.pack(side="right", padx=5)
        
        self.btn_zoom_in = ctk.CTkButton(self.toolbar, text="+", width=30, command=self.zoom_in)
        self.btn_zoom_in.pack(side="right", padx=5)
        
        # Botón para eliminar firma seleccionada
        self.btn_del_sig = ctk.CTkButton(self.toolbar, text="Eliminar firma", width=80, fg_color="red", hover_color="darkred", command=self.delete_selected_signature)
        self.btn_del_sig.pack(side="right", padx=20)
        self.update_delete_btn()
        
        self.canvas_container = ctk.CTkFrame(self, fg_color="#505050")
        self.canvas_container.pack(fill="both", expand=True)
        
        self.canvas = tk.Canvas(self.canvas_container, bg="#505050", highlightthickness=0)
        self.v_scroll = ctk.CTkScrollbar(self.canvas_container, command=self.canvas.yview)
        self.h_scroll = ctk.CTkScrollbar(self.canvas_container, orientation="horizontal", command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)
        
        self.v_scroll.pack(side="right", fill="y")
        self.h_scroll.pack(side="bottom", fill="x")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Vinculaciones
        self.canvas.bind("<ButtonPress-1>", self.on_drag_start)
        self.canvas.bind("<B1-Motion>", self.on_drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self.on_drag_stop)
        self.canvas.bind("<Motion>", self.on_mouse_move)

    def load_pdf(self, path):
        self.pdf_path = path
        try:
            # Cerrar el documento previo para liberar memoria y el bloqueo del archivo.
            if self.doc:
                try:
                    self.doc.close()
                except Exception:
                    pass
            self.doc = fitz.open(path)
            self.current_page_idx = 0
            self.zoom_level = 1.0 
            self.signatures = [] # Limpiar firmas al abrir un nuevo archivo
            self.selected_sig_id = None
            self.render_page()
            self.update_info()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar PDF: {e}")

    def render_page(self):
        if not self.doc: return
        page = self.doc[self.current_page_idx]
        
        pix = page.get_pixmap(matrix=fitz.Matrix(self.zoom_level, self.zoom_level))
        img_data = pix.tobytes("png")
        pil_img = Image.open(io.BytesIO(img_data))
        self.tk_img = ImageTk.PhotoImage(pil_img)
        
        self.canvas.delete("all")
        self.bg_item = self.canvas.create_image(0, 0, image=self.tk_img, anchor="nw")
        
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        self.lbl_zoom.configure(text=f"{int(self.zoom_level * 100)}%")
        
        self.render_signatures()
        self.update_delete_btn()

    def update_info(self):
        if self.doc:
            self.lbl_page.configure(text=f"Página: {self.current_page_idx + 1}/{len(self.doc)}")

    def prev_page(self):
        if self.doc and self.current_page_idx > 0:
            self.current_page_idx -= 1
            self.render_page()
            self.update_info()

    def next_page(self):
        if self.doc and self.current_page_idx < len(self.doc) - 1:
            self.current_page_idx += 1
            self.render_page()
            self.update_info()

    def add_signature(self, pil_image, image_path=None):
        if not self.doc: return
        
        ts_w = 150
        ratio = ts_w / pil_image.width
        ts_h = int(pil_image.height * ratio)
        
        sig_id = str(uuid.uuid4())
        
        new_sig = {
            'id': sig_id,
            'page': self.current_page_idx,
            'x': 50.0,
            'y': 50.0,
            'w': float(ts_w),
            'h': float(ts_h),
            'img': pil_image,
            'path': image_path
        }
        
        self.signatures.append(new_sig)
        self.selected_sig_id = sig_id
        self.render_signatures()
        self.update_delete_btn()

    def delete_selected_signature(self):
        if self.selected_sig_id:
            self.signatures = [s for s in self.signatures if s['id'] != self.selected_sig_id]
            self.selected_sig_id = None
            self.render_signatures()
            self.update_delete_btn()

    def update_delete_btn(self):
        if self.selected_sig_id:
            self.btn_del_sig.configure(state="normal")
        else:
            self.btn_del_sig.configure(state="disabled")

    def render_signatures(self):
        self.canvas.delete("signature_widget")
        self.cached_tk_images = []
        
        if not self.doc: return
        
        page = self.doc[self.current_page_idx]
        pdf_w, pdf_h = page.rect.width, page.rect.height
        
        scale = self.zoom_level
        
        scale = self.zoom_level
        
        for sig in self.signatures:
            if sig['page'] != self.current_page_idx:
                continue
                
            cx = sig['x'] * scale
            cy = sig['y'] * scale
            cw = sig['w'] * scale
            ch = sig['h'] * scale
            
            cw, ch = max(1, int(cw)), max(1, int(ch))
            
            resized = sig['img'].resize((cw, ch), Image.Resampling.LANCZOS)
            tk_img = ImageTk.PhotoImage(resized)
            self.cached_tk_images.append(tk_img)
            
            self.canvas.create_image(cx, cy, image=tk_img, anchor="nw", 
                                     tags=("signature_widget", "signature_image", f"sig_id_{sig['id']}"))
            
            if sig['id'] == self.selected_sig_id:
                self.canvas.create_rectangle(cx, cy, cx+cw, cy+ch, outline="blue", dash=(2, 2), 
                                             tags=("signature_widget", "sig_border", f"sig_id_{sig['id']}"))
                                             
                handle_size = 6
                handles = [
                    (cx, cy, "resize_nw"),
                    (cx+cw, cy, "resize_ne"),
                    (cx, cy+ch, "resize_sw"),
                    (cx+cw, cy+ch, "resize_se")
                ]
                for hx, hy, tag in handles:
                    self.canvas.create_rectangle(hx - handle_size/2, hy - handle_size/2,
                                                 hx + handle_size/2, hy + handle_size/2,
                                                 fill="white", outline="blue", 
                                                 tags=("signature_widget", "resize_handle", tag, f"sig_id_{sig['id']}"))

    def on_mouse_move(self, event):
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        item = self.canvas.find_closest(canvas_x, canvas_y)
        tags = self.canvas.gettags(item)
        
        cursor = ""
        if "resize_nw" in tags or "resize_se" in tags:
            cursor = "ul_angle" 
        elif "resize_ne" in tags or "resize_sw" in tags:
            cursor = "ur_angle"
        elif "signature_image" in tags or "sig_border" in tags:
            cursor = "fleur" 
        
        if cursor:
            self.canvas.config(cursor=cursor)
        else:
            self.canvas.config(cursor="")

    def on_drag_start(self, event):
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        item = self.canvas.find_closest(canvas_x, canvas_y)
        tags = self.canvas.gettags(item)
        
        # Buscar id de la firma
        sig_id = None
        for tag in tags:
            if tag.startswith("sig_id_"):
                sig_id = tag.replace("sig_id_", "")
                break
        
        if not sig_id:
            if self.selected_sig_id:
                self.selected_sig_id = None
                self.render_signatures()
                self.update_delete_btn()
            return
            
        self.selected_sig_id = sig_id
        self.render_signatures() 
        self.update_delete_btn()
            
        self.drag_start_x = canvas_x
        self.drag_start_y = canvas_y
        
        # Determinar modo
        self.active_mode = "move"
        if "resize_nw" in tags: self.active_mode = "resize_nw"
        elif "resize_ne" in tags: self.active_mode = "resize_ne"
        elif "resize_sw" in tags: self.active_mode = "resize_sw"
        elif "resize_se" in tags: self.active_mode = "resize_se"
        
        # Buscar objeto de firma
        sig = next((s for s in self.signatures if s['id'] == sig_id), None)
        if not sig: return
        
        if "resize" in self.active_mode:
            self.initial_resize_state = {
                'x': sig['x'], 'y': sig['y'], 'w': sig['w'], 'h': sig['h']
            }

    def on_drag_motion(self, event):
        if not self.active_mode or not self.selected_sig_id: return
        
        # Buscar firma
        sig = next((s for s in self.signatures if s['id'] == self.selected_sig_id), None)
        if not sig: return
        
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        dx_canvas = canvas_x - self.drag_start_x
        dy_canvas = canvas_y - self.drag_start_y
        
        # Convertir a delta de punto PDF
        scale = self.zoom_level
        dx = dx_canvas / scale
        dy = dy_canvas / scale
        
        if self.active_mode == "move":
            sig['x'] += dx
            sig['y'] += dy
            
            # Actualizar inicio para el próximo delta
            self.drag_start_x = canvas_x
            self.drag_start_y = canvas_y
            
        elif "resize" in self.active_mode:
            # Utiliza el delta acumulado desde el estado inicial para evitar errores de deriva/redondeo
            init = self.initial_resize_state
            
            aspect = init['w'] / init['h']
            
            new_w = sig['w']
            
            if self.active_mode == "resize_se":
                new_w += dx
            elif self.active_mode == "resize_sw":
                new_w -= dx
                sig['x'] += dx
            elif self.active_mode == "resize_ne":
                new_w += dx
            elif self.active_mode == "resize_nw":
                new_w -= dx
                sig['x'] += dx
                
            if new_w < 10: new_w = 10
            new_h = new_w / aspect
            
            # Verificar cambios en Y
            if self.active_mode == "resize_nw":
                sig['y'] += (sig['h'] - new_h)
            elif self.active_mode == "resize_ne":
                sig['y'] += (sig['h'] - new_h)
                
            sig['w'] = new_w
            sig['h'] = new_h
            
            self.drag_start_x = canvas_x
            self.drag_start_y = canvas_y

        self.render_signatures()

    def on_drag_stop(self, event):
        self.active_mode = None
        
    def zoom_in(self):
        self.change_zoom(0.25)
        
    def zoom_out(self):
        self.change_zoom(-0.25)
        
    def change_zoom(self, delta):
        if not self.doc: return
        new_level = self.zoom_level + delta
        if new_level < 0.25: new_level = 0.25
        if new_level > 5.0: new_level = 5.0
        
        if new_level == self.zoom_level: return
        self.zoom_level = new_level
        self.render_page()

class SignPdfPage(BasePage):
    def create_widgets(self):
        # Configurar cuadrícula
        self.content_frame.grid_columnconfigure(0, weight=0)
        self.content_frame.grid_columnconfigure(1, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        # --- Marco de Controles ---
        self.controls_frame = ctk.CTkFrame(self.content_frame, width=350, corner_radius=15, fg_color=Theme.SURFACE)
        self.controls_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.controls_frame.grid_propagate(False)
        
        ctk.CTkLabel(self.controls_frame, text="Firmar PDF", 
                     font=(Theme.FONT_FAMILY, 24, "bold"), text_color=Theme.TEXT_MAIN).pack(pady=(20, 10), padx=20, anchor="w")

        self.tab_view = ctk.CTkTabview(self.controls_frame, text_color=Theme.TEXT_MAIN)
        self.tab_view.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tab_visual = self.tab_view.add("Firma Visual")
        self.tab_digital = self.tab_view.add("Certificado Digital")
        
        self.setup_visual_tab()
        self.setup_digital_tab()
        
        # --- Panel Derecho ---
        # Lista o Visor
        self.right_panel = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(0, 20), pady=20)
        self.right_panel.grid_rowconfigure(0, weight=1)
        self.right_panel.grid_columnconfigure(0, weight=1)

        # Lista de archivos
        self.file_list = FileListFrame(self.right_panel, title="Seleccionar PDF para firmar")
        self.file_list.grid(row=0, column=0, sticky="nsew")
        
        # Visor de PDF
        self.pdf_viewer = PDFViewerFrame(self.right_panel)

        self.btn_add_pdf = ctk.CTkButton(self.controls_frame, text="+ Añadir archivo PDF", command=self.add_pdf_file).pack(fill="x", padx=20, pady=5)

        self.enable_dnd()
        
        self.bind_capture()

    def add_pdf_file(self):
        filenames = filedialog.askopenfilenames(filetypes=[("Archivos PDF", "*.pdf")])
        if filenames:
            for f in filenames:
                self.file_list.add_file(f)
            self.open_in_viewer(filenames[0])

    def open_in_viewer(self, path):
        self.file_list.grid_forget()
        self.pdf_viewer.grid(row=0, column=0, sticky="nsew")
        self.pdf_viewer.load_pdf(path)
        
        self.update_signature_on_viewer()
        
    def show_list(self):
        self.pdf_viewer.grid_forget()
        self.file_list.grid(row=0, column=0, sticky="nsew")

    def update_signature_on_viewer(self):
        if hasattr(self, 'pil_image'):
             self.pdf_viewer.set_signature_image(self.pil_image)
        elif self.sig_image_path:
             try:
                 img = Image.open(self.sig_image_path)
                 self.pdf_viewer.set_signature_image(img)
             except: pass

    # Sobrescribir la liberación del lienzo para actualizar el visor inmediatamente
    def on_canvas_release(self, event):
        self.drawing = False
        # Actualizar PIL
        if hasattr(self, 'pil_image'):
            self.update_signature_on_viewer()

    def setup_visual_tab(self):
        ctk.CTkLabel(self.tab_visual, text="Dibujar Firma:", text_color=Theme.TEXT_MUTED, font=(Theme.FONT_FAMILY, 12)).pack(anchor="w", padx=10)
        
        self.canvas_frame = ctk.CTkFrame(self.tab_visual, fg_color=Theme.SURFACE, border_width=1, border_color="gray")
        self.canvas_frame.pack(fill="x", padx=10, pady=5)
        
        self.canvas = Canvas(self.canvas_frame, height=120, bg="white", highlightthickness=0)
        self.canvas.pack(fill="x", padx=2, pady=2)
        
        self.drawing = False
        self.last_x, self.last_y = None, None
        
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        
        btn_frame = ctk.CTkFrame(self.tab_visual, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(btn_frame, text="Limpiar", width=80, height=25, command=self.clear_canvas,
                      fg_color="gray", hover_color="gray30").pack(side="left")
        
        ctk.CTkButton(btn_frame, text="Subir Imagen", width=120, height=25, command=self.upload_signature_image,
                      fg_color=Theme.SECONDARY, hover_color=Theme.SECONDARY_HOVER).pack(side="right")
        
        self.sig_image_path = None 
        
        # Botón para añadir a la página
        self.btn_add_to_page = ctk.CTkButton(self.tab_visual, text="Añadir firma a la página", command=self.add_current_signature,
                                             fg_color=Theme.SECONDARY, hover_color=Theme.SECONDARY_HOVER)
        self.btn_add_to_page.pack(fill="x", padx=10, pady=10)
        
        
        self.btn_sign_visual = ctk.CTkButton(self.tab_visual, text="Firmar PDF", command=self.sign_visual,
                                             height=40, font=(Theme.FONT_FAMILY, 16, "bold"),
                                             fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER)
        self.btn_sign_visual.pack(side="bottom", fill="x", padx=10, pady=20)
    
    def setup_digital_tab(self):
        ctk.CTkLabel(self.tab_digital, text="Certificado (.p12 / .pfx):", text_color=Theme.TEXT_MUTED, font=(Theme.FONT_FAMILY, 12)).pack(anchor="w", padx=10, pady=(10, 0))
        self.cert_entry = ctk.CTkEntry(self.tab_digital, placeholder_text="Seleccionar archivo...")
        self.cert_entry.pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(self.tab_digital, text="Explorar", command=self.browse_cert, width=80, height=25).pack(anchor="e", padx=10)
        
        ctk.CTkLabel(self.tab_digital, text="Contraseña:", text_color=Theme.TEXT_MUTED, font=(Theme.FONT_FAMILY, 12)).pack(anchor="w", padx=10, pady=(10, 0))
        self.pass_entry = ctk.CTkEntry(self.tab_digital, show="*")
        self.pass_entry.pack(fill="x", padx=10, pady=5)
        
        self.btn_sign_digital = ctk.CTkButton(self.tab_digital, text="Firmar PDF Digitalmente", command=self.sign_digital,
                                              height=40, font=(Theme.FONT_FAMILY, 16, "bold"),
                                              fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER)
        self.btn_sign_digital.pack(side="bottom", fill="x", padx=10, pady=20)

    def on_canvas_click(self, event):
        self.drawing = True
        self.last_x, self.last_y = event.x, event.y

    def on_canvas_drag(self, event):
        if self.drawing:
            x, y = event.x, event.y
            self.canvas.create_line((self.last_x, self.last_y, x, y), fill="black", width=2, capstyle=tk.ROUND, smooth=True)
            self.last_x, self.last_y = x, y

    def clear_canvas(self):
        self.canvas.delete("all")
        self.sig_image_path = None
        if hasattr(self, 'pil_image'):
             draw = ImageDraw.Draw(self.pil_image)
             draw.rectangle([0,0,self.pil_image.width, self.pil_image.height], fill="white")
        # self.update_signature_on_viewer() # Ya no se sincroniza inmediatamente

    def upload_signature_image(self):
        path = filedialog.askopenfilename(filetypes=[("Imágenes", "*.png *.jpg *.jpeg")])
        if path:
            self.sig_image_path = path
            messagebox.showinfo("Imagen seleccionada", f"Usando imagen: {os.path.basename(path)}")
            # self.update_signature_on_viewer()
            
            # Mostrar vista previa en el lienzo
            img = Image.open(path)
            # Ajustar tamaño
            img.thumbnail((300, 110))
            self.preview_tk = ImageTk.PhotoImage(img)
            self.canvas.delete("all")
            self.canvas.create_image(150, 60, image=self.preview_tk, anchor="center")

    def setup_draw_capture(self):
        if not hasattr(self, 'pil_image'):
            self.pil_image = Image.new("RGB", (self.canvas.winfo_width(), self.canvas.winfo_height()), "white")
            self.pil_draw = ImageDraw.Draw(self.pil_image)

    def on_canvas_click_capture(self, event):
        self.on_canvas_click(event)
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        if not hasattr(self, 'pil_image') or self.pil_image.size != (w, h):
            self.pil_image = Image.new("RGBA", (w, h), (255, 255, 255, 0)) 
            self.pil_draw = ImageDraw.Draw(self.pil_image)

    def on_canvas_drag_capture(self, event):
        lx, ly = self.last_x, self.last_y
        self.on_canvas_drag(event) 
        if hasattr(self, 'pil_image'):
             self.pil_draw.line([lx, ly, self.last_x, self.last_y], fill="black", width=2)

    def bind_capture(self):
        self.canvas.bind("<Button-1>", self.on_canvas_click_capture)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag_capture)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        
    def add_current_signature(self):
        # Determinar fuente: Ruta de imagen o Dibujo en el lienzo
        if self.sig_image_path:
            try:
                img = Image.open(self.sig_image_path)
                self.pdf_viewer.add_signature(img, self.sig_image_path)
            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar imagen: {e}")
                return
        elif hasattr(self, 'pil_image'):
            # Usar imagen dibujada
            self.pdf_viewer.add_signature(self.pil_image, None)
        else:
            messagebox.showwarning("Sin firma", "Por favor, dibuje o suba una firma primero.")

    def update_signature_on_viewer(self):
       pass # Ya no se actualiza automáticamente el visor

    def sign_visual(self):
        if not self.pdf_viewer.signatures:
             messagebox.showwarning("Sin firmas", "Por favor, añada firmas a las páginas del documento.")
             return
             
        try:
            target_pdf = self.pdf_viewer.pdf_path
            if not target_pdf: 
                messagebox.showwarning("Sin PDF", "Por favor, cargue un archivo PDF.")
                return
                
            output_path = filedialog.asksaveasfilename(
                initialfile=f"signed_{os.path.basename(target_pdf)}",
                defaultextension=".pdf",
                filetypes=[("Archivos PDF", "*.pdf")]
            )
            if not output_path: return
            
            # Preparar datos de las firmas
            # Lista de diccionarios: {'page': int, 'x': float, 'y': float, 'width': float, 'height': float, 'image_path': str}
            signatures_data = []
            temp_files = []
            
            for sig in self.pdf_viewer.signatures:
                img_path = sig['path']
                if not img_path:
                    # Guardar la imagen dibujada en un archivo temporal
                    fd, temp_path = tempfile.mkstemp(suffix=".png")
                    os.close(fd)
                    sig['img'].save(temp_path)
                    temp_files.append(temp_path)
                    img_path = temp_path
                
                signatures_data.append({
                    'page': sig['page'],
                    'x': sig['x'],
                    'y': sig['y'],
                    'width': sig['w'],
                    'height': sig['h'],
                    'image_path': img_path
                })
            
            PDFSigner.add_multiple_signatures(target_pdf, output_path, signatures_data)
            
            messagebox.showinfo("Éxito", "¡PDF firmado!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Fallo: {e}")
        finally:
            for tf in temp_files:
                if os.path.exists(tf):
                    os.remove(tf)

    def browse_cert(self):
        path = filedialog.askopenfilename(filetypes=[("Certificado", "*.p12 *.pfx")])
        if path:
            self.cert_entry.delete(0, "end")
            self.cert_entry.insert(0, path)

    def sign_digital(self):
        pdf_files = self.file_list.get_files()
        if not pdf_files: return
        
        cert_path = self.cert_entry.get()
        password = self.pass_entry.get()
        
        if not cert_path or not os.path.exists(cert_path):
            messagebox.showwarning("Error", "Por favor, seleccione un archivo de certificado válido.")
            return

        try:
            for pdf_path in pdf_files:
                output_path = filedialog.asksaveasfilename(
                    initialfile=f"signed_digital_{os.path.basename(pdf_path)}",
                    defaultextension=".pdf",
                    filetypes=[("Archivos PDF", "*.pdf")]
                )
                if not output_path: continue
                
                PDFSigner.sign_digital(pdf_path, output_path, cert_path, password)
                
            messagebox.showinfo("Éxito", "¡PDF firmado digitalmente!")
            
        except ImportError:
             messagebox.showerror("Error", "Bibliotecas de firma digital (pyHanko) no encontradas.")
        except Exception as e:
             messagebox.showerror("Error", f"Error al firmar: {str(e)}")

    def handle_dropped_files(self, files):
        valid = [f for f in files if f.lower().endswith('.pdf')]
        for f in valid:
             self.file_list.add_file(f)
             
        if valid:
             self.open_in_viewer(valid[0])
        return True

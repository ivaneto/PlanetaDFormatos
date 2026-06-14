import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
from app.gui.components import dialogs as messagebox
from app.gui.pages.base_page import BasePage
from app.core.pdf_editor import PDFEditorBackend
from app.gui.theme import Theme
import io
from PIL import Image, ImageTk
import fitz # PyMuPDF
import uuid

class RedactPage(BasePage):
    def create_widgets(self):
        self.backend = PDFEditorBackend()
        self.current_pdf_path = None
        self.doc = None
        self.current_page_idx = 0
        self.tk_img = None 
        self.images_cache = []
        self.zoom_level = 1.0
        
        self.page_draw_data = {} # { page_idx: { uid: diccionario_de_datos } }
        self.selected_item_ids = set() # Conjunto de UUIDs para selección múltiple
        self.drag_data = {"x": 0, "y": 0, "item": None, "mode": None}
        self.tool_mode = "marker" # Herramienta predeterminada
        self.current_draw_id = None
        self.last_x = 0
        self.last_y = 0
        
        # Centrado
        self.offset_x = 0
        self.offset_y = 0
        
        # Selección de texto
        self.page_chars = []
        self.selection_start_idx = None
        self.selection_end_idx = None
         
        # Deshacer/Rehacer
        self.undo_stack = [] # Lista de acciones
        self.redo_stack = []
        
        # --- Barra de herramientas ---
        self.toolbar = ctk.CTkFrame(self.content_frame, height=50, fg_color=Theme.CARD_BG_N3)
        self.toolbar.pack(fill="x", side="top")
        
        self.create_toolbar_buttons()
        
        # --- Lienzo ---
        self.canvas_container = ctk.CTkFrame(self.content_frame, fg_color="gray90")
        self.canvas_container.pack(fill="both", expand=True)
        
        self.canvas = tk.Canvas(self.canvas_container, bg="gray80", highlightthickness=0)
        
        self.v_scroll = ctk.CTkScrollbar(self.canvas_container, command=self.canvas.yview)
        self.h_scroll = ctk.CTkScrollbar(self.canvas_container, orientation="horizontal", command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)
        
        self.v_scroll.pack(side="right", fill="y")
        self.h_scroll.pack(side="bottom", fill="x")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Eventos
        self.canvas.bind("<ButtonPress-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<Motion>", self.on_mouse_move)
        
        # Eventos de teclado
        self.canvas.bind("<Delete>", self.on_key_delete)
        self.canvas.bind("<BackSpace>", self.on_key_delete)

        self.show_welcome_message()

    def show_welcome_message(self):
        self.canvas.delete("all")
        self.canvas.create_text(400, 300, text="Abre un PDF para comenzar a censurar", font=("Arial", 20), fill="gray")

    def create_toolbar_buttons(self):
        # Operaciones de archivo
        btn_open = ctk.CTkButton(self.toolbar, text="📂", width=40, height=30, command=self.select_file)
        btn_open.pack(side="left", padx=5, pady=5)
        
        btn_save = ctk.CTkButton(self.toolbar, text="💾", width=40, height=30, fg_color=Theme.SUCCESS, command=self.save_redactions)
        btn_save.pack(side="left", padx=5, pady=5)
        
        tk.Frame(self.toolbar, width=1, bg="gray50").pack(side="left", fill="y", padx=5, pady=10)
        
        # Herramientas deshacer/rehacer
        self.btn_undo = ctk.CTkButton(self.toolbar, text="↩️", width=40, height=30, command=self.undo_action)
        self.btn_undo.pack(side="left", padx=2)
        
        self.btn_redo = ctk.CTkButton(self.toolbar, text="↪️", width=40, height=30, command=self.redo_action)
        self.btn_redo.pack(side="left", padx=2)
         
        tk.Frame(self.toolbar, width=1, bg="gray50").pack(side="left", fill="y", padx=5, pady=10)
        
        # Navegación
        self.btn_prev = ctk.CTkButton(self.toolbar, text="<", width=30, height=30, command=self.prev_page)
        self.btn_prev.pack(side="left", padx=2)
        self.lbl_page = ctk.CTkLabel(self.toolbar, text="0/0", width=60)
        self.lbl_page.pack(side="left", padx=2)
        self.btn_next = ctk.CTkButton(self.toolbar, text=">", width=30, height=30, command=self.next_page)
        self.btn_next.pack(side="left", padx=2)

        # Ir a página
        self.entry_page = ctk.CTkEntry(self.toolbar, width=40, height=30, placeholder_text="#")
        self.entry_page.pack(side="left", padx=5)
        self.entry_page.bind("<Return>", lambda event: self.go_to_page())
        
        self.btn_go = ctk.CTkButton(self.toolbar, text="Ir", width=30, height=30, command=self.go_to_page)
        self.btn_go.pack(side="left", padx=2)
        
        tk.Frame(self.toolbar, width=1, bg="gray50").pack(side="left", fill="y", padx=5, pady=10)

        # Zoom
        self.btn_zoom_out = ctk.CTkButton(self.toolbar, text="🔍-", width=30, height=30, command=self.zoom_out)
        self.btn_zoom_out.pack(side="left", padx=2)
        self.btn_zoom_in = ctk.CTkButton(self.toolbar, text="🔍+", width=30, height=30, command=self.zoom_in)
        self.btn_zoom_in.pack(side="left", padx=2)
        
        tk.Frame(self.toolbar, width=1, bg="gray50").pack(side="left", fill="y", padx=5, pady=10)
        
        # Herramientas
        self.btn_hand = ctk.CTkButton(self.toolbar, text="🖐️", width=40, height=30, 
                                      fg_color="transparent", border_width=1,
                                      command=lambda: self.set_tool("hand"))
        self.btn_hand.pack(side="left", padx=5)
        
        # Herramienta marcador
        self.btn_marker = ctk.CTkButton(self.toolbar, text="🖍️", width=40, height=30,
                                        fg_color="black", text_color="white", hover_color="#333",
                                        command=lambda: self.set_tool("marker"))
        self.btn_marker.pack(side="left", padx=5)

        # Herramienta rectángulo
        self.btn_rect = ctk.CTkButton(self.toolbar, text="⬛", width=40, height=30,
                                      fg_color="transparent", border_width=1, text_color="black",
                                      command=lambda: self.set_tool("rect"))
        self.btn_rect.pack(side="left", padx=5)

        # Botón para eliminar selección
        self.btn_del_sel = ctk.CTkButton(self.toolbar, text="❌", width=40, height=30,
                                        fg_color="transparent", hover_color=Theme.DANGER_HOVER, text_color=Theme.DANGER, 
                                        command=self.delete_selected_manual)
        self.btn_del_sel.pack(side="left", padx=5)

        self.btn_clear = ctk.CTkButton(self.toolbar, text="🗑️", width=40, height=30,
                                        fg_color="transparent", hover_color=Theme.DANGER_HOVER, text_color=Theme.DANGER,
                                        font=("Arial", 16), command=self.clear_page)
        self.btn_clear.pack(side="left", padx=5)

    def select_file(self):
        path = filedialog.askopenfilename(filetypes=[("Archivos PDF", "*.pdf")])
        if path:
            self.load_pdf(path)

    def load_pdf(self, path):
        self.current_pdf_path = path
        try:
            # Cerrar el documento previo para liberar memoria y el bloqueo del archivo.
            if self.doc:
                try:
                    self.doc.close()
                except Exception:
                    pass
            self.doc = fitz.open(path)
            self.current_page_idx = 0
            self.page_draw_data = {} 
            self.render_page()
            self.set_tool("marker")
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar PDF: {e}")

    def render_page(self):
        if not self.doc: return
        self.canvas.delete("all")
        self.selected_item_ids = set()
        
        page = self.doc[self.current_page_idx]
        pix = page.get_pixmap(matrix=fitz.Matrix(self.zoom_level, self.zoom_level))
        img_data = pix.tobytes("png")
        pil_img = Image.open(io.BytesIO(img_data))
        self.tk_img = ImageTk.PhotoImage(pil_img)
        
        self.canvas.update_idletasks()
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        iw, ih = self.tk_img.width(), self.tk_img.height()
        
        self.offset_x = max(0, (cw - iw) // 2)
        self.offset_y = max(0, (ch - ih) // 2)
        
        self.canvas.create_image(self.offset_x, self.offset_y, image=self.tk_img, anchor="nw", tags="bg")
        self.canvas.configure(scrollregion=(0, 0, max(iw, cw), max(ih, ch)))
        
        # Analizar caracteres para selección precisa
        self._parse_page_chars(page)
        
        # Restaurar censuras
        if self.current_page_idx in self.page_draw_data:
            self.restore_drawings()
        
        self.lbl_page.configure(text=f"{self.current_page_idx + 1}/{len(self.doc)}")

    def _parse_page_chars(self, page):
        self.page_chars = []
        raw = page.get_text("rawdict")
        line_idx = 0
        for block in raw.get("blocks", []):
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    for char in span.get("chars", []):
                        self.page_chars.append({
                            "bbox": char["bbox"],
                            "c": char["c"],
                            "line": line_idx
                        })
                line_idx += 1

    def get_char_at_pos(self, x, y):
        cx = self.canvas.canvasx(x)
        cy = self.canvas.canvasy(y)
        pdf_x = (cx - self.offset_x) / self.zoom_level
        pdf_y = (cy - self.offset_y) / self.zoom_level
        
        best_idx = None
        min_dist = 200
        
        for i, char in enumerate(self.page_chars):
            bx0, by0, bx1, by1 = char["bbox"]
            if bx0 <= pdf_x <= bx1 and by0 <= pdf_y <= by1:
                return i
            # Proximidad
            d = (pdf_x - (bx0+bx1)/2)**2 + (pdf_y - (by0+by1)/2)**2
            if d < min_dist:
                min_dist = d
                best_idx = i
        return best_idx

    def update_text_selection_visuals(self):
        self.canvas.delete("text_sel_marker")
        if self.selection_start_idx is None or self.selection_end_idx is None: return
        
        start, end = sorted((self.selection_start_idx, self.selection_end_idx))
        subset = self.page_chars[start:end+1]
        
        rects = []
        cur_rect = None
        cur_line = -1
        
        for char in subset:
            if char['line'] != cur_line:
                if cur_rect: rects.append(cur_rect)
                cur_rect = list(char['bbox'])
                cur_line = char['line']
            else:
                cur_rect[0] = min(cur_rect[0], char['bbox'][0])
                cur_rect[1] = min(cur_rect[1], char['bbox'][1])
                cur_rect[2] = max(cur_rect[2], char['bbox'][2])
                cur_rect[3] = max(cur_rect[3], char['bbox'][3])
        if cur_rect: rects.append(cur_rect)
        
        scale = self.zoom_level
        ox, oy = self.offset_x, self.offset_y
        
        for r in rects:
            self.canvas.create_rectangle(
                r[0]*scale + ox, r[1]*scale + oy,
                r[2]*scale + ox, r[3]*scale + oy,
                fill="black", stipple="gray50", outline="", tags="text_sel_marker"
            )

    def restore_drawings(self):
        scale = self.zoom_level
        ox, oy = self.offset_x, self.offset_y
        page_data = self.page_draw_data.get(self.current_page_idx, {})
        
        for uid, item in page_data.items():
            if item['type'] == 'redact_rect':
                x0, y0, x1, y1 = item['rect']
                self.canvas.create_rectangle(x0*scale + ox, y0*scale + oy, x1*scale + ox, y1*scale + oy,
                                             fill="black", outline="black", tags=("redaction", uid))

    def set_tool(self, tool):
        self.tool_mode = tool
        self.deselect() # Limpiar selección al cambiar de herramienta
        
        # Restablecer estilos
        self.btn_marker.configure(fg_color="transparent", text_color="black")
        self.btn_rect.configure(fg_color="transparent", text_color="black")
        self.btn_hand.configure(fg_color="transparent", text_color="black")
        
        if tool == "marker":
            self.canvas.config(cursor="xterm")
            self.btn_marker.configure(fg_color="black", text_color="white")
        elif tool == "rect":
            self.canvas.config(cursor="crosshair")
            self.btn_rect.configure(fg_color="black", text_color="white")
        elif tool == "hand":
            self.canvas.config(cursor="fleur")
            self.btn_hand.configure(fg_color=Theme.PRIMARY, text_color="white")

    def on_canvas_click(self, event):
        self.canvas.focus_set()
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self.last_x, self.last_y = x, y
        
        # Lógica de selección múltiple
        is_ctrl = (event.state & 0x0004) != 0

        if self.tool_mode == "marker":
            # Selección de texto
            idx = self.get_char_at_pos(event.x, event.y)
            if idx is not None:
                self.selection_start_idx = idx
                self.selection_end_idx = idx
                self.update_text_selection_visuals()
            else:
                self.selection_start_idx = None
                self.canvas.delete("text_sel_marker")
            
        elif self.tool_mode == "rect":
            # Modo de Rectángulo: Comenzar a dibujar el rectángulo
            self.current_draw_id = self.canvas.create_rectangle(x, y, x, y, fill="black", outline="black", stipple="gray50")
            if not is_ctrl:
                self.deselect()
            
        elif self.tool_mode == "hand":
            self.canvas.scan_mark(event.x, event.y)
        else:
            self.select_item_at(x, y, toggle=is_ctrl)

    def on_key_delete(self, event):
        self.delete_selected_manual()

    def on_canvas_drag(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        if self.tool_mode == "marker":
            if self.selection_start_idx is not None:
                idx = self.get_char_at_pos(event.x, event.y)
                if idx is not None:
                    self.selection_end_idx = idx
                    self.update_text_selection_visuals()
            
        elif self.tool_mode == "rect":
            if self.current_draw_id:
                self.canvas.coords(self.current_draw_id, self.last_x, self.last_y, x, y)
                
        elif self.tool_mode == "hand":
            self.canvas.scan_dragto(event.x, event.y, gain=1)

    def check_text_under_cursor(self, x, y):
        hit_existing = False
        scale = self.zoom_level
        px, py = x / scale, y / scale

        if self.current_page_idx in self.page_draw_data:
            for uid, data in self.page_draw_data[self.current_page_idx].items():
                if data['type'] == 'redact_rect':
                    r = data['rect']
                    if r[0] <= px <= r[2] and r[1] <= py <= r[3]:
                        if uid not in self.selected_item_ids:
                            self.selected_item_ids.add(uid)
                            self.draw_selection_box()
                        hit_existing = True

        if not self.doc:
            return
        page = self.doc[self.current_page_idx]

        words = page.get_text("words")
        for w in words:
            r = fitz.Rect(w[:4])
            if (px, py) in r:
                
                if hit_existing:
                     pass 
                else:
                    self.apply_redaction(r)
                break
    
    def on_canvas_release(self, event):
        if self.tool_mode == "marker":
             # Convertir selección de texto en rectángulos de censura
             self.convert_text_selection_to_redaction()
             self.selection_start_idx = None
             self.selection_end_idx = None
             self.canvas.delete("text_sel_marker")

        if self.tool_mode == "rect" and self.current_draw_id:
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)
            scale = self.zoom_level
            ox, oy = self.offset_x, self.offset_y
            
            x0, y0 = min(self.last_x, x), min(self.last_y, y)
            x1, y1 = max(self.last_x, x), max(self.last_y, y)
            
            # Ajustar a coordenadas PDF, quitando offset
            pdf_x0 = (x0 - ox) / scale
            pdf_y0 = (y0 - oy) / scale
            pdf_x1 = (x1 - ox) / scale
            pdf_y1 = (y1 - oy) / scale
            
            # Eliminar el rectángulo de arrastre temporal
            self.canvas.delete(self.current_draw_id)
            self.current_draw_id = None
            
            if abs(x1-x0) < 2 or abs(y1-y0) < 2:
                return

            uid = str(uuid.uuid4())
            data = {
                "type": "redact_rect",
                "rect": (pdf_x0, pdf_y0, pdf_x1, pdf_y1),
                "uuid": uid
            }
            
            # Crear rectángulo permanente
            self.canvas.create_rectangle(pdf_x0*scale + ox, pdf_y0*scale + oy,
                                         pdf_x1*scale + ox, pdf_y1*scale + oy,
                                         fill="black", outline="black", tags=("redaction", uid))

            self.save_draw_data_item(uid, data)
            
            # Seleccionar el nuevo rectángulo
            self.selected_item_ids.add(uid)
            self.draw_selection_box()

    def convert_text_selection_to_redaction(self):
        if self.selection_start_idx is None or self.selection_end_idx is None: return
        start, end = sorted((self.selection_start_idx, self.selection_end_idx))
        subset = self.page_chars[start:end+1]
        
        rects = []
        cur_rect = None
        cur_line = -1
        
        for char in subset:
            if char['line'] != cur_line:
                if cur_rect: rects.append(cur_rect)
                cur_rect = list(char['bbox'])
                cur_line = char['line']
            else:
                cur_rect[0] = min(cur_rect[0], char['bbox'][0])
                cur_rect[1] = min(cur_rect[1], char['bbox'][1])
                cur_rect[2] = max(cur_rect[2], char['bbox'][2])
                cur_rect[3] = max(cur_rect[3], char['bbox'][3])
        if cur_rect: rects.append(cur_rect)
        
        scale = self.zoom_level
        ox, oy = self.offset_x, self.offset_y
        
        # Agrupar rectángulos en un lote de deshacer
        items_batch = []
        
        for r in rects:
            uid = str(uuid.uuid4())
            data = {
                "type": "redact_rect",
                "rect": (r[0], r[1], r[2], r[3]),
                "uuid": uid
            }
            # Dibujar
            self.canvas.create_rectangle(
                r[0]*scale + ox, r[1]*scale + oy,
                r[2]*scale + ox, r[3]*scale + oy,
                fill="black", outline="black", tags=("redaction", uid)
            )
            
            # Guardar en memoria
            if self.current_page_idx not in self.page_draw_data:
                self.page_draw_data[self.current_page_idx] = {}
            self.page_draw_data[self.current_page_idx][uid] = data
            
            items_batch.append((uid, data))
            
        if items_batch:
            self.push_undo_group(self.current_page_idx, items_batch, "add")

    def save_draw_data_item(self, uid, data):
        if self.current_page_idx not in self.page_draw_data:
            self.page_draw_data[self.current_page_idx] = {}
        self.page_draw_data[self.current_page_idx][uid] = data
        self.push_undo(self.current_page_idx, uid, data, "add")

    def apply_redaction(self, rect):
        scale = self.zoom_level
        x0, y0, x1, y1 = rect.x0, rect.y0, rect.x1, rect.y1
        
        uid = str(uuid.uuid4())
        
        # Dibujar con la etiqueta 'redaction' Y el uid
        draw_id = self.canvas.create_rectangle(x0*scale, y0*scale, x1*scale, y1*scale,
                                               fill="black", outline="black", tags=("redaction", uid))
        
        data = {
            "type": "redact_rect",
            "rect": (x0, y0, x1, y1),
            "uuid": uid
        }
        
        if self.current_page_idx not in self.page_draw_data:
            self.page_draw_data[self.current_page_idx] = {}
        
        self.page_draw_data[self.current_page_idx][uid] = data
        
        # Añadir al lote si existe, de lo contrario, inserción individual
        if hasattr(self, 'marker_batch') and self.marker_batch is not None:
             self.marker_batch.append((uid, data))
        else:
             self.push_undo(self.current_page_idx, uid, data, "add")
             
        # Seleccionar el nuevo elemento
        self.selected_item_ids.add(uid)
        self.draw_selection_box()

    def push_undo(self, page_idx, item_id, item_data, action_type="add"):
        # Inserción de acción única
        action = {
            "page_idx": page_idx,
            "items": [(item_id, item_data)], # Lista de elementos
            "type": action_type
        }
        self.undo_stack.append(action)
        self.redo_stack.clear()
        
    def push_undo_group(self, page_idx, items_list, action_type="add"):
        if not items_list: return
        action = {
            "page_idx": page_idx,
            "items": items_list,
            "type": action_type
        }
        self.undo_stack.append(action)
        self.redo_stack.clear()

    def start_marker_batch(self):
        self.marker_batch = []

    def finish_marker_batch(self):
        if hasattr(self, 'marker_batch') and self.marker_batch:
            self.push_undo_group(self.current_page_idx, self.marker_batch, "add")
            self.marker_batch = []

    def undo_action(self):
        if not self.undo_stack: return
        
        action = self.undo_stack.pop()
        page_idx = action["page_idx"]
        action_type = action["type"]
        items = action["items"]
        
        if action_type == "add":
            # Reversa: Eliminar todos los elementos de este grupo
            for uid, item_data in items:
                # Eliminar de los datos
                if page_idx in self.page_draw_data and uid in self.page_draw_data[page_idx]:
                     del self.page_draw_data[page_idx][uid]
                
                # Eliminar de la parte visual si está en la página actual
                if page_idx == self.current_page_idx:
                    self.canvas.delete(uid) 
            
            self.deselect()
            self.redo_stack.append(action)
            
        elif action_type == "delete":
            if page_idx not in self.page_draw_data:
                self.page_draw_data[page_idx] = {}
                
            for uid, item_data in items:
                self.page_draw_data[page_idx][uid] = item_data
            
            self.redo_stack.append(action)
            if page_idx == self.current_page_idx:
                self.restore_drawings()

    def redo_action(self):
        if not self.redo_stack: return
        
        action = self.redo_stack.pop()
        page_idx = action["page_idx"]
        action_type = action["type"]
        items = action["items"]
        
        if action_type == "add":
            if page_idx not in self.page_draw_data:
                self.page_draw_data[page_idx] = {}
            
            for uid, item_data in items:
                self.page_draw_data[page_idx][uid] = item_data
            
            self.undo_stack.append(action)
            if page_idx == self.current_page_idx:
                self.restore_drawings()
                
        elif action_type == "delete":
            if page_idx in self.page_draw_data:
                for uid, item_data in items:
                    if uid in self.page_draw_data[page_idx]:
                        del self.page_draw_data[page_idx][uid]
                        
            # Eliminar visual
            if page_idx == self.current_page_idx:
                for uid, _ in items:
                    self.canvas.delete(uid)
                    
            self.undo_stack.append(action)

    def select_item_at(self, x, y, toggle=False):
        # Permitir seleccionar censuras existentes para eliminarlas manualmente
        item = self.canvas.find_closest(x, y, halo=5)
        uid_found = None
        
        if item:
            tags = self.canvas.gettags(item[0])
            if "redaction" in tags:
                # Buscar la etiqueta UUID.
                for t in tags:
                    if t != "current" and t != "redaction" and t != "sel_box":
                        uid_found = t
                        break
        
        if uid_found:
            if toggle:
                if uid_found in self.selected_item_ids:
                    self.selected_item_ids.remove(uid_found)
                else:
                    self.selected_item_ids.add(uid_found)
            else:
                self.selected_item_ids = {uid_found}
            
            self.draw_selection_box()
        else:
            if not toggle:
                self.deselect()

    def deselect(self):
        self.selected_item_ids = set()
        self.canvas.delete("sel_box")

    def draw_selection_box(self):
        self.canvas.delete("sel_box")
        if not self.selected_item_ids: return
        
        for uid in self.selected_item_ids:
            # Buscar elemento del lienzo por etiqueta
            items = self.canvas.find_withtag(uid)
            if items:
                bbox = self.canvas.bbox(items[0])
                if bbox:
                    self.canvas.create_rectangle(bbox[0]-2, bbox[1]-2, bbox[2]+2, bbox[3]+2, 
                                                 outline="red", width=2, tags="sel_box")

    def delete_selected_manual(self):
        if not self.selected_item_ids: return
        
        items_to_delete = []
        
        if self.current_page_idx in self.page_draw_data:
            page_data = self.page_draw_data[self.current_page_idx]
            
            # Crear una lista para evitar modificar el conjunto mientras se itera
            for uid in list(self.selected_item_ids):
                if uid in page_data:
                    items_to_delete.append((uid, page_data[uid]))
                    del page_data[uid]
                
                # Eliminación visual
                self.canvas.delete(uid)
        
        if items_to_delete:
            self.push_undo_group(self.current_page_idx, items_to_delete, "delete")
            
        self.deselect()

    def clear_page(self):
        if self.current_page_idx in self.page_draw_data:
            response = messagebox.askyesno("Confirmar", "¿Estás seguro de que deseas limpiar todas las censuras de esta página?")
            if response:
                del self.page_draw_data[self.current_page_idx]
                self.restore_drawings() 
                self.canvas.delete("redaction")
                self.canvas.delete("sel_box")
                self.selected_item_ids = set()
                self.undo_stack.clear() # Limpiar la pila de deshacer en la eliminación masiva
                self.redo_stack.clear()

    def prev_page(self):
        if self.doc and self.current_page_idx > 0:
            self.current_page_idx -= 1
            self.render_page()

    def next_page(self):
        if self.doc and self.current_page_idx < len(self.doc) - 1:
            self.current_page_idx += 1
            self.render_page()

    def go_to_page(self):
        if not self.doc: return
        try:
            val = self.entry_page.get()
            if not val: return
            page_num = int(val)
            if 1 <= page_num <= len(self.doc):
                self.current_page_idx = page_num - 1
                self.render_page()
                self.entry_page.delete(0, 'end')
            else:
                 messagebox.showwarning("Página Inválida", f"Ingrese un número entre 1 y {len(self.doc)}")
        except ValueError:
             messagebox.showwarning("Error", "Ingrese un número de página válido.")

    def zoom_in(self):
        self.zoom_level += 0.2
        self.render_page()

    def zoom_out(self):
        if self.zoom_level > 0.4:
            self.zoom_level -= 0.2
            self.render_page()
            
    def on_mouse_move(self, event):
        pass

    def save_redactions(self):
        # Guardar cambios
        if not self.current_pdf_path: return
        try:
            output_path = filedialog.asksaveasfilename(filetypes=[("Archivos PDF", "*.pdf")], defaultextension=".pdf")
            if not output_path: return
            
            doc_to_save = fitz.open(self.current_pdf_path)
            
            for page_idx, items in self.page_draw_data.items():
                if page_idx >= len(doc_to_save): continue
                page = doc_to_save[page_idx]
                
                for item in items.values():
                    if item['type'] == 'redact_rect':
                        rect = fitz.Rect(item['rect'])
                        page.add_redact_annot(rect, fill=(0, 0, 0))
                
                page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)
            
            doc_to_save.save(output_path)
            doc_to_save.close()
            
            messagebox.showinfo("Éxito", "¡PDF censurado guardado con éxito!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar: {e}")

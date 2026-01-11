import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from app.gui.pages.base_page import BasePage
from app.core.pdf_editor import PDFEditorBackend
from app.gui.theme import Theme
import io
from PIL import Image, ImageTk
import fitz # PyMuPDF

class EditPdfPage(BasePage):
    def create_widgets(self):
        self.backend = PDFEditorBackend()
        self.current_pdf_path = None
        self.images_cache = [] 
        self.zoom_level = 1.0
        self.tool_mode = "select" 
        self.current_draw_id = None
        self.page_draw_data = {}
        self.doc = None
        self.current_page_idx = 0
        self.tk_img = None 
        self.selected_item_id = None
        self.drag_data = {"x": 0, "y": 0, "item": None}
        
        # Centrar vista
        self.offset_x = 0
        self.offset_y = 0
        
        # Selección de Texto y Búsqueda
        self.page_chars = []
        self.selection_start_idx = None
        self.selection_end_idx = None
        self.selected_text_content = ""
        
        self.search_results = []
        self.current_search_idx = -1
        self.search_term = ""

        # --- Barra de herramientas ---
        self.toolbar = ctk.CTkFrame(self.content_frame, height=50, fg_color=Theme.CARD_BG_N2)
        self.toolbar.pack(fill="x", side="top")
        
        self.create_toolbar_buttons()
        
        # --- Área Principal ---
        self.canvas_container = ctk.CTkFrame(self.content_frame, fg_color="gray90")
        self.canvas_container.pack(fill="both", expand=True)
        
        self.canvas = tk.Canvas(self.canvas_container, bg="gray80", highlightthickness=0)
        
        # Barras de desplazamiento (Scrollbars)
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
        self.canvas.bind("<Double-Button-1>", self.on_canvas_double_click)
        self.canvas.bind("<Motion>", self.on_mouse_move)
        
        # Atajos de teclado
        self.canvas.bind("<Control-c>", lambda e: self.copy_selection())
        self.canvas.bind("<Delete>", lambda e: self.delete_selected_item())
        self.canvas.focus_set()
        
        self.show_welcome_message()

    def create_toolbar_buttons(self):
        # Archivo, Navegación, Zoom y Búsqueda
        row1 = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        row1.pack(side="top", fill="x", padx=2, pady=2)
        
        ctk.CTkButton(row1, text="📂", width=30, command=self.select_file).pack(side="left", padx=2)
        ctk.CTkButton(row1, text="💾", width=30, command=self.save_file).pack(side="left", padx=2)
        
        tk.Frame(row1, width=1, bg="gray50").pack(side="left", fill="y", padx=5)
        
        self.btn_prev = ctk.CTkButton(row1, text="<", width=30, command=self.prev_page)
        self.btn_prev.pack(side="left", padx=2)
        self.lbl_page = ctk.CTkLabel(row1, text="0/0", width=50)
        self.lbl_page.pack(side="left", padx=2)
        self.btn_next = ctk.CTkButton(row1, text=">", width=30, command=self.next_page)
        self.btn_next.pack(side="left", padx=2)
        
        tk.Frame(row1, width=1, bg="gray50").pack(side="left", fill="y", padx=5)
        
        ctk.CTkButton(row1, text="🔍+", width=30, command=self.zoom_in).pack(side="left", padx=2)
        ctk.CTkButton(row1, text="🔍-", width=30, command=self.zoom_out).pack(side="left", padx=2)
        
        tk.Frame(row1, width=1, bg="gray50").pack(side="left", fill="y", padx=5)
        
        # Barra de Búsqueda
        self.entry_search = ctk.CTkEntry(row1, width=120, placeholder_text="Buscar...")
        self.entry_search.pack(side="left", padx=2)
        self.entry_search.bind("<Return>", lambda e: self.perform_search())
        ctk.CTkButton(row1, text="🔍", width=30, command=self.perform_search).pack(side="left", padx=2)
        ctk.CTkButton(row1, text="⬆️", width=30, command=self.prev_match).pack(side="left", padx=1)
        ctk.CTkButton(row1, text="⬇️", width=30, command=self.next_match).pack(side="left", padx=1)
        self.lbl_search_status = ctk.CTkLabel(row1, text="")
        self.lbl_search_status.pack(side="left", padx=5)

        # Herramientas
        row2 = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        row2.pack(side="top", fill="x", padx=2, pady=2)
        
        self.btn_hand = ctk.CTkButton(row2, text="🖐️", width=40, command=lambda: self.set_tool("hand"))
        self.btn_hand.pack(side="left", padx=2)
        
        self.btn_select = ctk.CTkButton(row2, text="↖️", width=40, command=lambda: self.set_tool("select"))
        self.btn_select.pack(side="left", padx=2)
        
        # Herramientas de Edición
        tk.Frame(row2, width=1, bg="gray50").pack(side="left", fill="y", padx=5)
        
        self.btn_text = ctk.CTkButton(row2, text="T", width=40, command=lambda: self.set_tool("text"))
        self.btn_text.pack(side="left", padx=2)
        
        self.btn_pencil = ctk.CTkButton(row2, text="✏️", width=40, command=lambda: self.set_tool("pencil"))
        self.btn_pencil.pack(side="left", padx=2)
        
        self.btn_highlight = ctk.CTkButton(row2, text="🖍️", width=40, command=lambda: self.set_tool("highlight"))
        self.btn_highlight.pack(side="left", padx=2)
        
        self.btn_whiteout = ctk.CTkButton(row2, text="⬜", width=40, command=lambda: self.set_tool("whiteout"))
        self.btn_whiteout.pack(side="left", padx=2)
        
        self.btn_image = ctk.CTkButton(row2, text="🖼️", width=40, command=lambda: self.set_tool("image"))
        self.btn_image.pack(side="left", padx=2)

        tk.Frame(row2, width=1, bg="gray50").pack(side="left", fill="y", padx=5)
        
        self.btn_delete = ctk.CTkButton(row2, text="🗑️", width=40, fg_color="darkred", hover_color="red", command=self.delete_selected_item)
        self.btn_delete.pack(side="left", padx=2)
        
        self.btn_replace = ctk.CTkButton(row2, text="🔄", width=40, fg_color="green", hover_color="darkgreen", command=self.replace_selected_text)
        self.btn_replace.pack(side="left", padx=2)

    def show_welcome_message(self):
        self.canvas.delete("all")
        self.canvas.create_text(400, 300, text="Abra un PDF para comenzar a editar", font=("Arial", 20), fill="gray")

    def select_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Archivos PDF", "*.pdf")])
        if filename:
            self.load_pdf(filename)

    def load_pdf(self, path):
        self.current_pdf_path = path
        try:
            self.doc = fitz.open(path)
            self.current_page_idx = 0
            self.page_draw_data = {} 
            self.search_results = []
            self.current_search_idx = -1
            self.render_page()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar PDF: {e}")

    def update_info(self):
        if self.doc:
            self.lbl_page.configure(text=f"{self.current_page_idx + 1}/{len(self.doc)}")

    def prev_page(self):
        if self.doc and self.current_page_idx > 0:
            self.current_page_idx -= 1
            self.render_page()

    def next_page(self):
        if self.doc and self.current_page_idx < len(self.doc) - 1:
            self.current_page_idx += 1
            self.render_page()

    def render_page(self):
        if not self.doc: return
        
        self.canvas.delete("all")
        self.selected_item_id = None
        self.drag_data["item"] = None
        
        page = self.doc[self.current_page_idx]
        
        # Renderizar Imagen de Fondo
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
        
        # Texto para Selección/Búsqueda
        self._parse_page_chars(page)
        
        # Dibujar Resaltados de Búsqueda
        self.draw_search_highlights()
        
        # Restaurar Dibujos Personalizados
        if self.current_page_idx in self.page_draw_data:
            self.restore_drawings()
            
        self.update_info()

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

    def restore_drawings(self):
        scale = self.zoom_level
        ox, oy = self.offset_x, self.offset_y
        
        page_data = self.page_draw_data.get(self.current_page_idx, {})
        new_page_data_map = {}
        self.images_cache = [] 
        
        for old_id, item in page_data.items():
            new_id = None
            if item['type'] == 'text':
                fsize = int(item.get('fontsize', 12) * scale)
                new_id = self.canvas.create_text(item['x']*scale + ox, item['y']*scale + oy, 
                                                 text=item['content'], 
                                                 font=("Arial", fsize), fill="black", anchor="nw")
            
            elif item['type'] == 'image':
                try:
                    pil_img = Image.open(item['path'])
                    w = int(item['width'] * scale)
                    h = int(item['height'] * scale)
                    pil_img = pil_img.resize((w, h), Image.Resampling.LANCZOS)
                    tk_img = ImageTk.PhotoImage(pil_img)
                    self.images_cache.append(tk_img)
                    new_id = self.canvas.create_image(item['x0']*scale + ox, item['y0']*scale + oy, image=tk_img, anchor="nw")
                except: pass
                
            elif item['type'] in ['rect', 'whiteout']:
                fill = "white" if item['type'] == 'whiteout' else ""
                outline = "white" if item['type'] == 'whiteout' else "red"
                wd = 0 if item['type'] == 'whiteout' else 2*scale
                new_id = self.canvas.create_rectangle(item['x0']*scale + ox, item['y0']*scale + oy,
                                                      item['x1']*scale + ox, item['y1']*scale + oy,
                                                      fill=fill, outline=outline, width=wd)
            
            elif item['type'] == 'pencil':
                # Desplazar puntos
                scaled_points = []
                for i in range(0, len(item['points']), 2):
                    scaled_points.append(item['points'][i] * scale + ox)
                    scaled_points.append(item['points'][i+1] * scale + oy)
                if len(scaled_points) > 2:
                    new_id = self.canvas.create_line(scaled_points, fill="red", width=2*scale, capstyle="round", smooth=True)

            elif item['type'] == 'highlight_annot':
                new_id = self.canvas.create_rectangle(item['x0']*scale + ox, item['y0']*scale + oy,
                                                      item['x1']*scale + ox, item['y1']*scale + oy,
                                                      fill="yellow", outline="", stipple="gray50")
            
            elif item['type'] == 'redact_annot':
                new_id = self.canvas.create_rectangle(item['x0']*scale + ox, item['y0']*scale + oy,
                                                      item['x1']*scale + ox, item['y1']*scale + oy,
                                                      fill="black", outline="red")
            
            elif item['type'] == 'replace':
                new_id = self.canvas.create_rectangle(item['x0']*scale + ox, item['y0']*scale + oy,
                                                      item['x1']*scale + ox, item['y1']*scale + oy,
                                                      fill="white", outline="green", width=2)
                self.canvas.create_text(item['x0']*scale + ox, item['y1']*scale + oy - 2,
                                        text=item['content'], font=("Arial", int(item.get('fontsize',12)*scale)),
                                        fill="green", anchor="sw")

            if new_id:
                new_page_data_map[new_id] = item
        
        self.page_draw_data[self.current_page_idx] = new_page_data_map

    def set_tool(self, tool_name):
        self.tool_mode = tool_name
        buttons = {
            "hand": self.btn_hand, "select": self.btn_select, "text": self.btn_text,
            "pencil": self.btn_pencil, "whiteout": self.btn_whiteout, 
            "highlight": self.btn_highlight, "image": self.btn_image
        }
        for name, btn in buttons.items():
            if name == tool_name: btn.configure(fg_color=Theme.PRIMARY)
            else: btn.configure(fg_color="transparent")
        
        cursors = { "hand": "fleur", "text": "xterm", "select": "arrow", 
                   "highlight": "xterm", "whiteout": "crosshair" }
        self.canvas.config(cursor=cursors.get(tool_name, "arrow"))

    # --- Eventos del Ratón ---
    def on_canvas_click(self, event):
        self.canvas.focus_set()
        self.last_x = self.canvas.canvasx(event.x)
        self.last_y = self.canvas.canvasy(event.y)
        
        if self.tool_mode == "hand":
            self.canvas.scan_mark(event.x, event.y)
            return

        if self.tool_mode == "select":
            # Comprobar manejadores (handles)
            clicked_items = self.canvas.find_overlapping(self.last_x-5, self.last_y-5, self.last_x+5, self.last_y+5)
            for item_id in clicked_items:
                tags = self.canvas.gettags(item_id)
                if "resize_handle" in tags:
                    self.drag_data["mode"] = "resize"
                    self.drag_data["item"] = self.selected_item_id
                    for t in tags: 
                        if t in ["nw", "ne", "sw", "se"]: self.drag_data["handle"] = t
                    return
            
            current_data = self.page_draw_data.get(self.current_page_idx, {})
            clean_items = [i for i in clicked_items if i in current_data]
            if clean_items:
                selected = clean_items[-1] 
                self.selected_item_id = selected
                self.drag_data["item"] = selected
                self.drag_data["mode"] = "move"
                self.drag_data["x"] = self.last_x
                self.drag_data["y"] = self.last_y
                self.update_selection_box()
                
                # Limpiar la selección de texto
                self.selection_start_idx = None
                self.selection_end_idx = None
                self.selected_text_content = ""
                self.canvas.delete("text_selection")
                return
        
        idx = self.get_char_at_pos(event.x, event.y)
        if idx is not None:
            # Se hizo clic en texto
            self.selection_start_idx = idx
            self.selection_end_idx = idx
            self.update_text_selection_visuals()
            self.selected_item_id = None # Deseleccionar objeto
            self.update_selection_box() # Limpiar cuadro
        else:
            if self.tool_mode in ["text"]:
                self.create_text_input(self.last_x, self.last_y)
            elif self.tool_mode in ["image"]:
                self.insert_image(self.last_x, self.last_y)
            elif self.tool_mode == "pencil":
                self.start_pencil(self.last_x, self.last_y)
            elif self.tool_mode == "whiteout":
                self.start_rect(self.last_x, self.last_y, "whiteout")
            else:
                # Limpiar todas las selecciones
                self.selection_start_idx = None
                self.canvas.delete("text_selection")
                self.selected_item_id = None
                self.update_selection_box()

    def on_canvas_drag(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        if self.tool_mode == "hand":
            self.canvas.scan_dragto(event.x, event.y, gain=1)
            return

        if self.drag_data["item"] and self.tool_mode == "select":
            self.handle_item_drag(x, y)
            return

        # Arrastre de Selección de Texto
        if self.selection_start_idx is not None:
            idx = self.get_char_at_pos(event.x, event.y)
            if idx is not None:
                self.selection_end_idx = idx
                self.update_text_selection_visuals()
            return
            
        # Arrastre de Dibujo
        if self.tool_mode == "pencil":
            self.continue_pencil(x, y)
        elif self.tool_mode in ["whiteout"]:
            self.continue_rect(x, y)

    def on_canvas_release(self, event):
        self.drag_data["item"] = None
        self.drag_data["mode"] = None
        
        # Si es la herramienta de Resaltado y el texto está seleccionado -> Aplicar Resaltado
        if self.tool_mode == "highlight" and self.selection_start_idx is not None and self.selection_end_idx is not None:
            self.apply_highlight_to_selection()
            self.selection_start_idx = None
            self.selection_end_idx = None
            self.canvas.delete("text_selection")

        # Finalizar Dibujo
        if self.current_draw_id:
             self.finish_drawing()

    def on_canvas_double_click(self, event):
        if self.tool_mode == "select":
            item = self.canvas.find_closest(self.canvas.canvasx(event.x), self.canvas.canvasy(event.y), halo=5)
            if item:
                item_id = item[0]
                current_data = self.page_draw_data.get(self.current_page_idx, {})
                if item_id in current_data:
                    data = current_data[item_id]
                    if data['type'] == 'text':
                         self.edit_text_item(item_id, data)

    def edit_text_item(self, item_id, data):
        entry = tk.Entry(self.canvas, font=("Arial", data.get('fontsize', 12)), fg="black", bd=1, relief="solid")
        entry.insert(0, data['content'])
        
        # Posición en las coordenadas PDF actuales -> Coordenadas de pantalla
        scale = self.zoom_level
        ox, oy = self.offset_x, self.offset_y
        sx = data['x'] * scale + ox
        sy = data['y'] * scale + oy
        
        window_id = self.canvas.create_window(sx, sy, window=entry, anchor="nw")
        entry.focus()
        entry.selection_range(0, tk.END)
        
        def finalize_edit(event=None):
            new_text = entry.get()
            if new_text:
                data['content'] = new_text
                self.restore_drawings()
            else:
                # Texto vacío -> Eliminar
                del self.page_draw_data[self.current_page_idx][item_id]
                self.canvas.delete(item_id)
                self.canvas.delete("selection_box")
                
            self.canvas.delete(window_id)
            
        entry.bind("<Return>", finalize_edit)
        entry.bind("<FocusOut>", finalize_edit)

    # --- Lógica de Selección de Texto ---
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
        self.canvas.delete("text_selection")
        if self.selection_start_idx is None or self.selection_end_idx is None: return
        
        start, end = sorted((self.selection_start_idx, self.selection_end_idx))
        subset = self.page_chars[start:end+1]
        
        # Recopilar Texto
        chars = [c['c'] for c in subset]
        self.selected_text_content = "".join(chars)
        
        # Dibujar Rectángulos
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
                fill="blue", stipple="gray50", outline="", tags="text_selection"
            )
        self.canvas.tag_raise("text_selection", "bg")

    def apply_highlight_to_selection(self):
        if self.selection_start_idx is None: return
        start, end = sorted((self.selection_start_idx, self.selection_end_idx))
        subset = self.page_chars[start:end+1]
        if not subset: return

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

        # Guardar cada rectángulo como un resaltado
        for r in rects:
            import uuid
            item_id = self.canvas.create_rectangle(0,0,0,0) # Marcador de posición
            self.save_draw_data(item_id, {
                "type": "highlight_annot",
                "x0": r[0], "y0": r[1], "x1": r[2], "y1": r[3]
            })
        self.restore_drawings()

    def copy_selection(self):
        if self.selected_text_content:
            self.clipboard_clear()
            self.clipboard_append(self.selected_text_content)

    def replace_selected_text(self):
        if not self.selected_text_content or self.selection_start_idx is None:
            messagebox.showwarning("Reemplazar", "Por favor, seleccione el texto a reemplazar primero.")
            return
            
        new_text = ctk.CTkInputDialog(text="Ingrese el texto de reemplazo:", title="Reemplazar texto").get_input()
        if new_text is None: return # Cancelado
        
        # Calcular el cuadro delimitador del texto seleccionado
        start, end = sorted((self.selection_start_idx, self.selection_end_idx))
        subset = self.page_chars[start:end+1]
        if not subset: return

        # Combinar cuadros
        count = 0
        min_x, min_y, max_x, max_y = float('inf'), float('inf'), float('-inf'), float('-inf')
        
        for char in subset:
            min_x = min(min_x, char['bbox'][0])
            min_y = min(min_y, char['bbox'][1])
            max_x = max(max_x, char['bbox'][2])
            max_y = max(max_y, char['bbox'][3])
            
        item_id = self.canvas.create_rectangle(0,0,0,0) # Marcador de posición
        
        self.save_draw_data(item_id, {
            "type": "replace",
            "x0": min_x, "y0": min_y, "x1": max_x, "y1": max_y,
            "content": new_text,
            "fontsize": 12, 
            "color": (0,0,0)
        })
        
        # Limpiar la selección y redibujar
        self.selection_start_idx = None
        self.selected_text_content = ""
        self.canvas.delete("text_selection")
        self.restore_drawings()

    def delete_selected_item(self):
        if self.selected_item_id:
            if self.selected_item_id in self.page_draw_data.get(self.current_page_idx, {}):
                del self.page_draw_data[self.current_page_idx][self.selected_item_id]
                self.canvas.delete(self.selected_item_id)
                self.canvas.delete("selection_box")
                self.selected_item_id = None
                return

        if self.selected_text_content and self.selection_start_idx is not None:
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
            
            for r in rects:
                 item_id = self.canvas.create_rectangle(0,0,0,0)
                 self.save_draw_data(item_id, {
                     "type": "redact_annot",
                     "x0": r[0], "y0": r[1], "x1": r[2], "y1": r[3],
                     "fill": (0,0,0) 
                 })
            
            self.selection_start_idx = None
            self.canvas.delete("text_selection")
            self.restore_drawings()

    # --- Arrastre/Cambio de tamaño de elementos ---
    def handle_item_drag(self, x, y):
        item_id = self.drag_data["item"]
        data = self.page_draw_data.get(self.current_page_idx, {}).get(item_id)
        if not data: return
        
        scale = self.zoom_level
        ox, oy = self.offset_x, self.offset_y

        if self.drag_data["mode"] == "move":
             dx = x - self.drag_data["x"]
             dy = y - self.drag_data["y"]
             self.canvas.move(item_id, dx, dy)
             
             # Actualizar Datos (Coordenadas PDF)
             d_pdf_x = dx / scale
             d_pdf_y = dy / scale
             
             if "x" in data: 
                 data['x'] += d_pdf_x
                 data['y'] += d_pdf_y
             elif "x0" in data:
                 data['x0'] += d_pdf_x
                 data['y0'] += d_pdf_y
                 data['x1'] += d_pdf_x
                 data['y1'] += d_pdf_y
             elif "points" in data:
                 for i in range(len(data['points'])):
                     data['points'][i] += (d_pdf_x if i%2==0 else d_pdf_y)
             
             self.drag_data["x"] = x
             self.drag_data["y"] = y
             self.update_selection_box()
             
        elif self.drag_data["mode"] == "resize":
             if data['type'] == 'text':
                 scale = self.zoom_level
                 current_fontsize = data.get('fontsize', 12)
                 anchor_screen_x = data['x'] * scale + ox
                 anchor_screen_y = data['y'] * scale + oy
                 
                 dy = y - anchor_screen_y

                 if dy > 5:
                     new_fs = int(dy / scale)
                     if new_fs < 5: new_fs = 5
                     
                     if new_fs != current_fontsize:
                         data['fontsize'] = new_fs
                         self.canvas.itemconfigure(item_id, font=("Arial", int(new_fs*scale)))
                 
                 self.update_selection_box()
                 return

             if data['type'] not in ['rect', 'image', 'whiteout']: return

             x0, y0, x1, y1 = data['x0'], data['y0'], data['x1'], data['y1']
             
             mx_pdf = (x - ox) / scale
             my_pdf = (y - oy) / scale
             
             handle = self.drag_data["handle"]
             if "w" in handle: x0 = mx_pdf
             if "e" in handle: x1 = mx_pdf
             if "n" in handle: y0 = my_pdf
             if "s" in handle: y1 = my_pdf
             
             # Restricción
             if x1 < x0 + 1: x1 = x0 + 1
             if y1 < y0 + 1: y1 = y0 + 1
             
             data.update({"x0": x0, "y0": y0, "x1": x1, "y1": y1})
             
             # Redibujar Elemento
             sx0, sy0 = x0*scale + ox, y0*scale + oy
             sx1, sy1 = x1*scale + ox, y1*scale + oy
             
             if data['type'] == 'image':
                 try:
                     pil_img = Image.open(data['path'])
                     w_t = int(sx1 - sx0)
                     h_t = int(sy1 - sy0)
                     pil_r = pil_img.resize((w_t, h_t), Image.Resampling.LANCZOS)
                     tk_i = ImageTk.PhotoImage(pil_r)
                     self.images_cache.append(tk_i)
                     self.canvas.itemconfig(item_id, image=tk_i)
                     self.canvas.coords(item_id, sx0, sy0)
                 except: pass
             else:
                 self.canvas.coords(item_id, sx0, sy0, sx1, sy1)
             
             self.update_selection_box()

    def update_selection_box(self):
        self.canvas.delete("selection_box")
        self.canvas.delete("resize_handle")
        if not self.selected_item_id: return
        
        bbox = self.canvas.bbox(self.selected_item_id)
        if not bbox: return
        
        x1, y1, x2, y2 = bbox
        self.canvas.create_rectangle(x1-2, y1-2, x2+2, y2+2, outline="blue", dash=(4, 4), tags="selection_box")
        
        # Manejadores (Handles)
        handles = [(x1,y1,"nw"), (x2,y1,"ne"), (x1,y2,"sw"), (x2,y2,"se")]
        for hx, hy, t in handles:
            self.canvas.create_rectangle(hx-5, hy-5, hx+5, hy+5, fill="white", outline="blue", tags=("resize_handle", t))

    # --- Herramientas de Creación ---
    def create_text_input(self, x, y):
        # Widget de entrada (Entry)
        entry = tk.Entry(self.canvas, font=("Arial", 12), fg="black", bd=1, relief="solid")
        win_id = self.canvas.create_window(x, y, window=entry, anchor="nw")
        entry.focus()
        
        scale = self.zoom_level
        ox, oy = self.offset_x, self.offset_y
        
        def finalize(e=None):
            txt = entry.get()
            if txt:
                # Coordenadas PDF
                px = (x - ox) / scale
                py = (y - oy) / scale
                
                cid = self.canvas.create_text(x, y, text=txt, font=("Arial", int(12*scale)), fill="black", anchor="nw")
                self.save_draw_data(cid, {
                    "type": "text", "x": px, "y": py, "content": txt, "fontsize": 12, "color": (0,0,0)
                })
                self.set_tool("select")
                self.selected_item_id = cid
                self.drag_data["item"] = cid
                self.update_selection_box()
            self.canvas.delete(win_id)
            
        entry.bind("<Return>", finalize)
        entry.bind("<FocusOut>", finalize)

    def start_pencil(self, x, y):
        self.current_points = [x, y]
        self.current_draw_id = self.canvas.create_line(x, y, x, y, fill="red", width=2, capstyle="round")

    def continue_pencil(self, x, y):
        if self.current_draw_id:
            self.current_points.extend([x, y])
            self.canvas.coords(self.current_draw_id, *self.current_points)

    def start_rect(self, x, y, type_):
        self.current_draw_id = self.canvas.create_rectangle(x, y, x, y, outline="red" if type_=="rect" else "white", fill="white" if type_=="whiteout" else "")

    def continue_rect(self, x, y):
         if self.current_draw_id:
             self.canvas.coords(self.current_draw_id, self.last_x, self.last_y, x, y)
             
    def finish_drawing(self):
        scale = self.zoom_level
        ox, oy = self.offset_x, self.offset_y
        
        if self.tool_mode == "pencil":
             # Guardar puntos convertidos a PDF
             pdf_pts = []
             for i in range(0, len(self.current_points), 2):
                 pdf_pts.append( (self.current_points[i] - ox) / scale )
                 pdf_pts.append( (self.current_points[i+1] - oy) / scale )
             
             self.save_draw_data(self.current_draw_id, {
                 "type": "pencil", "points": pdf_pts, "color": "red", "width": 2
             })
             
        elif self.tool_mode in ["whiteout"]:
             coords = self.canvas.coords(self.current_draw_id)
             x0, y0, x1, y1 = coords
             self.save_draw_data(self.current_draw_id, {
                 "type": "whiteout",
                 "x0": (x0-ox)/scale, "y0": (y0-oy)/scale,
                 "x1": (x1-ox)/scale, "y1": (y1-oy)/scale,
                 "fill": (1, 1, 1)
             })
        self.current_draw_id = None

    def insert_image(self, x, y):
        path = filedialog.askopenfilename(filetypes=[("Imágenes", "*.png *.jpg")])
        if path:
            pil_img = Image.open(path)
            aspect = pil_img.height / pil_img.width
            w_pdf = 100
            h_pdf = 100 * aspect
            
            scale = self.zoom_level
            ox, oy = self.offset_x, self.offset_y
            
            px = (x - ox) / scale
            py = (y - oy) / scale
            
            # Renderizar
            w_s = int(w_pdf * scale)
            h_s = int(h_pdf * scale)
            pil_r = pil_img.resize((w_s, h_s))
            tk_i = ImageTk.PhotoImage(pil_r)
            self.images_cache.append(tk_i)
            
            iid = self.canvas.create_image(x, y, image=tk_i, anchor="nw")
            self.save_draw_data(iid, {
                "type": "image", "path": path, 
                "x0": px, "y0": py, "x1": px+w_pdf, "y1": py+h_pdf,
                "width": w_pdf, "height": h_pdf
            })
            self.set_tool("select")

    def save_draw_data(self, item_id, data):
        if self.current_page_idx not in self.page_draw_data:
            self.page_draw_data[self.current_page_idx] = {}
        self.page_draw_data[self.current_page_idx][item_id] = data

    # --- Búsqueda ---
    def perform_search(self):
        term = self.entry_search.get()
        if not term: return
        
        self.search_results = []
        
        # Buscar en todas las páginas
        for i in range(len(self.doc)):
            page = self.doc[i]
            rects = page.search_for(term)
            for r in rects:
                self.search_results.append((i, r))
        
        if self.search_results:
            self.current_search_idx = 0
            self.jump_to_search_result()
        else:
            self.lbl_search_status.configure(text="0 encontrados")
            
    def next_match(self):
        if not self.search_results: return
        self.current_search_idx = (self.current_search_idx + 1) % len(self.search_results)
        self.jump_to_search_result()

    def prev_match(self):
        if not self.search_results: return
        self.current_search_idx = (self.current_search_idx - 1) % len(self.search_results)
        self.jump_to_search_result()
        
    def jump_to_search_result(self):
        pidx, _ = self.search_results[self.current_search_idx]
        self.lbl_search_status.configure(text=f"{self.current_search_idx+1}/{len(self.search_results)}")
        
        if pidx != self.current_page_idx:
            self.current_page_idx = pidx
            self.render_page()
        else:
            self.draw_search_highlights()

    def draw_search_highlights(self):
        self.canvas.delete("search_res")
        if not self.search_results: return
        
        scale = self.zoom_level
        ox, oy = self.offset_x, self.offset_y
        
        # Filtrar para la página actual
        page_res = [res for i, res in enumerate(self.search_results) if res[0] == self.current_page_idx]
        
        for i, (pidx, rect) in enumerate(self.search_results):
            if pidx != self.current_page_idx: continue
            
            is_active = (i == self.current_search_idx)
            fill = "orange" if is_active else "yellow"
            
            x0 = rect[0]*scale + ox
            y0 = rect[1]*scale + oy
            x1 = rect[2]*scale + ox
            y1 = rect[3]*scale + oy
            
            self.canvas.create_rectangle(x0, y0, x1, y1, fill=fill, stipple="gray50", outline="", tags="search_res")

    def zoom_in(self):
        self.zoom_level += 0.25
        self.render_page()
    
    def zoom_out(self):
        if self.zoom_level > 0.5:
            self.zoom_level -= 0.25
            self.render_page()
            
    def save_file(self):
        if not self.current_pdf_path: return
        out_path = filedialog.asksaveasfilename(filetypes=[("Archivos PDF", "*.pdf")], defaultextension=".pdf")
        if not out_path: return
        
        # Aplanar datos
        changes = []
        for pidx, items in self.page_draw_data.items():
            for item in items.values():
                c = item.copy()
                c['page'] = pidx
                if c['type'] == 'pencil':
                     pts = item['points']
                     c['points_list'] = [(pts[i], pts[i+1]) for i in range(0, len(pts), 2)]
                changes.append(c)
                
        self.backend.save_changes(self.current_pdf_path, changes, out_path)
        messagebox.showinfo("Guardado", "¡Archivo guardado!")

    def on_mouse_move(self, event):
        pass

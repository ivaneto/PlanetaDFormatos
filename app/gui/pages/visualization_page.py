import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from app.gui.pages.base_page import BasePage
from app.gui.theme import Theme
import io
from PIL import Image, ImageTk
import fitz # PyMuPDF
import os

# Páginas de Destino para Accesos Directos
from app.gui.pages.rotate_page import RotatePage
from app.gui.pages.merge_page import MergePage
from app.gui.pages.crop_page import CropPage
from app.gui.pages.page_numbers_page import PageNumbersPage
from app.gui.pages.multi_split_page import MultiSplitPage
from app.gui.pages.watermark_page import WatermarkPage
from app.gui.pages.protect_page import ProtectPage
from app.gui.pages.compress_page import CompressPage
from app.gui.pages.ocr_page import OCRPage

class VisualizationPage(BasePage):
    def create_widgets(self):
        self.tool_mode = "select" # Por defecto seleccionar
        self.doc = None
        self.current_page_idx = 0
        self.zoom_level = 1.0
        self.tk_img = None
        self.search_results = [] 
        self.current_search_idx = -1
        self.search_term = ""
        
        self.page_chars = []
        self.selection_start_idx = None
        self.selection_end_idx = None
        self.selected_text = ""
        
        self.offset_x = 0
        self.offset_y = 0
        self.page_layouts = []
        self.page_images = {} # Usar dict para lazy loading idx: tk_img
        self.page_chars_cache = {}
        self.rendering_queue = set() # Páginas pendientes de renderizado
        self.render_after_id = None

        # --- Barra de herramientas ---
        self.toolbar = ctk.CTkFrame(self.content_frame, height=50, fg_color=Theme.CARD_BG_N1)
        self.toolbar.pack(fill="x", side="top")
        
        self.create_toolbar()
        
        # --- Área Principal ---
        self.canvas_container = ctk.CTkFrame(self.content_frame, fg_color="gray90")
        self.canvas_container.pack(fill="both", expand=True)
        
        self.canvas = tk.Canvas(self.canvas_container, bg="gray80", highlightthickness=0)
        
        self.v_scroll = ctk.CTkScrollbar(self.canvas_container, command=self.canvas.yview)
        self.h_scroll = ctk.CTkScrollbar(self.canvas_container, orientation="horizontal", command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)
        
        self.v_scroll.pack(side="right", fill="y")
        self.h_scroll.pack(side="bottom", fill="x")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Debounce para el scroll
        self.canvas.bind("<Configure>", self.on_configure)
        self.v_scroll.configure(command=self.on_v_scroll)
        
        # Vinculaciones (Bindings)
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        # Rueda del ratón
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel) 
        # Rueda del ratón en Linux
        # self.canvas.bind("<Button-4>", self.on_mouse_wheel)
        # self.canvas.bind("<Button-5>", self.on_mouse_wheel)
        
        # Atajos de teclado
        self.canvas.bind("<Control-c>", lambda e: self.copy_selection())
        self.canvas.focus_set()

        self.show_welcome()

    def create_toolbar(self):
        # Abrir
        btn_open = ctk.CTkButton(self.toolbar, text="📂 Abrir", width=80, command=self.select_file)
        btn_open.pack(side="left", padx=5, pady=5)
        
        # Separador
        tk.Frame(self.toolbar, width=1, bg="gray50").pack(side="left", fill="y", padx=5, pady=10)

        # Navegación
        self.btn_prev = ctk.CTkButton(self.toolbar, text="<", width=30, command=self.prev_page)
        self.btn_prev.pack(side="left", padx=2)
        
        self.entry_page = ctk.CTkEntry(self.toolbar, width=50, justify="center")
        self.entry_page.pack(side="left", padx=2)
        self.entry_page.bind("<Return>", self.on_page_entry)
        
        self.lbl_total = ctk.CTkLabel(self.toolbar, text="/ 0")
        self.lbl_total.pack(side="left", padx=2)
        
        self.btn_next = ctk.CTkButton(self.toolbar, text=">", width=30, command=self.next_page)
        self.btn_next.pack(side="left", padx=2)

        tk.Frame(self.toolbar, width=1, bg="gray50").pack(side="left", fill="y", padx=5, pady=10)

        # Zoom
        btn_out = ctk.CTkButton(self.toolbar, text="-", width=30, command=self.zoom_out)
        btn_out.pack(side="left", padx=2)
        
        self.lbl_zoom = ctk.CTkLabel(self.toolbar, text="100%")
        self.lbl_zoom.pack(side="left", padx=2)
        
        btn_in = ctk.CTkButton(self.toolbar, text="+", width=30, command=self.zoom_in)
        btn_in.pack(side="left", padx=2)

        tk.Frame(self.toolbar, width=1, bg="gray50").pack(side="left", fill="y", padx=5, pady=10)

        # Herramientas
        self.btn_hand = ctk.CTkButton(self.toolbar, text="🖐️", width=40, 
                                      fg_color=Theme.PRIMARY, command=lambda: self.set_tool("hand"))
        self.btn_hand.pack(side="left", padx=2)
        
        # Botón de Acceso Directo a Herramientas
        self.btn_tools = ctk.CTkButton(self.toolbar, text="🛠", width=40, 
                                       fg_color="#333333", hover_color="#555555",
                                       command=self.open_tools_dialog)
        self.btn_tools.pack(side="left", padx=2)
        
        self.btn_select = ctk.CTkButton(self.toolbar, text="Seleccionar", width=80, 
                                        fg_color="transparent", border_width=1, command=lambda: self.set_tool("select"))
        self.btn_select.pack(side="left", padx=2)
        
        self.btn_copy = ctk.CTkButton(self.toolbar, text="📋 Copiar", width=60, 
                                      fg_color="transparent", border_width=1, command=self.copy_selection)
        self.btn_copy.pack(side="left", padx=2)

        tk.Frame(self.toolbar, width=1, bg="gray50").pack(side="left", fill="y", padx=5, pady=10)

        # Búsqueda
        self.entry_search = ctk.CTkEntry(self.toolbar, width=150, placeholder_text="Buscar...")
        self.entry_search.pack(side="left", padx=2)
        self.entry_search.bind("<Return>", lambda e: self.perform_search())
        
        btn_search = ctk.CTkButton(self.toolbar, text="🔍", width=40, command=self.perform_search)
        btn_search.pack(side="left", padx=2)
        
        self.btn_prev_search = ctk.CTkButton(self.toolbar, text="⬆️", width=30, command=self.prev_match)
        self.btn_prev_search.pack(side="left", padx=1)
        
        self.btn_next_search = ctk.CTkButton(self.toolbar, text="⬇️", width=30, command=self.next_match)
        self.btn_next_search.pack(side="left", padx=1)
        
        self.lbl_search_status = ctk.CTkLabel(self.toolbar, text="")
        self.lbl_search_status.pack(side="left", padx=5)

    def show_welcome(self):
        self.canvas.delete("all")
        self.canvas.create_text(400, 300, text="Abre un PDF para visualizar", font=("Arial", 20), fill="gray")

    def select_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Archivos PDF", "*.pdf")])
        if filename:
            self.load_pdf(filename)

    def load_pdf(self, path):
        try:
            self.doc = fitz.open(path)
            self.current_page_idx = 0
            self.search_results = []
            self.current_search_idx = -1
            self.lbl_total.configure(text=f"/ {len(self.doc)}")
            self.page_layouts = []
            self.page_images = {}
            self.page_chars_cache = {}
            
            # Resetear canvas y scroll antes de calcular
            self.canvas.delete("all")
            self.canvas.yview_moveto(0)
            
            self.queue_update_layout()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el PDF: {e}")

    def on_configure(self, event):
        if self.doc:
            # Si hay documento pero no hay layouts (recién cargado o redimensionado desde 0), forzar layout
            if not self.page_layouts:
                self.queue_update_layout()
            else:
                self.queue_render_visible()

    def queue_update_layout(self):
        if self.render_after_id:
            self.after_cancel(self.render_after_id)
        self.render_after_id = self.after(100, self.update_layout)

    def update_layout(self):
        if not self.doc: return

        self.canvas.update_idletasks()
        cv_width = self.canvas.winfo_width()
        cv_height = self.canvas.winfo_height()
        
        # Si el canvas es muy pequeño, probablemente aún no se ha dibujado.
        # Diferir la actualización hasta que tenga tamaño real.
        if cv_width < 50 or cv_height < 50:
             self.after(100, self.update_layout)
             return

        # Limpiar canvas e imágenes antiguas (especialmente al cambiar zoom)
        self.canvas.delete("all")
        self.page_images = {}
        self.page_layouts = []
        self.rendering_queue = set()

        current_y = 20
        max_w = 0
        
        for i in range(len(self.doc)):
            page = self.doc[i]
            # Usar dimensiones originales para calcular el layout con el zoom
            p_rect = page.rect
            w = p_rect.width * self.zoom_level
            h = p_rect.height * self.zoom_level
            
            offset_x = max(20, (cv_width - w) // 2)
            
            self.page_layouts.append({
                "y_offset": current_y,
                "x_offset": offset_x,
                "width": w,
                "height": h
            })
            
            # Crear un rectángulo de marcador de posición (placeholder)
            # Usar tags para poder reemplazarlo luego
            self.canvas.create_rectangle(offset_x, current_y, offset_x + w, current_y + h, 
                                         fill="white", outline="gray90", tags=(f"placeholder_{i}", "placeholder"))
            
            # Texto indicador de carga
            self.canvas.create_text(offset_x + w/2, current_y + h/2, text=f"Página {i+1}", 
                                    fill="gray80", font=("Arial", 16), tags=(f"loading_text_{i}", "placeholder"))
            
            current_y += h + 30
            max_w = max(max_w, w + offset_x * 2)

        self.canvas.config(scrollregion=(0, 0, max(max_w, cv_width), current_y))
        
        # Actualizar Controles
        self.entry_page.delete(0, "end")
        self.entry_page.insert(0, str(self.current_page_idx + 1))
        self.lbl_zoom.configure(text=f"{int(self.zoom_level * 100)}%")
        
        # Renderizar páginas visibles inmediatamente después de actualizar el layout
        self.render_visible_pages()

    def queue_render_visible(self):
        if self.render_after_id:
            self.after_cancel(self.render_after_id)
        self.render_after_id = self.after(100, self.render_visible_pages)

    def render_visible_pages(self):
        if not self.doc: return
        
        # Obtener el área visible del canvas
        y_top = self.canvas.canvasy(0)
        y_bottom = y_top + self.canvas.winfo_height()
        
        # Margen para pre-renderizar
        margin = 1000
        
        for i, layout in enumerate(self.page_layouts):
            p_top = layout["y_offset"]
            p_bottom = p_top + layout["height"]
            
            # Si la página está en el área visible (con margen) y no se ha renderizado
            if p_top < y_bottom + margin and p_bottom > y_top - margin:
                if i not in self.page_images:
                    self.render_page_at_index(i)
        
        self.draw_search_highlights()

    def render_page_at_index(self, idx):
        if idx in self.page_images or not self.doc: return
        
        page = self.doc[idx]
        layout = self.page_layouts[idx]
        
        mat = fitz.Matrix(self.zoom_level, self.zoom_level)
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        pil_img = Image.open(io.BytesIO(img_data))
        tk_img = ImageTk.PhotoImage(pil_img)
        self.page_images[idx] = tk_img
        
        # Reemplazar placeholder con la imagen real
        self.canvas.delete(f"placeholder_{idx}")
        self.canvas.delete(f"loading_text_{idx}")
        self.canvas.create_image(layout["x_offset"], layout["y_offset"], image=tk_img, anchor="nw", tags=(f"page_{idx}", "bg"))
        self.canvas.tag_lower(f"page_{idx}")

    def on_v_scroll(self, *args):
        self.canvas.yview(*args)
        self.queue_render_visible()
        # Actualizar current_page_idx basado en scroll
        y_mid = self.canvas.canvasy(self.canvas.winfo_height() // 2)
        for i, layout in enumerate(self.page_layouts):
            if layout["y_offset"] <= y_mid <= layout["y_offset"] + layout["height"] + 30:
                if self.current_page_idx != i:
                    self.current_page_idx = i
                    self.entry_page.delete(0, "end")
                    self.entry_page.insert(0, str(i + 1))
                break

    def update_scroll_to_page(self, idx):
        if not self.page_layouts or idx < 0 or idx >= len(self.page_layouts): return
        layout = self.page_layouts[idx]
        try:
            bbox = self.canvas.cget("scrollregion").split(" ")
            total_h = float(bbox[3])
            if total_h > 0:
                self.canvas.yview_moveto(layout["y_offset"] / total_h)
            self.queue_render_visible()
        except:
            pass

    def zoom_in(self):
        self.zoom_level += 0.25
        self.queue_update_layout()

    def zoom_out(self):
        if self.zoom_level > 0.25:
            self.zoom_level -= 0.25
            self.queue_update_layout()

    def prev_page(self):
        if self.doc and self.current_page_idx > 0:
            self.current_page_idx -= 1
            self.update_scroll_to_page(self.current_page_idx)
            self.entry_page.delete(0, "end")
            self.entry_page.insert(0, str(self.current_page_idx + 1))

    def next_page(self):
        if self.doc and self.current_page_idx < len(self.doc) - 1:
            self.current_page_idx += 1
            self.update_scroll_to_page(self.current_page_idx)
            self.entry_page.delete(0, "end")
            self.entry_page.insert(0, str(self.current_page_idx + 1))

    def on_page_entry(self, event):
        try:
            p = int(self.entry_page.get())
            if 1 <= p <= len(self.doc):
                self.current_page_idx = p - 1
                self.update_scroll_to_page(self.current_page_idx)
            else:
                self.entry_page.delete(0, "end")
                self.entry_page.insert(0, str(self.current_page_idx + 1))
        except:
            pass

    def set_tool(self, tool):
        self.tool_mode = tool
        if tool == "hand":
            self.canvas.config(cursor="fleur")
            self.btn_hand.configure(fg_color=Theme.PRIMARY)
            self.btn_select.configure(fg_color="transparent")
        else:
            self.canvas.config(cursor="xterm")
            self.btn_hand.configure(fg_color="transparent")
            self.btn_select.configure(fg_color=Theme.PRIMARY)

    def _parse_page_chars(self, page):
        self.page_chars = []
        raw = page.get_text("rawdict")
        line_idx = 0
        # Estructura aplanada: bloques -> líneas -> intervalos (spans) -> caracteres
        for block in raw.get("blocks", []):
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    for char in span.get("chars", []):
                        # claves de char: 'bbox' (rect), 'c' (caracter), 'origin'
                        self.page_chars.append({
                            "bbox": char["bbox"],
                            "c": char["c"],
                            "line": line_idx
                        })
                line_idx += 1

    def get_char_at_pos(self, x, y):
        cx = self.canvas.canvasx(x)
        cy = self.canvas.canvasy(y)
        
        # Encontrar página bajo el ratón
        target_idx = -1
        layout = None
        for i, l in enumerate(self.page_layouts):
            if l["y_offset"] <= cy <= l["y_offset"] + l["height"]:
                target_idx = i
                layout = l
                break
        
        if target_idx == -1: return None
        
        # Cambiar página actual si es necesario
        if target_idx != self.current_page_idx:
            self.current_page_idx = target_idx
            self.entry_page.delete(0, "end")
            self.entry_page.insert(0, str(self.current_page_idx + 1))

        # Obtener caracteres de esta página
        if target_idx not in self.page_chars_cache:
            self._parse_page_chars(self.doc[target_idx])
            self.page_chars_cache[target_idx] = self.page_chars
        else:
            self.page_chars = self.page_chars_cache[target_idx]

        if not self.page_chars: return None

        pdf_x = (cx - layout["x_offset"]) / self.zoom_level
        pdf_y = (cy - layout["y_offset"]) / self.zoom_level
        
        best_idx = None
        min_dist = float('inf')
        
        for i, char in enumerate(self.page_chars):
            bx0, by0, bx1, by1 = char["bbox"]
            if bx0 <= pdf_x <= bx1 and by0 <= pdf_y <= by1:
                return i
            
            cx_char, cy_char = (bx0+bx1)/2, (by0+by1)/2
            dist = (pdf_x - cx_char)**2 + (pdf_y - cy_char)**2
            if dist < min_dist:
                min_dist = dist
                best_idx = i
                
        if min_dist < 400:
            return best_idx
        return None

    def on_mouse_wheel(self, event):
        if self.doc:
            if event.delta > 0 or event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            else:
                self.canvas.yview_scroll(1, "units")
            self.queue_render_visible()

    def on_mouse_down(self, event):
        self.canvas.focus_set()
        if self.tool_mode == "hand":
            self.canvas.scan_mark(event.x, event.y)
        else:
            idx = self.get_char_at_pos(event.x, event.y)
            if idx is not None:
                self.selection_start_idx = idx
                self.selection_end_idx = idx
                self.update_selection_visuals()
            else:
                self.selection_start_idx = None
                self.selection_end_idx = None
                self.selected_text = ""
                self.canvas.delete("selection")

    def on_mouse_drag(self, event):
        if self.tool_mode == "hand":
            self.canvas.scan_dragto(event.x, event.y, gain=1)
        else:
            idx = self.get_char_at_pos(event.x, event.y)
            
            if self.selection_start_idx is None:
                if idx is not None:
                    self.selection_start_idx = idx
            
            if self.selection_start_idx is not None and idx is not None:
                self.selection_end_idx = idx
                self.update_selection_visuals()

    def on_mouse_up(self, event):
        pass 

    def update_selection_visuals(self):
        self.canvas.delete("selection")
        if self.selection_start_idx is None or self.selection_end_idx is None: return
        
        start = min(self.selection_start_idx, self.selection_end_idx)
        end = max(self.selection_start_idx, self.selection_end_idx)
        
        subset = self.page_chars[start : end+1]
        if not subset: return
        
        rects_to_draw = []
        chars_text = []
        
        current_rect = None 
        current_line_idx = -1
        
        last_char = None
        
        for char in subset:
            if last_char:
                if char['line'] != last_char['line']:
                    chars_text.append("\n")
                else:
                    gap = char['bbox'][0] - last_char['bbox'][2]
                    if gap > 1.5: 
                        chars_text.append(" ")
            
            chars_text.append(char['c'])
            last_char = char
            
            # Fusión Visual
            c_box = char["bbox"]
            if char["line"] != current_line_idx:
                if current_rect: rects_to_draw.append(current_rect)
                current_rect = list(c_box)
                current_line_idx = char["line"]
            else:
                # Combinar: Unión de rectángulos
                current_rect[0] = min(current_rect[0], c_box[0])
                current_rect[1] = min(current_rect[1], c_box[1])
                current_rect[2] = max(current_rect[2], c_box[2])
                current_rect[3] = max(current_rect[3], c_box[3])
        
        if current_rect: rects_to_draw.append(current_rect)
        
        self.selected_text = "".join(chars_text)
        
        # Dibujar rectángulos combinados
        layout = self.page_layouts[self.current_page_idx]
        for r in rects_to_draw:
            sx0 = (r[0] * self.zoom_level) + layout["x_offset"]
            sy0 = (r[1] * self.zoom_level) + layout["y_offset"]
            sx1 = (r[2] * self.zoom_level) + layout["x_offset"]
            sy1 = (r[3] * self.zoom_level) + layout["y_offset"]
            
            self.canvas.create_rectangle(sx0, sy0, sx1, sy1, fill="blue", stipple="gray50", outline="", tags="selection")
            
        self.canvas.tag_lower("selection") 
        self.canvas.tag_lower("bg", "selection")

    def copy_selection(self):
        if self.selected_text:
            self.clipboard_clear()
            self.clipboard_append(self.selected_text)
        else:
            pass

    def perform_search(self):
        term = self.entry_search.get()
        if not term:
            # Limpiar búsqueda si está vacía
            self.search_term = ""
            self.search_results = []
            self.current_search_idx = -1
            self.lbl_search_status.configure(text="")
            self.canvas.delete("search_res")
            return

        if not self.doc: return
        
        # Restablecer si el término es nuevo
        if term != self.search_term:
            self.search_term = term
            self.search_results = []
            
            # Búsqueda precisa: usar quads=True para obtener ubicaciones exactas (corrige TypeError 'quad')
            for i in range(len(self.doc)):
                page = self.doc[i]
                # search_for con quads=True devuelve una lista de Quads
                try:
                    res = page.search_for(term, quads=True)
                except TypeError:
                    res_rects = page.search_for(term)
                    res = [fitz.Quad(r) for r in res_rects]

                for quad in res:
                    self.search_results.append((i, quad))
                    
            if not self.search_results:
                self.lbl_search_status.configure(text="0 encontrados")
                messagebox.showinfo("Búsqueda", "No se encontraron resultados.")
                return
            
            self.current_search_idx = 0
            self.lbl_search_status.configure(text=f"1 / {len(self.search_results)}")
            self.jump_to_search_result()
        else:
            self.next_match()

    def next_match(self):
        if not self.search_results: return
        self.current_search_idx = (self.current_search_idx + 1) % len(self.search_results)
        self.update_search_label()
        self.jump_to_search_result()

    def prev_match(self):
        if not self.search_results: return
        self.current_search_idx = (self.current_search_idx - 1) % len(self.search_results)
        self.update_search_label()
        self.jump_to_search_result()
        
    def update_search_label(self):
        self.lbl_search_status.configure(text=f"{self.current_search_idx + 1} / {len(self.search_results)}")

    def jump_to_search_result(self):
        if not self.search_results: return
        target_page_idx, _ = self.search_results[self.current_search_idx]
        self.current_page_idx = target_page_idx
        self.update_scroll_to_page(target_page_idx)
        # Resaltado activo se maneja en draw_search_highlights que se llama indirectamente o redibuja
        self.draw_search_highlights()
            
    def draw_search_highlights(self):
        if not self.doc or not self.search_results: return
        self.canvas.delete("search_res")
        
        for idx, (page_idx, quad) in enumerate(self.search_results):
            if page_idx >= len(self.page_layouts): continue
            layout = self.page_layouts[page_idx]
            scale = self.zoom_level
            
            try:
                points = [(quad.ul.x * scale) + layout["x_offset"], (quad.ul.y * scale) + layout["y_offset"], 
                          (quad.ur.x * scale) + layout["x_offset"], (quad.ur.y * scale) + layout["y_offset"],
                          (quad.lr.x * scale) + layout["x_offset"], (quad.lr.y * scale) + layout["y_offset"],
                          (quad.ll.x * scale) + layout["x_offset"], (quad.ll.y * scale) + layout["y_offset"]]
                
                is_active = (idx == self.current_search_idx)
                fill_col = "orange" if is_active else "yellow"
                
                self.canvas.create_polygon(points, fill=fill_col, stipple="gray50", outline="", tags="search_res")
            except Exception as e:
                print(f"Error al dibujar el resaltado: {e}")


    def infos(self):
        return (self.winfo_rootx(), self.winfo_rooty())

    # -------------------------------------------------------------------------
    # Lógica del Diálogo de Herramientas
    # -------------------------------------------------------------------------
    def open_tools_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Herramientas Rápidas")
        dialog.geometry("350x500")
        dialog.transient(self)
        dialog.grab_set()
        
        x = self.infos()[0] + (self.winfo_width()//2) - 175
        y = self.infos()[1] + (self.winfo_height()//2) - 200
        dialog.geometry(f"+{x}+{y}")
        
        ctk.CTkLabel(dialog, text="¿Qué quieres hacer?", font=(Theme.FONT_FAMILY, 18, "bold")).pack(pady=20)
        
        # Opciones
        self.tool_var = tk.StringVar(value="rotate")
        
        options = [
            ("Organizar PDF", "rotate", RotatePage),
            ("Unir PDF", "merge", MergePage),
            ("Dividir Páginas", "split", MultiSplitPage),
            ("Recortar", "crop", CropPage),
            ("Números de Página", "numbers", PageNumbersPage),
            ("OCR", "ocr", OCRPage),
            ("Marca de Agua", "watermark", WatermarkPage),
            ("Proteger PDF", "protect", ProtectPage),
            ("Comprimir", "compress", CompressPage)

        ]
        
        # Mapeo a clases
        self.tool_map = {tag: cls for _, tag, cls in options}
        
        opts_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        opts_frame.pack(fill="both", expand=True, padx=20)
        
        for text, val, _ in options:
            ctk.CTkRadioButton(opts_frame, text=text, variable=self.tool_var, value=val,
                               font=(Theme.FONT_FAMILY, 14)).pack(anchor="w", pady=8, padx=10)
                               
        def _confirm():
            selection = self.tool_var.get()
            target_cls = self.tool_map.get(selection)
            if target_cls:
                dialog.destroy()
                self.navigate_to_tool(target_cls)
                
        btn_ok = ctk.CTkButton(dialog, text="Aceptar", command=_confirm, fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER)
        btn_ok.pack(pady=20)

    def navigate_to_tool(self, target_cls):
        pdf_path = None
        
        if self.doc and hasattr(self.doc, "name") and self.doc.name:
             pdf_path = self.doc.name
             # Asegurarse de que sea una ruta de archivo real
             if not os.path.exists(pdf_path):
                 pdf_path = None
            
        self.controller.show_page(target_cls)
        
        new_page = self.controller.current_page
        
        if pdf_path:
            try:
                if isinstance(new_page, RotatePage):
                    new_page.load_pdf(pdf_path)
                    
                elif isinstance(new_page, MultiSplitPage):
                    new_page.load_pdf(pdf_path)
                    
                elif isinstance(new_page, CropPage):
                    new_page.load_pdf(pdf_path)
                    
                elif isinstance(new_page, MergePage):
                    new_page.process_file(pdf_path)
                    
                elif isinstance(new_page, PageNumbersPage):
                    new_page.handle_dropped_files([pdf_path])
                    
                elif isinstance(new_page, WatermarkPage):
                    new_page.handle_dropped_files([pdf_path])
                    
                else:
                    if hasattr(new_page, 'load_pdf'):
                        new_page.load_pdf(pdf_path)
                    elif hasattr(new_page, 'handle_dropped_files'):
                        new_page.handle_dropped_files([pdf_path])
                        
            except Exception as e:
                print(f"Error al transferir el archivo a la herramienta: {e}")

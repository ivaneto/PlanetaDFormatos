import customtkinter as ctk
from tkinter import filedialog, Canvas
from app.gui.components import dialogs as messagebox
from app.gui.pages.base_page import BasePage
from app.gui.theme import Theme
import fitz # PyMuPDF
from PIL import Image, ImageTk
import threading
import os

class RotateCard(ctk.CTkFrame):
    def __init__(self, parent, page_num, pil_image, on_rotate, on_delete, on_drag_start, on_drag_motion, on_drag_end):
        super().__init__(parent, fg_color="transparent")
        self.page_num = page_num
        self.original_image = pil_image
        self.source_doc = None
        self.doc_index = -1
        self.original_page_index = -1
        self.current_rotation = 0
        self.on_rotate = on_rotate
        self.on_delete = on_delete
        
        self.on_drag_start = on_drag_start
        self.on_drag_motion = on_drag_motion
        self.on_drag_end = on_drag_end
        
        self.image_container = ctk.CTkFrame(self, width=150, height=200, fg_color="transparent", corner_radius=5)
        self.image_container.pack(padx=5, pady=5)
        self.image_container.pack_propagate(False)
        
        self.ctk_image = None
        self.image_label = ctk.CTkLabel(self.image_container, text="")
        self.image_label.place(relx=0.5, rely=0.5, anchor="center")

        self.btn_rotate = ctk.CTkButton(self.image_container, text="⟳", width=16, height=16,
                                        fg_color=Theme.PRIMARY,
                                        hover_color=Theme.PRIMARY_HOVER,
                                        font=("Arial", 12), corner_radius=4,
                                        command=self.perform_rotate)   
        self.btn_rotate.place(relx=0.5, rely=0.5, anchor="center")
        
        # Controles inferiores
        self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_frame.pack(fill="x", padx=5, pady=(0, 5))
        
        self.lbl_num = ctk.CTkLabel(self.bottom_frame, text=f"Página {page_num + 1}", font=(Theme.FONT_FAMILY, 12), text_color=Theme.TEXT_MUTED)
        self.lbl_num.pack(side="left", padx=5)
        
        self.btn_delete = ctk.CTkButton(self.bottom_frame, text="🗑", width=25, height=25,
                                        fg_color="transparent", text_color=Theme.DANGER, hover_color="#FFEEEE",
                                        font=(Theme.FONT_FAMILY, 14),
                                        command=lambda: on_delete(self))
        self.btn_delete.pack(side="right", padx=5)
        
        # Vincular eventos de arrastre
        self.image_label.bind("<Button-1>", self.start_drag)
        self.image_label.bind("<B1-Motion>", self.drag_motion)
        self.image_label.bind("<ButtonRelease-1>", self.end_drag)
        
        self.image_container.bind("<Button-1>", self.start_drag)
        self.image_container.bind("<B1-Motion>", self.drag_motion)
        self.image_container.bind("<ButtonRelease-1>", self.end_drag)
        
        # Renderizado inicial de la imagen
        self.update_image()

    def start_drag(self, event):
        if self.on_drag_start:
            self.on_drag_start(event, self)

    def drag_motion(self, event):
        if self.on_drag_motion:
            self.on_drag_motion(event, self)

    def end_drag(self, event):
        if self.on_drag_end:
            self.on_drag_end(event, self)

    def perform_rotate(self):
        self.current_rotation = (self.current_rotation + 90) % 360
        self.update_image()
        if self.on_rotate:
            self.on_rotate(self.page_num, self.current_rotation)

    def update_image(self):
        rotated = self.original_image.rotate(-self.current_rotation, expand=True)
        rotated.thumbnail((140, 190))
        
        self.ctk_image = ctk.CTkImage(light_image=rotated, dark_image=rotated, size=rotated.size)
        self.image_label.configure(image=self.ctk_image)

class RotatePage(BasePage):
    def create_widgets(self):
        self.docs = []
        self.page_cards = []
        
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=0)
        self.content_frame.grid_rowconfigure(1, weight=1)
        
        # --- Barra superior ---
        top_bar = ctk.CTkFrame(self.content_frame, height=60, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        
        ctk.CTkLabel(top_bar, text="Organizar PDF", font=(Theme.FONT_FAMILY, 20, "bold")).pack(side="left")
        
        ctk.CTkButton(top_bar, text="Abrir", command=self.select_file,
                      fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER).pack(side="right", padx=10)
        
        self.btn_save = ctk.CTkButton(top_bar, text="Guardar PDF", command=self.save_pdf, state="disabled",
                                      fg_color=Theme.SUCCESS, hover_color=Theme.SUCCESS_HOVER)
        self.btn_save.pack(side="right", padx=10)

        # --- Área de contenido ---
        self.scroll_frame = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.scroll_frame.columnconfigure(0, weight=1)
        
        self.enable_dnd()
        
        self.drag_data = {"item": None, "index": None, "x": 0, "y": 0}

    def handle_dropped_files(self, files):
        pdf_files = []
        image_files = []
        word_files = []
        ppt_files = []
        
        for f in files:
            ext = f.lower().split('.')[-1]
            if ext == 'pdf':
                pdf_files.append(f)
            elif ext in ['png', 'jpg', 'jpeg', 'bmp', 'tiff']:
                image_files.append(f)
            elif ext in ['doc', 'docx']:
                word_files.append(f)
            elif ext in ['ppt', 'pptx']:
                ppt_files.append(f)

        handled = False
        
        for f in pdf_files:
            self.load_pdf(f, append=True)
            handled = True
            
        if image_files:
            self.process_dropped_images(image_files)
            handled = True
            
        if word_files:
            self.process_dropped_word_files(word_files)
            handled = True
            
        if ppt_files:
            self.process_dropped_ppt_files(ppt_files)
            handled = True
            
        return handled

    def select_file(self):
        filename = filedialog.askopenfilename(filetypes=[
            ("Archivos PDF", "*.pdf"),
            ("Archivos Word", "*.doc *.docx"),
            ("Archivos Imagen", "*.png *.jpg *.jpeg"),
            ("Todos los archivos", "*.pdf *.doc *.docx *.png *.jpg *.jpeg")
        ])
        if filename:
            ext = filename.lower().split('.')[-1]
            if ext == 'pdf':
                self.load_pdf(filename, append=True)
            elif ext in ['png', 'jpg', 'jpeg', 'bmp', 'tiff']:
                self.process_dropped_images([filename])
            elif ext in ['doc', 'docx']:
                self.process_dropped_word_files([filename])
            elif ext in ['ppt', 'pptx']:
                self.process_dropped_ppt_files([filename])
            else:
                self.load_pdf(filename, append=True) # Intento por defecto

    def load_pdf(self, path, append=False):
        if not append:
            for card in self.page_cards:
                card.destroy()
            self.page_cards = []
            
            for d in self.docs:
                d.close()
            self.docs = []
            
        try:
            new_doc = fitz.open(path)
            self.docs.append(new_doc)
            doc_idx = len(self.docs) - 1
            
            # Iniciar la carga de miniaturas en un hilo separado
            threading.Thread(target=self._load_thumbnails_thread, args=(new_doc, doc_idx), daemon=True).start()
            
            self.btn_save.configure(state="normal")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar PDF: {e}")

    def _load_thumbnails_thread(self, doc, doc_index):
        # Determinar el tamaño de la cuadrícula
        cols = 7
        
        for i, page in enumerate(doc):
            pix = page.get_pixmap(matrix=fitz.Matrix(0.4, 0.4)) 
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)    
            # Crear widget en el hilo principal
            self.after(0, lambda idx=i, im=img, di=doc_index: self._add_card(idx, im, cols, di))
            
    def _add_card(self, original_page_index, pil_image, cols, doc_index):
        # Calcular el índice visual basado en la lista actual
        current_count = len(self.page_cards)
        index = current_count # la nueva tarjeta se añade al final
        
        r = index // cols
        c = index % cols
        
        card = RotateCard(self.scroll_frame, index, pil_image, 
                          on_rotate=None, 
                          on_delete=self.delete_card,
                          on_drag_start=lambda e, w=None: self.start_drag(e, w),
                          on_drag_motion=self.on_drag,
                          on_drag_end=self.end_drag)

        card.source_doc = self.docs[doc_index]
        card.doc_index = doc_index
        card.original_page_index = original_page_index
        
        card.grid(row=r, column=c, padx=10, pady=10)
        card.lbl_num.configure(text=f"Página {index + 1}")
        
        self.page_cards.append(card)

    # --- Lógica de reordenación ---
    def start_drag(self, event, widget):
        if not widget: return
        try:
            index = self.page_cards.index(widget)
            self.drag_data["item"] = widget
            self.drag_data["index"] = index
            self.drag_data["x"] = event.x_root
            self.drag_data["y"] = event.y_root
            
            widget.image_container.configure(fg_color="#D0D0D0")
        except ValueError:
            pass

    def on_drag(self, event, widget):
        pass

    def end_drag(self, event, widget):
        widget.image_container.configure(fg_color="#F0F0F0")
        
        drop_x = event.x_root
        drop_y = event.y_root
        
        closest_index = -1
        min_dist = float('inf')
        
        for i, card in enumerate(self.page_cards):
            cx = card.winfo_rootx() + (card.winfo_width() / 2)
            cy = card.winfo_rooty() + (card.winfo_height() / 2)
            
            dist = ((drop_x - cx)**2 + (drop_y - cy)**2) ** 0.5
            
            if dist < min_dist:
                min_dist = dist
                closest_index = i
        
        if self.drag_data["index"] is not None and closest_index != -1 and closest_index != self.drag_data["index"]:
            item = self.page_cards.pop(self.drag_data["index"])
            self.page_cards.insert(closest_index, item)
            self._reflow_grid(cols=6)

        self.drag_data = {"item": None, "index": None}

    def delete_card(self, card):
        card.destroy()
        self.page_cards.remove(card)
        self._reflow_grid()

    def _reflow_grid(self, cols=6):
        for i, card in enumerate(self.page_cards):
            card.grid_forget()
            r = i // cols
            c = i % cols
            card.grid(row=r, column=c, padx=10, pady=10)
            
            # Usar 'i' como la nueva etiqueta genérica "Página X", 
            card.lbl_num.configure(text=f"Página {i + 1}")

    def save_pdf(self):
        if not self.page_cards:
            return
            
        output_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("Archivos PDF", "*.pdf")])
        if not output_path:
            return
            
        try:
            # Crear nuevo PDF
            out_doc = fitz.open()
            
            # Iterar a través de las tarjetas visibles
            for card in self.page_cards:
                # Documento fuente y el índice original
                source_doc = card.source_doc
                page_num = card.original_page_index 
                rotation = card.current_rotation
                
                # Comprobar límites
                if source_doc and page_num < len(source_doc):
                    # Copiar página
                    out_doc.insert_pdf(source_doc, from_page=page_num, to_page=page_num) 
                    new_page = out_doc[-1] # La página recien añadida
                    new_page.set_rotation(new_page.rotation + rotation)
                    
            out_doc.save(output_path)
            out_doc.close()
            
            if messagebox.askyesno("Éxito", "PDF guardado. ¿Desea visualizarlo?"):
                from app.gui.pages.visualization_page import VisualizationPage
                self.controller.show_page(VisualizationPage)
                self.controller.current_page.load_pdf(output_path)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar PDF: {e}")

    # --- Controladores de conversión de archivos ---
    def process_dropped_images(self, images):
        prog_win = self._create_progress_window("Convirtiendo imágenes...")
        progress, status, label = self._get_progress_widgets(prog_win, "Convirtiendo imágenes a PDF...")
        threading.Thread(target=self._convert_images_thread, args=(images, prog_win, progress, status, label)).start()

    def process_dropped_word_files(self, files):
        prog_win = self._create_progress_window("Convirtiendo documentos Word...")
        progress, status, label = self._get_progress_widgets(prog_win, "Convirtiendo Word a PDF...")
        threading.Thread(target=self._convert_word_thread, args=(files, prog_win, progress, status, label)).start()

    def process_dropped_ppt_files(self, files):
        prog_win = self._create_progress_window("Convirtiendo presentaciones...")
        progress, status, label = self._get_progress_widgets(prog_win, "Convirtiendo PowerPoint a PDF...")
        threading.Thread(target=self._convert_ppt_thread, args=(files, prog_win, progress, status, label)).start()

    def _create_progress_window(self, title):
        prog_win = ctk.CTkToplevel(self)
        prog_win.title(title)
        
        width = 300
        height = 150
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        prog_win.geometry(f"{width}x{height}+{x}+{y}")
        prog_win.attributes("-topmost", True)
        return prog_win

    def _get_progress_widgets(self, win, label_text):
        label = ctk.CTkLabel(win, text=label_text, font=(Theme.FONT_FAMILY, 14))
        label.pack(pady=(20, 10))
        progress = ctk.CTkProgressBar(win, width=200)
        progress.pack(pady=10)
        progress.set(0)
        status = ctk.CTkLabel(win, text="0 / 0")
        status.pack(pady=5)
        return progress, status, label

    def _convert_images_thread(self, images, prog_win, progress, status_lbl, label_lbl):
        from app.core.converters import Converter
        import tempfile
        
        total = len(images)
        temp_dir = tempfile.gettempdir()
        
        try:
            output_pdf_name = f"converted_images_{os.getpid()}_{threading.get_ident()}.pdf"
            output_pdf = os.path.join(temp_dir, output_pdf_name)

            self.ui(lambda: label_lbl.configure(text="Procesando imágenes..."))
            self.ui(lambda: progress.set(0.5))

            Converter.images_to_pdf(images, output_pdf)

            self.ui(lambda: progress.set(1.0))
            self.ui(lambda: status_lbl.configure(text="Hecho"))

            self.after(0, lambda p=output_pdf: self.load_pdf(p, append=True))
            
        except Exception as e:
            print(f"Error al convertir imágenes: {e}")
            self.after(0, lambda: messagebox.showerror("Error", f"Error al convertir imágenes: {e}"))
            
        self.after(0, prog_win.destroy)

    def _convert_word_thread(self, files, prog_win, progress, status_lbl, label_lbl):
        from app.core.converters import Converter
        import tempfile
        import pythoncom
        
        pythoncom.CoInitialize()
        total = len(files)
        temp_dir = tempfile.gettempdir()
        
        for i, doc_path in enumerate(files):
            prog = i / total
            self.ui(lambda p=prog: progress.set(p))
            self.ui(lambda d=doc_path: label_lbl.configure(text=f"Convirtiendo: {os.path.basename(d)}"))
            self.ui(lambda i=i: status_lbl.configure(text=f"{i+1} / {total}"))

            try:
                output_pdf_name = f"converted_{os.path.basename(doc_path)}.pdf"
                output_pdf = os.path.join(temp_dir, output_pdf_name)

                Converter.word_to_pdf(doc_path, output_pdf)

                self.after(0, lambda p=output_pdf: self.load_pdf(p, append=True))

            except Exception as e:
                print(f"Error al convertir archivo Word {doc_path}: {e}")
        
        self.after(0, prog_win.destroy)

    def _convert_ppt_thread(self, files, prog_win, progress, status_lbl, label_lbl):
        from app.core.converters import Converter
        import tempfile
        import pythoncom
        
        pythoncom.CoInitialize()
        total = len(files)
        temp_dir = tempfile.gettempdir()
        
        for i, ppt_path in enumerate(files):
            prog = i / total
            self.ui(lambda p=prog: progress.set(p))
            self.ui(lambda d=ppt_path: label_lbl.configure(text=f"Convirtiendo: {os.path.basename(d)}"))
            self.ui(lambda i=i: status_lbl.configure(text=f"{i+1} / {total}"))

            try:
                output_pdf_name = f"converted_{os.path.basename(ppt_path)}.pdf"
                output_pdf = os.path.join(temp_dir, output_pdf_name)

                Converter.powerpoint_to_pdf(ppt_path, output_pdf)

                self.after(0, lambda p=output_pdf: self.load_pdf(p, append=True))

            except Exception as e:
                print(f"Error al convertir archivo PPT {ppt_path}: {e}")
        
        self.after(0, prog_win.destroy)

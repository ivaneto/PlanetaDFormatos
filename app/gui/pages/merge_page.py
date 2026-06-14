import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
from app.gui.components import dialogs as messagebox
import threading
from app.gui.pages.base_page import BasePage
from app.gui.theme import Theme
from app.core.pdf_ops import PDFManager
from app.core.thumbnail_manager import ThumbnailManager
from app.gui.components.thumbnail_widget import PageThumbnailWidget
import os
import re

class MergePage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, show_back_button=False)

    def create_widgets(self):
        self.source_files = [] 
        self.destination_pages = [] 
        
        self.drag_data = {"item": None, "index": None, "x": 0}

        self.content_frame.grid_rowconfigure(0, weight=3)
        self.content_frame.grid_rowconfigure(1, weight=0)
        self.content_frame.grid_rowconfigure(2, weight=2)
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        self.enable_dnd()
        
        # --- Source Area ---
        self.source_container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.source_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=(5, 5))
        
        # Header
        source_header = ctk.CTkFrame(self.source_container, fg_color="transparent")
        source_header.pack(fill="x", pady=(0, 2))
        ctk.CTkLabel(source_header, text="Archivos de Origen", font=(Theme.FONT_FAMILY, 14, "bold"), text_color=Theme.TEXT_MAIN).pack(side="left")
        ctk.CTkButton(source_header, text="+ Añadir PDF", command=self.add_file, width=80, height=25, font=(Theme.FONT_FAMILY, 12),
                      fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER).pack(side="right")
        
        # Advanced Selection Entry
        adv_frame = ctk.CTkFrame(self.source_container, fg_color="transparent")
        adv_frame.pack(fill="x", pady=(0, 5))
        
        self.entry_adv = ctk.CTkEntry(adv_frame, placeholder_text="Selección Avanzada: (A:1, 2-5)(B:3, 6-8)...", height=30)
        self.entry_adv.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        ctk.CTkButton(adv_frame, text="Añadir Selección", command=self.process_advanced_selection, width=100, height=30,
                      fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER).pack(side="right")
        
        # Scrollable Area
        self.source_scroll = ctk.CTkScrollableFrame(self.source_container, fg_color=Theme.SURFACE)
        self.source_scroll.pack(fill="both", expand=True)

        sep = ctk.CTkFrame(self.content_frame, height=2, fg_color="gray80")
        sep.grid(row=1, column=0, sticky="ew", padx=10, pady=2)
        
        # --- Destination Area ---
        self.dest_container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.dest_container.grid(row=2, column=0, sticky="nsew", padx=10, pady=(5, 5))
        
        # Header
        dest_header = ctk.CTkFrame(self.dest_container, fg_color="transparent")
        dest_header.pack(fill="x", pady=(0, 2))
        ctk.CTkLabel(dest_header, text="Composición del Nuevo PDF", font=(Theme.FONT_FAMILY, 14, "bold"), text_color=Theme.TEXT_MAIN).pack(side="left")
        
        # Control Buttons
        dest_controls = ctk.CTkFrame(dest_header, fg_color="transparent")
        dest_controls.pack(side="right")
        
        # Button to delete range
        ctk.CTkLabel(dest_controls, text="Rango a eliminar:", font=(Theme.FONT_FAMILY, 10), text_color=Theme.TEXT_MUTED).pack(side="left", padx=(0, 2))
        dest_range_entry = ctk.CTkEntry(dest_controls, width=60, height=25, font=(Theme.FONT_FAMILY, 11), placeholder_text="ej. 5-9")
        dest_range_entry.pack(side="left", padx=2)
        ctk.CTkButton(dest_controls, text="🗑", width=30, height=25, 
                      fg_color=Theme.DANGER, hover_color=Theme.DANGER_HOVER,
                      command=lambda: self.delete_dest_range(dest_range_entry.get())).pack(side="left", padx=(0, 10))
  
        ctk.CTkButton(dest_controls, text="Crear PDF", command=self.create_pdf, width=100, height=30,
                      fg_color=Theme.SUCCESS, hover_color=Theme.SUCCESS_HOVER, font=(Theme.FONT_FAMILY, 13, "bold")).pack(side="left")
        
        # Scrollable Timeline
        self.timeline_scroll = ctk.CTkScrollableFrame(self.dest_container, orientation="horizontal", height=220, fg_color=Theme.SURFACE)
        self.timeline_scroll.pack(fill="x", expand=True)
        
        self.timeline_placeholder = ctk.CTkLabel(self.timeline_scroll, text="Arrastra las páginas aquí", text_color=Theme.TEXT_MUTED)
        self.timeline_placeholder.pack(pady=60, padx=200)

    def add_file(self):
        filenames = filedialog.askopenfilenames(title="Seleccionar archivos PDF", filetypes=[("Archivos PDF", "*.pdf")])
        if filenames:
            for f in filenames:
                self.process_file(f)

    def process_file(self, filepath):
        # Identify Letter (A, B, C...)
        idx = len(self.source_files)
        letter = chr(65 + idx) if idx < 26 else f"Z{idx}" # Fallback for many files
        
        # Create Row
        row_frame = ctk.CTkFrame(self.source_scroll, fg_color="transparent")
        row_frame.pack(fill="x", pady=2, padx=2)
        
        # Info Column
        info_frame = ctk.CTkFrame(row_frame, width=140, fg_color="transparent")
        info_frame.pack(side="left", fill="y", padx=(0, 5))
        
        # Filename & Page Count
        filename = os.path.basename(filepath)
        display_name = f"{letter} - {filename}"
        
        ctk.CTkLabel(info_frame, text=display_name, font=(Theme.FONT_FAMILY, 11, "bold"), wraplength=130, text_color=Theme.PRIMARY).pack(anchor="w")
        
        page_count = ThumbnailManager.get_pdf_page_count(filepath)
        ctk.CTkLabel(info_frame, text=f"{page_count} páginas", font=(Theme.FONT_FAMILY, 9), text_color=Theme.TEXT_MUTED).pack(anchor="w")
        
        # File Reference
        self.source_files.append({"path": filepath, "widget": row_frame, "letter": letter, "page_count": page_count})
        
        # Controls Row (Range + Trash)
        controls_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        controls_frame.pack(anchor="w", pady=(5, 0))
        
        # Range Entry
        ctk.CTkLabel(controls_frame, text="Rango:", font=(Theme.FONT_FAMILY, 9), text_color=Theme.TEXT_MUTED).pack(side="left")
        range_entry = ctk.CTkEntry(controls_frame, width=60, height=20, font=(Theme.FONT_FAMILY, 10), placeholder_text="2-5(, 6-8)")
        range_entry.pack(side="left", padx=2)
        
        # Add Range Button
        ctk.CTkButton(controls_frame, text="+", width=20, height=20, 
                      fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER,
                      command=lambda fp=filepath, re=range_entry, pc=page_count: self.add_range_to_dest(fp, re.get(), pc)).pack(side="left", padx=2)

        # Trash Button (Remove File)
        ctk.CTkButton(controls_frame, text="🗑", width=20, height=20, 
                      fg_color=Theme.DANGER, hover_color=Theme.DANGER_HOVER,
                      command=lambda w=row_frame: self.remove_source_file(w)).pack(side="left", padx=(5, 0))

        # Thumbnail Container (Horizontal)
        thumbs_scroll = ctk.CTkScrollableFrame(row_frame, orientation="horizontal", height=150, fg_color="#F9F9F9")
        thumbs_scroll.pack(side="left", fill="x", expand=True)
        
        # Load thumbnails in thread
        threading.Thread(target=self.load_thumbnails, args=(filepath, page_count, thumbs_scroll), daemon=True).start()

    def remove_source_file(self, widget):
        widget.destroy()
        # Remove from list
        self.source_files = [f for f in self.source_files if f["widget"] != widget]

    def process_advanced_selection(self):
        text = self.entry_adv.get()
        if not text:
            return

        # Groups: 1=Letter, 2=Pages
        pattern = r"\(([a-zA-Z]+):([^)]+)\)"
        matches = re.findall(pattern, text)
        
        if not matches:
             messagebox.showinfo("Información", "No se encontraron patrones válidos. Use el formato (Letra:Páginas). Ejemplo: (A:1-3)")
             return

        for letter, range_str in matches:
            target_file = None
            for f in self.source_files:
                if f["letter"].upper() == letter.upper():
                    target_file = f
                    break
            
            if target_file:
                self.add_range_to_dest(target_file["path"], range_str, target_file["page_count"])
            else:
                print(f"Archivo con letra {letter} no encontrado.")

    def add_range_to_dest(self, filepath, range_str, page_count):
        if not range_str:
            return
            
        try:
            pages_to_add = []
            parts = range_str.split(',')
            for part in parts:
                part = part.strip()
                if '-' in part:
                    try:
                        start, end = map(int, part.split('-'))
                    except ValueError:
                        messagebox.showerror("Error", f"Formato de rango inválido: '{part}'. Use números separados por '-'.")
                        return

                    if start > end:
                        messagebox.showerror("Error", f"Rango inválido: {start}-{end}. El inicio debe ser menor o igual al fin.")
                        return
                    
                    if start < 1 or end > page_count:
                        messagebox.showerror("Error", f"El rango {start}-{end} está fuera de los límites. El archivo tiene {page_count} páginas.")
                        return

                    pages_to_add.extend(range(start - 1, end))
                else:
                    try:
                        page = int(part)
                    except ValueError:
                        messagebox.showerror("Error", f"Número de página inválido: '{part}'.")
                        return

                    if page < 1 or page > page_count:
                        messagebox.showerror("Error", f"La página {page} está fuera de los límites. El archivo tiene {page_count} páginas.")
                        return
                        
                    pages_to_add.append(page - 1)
            
            # Add pages
            for page_num in pages_to_add:
                pil_img = ThumbnailManager.get_page_thumbnail(filepath, page_num, size=(90, 120))
                if pil_img:
                    ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(90, 120))
                    self.add_page_to_dest(filepath, page_num, ctk_img, pil_image=pil_img)
                    
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error inesperado: {str(e)}")

    def load_thumbnails(self, filepath, page_count, parent_frame):
        # This runs in a thread. Open the PDF only once via iter_thumbnails.
        for i, img in ThumbnailManager.iter_thumbnails(filepath, size=(90, 120)):
            # Update UI in main thread
            self.after(0, lambda p=parent_frame, im=img, idx=i, fp=filepath: self.add_thumbnail_widget(p, im, idx, fp))

    def add_thumbnail_widget(self, parent, pil_image, page_num, filepath):
        ctk_img = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(90, 120))
        widget = PageThumbnailWidget(parent, image=ctk_img, page_num=page_num)
        widget.pack(side="left", padx=2, pady=2)
        
        widget.on_click = lambda w: self.add_page_to_dest(filepath, page_num, ctk_img, pil_image=pil_image)

    def add_page_to_dest(self, filepath, page_num, image, pil_image=None):
        if self.timeline_placeholder.winfo_exists():
            self.timeline_placeholder.destroy()
            
        # Add to data list
        self.destination_pages.append({
            "path": filepath, 
            "page": page_num, 
            "image": image, 
            "pil_image": pil_image,
            "rotation": 0
        })
        self.refresh_timeline()

    def refresh_timeline(self):
        # Clear current widgets
        for widget in self.timeline_scroll.winfo_children():
            if widget != self.timeline_placeholder:
                widget.destroy()
                
        if not self.destination_pages:
            self.timeline_placeholder = ctk.CTkLabel(self.timeline_scroll, text="Arrastra las páginas aquí", text_color=Theme.TEXT_MUTED)
            self.timeline_placeholder.pack(pady=60, padx=200)
            return
 
        # Re-create widgets based on current list order
        for i, item in enumerate(self.destination_pages):
            widget = PageThumbnailWidget(self.timeline_scroll, image=item["image"], page_num=i,
                                         enable_controls=True,
                                         show_page_num=True,
                                         on_delete=lambda w, idx=i: self.delete_page(idx),
                                         on_rotate=lambda w, idx=i: self.rotate_page(idx),
                                         on_drag_start=lambda e, w, idx=i: self.start_drag(e, w, idx),
                                         on_drag_motion=self.on_drag,
                                         on_drag_end=self.end_drag)
            widget.pack(side="left", padx=2, pady=2)

    def rotate_page(self, index):
        if 0 <= index < len(self.destination_pages):
            item = self.destination_pages[index]
            
            # Update rotation
            item["rotation"] = (item["rotation"] + 90) % 360
            
            # Update display image if we have PIL image
            if item.get("pil_image"):
                # Rotate PIL image (negative to match usual visual rotation)
                rotated_pil = item["pil_image"].rotate(-item["rotation"], expand=True)
                rotated_pil.thumbnail((90, 120)) # Ensure size consistency
                
                # Create new display image
                new_ctk_img = ctk.CTkImage(light_image=rotated_pil, dark_image=rotated_pil, size=rotated_pil.size)
                item["image"] = new_ctk_img
                
                # Update timeline to show update
                self.refresh_timeline()

    def delete_dest_range(self, range_str):
        if not range_str:
            return
            
        try:
            indices_to_delete = set()
            parts = range_str.split(',')
            total_pages = len(self.destination_pages)
            
            for part in parts:
                part = part.strip()
                if '-' in part:
                    try:
                        start, end = map(int, part.split('-'))
                    except ValueError:
                        messagebox.showerror("Error", f"Invalid range format: '{part}'. Use numbers separated by '-'.")
                        return
                        
                    if start > end:
                        messagebox.showerror("Error", f"Invalid range: {start}-{end}. Start must be less than or equal to End.")
                        return
                    
                    if start < 1 or end > total_pages:
                        messagebox.showerror("Error", f"El rango {start}-{end} está fuera de los límites. La composición tiene {total_pages} páginas.")
                        return

                    # Add all indices in range
                    for i in range(start, end + 1):
                        indices_to_delete.add(i - 1)
                else:
                    try:
                        idx = int(part)
                    except ValueError:
                        messagebox.showerror("Error", f"Invalid page number: '{part}'.")
                        return
                        
                    if idx < 1 or idx > total_pages:
                        messagebox.showerror("Error", f"La página {idx} está fuera de los límites. La composición tiene {total_pages} páginas.")
                        return
                        
                    indices_to_delete.add(idx - 1)
            
            # Remove from list 
            for idx in sorted(indices_to_delete, reverse=True):
                self.destination_pages.pop(idx)
                
            self.refresh_timeline()
            
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")

    def delete_page(self, index):
        if 0 <= index < len(self.destination_pages):
            self.destination_pages.pop(index)
            self.refresh_timeline()

    def handle_dropped_files(self, files):
        handled = False
        pdfs = []
        images = []
        word_files = []
        ppt_files = []
        
        for f in files:
            ext = f.lower()
            if ext.endswith('.pdf'):
                pdfs.append(f)
                handled = True
            elif ext.endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                images.append(f)
                handled = True
            elif ext.endswith(('.docx', '.doc')):
                word_files.append(f)
                handled = True
            elif ext.endswith(('.pptx', '.ppt')):
                ppt_files.append(f)
                handled = True
        
        if pdfs:
            for pdf in pdfs:
                self.process_file(pdf)
        
        if word_files:
            self.process_dropped_word_files(word_files)

        if ppt_files:
            self.process_dropped_ppt_files(ppt_files)
                
        if images:
            self.process_dropped_images(images)
            
        return handled

    def process_dropped_word_files(self, files):
        prog_win = ctk.CTkToplevel(self)
        prog_win.title("Convirtiendo documentos Word...")
        prog_win.geometry("300x150")
        prog_win.attributes("-topmost", True)
        
        label = ctk.CTkLabel(prog_win, text="Convirtiendo Word a PDF...", font=(Theme.FONT_FAMILY, 14))
        label.pack(pady=(20, 10))
        
        progress = ctk.CTkProgressBar(prog_win, width=200)
        progress.pack(pady=10)
        progress.set(0)
        
        status = ctk.CTkLabel(prog_win, text="0 / 0")
        status.pack(pady=5)
        
        threading.Thread(target=self._convert_word_thread, args=(files, prog_win, progress, status, label)).start()

    def _convert_word_thread(self, files, prog_win, progress, status_lbl, label_lbl):
        from app.core.converters import Converter
        import tempfile
        import pythoncom
        
        pythoncom.CoInitialize()
        
        total = len(files)
        temp_dir = tempfile.gettempdir()
        
        for i, doc_path in enumerate(files):
            # Update UI (siempre en el hilo principal)
            prog = (i) / total
            self.ui(lambda p=prog: progress.set(p))
            self.ui(lambda d=doc_path: label_lbl.configure(text=f"Convirtiendo: {os.path.basename(d)}"))
            self.ui(lambda i=i: status_lbl.configure(text=f"{i+1} / {total}"))

            try:
                # Convert Doc to PDF
                output_pdf_name = f"converted_{os.path.basename(doc_path)}.pdf"
                output_pdf = os.path.join(temp_dir, output_pdf_name)

                Converter.word_to_pdf(doc_path, output_pdf)

                # Add to source files (Main Thread)
                self.after(0, lambda p=output_pdf: self.process_file(p))

            except Exception as e:
                print(f"Error converting word file {doc_path}: {e}")
        
        self.after(0, prog_win.destroy)

    def process_dropped_ppt_files(self, files):
        prog_win = ctk.CTkToplevel(self)
        prog_win.title("Convirtiendo Presentaciones...")
        prog_win.geometry("300x150")
        prog_win.attributes("-topmost", True)
        
        label = ctk.CTkLabel(prog_win, text="Convirtiendo PowerPoint a PDF...", font=(Theme.FONT_FAMILY, 14))
        label.pack(pady=(20, 10))
        
        progress = ctk.CTkProgressBar(prog_win, width=200)
        progress.pack(pady=10)
        progress.set(0)
        
        status = ctk.CTkLabel(prog_win, text="0 / 0")
        status.pack(pady=5)
        
        threading.Thread(target=self._convert_ppt_thread, args=(files, prog_win, progress, status, label)).start()

    def _convert_ppt_thread(self, files, prog_win, progress, status_lbl, label_lbl):
        from app.core.converters import Converter
        import tempfile
        import pythoncom
        
        pythoncom.CoInitialize()
        
        total = len(files)
        temp_dir = tempfile.gettempdir()
        
        for i, ppt_path in enumerate(files):
            prog = (i) / total
            self.ui(lambda p=prog: progress.set(p))
            self.ui(lambda d=ppt_path: label_lbl.configure(text=f"Convirtiendo: {os.path.basename(d)}"))
            self.ui(lambda i=i: status_lbl.configure(text=f"{i+1} / {total}"))

            try:
                # Convert PPT to PDF
                output_pdf_name = f"converted_{os.path.basename(ppt_path)}.pdf"
                output_pdf = os.path.join(temp_dir, output_pdf_name)

                Converter.powerpoint_to_pdf(ppt_path, output_pdf)
                self.after(0, lambda p=output_pdf: self.process_file(p))

            except Exception as e:
                print(f"Error converting ppt file {ppt_path}: {e}")
        
        self.after(0, prog_win.destroy)

    def process_dropped_images(self, images):
        prog_win = ctk.CTkToplevel(self)
        prog_win.title("Convirtiendo Imágenes...")
        prog_win.geometry("300x150")
        prog_win.attributes("-topmost", True)
        
        label = ctk.CTkLabel(prog_win, text="Convirtiendo imágenes a PDF...", font=(Theme.FONT_FAMILY, 14))
        label.pack(pady=(20, 10))
        
        progress = ctk.CTkProgressBar(prog_win, width=200)
        progress.pack(pady=10)
        progress.set(0)
        
        status = ctk.CTkLabel(prog_win, text="0 / 0")
        status.pack(pady=5)
        
        threading.Thread(target=self._convert_images_thread, args=(images, prog_win, progress, status, label)).start()

    def _convert_images_thread(self, images, prog_win, progress, status_lbl, label_lbl):
        from app.core.converters import Converter
        import tempfile
        
        total = len(images)
        temp_dir = tempfile.gettempdir()
        
        for i, img_path in enumerate(images):
            prog = (i) / total
            self.ui(lambda p=prog: progress.set(p))
            self.ui(lambda d=img_path: label_lbl.configure(text=f"Convirtiendo: {os.path.basename(d)}"))
            self.ui(lambda i=i: status_lbl.configure(text=f"{i+1} / {total}"))

            try:
                # Convert image to PDF
                output_pdf_name = f"temp_img_{os.path.basename(img_path)}.pdf"
                output_pdf = os.path.join(temp_dir, output_pdf_name)
                
                Converter.images_to_pdf([img_path], output_pdf)
                
                from PIL import Image as PILImage
                pil_img = PILImage.open(img_path)
                pil_img.thumbnail((90, 120))
                
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(90, 120))
                self.after(0, lambda p=output_pdf, im=ctk_img, pi=pil_img: self.add_page_to_dest(p, 0, im, pil_image=pi))
                
            except Exception as e:
                print(f"Error converting image {img_path}: {e}")
        
        self.after(0, prog_win.destroy)

    # --- Drag Logic ---
    def start_drag(self, event, widget, index):
        self.drag_data["item"] = widget
        self.drag_data["index"] = index
        self.drag_data["x"] = event.x_root
        widget.configure(fg_color="#E0E0E0") 

    def on_drag(self, event, widget):
        pass

    def end_drag(self, event, widget):
        if self.drag_data["index"] is None:
            return

        widget.configure(fg_color="transparent") 
        
        drop_x = event.x_root
        
        closest_index = -1
        min_dist = float('inf')
        
        widgets = [w for w in self.timeline_scroll.winfo_children() if isinstance(w, PageThumbnailWidget)]
        
        for i, w in enumerate(widgets):
            w_center = w.winfo_rootx() + (w.winfo_width() / 2)
            dist = abs(drop_x - w_center)
            if dist < min_dist:
                min_dist = dist
                closest_index = i
        
        if closest_index != -1 and closest_index != self.drag_data["index"]:
            item = self.destination_pages.pop(self.drag_data["index"])
            self.destination_pages.insert(closest_index, item)
            self.refresh_timeline()
            
        self.drag_data = {"item": None, "index": None, "x": 0}

    def create_pdf(self):
        if not self.destination_pages:
            messagebox.showwarning("Advertencia", "¡No hay páginas en la composición!")
            return
            
        output_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("Archivos PDF", "*.pdf")])
        if output_path:
            try:
                PDFManager.create_from_pages(self.destination_pages, output_path)
                
                if messagebox.askyesno("Éxito", "PDF creado con éxito. ¿Desea visualizarlo?"):
                    from app.gui.pages.visualization_page import VisualizationPage
                    self.controller.show_page(VisualizationPage)
                    self.controller.current_page.load_pdf(output_path)
                    
            except Exception as e:
                messagebox.showerror("Error", f"Ocurrió un error: {str(e)}")

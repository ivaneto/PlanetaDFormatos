import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os
from app.gui.pages.base_page import BasePage
from app.core.pdf_ops import PDFManager
from app.core.converters import Converter
from app.gui.theme import Theme

class MultiSplitPage(BasePage):
    def create_widgets(self):
        self.selected_file = None
        self.total_pages = 0
        self.ranges = []
        
        # Header
        header = ctk.CTkLabel(self.content_frame, text="Dividir PDF", font=(Theme.FONT_FAMILY, 24, "bold"), text_color=Theme.TEXT_MAIN)
        header.pack(pady=(20, 10))
        
        # --- File Selection ---
        top_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=10)
        
        self.file_label = ctk.CTkLabel(top_frame, text="Ningún archivo seleccionado", font=(Theme.FONT_FAMILY, 14), text_color="gray", anchor="w")
        self.file_label.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        ctk.CTkButton(top_frame, text="Seleccionar PDF", command=self.select_file,
                      fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER, font=(Theme.FONT_FAMILY, 14)).pack(side="right")
        
        # --- Actions ---
        bottom_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", padx=20, pady=20)
        self.action_var = tk.StringVar(value="split_ranges")
        
        # Process Button
        self.btn_process = ctk.CTkButton(bottom_frame, text="Crear", command=self.process_action,
                                         fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER, font=(Theme.FONT_FAMILY, 16, "bold"), width=150, height=40)
        self.btn_process.pack(side="bottom", pady=(10, 0))

        # Options Frame
        options_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        options_frame.pack(side="bottom", pady=10)
        
        # Compact Radio Buttons
        # Row 1
        ctk.CTkRadioButton(options_frame, text="🖼️ Rango Imágenes", variable=self.action_var, value="images_range").grid(row=0, column=0, padx=15, pady=5)
        ctk.CTkRadioButton(options_frame, text="🖼️ Todo Imágenes", variable=self.action_var, value="images_all").grid(row=0, column=1, padx=15, pady=5)
        ctk.CTkRadioButton(options_frame, text="✂️ Dividir Rangos", variable=self.action_var, value="split_ranges").grid(row=0, column=2, padx=15, pady=5)
        
        # Row 2
        ctk.CTkRadioButton(options_frame, text="✂️ Dividir Todo", variable=self.action_var, value="split_all").grid(row=1, column=0, padx=15, pady=5)
        ctk.CTkRadioButton(options_frame, text="📑 Unir Rangos", variable=self.action_var, value="merge_ranges").grid(row=1, column=1, padx=15, pady=5)

        # --- Split Columns ---
        
        center_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        center_frame.pack(side="top", fill="both", expand=True, padx=20, pady=10)
        center_frame.grid_columnconfigure(0, weight=1, uniform="group1")
        center_frame.grid_columnconfigure(1, weight=1, uniform="group1")
        center_frame.grid_rowconfigure(0, weight=1)
        
        # Left Column: Entries & Information
        left_col = ctk.CTkFrame(center_frame, fg_color=Theme.CARD_BG_N2, corner_radius=10)
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=0)
        
        ctk.CTkLabel(left_col, text="Información del PDF", font=(Theme.FONT_FAMILY, 18, "bold"), text_color=Theme.TEXT_MAIN).pack(pady=(15, 5))
        
        self.pages_label = ctk.CTkLabel(left_col, text="Páginas Totales: -", font=(Theme.FONT_FAMILY, 14))
        self.pages_label.pack(pady=5)
        
        self.output_count_label = ctk.CTkLabel(left_col, text="PDFs de Salida: 0", font=(Theme.FONT_FAMILY, 14))
        self.output_count_label.pack(pady=5)
        
        ctk.CTkFrame(left_col, height=2, fg_color="gray").pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(left_col, text="Definir Rango", font=(Theme.FONT_FAMILY, 16, "bold"), text_color=Theme.TEXT_MAIN).pack(pady=(0, 10))
        
        # Range Entries
        input_frame = ctk.CTkFrame(left_col, fg_color="transparent")
        input_frame.pack(pady=10)
        
        ctk.CTkLabel(input_frame, text="Desde:", font=(Theme.FONT_FAMILY, 14)).grid(row=0, column=0, padx=5)
        self.start_entry = ctk.CTkEntry(input_frame, width=60, font=(Theme.FONT_FAMILY, 14))
        self.start_entry.grid(row=0, column=1, padx=5)
        
        ctk.CTkLabel(input_frame, text="Hasta:", font=(Theme.FONT_FAMILY, 14)).grid(row=0, column=2, padx=5)
        self.end_entry = ctk.CTkEntry(input_frame, width=60, font=(Theme.FONT_FAMILY, 14))
        self.end_entry.grid(row=0, column=3, padx=5)
        
        self.add_btn = ctk.CTkButton(left_col, text="Añadir Rango", command=self.add_range,
                                     fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER, font=(Theme.FONT_FAMILY, 14, "bold"))
        self.add_btn.pack(pady=20)
        
        # Right Column: Ranges List
        right_col = ctk.CTkFrame(center_frame, fg_color=Theme.CARD_BG_N2, corner_radius=10)
        right_col.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=0)
        
        ctk.CTkLabel(right_col, text="Rangos a Crear", font=(Theme.FONT_FAMILY, 18, "bold"), text_color=Theme.TEXT_MAIN).pack(pady=15)
        
        self.ranges_scroll = ctk.CTkScrollableFrame(right_col, fg_color="transparent")
        self.ranges_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.enable_dnd()
        
    def select_file(self):
        filename = filedialog.askopenfilename(title="Seleccionar archivo PDF", filetypes=[("Archivos PDF", "*.pdf")])
        if filename:
            self.load_pdf(filename)
            
    def load_pdf(self, filename):
        self.selected_file = filename
        self.file_label.configure(text=filename)
        self.total_pages = PDFManager.get_page_count(filename)
        self.pages_label.configure(text=f"Páginas Totales: {self.total_pages}")
        # Reset ranges
        self.ranges = []
        self.refresh_ranges_list()
        
    def add_range(self):
        if not self.selected_file:
            messagebox.showwarning("Advertencia", "Por favor, seleccione un archivo PDF primero.")
            return
            
        start_str = self.start_entry.get().strip()
        end_str = self.end_entry.get().strip()
        
        if not start_str:
            messagebox.showwarning("Advertencia", "Por favor, ingrese al menos la página de inicio.")
            return
            
        try:
            start = int(start_str)
            if end_str:
                end = int(end_str)
            else:
                end = start
        except ValueError:
            messagebox.showerror("Error", "Los números de página deben ser enteros.")
            return
            
        if start < 1 or end > self.total_pages or start > end:
            messagebox.showerror("Error", f"Rango inválido. Debe estar entre 1 y {self.total_pages}, e Inicio <= Fin.")
            return
            
        self.ranges.append((start, end))
        self.start_entry.delete(0, 'end')
        self.end_entry.delete(0, 'end')
        self.refresh_ranges_list()
        
    def remove_range(self, index):
        if 0 <= index < len(self.ranges):
            del self.ranges[index]
            self.refresh_ranges_list()
            
    def refresh_ranges_list(self):
        # Clear existing widgets in scroll frame
        for widget in self.ranges_scroll.winfo_children():
            widget.destroy()
            
        for i, (start, end) in enumerate(self.ranges):
            row = ctk.CTkFrame(self.ranges_scroll, fg_color=("gray85", "gray25"), corner_radius=5)
            row.pack(fill="x", pady=5)
            
            info = f"PDF {i+1}: Páginas {start} - {end}"
            ctk.CTkLabel(row, text=info, font=(Theme.FONT_FAMILY, 14)).pack(side="left", padx=10, pady=5)
            
            # Delete Button
            ctk.CTkButton(row, text="✕", width=30, height=30, fg_color="transparent", text_color="red", hover_color=("gray75", "gray30"),
                          command=lambda idx=i: self.remove_range(idx)).pack(side="right", padx=5)
            
            row.bind("<Button-1>", lambda e, idx=i: self.on_drag_start(e, idx))
            row.bind("<ButtonRelease-1>", self.on_drag_stop)
            
            for child in row.winfo_children():
                if isinstance(child, ctk.CTkLabel):
                    child.bind("<Button-1>", lambda e, idx=i: self.on_drag_start(e, idx))
                    child.bind("<ButtonRelease-1>", self.on_drag_stop)
                          
        self.output_count_label.configure(text=f"PDFs de Salida: {len(self.ranges)}")
        
    def on_drag_start(self, event, index):
        self.drag_source_index = index
        self.drag_cursor = "fleur"
        self.configure(cursor="hand2")

    def on_drag_stop(self, event):
        self.configure(cursor="")
        if not hasattr(self, 'drag_source_index') or self.drag_source_index is None:
            return
            
        x, y = self.winfo_pointerxy()
        target = self.winfo_containing(x, y)

        found_index = -1

        rows = self.ranges_scroll.winfo_children() 

        for idx, widget in enumerate(rows):
            if target == widget or str(target).startswith(str(widget)):
                found_index = idx
                break
                
        if found_index != -1 and found_index != self.drag_source_index:
            item = self.ranges.pop(self.drag_source_index)
            self.ranges.insert(found_index, item)
            self.refresh_ranges_list()
            
        self.drag_source_index = None
        
    def split_custom(self):
        if not self.selected_file:
            messagebox.showwarning("Advertencia", "¡Ningún archivo seleccionado!")
            return
        if not self.ranges:
            messagebox.showwarning("Advertencia", "¡No se han definido rangos!")
            return
            
        output_dir = filedialog.askdirectory(title="Seleccionar Carpeta de Salida para los PDFs divididos")
        if output_dir:
            try:
                base_name = os.path.splitext(os.path.basename(self.selected_file))[0]
                for i, (start, end) in enumerate(self.ranges):
                    output_name = f"{base_name}_part_{i+1}_pages_{start}-{end}.pdf"
                    output_path = os.path.join(output_dir, output_name)
                    PDFManager.extract_range(self.selected_file, start, end, output_path)
                    
                messagebox.showinfo("Éxito", f"¡Se crearon {len(self.ranges)} archivos PDF con éxito!")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def create_images(self):
        if not self.selected_file:
            messagebox.showwarning("Advertencia", "¡Ningún archivo seleccionado!")
            return
        if not self.ranges:
            messagebox.showwarning("Advertencia", "¡No se han definido rangos!")
            return
            
        output_dir = filedialog.askdirectory(title="Select Output Directory for Images")
        if output_dir:
            try:
                # Collect all unique pages
                pages_to_convert = set()
                for start, end in self.ranges:
                    # Convert 1-based range to 0-based indices
                    for p in range(start, end + 1):
                        pages_to_convert.add(p - 1)
                
                sorted_pages = sorted(list(pages_to_convert))
                
                Converter.pdf_to_images(self.selected_file, output_dir, pages=sorted_pages)
                
                messagebox.showinfo("Éxito", f"¡Imágenes creadas para {len(sorted_pages)} páginas específicas!")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def create_images_all(self):
        if not self.selected_file:
            messagebox.showwarning("Advertencia", "¡Ningún archivo seleccionado!")
            return
            
        output_dir = filedialog.askdirectory(title="Select Output Directory for Images")
        if output_dir:
            try:
                # pages=None implies converting all pages
                Converter.pdf_to_images(self.selected_file, output_dir, pages=None)
                messagebox.showinfo("Éxito", "¡Imágenes creadas para todas las páginas!")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def split_all(self):
        if not self.selected_file:
            messagebox.showwarning("Advertencia", "¡Ningún archivo seleccionado!")
            return
            
        output_dir = filedialog.askdirectory(title="Seleccionar Carpeta de Salida para las Páginas divididas")
        if output_dir:
            try:
                PDFManager.split_pdf(self.selected_file, output_dir)
                messagebox.showinfo("Éxito", "¡PDF dividido en páginas individuales con éxito!")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def process_action(self):
        action = self.action_var.get()
        if action == "images_range":
            self.create_images()
        elif action == "images_all":
            self.create_images_all()
        elif action == "split_ranges":
            self.split_custom()
        elif action == "split_all":
            self.split_all()
        elif action == "merge_ranges":
            self.merge_ranges()

    def merge_ranges(self):
        if not self.selected_file:
            messagebox.showwarning("Advertencia", "¡Ningún archivo seleccionado!")
            return
        if not self.ranges:
            messagebox.showwarning("Advertencia", "¡No se han definido rangos!")
            return
        
        output_path = filedialog.asksaveasfilename(title="Guardar PDF unido", defaultextension=".pdf", filetypes=[("Archivos PDF", "*.pdf")])
        if output_path:
            try:
                import fitz
                doc = fitz.open(self.selected_file)
                out_doc = fitz.open()
                
                for start, end in self.ranges:
                    p_start = start - 1
                    p_end = end - 1 
                    
                    if p_start < 0: p_start = 0
                    if p_end >= len(doc): p_end = len(doc) - 1
                    if p_start > p_end: continue
                    
                    out_doc.insert_pdf(doc, from_page=p_start, to_page=p_end)
                    
                out_doc.save(output_path)
                out_doc.close()
                doc.close()
                
                messagebox.showinfo("Éxito", f"¡Se unieron {len(self.ranges)} rangos en un solo PDF!")
                
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {str(e)}")

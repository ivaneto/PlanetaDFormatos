import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
from app.gui.components import dialogs as messagebox
import os
import threading

from app.gui.pages.base_page import BasePage
from app.gui.theme import Theme
from app.core.converters import Converter

class ConversionToolsPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.is_converting = False
        self.cancel_conversion_flag = False

    def create_widgets(self):
        # Encabezado
        header = ctk.CTkLabel(self.content_frame, text="Herramientas de Conversión", 
                              font=(Theme.FONT_FAMILY, 24, "bold"), text_color=Theme.TEXT_MAIN)
        header.pack(pady=20)
        
        # Contenedor principal para las 3 columnas
        self.cols_container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.cols_container.pack(fill="both", expand=True, padx=20, pady=10)
        
        # --- Columna 1: Extraer Texto ---
        self.col1 = self.create_column_frame("Extraer Texto (.txt)", "📄")
        self.create_extract_text_widgets(self.col1)
        
        # --- Columna 2: HTML a PDF ---
        self.col2 = self.create_column_frame("HTML a PDF", "🌐")
        self.create_html_to_pdf_widgets(self.col2)
        
        # --- Columna 3: PDF a HTML ---
        self.col3 = self.create_column_frame("PDF a HTML", "📝")
        self.create_pdf_to_html_widgets(self.col3)
        
        self.enable_dnd()

    def handle_dropped_files(self, files):
        handled = False
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext == '.pdf':
                # Extracción de Texto, luego PDF->HTML
                if not self.txt_pdf_path:
                    self.txt_pdf_path = f
                    self.txt_file_label.configure(text=os.path.basename(f), text_color="black")
                else:
                    # Si la extracción de texto ya tiene archivo, usar para PDF->HTML
                    self.html_pdf_source = f
                    self.lbl_pdf_html.configure(text=os.path.basename(f), text_color="black")
                handled = True
                
            elif ext in ['.html', '.htm']:
                self.html_file_path = f
                self.lbl_html_file.configure(text=os.path.basename(f), text_color="black")
                self.tabview.set("Archivo")
                handled = True
        return handled

    def create_column_frame(self, title, icon):
        frame = ctk.CTkFrame(self.cols_container, fg_color=Theme.SURFACE, corner_radius=15, border_width=1, border_color="gray80")
        frame.pack(side="left", fill="both", expand=True, padx=10, pady=5)
        
        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=15, pady=15)
        
        title_label = ctk.CTkLabel(inner, text=f"{icon} {title}", font=(Theme.FONT_FAMILY, 18, "bold"), text_color=Theme.TEXT_MAIN)
        title_label.pack(pady=(0, 15))
        
        return inner

    # -------------------------------------------------------------------------
    # Lógica de la Columna 1: Extraer Texto
    # -------------------------------------------------------------------------
    def create_extract_text_widgets(self, parent):
        self.txt_pdf_path = None
        self.txt_file_frame = ctk.CTkFrame(parent, fg_color="gray80", border_width=1, border_color="#FFD54F", corner_radius=10)
        self.txt_file_frame.pack(fill="x", pady=10)
        
        self.txt_file_label = ctk.CTkLabel(self.txt_file_frame, text="Seleccionar PDF o soltar aquí", text_color="gray50")
        self.txt_file_label.pack(pady=(20, 5))
        
        btn_select = ctk.CTkButton(self.txt_file_frame, text="Elegir PDF", command=self.select_txt_pdf)
        btn_select.pack(pady=(5, 20))
        
        self.chk_newlines = ctk.CTkCheckBox(parent, text="Mantener salto de línea", text_color=Theme.TEXT_MAIN)
        self.chk_newlines.select()
        self.chk_newlines.pack(pady=10, anchor="w")
        
        btn_extract = ctk.CTkButton(parent, text="Extraer Texto", command=self.run_extract_text,
                                    fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER, font=(Theme.FONT_FAMILY, 14, "bold"))
        btn_extract.pack(fill="x", pady=10)
        pass

    def select_txt_pdf(self):
        f = filedialog.askopenfilename(filetypes=[("Archivos PDF", "*.pdf")])
        if f:
            self.txt_pdf_path = f
            self.txt_file_label.configure(text=os.path.basename(f), text_color="black")

    def run_extract_text(self):
        if not self.txt_pdf_path:
            messagebox.showwarning("Aviso", "Selecciona un PDF primero.")
            return

        formatted = bool(self.chk_newlines.get())
        
        output_path = filedialog.asksaveasfilename(filetypes=[("Archivos de Texto", "*.txt")], defaultextension=".txt")
        if not output_path:
            return

        def _task():
            try:
                Converter.pdf_to_text(self.txt_pdf_path, output_path, preserve_layout=formatted)
                self.after(0, lambda: messagebox.showinfo("Éxito", "Texto extraído y guardado correctamente."))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", f"Error al extraer texto: {e}"))
                
        threading.Thread(target=_task, daemon=True).start()

    # -------------------------------------------------------------------------
    # Lógica de la Columna 2: HTML a PDF
    # -------------------------------------------------------------------------
    def create_html_to_pdf_widgets(self, parent):
        self.tabview = ctk.CTkTabview(parent, height=120)
        self.tabview.pack(fill="x", pady=5)
        self.tabview.add("Archivo")
        self.tabview.add("URL")
        
        self.html_file_path = None
        self.lbl_html_file = ctk.CTkLabel(self.tabview.tab("Archivo"), text="Ningún archivo seleccionado", text_color=Theme.TEXT_MUTED)
        self.lbl_html_file.pack(pady=5)
        ctk.CTkButton(self.tabview.tab("Archivo"), text="Elegir HTML", command=self.select_html_file).pack()
        
        self.entry_url = ctk.CTkEntry(self.tabview.tab("URL"), placeholder_text="https://example.com")
        self.entry_url.pack(fill="x", pady=5, padx=5)
        ctk.CTkButton(self.tabview.tab("URL"), text="Pegar", width=60, command=self.paste_url).pack(pady=5)
        
        opts_frame = ctk.CTkFrame(parent, fg_color="transparent")
        opts_frame.pack(fill="x", pady=5)

        self.var_html_engine = tk.StringVar(value="basic")
        
        opts_frame.grid_columnconfigure(0, weight=1)
        opts_frame.grid_columnconfigure(1, weight=1)

        rb_basic = ctk.CTkRadioButton(opts_frame, text="Básico (Rápido)", variable=self.var_html_engine, value="basic", text_color=Theme.TEXT_MAIN, fg_color=Theme.PRIMARY)
        rb_basic.grid(row=0, column=0, sticky="w", pady=2)
        
        rb_adv = ctk.CTkRadioButton(opts_frame, text="Alta Calidad", variable=self.var_html_engine, value="playwright", text_color=Theme.TEXT_MAIN, fg_color=Theme.PRIMARY)
        rb_adv.grid(row=0, column=1, sticky="w", pady=2)

        # Opciones Avanzadas
        self.adv_opts_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.adv_opts_frame.pack(fill="x", pady=0)
        
        self.chk_landscape = ctk.CTkCheckBox(self.adv_opts_frame, text="Horizontal", text_color=Theme.TEXT_MAIN)
        self.chk_landscape.pack(side="left", padx=5)
        
        self.opt_format = ctk.CTkOptionMenu(self.adv_opts_frame, values=["A4", "Letter", "Legal"], width=80, fg_color=Theme.PRIMARY, button_color=Theme.PRIMARY_HOVER)
        self.opt_format.pack(side="right", padx=5)
        
        def _toggle_opts(*args):
            if self.var_html_engine.get() == "playwright":
                self.adv_opts_frame.pack(fill="x", pady=5, before=btn_convert)
            else:
                self.adv_opts_frame.pack_forget()
        
        self.var_html_engine.trace_add("write", _toggle_opts)
        _toggle_opts() # inicializar
        
        btn_convert = ctk.CTkButton(parent, text="Convertir a PDF", command=self.run_html_to_pdf,
                                    fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER, font=(Theme.FONT_FAMILY, 14, "bold"))
        btn_convert.pack(fill="x", pady=10)

    def select_html_file(self):
        f = filedialog.askopenfilename(filetypes=[("Archivos HTML", "*.html *.htm")])
        if f:
            self.html_file_path = f
            self.lbl_html_file.configure(text=os.path.basename(f), text_color="black")

    def paste_url(self):
        try:
            url = self.clipboard_get()
            self.entry_url.delete(0, "end")
            self.entry_url.insert(0, url)
        except:
            pass
            
    def run_html_to_pdf(self):
        tab = self.tabview.get()
        source = None
        is_url = False
        
        if tab == "Archivo":
            if not self.html_file_path:
                messagebox.showwarning("Aviso", "Selecciona un archivo HTML.")
                return
            source = self.html_file_path
        else:
            url = self.entry_url.get().strip()
            if not url:
                messagebox.showwarning("Aviso", "Ingresa una URL.")
                return
            source = url
            is_url = True
            
        output = filedialog.asksaveasfilename(filetypes=[("Archivos PDF", "*.pdf")], defaultextension=".pdf")
        if not output:
            return

        engine = self.var_html_engine.get()
        landscape = bool(self.chk_landscape.get())
        paper_fmt = self.opt_format.get()

        def _task():
            try:
                if engine == "playwright":
                     Converter.html_to_pdf_playwright(source, output, is_url=is_url, 
                                                      landscape=landscape, paper_format=paper_fmt)
                else:
                    Converter.html_to_pdf(source, output, is_url=is_url)
                
                self.after(0, lambda: messagebox.showinfo("Éxito", "PDF creado correctamente."))
            except ImportError as ie:
                msg = str(ie)
                self.after(0, lambda: messagebox.showerror("Error de Dependencia", msg))
            except Exception as e:
                msg = f"Ocurrió un error:\n{e}"
                self.after(0, lambda: messagebox.showerror("Error", msg))

        threading.Thread(target=_task, daemon=True).start()

    # -------------------------------------------------------------------------
    # Lógica de la Columna 3: PDF a HTML
    # -------------------------------------------------------------------------
    def create_pdf_to_html_widgets(self, parent):
        self.html_pdf_source = None
        self.html_pdf_frame = ctk.CTkFrame(parent, fg_color="gray80", border_width=1, border_color="#FFD54F", corner_radius=10)
        self.html_pdf_frame.pack(fill="x", pady=10)
        
        self.lbl_pdf_html = ctk.CTkLabel(self.html_pdf_frame, text="Seleccionar archivo PDF", text_color="gray50")
        self.lbl_pdf_html.pack(pady=(20, 5))
        
        ctk.CTkButton(self.html_pdf_frame, text="Elegir PDF", command=self.select_pdf_for_html).pack(pady=(5, 20))
        
        info_lbl = ctk.CTkLabel(parent, text="Modo Visual", text_color=Theme.TEXT_MUTED, font=("Arial", 12))
        info_lbl.pack(pady=10)
        
        btn_convert = ctk.CTkButton(parent, text="Convertir a HTML", command=self.run_pdf_to_html,
                                    fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER, font=(Theme.FONT_FAMILY, 14, "bold"))
        btn_convert.pack(fill="x", pady=20)

    def select_pdf_for_html(self):
        f = filedialog.askopenfilename(filetypes=[("Archivos PDF", "*.pdf")])
        if f:
            self.html_pdf_source = f
            self.lbl_pdf_html.configure(text=os.path.basename(f), text_color="black")
            
    def run_pdf_to_html(self):
        if self.is_converting:
            return

        if not self.html_pdf_source:
             messagebox.showwarning("Aviso", "Selecciona un PDF.")
             return
             
        output = filedialog.asksaveasfilename(filetypes=[("Archivos HTML", "*.html")], defaultextension=".html")
        if not output:
            return
            
        mode = "visual"
        
        # Iniciar estado de conversión
        self.is_converting = True
        self.cancel_conversion_flag = False
        
        # Crear ventana de progreso
        self.prog_win = ctk.CTkToplevel(self)
        self.prog_win.title("Convirtiendo PDF a HTML")
        self.prog_win.geometry("350x200")
        self.prog_win.protocol("WM_DELETE_WINDOW", self.cancel_conversion)
        self.prog_win.attributes("-topmost", True)
        
        # Centrar ventana
        self.prog_win.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (350 // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (200 // 2)
        self.prog_win.geometry(f"+{x}+{y}")
        
        ctk.CTkLabel(self.prog_win, text="Convirtiendo...", font=(Theme.FONT_FAMILY, 16, "bold")).pack(pady=(20, 10))
        
        self.progress_bar = ctk.CTkProgressBar(self.prog_win, width=250)
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)
        
        self.progress_label = ctk.CTkLabel(self.prog_win, text="0 / ?")
        self.progress_label.pack(pady=5)
        
        ctk.CTkButton(self.prog_win, text="Cancelar", command=self.cancel_conversion, fg_color=Theme.DANGER, hover_color=Theme.DANGER_HOVER).pack(pady=20)
        
        def _progress_cb(current, total):
            if self.cancel_conversion_flag: return
            
            # Actualizar UI en hilo principal
            prog_val = current / total if total > 0 else 0
            self.after(0, lambda: self.update_progress_ui(prog_val, f"{current} / {total}"))

        def _cancel_check():
            return self.cancel_conversion_flag

        def _task():
            try:
                Converter.pdf_to_html(self.html_pdf_source, output, mode=mode, 
                                      progress_callback=_progress_cb, 
                                      cancel_check=_cancel_check)
                
                if not self.cancel_conversion_flag:
                    self.after(0, lambda: self.finish_conversion(True, "HTML guardado correctamente."))
                else:
                    self.after(0, lambda: self.finish_conversion(False, "Conversión cancelada por el usuario."))
                    
            except Exception as e:
                self.after(0, lambda: self.finish_conversion(False, str(e)))
                
        threading.Thread(target=_task, daemon=True).start()

    def update_progress_ui(self, val, text):
        if self.prog_win.winfo_exists():
            self.progress_bar.set(val)
            self.progress_label.configure(text=text)

    def cancel_conversion(self):
        self.cancel_conversion_flag = True
        if self.prog_win.winfo_exists():
            self.progress_label.configure(text="Cancelando...")

    def finish_conversion(self, success, message):
        self.is_converting = False
        if self.prog_win.winfo_exists():
            self.prog_win.destroy()
            
        if success:
            messagebox.showinfo("Éxito", message)
        else:
            if "cancelada" in message:
                messagebox.showinfo("Cancelado", message)
            else:
                messagebox.showerror("Error", f"Error al convertir: {message}")

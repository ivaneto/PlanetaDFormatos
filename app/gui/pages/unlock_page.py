import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from app.gui.pages.base_page import BasePage
from app.core.pdf_editor import PDFEditorBackend
from app.gui.theme import Theme
import os

class UnlockPage(BasePage):
    def create_widgets(self):
        self.backend = PDFEditorBackend()
        self.full_input_path = ""
        self.password = tk.StringVar()

        # Header
        header = ctk.CTkLabel(self.content_frame, text="Desbloquear PDF", font=(Theme.FONT_FAMILY, 24, "bold"), text_color=Theme.TEXT_MAIN)
        header.pack(pady=20)
        
        # Description
        desc_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        desc_frame.pack(fill="x", padx=40, pady=10)
        desc_lbl = ctk.CTkLabel(desc_frame, text="Elimina la contraseña y restricciones de un archivo PDF protegido.\nNota: Debes conocer la contraseña actual para desbloquearlo.",
                                font=(Theme.FONT_FAMILY, 14), text_color=Theme.TEXT_MAIN, wraplength=800)
        desc_lbl.pack()

        # Main Content Frame
        content_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Input PDF Selection
        input_frame = ctk.CTkFrame(content_frame, fg_color="white", corner_radius=10)
        input_frame.pack(fill="x", pady=20, padx=20)
        
        ctk.CTkLabel(input_frame, text="PDF Protegido:", font=(Theme.FONT_FAMILY, 14, "bold"), text_color=Theme.TEXT_MAIN).pack(side="left", padx=20, pady=20)
        
        self.file_label = ctk.CTkLabel(input_frame, text="Ningún archivo seleccionado", width=300, font=(Theme.FONT_FAMILY, 14), text_color="gray")
        self.file_label.pack(side="left", padx=10, fill="x", expand=True)
        ctk.CTkButton(input_frame, text="Explorar...", command=self.browse_pdf, width=120, height=40,
                      fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER, font=(Theme.FONT_FAMILY, 14, "bold")).pack(side="left", padx=20, pady=20)

        # Password Entry
        pw_frame = ctk.CTkFrame(content_frame, fg_color="white", corner_radius=10)
        pw_frame.pack(fill="x", pady=10, padx=20)
        
        ctk.CTkLabel(pw_frame, text="Contraseña:", font=(Theme.FONT_FAMILY, 14, "bold"), text_color=Theme.TEXT_MAIN).pack(side="left", padx=20, pady=20)
        ctk.CTkEntry(pw_frame, textvariable=self.password, show="*", width=400, font=(Theme.FONT_FAMILY, 14)).pack(side="left", fill="x", expand=True, padx=10, pady=20)
        
        # Action Button
        ctk.CTkButton(self.content_frame, text="Desbloquear PDF", command=self.unlock_pdf, 
                      fg_color=Theme.SUCCESS, hover_color="#0C955A", font=(Theme.FONT_FAMILY, 18, "bold"), width=250, height=50).pack(pady=40)
        
        self.enable_dnd()

    def handle_dropped_files(self, files):
        for f in files:
            if f.lower().endswith('.pdf'):
                self.full_input_path = f
                self.file_label.configure(text=os.path.basename(f), text_color=Theme.TEXT_MAIN)
                return True
        return False

    def browse_pdf(self):
        filename = filedialog.askopenfilename(filetypes=[("Archivos PDF", "*.pdf")])
        if filename:
            self.full_input_path = filename
            self.file_label.configure(text=os.path.basename(filename), text_color=Theme.TEXT_MAIN)

    def unlock_pdf(self):
        input_path = self.full_input_path
        if not input_path or not os.path.exists(input_path):
            messagebox.showwarning("Advertencia", "Por favor seleccione un archivo PDF válido.")
            return

        password = self.password.get()
        if not password:
             messagebox.showwarning("Advertencia", "Por favor ingrese la contraseña del archivo.")
             return

        output_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("Archivos PDF", "*.pdf")])
        if not output_path:
            return
            
        try:
           success = self.backend.unlock_pdf(input_path, output_path, password)
           if success:
               messagebox.showinfo("Éxito", "El PDF ha sido desbloqueado exitosamente.")
               self.file_label.configure(text="Ningún archivo seleccionado", text_color="gray")
               self.full_input_path = ""
               self.password.set("")
           else:
               messagebox.showerror("Error", "No se pudo desbloquear el PDF. Verifique que la contraseña sea correcta.")
               
        except Exception as e:
            messagebox.showerror("Error", f"Error inesperado: {str(e)}")

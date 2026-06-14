import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from app.gui.pages.base_page import BasePage
from app.core.pdf_editor import PDFEditorBackend
from app.gui.theme import Theme
import fitz 
import os

class ProtectPage(BasePage):
    def create_widgets(self):
        self.backend = PDFEditorBackend()
        self.full_input_path = ""
        self.input_pdf = tk.StringVar()
        
        # Passwords
        self.user_pw = tk.StringVar()
        self.owner_pw = tk.StringVar()
        
        # Permissions
        self.perm_print = tk.BooleanVar(value=True)
        self.perm_copy = tk.BooleanVar(value=True)
        self.perm_edit = tk.BooleanVar(value=True)
        self.perm_annot = tk.BooleanVar(value=True)

        # Header
        header = ctk.CTkLabel(self.content_frame, text="Proteger PDF", font=(Theme.FONT_FAMILY, 24, "bold"), text_color=Theme.TEXT_MAIN)
        header.pack(pady=20)
        
        # Description
        desc_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        desc_frame.pack(fill="x", padx=40, pady=10)
        desc_lbl = ctk.CTkLabel(desc_frame, text="Establece contraseñas para restringir el acceso o los permisos de tu archivo PDF.",
                                font=(Theme.FONT_FAMILY, 14), text_color=Theme.TEXT_MAIN)
        desc_lbl.pack()

        # Main Scrollable Content
        content_frame = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Input PDF Section
        input_frame = ctk.CTkFrame(content_frame, fg_color="white", corner_radius=10)
        input_frame.pack(fill="x", pady=10, padx=20)
        ctk.CTkLabel(input_frame, text="PDF de Entrada:", font=(Theme.FONT_FAMILY, 14, "bold"), text_color=Theme.TEXT_MAIN).pack(side="left", padx=20, pady=20)
        
        self.file_label = ctk.CTkLabel(input_frame, text="Ningún archivo seleccionado", width=300, font=(Theme.FONT_FAMILY, 14), text_color="gray")
        self.file_label.pack(side="left", padx=10, fill="x", expand=True)
        ctk.CTkButton(input_frame, text="Explorar...", command=self.browse_pdf, width=100,
                      fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER).pack(side="left", padx=20, pady=20)

        # Password Section
        pw_frame = ctk.CTkFrame(content_frame, fg_color="white", corner_radius=10)
        pw_frame.pack(fill="x", pady=10, padx=20)
        
        ctk.CTkLabel(pw_frame, text="Contraseñas", font=(Theme.FONT_FAMILY, 16, "bold"), text_color=Theme.TEXT_MAIN).pack(pady=10, padx=20, anchor="w")
        
        # User Password
        row1 = ctk.CTkFrame(pw_frame, fg_color="transparent")
        row1.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(row1, text="Contraseña de Usuario (Abrir):", width=200, anchor="w", text_color=Theme.TEXT_MAIN).pack(side="left")
        ctk.CTkEntry(row1, textvariable=self.user_pw, show="*", width=300).pack(side="left", fill="x", expand=True)
        
        # Owner Password
        row2 = ctk.CTkFrame(pw_frame, fg_color="transparent")
        row2.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(row2, text="Contraseña de Propietario (Edit):", width=200, anchor="w", text_color=Theme.TEXT_MAIN).pack(side="left")
        ctk.CTkEntry(row2, textvariable=self.owner_pw, show="*", width=300).pack(side="left", fill="x", expand=True)
        
        ctk.CTkLabel(pw_frame, text="* La contraseña de propietario es necesaria para cambiar permisos en el futuro.", 
                     font=(Theme.FONT_FAMILY, 12, "italic"), text_color="gray").pack(pady=10, padx=20, anchor="w")

        # Permissions Section
        perm_frame = ctk.CTkFrame(content_frame, fg_color="white", corner_radius=10)
        perm_frame.pack(fill="x", pady=10, padx=20)
        
        ctk.CTkLabel(perm_frame, text="Permisos permitidos", font=(Theme.FONT_FAMILY, 16, "bold"), text_color=Theme.TEXT_MAIN).pack(pady=10, padx=20, anchor="w")
        
        grid = ctk.CTkFrame(perm_frame, fg_color="transparent")
        grid.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkCheckBox(grid, text="Imprimir", variable=self.perm_print, fg_color=Theme.PRIMARY).pack(side="left", padx=20)
        ctk.CTkCheckBox(grid, text="Copiar Texto/Img", variable=self.perm_copy, fg_color=Theme.PRIMARY).pack(side="left", padx=20)
        ctk.CTkCheckBox(grid, text="Editar Contenido", variable=self.perm_edit, fg_color=Theme.PRIMARY).pack(side="left", padx=20)
        ctk.CTkCheckBox(grid, text="Anotaciones", variable=self.perm_annot, fg_color=Theme.PRIMARY).pack(side="left", padx=20)

        # Action Button
        ctk.CTkButton(self.content_frame, text="Proteger PDF", command=self.protect_pdf, 
                      fg_color=Theme.SUCCESS, hover_color="#0C955A", font=(Theme.FONT_FAMILY, 18, "bold"), width=250, height=50).pack(pady=20)
        
        self.enable_dnd()

    def handle_dropped_files(self, files):
        for f in files:
            if f.lower().endswith('.pdf'):
                self.full_input_path = f
                self.file_label.configure(text=os.path.basename(f), text_color=Theme.TEXT_MAIN)
                self.check_pdfa_status(f)
                return True
        return False

    def browse_pdf(self):
        filename = filedialog.askopenfilename(filetypes=[("Archivos PDF", "*.pdf")])
        if filename:
            self.full_input_path = filename
            self.file_label.configure(text=os.path.basename(filename), text_color=Theme.TEXT_MAIN)
            self.check_pdfa_status(filename)

    def check_pdfa_status(self, path):
        if self.backend.is_pdfa(path):
             messagebox.showwarning(
                "Advertencia PDF/A", 
                "Estás cargando un PDF/A.\nSi continúas y lo proteges, perderá su validación de archivado."
            )

    def protect_pdf(self):
        input_path = self.full_input_path
        if not input_path or not os.path.exists(input_path):
            messagebox.showwarning("Advertencia", "Por favor seleccione un archivo PDF válido.")
            return
            

        user_pw = self.user_pw.get()
        owner_pw = self.owner_pw.get()
        
        # Check if any permission is restricted (unchecked)
        permissions_restricted = not (self.perm_print.get() and 
                                    self.perm_copy.get() and 
                                    self.perm_edit.get() and 
                                    self.perm_annot.get())

        has_password = bool(user_pw or owner_pw)

        if not has_password and not permissions_restricted:
            messagebox.showwarning("Advertencia", "Debe establecer al menos una contraseña o restringir algún permiso.")
            return

        if permissions_restricted and not owner_pw:
            confirm = messagebox.askyesno(
                "Seguridad Baja",
                "Ha establecido restricciones pero no una contraseña de propietario.\n\n"
                "Sin contraseña de propietario, las restricciones son fáciles de eliminar.\n\n"
                "¿Desea continuar de todos modos?"
            )
            if not confirm:
                return

        output_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("Archivos PDF", "*.pdf")])
        if not output_path:
            return
            
        # Calculate permissions mask
        perms = fitz.PDF_PERM_ACCESSIBILITY
        
        if self.perm_print.get(): perms |= fitz.PDF_PERM_PRINT
        if self.perm_copy.get(): perms |= fitz.PDF_PERM_COPY
        if self.perm_edit.get(): perms |= fitz.PDF_PERM_MODIFY
        if self.perm_annot.get(): perms |= fitz.PDF_PERM_ANNOTATE
            
        try:
           success = self.backend.encrypt_pdf(input_path, output_path, user_pw, owner_pw, perms)
           if success:
               messagebox.showinfo("Éxito", "El PDF ha sido protegido exitosamente.")
               self.full_input_path = ""
               self.file_label.configure(text="Ningún archivo seleccionado", text_color="gray")
               self.user_pw.set("")
               self.owner_pw.set("")
           else:
               messagebox.showerror("Error", "Ocurrió un error al proteger el PDF.")
               
        except Exception as e:
            messagebox.showerror("Error", f"Error inesperado: {str(e)}")

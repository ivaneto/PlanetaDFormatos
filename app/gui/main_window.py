import customtkinter as ctk
from tkinterdnd2 import TkinterDnD, DND_ALL
from app.gui.theme import Theme
from app.gui.pages.dashboard_page import DashboardPage
from app.gui.pages.merge_page import MergePage
from app.gui.pages.split_page import SplitPage
from app.gui.pages.multi_split_page import MultiSplitPage
from app.gui.pages.img2pdf_page import Img2PdfPage
from app.gui.pages.pdf2img_page import Pdf2ImgPage
from app.gui.pages.watermark_page import WatermarkPage
from app.gui.pages.pdf2word_page import Pdf2WordPage
from app.gui.pages.word2pdf_page import Word2PdfPage
from app.gui.pages.excel2pdf_page import Excel2PdfPage
from app.gui.pages.ppt2pdf_page import Ppt2PdfPage
from app.gui.pages.pdf2excel_page import Pdf2ExcelPage
from app.gui.pages.pdf2ppt_page import Pdf2PptPage
from app.gui.pages.conversion_tools_page import ConversionToolsPage
from app.gui.pages.form_filler_page import FormFillerPage
from app.gui.pages.page_numbers_page import PageNumbersPage
from app.gui.pages.rotate_page import RotatePage
from app.gui.pages.compress_page import CompressPage
from app.gui.pages.crop_page import CropPage
from app.gui.pages.ocr_page import OCRPage
from app.gui.pages.edit_pdf_page import EditPdfPage
from app.gui.pages.sign_page import SignPdfPage
from app.gui.pages.redact_page import RedactPage
from app.gui.pages.flatten_page import FlattenPage
from app.gui.pages.protect_page import ProtectPage
from app.gui.pages.unlock_page import UnlockPage
from app.gui.pages.metadata_page import MetadataPage
from app.gui.pages.repair_page import RepairPage
from app.gui.pages.pdfa_page import PdfaPage
from app.gui.pages.visualization_page import VisualizationPage

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")


# Estructura de navegación: (sección, [(icono, etiqueta, página)])
NAV_SECTIONS = [
    ("Principal", [
        ("🏠", "Inicio", DashboardPage),
        ("📖", "Visualizador", VisualizationPage),
        ("🔄", "Organizar", RotatePage),
        ("📄", "Unir PDF", MergePage),
    ]),
    ("Manipular", [
        ("📑", "Dividir", MultiSplitPage),
        ("✂️", "Recortar", CropPage),
        ("🖼️", "Imágenes a PDF", Img2PdfPage),
        ("#", "Números de página", PageNumbersPage),
    ]),
    ("Editar", [
        ("👁️", "OCR", OCRPage),
        ("💧", "Marca de agua", WatermarkPage),
        ("⬛", "Censurar", RedactPage),
        ("✏️", "Editar PDF", EditPdfPage),
        ("✍️", "Firmar", SignPdfPage),
        ("📝", "Formularios", FormFillerPage),
    ]),
    ("Convertir", [
        ("🛠️", "Herramientas", ConversionToolsPage),
        ("📰", "PDF a Word", Pdf2WordPage),
        ("📘", "Word a PDF", Word2PdfPage),
        #("📊", "PDF a Excel", Pdf2ExcelPage),
        #("📗", "Excel a PDF", Excel2PdfPage),
        #("📽️", "PDF a PPT", Pdf2PptPage),
        ("📕", "PPT a PDF", Ppt2PdfPage),
        ("📦", "PDF/A", PdfaPage),
    ]),
    ("Seguridad", [
        ("🛡️", "Proteger", ProtectPage),
        ("🔓", "Desbloquear", UnlockPage),
        ("ℹ️", "Metadatos", MetadataPage),
        ("🩹", "Reparar", RepairPage),
        ("📉", "Comprimir", CompressPage),
        ("🔨", "Aplanar", FlattenPage),
    ]),
]


class MainWindow(ctk.CTk, TkinterDnD.DnDWrapper):
    SIDEBAR_EXPANDED = 230
    SIDEBAR_COLLAPSED = 64

    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)
        self.title("Planeta De Formatos -> PDF")
        self.geometry("1400x900")
        self.configure(fg_color=Theme.BACKGROUND)

        self.grid_columnconfigure(0, weight=0)  # Sidebar
        self.grid_columnconfigure(1, weight=1)  # Content
        self.grid_rowconfigure(0, weight=1)

        self.sidebar_expanded = True
        self.nav_buttons = {}   # page_class -> button
        self.page_titles = {}   # page_class -> (icono, etiqueta)
        self.current_page = None
        self._active_page_class = None

        self.create_widgets()
        self.show_dashboard()

    # ------------------------------------------------------------------
    # Construcción de la interfaz
    # ------------------------------------------------------------------
    def create_widgets(self):
        # ---- Barra lateral ----
        self.sidebar_frame = ctk.CTkScrollableFrame(
            self, width=self.SIDEBAR_EXPANDED, corner_radius=0, fg_color=Theme.SIDEBAR_BG
        )
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")

        # Cabecera del sidebar: logo + botón de colapsar
        header = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        header.pack(fill="x", pady=(16, 10), padx=10)

        self.logo_label = ctk.CTkLabel(
            header, text="📚 Planeta PDF",
            font=(Theme.FONT_FAMILY, 16, "bold"), text_color=Theme.TEXT_ON_DARK
        )
        self.logo_label.pack(side="left", padx=(4, 0))

        self.btn_collapse = ctk.CTkButton(
            header, text="≡", width=34, height=30, fg_color="transparent",
            hover_color=Theme.PRIMARY, font=("Arial", 18), command=self.toggle_sidebar
        )
        self.btn_collapse.pack(side="right")

        self.btn_theme = ctk.CTkButton(
            header, text="🌙", width=34, height=30, fg_color="transparent",
            hover_color=Theme.PRIMARY, font=("Arial", 16), command=self.toggle_appearance
        )
        self.btn_theme.pack(side="right", padx=(0, 4))

        # Secciones + items
        self.section_labels = []
        for section, items in NAV_SECTIONS:
            lbl = ctk.CTkLabel(
                self.sidebar_frame, text=section.upper(), anchor="w",
                font=(Theme.FONT_FAMILY, 10, "bold"), text_color=Theme.SECONDARY
            )
            lbl.pack(fill="x", padx=16, pady=(14, 2))
            self.section_labels.append(lbl)

            for icon, label, page in items:
                self._create_nav_item(icon, label, page)

        # ---- Área de contenido ----
        self.content_area = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content_area.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        # Barra superior: título dinámico de la herramienta actual
        self.top_bar = ctk.CTkFrame(self.content_area, height=60, fg_color="transparent")
        self.top_bar.pack(fill="x", pady=(0, 16))

        self.page_title = ctk.CTkLabel(
            self.top_bar, text="Inicio",
            font=(Theme.FONT_FAMILY, 26, "bold"), text_color=Theme.PRIMARY
        )
        self.page_title.pack(side="left")

        self.btn_home_top = ctk.CTkButton(
            self.top_bar, text="← Inicio", width=90, height=34,
            fg_color="transparent", border_width=1, border_color=Theme.PRIMARY,
            text_color=Theme.PRIMARY, hover_color=Theme.ACCENT_SOFT,
            command=self.show_dashboard
        )
        self.btn_home_top.pack(side="right")

    def _create_nav_item(self, icon, label, page):
        btn = ctk.CTkButton(
            self.sidebar_frame, text=f"  {icon}   {label}", anchor="w",
            height=38, corner_radius=8, fg_color="transparent",
            hover_color=Theme.PRIMARY, text_color=Theme.TEXT_ON_DARK,
            font=(Theme.FONT_FAMILY, 13), command=lambda p=page: self.show_page(p)
        )
        btn.pack(fill="x", padx=8, pady=1)
        btn._nav_icon = icon
        btn._nav_label = label
        self.nav_buttons[page] = btn
        self.page_titles[page] = (icon, label)

    # ------------------------------------------------------------------
    # Colapsar / expandir
    # ------------------------------------------------------------------
    def toggle_sidebar(self):
        self.sidebar_expanded = not self.sidebar_expanded
        if self.sidebar_expanded:
            self.sidebar_frame.configure(width=self.SIDEBAR_EXPANDED)
            self.logo_label.configure(text="📚 Planeta PDF")
            for lbl in self.section_labels:
                lbl.pack(fill="x", padx=16, pady=(14, 2))
            for page, btn in self.nav_buttons.items():
                btn.configure(text=f"  {btn._nav_icon}   {btn._nav_label}", anchor="w")
        else:
            self.sidebar_frame.configure(width=self.SIDEBAR_COLLAPSED)
            self.logo_label.configure(text="📚")
            for lbl in self.section_labels:
                lbl.pack_forget()
            for page, btn in self.nav_buttons.items():
                btn.configure(text=btn._nav_icon, anchor="center")

    # ------------------------------------------------------------------
    # Navegación
    # ------------------------------------------------------------------
    def toggle_appearance(self):
        """Alterna entre modo claro y oscuro. Los tokens de Theme son tuplas
        (claro, oscuro), por lo que CustomTkinter actualiza los colores solo."""
        new_mode = "Dark" if ctk.get_appearance_mode() == "Light" else "Light"
        ctk.set_appearance_mode(new_mode)
        self.btn_theme.configure(text="☀️" if new_mode == "Dark" else "🌙")

    def show_dashboard(self):
        self.show_page(DashboardPage)

    def show_page(self, page_class):
        if self.current_page:
            self.current_page.destroy()

        self.current_page = page_class(self.content_area, self)
        self.current_page.pack(fill="both", expand=True)

        self._set_active(page_class)

    def _set_active(self, page_class):
        # Resaltar el botón de la página activa
        for page, btn in self.nav_buttons.items():
            if page == page_class:
                btn.configure(fg_color=Theme.PRIMARY)
            else:
                btn.configure(fg_color="transparent")
        self._active_page_class = page_class

        # Actualizar título de la barra superior
        icon, label = self.page_titles.get(page_class, ("", page_class.__name__))
        self.page_title.configure(text=f"{icon}  {label}".strip())

    def run(self):
        self.mainloop()

    # ------------------------------------------------------------------
    # Enrutado de archivos arrastrados al dashboard
    # ------------------------------------------------------------------
    def route_files(self, files):
        if not isinstance(self.current_page, DashboardPage):
            return

        pdfs = [f for f in files if f.lower().endswith('.pdf')]
        images = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
        words = [f for f in files if f.lower().endswith(('.docx', '.doc'))]
        excels = [f for f in files if f.lower().endswith(('.xlsx', '.xls'))]
        ppts = [f for f in files if f.lower().endswith(('.pptx', '.ppt'))]

        target_page = None
        target_files = []

        if pdfs:
            target_page = MergePage
            target_files = pdfs
        elif images:
            target_page = Img2PdfPage
            target_files = images
        elif words:
            target_page = Word2PdfPage
            target_files = words
        elif excels:
            target_page = Excel2PdfPage
            target_files = excels
        elif ppts:
            target_page = Ppt2PdfPage
            target_files = ppts

        if target_page:
            if not isinstance(self.current_page, target_page):
                self.show_page(target_page)
            if hasattr(self.current_page, 'handle_dropped_files'):
                self.current_page.handle_dropped_files(target_files)

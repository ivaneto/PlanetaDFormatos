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
from app.gui.pages.conversion_tools_page import ConversionToolsPage
from app.gui.pages.form_filler_page import FormFillerPage
from app.gui.pages.page_numbers_page import PageNumbersPage
from app.gui.pages.rotate_page import RotatePage
from app.gui.pages.compress_page import CompressPage
from app.gui.pages.crop_page import CropPage
from app.gui.pages.ocr_page import OCRPage
from app.gui.pages.edit_pdf_page import EditPdfPage
from app.gui.pages.sign_page import SignPdfPage
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

class MainWindow(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)
        self.title("Planeta De Formatos -> PDF")
        self.geometry("1400x900")
        self.configure(fg_color=Theme.BACKGROUND)
        
        self.grid_columnconfigure(0, weight=0) # Barra lateral
        self.grid_columnconfigure(1, weight=1) # Contenido
        self.grid_rowconfigure(0, weight=1)
        
        self.create_widgets()
        self.show_dashboard()
        
    def create_widgets(self):
        # Marco de la barra lateral
        self.sidebar_frame = ctk.CTkScrollableFrame(self, width=100, corner_radius=0, fg_color=Theme.SIDEBAR_BG)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        
        # Iconos/Botones de la barra lateral
        # Botón de Inicio
        self.btn_home = ctk.CTkButton(self.sidebar_frame, text="🏠", width=50, height=50,
                                      fg_color="transparent", hover_color=Theme.PRIMARY_HOVER,
                                      font=("Arial", 24), command=self.show_dashboard)
        self.btn_home.pack(pady=(20, 10), padx=10)

        # Botón del Visualizador
        self.btn_viz = ctk.CTkButton(self.sidebar_frame, text="📖", width=50, height=50,
                                       fg_color="transparent", hover_color=Theme.PRIMARY_HOVER,
                                       font=("Arial", 24), command=lambda: self.show_page(VisualizationPage))
        self.btn_viz.pack(pady=10, padx=10)

        # Organizar PDF
        self.btn_rotate = ctk.CTkButton(self.sidebar_frame, text="🔄", width=50, height=50,
                                        fg_color="transparent", hover_color=Theme.PRIMARY_HOVER,
                                        font=("Arial", 24), command=lambda: self.show_page(RotatePage))
        self.btn_rotate.pack(pady=10, padx=10)

        # Fusionar PDF
        self.btn_merge = ctk.CTkButton(self.sidebar_frame, text="📄", width=50, height=50,
                                       fg_color="transparent", hover_color=Theme.PRIMARY_HOVER,
                                       font=("Arial", 24), command=lambda: self.show_page(MergePage))
        self.btn_merge.pack(pady=10, padx=10)

        # División Múltiple
        self.btn_multi = ctk.CTkButton(self.sidebar_frame, text="📑", width=50, height=50,
                                       fg_color="transparent", hover_color=Theme.PRIMARY_HOVER,
                                       font=("Arial", 24), command=lambda: self.show_page(MultiSplitPage))
        self.btn_multi.pack(pady=10, padx=10)

        # Recortar PDF
        self.btn_crop = ctk.CTkButton(self.sidebar_frame, text="✂️", width=50, height=50,
                                         fg_color="transparent", hover_color=Theme.PRIMARY_HOVER,
                                         font=("Arial", 24), command=lambda: self.show_page(CropPage))
        self.btn_crop.pack(pady=10, padx=10)

        # Imágenes a PDF
        self.btn_img2pdf = ctk.CTkButton(self.sidebar_frame, text="🖼️", width=50, height=50,
                                         fg_color="transparent", hover_color=Theme.PRIMARY_HOVER,
                                         font=("Arial", 24), command=lambda: self.show_page(Img2PdfPage))
        self.btn_img2pdf.pack(pady=10, padx=10)

        # Números de Página
        self.btn_pagenum = ctk.CTkButton(self.sidebar_frame, text="#", width=50, height=50,
                                         fg_color="transparent", hover_color=Theme.PRIMARY_HOVER,
                                         font=("Arial", 24), command=lambda: self.show_page(PageNumbersPage))
        self.btn_pagenum.pack(pady=10, padx=10)

        # OCR
        self.btn_ocr = ctk.CTkButton(self.sidebar_frame, text="👁️", width=50, height=50,
                                         fg_color="transparent", hover_color=Theme.PRIMARY_HOVER,
                                         font=("Arial", 24), command=lambda: self.show_page(OCRPage))
        self.btn_ocr.pack(pady=10, padx=10)

        # Marca de Agua
        self.btn_watermark = ctk.CTkButton(self.sidebar_frame, text="💧", width=50, height=50,
                                           fg_color="transparent", hover_color=Theme.PRIMARY_HOVER,
                                           font=("Arial", 24), command=lambda: self.show_page(WatermarkPage))
        self.btn_watermark.pack(pady=10, padx=10)

        # Redactar PDF
        self.btn_redact = ctk.CTkButton(self.sidebar_frame, text="⬛", width=50, height=50,
                                         fg_color="transparent", hover_color=Theme.PRIMARY_HOVER,
                                         font=("Arial", 24), command=lambda: self.show_page(RedactPage))
        self.btn_redact.pack(pady=10, padx=10)

        # Editar PDF
        self.btn_edit = ctk.CTkButton(self.sidebar_frame, text="✏️", width=50, height=50,
                                       fg_color="transparent", hover_color=Theme.PRIMARY_HOVER,
                                       font=("Arial", 24), command=lambda: self.show_page(EditPdfPage))
        self.btn_edit.pack(pady=10, padx=10)

        # Firmar PDF
        self.btn_sign = ctk.CTkButton(self.sidebar_frame, text="✍️", width=50, height=50,
                                       fg_color="transparent", hover_color=Theme.PRIMARY_HOVER,
                                       font=("Arial", 24), command=lambda: self.show_page(SignPdfPage))
        self.btn_sign.pack(pady=10, padx=10)

        # Rellenador de Formularios (Nuevo)
        self.btn_form = ctk.CTkButton(self.sidebar_frame, text="📝", width=50, height=50,
                                         fg_color="transparent", hover_color=Theme.PRIMARY_HOVER,
                                         font=("Arial", 24), command=lambda: self.show_page(FormFillerPage))
        self.btn_form.pack(pady=10, padx=10)

        # Herramientas / Conversión (Nueva Página)
        self.btn_tools = ctk.CTkButton(self.sidebar_frame, text="🛠️", width=50, height=50,
                                         fg_color="transparent", hover_color=Theme.PRIMARY_HOVER,
                                         font=("Arial", 24), command=lambda: self.show_page(ConversionToolsPage))
        self.btn_tools.pack(pady=10, padx=10)

        # PDF/A
        self.btn_pdfa = ctk.CTkButton(self.sidebar_frame, text="📦", width=50, height=50,
                                         fg_color="transparent", hover_color=Theme.PRIMARY_HOVER,
                                         font=("Arial", 24), command=lambda: self.show_page(PdfaPage))
        self.btn_pdfa.pack(pady=10, padx=10)

        # Proteger PDF
        self.btn_protect = ctk.CTkButton(self.sidebar_frame, text="🛡️", width=50, height=50,
                                         fg_color="transparent", hover_color=Theme.PRIMARY_HOVER,
                                         font=("Arial", 24), command=lambda: self.show_page(ProtectPage))
        self.btn_protect.pack(pady=10, padx=10)

        # Desbloquear PDF
        self.btn_unlock = ctk.CTkButton(self.sidebar_frame, text="🔓", width=50, height=50,
                                         fg_color="transparent", hover_color=Theme.PRIMARY_HOVER,
                                         font=("Arial", 24), command=lambda: self.show_page(UnlockPage))
        self.btn_unlock.pack(pady=10, padx=10)

        # Metadatos PDF
        self.btn_metadata = ctk.CTkButton(self.sidebar_frame, text="ℹ️", width=50, height=50,
                                         fg_color="transparent", hover_color=Theme.PRIMARY_HOVER,
                                         font=("Arial", 24), command=lambda: self.show_page(MetadataPage))
        self.btn_metadata.pack(pady=10, padx=10)

        # Reparar PDF
        self.btn_repair = ctk.CTkButton(self.sidebar_frame, text="🩹", width=50, height=50,
                                         fg_color="transparent", hover_color=Theme.PRIMARY_HOVER,
                                         font=("Arial", 24), command=lambda: self.show_page(RepairPage))
        self.btn_repair.pack(pady=10, padx=10)
        
        # Comprimir PDF
        self.btn_compress = ctk.CTkButton(self.sidebar_frame, text="📉", width=50, height=50,
                                          fg_color="transparent", hover_color=Theme.PRIMARY_HOVER,
                                          font=("Arial", 24), command=lambda: self.show_page(CompressPage))
        self.btn_compress.pack(pady=10, padx=10)

        # Aplanar (Flatten) PDF
        self.btn_flatten = ctk.CTkButton(self.sidebar_frame, text="🔨", width=50, height=50,
                                         fg_color="transparent", hover_color=Theme.PRIMARY_HOVER,
                                         font=("Arial", 24), command=lambda: self.show_page(FlattenPage))
        self.btn_flatten.pack(pady=10, padx=10)
        
        # Convertir (Word)
        self.btn_convert = ctk.CTkButton(self.sidebar_frame, text="📝", width=50, height=50,
                                         fg_color="transparent", hover_color=Theme.PRIMARY_HOVER,
                                         font=("Arial", 24), command=lambda: self.show_page(Pdf2WordPage))
        self.btn_convert.pack(pady=10, padx=10)

        # Word a PDF
        self.btn_word2pdf = ctk.CTkButton(self.sidebar_frame, text="W", width=50, height=50,
                                         fg_color="transparent", hover_color=Theme.PRIMARY_HOVER,
                                         font=("Arial", 24), command=lambda: self.show_page(Word2PdfPage))
        self.btn_word2pdf.pack(pady=10, padx=10)

        # PPT a PDF
        self.btn_ppt2pdf = ctk.CTkButton(self.sidebar_frame, text="P", width=50, height=50,
                                         fg_color="transparent", hover_color=Theme.PRIMARY_HOVER,
                                         font=("Arial", 24), command=lambda: self.show_page(Ppt2PdfPage))
        self.btn_ppt2pdf.pack(pady=10, padx=10)
        
        # Área de Contenido
        self.content_area = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content_area.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        # Barra Superior
        self.top_bar = ctk.CTkFrame(self.content_area, height=60, fg_color="transparent")
        self.top_bar.pack(fill="x", pady=(0, 20))
        
        # Logo / Título en la Barra Superior
        ctk.CTkLabel(self.top_bar, text="Planeta De Formatos -> PDF", 
                     font=(Theme.FONT_FAMILY, 28, "bold"), text_color=Theme.PRIMARY).pack(side="left")

        self.current_page = None

    def show_dashboard(self):
        self.show_page(DashboardPage)

    def show_page(self, page_class):
        if self.current_page:
            self.current_page.destroy()
            
        self.current_page = page_class(self.content_area, self)
        self.current_page.pack(fill="both", expand=True)

    def run(self):
        self.mainloop()

    def route_files(self, files):
        if not isinstance(self.current_page, DashboardPage):
            return

        # Lógica para determinar qué herramienta abrir basándose en el tipo de archivo
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
            else:
                if hasattr(self.current_page, 'handle_dropped_files'):
                    self.current_page.handle_dropped_files(target_files)

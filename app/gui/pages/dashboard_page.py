import customtkinter as ctk
from app.gui.pages.base_page import BasePage
from app.gui.theme import Theme
from app.gui.pages.merge_page import MergePage
from app.gui.pages.compress_page import CompressPage
from app.gui.pages.pdf2word_page import Pdf2WordPage
from app.gui.pages.split_page import SplitPage
from app.gui.pages.multi_split_page import MultiSplitPage
from app.gui.pages.img2pdf_page import Img2PdfPage
from app.gui.pages.pdf2img_page import Pdf2ImgPage
from app.gui.pages.watermark_page import WatermarkPage
from app.gui.pages.rotate_page import RotatePage
from app.gui.pages.page_numbers_page import PageNumbersPage
from app.gui.pages.word2pdf_page import Word2PdfPage
from app.gui.pages.ppt2pdf_page import Ppt2PdfPage
from app.gui.pages.crop_page import CropPage
from app.gui.pages.edit_pdf_page import EditPdfPage
from app.gui.pages.flatten_page import FlattenPage
from app.gui.pages.form_filler_page import FormFillerPage
from app.gui.pages.metadata_page import MetadataPage
from app.gui.pages.ocr_page import OCRPage
from app.gui.pages.pdfa_page import PdfaPage
from app.gui.pages.protect_page import ProtectPage
from app.gui.pages.redact_page import RedactPage
from app.gui.pages.repair_page import RepairPage
from app.gui.pages.sign_page import SignPdfPage
from app.gui.pages.unlock_page import UnlockPage
from app.gui.pages.visualization_page import VisualizationPage
from app.gui.pages.conversion_tools_page import ConversionToolsPage
from app.gui.pages.excel2pdf_page import Excel2PdfPage
from app.gui.pages.pdf2excel_page import Pdf2ExcelPage
from app.gui.pages.pdf2ppt_page import Pdf2PptPage

class DashboardPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, show_back_button=False)

    def create_widgets(self):
        
        # Contenedor de Tarjetas
        self.cards_frame = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        self.cards_frame.pack(fill="both", expand=True)
        
        # Configurar columnas
        self.cards_frame.grid_columnconfigure(0, weight=1)
        self.cards_frame.grid_columnconfigure(1, weight=1)
        self.cards_frame.grid_columnconfigure(2, weight=1)
        
        # Datos de las Tarjetas
        tools = [
            #Principal
            {"title": "Visualizador", "desc": "Ver, buscar y seleccionar texto en PDF.", "icon": "👁️", "color": Theme.CARD_BG_N1, "text_color": Theme.TEXT_MAIN, "page": VisualizationPage},
            {"title": "Organizar PDF", "desc": "Reordenar, girar y eliminar páginas de una manera visual.", "icon": "🔄", "color": Theme.CARD_BG_N1, "text_color": Theme.TEXT_MAIN, "page": RotatePage},
            {"title": "Unir PDF", "desc": "Une múltiples PDFs en uno solo.", "icon": "📄", "color": Theme.CARD_BG_N1, "text_color": Theme.TEXT_MAIN, "page": MergePage},
            #Manipular
            {"title": "Dividir Páginas", "desc": "Divide PDF en rangos separados o crea imagenes apartir de rangos.", "icon": "➗", "color": Theme.CARD_BG_N2, "text_color": Theme.TEXT_MAIN, "page": MultiSplitPage},
            {"title": "Recortar PDF", "desc": "Recorta páginas o elimina márgenes.", "icon": "✂️", "color": Theme.CARD_BG_N2, "text_color": Theme.TEXT_MAIN, "page": CropPage},
            {"title": "Imágenes a PDF", "desc": "Convierte imágenes JPG/PNG a PDF.", "icon": "🖼️", "color": Theme.CARD_BG_N2, "text_color": Theme.TEXT_MAIN, "page": Img2PdfPage},
            #Otros
            {"title": "Números de Página", "desc": "Añade numeración al PDF.", "icon": "#", "color": Theme.CARD_BG_N3, "text_color": Theme.TEXT_MAIN, "page": PageNumbersPage},            
            {"title": "OCR", "desc": "Reconocimiento de texto en PDFs escaneados.", "icon": "📷", "color": Theme.CARD_BG_N3, "text_color": Theme.TEXT_MAIN, "page": OCRPage},            
            {"title": "Marca de Agua", "desc": "Añade marcas de agua de texto o imagen.", "icon": "💧", "color": Theme.CARD_BG_N3, "text_color": Theme.TEXT_MAIN, "page": WatermarkPage},
            #Editar PDF
            {"title": "Censurar PDF (Beta)", "desc": "Elimina información sensible permanentemente.", "icon": "⬛", "color": Theme.CARD_BG_N4, "text_color": Theme.TEXT_MAIN, "page": RedactPage},
            {"title": "Editar PDF (Beta)", "desc": "Modificar el contenido del PDF.", "icon": "✏️", "color": Theme.CARD_BG_N4, "text_color": Theme.TEXT_MAIN, "page": EditPdfPage},
            {"title": "Firmar PDF (Beta)", "desc": "Añade firmas digitales.", "icon": "✍️", "color": Theme.CARD_BG_N4, "text_color": Theme.TEXT_MAIN, "page": SignPdfPage},
            #Editar +
            {"title": "Rellenar Formularios (Beta)", "desc": "Rellena formularios PDF.", "icon": "📝", "color": Theme.CARD_BG_N5, "text_color": Theme.TEXT_MAIN, "page": FormFillerPage},
            {"title": "Herramientas de conversión", "desc": "Convierte PDF en HTML/txt o HTML a PDF.", "icon": "<->", "color": Theme.CARD_BG_N5, "text_color": Theme.TEXT_MAIN, "page": ConversionToolsPage},
            {"title": "PDF/A", "desc": "Convierte a formato PDF/A.", "icon": "🇦", "color": Theme.CARD_BG_N5, "text_color": Theme.TEXT_MAIN, "page": PdfaPage},
            #Proteccion
            {"title": "Proteger PDF", "desc": "Encriptar con contraseña.", "icon": "🔒", "color": Theme.CARD_BG_N6, "text_color": Theme.TEXT_MAIN, "page": ProtectPage},
            {"title": "Desbloquear PDF", "desc": "Elimina protección por contraseña.", "icon": "🔓", "color": Theme.CARD_BG_N6, "text_color": Theme.TEXT_MAIN, "page": UnlockPage},
            {"title": "Metadatos", "desc": "Edita los metadatos del PDF.", "icon": "ℹ️", "color": Theme.CARD_BG_N6, "text_color": Theme.TEXT_MAIN, "page": MetadataPage},
            #Cambio de formato
            {"title": "Reparar", "desc": "Intenta reparar PDFs corruptos.", "icon": "🔧", "color": Theme.CARD_BG_N7, "text_color": Theme.TEXT_MAIN, "page": RepairPage},
            {"title": "Comprimir", "desc": "Reduce el tamaño manteniendo calidad.", "icon": "📉", "color": Theme.CARD_BG_N7, "text_color": Theme.TEXT_MAIN, "page": CompressPage},
            {"title": "Aplanar", "desc": "Aplana campos y anotaciones.", "icon": "➖", "color": Theme.CARD_BG_N7, "text_color": Theme.TEXT_MAIN, "page": FlattenPage},
            #Conversiones
            {"title": "PDF a Word", "desc": "Convierte PDF a DOCX.", "icon": "📝", "color": Theme.CARD_BG_N8, "text_color": Theme.TEXT_MAIN, "page": Pdf2WordPage},
            {"title": "Word a PDF", "desc": "Convierte documentos Word a PDF.", "icon": "📄", "color": Theme.CARD_BG_N8, "text_color": Theme.TEXT_MAIN, "page": Word2PdfPage},
            #{"title": "PDF a Excel", "desc": "Extrae tablas del PDF a XLSX.", "icon": "📊", "color": Theme.CARD_BG_N8, "text_color": Theme.TEXT_MAIN, "page": Pdf2ExcelPage},
            #{"title": "Excel a PDF", "desc": "Convierte hojas de cálculo a PDF.", "icon": "📗", "color": Theme.CARD_BG_N8, "text_color": Theme.TEXT_MAIN, "page": Excel2PdfPage},
            {"title": "PPT a PDF", "desc": "Convierte PowerPoint a PDF.", "icon": "📽️", "color": Theme.CARD_BG_N8, "text_color": Theme.TEXT_MAIN, "page": Ppt2PdfPage},
            #{"title": "PDF a PPT", "desc": "Convierte páginas PDF en diapositivas.", "icon": "📕", "color": Theme.CARD_BG_N8, "text_color": Theme.TEXT_MAIN, "page": Pdf2PptPage},
            ]
        
        # Crear Tarjetas
        for i, tool in enumerate(tools):
            row = i // 3
            col = i % 3
            self.create_card(row, col, tool)
            
        self.enable_dnd()

    def handle_dropped_files(self, files):
        return False

    def create_card(self, row, col, tool):
        bg_color = tool.get("color", Theme.BACKGROUND)
        text_color = tool.get("text_color", "white" if bg_color == Theme.PRIMARY else Theme.TEXT_MAIN)
        
        card_frame = ctk.CTkFrame(self.cards_frame, fg_color=bg_color, corner_radius=16, height=180,
                                  border_width=1, border_color=Theme.BORDER, cursor="hand2")
        card_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        card_frame.bind("<Button-1>", lambda e, p=tool["page"]: self.handle_click(p))

        # Efecto hover (resaltado) sobre la tarjeta y sus hijos
        def _enter(_e, cf=card_frame):
            cf.configure(border_color=Theme.PRIMARY, border_width=2)
        def _leave(_e, cf=card_frame):
            cf.configure(border_color=Theme.BORDER, border_width=1)
        card_frame.bind("<Enter>", _enter)
        card_frame.bind("<Leave>", _leave)
        
        icon_label = ctk.CTkLabel(card_frame, text=tool["icon"], font=("Arial", 30), text_color=Theme.PRIMARY if bg_color != Theme.PRIMARY else "white")
        icon_label.pack(anchor="w", padx=20, pady=(20, 10))
        icon_label.bind("<Button-1>", lambda e, p=tool["page"]: self.handle_click(p))
        
        title_label = ctk.CTkLabel(card_frame, text=tool["title"], font=(Theme.FONT_FAMILY, 18, "bold"), text_color=text_color)
        title_label.pack(anchor="w", padx=20, pady=(0, 5))
        title_label.bind("<Button-1>", lambda e, p=tool["page"]: self.handle_click(p))
        
        desc_label = ctk.CTkLabel(card_frame, text=tool["desc"], font=(Theme.FONT_FAMILY, 12), text_color=text_color, wraplength=240, justify="left")
        desc_label.pack(anchor="w", padx=20, pady=(0, 20))
        desc_label.bind("<Button-1>", lambda e, p=tool["page"]: self.handle_click(p))

    def handle_click(self, page_class):
        if page_class:
            self.controller.show_page(page_class)
        else:
            from app.gui.components import dialogs as messagebox
            messagebox.showinfo("Próximamente", "Esta función aún no ha sido implementada.")

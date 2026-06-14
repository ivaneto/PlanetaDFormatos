from app.gui.pages.simple_tool_page import SimpleToolPage
from app.core.converters import Converter


class Pdf2PptPage(SimpleToolPage):
    title = "PDF a PowerPoint"
    description = "Convierte cada página del PDF en una diapositiva (imagen) de una presentación (.pptx)."
    select_text = "Seleccionar PDF"
    button_text = "Convertir a PowerPoint"
    processing_text = "Convirtiendo..."
    accept_ext = (".pdf",)
    in_filetypes = [("Archivos PDF", "*.pdf")]
    out_ext = ".pptx"
    out_filetypes = [("Presentaciones PowerPoint", "*.pptx")]
    offer_view = False
    success_msg = "¡Presentación creada con éxito!"

    def run(self, in_path, out_path):
        Converter.pdf_to_powerpoint(in_path, out_path)

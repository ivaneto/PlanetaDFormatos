from app.gui.pages.simple_tool_page import SimpleToolPage
from app.core.converters import Converter


class Pdf2WordPage(SimpleToolPage):
    title = "PDF a Word"
    description = "Convierte un PDF a un documento de Word (.docx) editable."
    select_text = "Seleccionar PDF"
    button_text = "Convertir a Word"
    processing_text = "Convirtiendo..."
    accept_ext = (".pdf",)
    in_filetypes = [("Archivos PDF", "*.pdf")]
    out_ext = ".docx"
    out_filetypes = [("Documentos Word", "*.docx")]
    offer_view = False
    success_msg = "¡Documento Word creado con éxito!"

    def run(self, in_path, out_path):
        Converter.pdf_to_word(in_path, out_path)

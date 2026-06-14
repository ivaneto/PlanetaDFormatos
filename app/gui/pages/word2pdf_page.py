from app.gui.pages.simple_tool_page import SimpleToolPage
from app.core.converters import Converter


class Word2PdfPage(SimpleToolPage):
    title = "Word a PDF"
    description = "Convierte documentos de Word (.docx/.doc) a PDF. Usa MS Word o LibreOffice si está disponible."
    select_text = "Seleccionar archivo Word"
    button_text = "Convertir a PDF"
    processing_text = "Convirtiendo..."
    accept_ext = (".docx", ".doc")
    in_filetypes = [("Archivos Word", "*.docx *.doc")]
    out_ext = ".pdf"
    out_filetypes = [("Archivos PDF", "*.pdf")]
    success_msg = "¡PDF creado con éxito!"

    def run(self, in_path, out_path):
        Converter.word_to_pdf(in_path, out_path)

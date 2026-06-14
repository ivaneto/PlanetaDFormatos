from app.gui.pages.simple_tool_page import SimpleToolPage
from app.core.converters import Converter


class Ppt2PdfPage(SimpleToolPage):
    title = "PowerPoint a PDF"
    description = "Convierte presentaciones (.pptx/.ppt) a PDF. Usa MS PowerPoint o LibreOffice si está disponible."
    select_text = "Seleccionar archivo PowerPoint"
    button_text = "Convertir a PDF"
    processing_text = "Convirtiendo..."
    accept_ext = (".pptx", ".ppt")
    in_filetypes = [("Archivos PowerPoint", "*.pptx *.ppt")]
    out_ext = ".pdf"
    out_filetypes = [("Archivos PDF", "*.pdf")]
    success_msg = "¡PDF creado con éxito!"

    def run(self, in_path, out_path):
        Converter.powerpoint_to_pdf(in_path, out_path)

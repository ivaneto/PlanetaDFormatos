from app.gui.pages.simple_tool_page import SimpleToolPage
from app.core.converters import Converter


class Excel2PdfPage(SimpleToolPage):
    title = "Excel a PDF"
    description = "Convierte hojas de cálculo (.xlsx/.xls) a PDF. Usa MS Excel o LibreOffice si está disponible."
    select_text = "Seleccionar archivo Excel"
    button_text = "Convertir a PDF"
    processing_text = "Convirtiendo..."
    accept_ext = (".xlsx", ".xls")
    in_filetypes = [("Archivos Excel", "*.xlsx *.xls")]
    out_ext = ".pdf"
    out_filetypes = [("Archivos PDF", "*.pdf")]
    success_msg = "¡PDF creado con éxito!"

    def run(self, in_path, out_path):
        Converter.excel_to_pdf(in_path, out_path)

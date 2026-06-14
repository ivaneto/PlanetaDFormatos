from app.gui.pages.simple_tool_page import SimpleToolPage
from app.core.converters import Converter


class Pdf2ExcelPage(SimpleToolPage):
    title = "PDF a Excel"
    description = ("Detecta y extrae las tablas del PDF a una hoja de cálculo (.xlsx). "
                   "Cada tabla se coloca en su propia hoja.")
    select_text = "Seleccionar PDF"
    button_text = "Convertir a Excel"
    processing_text = "Extrayendo tablas..."
    accept_ext = (".pdf",)
    in_filetypes = [("Archivos PDF", "*.pdf")]
    out_ext = ".xlsx"
    out_filetypes = [("Hojas de cálculo Excel", "*.xlsx")]
    offer_view = False
    success_msg = "¡Hoja de cálculo creada con éxito!"

    def run(self, in_path, out_path):
        Converter.pdf_to_excel(in_path, out_path)

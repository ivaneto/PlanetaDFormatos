from app.gui.pages.simple_tool_page import SimpleToolPage
from app.core.pdf_editor import PDFEditorBackend


class PdfaPage(SimpleToolPage):
    title = "Convertir a PDF/A"
    description = ("Optimiza el archivo para la preservación a largo plazo (estándar de archivo). "
                   "Incrusta fuentes, elimina cifrado y agrega metadatos de compatibilidad.")
    select_text = "Seleccionar PDF"
    button_text = "Convertir a PDF/A"
    processing_text = "Convirtiendo..."
    accept_ext = (".pdf",)
    in_filetypes = [("Archivos PDF", "*.pdf")]
    out_ext = ".pdf"
    out_filetypes = [("Archivos PDF", "*.pdf")]
    success_msg = "El PDF ha sido convertido a formato de archivo (PDF/A)."
    fail_msg = "Ocurrió un error en la conversión."

    def run(self, in_path, out_path):
        return PDFEditorBackend().convert_to_pdfa(in_path, out_path)

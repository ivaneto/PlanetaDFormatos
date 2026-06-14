from app.gui.pages.simple_tool_page import SimpleToolPage
from app.core.pdf_editor import PDFEditorBackend


class RepairPage(SimpleToolPage):
    title = "Reparar PDF"
    description = ("Intenta reconstruir la estructura y la tabla de referencias (XREF) de archivos dañados. "
                   "Útil si el PDF no se abre o muestra errores al cargar.")
    select_text = "Seleccionar PDF dañado"
    button_text = "Reparar PDF"
    processing_text = "Reparando..."
    accept_ext = (".pdf",)
    in_filetypes = [("Archivos PDF", "*.pdf")]
    out_ext = ".pdf"
    out_filetypes = [("Archivos PDF", "*.pdf")]
    success_msg = "El PDF ha sido reparado (reconstruido) exitosamente."
    fail_msg = "No se pudo reparar el archivo PDF. Es posible que el daño sea demasiado severo."

    def run(self, in_path, out_path):
        return PDFEditorBackend().repair_pdf(in_path, out_path)

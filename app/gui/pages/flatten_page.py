from app.gui.pages.simple_tool_page import SimpleToolPage
from app.core.pdf_editor import PDFEditorBackend


class FlattenPage(SimpleToolPage):
    title = "Aplanar PDF (Flatten)"
    description = ("Combina todas las capas del PDF (anotaciones, firmas, campos de formulario) en una sola "
                   "capa base. Esto evita que los elementos se puedan editar o mover posteriormente.")
    select_text = "Seleccionar PDF"
    button_text = "Aplanar y Guardar PDF"
    processing_text = "Aplanando..."
    accept_ext = (".pdf",)
    in_filetypes = [("Archivos PDF", "*.pdf")]
    out_ext = ".pdf"
    out_filetypes = [("Archivos PDF", "*.pdf")]
    success_msg = "El PDF ha sido aplanado y guardado correctamente."
    fail_msg = "Ocurrió un error al aplanar el PDF."

    def run(self, in_path, out_path):
        return PDFEditorBackend().flatten_pdf(in_path, out_path)

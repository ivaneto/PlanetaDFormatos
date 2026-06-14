import fitz  # PyMuPDF
from PIL import Image
import io

class ThumbnailManager:
    @staticmethod
    def get_page_thumbnail(pdf_path, page_num, size=(100, 140)):
        """
        Generate a thumbnail for a specific page of a PDF.
        :param pdf_path: Path to the PDF file.
        :param page_num: Page number (starting with 0).
        :param size: Tuple (width, height) for the thumbnail.
        :return: PIL Image object.
        """
        try:
            doc = fitz.open(pdf_path)
            page = doc.load_page(page_num)
            
            zoom = size[0] / page.rect.width
            mat = fitz.Matrix(zoom, zoom)
            
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            img = Image.open(io.BytesIO(img_data))
            doc.close()
            return img
        except Exception as e:
            print(f"Error al generar la miniatura de {pdf_path} página {page_num}: {e}")
            return None

    @staticmethod
    def get_pdf_page_count(pdf_path):
        try:
            doc = fitz.open(pdf_path)
            count = len(doc)
            doc.close()
            return count
        except Exception:
            return 0

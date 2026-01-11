import img2pdf
import fitz  # PyMuPDF
from PIL import Image
import os
from pdf2docx import Converter as DocxConverter
import pdfplumber
import pandas as pd
from pptx import Presentation
from pptx.util import Inches
import comtypes.client
from docx2pdf import convert as docx_convert
import pytesseract
import io
import requests
from pypdf import PdfWriter, PdfReader
import tempfile
from urllib.parse import urlparse
from pathlib import Path
import logging

LOG = logging.getLogger(__name__)

import sys

# Configurar la ruta de Tesseract
def get_tesseract_cmd():
    if getattr(sys, 'frozen', False):
        # Buscar tesseract en la carpeta temporal interna (_MEIPASS)
        bundled_path = os.path.join(sys._MEIPASS, "Tesseract-OCR", "tesseract.exe")
        if os.path.exists(bundled_path):
            return bundled_path
        
        # O buscar junto al ejecutable
        local_path = os.path.join(os.path.dirname(sys.executable), "Tesseract-OCR", "tesseract.exe")
        if os.path.exists(local_path):
            return local_path
            
    # En Desarrollo: Comprobar si hay una carpeta Tesseract-OCR local en el proyecto
    dev_local_path = os.path.join(os.getcwd(), "Tesseract-OCR", "tesseract.exe")
    if os.path.exists(dev_local_path):
        return dev_local_path
        
    # En carpeta bin/Tesseract-OCR (Portable)
    bin_sub_path = os.path.join(os.getcwd(), "bin", "Tesseract-OCR", "tesseract.exe")
    if os.path.exists(bin_sub_path):
        return bin_sub_path
        
    # Directamente en bin (Portable)
    bin_root_path = os.path.join(os.getcwd(), "bin", "tesseract.exe")
    if os.path.exists(bin_root_path):
        return bin_root_path

    # Por defecto: Asumir que está en el PATH del sistema
    return "tesseract"

pytesseract.pytesseract.tesseract_cmd = get_tesseract_cmd()

class Converter:
    @staticmethod
    def images_to_pdf(image_list, output_path):
        """
        Convertir una lista de imágenes en un único PDF.
        :param image_list: Lista de rutas a los archivos de imagen
        :param output_path: Ruta para guardar el PDF generado
        """
        with open(output_path, "wb") as f:
            f.write(img2pdf.convert(image_list))

    @staticmethod
    def pdf_to_images(pdf_path, output_dir, fmt='png', pages=None):
        """
        Convertir un PDF en una serie de imágenes.
        :param pdf_path: Ruta al archivo PDF
        :param output_dir: Directorio para guardar las imágenes
        :param fmt: Formato de imagen (por defecto: png)
        :param pages: Lista de índices de página (empezando por 0) para convertir. Si es None, convierte todas.
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        doc = fitz.open(pdf_path)
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        
        for i, page in enumerate(doc):
            if pages is not None and i not in pages:
                continue
                
            pix = page.get_pixmap()
            output_filename = f"{base_name}_page_{i+1}.{fmt}"
            output_path = os.path.join(output_dir, output_filename)
            pix.save(output_path)
        
        doc.close()

    @staticmethod
    def pdf_to_word(pdf_path, output_path):
        """
        Convertir PDF a Word (DOCX).
        :param pdf_path: Ruta al archivo PDF
        :param output_path: Ruta para guardar el archivo DOCX
        """
        cv = DocxConverter(pdf_path)
        cv.convert(output_path, start=0, end=None)
        cv.close()

    @staticmethod
    def pdf_to_excel(pdf_path, output_path):
        """
        (Funcion no implementada en la GUI)
        Funcion en desarrollo, faltan mas pruebas y mejoras en el codigo
        Convertir PDF a Excel (XLSX).
        Extrae tablas de las páginas del PDF y las guarda en un archivo Excel.
        :param pdf_path: Ruta al archivo PDF
        :param output_path: Ruta para guardar el archivo XLSX
        """
        with pdfplumber.open(pdf_path) as pdf:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                has_tables = False
                for i, page in enumerate(pdf.pages):
                    tables = page.extract_tables()
                    if tables:
                        has_tables = True
                        for j, table in enumerate(tables):
                            df = pd.DataFrame(table)
                            # Usar la primera fila como encabezado si parece un encabezado
                            # Por simplicidad, solo volcamos los datos
                            sheet_name = f"Pagina_{i+1}_Tabla_{j+1}"
                            df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
                
                if not has_tables:
                    # Crear una hoja vacía si no se encuentran tablas para evitar errores
                    pd.DataFrame(["No se encontraron tablas"]).to_excel(writer, sheet_name="Info", index=False, header=False)

    @staticmethod
    def pdf_to_powerpoint(pdf_path, output_path):
        """
        (Funcion no implementada en la GUI)
        Convertir PDF a PowerPoint (PPTX).
        Convierte las páginas en imágenes y las coloca en diapositivas.
        :param pdf_path: Ruta al archivo PDF
        :param output_path: Ruta para guardar el archivo PPTX
        """
        prs = Presentation()
        # Usar un directorio temporal para las imágenes
        
        with tempfile.TemporaryDirectory() as temp_dir:
            doc = fitz.open(pdf_path)
            
            for i, page in enumerate(doc):
                # Renderizar página a imagen
                pix = page.get_pixmap()
                image_path = os.path.join(temp_dir, f"pagina_{i}.png")
                pix.save(image_path)
                
                # Añadir una diapositiva en blanco
                blank_slide_layout = prs.slide_layouts[6] 
                slide = prs.slides.add_slide(blank_slide_layout)
                
                # Actualizar el tamaño de la diapositiva de la presentación basado en las dimensiones de la primera página
                if i == 0:
                    # page.rect da el tamaño en puntos (1/72 pulgada)
                    width_pt = page.rect.width
                    height_pt = page.rect.height
                    
                    # Convertir puntos a EMU (1 punto = 12700 EMU)
                    prs.slide_width = int(width_pt * 12700)
                    prs.slide_height = int(height_pt * 12700)
                
                # Añadir imagen a la diapositiva
                slide.shapes.add_picture(image_path, 0, 0, width=prs.slide_width, height=prs.slide_height)
            
            doc.close()
        prs.save(output_path)

    @staticmethod
    def word_to_pdf(doc_path, output_path):
        """
        Convertir Word a PDF.
        Requiere Microsoft Word instalado.
        :param doc_path: Ruta al archivo DOCX/DOC
        :param output_path: Ruta para guardar el archivo PDF
        """
        # docx2pdf usa comtypes/win32com internamente
        docx_convert(doc_path, output_path)

    @staticmethod
    def excel_to_pdf(excel_path, output_path):
        """
        (Funcion no implementada en la GUI)
        Falta desarrollo en el codigo
        Convertir Excel a PDF.
        Requiere Microsoft Excel instalado.
        :param excel_path: Ruta al archivo XLSX/XLS
        :param output_path: Ruta para guardar el archivo PDF
        """
        excel_path = os.path.abspath(excel_path)
        output_path = os.path.abspath(output_path)
        
        excel = comtypes.client.CreateObject("Excel.Application")
        excel.Visible = False
        
        try:
            wb = excel.Workbooks.Open(excel_path)
            # 0 es xlTypePDF
            wb.ExportAsFixedFormat(0, output_path)
            wb.Close()
        finally:
            excel.Quit()

    @staticmethod
    def powerpoint_to_pdf(ppt_path, output_path):
        """
        (Funcion no implementada en la GUI)
        Falta desarrollo en el codigo
        Convertir PowerPoint a PDF.
        Requiere Microsoft PowerPoint instalado.
        :param ppt_path: Ruta al archivo PPTX/PPT
        :param output_path: Ruta para guardar el archivo PDF
        """
        ppt_path = os.path.abspath(ppt_path)
        output_path = os.path.abspath(output_path)
        
        powerpoint = comtypes.client.CreateObject("Powerpoint.Application")
        # PowerPoint podría necesitar ser visible o podría fallar en algunas versiones, pero usualmente es seguro ocultarlo o minimizarlo
        # powerpoint.Visible = 1 
        
        try:
            deck = powerpoint.Presentations.Open(ppt_path)
            # 32 es ppSaveAsPDF
            deck.SaveAs(output_path, 32)
            deck.Close()
        finally:
            powerpoint.Quit()

    @staticmethod
    def apply_ocr(pdf_path, output_path, lang='eng+spa'):
        """
        Aplicar OCR a un PDF escaneado para hacerlo buscable.
        :param pdf_path: Ruta al PDF escaneado
        :param output_path: Ruta para guardar el PDF buscable
        :param lang: Código de idioma para Tesseract (por defecto: 'eng+spa')
        """
        # comprobar si tesseract está instalado/disponible
        
        doc = fitz.open(pdf_path)
        writer = PdfWriter()
        
        for i, page in enumerate(doc):
            # Obtener imagen de la página
            # matrix=fitz.Matrix(2, 2) para mejor resolución/precisión
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_bytes = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_bytes))
            
            # Obtener datos PDF de tesseract
            # esto devuelve un archivo PDF como bytes
            try:
                pdf_bytes = pytesseract.image_to_pdf_or_hocr(img, extension='pdf', lang=lang)
            except pytesseract.TesseractNotFoundError:
                raise Exception("Tesseract no está instalado o no está en su PATH. Por favor instale Tesseract-OCR.")
                
            # Crear un lector PDF a partir de estos bytes
            ocr_page_reader = PdfReader(io.BytesIO(pdf_bytes))
            writer.add_page(ocr_page_reader.pages[0])
            
        doc.close()
        
        with open(output_path, "wb") as f:
            writer.write(f)

    @staticmethod
    def _is_url(s: str) -> bool:
        try:
            p = urlparse(s)
            return p.scheme in ("http", "https")
        except Exception:
            return False

    @staticmethod
    def _is_html_string(s: str) -> bool:
        return s.strip().lower().startswith("<!doctype") or s.strip().lower().startswith("<html")

    @staticmethod
    def html_to_pdf_playwright(source: str, output_path: str, *, is_url: bool = None,
                               paper_format: str = "A4", landscape: bool = False,
                               margin_mm: int = 12, scale: float = 1.0,
                               wait_for_network_idle: bool = True, timeout: int = 60_000):
        """
        Convierte HTML -> PDF con Playwright (Chromium headless) de alta fidelidad.
        """
        output_path = str(output_path)
        # Determinar tipo de source si no se especifica
        if is_url is None:
            is_url = Converter._is_url(source)

        page_url = ""
        temp_file = None

        if not is_url and os.path.exists(source) and Path(source).suffix.lower() in (".html", ".htm"):
            page_url = Path(source).absolute().as_uri()
        elif not is_url and Converter._is_html_string(source):
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8")
            temp_file.write(source)
            temp_file.flush()
            temp_file.close()
            page_url = Path(temp_file.name).absolute().as_uri()
        elif is_url:
            page_url = source
        else:
            if os.path.exists(source):
                page_url = Path(source).absolute().as_uri()
            else:
                raise ValueError("Error en la conversion HTML->PDF. Revisar rutas o archivos.")

        # Comprobación de Playwright
        try:
            from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
        except ImportError as e:
            raise ImportError("Playwright no instalado. Ejecuta 'pip install playwright' y 'playwright install'.") from e

        mm_to_in = lambda mm: mm / 25.4

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
                context = browser.new_context(viewport={"width": 1280, "height": 800})
                page = context.new_page()
                
                nav_opts = {"timeout": timeout}
                nav_opts["wait_until"] = "networkidle" if wait_for_network_idle else "load"
                
                page.goto(page_url, **nav_opts)
                
                # Esperar a los canvas/gráficos
                try:
                    page.wait_for_function(
                        """
                        () => {
                            const canvases = Array.from(document.querySelectorAll('canvas'));
                            if (canvases.length === 0) return true;
                            return canvases.every(c => {
                                try { return c.toDataURL().length > 200; } catch(e) { return false; }
                            });
                        }
                        """,
                        timeout=5000
                    )
                except:
                    pass
                
                page.wait_for_timeout(500)

                pdf_options = {
                    "path": output_path,
                    "format": paper_format,
                    "print_background": True,
                    "landscape": landscape,
                    "scale": scale,
                    "margin": {
                        "top": f"{mm_to_in(margin_mm)}in",
                        "bottom": f"{mm_to_in(margin_mm)}in",
                        "left": f"{mm_to_in(margin_mm)}in",
                        "right": f"{mm_to_in(margin_mm)}in",
                    }
                }
                
                page.pdf(**pdf_options)
                context.close()
                browser.close()
                
        finally:
            if temp_file and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                except:
                    pass

    @staticmethod
    def pdf_to_text(pdf_path, output_path, preserve_layout=True):
        """
        Extraer texto de PDF a un archivo TXT.
        :param pdf_path: Ruta al archivo PDF
        :param output_path: Ruta para guardar el archivo TXT
        :param preserve_layout: Si es True, intenta mantener el diseño físico (fitz 'text' o 'blocks'). 
                                Si es False, solo cadena sin procesar (puede perder saltos de línea).
        """
        doc = fitz.open(pdf_path)
        full_text = []

        for page in doc:
            # "text" preserva líneas y párrafos aproximadamente
            text = page.get_text("text") if preserve_layout else page.get_text("text").replace("\n", " ")
            full_text.append(text)
        
        doc.close()

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n\n".join(full_text))

    @staticmethod
    def html_to_pdf(source, output_path, is_url=False):
        """
        Convertir HTML (Archivo o URL) a PDF.
        :param source: Cadena de URL o ruta de archivo
        :param output_path: Ruta del PDF de salida
        :param is_url: Booleano
        """
        pdf_bytes = None
        
        if is_url:
            try:
                response = requests.get(source)
                response.raise_for_status()
                html_data = response.content
                # fitz.open("pdf", data) espera datos pdf.
                # PyMuPDF v1.24+ soporta "story" pero fitz.open(stream=html) estándar es para abrir, 
                # luego convert_to_pdf().
                
                # Comprobar si podemos abrir html directamente desde la memoria
                doc = fitz.open("html", html_data)
                pdf_bytes = doc.convert_to_pdf()
                doc.close()
            except Exception as e:
                raise Exception(f"Error al obtener o convertir la URL: {e}")
        else:
            # Local file
            if not os.path.exists(source):
                raise FileNotFoundError(f"Archivo HTML no encontrado: {source}")
            
            doc = fitz.open(source)
            pdf_bytes = doc.convert_to_pdf()
            doc.close()
            
        if pdf_bytes:
            with open(output_path, "wb") as f:
                f.write(pdf_bytes)

    @staticmethod
    def pdf_to_html(pdf_path, output_path, mode="text", progress_callback=None, cancel_check=None):
        """
        Convertir PDF a HTML.
        :param pdf_path: PDF de entrada
        :param output_path: HTML de salida
        :param mode: "text" (Pres. diseño), "visual" (Imágenes), "ocr" (Tesseract HOCR)
        :param progress_callback: Función(current_page, total_pages)
        :param cancel_check: Función() -> bool. Si devuelve True, cancela.
        """
        # Envoltorio de compatibilidad para llamadas antiguas si las hay
        if isinstance(mode, bool):
             mode = "ocr" if mode else "text"

        if mode == "text":
            # Modo Simple: Extraer texto/imágenes como HTML
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            
            # Generaremos un único HTML con todas las páginas añadidas.
            html_content = ["<html><body>"]
            for i, page in enumerate(doc):
                if cancel_check and cancel_check():
                    doc.close()
                    return # Cancelado
                
                html_content.append(page.get_text("html"))
                html_content.append("<hr>") # Separador de salto de página
                
                if progress_callback:
                    progress_callback(i + 1, total_pages)
            
            html_content.append("</body></html>")
            doc.close()
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(html_content))
                
        elif mode == "visual":
            # Modo Visual: Renderizar páginas como imágenes (Base64) para preservar el aspecto perfecto
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            html_content = ["<html><head><style>body { background: #525659; margin: 0; padding: 20px; text-align: center; } img { box-shadow: 0 0 10px rgba(0,0,0,0.5); margin-bottom: 20px; max-width: 100%; }</style></head><body>"]
            
            import base64
            
            for i, page in enumerate(doc):
                if cancel_check and cancel_check():
                    doc.close()
                    return
                
                # Renderizar alta calidad (zoom 2x)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img_data = pix.tobytes("png")
                b64_img = base64.b64encode(img_data).decode('utf-8')
                
                html_content.append(f'<div class="page"><img src="data:image/png;base64,{b64_img}" alt="Page {i+1}" /></div>')
                
                if progress_callback:
                    progress_callback(i + 1, total_pages)
            
            html_content.append("</body></html>")
            doc.close()
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(html_content))

        elif mode == "ocr":
            # Modo Complejo
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            full_hocr = ["<html><body>"]
            
            for i, page in enumerate(doc):
                if cancel_check and cancel_check():
                    doc.close()
                    return
                    
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img_bytes = pix.tobytes("png")
                pil_img = Image.open(io.BytesIO(img_bytes))
                
                try:
                    hocr = pytesseract.image_to_pdf_or_hocr(pil_img, extension='hocr', lang='eng+spa')
                    full_hocr.append(hocr.decode('utf-8'))
                except:
                    full_hocr.append(f"<p>Error de OCR en la página {i+1}</p>")
                    
                full_hocr.append("<hr>")
                
                if progress_callback:
                    progress_callback(i + 1, total_pages)
            
            full_hocr.append("</body></html>")
            doc.close()
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(full_hocr))

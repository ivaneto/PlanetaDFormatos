import os
import io
import difflib
from pypdf import PdfReader, PdfWriter, PageObject
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
import fitz # PyMuPDF

class PDFOperations:
    @staticmethod
    def create_cropped_pdf(pdf_path, output_path, page_crops):
        """
        Crear un nuevo PDF que contenga solo las páginas recortadas seleccionadas.
        Si una página tiene varios recortes, generará varias páginas de salida.
        :param pdf_path: Ruta del PDF de origen.
        :param output_path: Ruta del PDF de destino.
        :param page_crops: Dict {índice_página: [(x0, y0, x1, y1), ...]} que mapea índices de página a listas de cuadros de recorte.
        """
        doc = fitz.open(pdf_path)
        out_doc = fitz.open()
        
        # Ordenar las páginas para mantener el orden
        sorted_pages = sorted(page_crops.keys())
        
        for page_num in sorted_pages:
            crops = page_crops[page_num]
            # Manejar tanto la tupla única como la lista de tuplas
            if not isinstance(crops, list):
                crops = [crops]
                
            for crop_rect in crops:
                # Insertar en el nuevo documento
                out_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
                
                # Ahora establecer el recorte en la nueva página
                new_page = out_doc[-1]
                rect = fitz.Rect(crop_rect)
                
                new_page.set_cropbox(rect)
            
        out_doc.save(output_path)
        out_doc.close()
        doc.close()


    @staticmethod
    def apply_crops_to_pdf(pdf_path, output_path, page_crops):
        """
        Crear un nuevo PDF que incluya TODAS las páginas del origen.
        - Las páginas SIN recortes se incluyen tal cual.
        - Las páginas CON recortes se "explotan": la página se repite por cada recorte definido, 
          aplicando el recorte. La página completa original NO se incluye si existen recortes.
        :param pdf_path: Ruta del PDF de origen.
        :param output_path: Ruta del PDF de destino.
        :param page_crops: Dict {índice_página: [(x0, y0, x1, y1), ...]}
        """
        doc = fitz.open(pdf_path)
        out_doc = fitz.open()
        
        total_pages = len(doc)
        
        for i in range(total_pages):
            # Comprobar si esta página tiene recortes
            if i in page_crops and page_crops[i]:
                # Explotar esta página en múltiples páginas recortadas
                crops = page_crops[i]
                if not isinstance(crops, list):
                    crops = [crops]
                    
                for crop_rect in crops:
                    out_doc.insert_pdf(doc, from_page=i, to_page=i)
                    new_page = out_doc[-1]
                    new_page.set_cropbox(fitz.Rect(crop_rect))
            else:
                # Sin recortes, incluir la página original tal cual
                out_doc.insert_pdf(doc, from_page=i, to_page=i)
                
        out_doc.save(output_path)
        out_doc.close()
        doc.close()

    @staticmethod
    def compare_pdfs(file1_path, file2_path, output_path):
        """
        Comparar dos PDFs extrayendo el texto y generando un informe de diferencias.
        :param file1_path: Ruta al primer PDF
        :param file2_path: Ruta al segundo PDF
        :param output_path: Ruta para guardar el informe de comparación (TXT)
        """
        text1 = []
        text2 = []

        try:
            reader1 = PdfReader(file1_path)
            for page in reader1.pages:
                text1.append(page.extract_text())
            
            reader2 = PdfReader(file2_path)
            for page in reader2.pages:
                text2.append(page.extract_text())
        except Exception as e:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"Error al leer los PDFs: {str(e)}")
            return

        full_text1 = "\n".join(text1).splitlines()
        full_text2 = "\n".join(text2).splitlines()

        diff = difflib.unified_diff(
            full_text1, full_text2,
            fromfile=os.path.basename(file1_path),
            tofile=os.path.basename(file2_path),
            lineterm=''
        )

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(list(diff)))

    @staticmethod
    def add_page_numbers(pdf_path, output_path, position='bottom-right'):
        """
        Añadir números de página a un PDF.
        :param pdf_path: Ruta al PDF de origen
        :param output_path: Ruta para guardar el PDF modificado
        :param position: Posición del número de página (actualmente solo se admite 'bottom-right')
        """
        reader = PdfReader(pdf_path)
        writer = PdfWriter()

        for i, page in enumerate(reader.pages):
            # Crear un PDF temporal con el número de página
            packet = io.BytesIO()
            # Usar el tamaño de página de la página original si es posible, de lo contrario por defecto a letter
            width = float(page.mediabox.width)
            height = float(page.mediabox.height)
            
            c = canvas.Canvas(packet, pagesize=(width, height))
            
            page_num_text = f"{i + 1}"
            
            if position == 'bottom-right':
                c.drawString(width - 50, 20, page_num_text)
            elif position == 'bottom-center':
                c.drawCentredString(width / 2, 20, page_num_text)
            elif position == 'bottom-left':
                c.drawString(50, 20, page_num_text)
            else:
                c.drawString(width - 50, 20, page_num_text) # Por defecto
                
            c.save()
            packet.seek(0)
            
            number_pdf = PdfReader(packet)
            page.merge_page(number_pdf.pages[0])
            writer.add_page(page)

        with open(output_path, "wb") as f:
            writer.write(f)

    @staticmethod
    def rotate_pages(pdf_path, output_path, rotation=90, page_indices=None):
        """
        Rotar páginas en un PDF.
        :param pdf_path: Ruta al PDF de origen
        :param output_path: Ruta para guardar el PDF modificado
        :param rotation: Grados a rotar (en sentido horario: 90, 180, 270)
        :param page_indices: Lista de índices de página (empezando por 0) para rotar. Si es None, rota todas.
        """
        reader = PdfReader(pdf_path)
        writer = PdfWriter()

        for i, page in enumerate(reader.pages):
            if page_indices is None or i in page_indices:
                page.rotate(rotation)
            writer.add_page(page)

        with open(output_path, "wb") as f:
            writer.write(f)

    @staticmethod
    def compress_pdf(pdf_path, output_path):
        """
        Esta es una compresión sin pérdidas (en su mayoría) y podría no reducir significativamente el tamaño de las imágenes.
        :param pdf_path: Ruta al PDF de origen
        :param output_path: Ruta para guardar el PDF comprimido
        """
        reader = PdfReader(pdf_path)
        writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        for page in writer.pages:
            page.compress_content_streams()
            
        with open(output_path, "wb") as f:
            writer.write(f)

class PDFManager:
    @staticmethod
    def merge_pdfs(pdf_list, output_path):
        """
        Fusionar una lista de archivos PDF en un único PDF.
        :param pdf_list: Lista de rutas a archivos PDF
        :param output_path: Ruta para guardar el PDF fusionado
        """
        merger = PdfWriter()
        for pdf in pdf_list:
            merger.append(pdf)
        merger.write(output_path)
        merger.close()

    @staticmethod
    def create_from_pages(pages_list, output_path):
        """
        Crear un nuevo PDF a partir de una lista de páginas específicas.
        :param pages_list: Lista de diccionarios {'path': str, 'page': int, 'rotation': int (opcional)}
        :param output_path: Ruta para guardar el nuevo PDF
        """
        out_doc = fitz.open()
        
        # Caché de documentos abiertos
        docs = {}
        
        try:
            for item in pages_list:
                path = item['path']
                page_num = item['page']
                rotation = item.get('rotation', 0)
                
                if path not in docs:
                    docs[path] = fitz.open(path)
                
                src_doc = docs[path]
                
                # Comprobar los límites
                if page_num < len(src_doc):
                    # parámetros de insert_pdf: from_page, to_page (inclusive)
                    # rotate: rota la página insertada por este ángulo relativo al actual.
                    
                    # Vamos a insertar primero, luego rotar la última página de out_doc.
                    out_doc.insert_pdf(src_doc, from_page=page_num, to_page=page_num)
                    
                    if rotation != 0:
                        page = out_doc[-1]
                        src_page = src_doc[page_num]
                        current_rot = src_page.rotation
                        new_rot = (current_rot + rotation) % 360
                        page.set_rotation(new_rot)

            out_doc.save(output_path)
            out_doc.close()
        except Exception as e:
            raise e
        finally:
            for d in docs.values():
                d.close()

    @staticmethod
    def split_pdf(pdf_path, output_dir):
        """
        Dividir un PDF en páginas individuales.
        :param pdf_path: Ruta al archivo PDF
        :param output_dir: Directorio para guardar las páginas divididas
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        reader = PdfReader(pdf_path)
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        
        for i, page in enumerate(reader.pages):
            writer = PdfWriter()
            writer.add_page(page)
            output_filename = f"{base_name}_page_{i+1}.pdf"
            output_path = os.path.join(output_dir, output_filename)
            with open(output_path, "wb") as out:
                writer.write(out)

    @staticmethod
    def add_watermark(pdf_path, output_path, watermark_text=None, watermark_image=None, opacity=0.5, rotation=45):
        """
        Añadir una marca de agua (texto o imagen) a un PDF.
        :param pdf_path: Ruta al PDF de entrada
        :param output_path: Ruta para guardar el PDF con marca de agua
        :param watermark_text: Texto a usar como marca de agua
        :param watermark_image: Ruta a la imagen a usar como marca de agua
        :param opacity: Opacidad de la marca de agua (0.0 a 1.0)
        :param rotation: Ángulo de rotación en grados
        """
        reader = PdfReader(pdf_path)
        writer = PdfWriter()

        # Crear el PDF de la marca de agua en memoria
        packet = io.BytesIO()
        # Usar el tamaño de página por defecto, pero ajustaremos la escala más tarde si es necesario
        c = canvas.Canvas(packet, pagesize=letter)
        
        # Establecer transparencia
        c.setFillAlpha(opacity)
        c.setStrokeAlpha(opacity)

        if watermark_text:
            c.saveState()
            c.translate(300, 400) # Centro aproximado
            c.rotate(rotation)
            c.setFont("Helvetica-Bold", 50)
            c.drawCentredString(0, 0, watermark_text)
            c.restoreState()
        
        if watermark_image:
            c.saveState()
            c.translate(300, 400)
            c.rotate(rotation)
            # Dibujar la imagen centrada
            img = ImageReader(watermark_image)
            iw, ih = img.getSize()
            aspect = ih / float(iw)
            width = 400
            height = width * aspect
            c.drawImage(watermark_image, -width/2, -height/2, width=width, height=height, mask='auto')
            c.restoreState()

        c.save()
        packet.seek(0)
        watermark_pdf = PdfReader(packet)
        watermark_page = watermark_pdf.pages[0]

        for page in reader.pages:
            # Combinar la marca de agua con la página
            page.merge_page(watermark_page)
            writer.add_page(page)

        with open(output_path, "wb") as f:
            writer.write(f)

    @staticmethod
    def get_page_count(pdf_path):
        """
        Obtener el número total de páginas en un PDF.
        :param pdf_path: Ruta al archivo PDF
        :return: Recuento de páginas como entero
        """
        try:
            reader = PdfReader(pdf_path)
            return len(reader.pages)
        except Exception:
            return 0

    @staticmethod
    def extract_range(pdf_path, start_page, end_page, output_path):
        """
        Extraer un rango de páginas a un nuevo PDF.
        :param pdf_path: Ruta al PDF de origen
        :param start_page: Número de página inicial (empezando por 1)
        :param end_page: Número de página final (empezando por 1, inclusive)
        :param output_path: Ruta para guardar el PDF extraído
        """
        reader = PdfReader(pdf_path)
        writer = PdfWriter()
        
        # Ajustar para la indexación basada en 0
        start_idx = max(0, start_page - 1)
        end_idx = min(len(reader.pages), end_page)
        
        for i in range(start_idx, end_idx):
            writer.add_page(reader.pages[i])
            
        with open(output_path, "wb") as f:
            writer.write(f)

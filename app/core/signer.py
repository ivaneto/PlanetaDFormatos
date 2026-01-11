import os
import io
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
import tempfile

try:
    from pyhanko.sign import signers, fields
    from pyhanko.pdf_utils import text, images
    from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
    from pyhanko.sign.fields import SigSeedSubFilter
    HAS_PYHANKO = True
except ImportError:
    HAS_PYHANKO = False

class PDFSigner:
    @staticmethod
    def add_visual_signature(pdf_path, output_path, image_path, page_indices=None, position='bottom-right', coords=None):
        """
        Añadir una firma visual (imagen) a un PDF.
        :param pdf_path: Ruta al PDF de origen
        :param output_path: Ruta para guardar la salida
        :param image_path: Ruta a la imagen de la firma (PNG/JPG)
        :param page_indices: Lista de números de página para firmar (empezando por 0). Predeterminado: [0] (Primera página)
        :param position: 'bottom-right', 'bottom-left', 'center', o None (usar coordenadas)
        :param coords: Tupla (x, y, ancho, alto) si la posición es None.
        """
        reader = PdfReader(pdf_path)
        writer = PdfWriter()

        if page_indices is None:
            page_indices = [0]

        # Cargar la imagen una vez para comprobar la relación de aspecto
        img = ImageReader(image_path)
        iw, ih = img.getSize()
        aspect = ih / float(iw)

        for i, page in enumerate(reader.pages):
            if i in page_indices:
                # Crear un PDF temporal para la firma de esta página
                packet = io.BytesIO()
                
                # Obtener el tamaño de la página
                pw = float(page.mediabox.width)
                ph = float(page.mediabox.height)
                
                c = canvas.Canvas(packet, pagesize=(pw, ph))
                
                # Determinar ubicación
                sig_w = 150
                sig_h = sig_w * aspect
                
                x, y = 0, 0
                
                if coords:
                    x, y, sig_w, sig_h = coords
                else:
                    padding = 50
                    if position == 'bottom-right':
                        x = pw - sig_w - padding
                        y = padding
                    elif position == 'bottom-left':
                        x = padding
                        y = padding
                    elif position == 'center':
                        x = (pw - sig_w) / 2
                        y = (ph - sig_h) / 2

                c.drawImage(image_path, x, y, width=sig_w, height=sig_h, mask='auto')
                c.save()
                
                packet.seek(0)
                sig_pdf = PdfReader(packet)
                page.merge_page(sig_pdf.pages[0])
            
            writer.add_page(page)

        with open(output_path, "wb") as f:
            writer.write(f)

    @staticmethod
    def sign_digital(pdf_path, output_path, pfx_path, password):
        """
        Firmar PDF digitalmente usando un certificado PFX/P12.
        """
        if not HAS_PYHANKO:
            raise ImportError("pyHanko no está instalado. Por favor instálelo para usar firmas digitales.")

        signer = signers.P12Signer(
            entry_fname=pfx_path,
            passphrase=password.encode() if password else None
        )

        with open(pdf_path, 'rb') as inf:
            w = IncrementalPdfFileWriter(inf)
            fields.append_signature_field(
                w,
                fields.SigFieldSpec(
                    'Signature1',
                    box=(100, 100, 300, 150)
                )
            )
            
            with open(output_path, 'wb') as outf:
                signers.sign_pdf(
                    w, signers.PdfSignatureMetadata(field_name='Signature1'),
                    signer=signer,
                    output=outf,
                )

    @staticmethod
    def add_multiple_signatures(pdf_path, output_path, signatures_data):
        """
        Añadir múltiples firmas visuales a un PDF.
        :param pdf_path: Ruta al PDF de origen
        :param output_path: Ruta para guardar la salida
        :param signatures_data: Lista de dicts: {'page': int, 'x': float, 'y': float, 'width': float, 'height': float, 'image_path': str}
        """
        reader = PdfReader(pdf_path)
        writer = PdfWriter()
        
        # Agrupar firmas por página
        sigs_by_page = {}
        for sig in signatures_data:
            p = sig['page']
            if p not in sigs_by_page: sigs_by_page[p] = []
            sigs_by_page[p].append(sig)
            
        for i, page in enumerate(reader.pages):
            if i in sigs_by_page:
                packet = io.BytesIO()
                pw = float(page.mediabox.width)
                ph = float(page.mediabox.height)
                c = canvas.Canvas(packet, pagesize=(pw, ph))
                
                for sig in sigs_by_page[i]:
                    # Asumimos que se pasan como puntos PDF absolutos (x, y, w, h)
                    x, y, w, h = sig['x'], sig['y'], sig['width'], sig['height']
                    img_path = sig['image_path']
                    c.drawImage(img_path, x, y, width=w, height=h, mask='auto')
                
                c.save()
                packet.seek(0)
                sig_pdf = PdfReader(packet)
                page.merge_page(sig_pdf.pages[0])
            
            writer.add_page(page)
            
        with open(output_path, "wb") as f:
            writer.write(f)


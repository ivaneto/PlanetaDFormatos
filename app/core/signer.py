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
        Add a visual signature (image) to a PDF.
        :param pdf_path: Path to source PDF
        :param output_path: Path to save output
        :param image_path: Path to signature image (PNG/JPG)
        :param page_indices: List of page numbers to sign (starting with 0). Default: [0] (First page)
        :param position: 'bottom-right', 'bottom-left', 'center', or None (use coordinates)
        :param coords: Tuple (x, y, width, height) if position is None.
        """
        reader = PdfReader(pdf_path)
        writer = PdfWriter()

        if page_indices is None:
            page_indices = [0]

        # Load image once to check aspect ratio
        img = ImageReader(image_path)
        iw, ih = img.getSize()
        aspect = ih / float(iw)

        for i, page in enumerate(reader.pages):
            if i in page_indices:
                # Create a temporary PDF for the signature of this page
                packet = io.BytesIO()
                
                # Get page size
                pw = float(page.mediabox.width)
                ph = float(page.mediabox.height)
                
                c = canvas.Canvas(packet, pagesize=(pw, ph))
                
                # Determine location
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
        Sign PDF digitally using a PFX/P12 certificate.
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
        Add multiple visual signatures to a PDF.
        :param pdf_path: Path to source PDF
        :param output_path: Path to save output
        :param signatures_data: List of dicts: {'page': int, 'x': float, 'y': float, 'width': float, 'height': float, 'image_path': str}
        """
        reader = PdfReader(pdf_path)
        writer = PdfWriter()
        
        # Group signatures by page
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
                    # We assume they are passed as absolute PDF points (x, y, w, h)
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


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
        Create a new PDF containing only selected cropped pages.
        If a page has multiple crops, it will generate multiple output pages.
        :param pdf_path: Source PDF path.
        :param output_path: Destination PDF path.
        :param page_crops: Dict {page_index: [(x0, y0, x1, y1), ...]} mapping page indices to lists of crop boxes.
        """
        doc = fitz.open(pdf_path)
        out_doc = fitz.open()
        
        # Sort pages to maintain order
        sorted_pages = sorted(page_crops.keys())
        
        for page_num in sorted_pages:
            crops = page_crops[page_num]
            # Handle both single tuple and list of tuples
            if not isinstance(crops, list):
                crops = [crops]
                
            for crop_rect in crops:
                # Insert into new document
                out_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
                
                # Now set the crop on the new page
                new_page = out_doc[-1]
                rect = fitz.Rect(crop_rect)
                
                new_page.set_cropbox(rect)
            
        out_doc.save(output_path)
        out_doc.close()
        doc.close()


    @staticmethod
    def apply_crops_to_pdf(pdf_path, output_path, page_crops):
        """
        Create a new PDF that includes ALL source pages.
        - Pages WITHOUT crops are included as is.
        - Pages WITH crops are "exploded": the page is repeated for each defined crop, 
          applying the crop. The original full page is NOT included if crops exist.
        :param pdf_path: Source PDF path.
        :param output_path: Destination PDF path.
        :param page_crops: Dict {page_index: [(x0, y0, x1, y1), ...]}
        """
        doc = fitz.open(pdf_path)
        out_doc = fitz.open()
        
        total_pages = len(doc)
        
        for i in range(total_pages):
            # Check if this page has crops
            if i in page_crops and page_crops[i]:
                # Explode this page into multiple cropped pages
                crops = page_crops[i]
                if not isinstance(crops, list):
                    crops = [crops]
                    
                for crop_rect in crops:
                    out_doc.insert_pdf(doc, from_page=i, to_page=i)
                    new_page = out_doc[-1]
                    new_page.set_cropbox(fitz.Rect(crop_rect))
            else:
                # No crops, include original page as is
                out_doc.insert_pdf(doc, from_page=i, to_page=i)
                
        out_doc.save(output_path)
        out_doc.close()
        doc.close()

    @staticmethod
    def compare_pdfs(file1_path, file2_path, output_path):
        """
        Compare two PDFs by extracting text and generating a diff report.
        :param file1_path: Path to first PDF
        :param file2_path: Path to second PDF
        :param output_path: Path to save comparison report (TXT)
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
        Add page numbers to a PDF.
        :param pdf_path: Path to source PDF
        :param output_path: Path to save modified PDF
        :param position: Page number position (currently only 'bottom-right' is supported)
        """
        reader = PdfReader(pdf_path)
        writer = PdfWriter()

        for i, page in enumerate(reader.pages):
            # Create a temporary PDF with page number
            packet = io.BytesIO()
            # Use the original page size if possible, otherwise default to letter
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
                c.drawString(width - 50, 20, page_num_text) # Default
                
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
        Rotate pages in a PDF.
        :param pdf_path: Path to source PDF
        :param output_path: Path to save modified PDF
        :param rotation: Degrees to rotate (clockwise: 90, 180, 270)
        :param page_indices: List of page indices (starting with 0) to rotate. If None, rotates all.
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
        This is lossless compression (mostly) and might not significantly reduce image size.
        :param pdf_path: Path to source PDF
        :param output_path: Path to save compressed PDF
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
        Merge a list of PDF files into a single PDF.
        :param pdf_list: List of paths to PDF files
        :param output_path: Path to save merged PDF
        """
        merger = PdfWriter()
        for pdf in pdf_list:
            merger.append(pdf)
        merger.write(output_path)
        merger.close()

    @staticmethod
    def create_from_pages(pages_list, output_path):
        """
        Create a new PDF from a list of specific pages.
        :param pages_list: List of dictionaries {'path': str, 'page': int, 'rotation': int (optional)}
        :param output_path: Path to save new PDF
        """
        out_doc = fitz.open()
        
        # Cache of open documents
        docs = {}
        
        try:
            for item in pages_list:
                path = item['path']
                page_num = item['page']
                rotation = item.get('rotation', 0)
                
                if path not in docs:
                    docs[path] = fitz.open(path)
                
                src_doc = docs[path]
                
                # Check bounds
                if page_num < len(src_doc):
                    # insert_pdf params: from_page, to_page (inclusive)
                    # rotate: rotates inserted page by this angle relative to current.
                    
                    # Let's insert first, then rotate the last page of out_doc.
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
        Split a PDF into individual pages.
        :param pdf_path: Path to PDF file
        :param output_dir: Directory to save split pages
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
        Add a watermark (text or image) to a PDF.
        :param pdf_path: Path to input PDF
        :param output_path: Path to save watermarked PDF
        :param watermark_text: Text to use as watermark
        :param watermark_image: Path to image to use as watermark
        :param opacity: Watermark opacity (0.0 to 1.0)
        :param rotation: Rotation angle in degrees
        """
        reader = PdfReader(pdf_path)
        writer = PdfWriter()

        # Create watermark PDF in memory
        packet = io.BytesIO()
        # Use default page size, but we will adjust scale later if necessary
        c = canvas.Canvas(packet, pagesize=letter)
        
        # Set transparency
        c.setFillAlpha(opacity)
        c.setStrokeAlpha(opacity)

        if watermark_text:
            c.saveState()
            c.translate(300, 400) # Approximate center
            c.rotate(rotation)
            c.setFont("Helvetica-Bold", 50)
            c.drawCentredString(0, 0, watermark_text)
            c.restoreState()
        
        if watermark_image:
            c.saveState()
            c.translate(300, 400)
            c.rotate(rotation)
            # Draw image centered
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
            # Merge watermark with page
            page.merge_page(watermark_page)
            writer.add_page(page)

        with open(output_path, "wb") as f:
            writer.write(f)

    @staticmethod
    def get_page_count(pdf_path):
        """
        Get the total number of pages in a PDF.
        :param pdf_path: Path to PDF file
        :return: Page count as integer
        """
        try:
            reader = PdfReader(pdf_path)
            return len(reader.pages)
        except Exception:
            return 0

    @staticmethod
    def extract_range(pdf_path, start_page, end_page, output_path):
        """
        Extract a range of pages to a new PDF.
        :param pdf_path: Path to source PDF
        :param start_page: Start page number (starting with 1)
        :param end_page: End page number (starting with 1, inclusive)
        :param output_path: Path to save extracted PDF
        """
        reader = PdfReader(pdf_path)
        writer = PdfWriter()
        
        # Adjust for 0-based indexing
        start_idx = max(0, start_page - 1)
        end_idx = min(len(reader.pages), end_page)
        
        for i in range(start_idx, end_idx):
            writer.add_page(reader.pages[i])
            
        with open(output_path, "wb") as f:
            writer.write(f)

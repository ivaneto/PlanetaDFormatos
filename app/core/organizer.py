from typing import List
from pypdf import PdfReader, PdfWriter
import os

class PDFOrganizer:
    @staticmethod
    def reorder_pdf_pages(input_path: str, output_path: str, page_indices: List[int]):
        """
        Create a new PDF with pages from the input PDF in the specified order.
        Can be used to reorder, delete (by omitting indices) or duplicate pages.
        
        :param input_path: Path to source PDF
        :param output_path: Path to save the new PDF
        :param page_indices: List of page indices (starting with 0) to include in the new PDF
        """
        reader = PdfReader(input_path)
        writer = PdfWriter()
        
        total_pages = len(reader.pages)
        
        for index in page_indices:
            if 0 <= index < total_pages:
                writer.add_page(reader.pages[index])
            else:
                print(f"Advertencia: El índice de página {index} está fuera de los límites (0-{total_pages-1}). Omitido.")
                
        with open(output_path, "wb") as f:
            writer.write(f)

    @staticmethod
    def insert_pdf_pages(input_path: str, output_path: str, insert_pdf_path: str, at_index: int = -1):
        """
        Insert pages from another PDF into the input PDF at a specific index.
        
        :param input_path: Path to main PDF
        :param output_path: Path to save the result
        :param insert_pdf_path: Path to the PDF to insert
        :param at_index: Index (starting with 0) to insert before it. -1 to append at the end.
        """
        reader_main = PdfReader(input_path)
        reader_insert = PdfReader(insert_pdf_path)
        writer = PdfWriter()
        
        total_main_pages = len(reader_main.pages)
        
        # Normalize at_index
        if at_index < 0 or at_index > total_main_pages:
            at_index = total_main_pages
            
        # Add pages before insertion point
        for i in range(at_index):
            writer.add_page(reader_main.pages[i])
            
        # Add inserted pages
        for page in reader_insert.pages:
            writer.add_page(page)
            
        # Add remaining pages
        for i in range(at_index, total_main_pages):
            writer.add_page(reader_main.pages[i])
            
        with open(output_path, "wb") as f:
            writer.write(f)

from typing import List
from pypdf import PdfReader, PdfWriter
import os

class PDFOrganizer:
    @staticmethod
    def reorder_pdf_pages(input_path: str, output_path: str, page_indices: List[int]):
        """
        Crear un nuevo PDF con páginas del PDF de entrada en el orden especificado.
        Se puede usar para reordenar, eliminar (omitiendo índices) o duplicar páginas.
        
        :param input_path: Ruta al PDF de origen
        :param output_path: Ruta para guardar el nuevo PDF
        :param page_indices: Lista de índices de página (empezando por 0) para incluir en el nuevo PDF
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
        Insertar páginas de otro PDF en el PDF de entrada en un índice específico.
        
        :param input_path: Ruta al PDF principal
        :param output_path: Ruta para guardar el resultado
        :param insert_pdf_path: Ruta al PDF que se va a insertar
        :param at_index: Índice (empezando por 0) para insertar antes de él. -1 para añadir al final.
        """
        reader_main = PdfReader(input_path)
        reader_insert = PdfReader(insert_pdf_path)
        writer = PdfWriter()
        
        total_main_pages = len(reader_main.pages)
        
        # Normalizar at_index
        if at_index < 0 or at_index > total_main_pages:
            at_index = total_main_pages
            
        # Añadir páginas antes del punto de inserción
        for i in range(at_index):
            writer.add_page(reader_main.pages[i])
            
        # Añadir páginas insertadas
        for page in reader_insert.pages:
            writer.add_page(page)
            
        # Añadir las páginas restantes
        for i in range(at_index, total_main_pages):
            writer.add_page(reader_main.pages[i])
            
        with open(output_path, "wb") as f:
            writer.write(f)

"""Pruebas unitarias de la lógica de negocio (app/core).

Cubren la manipulación pura de PDF, que no depende de la GUI. Se ejecutan con:

    python -m unittest discover -s tests        (o)
    python -m unittest tests.test_core

Crean PDFs de muestra en una carpeta temporal con PyMuPDF, por lo que no
requieren archivos externos ni Microsoft Office.
"""
import os
import tempfile
import unittest

import fitz

from app.core.pdf_ops import PDFOperations, PDFManager
from app.core.organizer import PDFOrganizer
from app.core.thumbnail_manager import ThumbnailManager
from app.core.converters import Converter
from app.core.logger import get_logger


def make_pdf(path, n_pages=3, text_prefix="Pagina"):
    doc = fitz.open()
    for i in range(n_pages):
        page = doc.new_page()
        page.insert_text((72, 72), f"{text_prefix} {i + 1}")
    doc.save(path)
    doc.close()
    return path


def page_count(path):
    d = fitz.open(path)
    n = len(d)
    d.close()
    return n


class CoreTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="pf_test_")
        self.src = make_pdf(os.path.join(self.tmp, "src.pdf"), 5)

    def out(self, name):
        return os.path.join(self.tmp, name)

    # --- PDFManager ---
    def test_get_page_count(self):
        self.assertEqual(PDFManager.get_page_count(self.src), 5)
        self.assertEqual(PDFManager.get_page_count(self.out("noexiste.pdf")), 0)

    def test_extract_range(self):
        out = self.out("range.pdf")
        PDFManager.extract_range(self.src, 2, 4, out)
        self.assertEqual(page_count(out), 3)

    def test_split_pdf(self):
        outdir = os.path.join(self.tmp, "split")
        PDFManager.split_pdf(self.src, outdir)
        produced = [f for f in os.listdir(outdir) if f.endswith(".pdf")]
        self.assertEqual(len(produced), 5)

    def test_merge_pdfs(self):
        b = make_pdf(self.out("b.pdf"), 2)
        out = self.out("merged.pdf")
        PDFManager.merge_pdfs([self.src, b], out)
        self.assertEqual(page_count(out), 7)

    def test_create_from_pages_with_rotation(self):
        out = self.out("compose.pdf")
        pages = [
            {"path": self.src, "page": 0, "rotation": 90},
            {"path": self.src, "page": 2},
        ]
        PDFManager.create_from_pages(pages, out)
        self.assertEqual(page_count(out), 2)
        d = fitz.open(out)
        self.assertEqual(d[0].rotation % 360, 90)
        d.close()

    def test_add_watermark(self):
        out = self.out("wm.pdf")
        PDFManager.add_watermark(self.src, out, watermark_text="CONF", tile=True)
        self.assertEqual(page_count(out), 5)

    # --- PDFOperations ---
    def test_page_numbers_skip_first(self):
        out = self.out("nums.pdf")
        PDFOperations.add_page_numbers(self.src, out, position="top-center",
                                       fmt="{n} de {total}", skip_first=True)
        self.assertEqual(page_count(out), 5)

    def test_rotate_pages(self):
        out = self.out("rot.pdf")
        PDFOperations.rotate_pages(self.src, out, rotation=90, page_indices=[0, 1])
        d = fitz.open(out)
        self.assertEqual(d[0].rotation % 360, 90)
        self.assertEqual(d[2].rotation % 360, 0)
        d.close()

    def test_compress_returns_sizes(self):
        out = self.out("cmp.pdf")
        orig, new = PDFOperations.compress_pdf(self.src, out, level="medium")
        self.assertGreater(orig, 0)
        self.assertGreater(new, 0)
        self.assertTrue(os.path.exists(out))

    def test_create_cropped_pdf(self):
        out = self.out("crop.pdf")
        crops = {0: [(0, 0, 100, 100)], 2: [(0, 0, 50, 50), (50, 50, 100, 100)]}
        PDFOperations.create_cropped_pdf(self.src, out, crops)
        # Página 0 (1 recorte) + página 2 (2 recortes) = 3 páginas
        self.assertEqual(page_count(out), 3)

    # --- PDFOrganizer ---
    def test_reorder_pages(self):
        out = self.out("reorder.pdf")
        PDFOrganizer.reorder_pdf_pages(self.src, out, [4, 0, 2])
        self.assertEqual(page_count(out), 3)

    def test_reorder_ignores_out_of_bounds(self):
        out = self.out("reorder2.pdf")
        PDFOrganizer.reorder_pdf_pages(self.src, out, [0, 99, 1])
        self.assertEqual(page_count(out), 2)

    # --- ThumbnailManager ---
    def test_iter_thumbnails(self):
        thumbs = list(ThumbnailManager.iter_thumbnails(self.src, size=(60, 80)))
        self.assertEqual(len(thumbs), 5)
        idx, img = thumbs[0]
        self.assertEqual(idx, 0)
        self.assertIsNotNone(img)

    # --- Converters / Logger (sin dependencias pesadas) ---
    def test_pdf_to_text(self):
        out = self.out("texto.txt")
        Converter.pdf_to_text(self.src, out)
        with open(out, encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Pagina 1", content)

    def test_find_soffice_no_crash(self):
        # Solo debe devolver una ruta o None, sin lanzar excepción.
        result = Converter._find_soffice()
        self.assertTrue(result is None or isinstance(result, str))

    def test_logger(self):
        log = get_logger("tests")
        log.info("mensaje de prueba")  # no debe lanzar


if __name__ == "__main__":
    unittest.main()

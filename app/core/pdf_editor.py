
import fitz  # PyMuPDF
from pypdf import PdfWriter, PdfReader
import io
from app.core.logger import get_logger

LOG = get_logger(__name__)

class PDFEditorBackend:
    def __init__(self):
        self.doc = None
        self.pages_images = [] # PIL image cache for rendering
        self.scale = 1.0
        
    def load_pdf(self, path, scale=1.0):
        self.doc = fitz.open(path)
        self.scale = scale
        self.pages_images = []

        for page in self.doc:
            pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
            img_data = pix.tobytes("png")
            self.pages_images.append(img_data)
            
        return self.pages_images

    def get_page_count(self):
        if self.doc:
            return len(self.doc)
        return 0
    
    def close(self):
        if self.doc:
            self.doc.close()

    def save_changes(self, original_path, changes, output_path):
        """
        Apply changes to the PDF.
        changes: list of dictionaries like {'type': 'text', 'page': 0, 'x': 100, 'y': 100, ...}
        """
        doc = fitz.open(original_path)
        
        # First pass: Add annotations
        for change in changes:
            page_idx = change.get('page', 0)
            if page_idx >= len(doc):
                continue
                
            page = doc[page_idx]
            
            if change['type'] == 'text':
                page.insert_text(
                    point=(change['x'], change['y']),
                    text=change['content'],
                    fontsize=change.get('fontsize', 11),
                    color=change.get('color', (0, 0, 0))
                )
            
            elif change['type'] == 'rect': 
                rect = fitz.Rect(change['x0'], change['y0'], change['x1'], change['y1'])
                page.draw_rect(
                    rect,
                    color=change.get('stroke', (0,0,0)),
                    fill=change.get('fill', None),
                    width=change.get('width', 1)
                )

            elif change['type'] == 'highlight':
                 rect = fitz.Rect(change['x0'], change['y0'], change['x1'], change['y1'])
                 page.add_highlight_annot(rect)

            elif change['type'] == 'redact':
                 rect = fitz.Rect(change['x0'], change['y0'], change['x1'], change['y1'])
                 page.add_redact_annot(rect, fill=change.get('fill', (1, 1, 1)))

            elif change['type'] == 'replace':
                 rect = fitz.Rect(change['x0'], change['y0'], change['x1'], change['y1'])
                 page.add_redact_annot(rect, fill=(1, 1, 1)) 
                 page.insert_text(
                    point=(rect.x0, rect.y1 - 2),
                    text=change['content'],
                    fontsize=change.get('fontsize', 11),
                    color=change.get('color', (0, 0, 0))
                 )

            elif change['type'] == 'pencil':
                points = change.get('points_list', [])
                if len(points) > 1:
                    shape = page.new_shape()
                    shape.draw_polyline(points)
                    shape.finish(
                        color=change.get('color', (1, 0, 0)), 
                        width=change.get('width', 2)
                    )
                    shape.commit()

            elif change['type'] == 'image':
                rect = fitz.Rect(change['x0'], change['y0'], change['x1'], change['y1'])
                page.insert_image(rect, filename=change['path'])
        
        # Second pass: Apply redactions
        for page in doc:
            page.apply_redactions()

        doc.save(output_path)
        doc.close()

    def flatten_pdf(self, input_path, output_path):
        """
        Flattens all annotations, form fields and widgets on the page interface.
        This prevents future edits.
        """
        try:
            src_doc = fitz.open(input_path)
            out_doc = fitz.open() # New empty PDF
            
            for src_page in src_doc:
                # Create a new page in output with the same dimensions
                out_page = out_doc.new_page(width=src_page.rect.width, height=src_page.rect.height)
                
                # Render source page ONTO output page
                out_page.show_pdf_page(out_page.rect, src_doc, src_page.number)
            
            out_doc.save(output_path)
            src_doc.close()
            out_doc.close()
            return True
        except Exception as e:
            LOG.error(f"Error al aplanar el PDF: {e}")
            return False

    def encrypt_pdf(self, input_path, output_path, user_pw, owner_pw, permissions):
        """
        Encrypts the PDF with passwords and permissions using PikePDF.
        """
        try:
            import pikepdf
            import secrets

            if not owner_pw:
                owner_pw = secrets.token_hex(32)

            # Map fitz permissions to PikePDF logic
            can_print = (permissions & fitz.PDF_PERM_PRINT) != 0
            can_copy = (permissions & fitz.PDF_PERM_COPY) != 0
            can_modify = (permissions & fitz.PDF_PERM_MODIFY) != 0
            can_annotate = (permissions & fitz.PDF_PERM_ANNOTATE) != 0
            
            # Build Permissions object
            pike_perms = pikepdf.Permissions(
                print_lowres=can_print,
                print_highres=can_print,
                extract=can_copy,
                modify_assembly=can_modify,
                modify_form=can_modify,
                modify_annotation=can_annotate,
                modify_other=can_modify,
                accessibility=True 
            )

            # Open with PikePDF
            with pikepdf.open(input_path) as pdf:
                # Encryption with AES-256 (R=6)
                enc = pikepdf.Encryption(
                    user=user_pw,
                    owner=owner_pw,
                    allow=pike_perms,
                    R=6
                )
                pdf.save(output_path, encryption=enc)
            
            return True
        except Exception as e:
            LOG.error(f"Error al cifrar el PDF: {e}")
            return False

    def unlock_pdf(self, input_path, output_path, password):
        """
        Unlock a PDF by removing its encryption (requires a valid password).
        """
        try:
            doc = fitz.open(input_path)
            
            if doc.is_encrypted:
                if not doc.authenticate(password):
                    LOG.warning("Contraseña incorrecta")
                    doc.close()
                    return False
            
            # Saving without encryption arguments removes security
            doc.save(output_path)
            doc.close()
            return True
        except Exception as e:
            LOG.error(f"Error al desbloquear el PDF: {e}")
            return False

    def get_metadata(self, input_path):
        """
        Get PDF metadata as a dictionary.
        """
        try:
            doc = fitz.open(input_path)
            metadata = doc.metadata
            doc.close()
            return metadata
        except Exception as e:
            LOG.error(f"Error al leer los metadatos: {e}")
            return {}

    def save_metadata(self, input_path, output_path, metadata):
        """
        Save PDF with new metadata.
        metadata: dictionary of metadata keys (title, author, etc.)
        """
        try:
            doc = fitz.open(input_path)
            doc.set_metadata(metadata)
            doc.save(output_path)
            doc.close()
            return True
        except Exception as e:
            LOG.error(f"Error al guardar los metadatos: {e}")
            return False

    def repair_pdf(self, input_path, output_path):
        """
        Attempt to repair the PDF by forcing a full rewrite of the XREF table and structure.
        """
        try:
            # PyMuPDF attempts to repair on open
            doc = fitz.open(input_path)
            
            # garbage=4: deduplicate objects, clean storage
            # deflate=True: compress streams
            # clean=True: clean permission bits and content
            doc.save(output_path, garbage=4, deflate=True, clean=True)
            doc.close()
            return True
        except Exception as e:
            LOG.error(f"Error al reparar el PDF: {e}")
            return False

    def convert_to_pdfa(self, input_path, output_path):
        """
        Convert to PDF/A (Best effort).
        Embeds fonts and tries to add PDF/A metadata.
        """
        try:
            doc = fitz.open(input_path)
            pdfa_xml = '''<?xpacket begin="" id="W5M0MpCehiHzreSzNTczkc9d"?>
            <x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="Adobe XMP Core 5.6-c015 81.159809, 2016/11/11-01:42:16        ">
               <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
                  <rdf:Description rdf:about="" xmlns:pdfaExtension="http://www.aiim.org/pdfa/ns/extension/" xmlns:pdfaSchema="http://www.aiim.org/pdfa/ns/schema#" xmlns:pdfaProperty="http://www.aiim.org/pdfa/ns/property#" xmlns:pdf="http://ns.adobe.com/pdf/1.3/">
                     <pdfaExtension:schemas>
                        <rdf:Bag>
                           <rdf:li rdf:parseType="Resource">
                              <pdfaSchema:namespaceURI>http://www.aiim.org/pdfa/ns/id/</pdfaSchema:namespaceURI>
                              <pdfaSchema:prefix>pdfaid</pdfaSchema:prefix>
                              <pdfaSchema:schema>PDF/A Identification Schema</pdfaSchema:schema>
                               <pdfaSchema:property>
                                  <rdf:Seq>
                                     <rdf:li rdf:parseType="Resource">
                                        <pdfaProperty:category>internal</pdfaProperty:category>
                                        <pdfaProperty:description>Parte del estándar PDF/A</pdfaProperty:description>
                                        <pdfaProperty:name>part</pdfaProperty:name>
                                        <pdfaProperty:valueType>Integer</pdfaProperty:valueType>
                                     </rdf:li>
                                     <rdf:li rdf:parseType="Resource">
                                        <pdfaProperty:category>internal</pdfaProperty:category>
                                        <pdfaProperty:description>Enmienda del estándar PDF/A</pdfaProperty:description>
                                        <pdfaProperty:name>amd</pdfaProperty:name>
                                        <pdfaProperty:valueType>Text</pdfaProperty:valueType>
                                     </rdf:li>
                                     <rdf:li rdf:parseType="Resource">
                                        <pdfaProperty:category>internal</pdfaProperty:category>
                                        <pdfaProperty:description>Nivel de conformidad del estándar PDF/A</pdfaProperty:description>
                                        <pdfaProperty:name>conformance</pdfaProperty:name>
                                        <pdfaProperty:valueType>Text</pdfaProperty:valueType>
                                     </rdf:li>
                                  </rdf:Seq>
                               </pdfaSchema:property>
                           </rdf:li>
                        </rdf:Bag>
                     </pdfaExtension:schemas>
                  </rdf:Description>
                  <rdf:Description rdf:about="" xmlns:pdfaid="http://www.aiim.org/pdfa/ns/id/">
                     <pdfaid:part>1</pdfaid:part>
                     <pdfaid:conformance>B</pdfaid:conformance>
                  </rdf:Description>
               </rdf:RDF>
            </x:xmpmeta>
            <?xpacket end="w"?>'''
            
            doc.set_xml_metadata(pdfa_xml)
            
            # Remove permissions/encryption
            doc.save(output_path, garbage=4, deflate=True, clean=True)
            doc.close()
            return True
        except Exception as e:
            LOG.error(f"Error al convertir a PDF/A: {e}")
            return False

    def is_pdfa(self, input_path):
        """
        Check if PDF claims to be PDF/A (looking for pdfaid metadata).
        """
        try:
            doc = fitz.open(input_path)
            metadata_xml = doc.get_xml_metadata()
            doc.close()
            # Simple check for PDF/A ID namespace
            if metadata_xml and "pdfaid" in metadata_xml:
                 return True
            return False
        except Exception as e:
            LOG.error(f"Error al comprobar el estado de PDF/A: {e}")
            return False


import fitz  # PyMuPDF
import traceback
from app.core.logger import get_logger

LOG = get_logger(__name__)

class FormHandler:
    @staticmethod
    def extract_fields(pdf_path):
        """
        Scans the PDF for form widgets and returns a list of dictionaries with field information.
        """
        fields = []
        try:
            doc = fitz.open(pdf_path)
            for page_num, page in enumerate(doc):
                # Iterate over page widgets
                for widget in page.widgets():
                    if not widget.field_name:
                        continue
                        
                    field_data = {
                        "page": page_num,
                        "param": widget.field_name, # Actual name used for filling
                        "label": widget.field_label or widget.field_name, # Label for the user
                        "type": widget.field_type_string, # e.g. 'Text', 'Btn' (Checkbox/Radio), 'Ch' (Choice)
                        "value": widget.field_value,
                        "rect": list(widget.rect), # [x0, y0, x1, y1] for highlight context
                        "choices": widget.choice_values # For comboboxes / listboxes
                    }
                    
                    if int(widget.field_type) in [1, 5, fitz.PDF_WIDGET_TYPE_BUTTON, fitz.PDF_WIDGET_TYPE_CHECKBOX]:
                        flags = getattr(widget, 'field_flags', 0)
                        is_rb = getattr(widget, 'is_radio', False) or bool(flags & 32768)
                        is_cb = (not is_rb) and ((widget.field_type == 5) or getattr(widget, 'is_checkbox', False))

                        if is_rb:
                             field_data["type"] = "RadioButton"
                             try:
                                 field_data["on_value"] = widget.on_state() 
                             except:
                                 field_data["on_value"] = f"On_{page_num}_{int(widget.rect.x0)}_{int(widget.rect.y0)}"
                             
                             if "on_value" not in field_data or not field_data["on_value"]:
                                 field_data["on_value"] = f"On_{page_num}_{int(widget.rect.x0)}_{int(widget.rect.y0)}"
                                 
                        elif is_cb:
                            field_data["type"] = "Checkbox"
                            val = widget.field_value
                            if isinstance(val, bool):
                                field_data["value"] = val
                            elif isinstance(val, str):
                                field_data["value"] = val.lower() not in ['off', 'no', 'false', '0', '']
                            else:
                                field_data["value"] = False

                        else:
                             field_data["type"] = "Button"

                    fields.append(field_data)
            
            radio_groups = {}
            for f in fields:
                if f['type'] == 'RadioButton':
                    name = f['param']
                    if name not in radio_groups: radio_groups[name] = []
                    radio_groups[name].append(f)
            
            for name, group in radio_groups.items():
                seen_values = {}
                for f in group:
                    val = f.get('on_value', 'Yes')
                    
                    if val in seen_values:
                        new_val = f"{val}_{len(seen_values)+1}"
                        f['on_value'] = new_val
                        val = new_val
                        
                    seen_values[val] = True

            doc.close()
        except Exception as e:
            LOG.error(f"Error al extraer los campos: {e}")

        return fields

    @staticmethod
    def fill_pdf(pdf_path, field_data_map, output_path):
        """
        Fills the PDF with the provided data.
        :param field_data_map: Dictionary {field_name: new_value}
        """
        try:
            doc = fitz.open(pdf_path)
            form = doc.load_page(0).get_drawings()
            
            # Robust iteration:
            for page in doc:
                for widget in page.widgets():
                    # print(f"[DEBUG] inspecting widget {widget.field_name}")
                    if widget.field_name in field_data_map:
                        new_val = field_data_map[widget.field_name]
                        
                        try:
                            if int(widget.field_type) in [1, 5, fitz.PDF_WIDGET_TYPE_BUTTON, fitz.PDF_WIDGET_TYPE_CHECKBOX]:
                                flags = getattr(widget, 'field_flags', 0)
                                is_rb = getattr(widget, 'is_radio', False) or bool(flags & 32768)
                                
                                is_cb = (not is_rb) and ((widget.field_type == 5) or getattr(widget, 'is_checkbox', False))

                                if is_rb:
                                    try:
                                        pg_num = page.number
                                        synthetic_id = f"On_{pg_num}_{int(widget.rect.x0)}_{int(widget.rect.y0)}"
                                        
                                        natural_on = widget.on_state()
                                        
                                        should_be_on = (str(new_val) == synthetic_id) or (str(new_val) == str(natural_on))
                                        
                                        if should_be_on:
                                            widget.field_value = True
                                        else:
                                            widget.field_value = False
                                            
                                        widget.update()
                                    except Exception as r_err:
                                        print(f"Error en el botón de opción (Radio): {r_err}")
                                        traceback.print_exc()
                                        # Alternative
                                        widget.field_value = bool(new_val)
                                        widget.update()
                                
                                elif is_cb:
                                    widget.field_value = bool(new_val)
                                    widget.update()
                                        
                            # Handle Text /
                            else:
                                widget.field_value = str(new_val)
                                widget.update()
                        except Exception as w_err:
                            print(f"[ERROR] No se pudo establecer {widget.field_name}: {w_err}")
                            traceback.print_exc()

            xref = doc.pdf_catalog() 
            doc.xref_set_key(xref, "AcroForm/NeedAppearances", "true")
            doc.need_appearances(True)
            doc.save(output_path)
            doc.close()
            return True
        except Exception as e:
            traceback.print_exc()
            raise Exception(f"No se pudo rellenar el PDF: {e}")

# Planeta De Formatos -> PDF 📚

Este proyecto esta pensado para estudiantes, profesionales y personas que necesitan una herramienta para gestionar, editar y manipular archivos PDF de una manera más dinámica. Aunque todas las funciones estan en el mercado, existen toques adicionales que podrían ser muy utiles para la experiencia del usuario. Solo utiliza archivos locales, haciendolo más seguro y confiable.

<p align="center">
  <img src="assets/Pantalla_principal.png" alt="GUI1">
</p>

<p align="center">
  <img src="assets/Pantalla_principal_2.png" alt="GUI2">
</p>

## Características principales

### Organización y gestión
- **Unir PDF**: Combina múltiples archivos PDF de una forma visual, seleccionando las paginas que deseas unir de cada archivo. 
Con una selección avanzada puedes seleccionar rangos de paginas de cada archivo, ejemplo, tienes 3 archivos PDF, el primero tiene 10 paginas, el segundo 20 y el tercero 30, puedes seleccionar las paginas 1-5, 10 del primero, 6-10 del segundo, 11-15 del tercero y regresar al primero (o cualquiera) para las hojas 7-9. Cada archivo se distingue por una letra como en este ejemplo son tres serian A, B y C, para realizar esta selección debe de ser así: **(A:1-5,10)(B:6-10)(C:11-15)(A:7-9)**. Con esto tendras la unión para crear tu nuevo PDF, esto es muy útil para archivos con muchas hojas y no tener que seleccionar una por una.
- **Dividir PDF**: Se definen rangos de un PDF para poder dividirlo en varios PDFs. Dentro de esta función se tienen 5 opciones:
   - Rango de imagenes: Basado en los rangos definidos creara imagenes solamente de las paginas de los rangos seleccionados (Todos lo rangos que esten en la lista).
   - Todo imagenes: Creara imagenes de todas las paginas del PDF. (Se recomienda crear una carpeta donde guardar las imagenes).
   - Dividir rangos: Basado en los rangos definidos creara PDFs individuales de cada rango
   - Dividir todo: Creara PDFs de cada pagina del PDF. (Se recomienda crear una carpeta donde guardar los PDFs).
   - Unir rangos: Basado en los rangos definidos creara un PDF con las paginas de los rangos seleccionados (Todos lo rangos que esten en la lista).
- **Organizar PDF**: Reordena páginas visualmente mediante arrastrar y soltar (Drag & Drop),  rótalas según sea necesario y elimina las paginas que no desees. Soporta archivos PDF, documentos (word) e imágenes. 
(Al arrastrar desde tu ventana de archivos PPT o excel intentara hacerlos PDFs para mostrarlos, pero es posible que no funcione correctamente) 
- **Recortar**: Ajusta con precisión los márgenes y dimensiones de las páginas. Se tienen tres opciones:
   - PDF recortado: Creará un PDF solamente con las secciones recortadas por el usuario.
   - PDF completo con recortes: Creará un PDF con las paginas que no estan recortadas y en las que se hicieron recortes se reemplazara la pagina original por la sección o secciones recortadas.
   - Generar imagenes: Genera imagenes de las secciones recortadas.

### 📝 Edición y anotación
- **Editor de PDF (BETA)**: Modifica contenido, añade texto, formas y dibujos directamente sobre el documento.
- **Redactar (BETA)**: Censura información sensible de forma permanente y segura.
- **Marca de Agua**: Añade marcas de agua personalizadas (texto o imagen) con control total de opacidad, tamaño y rotación.
- **Números de Página**: Inserta numeración automática en diferentes posiciones.
- **Rellenar Formularios (BETA)**: Detecta automáticamente y permite completar campos de formularios interactivos.

### 🔄 Conversión inteligente
- **Imágenes a PDF**: Convierte lotes de imágenes (JPG, PNG, BMP, etc.) en documentos PDF.
- **Suite Office**: Conversión bidireccional de alta fidelidad entre PDF y formatos Word (.docx). Para Excel (.xlsx) y PowerPoint (.pptx) se necesita más desarrollo y pruebas para un funcionamiento óptimo.
- **OCR (Reconocimiento de Texto)**: Transforma PDFs escaneados o fotos de documentos en texto editable y buscable.
- **HTML a PDF**: Captura y convierte páginas web completas a PDF manteniendo el diseño original.

### 🛡️ Seguridad y optimización
- **Proteger y Desbloquear**: Gestiona contraseñas de apertura y permisos de edición/impresión.
- **Comprimir**: Optimiza el tamaño del archivo sin sacrificar la legibilidad.
- **Metadatos**: Edita la información interna del archivo (Autor, Título, Asunto, etc.).
- **Reparar**: Recupera y reconstruye archivos PDF que presentan errores o están dañados.
- **Estándar PDF/A**: Convierte documentos al estándar de archivado a largo plazo.

### 📖 Visualización y firma
- **Visor integrado**: Visualizador fluido con funciones de búsqueda, selección de texto y copia rápida. Pensado para una busqueda y con una función de salto para pasar a la herramienta necesaria. 
- **Firmar PDF**: Soporte para firmas visuales (dibujadas o imágenes) y firmas digitales basadas en certificados (.p12 / .pfx).

## Instalación y configuración

### Requisitos previos
- **Python 3.10+**
- **Tesseract OCR**: El proyecto contiene la carpeta bin con el ejecutable de Tesseract, pero si se desea usar es recomendable (no es obligatorio, ya esta dentro de bin) que en el sistema este instalado para las funciones de reconocimiento de texto.
- **Playwright**: Para la conversión de HTML a PDF.

### Pasos de instalación

1. **Clonar el repositorio**:
   ```bash
   git clone <url-del-repositorio>
   cd PlanetaDFormatos
   ```

2. **Entorno virtual**:
   ```bash
   python -m venv .venv
   # Activar en Windows:
   .venv\Scripts\activate
   ```

3. **Dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Navegadores para conversión web**:
   ```bash
   playwright install chromium
   ```

### Cómo ejecutar
Inicia la aplicación ejecutando el script principal:
```bash
python main.py
```

## 📦 Tecnologías utilizadas
- **Interfaz**: `customtkinter`, `tkinterdnd2`, `ttkthemes`.
- **Motor PDF**: `PyMuPDF (fitz)`, `pypdf`, `reportlab`, `pikepdf`.
- **Conversión**: `pdf2docx`, `docx2pdf`, `python-docx`, `python-pptx`, `pytesseract`, `playwright`.
- **Procesamiento**: `Pillow`, `opencv-python`, `pandas`.
- **Firma Digital**: `pyhanko`.

## ⚖️ Licencia
Este proyecto es software propietario. Consulte el archivo `COMMERCIAL_LICENSE.md` para más detalles sobre los términos de uso.

---
© 2026 Planeta De Formatos. Todos los derechos reservados.

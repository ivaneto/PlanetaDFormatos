import PyInstaller.__main__
import os
import sys
import shutil

# Configuración del Ejecutable
APP_NAME = "PlanetaDeFormatos_v1.0"
ENTRY_POINT = "main.py"

def build():
    print("Iniciando proceso de construcción...")
    
    # 1. Definir Datos Adicionales (Archivos no-python)
    # Formato: (ruta_origen, ruta_destino)
    datas = []
    
    # A) Bundling de Tesseract OCR
    # La aplicación espera encontrar tesseract en sys._MEIPASS/Tesseract-OCR/tesseract.exe
    # Mapeamos la carpeta 'bin' actual a 'Tesseract-OCR' dentro del ejecutable.
    if os.path.exists("bin"):
        print("Agregando binarios de Tesseract (carpeta 'bin')...")
        datas.append(('bin', 'Tesseract-OCR'))
    else:
        print("ADVERTENCIA: Carpeta 'bin' no encontrada. La función OCR podría fallar en el ejecutable si no se incluye Tesseract.")

    # B) Bundling de CustomTkinter (Temas y JSONs)
    try:
        import customtkinter
        ctk_path = os.path.dirname(customtkinter.__file__)
        print(f"Agregando CustomTkinter desde: {ctk_path}")
        datas.append((ctk_path, 'customtkinter'))
    except ImportError:
        print("Error: customtkinter no instalado.")
        return

    # C) Bundling de TkinterDnD2 (Librerías TCL/TK binarias)
    try:
        import tkinterdnd2
        tkdnd_path = os.path.dirname(tkinterdnd2.__file__)
        print(f"Agregando TkinterDnD2 desde: {tkdnd_path}")
        datas.append((tkdnd_path, 'tkinterdnd2'))
    except ImportError:
        print("Error: tkinterdnd2 no instalado.")
        return

    # 2. Definir Imports Ocultos (Hidden Imports)
    # Módulos que PyInstaller podría no detectar automáticamente
    hidden_imports = [
        'app',
        'app.gui',
        'app.core',
        'PIL',
        'pikepdf',
        'pypdf',
        'reportlab',
        'fitz',             # PyMuPDF
        'pdf2docx',
        'docx2pdf',
        'comtypes',
        'comtypes.stream',
        'comtypes.client',
        'pandas',
        'numpy',
        'openpyxl',
        'tqdm',
        'babel.numbers',
        'win32timezone',
        'playwright',
        'playwright.sync_api',
        'cryptography',
        'pyhanko',          # Si se instala posteriormente
        'requests',
        'urllib3',
        'certifi',
        'darkdetect',
    ]

    # 3. Argumentos para PyInstaller
    args = [
        ENTRY_POINT,                        # Archivo principal
        f'--name={APP_NAME}',               # Nombre del ejecutable
        '--noconfirm',                      # No preguntar confirmación de sobreescritura
        '--windowed',                       # Sin consola (GUI)
        '--clean',                          # Limpiar caché antes de construir
        '--onefile',                        # Crear un solo archivo .exe
        # '--debug=all',                    # Descomentar para debug
    ]
    
    # Añadir datos
    for src, dst in datas:
        # En Windows usamos ; como separador si usamos string, pero PyInstaller.__main__.run 
        # prefiere la sintaxis --add-data "src;dst"
        args.append(f'--add-data={src}{os.pathsep}{dst}')
        
    # Añadir hidden imports
    for imp in hidden_imports:
        args.append(f'--hidden-import={imp}')

    # Opciones adicionales de optimización o rutas
    # args.append('--collect-all=customtkinter') # Alternativa si add-data falla

    print(f"Ejecutando PyInstaller con argumentos: {args}")
    
    # Ejecutar PyInstaller
    try:
        PyInstaller.__main__.run(args)
        print("\n------------------------------------------------")
        print(f"Construcción finalizada exitosamente.")
        print(f"El ejecutable se encuentra en la carpeta 'dist/'.")
        print("------------------------------------------------")
    except Exception as e:
        print(f"Error durante la construcción: {e}")

if __name__ == "__main__":
    build()

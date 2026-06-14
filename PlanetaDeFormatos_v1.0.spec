# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('bin', 'Tesseract-OCR'), ('C:\\Users\\ivant\\Documents\\Antigravity\\PlanetaDFormatos\\.venv\\Lib\\site-packages\\customtkinter', 'customtkinter'), ('C:\\Users\\ivant\\Documents\\Antigravity\\PlanetaDFormatos\\.venv\\Lib\\site-packages\\tkinterdnd2', 'tkinterdnd2')],
    hiddenimports=['app', 'app.gui', 'app.core', 'PIL', 'pikepdf', 'pypdf', 'reportlab', 'fitz', 'pdf2docx', 'docx2pdf', 'comtypes', 'comtypes.stream', 'comtypes.client', 'pandas', 'numpy', 'openpyxl', 'tqdm', 'babel.numbers', 'win32timezone', 'playwright', 'playwright.sync_api', 'cryptography', 'pyhanko', 'requests', 'urllib3', 'certifi', 'darkdetect'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='PlanetaDeFormatos_v1.0',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

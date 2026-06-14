"""Registro centralizado de la aplicación.

Escribe a un archivo rotativo en ``user_data/app.log`` (junto al ejecutable o
al directorio de trabajo) y también a la consola en desarrollo. Como la app se
empaqueta con ``--windowed`` (sin consola), el archivo es la fuente principal
de diagnóstico.

Uso:
    from app.core.logger import get_logger
    LOG = get_logger(__name__)
    LOG.info("mensaje")
    LOG.exception("algo falló")  # incluye traceback
"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

_CONFIGURED = False


def _log_directory():
    """Devuelve un directorio escribible para los logs."""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.getcwd()
    path = os.path.join(base, "user_data")
    try:
        os.makedirs(path, exist_ok=True)
        return path
    except Exception:
        # Último recurso: carpeta temporal del sistema.
        import tempfile
        return tempfile.gettempdir()


def _configure_once():
    global _CONFIGURED
    if _CONFIGURED:
        return

    root = logging.getLogger("planeta")
    root.setLevel(logging.INFO)

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    try:
        log_file = os.path.join(_log_directory(), "app.log")
        fh = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
        fh.setFormatter(fmt)
        root.addHandler(fh)
    except Exception:
        pass

    # Consola solo en desarrollo (cuando hay stdout disponible).
    if not getattr(sys, "frozen", False) and sys.stderr:
        ch = logging.StreamHandler()
        ch.setFormatter(fmt)
        root.addHandler(ch)

    _CONFIGURED = True


def get_logger(name="planeta"):
    _configure_once()
    # Todos los loggers cuelgan del namespace 'planeta' para compartir handlers.
    if not name.startswith("planeta"):
        name = f"planeta.{name}"
    return logging.getLogger(name)

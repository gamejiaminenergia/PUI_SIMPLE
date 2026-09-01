"""
Configuración centralizada de logging para PUI_SIMPLE.

Genera archivos en `logs/` con rotación por fecha y stdout simultáneo.
"""
import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

_FMT = "%(asctime)s | %(levelname)-7s | %(name)-30s | %(message)s"
_DATEFMT = "%Y-%m-%d %H:%M:%S"

_INITIALIZED = False


def setup_logging(level: str = "INFO", log_to_console: bool = True) -> logging.Logger:
    """Inicializa el logger raíz una sola vez. Retorna el logger raíz."""
    global _INITIALIZED
    root = logging.getLogger()

    if _INITIALIZED:
        root.setLevel(getattr(logging, level.upper(), logging.INFO))
        return root

    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.handlers.clear()

    # Silenciar librerías muy ruidosas (HTTP, HF, transformers)
    for noisy in ("httpx", "httpcore", "urllib3", "huggingface_hub",
                  "transformers", "timesfm", "filelock"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    formatter = logging.Formatter(_FMT, datefmt=_DATEFMT)

    # Archivo con rotación diaria (mantiene 14 días)
    log_file = os.path.join(LOG_DIR, f"pui_{datetime.now().strftime('%Y%m%d')}.log")
    file_handler = TimedRotatingFileHandler(
        log_file, when="midnight", interval=1, backupCount=14, encoding="utf-8"
    )
    file_handler.suffix = "%Y%m%d"
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    # Archivo de solo errores para fallos
    err_file = os.path.join(LOG_DIR, "pui_errors.log")
    err_handler = TimedRotatingFileHandler(
        err_file, when="midnight", interval=1, backupCount=30, encoding="utf-8"
    )
    err_handler.suffix = "%Y%m%d"
    err_handler.setLevel(logging.ERROR)
    err_handler.setFormatter(formatter)
    root.addHandler(err_handler)

    if log_to_console:
        stream = logging.StreamHandler(sys.stdout)
        stream.setFormatter(formatter)
        root.addHandler(stream)

    _INITIALIZED = True
    root.info("=" * 70)
    root.info("Logging inicializado | archivo=%s | nivel=%s", log_file, level)
    return root


def get_logger(name: str) -> logging.Logger:
    """Obtiene un logger por módulo. Llama a setup_logging() si no se ha hecho."""
    setup_logging()
    return logging.getLogger(name)
import logging
import sys
from core.config import settings

def setup_logging() -> logging.Logger:
    logger = logging.getLogger("ai_service")
    if logger.handlers:
        return logger  # avoid duplicate handlers on reload

    logger.setLevel(settings.LOG_LEVEL)

    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

logger = setup_logging()
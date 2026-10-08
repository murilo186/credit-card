import json
import logging
from typing import Any


def configure_application_logger(name: str, level: str) -> logging.Logger:
    """Configure a stdout logger for safe structured application events."""
    logger = logging.getLogger(name)
    logger.setLevel(level.upper())

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)

    return logger


def log_event(logger: logging.Logger, event: str, **fields: Any) -> None:
    """Emit a structured log containing only safe operational metadata."""
    logger.info(json.dumps({"event": event, **fields}, ensure_ascii=False))

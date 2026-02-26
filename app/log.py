import logging
import socket
from pathlib import Path

from app.config import settings

FILE_FORMAT = "%(asctime)s - [{hostname}] - %(levelname)s - %(message)s"


def _get_handler() -> logging.FileHandler:
    """Creates a simple file handler."""
    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    hostname = socket.gethostname()

    log_file = log_dir / f"{settings.PROJECT_NAME.lower()}_{hostname}.log"
    formatter = logging.Formatter(FILE_FORMAT.replace("{hostname}", hostname))

    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)
    return handler


def get_logger(name: str, level: int = logging.DEBUG) -> logging.Logger:
    """Creates and configures a logger instance."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    logger.addHandler(_get_handler())
    logger.propagate = False
    return logger

import logging
import socket
import sys
from pathlib import Path

from app.config import settings

LOG_FORMAT = "%(asctime)s - [{hostname}] - %(levelname)s - %(message)s"


def _get_formatter(hostname: str) -> logging.Formatter:
    return logging.Formatter(LOG_FORMAT.replace("{hostname}", hostname))


def _get_file_handler(hostname: str) -> logging.FileHandler:
    """Creates a file handler writing to a per-host log file."""
    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"{settings.PROJECT_NAME.lower()}_{hostname}.log"
    handler = logging.FileHandler(log_file)
    handler.setFormatter(_get_formatter(hostname))
    return handler


def _get_stream_handler(hostname: str) -> logging.StreamHandler:
    """Creates a handler writing to stdout, picked up by `docker logs`."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_get_formatter(hostname))
    return handler


def get_logger(name: str, level: int = logging.DEBUG) -> logging.Logger:
    """Creates and configures a logger instance."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    hostname = socket.gethostname()
    logger.addHandler(_get_file_handler(hostname))
    logger.addHandler(_get_stream_handler(hostname))
    logger.propagate = False
    return logger

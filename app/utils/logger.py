"""Diagnostic logging. Tracebacks go to the log file, never to the UI."""
from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.utils.paths import logs_dir

LOGGER_NAME = "ytd"
LOG_FILE_NAME = "app.log"
_FORMAT = "%(asctime)s | %(levelname)-8s | %(threadName)s | %(name)s | %(message)s"


def setup_logging(log_dir: Path | None = None, level: int = logging.INFO,
                  console: bool = False) -> logging.Logger:
    """Configure the root app logger. Safe to call more than once."""
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)
    logger.propagate = False

    for h in list(logger.handlers):  # idempotent: replace existing handlers
        logger.removeHandler(h)
        h.close()

    target = (log_dir or logs_dir())
    target.mkdir(parents=True, exist_ok=True)
    fh = RotatingFileHandler(target / LOG_FILE_NAME, maxBytes=1_000_000,
                             backupCount=3, encoding="utf-8")
    fh.setFormatter(logging.Formatter(_FORMAT))
    logger.addHandler(fh)

    if console:
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(logging.Formatter(_FORMAT))
        logger.addHandler(sh)
    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    return logging.getLogger(f"{LOGGER_NAME}.{name}" if name else LOGGER_NAME)


def install_excepthook() -> None:
    """Log uncaught exceptions to file instead of printing tracebacks to users."""
    log = get_logger("uncaught")

    def hook(exc_type, exc, tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc, tb)
            return
        log.critical("Uncaught exception", exc_info=(exc_type, exc, tb))

    sys.excepthook = hook

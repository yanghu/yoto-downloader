"""Logging configuration for yoto-downloader.

Call setup_logging() once at application startup (in main.py).
Logs go to both stdout (visible via `docker logs`) and a rotating
file at /logs/app.log (persistent across container restarts).
"""

import logging
import logging.handlers
import sys

from config import APP_LOG_PATH, LOG_DIR
import os


def setup_logging() -> None:
    os.makedirs(LOG_DIR, exist_ok=True)

    fmt = logging.Formatter(
        "%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    # stdout — keeps `docker logs` working as before
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(fmt)
    root.addHandler(stdout_handler)

    # rotating file — 10 MB per file, keep 5 backups (~50 MB max)
    file_handler = logging.handlers.RotatingFileHandler(
        APP_LOG_PATH,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)

    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

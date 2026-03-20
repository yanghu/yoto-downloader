"""Application configuration: directory paths and environment settings."""

import os

# Base download directory, mapped to Docker volume
BASE_DOWNLOAD_DIR = "/downloads"

# Top-level category directories
AUDIO_BASE_DIR = os.path.join(BASE_DOWNLOAD_DIR, "audio")
COVER_BASE_DIR = os.path.join(BASE_DOWNLOAD_DIR, "covers")
COVER_CROPPED_BASE_DIR = os.path.join(BASE_DOWNLOAD_DIR, "covers-cropped")

# Archive directories (songs that have been added to Yoto cards)
ARCHIVE_AUDIO_DIR = os.path.join(BASE_DOWNLOAD_DIR, "archive", "audio")
ARCHIVE_COVER_DIR = os.path.join(BASE_DOWNLOAD_DIR, "archive", "covers")
ARCHIVE_COVER_CROPPED_DIR = os.path.join(BASE_DOWNLOAD_DIR, "archive", "covers-cropped")

# Discord Webhook (optional; notifications are skipped when not set)
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# Log directory, mapped to Docker volume
LOG_DIR = "/logs"
APP_LOG_PATH = os.path.join(LOG_DIR, "app.log")
FAILED_LOG_PATH = os.path.join(LOG_DIR, "failed.log")


def ensure_dirs() -> None:
    """Create all required download directories if they do not exist."""
    for path in (
        AUDIO_BASE_DIR,
        COVER_BASE_DIR,
        COVER_CROPPED_BASE_DIR,
        ARCHIVE_AUDIO_DIR,
        ARCHIVE_COVER_DIR,
        ARCHIVE_COVER_CROPPED_DIR,
        LOG_DIR,
    ):
        os.makedirs(path, exist_ok=True)

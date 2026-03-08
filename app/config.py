"""Application configuration: directory paths and environment settings."""

import os

# Base download directory, mapped to Docker volume
BASE_DOWNLOAD_DIR = "/downloads"

# Top-level category directories
AUDIO_BASE_DIR = os.path.join(BASE_DOWNLOAD_DIR, "audio")
COVER_BASE_DIR = os.path.join(BASE_DOWNLOAD_DIR, "covers")
ORIGINAL_COVER_BASE_DIR = os.path.join(BASE_DOWNLOAD_DIR, "covers", "originals")

# Archive directories (songs that have been added to Yoto cards)
ARCHIVE_AUDIO_DIR = os.path.join(BASE_DOWNLOAD_DIR, "archive", "audio")
ARCHIVE_COVER_DIR = os.path.join(BASE_DOWNLOAD_DIR, "archive", "covers")
ARCHIVE_ORIGINAL_COVER_DIR = os.path.join(BASE_DOWNLOAD_DIR, "archive", "covers", "originals")

# Discord Webhook (optional; notifications are skipped when not set)
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")


def ensure_dirs() -> None:
    """Create all required download directories if they do not exist."""
    for path in (AUDIO_BASE_DIR, COVER_BASE_DIR, ORIGINAL_COVER_BASE_DIR, ARCHIVE_AUDIO_DIR, ARCHIVE_COVER_DIR, ARCHIVE_ORIGINAL_COVER_DIR):
        os.makedirs(path, exist_ok=True)

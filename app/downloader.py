"""Background download task using yt-dlp."""

import json
import logging
import os
from datetime import datetime

import yt_dlp

from config import AUDIO_BASE_DIR, COVER_BASE_DIR, COVER_CROPPED_BASE_DIR, FAILED_LOG_PATH
from image import crop_thumbnail_to_square
from notifier import send_discord_notification
from validator import remove_download

logger = logging.getLogger(__name__)


def _record_failure(url: str, error: str) -> None:
    """Append a JSON line to failed.log for later retry."""
    entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "url": url,
        "error": error,
    }
    try:
        with open(FAILED_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.warning("Could not write to failed.log: %s", e)


# Filename template understood by yt-dlp (YouTube Music populates these fields)
_NAME_TEMPLATE = "%(title)s - %(artist)s [%(album)s]"


def _build_download_target(query: str) -> str:
    """Return a yt-dlp download target from a URL or plain-text search query."""
    if query.startswith("http"):
        return query
    return f"ytsearch1:{query}"


def _build_ydl_opts(audio_dir: str, cover_dir: str) -> dict:
    """Return yt-dlp options that download to *audio_dir* and *cover_dir*."""
    return {
        "format": "bestaudio/best",
        "noplaylist": True,
        "outtmpl": {
            "default": os.path.join(audio_dir, f"{_NAME_TEMPLATE}.%(ext)s"),
            "thumbnail": os.path.join(cover_dir, f"{_NAME_TEMPLATE}.%(ext)s"),
        },
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "m4a",
            }
        ],
        "writethumbnail": True,
        "updatetime": False,
        # Use Android/iOS clients to avoid "Video unavailable" errors caused by
        # YouTube tightening restrictions on the default web client extractor.
        # Force player_js_variant=main to avoid the tv-player-ias.js variant,
        # which causes deno to crash with "Cannot read properties of undefined
        # (reading 'origin')" when solving signature/n challenges.
        "extractor_args": {
            "youtube": {
                "client": ["android", "ios", "web"],
                "player_js_variant": ["main"],
            }
        },
    }


def _build_display_name(info: dict) -> str:
    """Build a human-readable display name from yt-dlp info metadata.

    Format: "Title - Artist [Album]", with missing parts omitted gracefully.
    """
    title = info.get("title", "")
    artist = info.get("artist", "")
    album = info.get("album", "")

    if not artist and not album:
        return title
    if not artist:
        return f"{title} [{album}]"
    if not album:
        return f"{title} - {artist}"
    return f"{title} - {artist} [{album}]"


def process_download(query: str) -> None:
    """Download audio and cover art for *query* (URL or search text).

    Files are stored under a YYYY-MM subdirectory of today's date.
    Sends a Discord notification on success or failure.
    """
    month_folder = datetime.now().strftime("%Y-%m")
    audio_dir = os.path.join(AUDIO_BASE_DIR, month_folder)
    cover_dir = os.path.join(COVER_BASE_DIR, month_folder)
    cropped_dir = os.path.join(COVER_CROPPED_BASE_DIR, month_folder)

    target = _build_download_target(query)
    ydl_opts = _build_ydl_opts(audio_dir, cover_dir)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(target, download=False)
            if "entries" in info:
                info = info["entries"][0]

            base_filename = os.path.splitext(
                os.path.basename(ydl.prepare_filename(info))
            )[0]

            ydl.download([target])

        crop_thumbnail_to_square(base_filename, cover_dir, cropped_dir)

        display_name = _build_display_name(info)
        logger.info("Downloaded and archived to %s: %s", month_folder, display_name)
        send_discord_notification(
            display_name, success=True, detail=f"已归档至 {month_folder}"
        )

    except Exception as exc:
        logger.error("Download failed for %s: %s", query, exc)
        _record_failure(query, str(exc))
        remove_download(query)
        send_discord_notification(query, success=False, detail=str(exc))

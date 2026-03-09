"""File-system helpers for listing and deleting downloaded songs."""

import os
import shutil
from config import (
    AUDIO_BASE_DIR,
    COVER_BASE_DIR,
    COVER_CROPPED_BASE_DIR,
    ARCHIVE_AUDIO_DIR,
    ARCHIVE_COVER_DIR,
    ARCHIVE_COVER_CROPPED_DIR,
)

# Separator used in filenames: "Title - Artist [Album].m4a"
_SEPARATOR = " - "


def _parse_filename(filename_no_ext: str) -> tuple[str, str, str]:
    """Parse a 'Title - Artist [Album]' filename into (title, artist, album).

    Steps:
      1. Extract album from trailing [...] brackets (if present).
      2. Split the remainder on the *last* ' - ' into title and artist.

    Returns (title, artist, album). Artist and album may be empty strings.
    """
    remaining = filename_no_ext
    album = ""

    # Extract [Album] from end
    if remaining.endswith("]"):
        bracket_idx = remaining.rfind("[")
        if bracket_idx != -1:
            album = remaining[bracket_idx + 1:-1].strip()
            remaining = remaining[:bracket_idx].strip()

    # Split remaining into Title - Artist
    idx = remaining.rfind(_SEPARATOR)
    if idx == -1:
        return remaining, "", album
    title = remaining[:idx]
    artist = remaining[idx + len(_SEPARATOR):]
    return title, artist, album


def list_all_songs() -> list[dict]:
    """Walk the audio directory and build a list of song records.

    Each record contains:
      - title: str          (song title parsed from filename)
      - artist: str         (artist parsed from filename, may be empty)
      - album: str          (album parsed from filename, may be empty)
      - display_name: str   (full filename without extension, used for cover matching)
      - date: str           (YYYY-MM derived from the YYYY-MM path)
      - audio_path: str     (path relative to /downloads)
      - cover_path: str|None (relative path to best available cover, or None)
      - size_bytes: int
      - is_duplicate: bool  (True when the same display_name exists on multiple dates)
    """
    songs: list[dict] = []
    title_dates: dict[str, set[str]] = {}

    if not os.path.isdir(AUDIO_BASE_DIR):
        return songs

    for root, _dirs, files in os.walk(AUDIO_BASE_DIR):
        for fname in files:
            if not fname.endswith(".m4a"):
                continue

            full_path = os.path.join(root, fname)
            display_name = os.path.splitext(fname)[0]
            title, artist, album = _parse_filename(display_name)

            # Extract date from directory structure: .../audio/YYYY-MM/file
            rel_from_audio = os.path.relpath(root, AUDIO_BASE_DIR)
            month_str = rel_from_audio.replace("\\", "/").split("/")[0]
            date_str = month_str if month_str != "." else "unknown"

            # Build relative paths (from /downloads root)
            audio_rel = os.path.relpath(full_path, os.path.dirname(AUDIO_BASE_DIR))
            audio_rel = audio_rel.replace("\\", "/")

            # Find matching cover (uses full display_name for file matching)
            cover_rel = _find_cover(display_name, rel_from_audio)

            size_bytes = os.path.getsize(full_path)
            downloaded_at = os.path.getmtime(full_path)

            songs.append({
                "title": title,
                "artist": artist,
                "album": album,
                "display_name": display_name,
                "date": date_str,
                "downloaded_at": downloaded_at,
                "audio_path": audio_rel,
                "cover_path": cover_rel,
                "size_bytes": size_bytes,
            })

            title_dates.setdefault(display_name, set()).add(date_str)

    # Mark duplicates (based on full display_name = title + artist)
    for song in songs:
        song["is_duplicate"] = len(title_dates.get(song["display_name"], set())) > 1

    # Sort by actual download time, newest first
    songs.sort(key=lambda s: s["downloaded_at"], reverse=True)

    return songs


def _find_cover(title: str, rel_from_audio: str) -> str | None:
    """Return the relative cover path (from /downloads) for a given title.

    Prefers the _square.jpg from covers-cropped/, then falls back to any
    original cover in covers/.
    """
    # Prefer cropped square version from the dedicated cropped directory
    cropped_dir = os.path.join(COVER_CROPPED_BASE_DIR, rel_from_audio)
    square = os.path.join(cropped_dir, f"{title}_square.jpg")
    if os.path.isfile(square):
        rel = os.path.relpath(square, os.path.dirname(COVER_CROPPED_BASE_DIR))
        return rel.replace("\\", "/")

    # Fall back to original cover in covers/
    cover_dir = os.path.join(COVER_BASE_DIR, rel_from_audio)
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        original = os.path.join(cover_dir, f"{title}{ext}")
        if os.path.isfile(original):
            rel = os.path.relpath(original, os.path.dirname(COVER_BASE_DIR))
            return rel.replace("\\", "/")

    return None


def delete_files(audio_paths: list[str]) -> list[dict]:
    """Delete audio files and their matching covers.

    Args:
        audio_paths: list of paths relative to /downloads (e.g. "audio/2026-03/Song.m4a")

    Returns:
        List of {"path": str, "deleted": bool, "error": str|None} results.
    """
    base = os.path.realpath(os.path.dirname(AUDIO_BASE_DIR))  # /downloads
    results = []

    for rel_path in audio_paths:
        result = {"path": rel_path, "deleted": False, "error": None}

        full_audio = os.path.realpath(
            os.path.join(base, rel_path.replace("/", os.sep))
        )

        # Guard against path traversal: resolved path must stay inside /downloads
        if not full_audio.startswith(base + os.sep):
            result["error"] = "Invalid path"
            results.append(result)
            continue

        if not os.path.isfile(full_audio):
            result["error"] = "File not found"
            results.append(result)
            continue

        title = os.path.splitext(os.path.basename(full_audio))[0]
        rel_from_audio = os.path.relpath(os.path.dirname(full_audio), AUDIO_BASE_DIR)
        cover_dir = os.path.join(COVER_BASE_DIR, rel_from_audio)
        cropped_dir = os.path.join(COVER_CROPPED_BASE_DIR, rel_from_audio)

        try:
            os.remove(full_audio)
            for cover_file in _cover_files_for_title(title, cover_dir):
                os.remove(os.path.join(cover_dir, cover_file))
            for cover_file in _cover_files_for_title(title, cropped_dir):
                os.remove(os.path.join(cropped_dir, cover_file))
            result["deleted"] = True
        except Exception as e:
            result["error"] = str(e)

        results.append(result)

    return results


def _cover_files_for_title(title: str, cover_dir: str) -> list[str]:
    """Return all filenames in *cover_dir* that belong to *title*.

    Matches both the original (``title.ext``) and square (``title_square.jpg``) variants.
    """
    if not os.path.isdir(cover_dir):
        return []
    matched = []
    for fname in os.listdir(cover_dir):
        stem = os.path.splitext(fname)[0]
        if stem == title or stem == f"{title}_square":
            matched.append(fname)
    return matched


def _unique_dest(dest_path: str) -> str:
    """Return dest_path if it doesn't exist, otherwise append _1, _2, etc."""
    if not os.path.exists(dest_path):
        return dest_path
    base, ext = os.path.splitext(dest_path)
    n = 1
    while os.path.exists(f"{base}_{n}{ext}"):
        n += 1
    return f"{base}_{n}{ext}"


def archive_selected(audio_paths: list[str]) -> dict:
    """Move specified songs (audio + covers) from date directories to the flat archive.

    Args:
        audio_paths: list of paths relative to /downloads (e.g. "audio/2026-03/Song.m4a")

    Returns {"archived": int, "errors": [str]}.
    """
    base = os.path.realpath(os.path.dirname(AUDIO_BASE_DIR))  # /downloads
    archived = 0
    errors = []

    for rel_path in audio_paths:
        full_audio = os.path.realpath(
            os.path.join(base, rel_path.replace("/", os.sep))
        )

        # Guard against path traversal
        if not full_audio.startswith(base + os.sep):
            errors.append(f"{rel_path}: Invalid path")
            continue

        if not os.path.isfile(full_audio):
            errors.append(f"{rel_path}: File not found")
            continue

        fname = os.path.basename(full_audio)
        display_name = os.path.splitext(fname)[0]
        rel_from_audio = os.path.relpath(os.path.dirname(full_audio), AUDIO_BASE_DIR)

        try:
            dst_audio = _unique_dest(os.path.join(ARCHIVE_AUDIO_DIR, fname))
            shutil.move(full_audio, dst_audio)

            cover_dir = os.path.join(COVER_BASE_DIR, rel_from_audio)
            for cover_file in _cover_files_for_title(display_name, cover_dir):
                src_cover = os.path.join(cover_dir, cover_file)
                dst_cover = _unique_dest(os.path.join(ARCHIVE_COVER_DIR, cover_file))
                shutil.move(src_cover, dst_cover)

            cropped_dir = os.path.join(COVER_CROPPED_BASE_DIR, rel_from_audio)
            for cover_file in _cover_files_for_title(display_name, cropped_dir):
                src_cover = os.path.join(cropped_dir, cover_file)
                dst_cover = _unique_dest(os.path.join(ARCHIVE_COVER_CROPPED_DIR, cover_file))
                shutil.move(src_cover, dst_cover)

            archived += 1
        except Exception as e:
            errors.append(f"{fname}: {e}")

    # Clean up empty month directories
    for base_dir in (AUDIO_BASE_DIR, COVER_BASE_DIR, COVER_CROPPED_BASE_DIR):
        if not os.path.isdir(base_dir):
            continue
        for entry in os.listdir(base_dir):
            month_dir = os.path.join(base_dir, entry)
            if os.path.isdir(month_dir) and not os.listdir(month_dir):
                os.rmdir(month_dir)

    return {"archived": archived, "errors": errors}


def archive_all() -> dict:
    """Move all songs (audio + covers) from date directories to the flat archive.

    Returns {"archived": int, "errors": [str]}.
    """
    archived = 0
    errors = []

    if not os.path.isdir(AUDIO_BASE_DIR):
        return {"archived": 0, "errors": []}

    # Collect files first to avoid mutating dirs during walk
    audio_files = []
    for root, _dirs, files in os.walk(AUDIO_BASE_DIR):
        for fname in files:
            if fname.endswith(".m4a"):
                audio_files.append((root, fname))

    for root, fname in audio_files:
        display_name = os.path.splitext(fname)[0]
        rel_from_audio = os.path.relpath(root, AUDIO_BASE_DIR)

        try:
            # Move audio
            src_audio = os.path.join(root, fname)
            dst_audio = _unique_dest(os.path.join(ARCHIVE_AUDIO_DIR, fname))
            shutil.move(src_audio, dst_audio)

            # Move matching original covers
            cover_dir = os.path.join(COVER_BASE_DIR, rel_from_audio)
            for cover_file in _cover_files_for_title(display_name, cover_dir):
                src_cover = os.path.join(cover_dir, cover_file)
                dst_cover = _unique_dest(os.path.join(ARCHIVE_COVER_DIR, cover_file))
                shutil.move(src_cover, dst_cover)

            # Move matching cropped covers
            cropped_dir = os.path.join(COVER_CROPPED_BASE_DIR, rel_from_audio)
            for cover_file in _cover_files_for_title(display_name, cropped_dir):
                src_cover = os.path.join(cropped_dir, cover_file)
                dst_cover = _unique_dest(os.path.join(ARCHIVE_COVER_CROPPED_DIR, cover_file))
                shutil.move(src_cover, dst_cover)

            archived += 1
        except Exception as e:
            errors.append(f"{fname}: {e}")

    # Clean up empty month directories
    for base_dir in (AUDIO_BASE_DIR, COVER_BASE_DIR, COVER_CROPPED_BASE_DIR):
        if not os.path.isdir(base_dir):
            continue
        for entry in os.listdir(base_dir):
            month_dir = os.path.join(base_dir, entry)
            if os.path.isdir(month_dir) and not os.listdir(month_dir):
                os.rmdir(month_dir)

    return {"archived": archived, "errors": errors}

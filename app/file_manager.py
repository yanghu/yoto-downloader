"""File-system helpers for listing and deleting downloaded songs."""

import os
from config import AUDIO_BASE_DIR, COVER_BASE_DIR

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
      - date: str           (YYYY-MM-DD derived from the YYYY-MM/DD path)
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

            # Extract date from directory structure: .../audio/YYYY-MM/DD/file
            rel_from_audio = os.path.relpath(root, AUDIO_BASE_DIR)
            parts = rel_from_audio.replace("\\", "/").split("/")
            if len(parts) >= 2:
                date_str = f"{parts[0]}-{parts[1]}"  # YYYY-MM-DD
            else:
                date_str = "unknown"

            # Build relative paths (from /downloads root)
            audio_rel = os.path.relpath(full_path, os.path.dirname(AUDIO_BASE_DIR))
            audio_rel = audio_rel.replace("\\", "/")

            # Find matching cover (uses full display_name for file matching)
            cover_rel = _find_cover(display_name, rel_from_audio)

            size_bytes = os.path.getsize(full_path)

            songs.append({
                "title": title,
                "artist": artist,
                "album": album,
                "display_name": display_name,
                "date": date_str,
                "audio_path": audio_rel,
                "cover_path": cover_rel,
                "size_bytes": size_bytes,
            })

            title_dates.setdefault(display_name, set()).add(date_str)

    # Mark duplicates (based on full display_name = title + artist)
    for song in songs:
        song["is_duplicate"] = len(title_dates.get(song["display_name"], set())) > 1

    # Sort newest first, then alphabetical
    songs.sort(key=lambda s: (s["date"], s["title"]), reverse=True)

    return songs


def _find_cover(title: str, rel_from_audio: str) -> str | None:
    """Return the relative cover path (from /downloads) for a given title.

    Prefers the _square.jpg variant, then falls back to any original cover.
    """
    cover_dir = os.path.join(COVER_BASE_DIR, rel_from_audio)
    if not os.path.isdir(cover_dir):
        return None

    # Prefer square version
    square = os.path.join(cover_dir, f"{title}_square.jpg")
    if os.path.isfile(square):
        rel = os.path.relpath(square, os.path.dirname(COVER_BASE_DIR))
        return rel.replace("\\", "/")

    # Fall back to original cover in any format
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        original = os.path.join(cover_dir, f"{title}{ext}")
        if os.path.isfile(original):
            rel = os.path.relpath(original, os.path.dirname(COVER_BASE_DIR))
            return rel.replace("\\", "/")

    return None


def delete_files(audio_paths: list[str]) -> list[dict]:
    """Delete audio files and their matching covers.

    Args:
        audio_paths: list of paths relative to /downloads (e.g. "audio/2026-03/04/Song.m4a")

    Returns:
        List of {"path": str, "deleted": bool, "error": str|None} results.
    """
    base = os.path.dirname(AUDIO_BASE_DIR)  # /downloads
    results = []

    for rel_path in audio_paths:
        full_audio = os.path.join(base, rel_path.replace("/", os.sep))
        result = {"path": rel_path, "deleted": False, "error": None}

        if not os.path.isfile(full_audio):
            result["error"] = "File not found"
            results.append(result)
            continue

        title = os.path.splitext(os.path.basename(full_audio))[0]

        # Derive matching cover directory
        # audio path: audio/YYYY-MM/DD/file.m4a → covers/YYYY-MM/DD/
        rel_from_audio = os.path.relpath(
            os.path.dirname(full_audio), AUDIO_BASE_DIR
        )
        cover_dir = os.path.join(COVER_BASE_DIR, rel_from_audio)

        try:
            os.remove(full_audio)

            # Remove all matching covers
            if os.path.isdir(cover_dir):
                for cover_file in os.listdir(cover_dir):
                    cover_name = os.path.splitext(cover_file)[0]
                    # Match "Title.ext" and "Title_square.jpg"
                    if cover_name == title or cover_name == f"{title}_square":
                        os.remove(os.path.join(cover_dir, cover_file))

            result["deleted"] = True
        except Exception as e:
            result["error"] = str(e)

        results.append(result)

    return results

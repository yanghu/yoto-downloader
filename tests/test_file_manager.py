"""Unit tests for file_manager module."""

import os
import pytest
from unittest.mock import patch
from file_manager import list_all_songs, delete_files, _find_cover, _parse_filename, archive_all


@pytest.fixture
def tmp_downloads(tmp_path):
    """Create a temporary downloads directory structure."""
    audio_base = tmp_path / "audio"
    cover_base = tmp_path / "covers"

    # Create songs in 2026-03
    month1_audio = audio_base / "2026-03"
    month1_cover = cover_base / "2026-03"
    month1_audio.mkdir(parents=True)
    month1_cover.mkdir(parents=True)

    (month1_audio / "SongA.m4a").write_bytes(b"\x00" * 1000)
    (month1_cover / "SongA.webp").write_bytes(b"\x00" * 200)
    (month1_cover / "SongA_square.jpg").write_bytes(b"\x00" * 300)
    (month1_audio / "SongB.m4a").write_bytes(b"\x00" * 2000)
    (month1_cover / "SongB_square.jpg").write_bytes(b"\x00" * 400)

    # Create a duplicate of SongA in a different month (same full filename = same display_name)
    month2_audio = audio_base / "2026-04"
    month2_audio.mkdir(parents=True)
    (month2_audio / "SongA.m4a").write_bytes(b"\x00" * 1500)

    return tmp_path


def _patch_dirs(tmp_path):
    """Return patches for AUDIO_BASE_DIR and COVER_BASE_DIR."""
    return (
        patch("file_manager.AUDIO_BASE_DIR", str(tmp_path / "audio")),
        patch("file_manager.COVER_BASE_DIR", str(tmp_path / "covers")),
    )


def test_list_songs_empty_dir(tmp_path):
    """No audio files → empty list."""
    empty_audio = tmp_path / "audio"
    empty_audio.mkdir()
    with patch("file_manager.AUDIO_BASE_DIR", str(empty_audio)), \
         patch("file_manager.COVER_BASE_DIR", str(tmp_path / "covers")):
        songs = list_all_songs()
    assert songs == []


def test_list_songs_returns_correct_records(tmp_downloads):
    """Listing should return all songs with correct fields."""
    p1, p2 = _patch_dirs(tmp_downloads)
    with p1, p2:
        songs = list_all_songs()

    assert len(songs) == 3
    titles = {s["title"] for s in songs}
    assert titles == {"SongA", "SongB"}

    # Check fields exist on every record
    for s in songs:
        assert "title" in s
        assert "artist" in s
        assert "album" in s
        assert "display_name" in s
        assert "date" in s
        assert "audio_path" in s
        assert "cover_path" is not None or s["title"] == "SongA"
        assert "size_bytes" in s
        assert "is_duplicate" in s


def test_list_songs_detects_duplicates(tmp_downloads):
    """Same title on multiple days → both marked as duplicates."""
    p1, p2 = _patch_dirs(tmp_downloads)
    with p1, p2:
        songs = list_all_songs()

    song_a_records = [s for s in songs if s["title"] == "SongA"]
    assert len(song_a_records) == 2
    assert all(s["is_duplicate"] for s in song_a_records)

    song_b_records = [s for s in songs if s["title"] == "SongB"]
    assert len(song_b_records) == 1
    assert not song_b_records[0]["is_duplicate"]


def test_list_songs_prefers_square_cover(tmp_downloads):
    """Cover path should prefer _square.jpg variant."""
    p1, p2 = _patch_dirs(tmp_downloads)
    with p1, p2:
        songs = list_all_songs()

    song_a_day1 = [s for s in songs if s["title"] == "SongA" and s["date"] == "2026-03"][0]
    assert song_a_day1["cover_path"] is not None
    assert "_square" in song_a_day1["cover_path"]


def test_delete_files_removes_audio_and_covers(tmp_downloads):
    """Deleting should remove the audio file and all matching covers."""
    p1, p2 = _patch_dirs(tmp_downloads)
    with p1, p2:
        results = delete_files(["audio/2026-03/SongA.m4a"])

    assert len(results) == 1
    assert results[0]["deleted"] is True
    assert results[0]["error"] is None

    # Audio file should be gone
    assert not (tmp_downloads / "audio" / "2026-03" / "SongA.m4a").exists()
    # Cover files should be gone
    assert not (tmp_downloads / "covers" / "2026-03" / "SongA.webp").exists()
    assert not (tmp_downloads / "covers" / "2026-03" / "SongA_square.jpg").exists()


def test_delete_files_nonexistent_path(tmp_downloads):
    """Deleting a nonexistent file should return an error, not raise."""
    p1, p2 = _patch_dirs(tmp_downloads)
    with p1, p2:
        results = delete_files(["audio/2026-03/NonExistent.m4a"])

    assert len(results) == 1
    assert results[0]["deleted"] is False
    assert results[0]["error"] == "File not found"


def test_delete_preserves_other_files(tmp_downloads):
    """Deleting one song should not affect another in the same directory."""
    p1, p2 = _patch_dirs(tmp_downloads)

    # Put an extra song in same month next to SongB
    extra = tmp_downloads / "audio" / "2026-03" / "SongC.m4a"
    extra.write_bytes(b"\x00" * 500)

    with p1, p2:
        delete_files(["audio/2026-03/SongB.m4a"])

    assert not (tmp_downloads / "audio" / "2026-03" / "SongB.m4a").exists()
    assert extra.exists(), "SongC should not be deleted"


# ─────────────────── _parse_filename tests ───────────────────

def test_parse_filename_with_artist():
    """Standard 'Title - Artist' format."""
    title, artist, album = _parse_filename("Hakuna Matata - Hans Zimmer")
    assert title == "Hakuna Matata"
    assert artist == "Hans Zimmer"
    assert album == ""


def test_parse_filename_without_artist():
    """Legacy filename without separator → artist is empty."""
    title, artist, album = _parse_filename("Hakuna Matata")
    assert title == "Hakuna Matata"
    assert artist == ""
    assert album == ""


def test_parse_filename_title_contains_dash():
    """Title with ' - ' in it → uses last occurrence."""
    title, artist, album = _parse_filename("Part 1 - The Beginning - Artist Name")
    assert title == "Part 1 - The Beginning"
    assert artist == "Artist Name"
    assert album == ""


def test_parse_filename_with_album():
    """Full 'Title - Artist [Album]' format."""
    title, artist, album = _parse_filename("Hakuna Matata - Hans Zimmer [The Lion King]")
    assert title == "Hakuna Matata"
    assert artist == "Hans Zimmer"
    assert album == "The Lion King"


def test_parse_filename_album_no_artist():
    """'Title [Album]' without artist."""
    title, artist, album = _parse_filename("Hakuna Matata [The Lion King]")
    assert title == "Hakuna Matata"
    assert artist == ""
    assert album == "The Lion King"


def test_list_songs_with_artist_filename(tmp_path):
    """Files named 'Title - Artist [Album].m4a' have all fields parsed correctly."""
    audio_base = tmp_path / "audio" / "2026-03"
    audio_base.mkdir(parents=True)
    (audio_base / "Hakuna Matata - Hans Zimmer [The Lion King].m4a").write_bytes(b"\x00" * 1000)

    with patch("file_manager.AUDIO_BASE_DIR", str(tmp_path / "audio")), \
         patch("file_manager.COVER_BASE_DIR", str(tmp_path / "covers")):
        songs = list_all_songs()

    assert len(songs) == 1
    assert songs[0]["title"] == "Hakuna Matata"
    assert songs[0]["artist"] == "Hans Zimmer"
    assert songs[0]["album"] == "The Lion King"
    assert songs[0]["display_name"] == "Hakuna Matata - Hans Zimmer [The Lion King]"


# ─────────────────── archive_all tests ───────────────────

def _patch_all_dirs(tmp_path):
    """Return patches for all four directory constants."""
    return (
        patch("file_manager.AUDIO_BASE_DIR", str(tmp_path / "audio")),
        patch("file_manager.COVER_BASE_DIR", str(tmp_path / "covers")),
        patch("file_manager.ARCHIVE_AUDIO_DIR", str(tmp_path / "archive" / "audio")),
        patch("file_manager.ARCHIVE_COVER_DIR", str(tmp_path / "archive" / "covers")),
    )


@pytest.fixture
def tmp_archive_setup(tmp_path):
    """Create downloads + empty archive directories."""
    audio = tmp_path / "audio" / "2026-03"
    covers = tmp_path / "covers" / "2026-03"
    archive_audio = tmp_path / "archive" / "audio"
    archive_covers = tmp_path / "archive" / "covers"
    for d in (audio, covers, archive_audio, archive_covers):
        d.mkdir(parents=True)

    (audio / "SongA.m4a").write_bytes(b"\x00" * 1000)
    (covers / "SongA_square.jpg").write_bytes(b"\x00" * 200)
    (covers / "SongA.webp").write_bytes(b"\x00" * 150)
    (audio / "SongB.m4a").write_bytes(b"\x00" * 2000)

    return tmp_path


def test_archive_all_moves_audio_and_covers(tmp_archive_setup):
    """Archive should move audio and matching covers to archive directory."""
    p1, p2, p3, p4 = _patch_all_dirs(tmp_archive_setup)
    with p1, p2, p3, p4:
        result = archive_all()

    assert result["archived"] == 2
    assert result["errors"] == []

    # Files should exist in archive
    assert (tmp_archive_setup / "archive" / "audio" / "SongA.m4a").exists()
    assert (tmp_archive_setup / "archive" / "audio" / "SongB.m4a").exists()
    assert (tmp_archive_setup / "archive" / "covers" / "SongA_square.jpg").exists()
    assert (tmp_archive_setup / "archive" / "covers" / "SongA.webp").exists()

    # Files should be gone from original
    assert not (tmp_archive_setup / "audio" / "2026-03" / "SongA.m4a").exists()
    assert not (tmp_archive_setup / "audio" / "2026-03" / "SongB.m4a").exists()


def test_archive_all_cleans_empty_month_dirs(tmp_archive_setup):
    """Empty month directories should be removed after archive."""
    p1, p2, p3, p4 = _patch_all_dirs(tmp_archive_setup)
    with p1, p2, p3, p4:
        archive_all()

    assert not (tmp_archive_setup / "audio" / "2026-03").exists()
    assert not (tmp_archive_setup / "covers" / "2026-03").exists()


def test_archive_all_handles_duplicate_names(tmp_archive_setup):
    """When a file with the same name already exists in archive, append suffix."""
    # Pre-populate archive with a SongA.m4a
    (tmp_archive_setup / "archive" / "audio" / "SongA.m4a").write_bytes(b"\x00" * 500)

    p1, p2, p3, p4 = _patch_all_dirs(tmp_archive_setup)
    with p1, p2, p3, p4:
        result = archive_all()

    assert result["archived"] == 2
    # Original archive file still there
    assert (tmp_archive_setup / "archive" / "audio" / "SongA.m4a").exists()
    # New one got a suffix
    assert (tmp_archive_setup / "archive" / "audio" / "SongA_1.m4a").exists()


def test_archive_all_empty_dir(tmp_path):
    """Archive with no songs returns 0."""
    audio = tmp_path / "audio"
    audio.mkdir()
    archive_audio = tmp_path / "archive" / "audio"
    archive_covers = tmp_path / "archive" / "covers"
    archive_audio.mkdir(parents=True)
    archive_covers.mkdir(parents=True)

    p1, p2, p3, p4 = _patch_all_dirs(tmp_path)
    with p1, p2, p3, p4:
        result = archive_all()

    assert result["archived"] == 0
    assert result["errors"] == []

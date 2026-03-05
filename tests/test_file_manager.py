"""Unit tests for file_manager module."""

import os
import pytest
from unittest.mock import patch
from file_manager import list_all_songs, delete_files, _find_cover, _parse_filename


@pytest.fixture
def tmp_downloads(tmp_path):
    """Create a temporary downloads directory structure."""
    audio_base = tmp_path / "audio"
    cover_base = tmp_path / "covers"

    # Create a song on 2026-03/04
    day1_audio = audio_base / "2026-03" / "04"
    day1_cover = cover_base / "2026-03" / "04"
    day1_audio.mkdir(parents=True)
    day1_cover.mkdir(parents=True)

    (day1_audio / "SongA.m4a").write_bytes(b"\x00" * 1000)
    (day1_cover / "SongA.webp").write_bytes(b"\x00" * 200)
    (day1_cover / "SongA_square.jpg").write_bytes(b"\x00" * 300)

    # Create another song on 2026-03/05
    day2_audio = audio_base / "2026-03" / "05"
    day2_cover = cover_base / "2026-03" / "05"
    day2_audio.mkdir(parents=True)
    day2_cover.mkdir(parents=True)

    (day2_audio / "SongB.m4a").write_bytes(b"\x00" * 2000)
    (day2_cover / "SongB_square.jpg").write_bytes(b"\x00" * 400)

    # Create a duplicate of SongA on a different day (same full filename = same display_name)
    (day2_audio / "SongA.m4a").write_bytes(b"\x00" * 1500)

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

    song_a_day1 = [s for s in songs if s["title"] == "SongA" and "04" in s["date"]][0]
    assert song_a_day1["cover_path"] is not None
    assert "_square" in song_a_day1["cover_path"]


def test_delete_files_removes_audio_and_covers(tmp_downloads):
    """Deleting should remove the audio file and all matching covers."""
    p1, p2 = _patch_dirs(tmp_downloads)
    with p1, p2:
        results = delete_files(["audio/2026-03/04/SongA.m4a"])

    assert len(results) == 1
    assert results[0]["deleted"] is True
    assert results[0]["error"] is None

    # Audio file should be gone
    assert not (tmp_downloads / "audio" / "2026-03" / "04" / "SongA.m4a").exists()
    # Cover files should be gone
    assert not (tmp_downloads / "covers" / "2026-03" / "04" / "SongA.webp").exists()
    assert not (tmp_downloads / "covers" / "2026-03" / "04" / "SongA_square.jpg").exists()


def test_delete_files_nonexistent_path(tmp_downloads):
    """Deleting a nonexistent file should return an error, not raise."""
    p1, p2 = _patch_dirs(tmp_downloads)
    with p1, p2:
        results = delete_files(["audio/2026-03/04/NonExistent.m4a"])

    assert len(results) == 1
    assert results[0]["deleted"] is False
    assert results[0]["error"] == "File not found"


def test_delete_preserves_other_files(tmp_downloads):
    """Deleting one song should not affect another in the same directory."""
    p1, p2 = _patch_dirs(tmp_downloads)

    # Put an extra song on day 2 next to SongB
    extra = tmp_downloads / "audio" / "2026-03" / "05" / "SongC.m4a"
    extra.write_bytes(b"\x00" * 500)

    with p1, p2:
        delete_files(["audio/2026-03/05/SongB.m4a"])

    assert not (tmp_downloads / "audio" / "2026-03" / "05" / "SongB.m4a").exists()
    assert extra.exists(), "SongC should not be deleted"


# ─────────────────── _parse_filename tests ───────────────────

def test_parse_filename_with_artist():
    """Standard 'Title - Artist' format."""
    title, artist = _parse_filename("Hakuna Matata - Hans Zimmer")
    assert title == "Hakuna Matata"
    assert artist == "Hans Zimmer"


def test_parse_filename_without_artist():
    """Legacy filename without separator → artist is empty."""
    title, artist = _parse_filename("Hakuna Matata")
    assert title == "Hakuna Matata"
    assert artist == ""


def test_parse_filename_title_contains_dash():
    """Title with ' - ' in it → uses last occurrence."""
    title, artist = _parse_filename("Part 1 - The Beginning - Artist Name")
    assert title == "Part 1 - The Beginning"
    assert artist == "Artist Name"


def test_list_songs_with_artist_filename(tmp_path):
    """Files named 'Title - Artist.m4a' have artist parsed correctly."""
    audio_base = tmp_path / "audio" / "2026-03" / "04"
    audio_base.mkdir(parents=True)
    (audio_base / "Hakuna Matata - Hans Zimmer.m4a").write_bytes(b"\x00" * 1000)

    with patch("file_manager.AUDIO_BASE_DIR", str(tmp_path / "audio")), \
         patch("file_manager.COVER_BASE_DIR", str(tmp_path / "covers")):
        songs = list_all_songs()

    assert len(songs) == 1
    assert songs[0]["title"] == "Hakuna Matata"
    assert songs[0]["artist"] == "Hans Zimmer"
    assert songs[0]["display_name"] == "Hakuna Matata - Hans Zimmer"

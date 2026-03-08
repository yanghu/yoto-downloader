import os
import sys
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

# Mock yt_dlp entirely before importing downloader, since it's not installed on dev
mock_yt_dlp = MagicMock()
sys.modules['yt_dlp'] = mock_yt_dlp

from downloader import (
    _build_display_name,
    _build_download_target,
    _build_ydl_opts,
    process_download,
)


@pytest.fixture(autouse=True)
def reset_yt_dlp_mock():
    """Reset the yt_dlp mock before each test."""
    mock_yt_dlp.reset_mock()
    yield


def _setup_ydl_mock(title="Test Video", artist="", album="", ext="m4a"):
    """Configure the mocked YoutubeDL context manager to return fake info."""
    mock_ydl_instance = MagicMock()
    info = {'title': title, 'ext': ext}
    if artist:
        info['artist'] = artist
    if album:
        info['album'] = album
    mock_ydl_instance.extract_info.return_value = info
    mock_ydl_instance.prepare_filename.return_value = f"/fake/path/{title}.{ext}"
    mock_yt_dlp.YoutubeDL.return_value.__enter__ = MagicMock(return_value=mock_ydl_instance)
    mock_yt_dlp.YoutubeDL.return_value.__exit__ = MagicMock(return_value=False)
    return mock_ydl_instance


# ---------------------------------------------------------------------------
# _build_download_target
# ---------------------------------------------------------------------------

class TestBuildDownloadTarget:
    def test_http_url_returned_unchanged(self):
        url = "https://www.youtube.com/watch?v=abc123"
        assert _build_download_target(url) == url

    def test_http_without_s_returned_unchanged(self):
        url = "http://youtu.be/abc123"
        assert _build_download_target(url) == url

    def test_plain_text_wrapped_as_ytsearch(self):
        assert _build_download_target("baby shark") == "ytsearch1:baby shark"

    def test_empty_string_wrapped_as_ytsearch(self):
        assert _build_download_target("") == "ytsearch1:"


# ---------------------------------------------------------------------------
# _build_ydl_opts
# ---------------------------------------------------------------------------

class TestBuildYdlOpts:
    def test_outtmpl_contains_audio_dir(self):
        opts = _build_ydl_opts("/audio/2026-03", "/covers/2026-03")
        assert "/audio/2026-03" in opts["outtmpl"]["default"]

    def test_outtmpl_contains_cover_dir(self):
        opts = _build_ydl_opts("/audio/2026-03", "/covers/2026-03")
        assert "/covers/2026-03" in opts["outtmpl"]["thumbnail"]

    def test_outtmpl_includes_artist_and_album_placeholders(self):
        opts = _build_ydl_opts("/audio", "/covers")
        assert "%(artist)s" in opts["outtmpl"]["default"]
        assert "%(album)s" in opts["outtmpl"]["default"]
        assert "%(artist)s" in opts["outtmpl"]["thumbnail"]
        assert "%(album)s" in opts["outtmpl"]["thumbnail"]

    def test_noplaylist_is_true(self):
        opts = _build_ydl_opts("/audio", "/covers")
        assert opts["noplaylist"] is True

    def test_postprocessor_codec_is_m4a(self):
        opts = _build_ydl_opts("/audio", "/covers")
        pp = opts["postprocessors"][0]
        assert pp["key"] == "FFmpegExtractAudio"
        assert pp["preferredcodec"] == "m4a"


# ---------------------------------------------------------------------------
# _build_display_name
# ---------------------------------------------------------------------------

class TestBuildDisplayName:
    def test_title_artist_album(self):
        name = _build_display_name({"title": "Song", "artist": "Band", "album": "Record"})
        assert name == "Song - Band [Record]"

    def test_title_artist_no_album(self):
        name = _build_display_name({"title": "Song", "artist": "Band"})
        assert name == "Song - Band"

    def test_title_album_no_artist(self):
        name = _build_display_name({"title": "Song", "album": "Record"})
        assert name == "Song [Record]"

    def test_title_only(self):
        name = _build_display_name({"title": "Song"})
        assert name == "Song"

    def test_empty_artist_and_album_strings(self):
        """Explicit empty strings behave like missing keys."""
        name = _build_display_name({"title": "Song", "artist": "", "album": ""})
        assert name == "Song"


# ---------------------------------------------------------------------------
# process_download integration
# ---------------------------------------------------------------------------

def test_direct_url_used_as_download_target():
    """A URL starting with http passes directly to yt-dlp."""
    mock_ydl = _setup_ydl_mock()

    with patch('downloader.crop_thumbnail_to_square'):
        process_download("https://www.youtube.com/watch?v=abc123")

    mock_ydl.download.assert_called_once_with(["https://www.youtube.com/watch?v=abc123"])


def test_text_query_prefixed_with_ytsearch():
    """A plain text string gets wrapped as ytsearch1:..."""
    mock_ydl = _setup_ydl_mock()

    with patch('downloader.crop_thumbnail_to_square'):
        process_download("baby shark song")

    mock_ydl.download.assert_called_once_with(["ytsearch1:baby shark song"])


def test_successful_download_sends_success_notification():
    """Happy path: mock yt-dlp extracts info + downloads → success notification sent."""
    _setup_ydl_mock(title="My Great Song")

    with patch('downloader.crop_thumbnail_to_square'), \
         patch('downloader.send_discord_notification') as mock_notify:
        process_download("https://www.youtube.com/watch?v=xyz")

    mock_notify.assert_called_once()
    assert mock_notify.call_args[1]['success'] is True
    assert "My Great Song" in mock_notify.call_args[0][0]


def test_download_failure_is_caught():
    """Mock yt-dlp raises an exception → failure notification sent, no crash."""
    mock_ydl = _setup_ydl_mock()
    mock_ydl.extract_info.side_effect = Exception("Network error")

    with patch('downloader.send_discord_notification') as mock_notify:
        process_download("https://www.youtube.com/watch?v=fail")

    mock_notify.assert_called_once()
    assert mock_notify.call_args[1]['success'] is False
    assert "Network error" in mock_notify.call_args[1]['detail']


def test_output_paths_use_todays_date():
    """yt-dlp options are built with today's YYYY-MM folder structure."""
    _setup_ydl_mock()

    expected_month = datetime.now().strftime("%Y-%m")

    with patch('downloader.crop_thumbnail_to_square'):
        process_download("https://www.youtube.com/watch?v=date_test")

    opts = mock_yt_dlp.YoutubeDL.call_args[0][0]
    normalized = opts['outtmpl']['default'].replace('\\', '/')
    assert expected_month in normalized


def test_discord_notification_includes_artist_and_album():
    """When artist+album metadata exist, notification includes 'Title - Artist [Album]'."""
    _setup_ydl_mock(title="Hakuna Matata", artist="Hans Zimmer", album="The Lion King")

    with patch('downloader.crop_thumbnail_to_square'), \
         patch('downloader.send_discord_notification') as mock_notify:
        process_download("https://www.youtube.com/watch?v=artist_album_test")

    display_name = mock_notify.call_args[0][0]
    assert display_name == "Hakuna Matata - Hans Zimmer [The Lion King]"


def test_discord_notification_no_artist_fallback():
    """When no artist metadata, notification uses title only."""
    _setup_ydl_mock(title="Some Song")

    with patch('downloader.crop_thumbnail_to_square'), \
         patch('downloader.send_discord_notification') as mock_notify:
        process_download("https://www.youtube.com/watch?v=no_artist")

    assert mock_notify.call_args[0][0] == "Some Song"

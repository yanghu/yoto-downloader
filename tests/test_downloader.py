import os
import sys
from unittest.mock import patch, MagicMock
from datetime import datetime

import pytest

# Mock yt_dlp entirely before importing downloader, since it's not installed on dev
mock_yt_dlp = MagicMock()
sys.modules['yt_dlp'] = mock_yt_dlp

from downloader import process_download


@pytest.fixture(autouse=True)
def reset_yt_dlp_mock():
    """Reset the yt_dlp mock before each test."""
    mock_yt_dlp.reset_mock()
    yield


def _setup_ydl_mock(title="Test Video", ext="m4a"):
    """Configure the mocked YoutubeDL context manager to return fake info."""
    mock_ydl_instance = MagicMock()
    mock_ydl_instance.extract_info.return_value = {
        'title': title,
        'ext': ext,
    }
    mock_ydl_instance.prepare_filename.return_value = f"/fake/path/{title}.{ext}"
    mock_yt_dlp.YoutubeDL.return_value.__enter__ = MagicMock(return_value=mock_ydl_instance)
    mock_yt_dlp.YoutubeDL.return_value.__exit__ = MagicMock(return_value=False)
    return mock_ydl_instance


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


def test_successful_download_logs_success(capsys):
    """Happy path: mock yt-dlp extracts info + downloads → success message printed."""
    _setup_ydl_mock(title="My Great Song")
    
    with patch('downloader.crop_thumbnail_to_square'):
        process_download("https://www.youtube.com/watch?v=xyz")
    
    captured = capsys.readouterr()
    assert "✅" in captured.out
    assert "My Great Song" in captured.out


def test_download_failure_is_caught(capsys):
    """Mock yt-dlp raises an exception → error printed, no crash."""
    mock_ydl = _setup_ydl_mock()
    mock_ydl.extract_info.side_effect = Exception("Network error")
    
    # Should not raise
    process_download("https://www.youtube.com/watch?v=fail")
    
    captured = capsys.readouterr()
    assert "❌" in captured.out
    assert "Network error" in captured.out


def test_output_paths_use_todays_date():
    """Verifies the outtmpl options are built with today's YYYY-MM/DD folder structure."""
    _setup_ydl_mock()
    
    now = datetime.now()
    expected_month = now.strftime("%Y-%m")
    expected_day = now.strftime("%d")
    
    with patch('downloader.crop_thumbnail_to_square'):
        process_download("https://www.youtube.com/watch?v=date_test")
    
    # Inspect the opts passed to YoutubeDL constructor
    call_args = mock_yt_dlp.YoutubeDL.call_args
    opts = call_args[0][0]  # first positional arg
    
    default_template = opts['outtmpl']['default']
    # Normalize separators for cross-platform (config.py uses / but os.path.join adds \ on Windows)
    normalized = default_template.replace('\\', '/')
    assert expected_month in normalized
    assert f"/{expected_day}/" in normalized

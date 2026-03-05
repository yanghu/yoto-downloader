"""Unit tests for the URL validation / extraction helpers."""

import pytest
from unittest.mock import patch
from validator import validate_url, extract_url_id, is_duplicate, record_download, _seen


# ---------------------------------------------------------------------------
# validate_url – domain check
# ---------------------------------------------------------------------------

class TestDomainValidation:
    def test_youtube_com_allowed(self):
        validate_url("https://www.youtube.com/watch?v=abc123")

    def test_youtu_be_allowed(self):
        validate_url("https://youtu.be/abc123")

    def test_non_youtube_rejected(self):
        with pytest.raises(ValueError, match="非法链接"):
            validate_url("https://example.com/video")

    def test_empty_string_rejected(self):
        with pytest.raises(ValueError, match="非法链接"):
            validate_url("")


# ---------------------------------------------------------------------------
# validate_url – playlist blocking
# ---------------------------------------------------------------------------

class TestPlaylistBlocking:
    def test_playlist_only_url_rejected(self):
        """Pure playlist link (list= without v=) should be blocked."""
        with pytest.raises(ValueError, match="不支持播放列表链接"):
            validate_url("https://www.youtube.com/playlist?list=PLxxxxxxx")

    def test_watch_with_list_but_no_v_rejected(self):
        """/watch?list=... (no v=) should also be blocked."""
        with pytest.raises(ValueError, match="不支持播放列表链接"):
            validate_url("https://www.youtube.com/watch?list=PLxxxxxxx")

    def test_video_with_list_param_allowed(self):
        """A single video that happens to sit inside a playlist should pass."""
        validate_url("https://www.youtube.com/watch?v=abc123&list=PLxxxxxxx")

    def test_video_without_list_allowed(self):
        """Normal video URL with no list param — always allowed."""
        validate_url("https://www.youtube.com/watch?v=abc123")


# ---------------------------------------------------------------------------
# extract_url_id
# ---------------------------------------------------------------------------

class TestExtractUrlId:
    def test_standard_watch_url(self):
        assert extract_url_id("https://www.youtube.com/watch?v=abc123") == "watch?v=abc123"

    def test_youtu_be_short_url(self):
        assert extract_url_id("https://youtu.be/abc123") == "abc123"

    def test_url_with_list_and_v(self):
        url = "https://www.youtube.com/watch?v=abc123&list=PLxxxxxxx"
        assert extract_url_id(url) == "watch?v=abc123&list=PLxxxxxxx"

    def test_strips_hostname(self):
        url_id = extract_url_id("https://www.youtube.com/watch?v=abc123")
        assert "youtube.com" not in url_id


# ---------------------------------------------------------------------------
# Duplicate detection
# ---------------------------------------------------------------------------

class TestDuplicateDetection:
    """Tests for is_duplicate / record_download."""

    def setup_method(self):
        """Clear the seen-set before each test."""
        _seen.clear()

    def test_first_request_is_not_duplicate(self):
        url = "https://www.youtube.com/watch?v=abc123"
        assert is_duplicate(url) is False

    def test_same_url_same_day_is_duplicate(self):
        url = "https://www.youtube.com/watch?v=abc123"
        record_download(url)
        assert is_duplicate(url) is True

    def test_different_urls_same_day_not_duplicate(self):
        record_download("https://www.youtube.com/watch?v=abc123")
        assert is_duplicate("https://www.youtube.com/watch?v=xyz789") is False

    def test_same_url_different_day_not_duplicate(self):
        url = "https://www.youtube.com/watch?v=abc123"
        record_download(url)
        with patch("validator._today", return_value="2099-12-31"):
            assert is_duplicate(url) is False


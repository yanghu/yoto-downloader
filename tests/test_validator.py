"""Unit tests for the URL validation / extraction helpers."""

import pytest
from validator import validate_url, extract_url_id


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

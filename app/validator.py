"""URL validation helpers for the download endpoint."""

from datetime import date
from urllib.parse import urlparse, parse_qs

# In-memory set of (date_str, url) pairs seen today.
# Resets on container restart; stale entries from past days are harmless.
_seen: set[tuple[str, str]] = set()

# Accepted YouTube hostnames (www. prefix is stripped before comparison)
_ALLOWED_HOSTS = {"youtube.com", "youtu.be", "m.youtube.com", "music.youtube.com"}


def is_duplicate(url: str) -> bool:
    """Return True if this URL was already accepted today."""
    return (_today(), url) in _seen


def record_download(url: str) -> None:
    """Mark a URL as accepted for today."""
    _seen.add((_today(), url))


def _today() -> str:
    return date.today().isoformat()


def validate_url(url: str) -> None:
    """Validate a download URL.

    Raises ValueError with a user-facing message if the URL is invalid.
    """
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    if host not in _ALLOWED_HOSTS:
        raise ValueError("非法链接")

    qs = parse_qs(parsed.query)
    if "list" in qs and "v" not in qs:
        raise ValueError("不支持播放列表链接")


def extract_url_id(url: str) -> str:
    """Return the path + query portion of a URL (strips the hostname)."""
    parsed = urlparse(url)
    url_id = parsed.path.lstrip("/")
    if parsed.query:
        url_id += f"?{parsed.query}"
    return url_id

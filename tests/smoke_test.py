"""Smoke tests against a live running instance.

These tests replace manual Swagger UI interaction. Run them after starting
the dev stack:

    make dev      # start the local server
    make smoke    # run these tests

The base URL defaults to http://localhost:8000 and can be overridden via the
BASE_URL environment variable.
"""

import os
import pytest
import httpx

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")

# A well-known public video used only for API shape tests (not actually downloaded).
_VALID_YT_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
_VALID_SHORT_URL = "https://youtu.be/dQw4w9WgXcQ"
_INVALID_URL = "https://example.com/video"
_PLAYLIST_ONLY_URL = "https://www.youtube.com/playlist?list=PLtest123"


@pytest.fixture(scope="session")
def client():
    """Synchronous httpx client shared across all smoke tests."""
    with httpx.Client(base_url=BASE_URL, timeout=15) as c:
        yield c


# ---------------------------------------------------------------------------
# Server health
# ---------------------------------------------------------------------------

@pytest.mark.smoke
def test_frontend_serves(client):
    """GET / returns 200 with HTML content."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")


@pytest.mark.smoke
def test_swagger_ui_available(client):
    """GET /docs returns 200 (Swagger UI is up)."""
    resp = client.get("/docs")
    assert resp.status_code == 200


@pytest.mark.smoke
def test_openapi_schema_available(client):
    """GET /openapi.json returns a valid schema dict."""
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    schema = resp.json()
    assert "paths" in schema
    assert "/download" in schema["paths"]


# ---------------------------------------------------------------------------
# Song list
# ---------------------------------------------------------------------------

@pytest.mark.smoke
def test_list_songs_returns_list(client):
    """GET /api/songs returns 200 and a JSON list."""
    resp = client.get("/api/songs")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


# ---------------------------------------------------------------------------
# Download endpoint — request shape / validation
# ---------------------------------------------------------------------------

@pytest.mark.smoke
def test_download_valid_youtube_url(client):
    """POST /download with a standard youtube.com URL → accepted (or already duplicate)."""
    resp = client.post("/download", json={"url": _VALID_YT_URL})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("accepted", "duplicate")
    assert "id" in data
    assert "youtube.com" not in data["id"]  # id must strip the hostname


@pytest.mark.smoke
def test_download_short_url(client):
    """POST /download with a youtu.be short URL → accepted or duplicate."""
    resp = client.post("/download", json={"url": _VALID_SHORT_URL})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("accepted", "duplicate")
    assert data["id"] == "dQw4w9WgXcQ"


@pytest.mark.smoke
def test_download_invalid_domain_rejected(client):
    """POST /download with a non-YouTube URL → 400."""
    resp = client.post("/download", json={"url": _INVALID_URL})
    assert resp.status_code == 400


@pytest.mark.smoke
def test_download_playlist_only_url_rejected(client):
    """POST /download with a playlist-only URL (no video id) → 400."""
    resp = client.post("/download", json={"url": _PLAYLIST_ONLY_URL})
    assert resp.status_code == 400


@pytest.mark.smoke
def test_download_missing_url_field(client):
    """POST /download with no url field → 422 validation error."""
    resp = client.post("/download", json={})
    assert resp.status_code == 422


@pytest.mark.smoke
def test_download_duplicate_detection(client):
    """POST the same unique URL twice in one session → second is 'duplicate'."""
    # Use a URL unlikely to have been submitted before this test run.
    url = "https://youtu.be/smoke_dedup_test_xyz"
    r1 = client.post("/download", json={"url": url})
    assert r1.status_code == 200

    r2 = client.post("/download", json={"url": url})
    assert r2.status_code == 200
    assert r2.json()["status"] == "duplicate"


# ---------------------------------------------------------------------------
# Songs management endpoints
# ---------------------------------------------------------------------------

@pytest.mark.smoke
def test_delete_songs_empty_list_rejected(client):
    """DELETE /api/songs with an empty paths list → 400."""
    resp = client.request("DELETE", "/api/songs", json={"paths": []})
    assert resp.status_code == 400


@pytest.mark.smoke
def test_delete_songs_missing_body(client):
    """DELETE /api/songs with no body → 422 validation error."""
    resp = client.request("DELETE", "/api/songs", json={})
    assert resp.status_code == 422

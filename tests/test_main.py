import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport

# Mock process_download before importing main, so the background task never runs
with patch('downloader.process_download'):
    from main import app

from validator import _seen


@pytest.mark.asyncio
async def test_valid_youtube_url():
    """POST a valid youtube.com URL → 200 with accepted status and correct id."""
    _seen.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/download", json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "accepted"
    assert data["id"] == "watch?v=dQw4w9WgXcQ"


@pytest.mark.asyncio
async def test_valid_youtu_be_url():
    """POST a youtu.be short URL → 200 with just the video ID."""
    _seen.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/download", json={"url": "https://youtu.be/dQw4w9WgXcQ"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "accepted"
    assert data["id"] == "dQw4w9WgXcQ"


@pytest.mark.asyncio
async def test_invalid_url_rejected():
    """POST a non-YouTube URL → 400."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/download", json={"url": "https://example.com/video"})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_id_strips_hostname():
    """The id field should never contain the hostname."""
    _seen.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/download", json={"url": "https://www.youtube.com/watch?v=abc123"})
    data = resp.json()
    assert "youtube.com" not in data["id"]
    assert data["id"] == "watch?v=abc123"


@pytest.mark.asyncio
async def test_background_task_enqueued():
    """Verifies process_download is called with the submitted URL."""
    _seen.clear()
    with patch('main.process_download') as mock_download:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            url = "https://www.youtube.com/watch?v=test123"
            await client.post("/download", json={"url": url})
        mock_download.assert_called_once_with(url)


@pytest.mark.asyncio
async def test_duplicate_url_returns_duplicate_status():
    """POST the same URL twice on the same day → second returns status 'duplicate'."""
    _seen.clear()
    url = "https://www.youtube.com/watch?v=dup_test"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        first = await client.post("/download", json={"url": url})
        second = await client.post("/download", json={"url": url})

    assert first.status_code == 200
    assert first.json()["status"] == "accepted"

    assert second.status_code == 200
    assert second.json()["status"] == "duplicate"


@pytest.mark.asyncio
async def test_get_songs_endpoint():
    """GET /api/songs → 200 and returns a list."""
    with patch('main.list_all_songs', return_value=[
        {"title": "Test", "date": "2026-03-04", "audio_path": "audio/2026-03/04/Test.m4a",
         "cover_path": None, "size_bytes": 1000, "is_duplicate": False}
    ]):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/songs")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["title"] == "Test"


@pytest.mark.asyncio
async def test_delete_songs_endpoint():
    """DELETE /api/songs with valid paths → 200 with results."""
    mock_results = [{"path": "audio/2026-03/04/Test.m4a", "deleted": True, "error": None}]
    with patch('main.delete_files', return_value=mock_results):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.request(
                "DELETE", "/api/songs",
                json={"paths": ["audio/2026-03/04/Test.m4a"]}
            )
    assert resp.status_code == 200
    data = resp.json()
    assert data["results"][0]["deleted"] is True


@pytest.mark.asyncio
async def test_delete_songs_empty_list():
    """DELETE /api/songs with empty paths list → 400."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.request(
            "DELETE", "/api/songs",
            json={"paths": []}
        )
    assert resp.status_code == 400

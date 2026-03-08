import os
import pytest
from PIL import Image

from image import _center_crop, _find_thumbnail, crop_thumbnail_to_square


def _create_test_image(path: str, width: int, height: int, mode: str = "RGB"):
    """Helper to create a test image file."""
    img = Image.new(mode, (width, height), color="red")
    img.save(path)


# ---------------------------------------------------------------------------
# _find_thumbnail
# ---------------------------------------------------------------------------

class TestFindThumbnail:
    def test_finds_webp(self, tmp_path):
        (tmp_path / "track.webp").write_bytes(b"\x00")
        assert _find_thumbnail("track", str(tmp_path)) == str(tmp_path / "track.webp")

    def test_finds_jpg(self, tmp_path):
        (tmp_path / "track.jpg").write_bytes(b"\x00")
        assert _find_thumbnail("track", str(tmp_path)) == str(tmp_path / "track.jpg")

    def test_finds_png(self, tmp_path):
        (tmp_path / "track.png").write_bytes(b"\x00")
        assert _find_thumbnail("track", str(tmp_path)) == str(tmp_path / "track.png")

    def test_prefers_webp_over_jpg(self, tmp_path):
        """webp is listed first in extensions, so it should be preferred."""
        (tmp_path / "track.webp").write_bytes(b"\x00")
        (tmp_path / "track.jpg").write_bytes(b"\x00")
        result = _find_thumbnail("track", str(tmp_path))
        assert result.endswith(".webp")

    def test_returns_none_when_not_found(self, tmp_path):
        assert _find_thumbnail("missing", str(tmp_path)) is None


# ---------------------------------------------------------------------------
# _center_crop
# ---------------------------------------------------------------------------

class TestCenterCrop:
    def test_landscape_becomes_square(self):
        img = Image.new("RGB", (200, 100))
        result = _center_crop(img)
        assert result.size == (100, 100)

    def test_portrait_becomes_square(self):
        img = Image.new("RGB", (100, 200))
        result = _center_crop(img)
        assert result.size == (100, 100)

    def test_already_square_unchanged(self):
        img = Image.new("RGB", (150, 150))
        result = _center_crop(img)
        assert result.size == (150, 150)


# ---------------------------------------------------------------------------
# crop_thumbnail_to_square (public API)
# ---------------------------------------------------------------------------

def test_square_image_is_saved_as_jpeg(tmp_path):
    """A 100x100 PNG is saved as _square.jpg without cropping."""
    _create_test_image(str(tmp_path / "thumb.png"), 100, 100)
    crop_thumbnail_to_square("thumb", str(tmp_path))

    out = tmp_path / "thumb_square.jpg"
    assert out.exists()
    with Image.open(str(out)) as img:
        assert img.size == (100, 100)
        assert img.mode == "RGB"


def test_landscape_image_is_cropped_to_square(tmp_path):
    """A 200x100 landscape image → output is 100x100."""
    _create_test_image(str(tmp_path / "wide.png"), 200, 100)
    crop_thumbnail_to_square("wide", str(tmp_path))

    out = tmp_path / "wide_square.jpg"
    assert out.exists()
    with Image.open(str(out)) as img:
        assert img.size == (100, 100)


def test_portrait_image_is_cropped_to_square(tmp_path):
    """A 100x200 portrait image → output is 100x100."""
    _create_test_image(str(tmp_path / "tall.png"), 100, 200)
    crop_thumbnail_to_square("tall", str(tmp_path))

    out = tmp_path / "tall_square.jpg"
    assert out.exists()
    with Image.open(str(out)) as img:
        assert img.size == (100, 100)


def test_rgba_is_converted_to_rgb(tmp_path):
    """RGBA image is saved without alpha channel error."""
    _create_test_image(str(tmp_path / "alpha.png"), 150, 100, mode="RGBA")
    crop_thumbnail_to_square("alpha", str(tmp_path))

    out = tmp_path / "alpha_square.jpg"
    assert out.exists()
    with Image.open(str(out)) as img:
        assert img.mode == "RGB"


def test_missing_thumbnail_does_not_raise(tmp_path):
    """No file present → function returns gracefully without raising."""
    crop_thumbnail_to_square("nonexistent", str(tmp_path))


def test_webp_thumbnail_is_found_and_cropped(tmp_path):
    """A .webp thumbnail is found via _find_thumbnail and cropped correctly."""
    _create_test_image(str(tmp_path / "track.webp"), 300, 200)
    crop_thumbnail_to_square("track", str(tmp_path))

    out = tmp_path / "track_square.jpg"
    assert out.exists()
    with Image.open(str(out)) as img:
        assert img.size == (200, 200)

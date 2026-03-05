import os
import pytest
from PIL import Image
from image import crop_thumbnail_to_square


def _create_test_image(path: str, width: int, height: int, mode: str = "RGB"):
    """Helper to create a test image file."""
    img = Image.new(mode, (width, height), color="red")
    img.save(path)


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
    # Should not raise any exception
    crop_thumbnail_to_square("nonexistent", str(tmp_path))

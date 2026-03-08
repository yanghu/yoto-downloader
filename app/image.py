"""Thumbnail processing: crop downloaded cover art to a square JPEG."""

import logging
import os

from PIL import Image

logger = logging.getLogger(__name__)

_THUMBNAIL_EXTENSIONS = (".webp", ".jpg", ".jpeg", ".png")


def _find_thumbnail(base_filename: str, cover_dir: str) -> str | None:
    """Return the path to the downloaded thumbnail for *base_filename*, or None."""
    for ext in _THUMBNAIL_EXTENSIONS:
        path = os.path.join(cover_dir, f"{base_filename}{ext}")
        if os.path.exists(path):
            return path
    return None


def _center_crop(img: Image.Image) -> Image.Image:
    """Return a square crop taken from the centre of *img*."""
    width, height = img.size
    size = min(width, height)
    left = (width - size) // 2
    top = (height - size) // 2
    return img.crop((left, top, left + size, top + size))


def crop_thumbnail_to_square(base_filename: str, cover_dir: str) -> None:
    """Locate the thumbnail for *base_filename* and save a square JPEG next to it.

    The square file is written as ``<base_filename>_square.jpg``.
    The original file is left in place.  Logs a warning when no thumbnail is
    found and silently absorbs image-processing errors.
    """
    src = _find_thumbnail(base_filename, cover_dir)
    if src is None:
        logger.warning("Thumbnail not found for: %s", base_filename)
        return

    out_path = os.path.join(cover_dir, f"{base_filename}_square.jpg")

    try:
        with Image.open(src) as img:
            if img.width != img.height:
                img = _center_crop(img)

            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            img.save(out_path, "JPEG", quality=95)
            logger.debug("Saved square thumbnail: %s", out_path)

    except Exception as exc:
        logger.error("Failed to process thumbnail %s: %s", src, exc)

import io
import os

from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image, ImageOps

try:
    import pillow_heif

    pillow_heif.register_heif_opener()
except ImportError:  # pragma: no cover - HEIC support is optional at runtime
    pillow_heif = None

# Formats every browser can show as-is; anything else raster gets converted.
BROWSER_SAFE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}
CONVERT_EXTS = {".heic", ".heif", ".avif", ".tif", ".tiff", ".bmp"}


def normalize_image_upload(upload):
    """Convert formats browsers can't display (notably iPhone/Mac HEIC) to JPEG.

    PNG/JPG/WebP/SVG/GIF pass through untouched. Returns the original upload
    if conversion isn't needed or isn't possible, so a bad file never blocks
    the save with a confusing error.
    """
    if upload is None:
        return upload
    stem, ext = os.path.splitext(upload.name or "")
    ctype = (getattr(upload, "content_type", "") or "").lower()
    needs_convert = ext.lower() in CONVERT_EXTS or ctype in {"image/heic", "image/heif", "image/avif"}
    if not needs_convert or ext.lower() in BROWSER_SAFE_EXTS:
        return upload
    try:
        upload.seek(0)
        img = Image.open(upload)
        img = ImageOps.exif_transpose(img)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=90, optimize=True)
    except Exception:
        upload.seek(0)
        return upload
    buf.seek(0)
    return InMemoryUploadedFile(
        buf, upload.field_name if hasattr(upload, "field_name") else None,
        f"{stem or 'image'}.jpg", "image/jpeg", buf.getbuffer().nbytes, None,
    )

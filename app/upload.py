from __future__ import annotations

import logging
from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from PIL import Image

from app import database as db
from app.models import UploadResponse
from config import settings

logger = logging.getLogger(__name__)

# Guard against decompression bombs
Image.MAX_IMAGE_PIXELS = 25_000_000  # ~25 megapixels

router = APIRouter()

# Simple in-memory rate limiter (IP -> list of timestamps)
_rate_limits: dict[str, list[float]] = {}


def _check_rate_limit(ip: str) -> bool:
    """Returns True if the request is allowed."""
    import time
    now = time.time()
    hour_ago = now - 3600

    if ip not in _rate_limits:
        _rate_limits[ip] = []

    # Clean old entries
    _rate_limits[ip] = [t for t in _rate_limits[ip] if t > hour_ago]

    if len(_rate_limits[ip]) >= settings.rate_limit_per_hour:
        return False

    _rate_limits[ip].append(now)
    return True


def _validate_file(upload: UploadFile) -> None:
    """Validate file type and size."""
    if not upload.filename:
        raise HTTPException(status_code=400, detail="Bestandsnaam ontbreekt")

    ext = upload.filename.rsplit(".", 1)[-1].lower() if "." in upload.filename else ""
    if ext not in settings.allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Ongeldig bestandstype '.{ext}'. Toegestaan: {', '.join(settings.allowed_extensions)}",
        )


@router.post("/upload", response_model=UploadResponse)
async def upload_photos(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    description: str = Form(default=""),
    consent: bool = Form(...),
    honeypot: str = Form(default="", alias="website"),
    files: list[UploadFile] = File(...),
):
    # Honeypot check
    if honeypot:
        # Bots fill this in; humans don't see it
        return UploadResponse(message="Bedankt!", submission_id="ok")

    if not consent:
        raise HTTPException(
            status_code=400,
            detail="Je moet bevestigen dat gefotografeerde personen toestemming hebben gegeven.",
        )

    if not files or len(files) > settings.max_upload_files:
        raise HTTPException(
            status_code=400,
            detail=f"Upload 1-{settings.max_upload_files} foto's.",
        )

    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    if not _check_rate_limit(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Te veel uploads. Probeer het later opnieuw.",
        )

    # Validate all files first
    for f in files:
        _validate_file(f)

    # Create submission
    sid = db.create_submission(
        source="upload",
        submitter_name=name,
        submitter_email=email,
        description=description,
    )

    photos_dir = Path(settings.photos_dir)
    photos_dir.mkdir(parents=True, exist_ok=True)

    for i, f in enumerate(files):
        data = await f.read()

        if len(data) > settings.max_file_size_mb * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail=f"Bestand '{f.filename}' is te groot (max {settings.max_file_size_mb}MB).",
            )

        ext = f".{f.filename.rsplit('.', 1)[-1].lower()}" if f.filename and "." in f.filename else ".jpg"

        photo_id = db.add_photo(
            submission_id=sid,
            original_size=len(data),
            sort_order=i,
        )

        local_path = photos_dir / f"{photo_id}{ext}"
        thumb_path = photos_dir / f"{photo_id}_thumb{ext}"

        _save_and_resize(data, local_path, thumb_path)

        with db.get_connection() as conn:
            conn.execute(
                "UPDATE photos SET local_path = ?, thumbnail_path = ? WHERE id = ?",
                (str(local_path), str(thumb_path), photo_id),
            )

    logger.info("Upload submission %s with %d photos from %s", sid, len(files), name)
    return UploadResponse(
        message="Bedankt! Je foto's verschijnen na goedkeuring.",
        submission_id=sid,
    )


def _save_and_resize(data: bytes, local_path: Path, thumb_path: Path) -> None:
    """Save original (resized if too large), strip EXIF, create thumbnail."""
    img = Image.open(BytesIO(data))

    # Strip EXIF for privacy by copying pixel data to a clean image
    img_clean = Image.new(img.mode, img.size)
    img_clean.paste(img)

    max_dim = settings.max_image_dimension
    if img_clean.width > max_dim or img_clean.height > max_dim:
        img_clean.thumbnail((max_dim, max_dim), Image.LANCZOS)

    img_clean.save(local_path, quality=85, optimize=True)

    thumb = img_clean.copy()
    thumb_dim = settings.thumbnail_dimension
    thumb.thumbnail((thumb_dim, thumb_dim), Image.LANCZOS)
    thumb.save(thumb_path, quality=80, optimize=True)

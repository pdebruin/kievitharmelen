from __future__ import annotations

import logging
from io import BytesIO
from pathlib import Path

import httpx
from PIL import Image

from app import database as db
from config import settings

logger = logging.getLogger(__name__)

# Guard against decompression bombs
Image.MAX_IMAGE_PIXELS = 25_000_000  # ~25 megapixels


async def poll_instance(instance: str, base_url: str | None = None) -> int:
    """Poll a single Fediverse instance for new posts with the configured hashtag.

    Returns the number of new submissions found.
    """
    url = base_url or f"https://{instance}"
    endpoint = f"{url}/api/v1/timelines/tag/{settings.hashtag}"

    state = db.get_poller_state(instance)
    params = {"limit": 40}
    if state and state["last_seen_id"]:
        params["since_id"] = state["last_seen_id"]

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(endpoint, params=params)
            resp.raise_for_status()
            posts = resp.json()
    except httpx.HTTPError as e:
        logger.error("Failed to poll %s: %s", instance, e)
        return 0

    if not posts:
        logger.info("No new posts from %s", instance)
        return 0

    new_count = 0
    # Process oldest first so last_seen_id tracks correctly
    for post in reversed(posts):
        post_id = str(post["id"])

        if db.submission_exists_by_source(post_id, instance):
            continue

        media = [a for a in post.get("media_attachments", []) if a["type"] == "image"]
        if not media:
            continue

        account = post.get("account", {})
        # Strip HTML tags from content for plain text description
        content = post.get("content", "")
        import re
        description = re.sub(r"<[^>]+>", "", content).strip()

        sid = db.create_submission(
            source="fediverse",
            source_url=post.get("url"),
            source_id=post_id,
            source_instance=instance,
            author_name=account.get("display_name", ""),
            author_handle=f"@{account.get('acct', '')}",
            author_avatar_url=account.get("avatar"),
            description=description,
            created_at=post.get("created_at"),
        )

        for i, attachment in enumerate(media):
            await _download_and_store(sid, attachment, i)

        new_count += 1
        db.update_poller_state(instance, post_id)

    logger.info("Found %d new submissions from %s", new_count, instance)
    return new_count


async def _download_and_store(
    submission_id: str, attachment: dict, sort_order: int
) -> None:
    """Download an image from a Fediverse media attachment and store locally."""
    image_url = attachment.get("url", "")
    if not image_url:
        return

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(image_url)
            resp.raise_for_status()
            data = resp.content
    except httpx.HTTPError as e:
        logger.error("Failed to download %s: %s", image_url, e)
        return

    photos_dir = Path(settings.photos_dir)
    photos_dir.mkdir(parents=True, exist_ok=True)

    # Determine extension from content type or URL
    ext = _guess_extension(resp.headers.get("content-type", ""), image_url)

    photo_id = db.add_photo(
        submission_id=submission_id,
        original_url=image_url,
        alt_text=attachment.get("description", ""),
        width=attachment.get("meta", {}).get("original", {}).get("width"),
        height=attachment.get("meta", {}).get("original", {}).get("height"),
        original_size=len(data),
        sort_order=sort_order,
    )

    # Save and process image
    local_path = photos_dir / f"{photo_id}{ext}"
    thumb_path = photos_dir / f"{photo_id}_thumb{ext}"

    _save_and_resize(data, local_path, thumb_path)

    # Update DB with paths
    with db.get_connection() as conn:
        conn.execute(
            "UPDATE photos SET local_path = ?, thumbnail_path = ? WHERE id = ?",
            (str(local_path), str(thumb_path), photo_id),
        )


def _guess_extension(content_type: str, url: str) -> str:
    ct_map = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }
    if content_type in ct_map:
        return ct_map[content_type]
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        if ext in url.lower():
            return ext
    return ".jpg"


def _save_and_resize(data: bytes, local_path: Path, thumb_path: Path) -> None:
    """Save original (resized if too large) and create thumbnail."""
    img = Image.open(BytesIO(data))

    # Strip EXIF for privacy by copying pixel data to a clean image
    img_clean = Image.new(img.mode, img.size)
    img_clean.paste(img)

    # Resize if larger than max dimension
    max_dim = settings.max_image_dimension
    if img_clean.width > max_dim or img_clean.height > max_dim:
        img_clean.thumbnail((max_dim, max_dim), Image.LANCZOS)

    img_clean.save(local_path, quality=85, optimize=True)

    # Create thumbnail
    thumb = img_clean.copy()
    thumb_dim = settings.thumbnail_dimension
    thumb.thumbnail((thumb_dim, thumb_dim), Image.LANCZOS)
    thumb.save(thumb_path, quality=80, optimize=True)


async def poll_all_instances() -> int:
    """Poll all configured instances. Returns total new submissions."""
    total = 0
    for instance in settings.fedi_instances:
        count = await poll_instance(instance)
        total += count
    return total

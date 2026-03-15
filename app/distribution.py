from __future__ import annotations

import logging

import httpx
from feedgen.feed import FeedGenerator

from app import database as db
from config import settings

logger = logging.getLogger(__name__)


def generate_rss_feed() -> str:
    """Generate an RSS/Atom feed of approved photos."""
    fg = FeedGenerator()
    fg.title("De Kievit Harmelen — Foto's")
    fg.link(href=f"{settings.base_url}/gallery", rel="alternate")
    fg.link(href=f"{settings.base_url}/feed", rel="self")
    fg.description("Nieuwste foto's van Stichting de Kievit Harmelen")
    fg.language("nl")

    photos = db.list_approved_photos(limit=20)
    for photo in photos:
        fe = fg.add_entry()
        fe.id(f"{settings.base_url}/api/photos/{photo['id']}")
        fe.title(photo.get("description") or "Foto van De Kievit")
        fe.link(href=f"{settings.base_url}/gallery#{photo['id']}")

        # Add image as enclosure
        if photo.get("local_path"):
            fe.enclosure(
                url=f"{settings.base_url}/photos/{photo['local_path'].split('/')[-1]}",
                type="image/jpeg",
            )

        # Attribution
        author = photo.get("author_name") or photo.get("author_handle") or "Community"
        fe.author(name=author)

        if photo.get("submission_date"):
            fe.published(photo["submission_date"])

        if photo.get("source_url"):
            fe.link(href=photo["source_url"], rel="via")

    return fg.rss_str(pretty=True).decode("utf-8")


async def autopost_to_fediverse(submission_id: str) -> bool:
    """Post an approved submission to De Kievit's own Fediverse account."""
    if not settings.fedi_autopost_enabled:
        return False

    submission = db.get_submission(submission_id)
    if not submission or submission["status"] != "approved":
        return False

    photos = db.get_photos_for_submission(submission_id)
    if not photos:
        return False

    instance_url = f"https://{settings.fedi_autopost_instance}"

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            headers = {"Authorization": f"Bearer {settings.fedi_autopost_token}"}

            # Upload media attachments
            media_ids = []
            for photo in photos:
                if not photo.get("local_path"):
                    continue
                with open(photo["local_path"], "rb") as f:
                    resp = await client.post(
                        f"{instance_url}/api/v2/media",
                        headers=headers,
                        files={"file": ("photo.jpg", f, "image/jpeg")},
                        data={"description": photo.get("alt_text", "")},
                    )
                    resp.raise_for_status()
                    media_ids.append(resp.json()["id"])

            # Create post
            description = submission.get("description", "")
            author = submission.get("author_name") or submission.get("author_handle") or ""
            attribution = f" (📸 {author})" if author else ""

            status_text = f"{description}{attribution}\n\n#{settings.hashtag}"

            resp = await client.post(
                f"{instance_url}/api/v1/statuses",
                headers=headers,
                json={
                    "status": status_text,
                    "media_ids": media_ids,
                    "visibility": "public",
                },
            )
            resp.raise_for_status()

    except httpx.HTTPError as e:
        logger.error("Failed to auto-post to Fediverse: %s", e)
        return False

    logger.info("Auto-posted submission %s to %s", submission_id, settings.fedi_autopost_instance)
    return True

"""Mock Mastodon API server for testing.

Mimics the endpoints our poller uses:
- POST /api/v1/media    — upload media
- POST /api/v1/statuses — create a post
- GET  /api/v1/timelines/tag/{hashtag} — list posts by hashtag

Run standalone: python -m tests.mock_fedi_server
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse

app = FastAPI(title="Mock Fediverse Server")

# In-memory storage
_media: dict[str, dict] = {}
_statuses: list[dict] = []
_media_dir = Path("tests/mock_media")


@app.on_event("startup")
def startup():
    _media_dir.mkdir(parents=True, exist_ok=True)


@app.post("/api/v1/media")
async def upload_media(
    file: UploadFile = File(...),
    description: str = Form(default=""),
):
    media_id = uuid.uuid4().hex[:12]
    ext = Path(file.filename).suffix if file.filename else ".jpg"
    local_path = _media_dir / f"{media_id}{ext}"

    data = await file.read()
    local_path.write_bytes(data)

    media_obj = {
        "id": media_id,
        "type": "image",
        "url": f"http://localhost:9999/mock_media/{media_id}{ext}",
        "preview_url": f"http://localhost:9999/mock_media/{media_id}{ext}",
        "description": description,
        "meta": {
            "original": {
                "width": 800,
                "height": 600,
            }
        },
    }
    _media[media_id] = media_obj
    return media_obj


@app.post("/api/v1/statuses")
async def create_status(
    status: str = Form(default=""),
    media_ids: list[str] = Form(default=[]),
    visibility: str = Form(default="public"),
):
    status_id = uuid.uuid4().hex[:12]
    now = datetime.now(timezone.utc).isoformat()

    # Resolve media attachments
    attachments = [_media[mid] for mid in media_ids if mid in _media]

    # Parse author from form or use default
    account = {
        "id": "testuser1",
        "username": "testnaturist",
        "acct": "testnaturist@localhost",
        "display_name": "Test Natuurfotograaf",
        "avatar": "https://example.com/avatar.png",
    }

    status_obj = {
        "id": status_id,
        "created_at": now,
        "content": f"<p>{status}</p>",
        "url": f"http://localhost:9999/@testnaturist/{status_id}",
        "account": account,
        "media_attachments": attachments,
        "tags": _extract_tags(status),
        "visibility": visibility,
    }
    _statuses.append(status_obj)
    return status_obj


@app.get("/api/v1/timelines/tag/{hashtag}")
async def timeline_tag(
    hashtag: str,
    since_id: str | None = None,
    limit: int = 40,
):
    # Filter statuses that contain the hashtag
    matching = [
        s for s in _statuses
        if any(t["name"].lower() == hashtag.lower() for t in s.get("tags", []))
    ]

    # Filter by since_id if provided
    if since_id:
        try:
            idx = next(i for i, s in enumerate(matching) if s["id"] == since_id)
            matching = matching[idx + 1:]
        except StopIteration:
            pass

    # Return newest first (like real Mastodon)
    matching = list(reversed(matching[-limit:]))
    return matching


@app.get("/mock_media/{filename}")
async def serve_media(filename: str):
    path = _media_dir / filename
    if not path.exists():
        return {"error": "not found"}
    return FileResponse(path)


@app.post("/reset")
async def reset():
    """Reset all data (for test isolation)."""
    _media.clear()
    _statuses.clear()
    # Clean media files
    for f in _media_dir.glob("*"):
        f.unlink()
    return {"message": "reset"}


def _extract_tags(text: str) -> list[dict]:
    import re
    tags = re.findall(r"#(\w+)", text)
    return [{"name": tag, "url": f"http://localhost:9999/tags/{tag}"} for tag in tags]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9999)

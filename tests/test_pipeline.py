"""Full end-to-end pipeline test: Fedi post → poller → queue → approve → gallery + RSS."""
from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from app import database as db
from app.poller import poll_instance
from tests.fedi_client import FediTestClient


@pytest.mark.anyio
async def test_full_pipeline(mock_fedi_server, app_client, sample_image_path, admin_headers):
    """Full flow: Fedi post → poller → moderation queue → approve → gallery + API + RSS."""
    db.init_db()

    # 1. Post photo to Fediverse
    fedi = FediTestClient(mock_fedi_server)
    fedi.post_photo(
        image_path=sample_image_path,
        description="Bijendag 2026 was een succes! #DeKievitHarmelen",
        alt_text="Kinderen bekijken de bijenkasten",
    )

    # 2. Poller picks it up
    count = await poll_instance("localhost:9999", base_url=mock_fedi_server)
    assert count == 1

    # 3. Submission is pending in the queue
    pending = db.list_submissions(status="pending")
    assert len(pending) == 1
    sid = pending[0]["id"]

    # 4. Admin sees it in the queue
    resp = app_client.get("/api/submissions", headers=admin_headers)
    assert resp.status_code == 200
    assert any(s["id"] == sid for s in resp.json()["submissions"])

    # 5. Admin approves
    resp = app_client.post(
        f"/api/submissions/{sid}/moderate",
        json={"status": "approved"},
        headers=admin_headers,
    )
    assert resp.status_code == 200

    # 6. Photo appears in gallery API
    resp = app_client.get("/api/photos")
    photos = resp.json()["photos"]
    assert len(photos) >= 1
    assert any("bijendag" in (p.get("description") or "").lower() for p in photos)

    # 7. Photo appears in RSS feed
    resp = app_client.get("/feed")
    root = ET.fromstring(resp.text)
    items = root.findall(".//item")
    assert len(items) >= 1

    # 8. Gallery page renders
    resp = app_client.get("/gallery")
    assert resp.status_code == 200
    assert "bijendag" in resp.text.lower() or "Foto" in resp.text

    fedi.reset()

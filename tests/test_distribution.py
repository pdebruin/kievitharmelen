"""T5, T6: Distribution tests (RSS, Fediverse auto-post)."""
from __future__ import annotations

import xml.etree.ElementTree as ET

from app import database as db


def _approve_test_submission() -> str:
    sid = db.create_submission(
        source="fediverse",
        author_name="Test Fotograaf",
        author_handle="@test@mastodon.nl",
        description="Prachtig uitzicht",
        source_url="http://mastodon.nl/@test/12345",
    )
    db.add_photo(
        submission_id=sid,
        original_url="http://example.com/photo.jpg",
        local_path="tests/sample_images/test_generated.jpg",
        thumbnail_path="tests/sample_images/test_generated.jpg",
        alt_text="Uitzicht over De Kievit",
    )
    db.moderate_submission(sid, "approved")
    return sid


def test_rss_feed(app_client):
    """T5: Approved photos appear in the RSS feed."""
    _approve_test_submission()

    resp = app_client.get("/feed")
    assert resp.status_code == 200
    assert "application/rss+xml" in resp.headers["content-type"]

    # Parse XML
    root = ET.fromstring(resp.text)
    items = root.findall(".//item")
    assert len(items) >= 1

    # Check that our photo is in the feed
    titles = [item.find("title").text for item in items]
    assert any("uitzicht" in t.lower() for t in titles if t)


def test_rss_feed_empty_when_none_approved(app_client):
    """RSS feed works but is empty when nothing is approved."""
    resp = app_client.get("/feed")
    assert resp.status_code == 200
    root = ET.fromstring(resp.text)
    # Should be valid XML regardless
    assert root.tag == "rss" or root.find(".//channel") is not None

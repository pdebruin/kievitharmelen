"""T1, T7: Fediverse poller tests."""
from __future__ import annotations

import pytest

from app import database as db
from app.poller import poll_instance
from tests.fedi_client import FediTestClient


@pytest.mark.anyio
async def test_fedi_post_appears_in_queue(mock_fedi_server, app_client, sample_image_path):
    """T1: A Fediverse post with the hashtag lands in the moderation queue."""
    db.init_db()

    # Post a photo to the mock server
    fedi = FediTestClient(mock_fedi_server)
    fedi.post_photo(
        image_path=sample_image_path,
        description="Prachtige dag bij de bijen! #DeKievitHarmelen",
    )

    # Run the poller against the mock server
    count = await poll_instance("localhost:9999", base_url=mock_fedi_server)
    assert count == 1

    # Check moderation queue
    submissions = db.list_submissions(status="pending")
    assert len(submissions) == 1

    sub = submissions[0]
    assert sub["source"] == "fediverse"
    assert "bijen" in sub["description"].lower()

    # Check photos were downloaded
    photos = db.get_photos_for_submission(sub["id"])
    assert len(photos) == 1
    assert photos[0]["local_path"] is not None

    from pathlib import Path
    assert Path(photos[0]["local_path"]).exists()

    # Clean up mock server
    fedi.reset()


@pytest.mark.anyio
async def test_duplicate_prevention(mock_fedi_server, app_client, sample_image_path):
    """T7: Same post polled twice → only stored once."""
    db.init_db()

    fedi = FediTestClient(mock_fedi_server)
    fedi.post_photo(
        image_path=sample_image_path,
        description="Herfstfoto #DeKievitHarmelen",
    )

    # Poll twice
    await poll_instance("localhost:9999", base_url=mock_fedi_server)
    await poll_instance("localhost:9999", base_url=mock_fedi_server)

    submissions = db.list_submissions()
    assert len(submissions) == 1

    fedi.reset()

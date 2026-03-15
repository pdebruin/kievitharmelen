"""T3, T4: Moderation queue tests."""
from __future__ import annotations

from app import database as db


def _create_test_submission() -> str:
    """Helper: create a pending submission with a photo."""
    sid = db.create_submission(
        source="upload",
        submitter_name="Test User",
        submitter_email="test@test.nl",
        description="Test submission",
    )
    db.add_photo(
        submission_id=sid,
        local_path="tests/sample_images/test_generated.jpg",
        thumbnail_path="tests/sample_images/test_generated.jpg",
    )
    return sid


def test_approve_shows_in_gallery(app_client, admin_headers):
    """T3: Approving a submission makes the photo visible."""
    sid = _create_test_submission()

    # Approve
    resp = app_client.post(
        f"/api/submissions/{sid}/moderate",
        json={"status": "approved"},
        headers=admin_headers,
    )
    assert resp.status_code == 200

    # Check API
    resp = app_client.get("/api/photos")
    assert resp.status_code == 200
    photos = resp.json()["photos"]
    assert any(p["submission_id"] == sid for p in photos)

    # Check gallery page
    resp = app_client.get("/gallery")
    assert resp.status_code == 200


def test_reject_not_in_gallery(app_client, admin_headers):
    """T4: Rejecting a submission keeps it out of the gallery."""
    sid = _create_test_submission()

    # Reject
    resp = app_client.post(
        f"/api/submissions/{sid}/moderate",
        json={"status": "rejected"},
        headers=admin_headers,
    )
    assert resp.status_code == 200

    # Check API
    resp = app_client.get("/api/photos")
    photos = resp.json()["photos"]
    assert not any(p["submission_id"] == sid for p in photos)


def test_admin_requires_auth(app_client):
    """Admin endpoints require authentication."""
    resp = app_client.get(
        "/api/submissions",
        headers={"Authorization": "Bearer wrong-token"},
    )
    assert resp.status_code == 401

"""T2, T8, T9, T10, T11: Upload form tests."""
from __future__ import annotations

from pathlib import Path

from app import database as db


def test_upload_appears_in_queue(app_client, sample_image_path, admin_headers):
    """T2: A photo uploaded via the form lands in the moderation queue."""
    from app.upload import _rate_limits
    _rate_limits.clear()

    with open(sample_image_path, "rb") as f:
        resp = app_client.post(
            "/upload",
            data={
                "name": "Jan de Vries",
                "email": "jan@voorbeeld.nl",
                "description": "Mooie lente bij De Kievit",
                "consent": "true",
            },
            files={"files": ("foto.jpg", f, "image/jpeg")},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert "Bedankt" in data["message"]

    # Check queue
    submissions = db.list_submissions(status="pending")
    assert len(submissions) >= 1
    latest = submissions[0]
    assert latest["source"] == "upload"
    assert latest["submitter_name"] == "Jan de Vries"

    photos = db.get_photos_for_submission(latest["id"])
    assert len(photos) == 1


def test_rate_limiting(app_client, sample_image_path):
    """T8: Rapid uploads are rate-limited."""
    # Reset rate limiter
    from app.upload import _rate_limits
    _rate_limits.clear()

    statuses = []
    for i in range(4):  # rate_limit_per_hour is 3 in test settings
        with open(sample_image_path, "rb") as f:
            resp = app_client.post(
                "/upload",
                data={
                    "name": f"Test {i}",
                    "email": f"test{i}@example.com",
                    "consent": "true",
                },
                files={"files": (f"foto{i}.jpg", f, "image/jpeg")},
            )
        statuses.append(resp.status_code)

    # First 3 should succeed, 4th should be rate-limited
    assert statuses[:3] == [200, 200, 200]
    assert statuses[3] == 429


def test_image_processing(app_client, admin_headers):
    """T9: Large images are resized; originals are preserved."""
    from app.upload import _rate_limits
    _rate_limits.clear()

    from PIL import Image
    import io

    # Create a large test image
    img = Image.new("RGB", (4000, 3000), color=(50, 120, 50))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    buf.seek(0)

    resp = app_client.post(
        "/upload",
        data={
            "name": "Fotograaf",
            "email": "foto@test.nl",
            "consent": "true",
        },
        files={"files": ("groot.jpg", buf, "image/jpeg")},
    )
    assert resp.status_code == 200

    # Check that the stored image was resized
    submissions = db.list_submissions(status="pending")
    photos = db.get_photos_for_submission(submissions[0]["id"])
    local_path = photos[0]["local_path"]
    thumb_path = photos[0]["thumbnail_path"]

    assert local_path is not None
    assert thumb_path is not None

    stored = Image.open(local_path)
    assert stored.width <= 2048 and stored.height <= 2048

    thumb = Image.open(thumb_path)
    assert thumb.width <= 400 and thumb.height <= 400


def test_invalid_file_type(app_client):
    """T10: Invalid file types are rejected."""
    from app.upload import _rate_limits
    _rate_limits.clear()

    resp = app_client.post(
        "/upload",
        data={
            "name": "Hacker",
            "email": "hack@test.nl",
            "consent": "true",
        },
        files={"files": ("virus.exe", b"malicious content", "application/octet-stream")},
    )
    assert resp.status_code == 400
    assert "Ongeldig bestandstype" in resp.json()["detail"]


def test_consent_required(app_client, sample_image_path):
    """T11: Uploads without consent are rejected."""
    from app.upload import _rate_limits
    _rate_limits.clear()

    with open(sample_image_path, "rb") as f:
        resp = app_client.post(
            "/upload",
            data={
                "name": "Jan",
                "email": "jan@test.nl",
                # consent omitted
            },
            files={"files": ("foto.jpg", f, "image/jpeg")},
        )
    assert resp.status_code == 422 or resp.status_code == 400

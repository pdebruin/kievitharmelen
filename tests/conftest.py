"""Pytest fixtures for the De Kievit PoC tests."""
from __future__ import annotations

import multiprocessing
import time
from pathlib import Path

import httpx
import pytest
import uvicorn
from fastapi.testclient import TestClient

from config import settings


@pytest.fixture(scope="session", autouse=True)
def _setup_settings():
    """Use a test database and photo dir."""
    settings.database_path = "test_kievit.db"
    settings.photos_dir = "test_photos"
    settings.admin_token = "test-token"
    settings.poll_interval_minutes = 9999  # don't auto-poll during tests
    settings.fedi_instances = ["localhost:9999"]
    settings.rate_limit_per_hour = 3


def _run_mock_server():
    from tests.mock_fedi_server import app
    uvicorn.run(app, host="127.0.0.1", port=9999, log_level="warning")


@pytest.fixture(scope="session")
def mock_fedi_server():
    """Start the mock Fediverse server in a background process."""
    proc = multiprocessing.Process(target=_run_mock_server, daemon=True)
    proc.start()
    # Wait for server to be ready
    for _ in range(30):
        try:
            httpx.get("http://localhost:9999/docs", timeout=1)
            break
        except httpx.ConnectError:
            time.sleep(0.2)
    yield "http://localhost:9999"
    proc.terminate()
    proc.join(timeout=5)


@pytest.fixture()
def app_client():
    """FastAPI test client (no actual HTTP server needed)."""
    # Re-import to pick up test settings
    from app.database import init_db
    from app.main import app

    init_db()
    with TestClient(app) as client:
        yield client

    # Cleanup test DB and photos
    db_path = Path(settings.database_path)
    if db_path.exists():
        db_path.unlink()
    photos_path = Path(settings.photos_dir)
    if photos_path.exists():
        import shutil
        shutil.rmtree(photos_path)


@pytest.fixture()
def admin_headers():
    return {"Authorization": f"Bearer {settings.admin_token}"}


@pytest.fixture()
def sample_image_path():
    """Create a minimal test image if no sample images exist."""
    sample_dir = Path("tests/sample_images")
    sample_dir.mkdir(parents=True, exist_ok=True)

    # Check for real sample images first
    for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
        images = list(sample_dir.glob(ext))
        if images:
            return images[0]

    # Generate a minimal test image
    from PIL import Image
    img_path = sample_dir / "test_generated.jpg"
    img = Image.new("RGB", (800, 600), color=(100, 160, 100))
    img.save(img_path, quality=85)
    return img_path

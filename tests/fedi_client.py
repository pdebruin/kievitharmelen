"""Test client for posting to the mock Fediverse server."""
from __future__ import annotations

from pathlib import Path

import httpx


class FediTestClient:
    def __init__(self, base_url: str = "http://localhost:9999"):
        self.base_url = base_url

    def post_photo(
        self,
        image_path: str | Path,
        description: str = "Mooie dag bij De Kievit! #DeKievitHarmelen",
        alt_text: str = "",
    ) -> dict:
        """Post a photo with a hashtag, simulating a Fediverse user.

        Returns the created status object.
        """
        image_path = Path(image_path)
        with httpx.Client(timeout=30) as client:
            # 1. Upload media
            with open(image_path, "rb") as f:
                resp = client.post(
                    f"{self.base_url}/api/v1/media",
                    files={"file": (image_path.name, f, "image/jpeg")},
                    data={"description": alt_text or f"Foto: {image_path.stem}"},
                )
                resp.raise_for_status()
                media = resp.json()

            # 2. Create status with media
            resp = client.post(
                f"{self.base_url}/api/v1/statuses",
                data={
                    "status": description,
                    "media_ids": [media["id"]],
                    "visibility": "public",
                },
            )
            resp.raise_for_status()
            return resp.json()

    def post_multiple_photos(
        self,
        image_paths: list[str | Path],
        description: str = "Vandaag bij De Kievit 🌿 #DeKievitHarmelen",
    ) -> dict:
        """Post multiple photos in a single status."""
        with httpx.Client(timeout=30) as client:
            media_ids = []
            for path in image_paths:
                path = Path(path)
                with open(path, "rb") as f:
                    resp = client.post(
                        f"{self.base_url}/api/v1/media",
                        files={"file": (path.name, f, "image/jpeg")},
                        data={"description": f"Foto: {path.stem}"},
                    )
                    resp.raise_for_status()
                    media_ids.append(resp.json()["id"])

            resp = client.post(
                f"{self.base_url}/api/v1/statuses",
                data={
                    "status": description,
                    "media_ids": media_ids,
                    "visibility": "public",
                },
            )
            resp.raise_for_status()
            return resp.json()

    def reset(self) -> None:
        """Clear all data on the mock server."""
        with httpx.Client(timeout=10) as client:
            client.post(f"{self.base_url}/reset")

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Hashtag to monitor (without #)
    hashtag: str = "DeKievitHarmelen"

    # Fediverse instances to poll
    fedi_instances: list[str] = [
        "mastodon.social",
        "mastodon.nl",
        "pixelfed.social",
    ]

    # Polling interval in minutes
    poll_interval_minutes: int = 15

    # Database path
    database_path: str = "kievit.db"

    # Photo storage directory
    photos_dir: str = "photos"

    # Upload limits
    max_upload_files: int = 10
    max_file_size_mb: int = 15
    allowed_extensions: set[str] = {"jpg", "jpeg", "png", "webp"}

    # Rate limiting: max submissions per IP per hour
    rate_limit_per_hour: int = 5

    # Image processing
    max_image_dimension: int = 2048  # resize larger images to fit
    thumbnail_dimension: int = 400

    # Admin auth (simple token for PoC)
    admin_token: str = "changeme-kievit-admin"

    # Fediverse auto-post (De Kievit's own account)
    fedi_autopost_enabled: bool = False
    fedi_autopost_instance: str = ""
    fedi_autopost_token: str = ""

    # Base URL for links in RSS feed etc.
    base_url: str = "http://localhost:8000"

    model_config = {"env_prefix": "KIEVIT_"}


settings = Settings()

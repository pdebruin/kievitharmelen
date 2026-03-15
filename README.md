# De Kievit Harmelen — Foto PoC

Community-driven photo sharing for Stichting de Kievit Harmelen. Collects photos from the Fediverse (Mastodon/Pixelfed) and website uploads, moderates them, and publishes to an open gallery with RSS and Fediverse distribution.

## Quick Start

### 1. Install dependencies

Requires **Python 3.11+**. Uses [uv](https://docs.astral.sh/uv/) for fast installs (or pip).

```bash
# With uv (recommended)
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Or with pip
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Run the app

```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```

Then open:
- **http://localhost:8000/** — Public photo gallery
- **http://localhost:8000/upload** — Photo upload form
- **http://localhost:8000/admin** — Moderation queue (admin token: `changeme-kievit-admin`)
- **http://localhost:8000/feed** — RSS feed
- **http://localhost:8000/docs** — Swagger API docs

### 3. Run the tests

```bash
source .venv/bin/activate
pytest tests/ -v
```

This will:
- Start a mock Fediverse server on port 9999
- Run all tests (upload, poller, moderation, distribution, full pipeline)
- Clean up test data automatically

## How It Works

```
[Mastodon/Pixelfed]                    [Website Upload Form]
  Post with #DeKievitHarmelen            "Deel je foto's"
        |                                       |
        v                                       v
   [Fedi Poller]                          [Upload Handler]
   polls every 15 min                     validates + resizes
        |                                       |
        +---------------+---------------------+
                        |
                        v
               [Moderation Queue]
               admin approves/rejects
                        |
            +-----------+-----------+
            |           |           |
            v           v           v
        [Gallery]   [RSS Feed]  [Fedi Auto-post]
        /gallery      /feed     (optional)
```

## Project Structure

```
kievitharmelen/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── api.py               # JSON API endpoints
│   ├── auth.py              # Simple admin auth
│   ├── database.py          # SQLite schema + queries
│   ├── distribution.py      # RSS feed + Fedi auto-post
│   ├── models.py            # Pydantic response models
│   ├── poller.py            # Fediverse hashtag poller
│   ├── upload.py            # Photo upload form handler
│   ├── templates/           # Jinja2 HTML templates
│   └── static/              # CSS
├── tests/
│   ├── mock_fedi_server.py  # Mock Mastodon API
│   ├── fedi_client.py       # Test client for mock server
│   ├── sample_images/       # Put test photos here
│   └── test_*.py            # Test files
├── photos/                  # Stored images (gitignored)
├── config.py                # All settings (env vars override)
├── requirements.txt
├── requirements.md          # Project requirements
├── poc-plan.md              # Implementation plan
└── test-plan.md             # Test plan
```

## Configuration

All settings are in `config.py` and can be overridden with environment variables prefixed with `KIEVIT_`:

```bash
# Change the admin token
export KIEVIT_ADMIN_TOKEN="my-secret-token"

# Set Fedi instances to poll
export KIEVIT_FEDI_INSTANCES='["mastodon.nl","pixelfed.social"]'

# Change poll interval
export KIEVIT_POLL_INTERVAL_MINUTES=10

# Enable Fedi auto-posting
export KIEVIT_FEDI_AUTOPOST_ENABLED=true
export KIEVIT_FEDI_AUTOPOST_INSTANCE=mastodon.nl
export KIEVIT_FEDI_AUTOPOST_TOKEN=your-access-token
```

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/photos` | No | List approved photos (paginated) |
| GET | `/api/photos/{id}` | No | Single photo detail |
| GET | `/api/submissions` | Admin | List all submissions |
| POST | `/api/submissions/{id}/moderate` | Admin | Approve or reject |
| POST | `/upload` | No | Submit photos via form |
| GET | `/feed` | No | RSS feed of approved photos |
| GET | `/docs` | No | Swagger API documentation |

Admin auth: send `Authorization: Bearer <token>` header.

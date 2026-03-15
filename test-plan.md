# Test Plan: De Kievit Photo PoC

## Overview
Automated test suite for the photo gathering and sharing pipeline. Designed to run without user input using a **mock Fediverse server** and **sample images**.

## Test Infrastructure

### Mock Fediverse Server
A lightweight FastAPI app that mimics the Mastodon API endpoints our poller uses. Runs on `localhost:9999` during tests.

**Endpoints:**
- `POST /api/v1/media` — upload a media attachment (stores locally, returns media ID)
- `POST /api/v1/statuses` — create a post with media and hashtags
- `GET /api/v1/timelines/tag/{hashtag}` — return posts matching the hashtag (same format as real Mastodon)

The mock server stores posts in memory. No database, no persistence — fresh state each test run.

### Test Client
A Python script/module that publishes posts to the mock server, simulating community members posting photos on the Fediverse.

**Usage:**
```python
from tests.fedi_client import FediTestClient

client = FediTestClient("http://localhost:9999")
client.post_photo(
    image_path="tests/sample_images/bijen.jpg",
    description="Mooie dag bij de bijenkas! #DeKievitHarmelen",
    author="@jan@mastodon.nl"
)
```

### Sample Images
Place sample images in `tests/sample_images/`:
- `bijen.jpg` — bee-related activity photo
- `natuur.jpg` — nature/landscape
- `kinderen.png` — children's activity (test different formats)
- `groot.jpg` — large file (~10MB, tests resize)
- `klein.webp` — small file (tests webp support)

These are provided by the project owner — not generated.

---

## Test Scenarios

### T1: Fediverse → Moderation Queue
**Goal:** A Fediverse post with the hashtag is picked up by the poller and lands in the moderation queue.

**Steps:**
1. Start mock Fedi server on localhost:9999
2. Start the PoC app (configured to poll localhost:9999)
3. Test client publishes a post with `#DeKievitHarmelen` and an image to mock server
4. Trigger a poll cycle (or wait for scheduled poll)
5. Assert: submission appears in DB with status='pending' and source='fediverse'
6. Assert: photo record created with local_path pointing to a downloaded file
7. Assert: downloaded image file exists on disk
8. Assert: admin queue page shows the pending submission

### T2: Website Upload → Moderation Queue
**Goal:** A photo uploaded via the website form lands in the moderation queue.

**Steps:**
1. POST to the upload endpoint with a sample image, name, email, consent checkbox
2. Assert: submission appears in DB with status='pending' and source='upload'
3. Assert: photo stored locally, resized version created
4. Assert: admin queue page shows the pending submission

### T3: Approve Submission → Gallery
**Goal:** Approving a submission makes the photo visible in the public gallery and API.

**Steps:**
1. Create a pending submission (via T1 or T2)
2. Approve the submission via admin endpoint
3. Assert: submission status='approved' in DB
4. Assert: `GET /api/photos` includes the approved photo
5. Assert: gallery page renders the photo with attribution
6. Assert: attribution links back to original Fediverse post (if source='fediverse')

### T4: Reject Submission
**Goal:** Rejecting a submission keeps the photo out of the public gallery.

**Steps:**
1. Create a pending submission
2. Reject the submission via admin endpoint
3. Assert: submission status='rejected' in DB
4. Assert: `GET /api/photos` does NOT include the rejected photo
5. Assert: gallery page does NOT show the rejected photo

### T5: Distribution — RSS Feed
**Goal:** Approved photos appear in the RSS/Atom feed.

**Steps:**
1. Approve a submission
2. GET `/feed`
3. Assert: valid RSS/Atom XML
4. Assert: feed contains an entry for the approved photo with title, image URL, and link

### T6: Distribution — Fediverse Auto-Post
**Goal:** Approved photos are automatically posted to De Kievit's own Fediverse account.

**Steps:**
1. Configure the app to auto-post to the mock Fedi server (as De Kievit's account)
2. Approve a submission
3. Assert: a new post appears on the mock Fedi server from De Kievit's account
4. Assert: post includes the photo and attribution to the original submitter

### T7: Duplicate Prevention
**Goal:** The same Fediverse post is not imported twice.

**Steps:**
1. Test client publishes a post to mock server
2. Trigger two poll cycles
3. Assert: only ONE submission in DB for that post
4. Assert: poller_state.last_seen_id is updated after first poll

### T8: Spam / Rate Limiting
**Goal:** Rapid uploads from the same source are rate-limited.

**Steps:**
1. Submit N+1 uploads in quick succession from the same IP (where N is the rate limit)
2. Assert: first N succeed (status 200)
3. Assert: N+1th is rejected (status 429)
4. Assert: rejected upload does NOT appear in moderation queue

### T9: Image Processing
**Goal:** Large images are resized; originals are preserved.

**Steps:**
1. Upload `groot.jpg` (~10MB, high resolution) via the upload form
2. Assert: original stored at full size
3. Assert: a resized/compressed version exists for serving
4. Assert: served image is smaller than original
5. Assert: EXIF data is stripped (privacy)

### T10: File Validation
**Goal:** Invalid file types and oversized files are rejected.

**Steps:**
1. Attempt to upload a `.exe` file → assert: rejected with clear error
2. Attempt to upload a file >15MB → assert: rejected with clear error
3. Attempt to upload a valid `.jpg` → assert: accepted

### T11: GDPR Consent Required
**Goal:** Uploads without consent checkbox are rejected.

**Steps:**
1. Submit upload form without consent checkbox → assert: rejected with clear error message
2. Submit upload form with consent checkbox → assert: accepted

---

## Running Tests

```bash
# Start mock Fedi server (background)
python -m tests.mock_fedi_server &

# Run all tests
pytest tests/ -v

# Run a specific test
pytest tests/test_pipeline.py::test_fedi_to_queue -v

# Cleanup
kill %1  # stop mock server
```

## Test Project Structure

```
tests/
├── conftest.py              # pytest fixtures (app client, mock server, DB setup)
├── mock_fedi_server.py      # mock Mastodon API server
├── fedi_client.py           # test client for posting to mock server
├── sample_images/           # sample photos (provided by project owner)
│   ├── bijen.jpg
│   ├── natuur.jpg
│   ├── kinderen.png
│   ├── groot.jpg
│   └── klein.webp
├── test_fedi_poller.py      # T1, T7
├── test_upload.py           # T2, T8, T9, T10, T11
├── test_moderation.py       # T3, T4
├── test_distribution.py     # T5, T6
└── test_pipeline.py         # full end-to-end (T1→T3→T5→T6 in sequence)
```

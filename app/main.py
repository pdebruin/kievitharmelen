from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import database as db
from app.api import router as api_router
from app.distribution import generate_rss_feed
from app.poller import poll_all_instances
from app.upload import router as upload_router
from config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    Path(settings.photos_dir).mkdir(parents=True, exist_ok=True)

    scheduler.add_job(
        poll_all_instances,
        "interval",
        minutes=settings.poll_interval_minutes,
        id="fedi_poller",
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    logger.info("Poller scheduled every %d minutes", settings.poll_interval_minutes)

    if settings.admin_token == "changeme-kievit-admin":
        logger.warning(
            "⚠️  Using default admin token! Set KIEVIT_ADMIN_TOKEN env var before deploying."
        )

    yield

    scheduler.shutdown()


app = FastAPI(
    title="De Kievit Harmelen — Foto's",
    description="Community-driven foto's van Stichting de Kievit",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        settings.base_url,
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and photos
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
photos_dir = Path(settings.photos_dir)
photos_dir.mkdir(parents=True, exist_ok=True)
app.mount("/photos", StaticFiles(directory=photos_dir), name="photos")

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

# Include API and upload routers
app.include_router(api_router)
app.include_router(upload_router)


# --- HTML pages ---


@app.get("/", response_class=HTMLResponse)
async def gallery_page(request: Request):
    photos = db.list_approved_photos(limit=50)
    return templates.TemplateResponse("gallery.html", {
        "request": request,
        "photos": photos,
        "settings": settings,
    })


@app.get("/gallery", response_class=HTMLResponse)
async def gallery_page_alt(request: Request):
    return await gallery_page(request)


@app.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    return templates.TemplateResponse("upload.html", {
        "request": request,
        "settings": settings,
    })


@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    pending = db.list_submissions(status="pending")
    approved = db.list_submissions(status="approved", limit=20)
    rejected = db.list_submissions(status="rejected", limit=10)
    counts = db.count_submissions()

    # Attach photos to each submission
    for sub_list in [pending, approved, rejected]:
        for s in sub_list:
            s["photos"] = db.get_photos_for_submission(s["id"])

    return templates.TemplateResponse("admin.html", {
        "request": request,
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
        "counts": counts,
        "settings": settings,
    })


@app.get("/feed")
async def rss_feed():
    content = generate_rss_feed()
    return Response(content=content, media_type="application/rss+xml")

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app import database as db
from app.auth import require_admin
from app.models import (
    ModerateRequest,
    PhotoListResponse,
    PhotoOut,
    SubmissionListResponse,
    SubmissionOut,
)

router = APIRouter(prefix="/api")


@router.get("/photos", response_model=PhotoListResponse)
async def list_photos(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    photos = db.list_approved_photos(limit=limit, offset=offset)
    total = db.count_approved_photos()
    return PhotoListResponse(
        photos=[PhotoOut(**p) for p in photos],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/photos/{photo_id}", response_model=PhotoOut)
async def get_photo(photo_id: str):
    # Find the photo and its submission
    from app.database import get_connection
    with get_connection() as conn:
        row = conn.execute(
            """SELECT p.*, s.author_name, s.author_handle, s.source_url,
                      s.source, s.description, s.created_at as submission_date
               FROM photos p
               JOIN submissions s ON p.submission_id = s.id
               WHERE p.id = ? AND s.status = 'approved'""",
            (photo_id,),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Photo not found")
    return PhotoOut(**dict(row))


@router.get("/submissions", response_model=SubmissionListResponse)
async def list_submissions(
    status: str | None = Query(default=None),
    _admin: bool = Depends(require_admin),
):
    submissions = db.list_submissions(status=status)
    counts = db.count_submissions()
    result = []
    for s in submissions:
        photos = db.get_photos_for_submission(s["id"])
        result.append(SubmissionOut(**s, photos=[PhotoOut(**p) for p in photos]))
    return SubmissionListResponse(submissions=result, counts=counts)


@router.get("/submissions/{submission_id}", response_model=SubmissionOut)
async def get_submission(
    submission_id: str,
    _admin: bool = Depends(require_admin),
):
    s = db.get_submission(submission_id)
    if not s:
        raise HTTPException(status_code=404, detail="Submission not found")
    photos = db.get_photos_for_submission(submission_id)
    return SubmissionOut(**s, photos=[PhotoOut(**p) for p in photos])


@router.post("/submissions/{submission_id}/moderate")
async def moderate_submission(
    submission_id: str,
    body: ModerateRequest,
    _admin: bool = Depends(require_admin),
):
    if body.status not in ("approved", "rejected", "pending"):
        raise HTTPException(status_code=400, detail="Status must be 'approved', 'rejected', or 'pending'")
    success = db.moderate_submission(submission_id, body.status)
    if not success:
        raise HTTPException(status_code=404, detail="Submission not found")
    return {"message": f"Submission {body.status}", "id": submission_id}

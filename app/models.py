from __future__ import annotations

from pydantic import BaseModel


class PhotoOut(BaseModel):
    id: str
    submission_id: str
    original_url: str | None = None
    local_path: str | None = None
    thumbnail_path: str | None = None
    alt_text: str | None = None
    width: int | None = None
    height: int | None = None
    # Joined from submission
    author_name: str | None = None
    author_handle: str | None = None
    source_url: str | None = None
    source: str | None = None
    description: str | None = None
    submission_date: str | None = None
    submitter_name: str | None = None


class PhotoListResponse(BaseModel):
    photos: list[PhotoOut]
    total: int
    limit: int
    offset: int


class SubmissionOut(BaseModel):
    id: str
    source: str
    source_url: str | None = None
    source_instance: str | None = None
    author_name: str | None = None
    author_handle: str | None = None
    description: str | None = None
    submitter_name: str | None = None
    created_at: str
    fetched_at: str
    status: str
    moderated_at: str | None = None
    photos: list[PhotoOut] = []


class SubmissionListResponse(BaseModel):
    submissions: list[SubmissionOut]
    counts: dict[str, int]


class ModerateRequest(BaseModel):
    status: str  # 'approved' or 'rejected'


class UploadResponse(BaseModel):
    message: str
    submission_id: str

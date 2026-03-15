from __future__ import annotations

from fastapi import Header, HTTPException

from config import settings


async def require_admin(authorization: str = Header()):
    """Simple token-based auth for admin endpoints.

    Send as: Authorization: Bearer <token>
    """
    expected = f"Bearer {settings.admin_token}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Invalid admin token")
    return True

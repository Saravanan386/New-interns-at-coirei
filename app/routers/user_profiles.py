# app/routers/user_profiles.py
"""
User Profile API
================
URL prefix: /api/users

Endpoints:
  GET /api/users/{user_id}/profile    → Fetch user profile for "View Profile" panel
  GET /api/users/{user_id}/avatar     → Return avatar (placeholder redirect for now)
  GET /api/courses/{course_id}/members → List all students in a course/batch (instructor)
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse

from app.database import get_db
from app.utils.security import get_current_user
from app.models.user import User
from app.models.enrollment import Enrollment
from app.schemas import UserProfileResponse, GroupMemberResponse

router = APIRouter(tags=["User Profile"])


def _make_avatar_url(user_id: int) -> str:
    """Return a deterministic avatar using DiceBear (free, no key needed)."""
    return f"https://api.dicebear.com/7.x/initials/svg?seed={user_id}"


# ── GET /api/users/{user_id}/profile ─────────────────────────────────────────

@router.get("/api/users/{user_id}/profile", response_model=UserProfileResponse)
def get_user_profile(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Fetch user profile for 'View Profile' panel in chat sidebar."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserProfileResponse(
        id=user.id,
        name=user.name,
        role=user.role,
        student_id=user.student_id,
        email=user.email,
        avatar_url=_make_avatar_url(user.id),
    )


# ── GET /api/users/{user_id}/avatar ──────────────────────────────────────────

@router.get("/api/users/{user_id}/avatar")
def get_user_avatar(user_id: int):
    """Redirect to DiceBear avatar for the user (initials-based)."""
    url = _make_avatar_url(user_id)
    return RedirectResponse(url=url)


# ── GET /api/courses/{course_id}/members ─────────────────────────────────────

@router.get("/api/courses/{course_id}/members", response_model=List[GroupMemberResponse])
def get_course_members(
    course_id: int,
    batch_name: Optional[str] = Query(None, description="Filter by batch name"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List all students in a course/batch (for group member panel).
    Instructor-only endpoint.
    """
    if current_user.get("role") not in ("instructor", "admin"):
        raise HTTPException(status_code=403, detail="Instructor access required")

    query = db.query(Enrollment).filter(
        Enrollment.course_id == course_id,
        Enrollment.status == "ongoing"
    )
    if batch_name:
        query = query.filter(Enrollment.batch_name == batch_name)

    enrollments = query.all()

    members = []
    seen_ids = set()
    for e in enrollments:
        if e.user_id in seen_ids:
            continue
        seen_ids.add(e.user_id)
        user = db.query(User).filter(User.id == e.user_id).first()
        if user:
            members.append(GroupMemberResponse(
                user_id=user.id,
                name=user.name,
                role=user.role,
                student_id=user.student_id,
                avatar_url=_make_avatar_url(user.id),
            ))

    return members

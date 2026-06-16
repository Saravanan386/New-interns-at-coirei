# app/routers/announcements.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.utils.security import get_current_user

from app.models.announcements import Announcement
from app.models.classroom import Classroom
from app.models.enrollment import Enrollment

from app.schemas import (
    AnnouncementCreate,
    AnnouncementResponse
)

from app.services.notifications import create_notification


router = APIRouter(
    prefix="/api/instructor/announcements",
    tags=["Announcements"]
)


# =========================
# CREATE ANNOUNCEMENT
# =========================
@router.post("/", response_model=AnnouncementResponse)
def create_announcement(
    payload: AnnouncementCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    if current_user.get("role") != "instructor":
        raise HTTPException(status_code=403, detail="Only instructors can create announcements")

    announcement = Announcement(
        instructor_id=current_user["user_id"],
        course_id=payload.course_id,
        classroom_id=payload.classroom_id,
        topic=payload.topic,
        message=payload.message
    )

    db.add(announcement)
    db.commit()
    db.refresh(announcement)

    return announcement


# =========================
# GET ANNOUNCEMENTS
# =========================
@router.get(
    "/",
    response_model=List[AnnouncementResponse]
)
def get_announcements(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    role = current_user.get("role")

    if role == "instructor":

        announcements = (
            db.query(Announcement)
            .filter(
                Announcement.instructor_id == current_user["user_id"]
            )
            .order_by(
                Announcement.created_at.desc()
            )
            .all()
        )

        return announcements

    enrollments = (
        db.query(Enrollment)
        .filter(
            Enrollment.user_id == current_user["user_id"]
        )
        .all()
    )

    classroom_ids = [e.classroom_id for e in enrollments]

    classrooms = (
        db.query(Classroom)
        .filter(Classroom.id.in_(classroom_ids))
        .all()
    )

    course_ids = [c.course_id for c in classrooms]

    announcements = (
        db.query(Announcement)
        .filter(Announcement.course_id.in_(course_ids))
        .order_by(Announcement.created_at.desc())
        .all()
    )

    return announcements


# =========================
# GET SINGLE ANNOUNCEMENT
# =========================
@router.get("/{announcement_id}", response_model=AnnouncementResponse)
def get_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    announcement = db.query(Announcement).filter(
        Announcement.id == announcement_id
    ).first()

    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")

    return announcement


# =========================
# UPDATE ANNOUNCEMENT
# =========================
@router.put("/{announcement_id}", response_model=AnnouncementResponse)
def update_announcement(
    announcement_id: int,
    payload: AnnouncementCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    announcement = db.query(Announcement).filter(
        Announcement.id == announcement_id
    ).first()

    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")

    if str(announcement.instructor_id) != str(current_user["user_id"]):
         raise HTTPException(status_code=403, detail="Not allowed to update this announcement")
    
    announcement.course_id = payload.course_id
    announcement.classroom_id = payload.classroom_id
    announcement.topic = payload.topic
    announcement.message = payload.message

    db.commit()
    db.refresh(announcement)

    return announcement


# =========================
# DELETE ANNOUNCEMENT
# =========================
@router.delete("/{announcement_id}")
def delete_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    announcement = db.query(Announcement).filter(
        Announcement.id == announcement_id
    ).first()

    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")

    if announcement.instructor_id != current_user["user_id"]:
        raise HTTPException(
            status_code=403,
            detail="Not allowed to delete this announcement"
        )

    db.delete(announcement)
    db.commit()

    return {
        "status": "success",
        "message": "Announcement deleted successfully"
    }
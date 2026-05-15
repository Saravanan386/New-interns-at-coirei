# app/routers/schedule.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.database import get_db
from app.models.schedule import CourseSchedule
from app.models.session import ClassSession
from app.utils.security import get_current_user

router = APIRouter(prefix="/schedule", tags=["Schedule"])

IST = ZoneInfo("Asia/Kolkata")

# Day-name → weekday number (Monday=0 … Sunday=6)
DAY_MAP = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------
class ScheduleEntry(BaseModel):
    day_of_week: str          # "monday", "wednesday", etc.
    session_type: str         # "class" or "doubt_clearing"
    start_time: str           # "09:00"
    end_time: str             # "10:00"
    instructor_name: Optional[str] = None


class SetScheduleRequest(BaseModel):
    course_id: int
    batch_name: str
    entries: List[ScheduleEntry]


# ---------------------------------------------------------------------------
# POST /schedule/set  — instructor sets the weekly timetable
# ---------------------------------------------------------------------------
@router.post("/set")
def set_schedule(
    body: SetScheduleRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "instructor":
        raise HTTPException(status_code=403, detail="Only instructors can set schedules")

    # Validate day names
    for entry in body.entries:
        if entry.day_of_week.lower() not in DAY_MAP:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid day_of_week: '{entry.day_of_week}'. "
                       f"Use: {', '.join(DAY_MAP.keys())}"
            )

    # Delete existing schedule for this course+batch, then re-insert
    db.query(CourseSchedule).filter(
        CourseSchedule.course_id == body.course_id,
        CourseSchedule.batch_name == body.batch_name
    ).delete()

    for entry in body.entries:
        db.add(CourseSchedule(
            course_id=body.course_id,
            batch_name=body.batch_name,
            day_of_week=entry.day_of_week.lower(),
            session_type=entry.session_type,
            start_time=entry.start_time,
            end_time=entry.end_time,
            instructor_name=entry.instructor_name,
        ))

    db.commit()
    return {
        "message": f"Schedule set successfully with {len(body.entries)} entries",
        "course_id": body.course_id,
        "batch_name": body.batch_name,
    }


# ---------------------------------------------------------------------------
# GET /schedule/upcoming  — returns next 3 upcoming scheduled sessions
# ---------------------------------------------------------------------------
@router.get("/upcoming")
def get_upcoming_schedule(
    course_id: int,
    batch_name: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Fetch the stored weekly schedule
    schedule_rows = db.query(CourseSchedule).filter(
        CourseSchedule.course_id == course_id,
        CourseSchedule.batch_name == batch_name
    ).all()

    if not schedule_rows:
        return []

    # Build a lookup: weekday_number → schedule row
    # (supports multiple entries on the same day if needed)
    day_schedule: dict[int, CourseSchedule] = {}
    for row in schedule_rows:
        weekday = DAY_MAP.get(row.day_of_week.lower())
        if weekday is not None:
            day_schedule[weekday] = row

    # Current date & time in IST
    now_ist = datetime.now(IST)
    today = now_ist.date()

    upcoming = []
    check_date = today

    # Walk forward up to 28 days to find 3 upcoming scheduled days
    for _ in range(28):
        weekday = check_date.weekday()   # Monday=0, Sunday=6
        if weekday in day_schedule:
            row = day_schedule[weekday]

            # Parse start_time to see if today's slot is still in the future
            try:
                hour, minute = map(int, row.start_time.split(":"))
                slot_start_ist = datetime(
                    check_date.year, check_date.month, check_date.day,
                    hour, minute,
                    tzinfo=IST
                )
            except Exception:
                slot_start_ist = None

            # Skip if the slot has already started today (treat it as past)
            if check_date == today and slot_start_ist and now_ist >= slot_start_ist:
                check_date += timedelta(days=1)
                continue

            # Check if a live session exists for this date
            live_session = db.query(ClassSession).filter(
                ClassSession.course_id == course_id,
                ClassSession.batch_name == batch_name,
                ClassSession.status == "live"
            ).first()

            # Only attach join_url if the live session's start_time is today
            is_live = False
            join_url = None
            if live_session and live_session.start_time:
                session_date = live_session.start_time.date()
                if session_date == check_date:
                    is_live = True
                    is_instructor = current_user.get("role") == "instructor"
                    join_url = live_session.host_url if is_instructor else live_session.join_url

            upcoming.append({
                "course_id": course_id,
                "batch_name": batch_name,
                "date": str(check_date),
                "day": check_date.strftime("%A"),        # e.g. "Monday"
                "session_type": row.session_type,        # "class" | "doubt_clearing"
                "start_time": row.start_time,
                "end_time": row.end_time,
                "instructor_name": row.instructor_name,
                "is_live": is_live,
                "join_url": join_url,
            })

            if len(upcoming) == 3:
                break

        check_date += timedelta(days=1)

    return upcoming


# ---------------------------------------------------------------------------
# GET /schedule/  — view the current weekly timetable for a course+batch
# ---------------------------------------------------------------------------
@router.get("/")
def get_schedule(
    course_id: int,
    batch_name: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    rows = db.query(CourseSchedule).filter(
        CourseSchedule.course_id == course_id,
        CourseSchedule.batch_name == batch_name
    ).order_by(CourseSchedule.id).all()

    return [
        {
            "id": r.id,
            "day_of_week": r.day_of_week,
            "session_type": r.session_type,
            "start_time": r.start_time,
            "end_time": r.end_time,
            "instructor_name": r.instructor_name,
        }
        for r in rows
    ]

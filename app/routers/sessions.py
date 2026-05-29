# app/routers/sessions.py

import asyncio
import urllib.parse

from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.models.attendance import SessionParticipant
from app.models.enrollment import Enrollment
from app.models.instructor_enrollment import InstructorEnrollment
from app.models.session import ClassSession
from app.models.user import User
from app.services.jitsi_service import create_room
from app.utils.security import get_current_user

IST = ZoneInfo("Asia/Kolkata")

router = APIRouter(prefix="/sessions", tags=["Sessions"])

# ---------------------------------------------------------------------------
# ATTENDANCE SETTINGS
# ---------------------------------------------------------------------------

ATTENDANCE_THRESHOLD_MINUTES = 30
ATTENDANCE_THRESHOLD_SECONDS = ATTENDANCE_THRESHOLD_MINUTES * 60


# ---------------------------------------------------------------------------
# BACKGROUND TASK
# ---------------------------------------------------------------------------

async def auto_mark_attendance(participant_id: int):
    """
    Auto-calculate attendance after threshold time.
    """

    await asyncio.sleep(ATTENDANCE_THRESHOLD_SECONDS)

    db: Session = SessionLocal()

    try:
        record = db.query(SessionParticipant).filter(
            SessionParticipant.id == participant_id
        ).first()

        if not record:
            return

        if record.status == "present":
            return

        now = datetime.now(IST).replace(tzinfo=None)

        # If student still inside class
        if record.leave_time is None and record.join_time:
            duration = (now - record.join_time).total_seconds() / 60
            record.duration_minutes = round(duration, 2)

        db.commit()

        total_duration = db.query(
            func.sum(SessionParticipant.duration_minutes)
        ).filter(
            SessionParticipant.session_id == record.session_id,
            SessionParticipant.user_id == record.user_id
        ).scalar() or 0

        if total_duration >= ATTENDANCE_THRESHOLD_MINUTES:
            record.status = "present"
        else:
            record.status = "absent"

        db.commit()

    finally:
        db.close()


# ---------------------------------------------------------------------------
# START SESSION
# ---------------------------------------------------------------------------

@router.post("/start")
async def start_session(
    course_id: int,
    batch_name: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    # Only instructor
    if current_user["role"] != "instructor":
        raise HTTPException(
            status_code=403,
            detail="Only instructors can start sessions"
        )

    # Check instructor assigned
    assignment = db.query(InstructorEnrollment).filter(
        InstructorEnrollment.user_id == current_user["user_id"],
        InstructorEnrollment.course_id == course_id,
        InstructorEnrollment.batch_name == batch_name
    ).first()

    if not assignment:
        raise HTTPException(
            status_code=403,
            detail="You are not assigned to this batch"
        )

    # Check if already live
    existing_live = db.query(ClassSession).filter(
        ClassSession.course_id == course_id,
        ClassSession.batch_name == batch_name,
        ClassSession.status == "live"
    ).first()

    if existing_live:
        raise HTTPException(
            status_code=400,
            detail="A live session is already running for this batch"
        )

    # Create room
    room_name = f"course_{course_id}_batch_{batch_name.replace(' ', '_')}"
    room = create_room(room_name)

    # Create new session
    session = ClassSession(
        course_id=course_id,
        batch_name=batch_name,
        livekit_room_name=room["room_id"],
        host_url=room["host_url"],
        join_url=room["guest_url"],
        status="live",
        start_time=datetime.now(IST).replace(tzinfo=None)
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return {
        "message": "Session started successfully",
        "session_id": session.id,
        "room_id": room["room_id"],
        "meet_link": room["host_url"],
        "guest_link": room["guest_url"],
        "status": session.status
    }


# ---------------------------------------------------------------------------
# GET ACTIVE SESSION
# ---------------------------------------------------------------------------

@router.get("/active")
def get_active_session(
    course_id: int,
    batch_name: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    session = db.query(ClassSession).filter(
        ClassSession.course_id == course_id,
        ClassSession.batch_name == batch_name,
        ClassSession.status == "live"
    ).order_by(ClassSession.id.desc()).first()

    if not session:
        return {
            "live": False,
            "join_enabled": False
        }

    is_instructor = current_user.get("role") == "instructor"

    meet_link = session.host_url if is_instructor else session.join_url

    # Append user name
    user_record = db.query(User).filter(
        User.id == current_user["user_id"]
    ).first()

    if user_record and user_record.name:
        encoded_name = urllib.parse.quote(user_record.name)

        connector = "&" if "?" in meet_link else "?"

        meet_link = f"{meet_link}{connector}name={encoded_name}"

    participant = db.query(SessionParticipant).filter(
        SessionParticipant.session_id == session.id,
        SessionParticipant.user_id == current_user["user_id"],
        SessionParticipant.leave_time == None
    ).first()

    return {
        "live": True,
        "join_enabled": True,
        "session_id": session.id,
        "room_id": session.livekit_room_name,
        "meet_link": meet_link,
        "is_joined": participant is not None,
        "participant_status": participant.status if participant else None
    }


# ---------------------------------------------------------------------------
# JOIN SESSION
# ---------------------------------------------------------------------------

@router.post("/join")
async def join_session(
    course_id: int,
    batch_name: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    if current_user["role"] != "student":
        raise HTTPException(
            status_code=403,
            detail="Only students can join"
        )

    # Check live session
    session = db.query(ClassSession).filter(
        ClassSession.course_id == course_id,
        ClassSession.batch_name == batch_name,
        ClassSession.status == "live"
    ).order_by(ClassSession.id.desc()).first()

    if not session:
        raise HTTPException(
            status_code=400,
            detail="Class not live"
        )

    # Check enrollment
    enrolled = db.query(Enrollment).filter(
        Enrollment.user_id == current_user["user_id"],
        Enrollment.course_id == course_id,
        Enrollment.batch_name == batch_name
    ).first()

    if not enrolled:
        raise HTTPException(
            status_code=403,
            detail="Student not enrolled"
        )

    # Already joined
    existing = db.query(SessionParticipant).filter(
        SessionParticipant.session_id == session.id,
        SessionParticipant.user_id == current_user["user_id"],
        SessionParticipant.leave_time == None
    ).first()

    if existing:
        return {
            "status": "already_joined"
        }

    participant = SessionParticipant(
        session_id=session.id,
        user_id=current_user["user_id"],
        join_time=datetime.now(IST).replace(tzinfo=None),
        status="pending"
    )

    db.add(participant)
    db.commit()
    db.refresh(participant)

    asyncio.create_task(auto_mark_attendance(participant.id))

    return {
        "status": "joined",
        "message": f"Attendance will be calculated after {ATTENDANCE_THRESHOLD_MINUTES} minutes"
    }


# ---------------------------------------------------------------------------
# LEAVE SESSION
# ---------------------------------------------------------------------------

@router.post("/leave")
def leave_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    record = db.query(SessionParticipant).filter(
        SessionParticipant.session_id == session_id,
        SessionParticipant.user_id == current_user["user_id"],
        SessionParticipant.leave_time == None
    ).first()

    if not record:
        raise HTTPException(
            status_code=404,
            detail="No active attendance record"
        )

    now = datetime.now(IST).replace(tzinfo=None)

    record.leave_time = now

    if not record.join_time:
        raise HTTPException(
            status_code=400,
            detail="Invalid attendance record"
        )

    duration = (now - record.join_time).total_seconds() / 60

    record.duration_minutes = round(duration, 2)

    db.commit()

    total_duration = db.query(
        func.sum(SessionParticipant.duration_minutes)
    ).filter(
        SessionParticipant.session_id == session_id,
        SessionParticipant.user_id == current_user["user_id"]
    ).scalar() or 0

    record.status = (
        "present"
        if total_duration >= ATTENDANCE_THRESHOLD_MINUTES
        else "absent"
    )

    db.commit()

    return {
        "status": "left",
        "duration_minutes": record.duration_minutes,
        "total_duration_minutes": round(total_duration, 2),
        "attendance_status": record.status,
        "join_time": record.join_time,
        "leave_time": record.leave_time
    }


# ---------------------------------------------------------------------------
# END SESSION
# ---------------------------------------------------------------------------

@router.post("/end")
def end_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    if current_user["role"] != "instructor":
        raise HTTPException(
            status_code=403,
            detail="Only instructors can end sessions"
        )

    session = db.query(ClassSession).filter(
        ClassSession.id == session_id
    ).first()

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    # Check instructor assignment
    assignment = db.query(InstructorEnrollment).filter(
        InstructorEnrollment.user_id == current_user["user_id"],
        InstructorEnrollment.course_id == session.course_id,
        InstructorEnrollment.batch_name == session.batch_name
    ).first()

    if not assignment:
        raise HTTPException(
            status_code=403,
            detail="You are not assigned to this batch"
        )

    if session.status != "live":
        raise HTTPException(
            status_code=400,
            detail="Session already ended"
        )

    now = datetime.now(IST).replace(tzinfo=None)

    session.status = "ended"
    session.end_time = now

    # Finalize open participants
    open_records = db.query(SessionParticipant).filter(
        SessionParticipant.session_id == session_id,
        SessionParticipant.leave_time == None,
        SessionParticipant.join_time != None
    ).all()

    for record in open_records:

        record.leave_time = now

        duration = (
            now - record.join_time
        ).total_seconds() / 60

        record.duration_minutes = round(duration, 2)

        total_duration = db.query(
            func.sum(SessionParticipant.duration_minutes)
        ).filter(
            SessionParticipant.session_id == session_id,
            SessionParticipant.user_id == record.user_id
        ).scalar() or 0

        record.status = (
            "present"
            if total_duration >= ATTENDANCE_THRESHOLD_MINUTES
            else "absent"
        )

    # Mark absent students
    enrolled_students = db.query(Enrollment).filter(
        Enrollment.course_id == session.course_id,
        Enrollment.batch_name == session.batch_name
    ).all()

    enrolled_ids = {e.user_id for e in enrolled_students}

    joined_ids = {
        r.user_id
        for r in db.query(SessionParticipant).filter(
            SessionParticipant.session_id == session_id
        ).all()
    }

    absent_students = enrolled_ids - joined_ids

    for user_id in absent_students:

        absent_record = SessionParticipant(
            session_id=session_id,
            user_id=user_id,
            join_time=None,
            leave_time=None,
            duration_minutes=0,
            status="absent"
        )

        db.add(absent_record)

    db.commit()

    return {
        "message": "Session ended successfully",
        "session_id": session.id
    }


# ---------------------------------------------------------------------------
# SESSION ATTENDANCE
# ---------------------------------------------------------------------------

@router.get("/session/{session_id}")
def get_session_attendance(
    session_id: int,
    db: Session = Depends(get_db)
):

    records = db.query(SessionParticipant).filter(
        SessionParticipant.session_id == session_id
    ).all()

    result = []

    for r in records:

        user = db.query(User).filter(
            User.id == r.user_id
        ).first()

        result.append({
            "user_id": r.user_id,
            "student_name": user.name if user else None,
            "join_time": r.join_time,
            "leave_time": r.leave_time,
            "duration_minutes": r.duration_minutes,
            "attendance_status": r.status
        })

    return result


# ---------------------------------------------------------------------------
# SESSION HISTORY
# ---------------------------------------------------------------------------

@router.get("/history")
def session_history(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    sessions = db.query(ClassSession).order_by(
        ClassSession.id.desc()
    ).all()

    return [
        {
            "session_id": s.id,
            "course_id": s.course_id,
            "batch_name": s.batch_name,
            "status": s.status,
            "start_time": s.start_time,
            "end_time": s.end_time,
            "room_name": s.livekit_room_name
        }
        for s in sessions
    ]
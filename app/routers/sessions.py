# app/routers/sessions.py

import asyncio
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

from app.database import get_db, SessionLocal
from app.models.session import ClassSession
from app.models.enrollment import Enrollment
from app.models.attendance import SessionParticipant
from app.models.user import User
from app.utils.security import get_current_user
from app.services.hms_service import create_room
import urllib.parse

router = APIRouter(prefix="/sessions", tags=["Sessions"])

# ⚠️ Set to 2 for testing — change back to 30 for production
ATTENDANCE_THRESHOLD_MINUTES = 30
ATTENDANCE_THRESHOLD_SECONDS = ATTENDANCE_THRESHOLD_MINUTES * 60


# ---------------------------------------------------------------------------
# BACKGROUND TASK: auto-mark attendance after threshold time
# ---------------------------------------------------------------------------
async def auto_mark_attendance(participant_id: int):
    """
    Sleeps for ATTENDANCE_THRESHOLD_SECONDS after a student joins.
    - Still in session (no leave_time) → PRESENT ✅
    - Left before threshold             → ABSENT  ❌
    - Already resolved by /leave        → skip
    """
    await asyncio.sleep(ATTENDANCE_THRESHOLD_SECONDS)

    db: Session = SessionLocal()
    try:
        record = db.query(SessionParticipant).filter(
            SessionParticipant.id == participant_id
        ).first()

        if not record:
            return

        # If already marked present, no need to downgrade to absent
        if record.status == "present":
            return

        now = datetime.now(IST).replace(tzinfo=None)

        # 1. Update current record's duration if it's still active
        if record.leave_time is None:
            duration = (now - record.join_time).total_seconds() / 60
            record.duration_minutes = round(duration, 2)
        
        db.commit() # save current record duration first

        # 2. Calculate TOTAL CUMULATIVE duration for this user in this session
        total_duration = db.query(func.sum(SessionParticipant.duration_minutes)).filter(
            SessionParticipant.session_id == record.session_id,
            SessionParticipant.user_id == record.user_id
        ).scalar() or 0

        # 3. Finalize status based on cumulative time
        if total_duration >= ATTENDANCE_THRESHOLD_MINUTES:
            record.status = "present"
            # Also optionally mark all other segments for this session as present? 
            # Usually marking the latest one is enough for the summary logic.
        else:
            # Only mark absent if we are sure they are not still inside another "join" record
            # But here we are specifically checking this record.
            if record.leave_time is not None:
                record.status = "absent"
            else:
                # Still inside, wait for threshold (already waited)
                # If total is still low, it stays "pending" or we can mark it now based on current time
                record.status = "absent" if total_duration < ATTENDANCE_THRESHOLD_MINUTES else "present"

        db.commit()
    finally:
        db.close()


# ---------------------------------------------------------------------------
# START SESSION  (instructor only)
# Creates a 100ms room and returns host + guest URLs
# ---------------------------------------------------------------------------
@router.post("/start")
async def start_session(
    course_id: int,
    batch_name: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "instructor":
        raise HTTPException(status_code=403, detail="Only instructor can start class")

    # Build a deterministic room name from course + batch
    room_name = f"course_{course_id}_batch_{batch_name.replace(' ', '_')}"

    session = db.query(ClassSession).filter(
        ClassSession.course_id == course_id,
        ClassSession.batch_name == batch_name
    ).first()

    # Create a new 100ms room (API call)
    room = await create_room(room_name)

    if session:
        # Clear old participants data for this session to allow fresh join/calculation
        db.query(SessionParticipant).filter(SessionParticipant.session_id == session.id).delete()
        
        session.status = "live"
        session.start_time = datetime.now(IST).replace(tzinfo=None)
        session.end_time = None
        session.livekit_room_name = room["room_id"]   # stores 100ms room_id
        session.host_url = room["host_url"]            # instructor join link
        session.join_url = room["guest_url"]           # student join link
    else:
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
        "session_id": session.id,
        "room_id": room["room_id"],
        "meet_link": room["host_url"],     # ← instructor opens this (host role)
        "guest_link": room["guest_url"],   # ← shown to students
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
    ).first()

    if not session:
        return {"live": False, "join_enabled": False}

    # Return role-appropriate meeting link
    is_instructor = current_user.get("role") == "instructor"
    meet_link = session.host_url if is_instructor else session.join_url

    # Automatically append student name if available
    user_record = db.query(User).filter(User.id == current_user["user_id"]).first()
    if user_record and user_record.name:
        encoded_name = urllib.parse.quote(user_record.name)
        connector = "&" if "?" in meet_link else "?"
        meet_link = f"{meet_link}{connector}name={encoded_name}"
        
    # Check if student has already joined (for sync across browsers)
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
# JOIN SESSION  (student only)
# Generates a LiveKit token + starts the attendance timer
# ---------------------------------------------------------------------------
@router.post("/join")
async def join_session(
    course_id: int,
    batch_name: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "student":
        raise HTTPException(status_code=403, detail="Only students can join")

    # Check session is live
    session = db.query(ClassSession).filter(
        ClassSession.course_id == course_id,
        ClassSession.batch_name == batch_name,
        ClassSession.status == "live"
    ).first()

    if not session:
        raise HTTPException(status_code=400, detail="Class not live")

    # Check student is enrolled
    enrolled = db.query(Enrollment).filter(
        Enrollment.user_id == current_user["user_id"],
        Enrollment.course_id == course_id,
        Enrollment.batch_name == batch_name
    ).first()

    if not enrolled:
        raise HTTPException(status_code=403, detail="Student not enrolled")

    # If already joined, skip creating a duplicate record
    existing = db.query(SessionParticipant).filter(
        SessionParticipant.session_id == session.id,
        SessionParticipant.user_id == current_user["user_id"],
        SessionParticipant.leave_time == None
    ).first()

    if existing:
        if existing.join_time is None:
            # This is a "no-show" record from a previous session end.
            # Delete it so we can create a fresh live join record.
            db.delete(existing)
            db.commit()
        else:
            return {"status": "already_joined"}

    # Create attendance record — status resolved after threshold time
    participant = SessionParticipant(
        session_id=session.id,
        user_id=current_user["user_id"],
        join_time=datetime.now(IST).replace(tzinfo=None),
        status="pending"
    )
    db.add(participant)
    db.commit()
    db.refresh(participant)

    # Schedule background attendance check
    asyncio.create_task(auto_mark_attendance(participant.id))

    return {
        "status": "joined",
        "message": f"Attendance will be auto-calculated after {ATTENDANCE_THRESHOLD_MINUTES} minutes"
    }


# ---------------------------------------------------------------------------
# LEAVE SESSION  (student)
# Records leave_time; background task uses it on next fire
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
        raise HTTPException(status_code=404, detail="No active attendance record")

    record.leave_time = datetime.now(IST).replace(tzinfo=None)

    # Guard: absent records created by /end have no join_time
    if record.join_time is None:
        raise HTTPException(status_code=400, detail="No join record found for this student")

    # Ensure naive subtraction
    jt = record.join_time.replace(tzinfo=None) if record.join_time.tzinfo else record.join_time
    lt = record.leave_time.replace(tzinfo=None) if record.leave_time.tzinfo else record.leave_time
    
    duration = (lt - jt).total_seconds() / 60
    record.duration_minutes = round(duration, 2)
    db.commit()

    # Calculate TOTAL CUMULATIVE duration
    from sqlalchemy import func
    total_duration = db.query(func.sum(SessionParticipant.duration_minutes)).filter(
        SessionParticipant.session_id == session_id,
        SessionParticipant.user_id == current_user["user_id"]
    ).scalar() or 0

    # Only mark absent if background task hasn't resolved it yet
    if record.status == "pending":
        record.status = "present" if total_duration >= ATTENDANCE_THRESHOLD_MINUTES else "absent"

    db.commit()

    return {
        "status": "left",
        "duration_minutes": record.duration_minutes,
        "total_duration_minutes": round(total_duration, 2),
        "attendance_status": record.status,
        "join_time": record.join_time,
        "leave_time": record.leave_time,
        "note": "Marked present" if record.status == "present" else f"Marked absent (cumulative time < {ATTENDANCE_THRESHOLD_MINUTES} minutes)"
    }


# ---------------------------------------------------------------------------
# END SESSION  (instructor only)
# Finalises all pending records + marks no-shows as absent
# ---------------------------------------------------------------------------
@router.post("/end")
def end_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "instructor":
        raise HTTPException(status_code=403, detail="Only instructor can end session")

    session = db.query(ClassSession).filter(
        ClassSession.id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status != "live":
        raise HTTPException(status_code=400, detail="Session already ended")

    now = datetime.now(IST).replace(tzinfo=None)
    session.status = "ended"
    session.end_time = now

    # Finalise any open records (including those already marked 'present' but still in the room)
    open_records = db.query(SessionParticipant).filter(
        SessionParticipant.session_id == session_id,
        SessionParticipant.leave_time == None,
        SessionParticipant.join_time != None
    ).all()

    for record in open_records:
        record.leave_time = now
        jt = record.join_time.replace(tzinfo=None) if record.join_time.tzinfo else record.join_time
        lt = record.leave_time.replace(tzinfo=None) if record.leave_time.tzinfo else record.leave_time
        
        duration = (lt - jt).total_seconds() / 60
        record.duration_minutes = round(duration, 2)
        
        # If it was still pending (e.g. ended before threshold), resolve it
        if record.status == "pending":
            record.status = "present" if duration >= ATTENDANCE_THRESHOLD_MINUTES else "absent"

    # Mark enrolled students who never joined as absent
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

    for user_id in enrolled_ids - joined_ids:
        db.add(SessionParticipant(
            session_id=session_id,
            user_id=user_id,
            join_time=None,
            leave_time=None,
            duration_minutes=0,
            status="absent"
        ))

    db.commit()

    return {
        "message": "Session ended successfully",
        "session_id": session.id
    }


# ---------------------------------------------------------------------------
# GET ATTENDANCE FOR A SESSION
# ---------------------------------------------------------------------------
@router.get("/session/{session_id}")
def get_session_attendance(
    session_id: int,
    db: Session = Depends(get_db)
):
    records = db.query(SessionParticipant).filter(
        SessionParticipant.session_id == session_id
    ).all()

    return [
        {
            "user_id": r.user_id,
            "join_time": r.join_time,
            "leave_time": r.leave_time,
            "duration_minutes": r.duration_minutes,
            "attendance_status": r.status   # present | absent | pending
        }
        for r in records
    ]

# app/routers/sessions.py

import asyncio

from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.config import JITSI_BASE_URL
from app.models.attendance import SessionParticipant
from app.models.classroom import Classroom
from app.models.enrollment import Enrollment
from app.models.instructor_enrollment import InstructorEnrollment
from app.models.session import ClassSession
from app.models.user import User
from app.services.jitsi_auth import build_meeting_url
from app.services.jitsi_auth import generate_room_name
from app.services.jitsi_service import create_room
from app.utils.security import get_current_user

IST = ZoneInfo("Asia/Kolkata")

router = APIRouter(
    prefix="/sessions",
    tags=["Sessions"]
)


def _ensure_session_access(
    db: Session,
    session: ClassSession,
    current_user: dict,
) -> None:
    role = current_user.get("role")

    if role == "student":

        enrollment = db.query(Enrollment).filter(
            Enrollment.user_id == current_user["user_id"],
            Enrollment.classroom_id == session.classroom_id
        ).first()

        if not enrollment:

            raise HTTPException(
                status_code=403,
                detail="Student not enrolled"
            )

    elif role == "instructor":

        assignment = db.query(InstructorEnrollment).filter(
            InstructorEnrollment.user_id == current_user["user_id"],
            InstructorEnrollment.classroom_id == session.classroom_id
        ).first()

        if not assignment:

            raise HTTPException(
                status_code=403,
                detail="Instructor not assigned"
            )

    elif role != "admin":

        raise HTTPException(
            status_code=403,
            detail="Not authorized to access this session"
        )


def _display_name_for_user(db: Session, user_id: int) -> str:
    user_record = db.query(User).filter(User.id == user_id).first()
    if user_record and user_record.name:
        return user_record.name
    return f"User_{user_id}"


# ---------------------------------------------------------------------------
# ATTENDANCE SETTINGS
# ---------------------------------------------------------------------------

ATTENDANCE_THRESHOLD_MINUTES = 30
ATTENDANCE_THRESHOLD_SECONDS = ATTENDANCE_THRESHOLD_MINUTES * 60


# ---------------------------------------------------------------------------
# BACKGROUND TASK
# ---------------------------------------------------------------------------

async def auto_mark_attendance(participant_id: int):

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

        if record.leave_time is None and record.join_time:

            duration = (
                now - record.join_time
            ).total_seconds() / 60

            record.duration_minutes = round(duration, 2)

        db.commit()

        total_duration = db.query(
            func.sum(SessionParticipant.duration_minutes)
        ).filter(
            SessionParticipant.session_id == record.session_id,
            SessionParticipant.user_id == record.user_id
        ).scalar() or 0

        record.status = (
            "present"
            if total_duration >= ATTENDANCE_THRESHOLD_MINUTES
            else "absent"
        )

        db.commit()

    finally:
        db.close()


# ---------------------------------------------------------------------------
# START SESSION
# ---------------------------------------------------------------------------

@router.post("/start")
async def start_session(
    classroom_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    # ONLY INSTRUCTORS
    if current_user["role"] != "instructor":

        raise HTTPException(
            status_code=403,
            detail="Only instructors can start sessions"
        )

    # VALIDATE CLASSROOM
    classroom = db.query(Classroom).filter(
        Classroom.id == classroom_id
    ).first()

    if not classroom:

        raise HTTPException(
            status_code=404,
            detail="Classroom not found"
        )

    # CHECK ASSIGNMENT
    assignment = db.query(InstructorEnrollment).filter(
        InstructorEnrollment.user_id == current_user["user_id"],
        InstructorEnrollment.classroom_id == classroom_id
    ).first()

    if not assignment:

        raise HTTPException(
            status_code=403,
            detail="You are not assigned to this classroom"
        )

    # CHECK LIVE SESSION
    existing_live = db.query(ClassSession).filter(
        ClassSession.classroom_id == classroom_id,
        ClassSession.status == "live"
    ).first()

    if existing_live:

        raise HTTPException(
            status_code=400,
            detail="A live session already exists"
        )

    # CREATE ROOM
    room_name = generate_room_name(
        classroom.id
    )

    room = create_room(room_name)
    instructor_name = _display_name_for_user(db, current_user["user_id"])
    host_url = build_meeting_url(
        room_name=room_name,
        user_id=current_user["user_id"],
        user_name=instructor_name,
        role="instructor",
    )

    # CREATE SESSION
    session = ClassSession(
        classroom_id=classroom.id,
        livekit_room_name=room["room_id"],
        host_url=host_url or room["host_url"],
        join_url=None,
        status="live",
        start_time=datetime.now(IST).replace(tzinfo=None)
    )

    db.add(session)

    db.commit()

    db.refresh(session)

    return {
        "message": "Session started successfully",
        "session_id": session.id,
        "classroom_id": classroom.id,
        "room_id": room["room_id"],
        "meet_link": host_url or room["host_url"],
        "guest_link": None,
        "status": session.status
    }


# ---------------------------------------------------------------------------
# GET ACTIVE SESSION
# ---------------------------------------------------------------------------

@router.get("/active")
def get_active_session(
    classroom_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    session = db.query(ClassSession).filter(
        ClassSession.classroom_id == classroom_id,
        ClassSession.status == "live"
    ).order_by(
        ClassSession.id.desc()
    ).first()

    if not session:

        return {
            "live": False,
            "join_enabled": False
        }

    _ensure_session_access(db, session, current_user)

    display_name = _display_name_for_user(db, current_user["user_id"])
    role = current_user.get("role", "student")
    meet_link = build_meeting_url(
        room_name=session.livekit_room_name,
        user_id=current_user["user_id"],
        user_name=display_name,
        role=role,
    )

    participant = db.query(SessionParticipant).filter(
        SessionParticipant.session_id == session.id,
        SessionParticipant.user_id == current_user["user_id"],
        SessionParticipant.leave_time == None
    ).first()

    return {
        "live": True,
        "join_enabled": True,
        "session_id": session.id,
        "classroom_id": classroom_id,
        "is_joined": participant is not None,
        "room_id": session.livekit_room_name,
        "meet_link": meet_link,
        "participant_status": (
            participant.status
            if participant
            else None
        )
    }


# ---------------------------------------------------------------------------
# JOIN SESSION
# ---------------------------------------------------------------------------

@router.post("/join")
async def join_session(
    classroom_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    if current_user["role"] != "student":

        raise HTTPException(
            status_code=403,
            detail="Only students can join"
        )

    # CHECK LIVE SESSION
    session = db.query(ClassSession).filter(
        ClassSession.classroom_id == classroom_id,
        ClassSession.status == "live"
    ).order_by(
        ClassSession.id.desc()
    ).first()

    if not session:

        raise HTTPException(
            status_code=400,
            detail="Class not live"
        )

    # CHECK ENROLLMENT
    enrolled = db.query(Enrollment).filter(
        Enrollment.user_id == current_user["user_id"],
        Enrollment.classroom_id == classroom_id
    ).first()

    if not enrolled:

        raise HTTPException(
            status_code=403,
            detail="Student not enrolled"
        )

    # ALREADY JOINED
    existing = db.query(SessionParticipant).filter(
        SessionParticipant.session_id == session.id,
        SessionParticipant.user_id == current_user["user_id"],
        SessionParticipant.leave_time == None
    ).first()

    if existing:

        return {
            "status": "already_joined",
            "meet_link": build_meeting_url(
                room_name=session.livekit_room_name,
                user_id=current_user["user_id"],
                user_name=_display_name_for_user(db, current_user["user_id"]),
                role="student",
            ),
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

    display_name = _display_name_for_user(db, current_user["user_id"])
    meeting_url = build_meeting_url(
        room_name=session.livekit_room_name,
        user_id=current_user["user_id"],
        user_name=display_name,
        role="student",
    )

    asyncio.create_task(
        auto_mark_attendance(participant.id)
    )

    return {
        "status": "joined",
        "meet_link": meeting_url,
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

    duration = (
        now - record.join_time
    ).total_seconds() / 60

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

    # CHECK ASSIGNMENT
    assignment = db.query(InstructorEnrollment).filter(
        InstructorEnrollment.user_id == current_user["user_id"],
        InstructorEnrollment.classroom_id == session.classroom_id
    ).first()

    if not assignment:

        raise HTTPException(
            status_code=403,
            detail="You are not assigned to this classroom"
        )

    if session.status != "live":

        raise HTTPException(
            status_code=400,
            detail="Session already ended"
        )

    now = datetime.now(IST).replace(tzinfo=None)

    session.status = "ended"

    session.end_time = now

    # FINALIZE PARTICIPANTS
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

    # FIND ENROLLED STUDENTS
    enrolled_students = db.query(Enrollment).filter(
        Enrollment.classroom_id == session.classroom_id
    ).all()

    enrolled_ids = {
        e.user_id
        for e in enrolled_students
    }

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

    sessions = db.query(
        ClassSession,
        Classroom
    ).join(
        Classroom,
        Classroom.id == ClassSession.classroom_id
    ).order_by(
        ClassSession.id.desc()
    ).all()

    result = []

    for session, classroom in sessions:

        result.append({
            "session_id": session.id,
            "classroom_id": classroom.id,
            "course_id": classroom.course_id,
            "batch_name": classroom.batch_name,
            "status": session.status,
            "start_time": session.start_time,
            "end_time": session.end_time,
            "room_name": session.livekit_room_name
        })

    return result



@router.post("/{session_id}/access")
def get_session_access(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    
    session = (
        db.query(ClassSession)
        .filter(
            ClassSession.id == session_id,
            ClassSession.status == "live"
        )
        .first()
    )

    if not session:

        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )
    _ensure_session_access(db, session, current_user)
    user = (
        db.query(User)
        .filter(
            User.id == current_user["user_id"]
        )
        .first()
    )

    display_name = user.name if user and user.name else f"User_{current_user['user_id']}"
    role = current_user["role"]
    meeting_url = build_meeting_url(
        room_name=session.livekit_room_name,
        user_id=current_user["user_id"],
        user_name=display_name,
        role=role,
    )

    return {

        "session_id": session.id,

        "room_name": session.livekit_room_name,

        "display_name": display_name,

        "role": role,

        "domain": JITSI_BASE_URL,

        "meeting_url": meeting_url,
    }

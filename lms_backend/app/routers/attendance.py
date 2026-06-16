from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

from app.database import get_db
from app.models.attendance import SessionParticipant
from app.models.session import ClassSession
from app.utils.security import require_roles

router = APIRouter(prefix="/attendance", tags=["Attendance"])

# Threshold for being marked present
ATT_THRESHOLD_MINUTES = 30

@router.post("/join")
def attendance_join(
    session_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_roles(["student"]))
):
    # Ensure session is live
    session = db.query(ClassSession).filter_by(
        id=session_id,
        status="live"
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not live")

    # Prevent duplicate joins
    existing = db.query(SessionParticipant).filter_by(
        session_id=session_id,
        user_id=user["user_id"],
        leave_time=None
    ).first()

    if existing:
        return {"message": "Already joined"}

    record = SessionParticipant(
        session_id=session_id,
        user_id=user["user_id"],
        join_time=datetime.now(IST).replace(tzinfo=None),
        status="pending"
    )

    db.add(record)
    db.commit()

    return {"message": "Attendance started"}

@router.post("/leave")
def attendance_leave(
    session_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_roles(["student"]))
):
    record = db.query(SessionParticipant).filter_by(
        session_id=session_id,
        user_id=user["user_id"],
        leave_time=None
    ).first()

    if not record:
        return {"message": "No active attendance"}

    record.leave_time = datetime.now(IST).replace(tzinfo=None)
    
    # Ensure naive subtraction
    jt = record.join_time.replace(tzinfo=None) if record.join_time.tzinfo else record.join_time
    lt = record.leave_time.replace(tzinfo=None) if record.leave_time.tzinfo else record.leave_time

    duration = round((lt - jt).total_seconds() / 60, 2)
    record.duration_minutes = duration
    db.commit()

    # Calculate TOTAL CUMULATIVE duration
    from sqlalchemy import func
    total_duration = db.query(func.sum(SessionParticipant.duration_minutes)).filter(
        SessionParticipant.session_id == session_id,
        SessionParticipant.user_id == user["user_id"]
    ).scalar() or 0
    
    # Set status based on duration if not already resolved
    if record.status == "pending" or record.status is None:
        record.status = "present" if total_duration >= ATT_THRESHOLD_MINUTES else "absent"
        
    db.commit()

    return {
        "message": "Attendance ended",
        "duration_minutes": duration,
        "total_duration_minutes": round(total_duration, 2),
        "status": record.status
    }

@router.get("/session/{session_id}")
def get_attendance(
    session_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_roles(["instructor"]))
):
    records = db.query(SessionParticipant).filter_by(
        session_id=session_id
    ).all()

    return [
        {
            "user_id": r.user_id,
            "join_time": r.join_time,
            "leave_time": r.leave_time,
            "duration_minutes": r.duration_minutes
        }
        for r in records
    ]

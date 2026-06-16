from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session
from sqlalchemy import func

IST = ZoneInfo("Asia/Kolkata")
from app.models.attendance import SessionParticipant

# Threshold for being marked present (consistent with sessions.py)
ATT_THRESHOLD_MINUTES = 30

def participant_join(db: Session, session_id: int, user_id: int):
    record = SessionParticipant(
        session_id=session_id,
        user_id=user_id,
        join_time=datetime.now(IST).replace(tzinfo=None),
        status="pending"
    )
    db.add(record)
    db.commit()

def participant_leave(db: Session, session_id: int, user_id: int):
    record = db.query(SessionParticipant).filter_by(
        session_id=session_id,
        user_id=user_id,
        leave_time=None
    ).first()

    if record:
        record.leave_time = datetime.now(IST).replace(tzinfo=None)
        
        jt = record.join_time.replace(tzinfo=None) if record.join_time.tzinfo else record.join_time
        lt = record.leave_time.replace(tzinfo=None) if record.leave_time.tzinfo else record.leave_time
        
        duration = (lt - jt).total_seconds() / 60
        record.duration_minutes = round(duration, 2)
        db.commit()

        # Calculate TOTAL CUMULATIVE duration
        total_duration = db.query(func.sum(SessionParticipant.duration_minutes)).filter(
            SessionParticipant.session_id == session_id,
            SessionParticipant.user_id == user_id
        ).scalar() or 0
        
        # Resolve status if not already set (e.g. by background task)
        if record.status == "pending" or record.status is None:
            record.status = "present" if total_duration >= ATT_THRESHOLD_MINUTES else "absent"
            
        db.commit()

def finalize_attendance(db: Session, session_id: int, total_minutes: float):
    records = db.query(SessionParticipant).filter_by(session_id=session_id).all()

    for r in records:
        ratio = r.duration_minutes / total_minutes
        if ratio >= 0.7:
            r.status = "present"
        elif ratio >= 0.5:
            r.status = "late"
        else:
            r.status = "absent"

    db.commit()

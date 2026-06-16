from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import SessionLocal
from app.utils.security import get_current_user
from app.models.session import ClassSession
from app.models.attendance import SessionParticipant
from app.models.course import Course
from app.models.enrollment import Enrollment
from datetime import datetime
from collections import defaultdict

router = APIRouter(
    prefix="/students/me/attendance",
    tags=["Student Attendance"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/summary")
def attendance_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["user_id"]

    # Only count sessions that have actually ended or are live
    total_classes = db.query(ClassSession).count()

    attended_classes = (
        db.query(SessionParticipant)
        .filter(
            SessionParticipant.user_id == user_id,
            SessionParticipant.status == "present"
        )
        .count()
    )

    attendance_percent = (
        round((attended_classes / total_classes) * 100)
        if total_classes > 0 else 0
    )

    return {
        "total_classes": total_classes,
        "attended_classes": attended_classes,
        "attendance_percent": attendance_percent
    }

@router.get("/history")
def attendance_history(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Returns all attendance records for the current student for calendar view."""
    user_id = current_user["user_id"]
    
    records = db.query(SessionParticipant).filter(
        SessionParticipant.user_id == user_id
    ).all()
    
    history = []
    for r in records:
        # Link back to session to get course info if needed, or just return record
        history.append({
            "session_id": r.session_id,
            "date": r.join_time.date() if r.join_time else None,
            "join_time": r.join_time,
            "leave_time": r.leave_time,
            "duration": r.duration_minutes,
            "status": r.status
        })
        
    return history

@router.get("/details")
def attendance_details(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Returns detailed attendance data for the calendar view and course stats.
    Matches the UI: calendar with icons, and course list with progress bars.
    """
    user_id = current_user["user_id"]
    now = datetime.now()

    # 1. Fetch all enrollments for this student
    enrollments = db.query(Enrollment).filter(Enrollment.user_id == user_id).all()
    course_ids = [e.course_id for e in enrollments]

    # 2. Fetch all sessions for these courses
    sessions = db.query(ClassSession, Course.name).join(
        Course, ClassSession.course_id == Course.id
    ).filter(ClassSession.course_id.in_(course_ids)).all()

    # 3. Fetch attendance records for this student and aggregate by session
    attendance_records = db.query(SessionParticipant).filter(
        SessionParticipant.user_id == user_id
    ).all()
    
    # Aggregate data by session_id
    aggregated_attn = defaultdict(lambda: {"total_duration": 0, "status": "absent", "is_present": False})
    for r in attendance_records:
        sid = r.session_id
        aggregated_attn[sid]["total_duration"] += (r.duration_minutes or 0)
        if r.status in ["present", "late"]:
            aggregated_attn[sid]["is_present"] = True
            aggregated_attn[sid]["status"] = "present"

    # 4. Process Calendar Data
    calendar = defaultdict(list)
    for session, course_name in sessions:
        attn = aggregated_attn.get(session.id)
        
        # Calculate total duration including currently live time if joined
        total_duration = attn["total_duration"] if attn else 0
        is_already_present = attn["is_present"] if attn else False

        status = "Yet to Start"
        if session.status == "live":
            # If already marked present or total duration >= threshold, it's Present
            status = "Present" if is_already_present or total_duration >= 30 else "Live"
        elif session.status == "ended" or (session.start_time and session.start_time < now):
            if is_already_present or total_duration >= 30:
                status = "Present"
            else:
                status = "Absent"

        # Group by date
        date_str = session.start_time.date().isoformat() if session.start_time else "unknown"
        calendar[date_str].append({
            "session_id": session.id,
            "course_name": course_name,
            "status": status,
            "start_time": session.start_time,
            "end_time": session.end_time,
            "time_range": f"{session.start_time.strftime('%I:%M%p') if session.start_time else ''}-"
                          f"{session.end_time.strftime('%I:%M%p') if session.end_time else ''}",
            "total_duration_minutes": round(total_duration, 2)
        })

    # 5. Process Course Stats
    course_stats = []
    for en in enrollments:
        course = db.query(Course).filter(Course.id == en.course_id).first()
        if not course:
            continue

        # Sessions for this specific course
        course_sessions = [s.id for s, name in sessions if s.course_id == course.id]
        total_sessions = len(course_sessions)
        
        # Count how many of these sessions have a cumulative duration >= threshold or are marked present
        attended_count = 0
        for sid in course_sessions:
            attn = aggregated_attn.get(sid)
            if attn and (attn["is_present"] or attn["total_duration"] >= 30):
                attended_count += 1

        course_stats.append({
            "course_id": course.id,
            "course_name": course.name,
            "progress_percent": en.progress_percent,
            "attended_count": attended_count,
            "total_count": total_sessions
        })

    return {
        "calendar": dict(calendar),
        "course_stats": course_stats
    }

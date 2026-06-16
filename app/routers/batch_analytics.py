# app/routers/batch_analytics.py
"""
Batch Analytics API
GET /batches/{course_id}/{batch_name}/overview

Returns the instructor's batch overview page data:
  - Batch name, course code / title
  - Attendance Rate  (avg % across all students, last 30 days)
  - Total Classes    (completed / scheduled)
  - Total Students   (active enrolled count)
  - Average Score    (avg score of the most recent submitted test)
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional

from app.database import get_db
from app.utils.security import get_current_user
from app.models.course import Course
from app.models.classroom import Classroom
from app.models.enrollment import Enrollment
from app.models.session import ClassSession
from app.models.attendance import SessionParticipant
from app.models.test import Test, TestSubmission
from app.models.user import User
from app.services.classroom_stats import require_classroom_access

router = APIRouter(prefix="/batches", tags=["Batch Analytics"])

ATTENDANCE_THRESHOLD_MINUTES = 30   # minutes to count as present
LAST_N_DAYS = 30                    # window for attendance rate


def check_instructor(current_user: dict):
    if current_user.get("role") != "instructor":
        raise HTTPException(status_code=403, detail="Instructor access required.")


# ── Helper: attendance rate for a batch over the last N days ─────────────────

def _attendance_rate(
    classroom_id: int,
    student_ids: list[int],
    db: Session,
    days: int = LAST_N_DAYS
) -> float:
    """
    Returns the average attendance rate (0–100) for all students in the batch
    over the last `days` days.

    Rate = (students marked present in session / total enrolled) averaged
           across all sessions in the window.
    """
    if not student_ids:
        return 0.0

    since = datetime.utcnow() - timedelta(days=days)

    sessions = db.query(ClassSession).filter(
        ClassSession.classroom_id == classroom_id,
        ClassSession.start_time >= since,
        ClassSession.status == "ended"
    ).all()

    if not sessions:
        # Fall back to all ended sessions (no 30-day filter)
        sessions = db.query(ClassSession).filter(
            ClassSession.classroom_id == classroom_id,
            ClassSession.status == "ended"
        ).all()

    if not sessions:
        return 0.0

    session_ids = [s.id for s in sessions]
    total_students = len(student_ids)

    # Count present participants per session
    total_rate_sum = 0.0
    for sid in session_ids:
        present_count = db.query(SessionParticipant).filter(
            SessionParticipant.session_id == sid,
            SessionParticipant.user_id.in_(student_ids),
            SessionParticipant.status == "present"
        ).count()
        session_rate = (present_count / total_students) * 100 if total_students > 0 else 0
        total_rate_sum += session_rate

    return round(total_rate_sum / len(session_ids), 1) if session_ids else 0.0


# ── Helper: class completion stats ───────────────────────────────────────────

def _class_stats(classroom_id: int, db: Session) -> dict:
    """
    Returns:
      completed  – number of `ended` ClassSession rows
      scheduled  – total scheduled slots (from CourseSchedule or ClassSession total)
    
    Strategy: CourseSchedules define the recurring schedule (days × weeks).
    We estimate "total scheduled" as the total ClassSession rows for the batch
    (each session row = one scheduled class whether ended or live/upcoming).
    """
    total = db.query(ClassSession).filter(
        ClassSession.classroom_id == classroom_id
    ).count()

    completed = db.query(ClassSession).filter(
        ClassSession.classroom_id == classroom_id,
        ClassSession.status == "ended"
    ).count()

    return {"completed": completed, "total": total}


# ── Helper: average score from the most recent test in the batch ──────────────

def _average_score(course_id: int, batch_name: str, db: Session) -> Optional[float]:
    """
    Returns the average score (0–100) of the most recently submitted test
    in this batch.  None if no submissions exist yet.
    """
    # Most recent test for this batch
    latest_test = (
        db.query(Test)
        .filter(Test.course_id == course_id, Test.batch_name == batch_name)
        .order_by(Test.created_at.desc())
        .first()
    )
    if not latest_test:
        return None

    avg = db.query(func.avg(TestSubmission.score_percentage)).filter(
        TestSubmission.test_id == latest_test.id,
        TestSubmission.status == "submitted"
    ).scalar()

    return round(float(avg), 1) if avg is not None else None


# ── Main Endpoint ─────────────────────────────────────────────────────────────

@router.get("/{course_id}/{batch_name}/overview")
def batch_overview(
    course_id: int,
    batch_name: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Instructor batch overview page.

    Returns:
    - batch_name, course_code, course_title
    - attendance_rate (%, last 30 days)
    - classes_completed / classes_total, completion_percent
    - total_students (active enrolled)
    - average_score (last assessment, /100)
    """
    if current_user.get("role") not in ("instructor", "admin"):
        raise HTTPException(status_code=403, detail="Instructor access required.")

    # 1. Validate course
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # 2. Validate batch exists
    classroom = db.query(Classroom).filter(
        Classroom.course_id == course_id,
        Classroom.batch_name == batch_name
    ).first()
    if not classroom:
        raise HTTPException(
            status_code=404,
            detail=f"Batch '{batch_name}' not found for this course"
        )

    require_classroom_access(db, current_user, classroom.id)

    # 3. Enrolled active students
    enrollments = db.query(Enrollment).filter(
        Enrollment.course_id == course_id,
        Enrollment.batch_name == batch_name,
        Enrollment.status == "ongoing"
    ).all()
    student_ids = [e.user_id for e in enrollments]
    total_students = len(student_ids)

    # 4. Attendance rate
    attendance_rate = _attendance_rate(classroom.id, student_ids, db)

    # 5. Class stats
    class_stats = _class_stats(classroom.id, db)
    classes_completed = class_stats["completed"]
    classes_total = class_stats["total"]
    completion_percent = (
        round((classes_completed / classes_total) * 100) if classes_total > 0 else 0
    )

    # 6. Average score (last assessment)
    average_score = _average_score(course_id, batch_name, db)

    return {
        "classroom_id": classroom.id,
        "batch_name": batch_name,
        "course_id": course_id,
        "course_title": course.name,

        # Attendance card: "87%  Avg. over last 30 days"
        "attendance_rate": attendance_rate,               # e.g. 87.0
        "attendance_window_days": LAST_N_DAYS,

        # Total Classes card: "26/31  81% Classes Completed"
        "classes_completed": classes_completed,           # e.g. 26
        "classes_total": classes_total,                   # e.g. 31
        "classes_completion_percent": completion_percent, # e.g. 81

        # Total Students card: "32  Enrolled active students"
        "total_students": total_students,                 # e.g. 32

        # Average Score card: "78/100  Last assessment"
        "average_score": average_score,                   # e.g. 78.0  (null if no tests)
        "average_score_max": 100
    }


# ── Bonus: list all batches for a course ─────────────────────────────────────

@router.get("/{course_id}/list")
def list_batches(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Lists all batches for a course, useful for the dropdown/nav."""
    check_instructor(current_user)

    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    classrooms = db.query(Classroom).filter(
        Classroom.course_id == course_id
    ).all()

    return {
        "course_id": course_id,
        "course_title": course.name,
        "batches": [
            {"batch_name": c.batch_name, "room_name": c.room_name}
            for c in classrooms
        ]
    }

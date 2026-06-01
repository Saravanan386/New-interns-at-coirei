from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db

from app.models.user import User
from app.models.course import Course
from app.models.classroom import Classroom
from app.models.enrollment import Enrollment
from app.models.session import ClassSession
from app.models.attendance import SessionParticipant

from app.utils.security import get_current_user

router = APIRouter(
    prefix="/dashboard/student",
    tags=["Student Dashboard"]
)


# -------------------------------------------------------------------
# STUDENT OVERVIEW
# -------------------------------------------------------------------
@router.get("/overview")
def student_overview(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    if current_user["role"] != "student":
        raise HTTPException(status_code=403, detail="Student access only")

    user_id = current_user["user_id"]

    student = db.query(User).filter(
        User.id == user_id
    ).first()

    total_courses = db.query(Enrollment).filter(
        Enrollment.user_id == user_id
    ).count()

    completed_courses = db.query(Enrollment).filter(
        Enrollment.user_id == user_id,
        Enrollment.status == "completed"
    ).count()

    ongoing_courses = db.query(Enrollment).filter(
        Enrollment.user_id == user_id,
        Enrollment.status == "ongoing"
    ).count()

    live_sessions = db.query(ClassSession).join(
        Enrollment,
        Enrollment.classroom_id == ClassSession.classroom_id
    ).filter(
        Enrollment.user_id == user_id,
        ClassSession.status == "live"
    ).count()

    attendance_total = db.query(SessionParticipant).filter(
        SessionParticipant.user_id == user_id,
        SessionParticipant.status.in_(["present", "absent"])
    ).count()

    attendance_present = db.query(SessionParticipant).filter(
        SessionParticipant.user_id == user_id,
        SessionParticipant.status == "present"
    ).count()

    attendance_percentage = 0

    if attendance_total > 0:
        attendance_percentage = round(
            (attendance_present / attendance_total) * 100,
            1
        )

    return {
        "student_id": student.student_id,
        "student_name": student.name,
        "email": student.email,
        "total_courses": total_courses,
        "completed_courses": completed_courses,
        "ongoing_courses": ongoing_courses,
        "live_sessions": live_sessions,
        "attendance_percentage": attendance_percentage
    }


# -------------------------------------------------------------------
# MY COURSES
# -------------------------------------------------------------------
@router.get("/courses")
def my_courses(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    rows = db.query(
        Enrollment,
        Classroom,
        Course
    ).join(
        Classroom,
        Classroom.id == Enrollment.classroom_id
    ).join(
        Course,
        Course.id == Classroom.course_id
    ).filter(
        Enrollment.user_id == current_user["user_id"]
    ).all()

    return [
        {
            "course_id": course.id,
            "course_name": course.name,
            "classroom_id": classroom.id,
            "batch_name": classroom.batch_name,
            "room_name": classroom.room_name,
            "progress_percent": enrollment.progress_percent,
            "status": enrollment.status,
            "duration_months": course.duration_months,
            "total_lessons": course.total_lessons
        }
        for enrollment, classroom, course in rows
    ]


# -------------------------------------------------------------------
# LIVE CLASSES
# -------------------------------------------------------------------
@router.get("/live-classes")
def live_classes(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    rows = db.query(
        ClassSession,
        Classroom,
        Course
    ).join(
        Classroom,
        Classroom.id == ClassSession.classroom_id
    ).join(
        Enrollment,
        Enrollment.classroom_id == Classroom.id
    ).join(
        Course,
        Course.id == Classroom.course_id
    ).filter(
        Enrollment.user_id == current_user["user_id"],
        ClassSession.status == "live"
    ).all()

    return [
        {
            "session_id": session.id,
            "course_name": course.name,
            "batch_name": classroom.batch_name,
            "room_name": classroom.room_name,
            "start_time": session.start_time,
            "join_url": session.join_url,
            "status": session.status
        }
        for session, classroom, course in rows
    ]


# -------------------------------------------------------------------
# ATTENDANCE
# -------------------------------------------------------------------
@router.get("/attendance")
def attendance_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    user_id = current_user["user_id"]

    total = db.query(SessionParticipant).filter(
        SessionParticipant.user_id == user_id,
        SessionParticipant.status.in_(["present", "absent"])
    ).count()

    present = db.query(SessionParticipant).filter(
        SessionParticipant.user_id == user_id,
        SessionParticipant.status == "present"
    ).count()

    absent = db.query(SessionParticipant).filter(
        SessionParticipant.user_id == user_id,
        SessionParticipant.status == "absent"
    ).count()

    percentage = 0

    if total > 0:
        percentage = round((present / total) * 100, 1)

    return {
        "total_classes": total,
        "present_classes": present,
        "absent_classes": absent,
        "attendance_percentage": percentage
    }
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db

from app.models.user import User
from app.models.course import Course
from app.models.classroom import Classroom
from app.models.enrollment import Enrollment
from app.models.session import ClassSession
from app.models.attendance import SessionParticipant
from app.models.instructor_enrollment import InstructorEnrollment

from app.utils.security import get_current_user

router = APIRouter(
    prefix="/dashboard/admin",
    tags=["Admin Dashboard"]
)


# -------------------------------------------------------------------
# ADMIN OVERVIEW
# -------------------------------------------------------------------
@router.get("/overview")
def admin_overview(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access only")

    total_students = db.query(User).filter(
        User.role == "student"
    ).count()

    total_instructors = db.query(User).filter(
        User.role == "instructor"
    ).count()

    total_courses = db.query(Course).count()

    total_batches = db.query(Classroom).count()

    live_sessions = db.query(ClassSession).filter(
        ClassSession.status == "live"
    ).count()

    attendance_total = db.query(SessionParticipant).filter(
        SessionParticipant.status.in_(["present", "absent"])
    ).count()

    attendance_present = db.query(SessionParticipant).filter(
        SessionParticipant.status == "present"
    ).count()

    attendance_percentage = 0

    if attendance_total > 0:
        attendance_percentage = round(
            (attendance_present / attendance_total) * 100,
            1
        )

    return {
        "total_students": total_students,
        "total_instructors": total_instructors,
        "total_courses": total_courses,
        "total_batches": total_batches,
        "live_sessions": live_sessions,
        "attendance_percentage": attendance_percentage
    }


# -------------------------------------------------------------------
# STUDENT ANALYTICS
# -------------------------------------------------------------------
@router.get("/students")
def student_analytics(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access only")

    students = db.query(User).filter(
        User.role == "student"
    ).all()

    result = []

    for student in students:

        total_courses = db.query(Enrollment).filter(
            Enrollment.user_id == student.id
        ).count()

        completed_courses = db.query(Enrollment).filter(
            Enrollment.user_id == student.id,
            Enrollment.status == "completed"
        ).count()

        result.append({
            "student_id": student.student_id,
            "name": student.name,
            "email": student.email,
            "total_courses": total_courses,
            "completed_courses": completed_courses
        })

    return result


# -------------------------------------------------------------------
# INSTRUCTOR ANALYTICS
# -------------------------------------------------------------------
@router.get("/instructors")
def instructor_analytics(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access only")

    instructors = db.query(User).filter(
        User.role == "instructor"
    ).all()

    result = []

    for instructor in instructors:

        assigned_batches = db.query(
            InstructorEnrollment
        ).filter(
            InstructorEnrollment.user_id == instructor.id
        ).count()

        result.append({
            "instructor_id": instructor.student_id,
            "name": instructor.name,
            "email": instructor.email,
            "assigned_batches": assigned_batches
        })

    return result


# -------------------------------------------------------------------
# COURSE ANALYTICS
# -------------------------------------------------------------------
@router.get("/courses")
def course_analytics(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access only")

    rows = db.query(
        Course,
        func.count(Enrollment.id).label("student_count")
    ).outerjoin(
        Classroom,
        Classroom.course_id == Course.id
    ).outerjoin(
        Enrollment,
        Enrollment.classroom_id == Classroom.id
    ).group_by(
        Course.id
    ).all()

    return [
        {
            "course_id": course.id,
            "course_name": course.name,
            "duration_months": course.duration_months,
            "total_lessons": course.total_lessons,
            "student_count": student_count
        }
        for course, student_count in rows
    ]


# -------------------------------------------------------------------
# LIVE SESSIONS
# -------------------------------------------------------------------
@router.get("/live-sessions")
def live_sessions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access only")

    rows = db.query(
        ClassSession,
        Classroom,
        Course
    ).join(
        Classroom,
        Classroom.id == ClassSession.classroom_id
    ).join(
        Course,
        Course.id == Classroom.course_id
    ).filter(
        ClassSession.status == "live"
    ).all()

    return [
        {
            "session_id": session.id,
            "classroom_id": classroom.id,
            "course_id": course.id,
            "course_name": course.name,
            "batch_name": classroom.batch_name,
            "room_name": classroom.room_name,
            "start_time": session.start_time,
            "status": session.status
        }
        for session, classroom, course in rows
    ]
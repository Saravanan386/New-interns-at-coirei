# app/routers/dashboard.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db

from app.utils.security import get_current_user

from app.models.user import User
from app.models.course import Course
from app.models.classroom import Classroom
from app.models.enrollment import Enrollment
from app.models.instructor_enrollment import InstructorEnrollment
from app.models.session import ClassSession
from app.models.attendance import SessionParticipant

# Optional modules
from app.models.assignment import Assignment, AssignmentSubmission
from app.models.test import Test, TestSubmission

router = APIRouter(
    prefix="/dashboard/admin",
    tags=["Instructor Dashboard"]
)


# ============================================================================
# HELPER
# ============================================================================

def get_instructor_classrooms(
    db: Session,
    user_id: int
):
    return (
        db.query(
            InstructorEnrollment,
            Classroom,
            Course
        )
        .join(
            Classroom,
            Classroom.id == InstructorEnrollment.classroom_id
        )
        .join(
            Course,
            Course.id == Classroom.course_id
        )
        .filter(
            InstructorEnrollment.user_id == user_id
        )
        .all()
    )


# ============================================================================
# DASHBOARD OVERVIEW
# ============================================================================

@router.get("/")
def instructor_dashboard(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    if current_user["role"] != "instructor":
        raise HTTPException(
            status_code=403,
            detail="Instructor access only"
        )

    user_id = current_user["user_id"]

    instructor_rows = get_instructor_classrooms(
        db,
        user_id
    )

    if not instructor_rows:
        return {
            "summary": {
                "active_courses": 0,
                "total_students": 0,
                "live_sessions": 0,
                "pending_reviews": 0
            },
            "courses": [],
            "recent_sessions": [],
            "live_classes": [],
            "recent_tests": []
        }

    classroom_ids = list({
        row.Classroom.id
        for row in instructor_rows
    })

    course_ids = list({
        row.Course.id
        for row in instructor_rows
    })

    # ------------------------------------------------------------------------
    # SUMMARY
    # ------------------------------------------------------------------------

    total_students = (
        db.query(
            func.count(
                func.distinct(Enrollment.user_id)
            )
        )
        .filter(
            Enrollment.classroom_id.in_(classroom_ids)
        )
        .scalar()
    ) or 0

    live_sessions = (
        db.query(ClassSession)
        .filter(
            ClassSession.classroom_id.in_(classroom_ids),
            ClassSession.status == "live"
        )
        .count()
    )

    pending_reviews = 0

    try:
        pending_reviews = (
            db.query(AssignmentSubmission)
            .join(
                Assignment,
                Assignment.id == AssignmentSubmission.assignment_id
            )
            .filter(
                Assignment.created_by == user_id,
                AssignmentSubmission.status == "submitted"
            )
            .count()
        )
    except:
        pass

    summary = {
        "active_courses": len(course_ids),
        "total_students": total_students,
        "live_sessions": live_sessions,
        "pending_reviews": pending_reviews
    }

    # ------------------------------------------------------------------------
    # COURSES
    # ------------------------------------------------------------------------

    courses_data = []

    for row in instructor_rows:

        classroom = row.Classroom
        course = row.Course

        student_count = (
            db.query(Enrollment)
            .filter(
                Enrollment.classroom_id == classroom.id
            )
            .count()
        )

        courses_data.append({
            "classroom_id": classroom.id,
            "course_id": course.id,
            "course_name": course.name,
            "course_code": course.course_code,
            "batch_name": classroom.batch_name,
            "room_name": classroom.room_name,
            "students": student_count
        })

    # ------------------------------------------------------------------------
    # RECENT SESSIONS
    # ------------------------------------------------------------------------

    sessions = (
        db.query(ClassSession)
        .filter(
            ClassSession.classroom_id.in_(classroom_ids)
        )
        .order_by(
            ClassSession.id.desc()
        )
        .limit(5)
        .all()
    )

    recent_sessions = []

    for session in sessions:

        classroom = db.query(Classroom).filter(
            Classroom.id == session.classroom_id
        ).first()

        present_count = (
            db.query(SessionParticipant)
            .filter(
                SessionParticipant.session_id == session.id,
                SessionParticipant.status == "present"
            )
            .count()
        )

        total_enrolled = (
            db.query(Enrollment)
            .filter(
                Enrollment.classroom_id == session.classroom_id
            )
            .count()
        )

        recent_sessions.append({
            "session_id": session.id,
            "batch_name": classroom.batch_name if classroom else None,
            "status": session.status,
            "start_time": session.start_time,
            "end_time": session.end_time,
            "attendance": {
                "present": present_count,
                "total": total_enrolled
            }
        })

    # ------------------------------------------------------------------------
    # LIVE CLASSES
    # ------------------------------------------------------------------------

    live_class_rows = (
        db.query(ClassSession)
        .filter(
            ClassSession.classroom_id.in_(classroom_ids),
            ClassSession.status == "live"
        )
        .all()
    )

    live_classes = []

    for session in live_class_rows:

        classroom = db.query(Classroom).filter(
            Classroom.id == session.classroom_id
        ).first()

        live_classes.append({
            "session_id": session.id,
            "batch_name": classroom.batch_name if classroom else None,
            "join_url": session.host_url,
            "status": session.status,
            "start_time": session.start_time
        })

    # ------------------------------------------------------------------------
    # TESTS
    # ------------------------------------------------------------------------

    recent_tests = []

    try:

        tests = (
            db.query(Test)
            .filter(
                Test.classroom_id.in_(classroom_ids)
            )
            .order_by(
                Test.id.desc()
            )
            .limit(5)
            .all()
        )

        for test in tests:

            submissions = (
                db.query(TestSubmission)
                .filter(
                    TestSubmission.test_id == test.id
                )
                .count()
            )

            passed = (
                db.query(TestSubmission)
                .filter(
                    TestSubmission.test_id == test.id,
                    TestSubmission.is_passed == True
                )
                .count()
            )

            recent_tests.append({
                "test_id": test.id,
                "title": test.title,
                "submissions": submissions,
                "passed": passed,
                "failed": submissions - passed
            })

    except:
        pass

    return {
        "summary": summary,
        "courses": courses_data,
        "recent_sessions": recent_sessions,
        "live_classes": live_classes,
        "recent_tests": recent_tests
    }
from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.assignment import Assignment
from app.models.attendance import SessionParticipant
from app.models.classroom import Classroom
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.instructor_enrollment import InstructorEnrollment
from app.models.session import ClassSession
from app.models.test import Test


def require_classroom_access(db: Session, current_user: dict, classroom_id: int) -> Classroom:
    classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")

    role = current_user.get("role")
    if role == "admin":
        return classroom

    if role != "instructor":
        raise HTTPException(status_code=403, detail="Instructor access required")

    assigned = (
        db.query(InstructorEnrollment.id)
        .filter(
            InstructorEnrollment.user_id == current_user["user_id"],
            InstructorEnrollment.classroom_id == classroom_id,
        )
        .first()
    )
    if not assigned:
        raise HTTPException(status_code=403, detail="You are not assigned to this classroom")

    return classroom


def classroom_student_ids(db: Session, classroom_id: int) -> list[int]:
    rows = (
        db.query(Enrollment.user_id)
        .filter(
            Enrollment.classroom_id == classroom_id,
            Enrollment.status == "ongoing",
        )
        .distinct()
        .all()
    )
    return [row.user_id for row in rows]


def classroom_assignment_count(db: Session, classroom: Classroom) -> int:
    return (
        db.query(Assignment.id)
        .filter(
            Assignment.course_id == classroom.course_id,
            Assignment.batch_name == classroom.batch_name,
        )
        .count()
    )


def classroom_test_count(db: Session, classroom: Classroom) -> int:
    return (
        db.query(Test.id)
        .filter(
            Test.course_id == classroom.course_id,
            Test.batch_name == classroom.batch_name,
        )
        .count()
    )


def classroom_session_stats(db: Session, classroom: Classroom) -> dict:
    sessions = (
        db.query(ClassSession)
        .filter(ClassSession.classroom_id == classroom.id)
        .order_by(ClassSession.start_time.asc())
        .all()
    )

    total_sessions = len(sessions)
    completed_sessions = sum(1 for session in sessions if session.status == "ended")
    live_sessions = sum(1 for session in sessions if session.status == "live")

    return {
        "sessions": sessions,
        "total_sessions": total_sessions,
        "completed_sessions": completed_sessions,
        "live_sessions": live_sessions,
    }


def classroom_attendance_percentage(db: Session, classroom: Classroom) -> float:
    student_ids = classroom_student_ids(db, classroom.id)
    if not student_ids:
        return 0.0

    sessions = (
        db.query(ClassSession.id)
        .filter(
            ClassSession.classroom_id == classroom.id,
            ClassSession.status == "ended",
        )
        .all()
    )
    session_ids = [row.id for row in sessions]
    if not session_ids:
        return 0.0

    present_rows = (
        db.query(
            SessionParticipant.session_id,
            func.count(SessionParticipant.id),
        )
        .filter(
            SessionParticipant.session_id.in_(session_ids),
            SessionParticipant.user_id.in_(student_ids),
            SessionParticipant.status == "present",
        )
        .group_by(SessionParticipant.session_id)
        .all()
    )
    present_by_session = {session_id: count for session_id, count in present_rows}

    total_students = len(student_ids)
    if total_students == 0:
        return 0.0

    total_rate = 0.0
    for session_id in session_ids:
        total_rate += (present_by_session.get(session_id, 0) / total_students) * 100

    return round(total_rate / len(session_ids), 2)


def classroom_dashboard_metrics(db: Session, classroom: Classroom) -> dict:
    course = db.query(Course).filter(Course.id == classroom.course_id).first()
    total_students = len(classroom_student_ids(db, classroom.id))
    session_stats = classroom_session_stats(db, classroom)
    attendance_percentage = classroom_attendance_percentage(db, classroom)
    assignment_count = classroom_assignment_count(db, classroom)
    test_count = classroom_test_count(db, classroom)

    total_sessions = session_stats["total_sessions"]
    completed_sessions = session_stats["completed_sessions"]
    completion_percentage = (
        round((completed_sessions / total_sessions) * 100, 2)
        if total_sessions
        else 0.0
    )

    return {
        "classroom_id": classroom.id,
        "course_id": classroom.course_id,
        "course_name": course.name if course else None,
        "course_code": course.course_code if course else None,
        "batch_name": classroom.batch_name,
        "room_name": classroom.room_name,
        "total_students": total_students,
        "attendance_percentage": attendance_percentage,
        "completed_classes": completed_sessions,
        "total_classes": total_sessions,
        "class_completion_percentage": completion_percentage,
        "assignment_count": assignment_count,
        "test_count": test_count,
        "live_sessions": session_stats["live_sessions"],
    }

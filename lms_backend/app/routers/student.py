from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.assignment import Assignment, AssignmentSubmission
from app.models.attendance import SessionParticipant
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.module import Module
from app.models.session import ClassSession
from app.models.test import Test, TestSubmission
from app.utils.security import get_current_user




router = APIRouter(prefix="/student", tags=["Student APIs"])


def require_student(current_user: dict):
    if current_user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Student access required.")


def get_student_enrollments(db: Session, user_id: int):
    return (
        db.query(Enrollment)
        .filter(
            Enrollment.user_id == user_id,
            Enrollment.status == "ongoing",
        )
        .all()
    )


def format_date(dt: Optional[datetime]):
    return dt.isoformat() if dt else None


def assignment_status(assignment: Assignment, submission: Optional[AssignmentSubmission]):
    if submission and submission.status in ("submitted", "graded"):
        return submission.status
    if assignment.due_date and assignment.due_date < datetime.utcnow():
        return "overdue"
    return "pending"


@router.get("/dashboard")
def student_dashboard(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    require_student(current_user)
    user_id = current_user["user_id"]
    enrollments = get_student_enrollments(db, user_id)

    course_ids = [en.course_id for en in enrollments]
    total_courses = len(course_ids)

    total_classes = 0
    attended_classes = 0
    if course_ids:
        total_classes = (
            db.query(ClassSession)
            .filter(ClassSession.course_id.in_(course_ids))
            .count()
        )
        attended_classes = (
            db.query(SessionParticipant)
            .join(ClassSession, ClassSession.id == SessionParticipant.session_id)
            .filter(
                SessionParticipant.user_id == user_id,
                SessionParticipant.status == "present",
                ClassSession.course_id.in_(course_ids),
            )
            .count()
        )

    assignment_query = db.query(Assignment)
    test_query = db.query(Test)
    if course_ids:
        assignment_filters = []
        test_filters = []
        for en in enrollments:
            assignment_filters.append(
                (Assignment.course_id == en.course_id)
                & (Assignment.batch_name == en.batch_name)
            )
            test_filters.append(
                (Test.course_id == en.course_id)
                & (Test.batch_name == en.batch_name)
            )
        from sqlalchemy import or_

        total_assignments = assignment_query.filter(or_(*assignment_filters)).count()
        total_tests = test_query.filter(or_(*test_filters)).count()
    else:
        total_assignments = 0
        total_tests = 0

    attendance_percent = (
        round((attended_classes / total_classes) * 100)
        if total_classes else 0
    )

    return {
        "student_id": user_id,
        "total_courses": total_courses,
        "total_classes": total_classes,
        "attended_classes": attended_classes,
        "attendance_percent": attendance_percent,
        "total_assignments": total_assignments,
        "total_tests": total_tests,
    }


@router.get("/materials")
def student_materials(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    require_student(current_user)
    enrollments = get_student_enrollments(db, current_user["user_id"])

    materials = []
    for en in enrollments:
        course = db.query(Course).filter(Course.id == en.course_id).first()
        if not course:
            continue

        modules = (
            db.query(Module)
            .filter(
                Module.course_id == en.course_id,
                (Module.batch_name == en.batch_name) | (Module.batch_name == None),
            )
            .order_by(Module.order)
            .all()
        )

        materials.append({
            "course_id": course.id,
            "course_name": course.name,
            "batch_name": en.batch_name,
            "modules": [
                {
                    "module_id": module.id,
                    "module_name": module.title,
                    "order": module.order,
                    "status": module.status,
                    "chapters": [
                        {
                            "chapter_id": chapter.id,
                            "chapter_name": chapter.title,
                            "order": chapter.order,
                        }
                        for chapter in module.chapters
                    ],
                }
                for module in modules
            ],
        })

    return materials


@router.get("/assignments")
def student_assignments(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    require_student(current_user)
    user_id = current_user["user_id"]
    enrollments = get_student_enrollments(db, user_id)

    submissions = (
        db.query(AssignmentSubmission)
        .filter(AssignmentSubmission.student_user_id == user_id)
        .all()
    )
    submission_map = {submission.assignment_id: submission for submission in submissions}

    items = []
    for en in enrollments:
        course = db.query(Course).filter(Course.id == en.course_id).first()
        assignments = (
            db.query(Assignment)
            .filter(
                Assignment.course_id == en.course_id,
                Assignment.batch_name == en.batch_name,
            )
            .order_by(Assignment.created_at.desc())
            .all()
        )

        for assignment in assignments:
            submission = submission_map.get(assignment.id)
            items.append({
                "assignment_id": assignment.id,
                "course_id": assignment.course_id,
                "course_name": course.name if course else None,
                "batch_name": assignment.batch_name,
                "module_name": assignment.module_name,
                "title": assignment.title,
                "description": assignment.description,
                "objective": assignment.objective,
                "expected_outcome": assignment.expected_outcome,
                "due_date": format_date(assignment.due_date),
                "status": assignment_status(assignment, submission),
                "submission_id": submission.id if submission else None,
                "grade": submission.grade if submission else None,
                "feedback": submission.feedback if submission else None,
            })

    return items


@router.get("/tests")
def student_tests(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    require_student(current_user)
    user_id = current_user["user_id"]
    enrollments = get_student_enrollments(db, user_id)

    submissions = (
        db.query(TestSubmission)
        .filter(TestSubmission.student_user_id == user_id)
        .all()
    )
    submission_map = {submission.test_id: submission for submission in submissions}

    items = []
    for en in enrollments:
        course = db.query(Course).filter(Course.id == en.course_id).first()
        tests = (
            db.query(Test)
            .filter(
                Test.course_id == en.course_id,
                Test.batch_name == en.batch_name,
            )
            .order_by(Test.start_time.asc())
            .all()
        )

        for test in tests:
            submission = submission_map.get(test.id)
            items.append({
                "test_id": test.id,
                "course_id": test.course_id,
                "course_name": course.name if course else None,
                "batch_name": test.batch_name,
                "module_name": test.module_name,
                "title": test.title,
                "description": test.description,
                "start_time": format_date(test.start_time),
                "end_time": format_date(test.end_time),
                "status": submission.status if submission else "not_started",
                "submission_id": submission.id if submission else None,
                "score": submission.score if submission else None,
                "is_passed": submission.is_passed if submission else None,
            })

    return items


@router.get("/certificates")
def student_certificates(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    require_student(current_user)
    user_id = current_user["user_id"]

    passed_submissions = (
        db.query(TestSubmission, Test, Course)
        .join(Test, Test.id == TestSubmission.test_id)
        .join(Course, Course.id == Test.course_id)
        .filter(
            TestSubmission.student_user_id == user_id,
            TestSubmission.is_passed == True,
        )
        .all()
    )

    return [
        {
            "certificate_id": f"TEST-{test.id}-USER-{user_id}",
            "test_id": test.id,
            "course_id": course.id,
            "course_name": course.name,
            "title": test.title,
            "issued_at": format_date(submission.submitted_at),
            "score": submission.score,
        }
        for submission, test, course in passed_submissions
    ]

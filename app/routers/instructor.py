from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.assignment import Assignment, AssignmentSubmission
from app.models.attendance import SessionParticipant
from app.models.classroom import Classroom
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.instructor_enrollment import InstructorEnrollment
from app.models.session import ClassSession
from app.models.test import Test, TestSubmission
from app.models.user import User
from app.utils.security import get_current_user

router = APIRouter(prefix="/instructor", tags=["Instructor APIs"])


def require_instructor(current_user: dict) -> None:
    if current_user.get("role") not in ("instructor", "admin"):
        raise HTTPException(status_code=403, detail="Instructor access required")


def _assigned_pairs(db: Session, current_user: dict) -> list[tuple[int, str]]:
    if current_user.get("role") == "admin":
        rows = db.query(Classroom.course_id, Classroom.batch_name).distinct().all()
    else:
        rows = (
            db.query(Classroom.course_id, Classroom.batch_name)
            .join(InstructorEnrollment, InstructorEnrollment.classroom_id == Classroom.id)
            .filter(InstructorEnrollment.user_id == current_user["user_id"])
            .distinct()
            .all()
        )
    return [(course_id, batch_name) for course_id, batch_name in rows if batch_name]


def _apply_pair_filter(query, model, pairs: list[tuple[int, str]]):
    if not pairs:
        return query.filter(False)

    condition = None
    for course_id, batch_name in pairs:
        pair_condition = (model.course_id == course_id) & (model.batch_name == batch_name)
        condition = pair_condition if condition is None else condition | pair_condition
    return query.filter(condition)


def _course_name_map(db: Session) -> dict[int, str]:
    return {course.id: course.name for course in db.query(Course).all()}


def _classroom_ids_for_pairs(
    db: Session,
    pairs: list[tuple[int, str]],
    course_id: Optional[int] = None,
    batch_name: Optional[str] = None,
) -> list[int]:
    query = db.query(Classroom.id, Classroom.course_id, Classroom.batch_name)

    if pairs:
        pair_condition = None
        for pair_course_id, pair_batch_name in pairs:
            current = (
                (Classroom.course_id == pair_course_id)
                & (Classroom.batch_name == pair_batch_name)
            )
            pair_condition = current if pair_condition is None else pair_condition | current
        query = query.filter(pair_condition)
    else:
        return []

    if course_id is not None:
        query = query.filter(Classroom.course_id == course_id)
    if batch_name:
        query = query.filter(Classroom.batch_name == batch_name)

    return [row.id for row in query.distinct().all()]


def _student_payload(student: Optional[User]) -> dict:
    if not student:
        return {
            "student_user_id": None,
            "student_id": None,
            "student_name": "Unknown",
            "email": None,
        }

    return {
        "student_user_id": student.id,
        "student_id": student.student_id or str(student.id),
        "student_name": student.name,
        "email": student.email,
    }


@router.get("/dashboard")
def instructor_dashboard(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    require_instructor(current_user)
    pairs = _assigned_pairs(db, current_user)
    course_names = _course_name_map(db)
    course_ids = sorted({course_id for course_id, _ in pairs})

    total_students = 0
    for course_id, batch_name in pairs:
        total_students += (
            db.query(Enrollment.user_id)
            .filter(
                Enrollment.course_id == course_id,
                Enrollment.batch_name == batch_name,
                Enrollment.status == "ongoing",
            )
            .distinct()
            .count()
        )

    classroom_ids = _classroom_ids_for_pairs(db, pairs)
    sessions_q = db.query(ClassSession).filter(
        ClassSession.classroom_id.in_(classroom_ids)
    )
    tests_q = _apply_pair_filter(db.query(Test), Test, pairs)
    assignments_q = db.query(Assignment).filter(Assignment.created_by == current_user["user_id"])
    if current_user.get("role") == "admin":
        assignments_q = _apply_pair_filter(db.query(Assignment), Assignment, pairs)

    return {
        "total_courses": len(course_ids),
        "total_batches": len(pairs),
        "total_students": total_students,
        "live_sessions": sessions_q.filter(ClassSession.status == "live").count(),
        "total_sessions": sessions_q.count(),
        "total_assignments": assignments_q.count(),
        "total_tests": tests_q.count(),
        "courses": [
            {
                "course_id": course_id,
                "course_name": course_names.get(course_id, "Unknown"),
                "batches": sorted(batch for cid, batch in pairs if cid == course_id),
            }
            for course_id in course_ids
        ],
    }


@router.get("/sessions")
def instructor_sessions(
    course_id: Optional[int] = None,
    batch_name: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    require_instructor(current_user)
    pairs = _assigned_pairs(db, current_user)
    classroom_ids = _classroom_ids_for_pairs(db, pairs, course_id=course_id, batch_name=batch_name)
    query = db.query(ClassSession).filter(ClassSession.classroom_id.in_(classroom_ids))
    if status:
        query = query.filter(ClassSession.status == status)

    course_names = _course_name_map(db)
    sessions = query.order_by(ClassSession.start_time.desc()).all()
    rows = []

    for session in sessions:
        attendance_counts = dict(
            db.query(SessionParticipant.status, func.count(SessionParticipant.id))
            .filter(SessionParticipant.session_id == session.id)
            .group_by(SessionParticipant.status)
            .all()
        )
        classroom = db.query(Classroom).filter(Classroom.id == session.classroom_id).first()
        total_enrolled = db.query(Enrollment).filter(
            Enrollment.classroom_id == session.classroom_id,
            Enrollment.status == "ongoing",
        ).count()

        rows.append({
            "session_id": session.id,
            "course_id": classroom.course_id if classroom else None,
            "course_name": course_names.get(classroom.course_id, "Unknown") if classroom else None,
            "batch_name": classroom.batch_name if classroom else None,
            "status": session.status,
            "start_time": session.start_time,
            "end_time": session.end_time,
            "meet_link": session.host_url,
            "guest_link": session.join_url,
            "total_enrolled": total_enrolled,
            "present_count": attendance_counts.get("present", 0),
            "absent_count": attendance_counts.get("absent", 0),
            "pending_count": attendance_counts.get("pending", 0),
        })

    return {"sessions": rows}


@router.get("/assignment-submissions")
def instructor_assignment_submissions(
    assignment_id: Optional[int] = None,
    course_id: Optional[int] = None,
    batch_name: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    require_instructor(current_user)

    query = db.query(Assignment)
    if current_user.get("role") != "admin":
        query = query.filter(Assignment.created_by == current_user["user_id"])
    else:
        query = _apply_pair_filter(query, Assignment, _assigned_pairs(db, current_user))

    if assignment_id is not None:
        query = query.filter(Assignment.id == assignment_id)
    if course_id is not None:
        query = query.filter(Assignment.course_id == course_id)
    if batch_name:
        query = query.filter(Assignment.batch_name == batch_name)

    course_names = _course_name_map(db)
    rows = []

    for assignment in query.order_by(Assignment.created_at.desc()).all():
        enrollments = db.query(Enrollment).filter(
            Enrollment.classroom_id.in_(
                db.query(Classroom.id).filter(
                    Classroom.course_id == assignment.course_id,
                    Classroom.batch_name == assignment.batch_name,
                )
            ),
            Enrollment.status == "ongoing",
        ).all()
        submissions = db.query(AssignmentSubmission).filter(
            AssignmentSubmission.assignment_id == assignment.id
        ).all()
        submission_by_student = {sub.student_user_id: sub for sub in submissions}

        for enrollment in enrollments:
            student = db.query(User).filter(User.id == enrollment.user_id).first()
            submission = submission_by_student.get(enrollment.user_id)
            row_status = submission.status if submission else "pending"
            if status and row_status != status:
                continue

            rows.append({
                "assignment_id": assignment.id,
                "assignment_title": assignment.title,
                "course_id": assignment.course_id,
                "course_name": course_names.get(assignment.course_id, "Unknown"),
                "batch_name": assignment.batch_name,
                "module_name": assignment.module.title if assignment.module else None,
                **_student_payload(student),
                "submission_id": submission.id if submission else None,
                "status": row_status,
                "submitted_at": submission.submitted_at if submission else None,
                "grade": submission.grade if submission else None,
                "feedback": submission.feedback if submission else None,
                "file_name": submission.file_name if submission else None,
                "file_path": submission.file_path if submission else None,
            })

    return {"submissions": rows}


@router.get("/test-results")
def instructor_test_results(
    test_id: Optional[int] = None,
    course_id: Optional[int] = None,
    batch_name: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    require_instructor(current_user)
    query = _apply_pair_filter(db.query(Test), Test, _assigned_pairs(db, current_user))

    if test_id is not None:
        query = query.filter(Test.id == test_id)
    if course_id is not None:
        query = query.filter(Test.course_id == course_id)
    if batch_name:
        query = query.filter(Test.batch_name == batch_name)

    course_names = _course_name_map(db)
    rows = []

    for test in query.order_by(Test.created_at.desc()).all():
        enrollments = db.query(Enrollment).filter(
            Enrollment.classroom_id.in_(
                db.query(Classroom.id).filter(
                    Classroom.course_id == test.course_id,
                    Classroom.batch_name == test.batch_name,
                )
            ),
            Enrollment.status == "ongoing",
        ).all()
        submissions = db.query(TestSubmission).filter(TestSubmission.test_id == test.id).all()
        submission_by_student = {sub.student_user_id: sub for sub in submissions}

        for enrollment in enrollments:
            student = db.query(User).filter(User.id == enrollment.user_id).first()
            submission = submission_by_student.get(enrollment.user_id)
            row_status = submission.status if submission else "not_attended"
            if status and row_status != status:
                continue

            rows.append({
                "test_id": test.id,
                "test_title": test.title,
                "course_id": test.course_id,
                "course_name": course_names.get(test.course_id, "Unknown"),
                "batch_name": test.batch_name,
                "module_name": test.module.title if test.module else None,
                **_student_payload(student),
                "submission_id": submission.id if submission else None,
                "status": row_status,
                "started_at": submission.started_at if submission else None,
                "submitted_at": submission.submitted_at if submission else None,
                "score": submission.score_percentage if submission else None,
                "is_passed": submission.is_passed if submission else None,
            })

    return {"results": rows}

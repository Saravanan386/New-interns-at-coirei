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
def require_student(current_user: dict):
    """
    Ensures the current user is a student.
    Raises 403 if not.
    """
    if current_user.get("role") != "student":
        raise HTTPException(
            status_code=403,
            detail="Student access only"
        )

    return True
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
            "course_code":course.course_code,
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



from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.security import get_current_user

from app.models.user import User
from app.models.course import Course
from app.models.classroom import Classroom
from app.models.enrollment import Enrollment
from app.models.assignment import Assignment, AssignmentSubmission
from app.models.test import Test, TestSubmission
from app.models.module import Module, Chapter
from app.models.session import ClassSession
from app.models.attendance import SessionParticipant
from app.models.registration_profile import StudentInformation

def check_student(current_user):
    if current_user.get("role") != "student":
        raise HTTPException(
            status_code=403,
            detail="Student only"
        )


@router.get("/profile-summary")
def profile_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_student(current_user)

    student_id = current_user["user_id"]

    user = db.query(User).filter(
        User.id == student_id
    ).first()

    profile = db.query(StudentInformation).filter(
        StudentInformation.user_id == student_id
    ).first()

    enrollments = db.query(Enrollment).filter(
        Enrollment.user_id == student_id,
        Enrollment.status == "ongoing"
    ).all()

    course_ids = []
    classroom_ids = []

    for e in enrollments:
        classroom_ids.append(e.classroom_id)

        classroom = db.query(Classroom).filter(
            Classroom.id == e.classroom_id
        ).first()

        if classroom:
            course_ids.append(classroom.course_id)

    course_ids = list(set(course_ids))

    total_courses = len(course_ids)

    courses_data = []

    total_modules = 0
    total_chapters = 0

    for course_id in course_ids:

        course = db.query(Course).filter(
            Course.id == course_id
        ).first()

        modules = db.query(Module).filter(
            Module.course_id == course_id
        ).all()

        module_count = len(modules)

        chapter_count = sum(
            len(m.chapters)
            for m in modules
        )

        total_modules += module_count
        total_chapters += chapter_count

        courses_data.append({
            "course_id": course.id,
            "course_code": course.course_code,
            "course_name": course.name,
            "duration_months": course.duration_months,
            "module_count": module_count,
            "chapter_count": chapter_count
        })

    total_classes = db.query(ClassSession).filter(
        ClassSession.classroom_id.in_(classroom_ids)
    ).count()

    attended_classes = db.query(SessionParticipant).filter(
        SessionParticipant.user_id == student_id,
        SessionParticipant.status == "present"
    ).count()

    attendance_percentage = 0

    if total_classes > 0:
        attendance_percentage = round(
            (attended_classes / total_classes) * 100,
            2
        )

    assignments = db.query(Assignment).filter(
        Assignment.course_id.in_(course_ids)
    ).all()

    assignment_ids = [a.id for a in assignments]

    submissions = db.query(AssignmentSubmission).filter(
        AssignmentSubmission.student_user_id == student_id
    ).all()

    submitted_assignment_ids = [
        s.assignment_id
        for s in submissions
    ]

    pending_assignments = len(
        [
            a for a in assignments
            if a.id not in submitted_assignment_ids
        ]
    )

    tests = db.query(Test).filter(
        Test.course_id.in_(course_ids)
    ).all()

    test_ids = [t.id for t in tests]

    test_submissions = db.query(TestSubmission).filter(
        TestSubmission.student_user_id == student_id
    ).all()

    submitted_tests = len(
        [
            t for t in test_submissions
            if t.status == "submitted"
        ]
    )

    passed_tests = len(
        [
            t for t in test_submissions
            if t.is_passed
        ]
    )

    failed_tests = len(
        [
            t for t in test_submissions
            if t.is_passed is False
        ]
    )

    avg_score = 0

    scores = [
        t.score_percentage
        for t in test_submissions
        if t.score_percentage is not None
    ]

    if scores:
        avg_score = round(
            sum(scores) / len(scores),
            2
        )

    return {

        "profile": {
            "user_id": user.id,
            "student_id": user.student_id,
            "name": user.name,
            "email": user.email,
            "phone": (
                profile.phone_number
                if profile
                else None
            ),
            "profile_image": (
                profile.profile_image_url
                if profile
                else None
            ),
            "status": (
                profile.account_status
                if profile
                else "active"
            )
        },

        "summary": {
            "courses": total_courses,
            "modules": total_modules,
            "chapters": total_chapters,

            "classes_total": total_classes,
            "classes_attended": attended_classes,
            "attendance_percentage": attendance_percentage,

            "assignments_total": len(assignments),
            "assignments_pending": pending_assignments,
            "assignments_submitted": len(submissions),

            "tests_total": len(tests),
            "tests_attempted": submitted_tests,
            "tests_passed": passed_tests,
            "tests_failed": failed_tests,
            "average_test_score": avg_score
        },

        "courses": courses_data
    }

# app/routers/dashboard_student.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_
from datetime import datetime

from app.database import get_db
from app.utils.security import get_current_user
from app.models.user import User
from app.models.enrollment import Enrollment
from app.models.classroom import Classroom
from app.models.course import Course
from app.models.module import Module, Chapter
from app.models.session import ClassSession
from app.models.attendance import SessionParticipant
from app.models.assignment import Assignment, AssignmentSubmission
from app.models.test import Test, TestSubmission

router = APIRouter(prefix="/dashboard/student", tags=["Student Dashboard"])


@router.get("/home")
def dashboard_home(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_student(current_user)

    user_id = current_user["user_id"]

    user = db.query(User).filter(User.id == user_id).first()
    profile = db.query(StudentInformation).filter(StudentInformation.user_id == user_id).first()

    enrollments = db.query(Enrollment).filter(
        Enrollment.user_id == user_id
    ).all()

    classroom_ids = [e.classroom_id for e in enrollments]
    classroom_map = {}
    classrooms = []
    if classroom_ids:
        classrooms = db.query(Classroom).filter(Classroom.id.in_(classroom_ids)).all()
        classroom_map = {c.id: c for c in classrooms}

    course_ids = list({c.course_id for c in classrooms if c.course_id})

    total_courses = len(enrollments)
    ongoing_courses = db.query(Enrollment).filter(
        Enrollment.user_id == user_id,
        Enrollment.status == "ongoing"
    ).count()
    completed_courses = db.query(Enrollment).filter(
        Enrollment.user_id == user_id,
        Enrollment.status == "completed"
    ).count()

    total_sessions = db.query(SessionParticipant).filter(SessionParticipant.user_id == user_id).count()
    present_sessions = db.query(SessionParticipant).filter(
        SessionParticipant.user_id == user_id,
        SessionParticipant.status.in_(["present", "late"])
    ).count()
    attendance_percentage = round((present_sessions / total_sessions) * 100, 1) if total_sessions else 0

    assignments_total = 0
    assignments_pending = 0
    assignments_submitted = 0
    tests_total = 0
    tests_attempted = 0
    average_score = 0

    if course_ids:
        assignments_total = db.query(Assignment).filter(
            Assignment.course_id.in_(course_ids)
        ).count()

        tests_total = db.query(Test).filter(
            Test.course_id.in_(course_ids)
        ).count()

        assignment_submissions = db.query(AssignmentSubmission).join(Assignment).filter(
            Assignment.course_id.in_(course_ids),
            AssignmentSubmission.student_user_id == user_id
        ).all()

        assignments_submitted = sum(1 for s in assignment_submissions if s.submitted_at or s.status == "submitted")
        assignments_pending = max(assignments_total - assignments_submitted, 0)

        test_submissions = db.query(TestSubmission).join(Test).filter(
            Test.course_id.in_(course_ids),
            TestSubmission.student_user_id == user_id
        ).all()

        tests_attempted = sum(1 for s in test_submissions if s.status in ["submitted", "in_progress"])
        scores = [s.score_percentage for s in test_submissions if s.score_percentage is not None]
        average_score = round(sum(scores) / len(scores), 1) if scores else 0

    live_classes = db.query(ClassSession).join(Classroom).filter(
        Classroom.id.in_(classroom_ids),
        ClassSession.status == "live"
    ).count() if classroom_ids else 0

    return {
        "profile": {
            "user_id": user.id if user else user_id,
            "student_id": profile.user.student_id if profile and profile.user else None,
            "name": profile.full_name if profile else (user.name if user else None),
            "email": profile.email if profile else (user.email if user else None),
            "phone": profile.phone_number if profile else None,
            "profile_image": profile.profile_image_url if profile else None,
        },
        "stats": {
            "total_courses": total_courses,
            "ongoing_courses": ongoing_courses,
            "completed_courses": completed_courses,
            "attendance_percentage": attendance_percentage,
            "assignments_total": assignments_total,
            "assignments_pending": assignments_pending,
            "assignments_submitted": assignments_submitted,
            "tests_total": tests_total,
            "tests_attempted": tests_attempted,
            "average_score": average_score,
            "live_classes": live_classes,
        }
    }


@router.get("/courses")
def my_courses(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_student(current_user)
    user_id = current_user["user_id"]

    enrollments = db.query(Enrollment).filter(
        Enrollment.user_id == user_id
    ).all()

    result = []
    for en in enrollments:
        classroom = db.query(Classroom).filter(Classroom.id == en.classroom_id).first()
        if not classroom:
            continue

        course = db.query(Course).filter(Course.id == classroom.course_id).first()

        module_count = db.query(Module).filter(Module.course_id == classroom.course_id).count()
        chapter_count = db.query(Chapter).join(Module).filter(Module.course_id == classroom.course_id).count()

        result.append({
            "course_id": course.id if course else classroom.course_id,
            "course_name": course.name if course else None,
            "course_code": course.course_code if course else None,
            "batch_name": classroom.batch_name,
            "duration_months": course.duration_months if course else None,
            "total_modules": module_count,
            "total_chapters": chapter_count,
            "progress_percent": en.progress_percent,
            "status": en.status
        })

    return result


@router.get("/assignments")
def my_assignments(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_student(current_user)
    user_id = current_user["user_id"]

    enrollments = db.query(Enrollment).filter(
        Enrollment.user_id == user_id
    ).all()

    result = []
    seen = set()

    for en in enrollments:
        classroom = db.query(Classroom).filter(Classroom.id == en.classroom_id).first()
        if not classroom:
            continue

        assignments = db.query(Assignment).filter(
            Assignment.course_id == classroom.course_id,
            Assignment.batch_name == classroom.batch_name
        ).all()

        for assignment in assignments:
            if assignment.id in seen:
                continue
            seen.add(assignment.id)

            course = db.query(Course).filter(Course.id == assignment.course_id).first()
            module = db.query(Module).filter(Module.id == assignment.module_id).first()

            submission = db.query(AssignmentSubmission).filter(
                AssignmentSubmission.assignment_id == assignment.id,
                AssignmentSubmission.student_user_id == user_id
            ).first()

            result.append({
                "assignment_id": assignment.id,
                "title": assignment.title,
                "course_name": course.name if course else None,
                "module_name": module.title if module else None,
                "batch_name": assignment.batch_name,
                "due_date": assignment.due_date,
                "status": submission.status if submission else "pending",
                "submitted_at": submission.submitted_at if submission else None
            })

    return result


@router.get("/tests")
def my_tests(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_student(current_user)
    user_id = current_user["user_id"]

    enrollments = db.query(Enrollment).filter(
        Enrollment.user_id == user_id
    ).all()

    result = []
    seen = set()

    for en in enrollments:
        classroom = db.query(Classroom).filter(Classroom.id == en.classroom_id).first()
        if not classroom:
            continue

        tests = db.query(Test).filter(
            Test.course_id == classroom.course_id,
            Test.batch_name == classroom.batch_name
        ).all()

        for test in tests:
            if test.id in seen:
                continue
            seen.add(test.id)

            course = db.query(Course).filter(Course.id == test.course_id).first()
            module = db.query(Module).filter(Module.id == test.module_id).first()
            submission = db.query(TestSubmission).filter(
                TestSubmission.test_id == test.id,
                TestSubmission.student_user_id == user_id
            ).first()

            result.append({
                "test_id": test.id,
                "title": test.title,
                "course_name": course.name if course else None,
                "module_name": module.title if module else None,
                "status": submission.status if submission else "not_attended",
                "score_percentage": submission.score_percentage if submission else None,
                "is_passed": submission.is_passed if submission else None
            })

    return result


@router.get("/attendance")
def attendance_summary(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_student(current_user)
    user_id = current_user["user_id"]

    total_classes = db.query(SessionParticipant).filter(SessionParticipant.user_id == user_id).count()
    present_classes = db.query(SessionParticipant).filter(
        SessionParticipant.user_id == user_id,
        SessionParticipant.status.in_(["present", "late"])
    ).count()
    absent_classes = db.query(SessionParticipant).filter(
        SessionParticipant.user_id == user_id,
        SessionParticipant.status == "absent"
    ).count()

    attendance_percentage = round((present_classes / total_classes) * 100, 1) if total_classes else 0

    return {
        "attendance_percentage": attendance_percentage,
        "total_classes": total_classes,
        "present_classes": present_classes,
        "absent_classes": absent_classes
    }


@router.get("/live-classes")
def live_classes(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_student(current_user)
    user_id = current_user["user_id"]

    enrollments = db.query(Enrollment).filter(Enrollment.user_id == user_id).all()
    classroom_ids = [e.classroom_id for e in enrollments]

    if not classroom_ids:
        return []

    sessions = db.query(ClassSession).join(Classroom).filter(
        Classroom.id.in_(classroom_ids),
        ClassSession.status == "live"
    ).all()

    result = []
    for s in sessions:
        classroom = db.query(Classroom).filter(Classroom.id == s.classroom_id).first()
        course = db.query(Course).filter(Course.id == classroom.course_id).first() if classroom else None

        result.append({
            "session_id": s.id,
            "course_name": course.name if course else None,
            "batch_name": classroom.batch_name if classroom else None,
            "room_name": classroom.room_name if classroom else None,
            "join_url": s.join_url,
            "start_time": s.start_time,
            "status": s.status
        })

    return result
# app/routers/dashboard_student.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.utils.security import get_current_user

from app.models.user import User
from app.models.enrollment import Enrollment
from app.models.classroom import Classroom
from app.models.course import Course
from app.models.module import Module, Chapter
from app.models.chapter_resources import ChapterResource
from app.models.session import ClassSession
from app.models.attendance import SessionParticipant
from app.models.assignment import Assignment, AssignmentSubmission
from app.models.test import Test, TestSubmission, Question, Option, StudentAnswer
from app.models.registration_profile import StudentInformation
from app.models.announcements import Announcement


# -------------------------------------------------------------------
# ROUTER
# -------------------------------------------------------------------
router = APIRouter(
    prefix="/dashboard/student",
    tags=["Student Dashboard"]
)


# -------------------------------------------------------------------
# HELPER
# -------------------------------------------------------------------
def require_student(current_user: dict):
    if current_user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Student access only")
    return True


# -------------------------------------------------------------------
# PYDANTIC SCHEMAS (for request bodies)
# -------------------------------------------------------------------
class AnswerSubmit(BaseModel):
    question_id: int
    selected_option_id: Optional[int] = None
    selected_option_ids: Optional[str] = None   # comma-separated for checkbox
    text_answer: Optional[str] = None


class TestSubmitRequest(BaseModel):
    answers: List[AnswerSubmit]


# -------------------------------------------------------------------
# 1. DASHBOARD HOME
# GET /dashboard/student/home
# -------------------------------------------------------------------
@router.get("/home")
def dashboard_home(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    require_student(current_user)
    user_id = current_user["user_id"]

    user    = db.query(User).filter(User.id == user_id).first()
    profile = db.query(StudentInformation).filter(StudentInformation.user_id == user_id).first()

    # ── enrollments & classrooms ──────────────────────────────────
    enrollments   = db.query(Enrollment).filter(Enrollment.user_id == user_id).all()
    classroom_ids = [e.classroom_id for e in enrollments]

    classrooms    = (
        db.query(Classroom).filter(Classroom.id.in_(classroom_ids)).all()
        if classroom_ids else []
    )
    course_ids = list({c.course_id for c in classrooms if c.course_id})

    # ── course counts ─────────────────────────────────────────────
    total_courses     = len(enrollments)
    ongoing_courses   = sum(1 for e in enrollments if e.status == "ongoing")
    completed_courses = sum(1 for e in enrollments if e.status == "completed")

    # ── attendance ────────────────────────────────────────────────
    total_sessions = db.query(SessionParticipant).filter(
        SessionParticipant.user_id == user_id
    ).count()

    present_sessions = db.query(SessionParticipant).filter(
        SessionParticipant.user_id == user_id,
        SessionParticipant.status.in_(["present", "late"])
    ).count()

    attendance_percentage = (
        round((present_sessions / total_sessions) * 100, 1)
        if total_sessions else 0
    )

    # ── assignments ───────────────────────────────────────────────
    assignments_total     = 0
    assignments_pending   = 0
    assignments_submitted = 0
    tests_total           = 0
    tests_attempted       = 0
    average_score         = 0

    if course_ids:
        assignments_total = db.query(Assignment).filter(
            Assignment.course_id.in_(course_ids)
        ).count()

        tests_total = db.query(Test).filter(
            Test.course_id.in_(course_ids)
        ).count()

        assignment_submissions = (
            db.query(AssignmentSubmission)
            .join(Assignment)
            .filter(
                Assignment.course_id.in_(course_ids),
                AssignmentSubmission.student_user_id == user_id
            )
            .all()
        )
        assignments_submitted = sum(
            1 for s in assignment_submissions
            if s.submitted_at or s.status == "submitted"
        )
        assignments_pending = max(assignments_total - assignments_submitted, 0)

        test_submissions = (
            db.query(TestSubmission)
            .join(Test)
            .filter(
                Test.course_id.in_(course_ids),
                TestSubmission.student_user_id == user_id
            )
            .all()
        )
        tests_attempted = sum(
            1 for s in test_submissions
            if s.status in ["submitted", "in_progress"]
        )
        scores = [
            s.score_percentage for s in test_submissions
            if s.score_percentage is not None
        ]
        average_score = round(sum(scores) / len(scores), 1) if scores else 0

    # ── live classes ──────────────────────────────────────────────
    live_classes = (
        db.query(ClassSession)
        .join(Classroom)
        .filter(
            Classroom.id.in_(classroom_ids),
            ClassSession.status == "live"
        ).count()
        if classroom_ids else 0
    )

    return {
        "profile": {
            "user_id":       user.id if user else user_id,
            "student_id":    user.student_id if user else None,
            "name":          profile.full_name if profile else (user.name if user else None),
            "email":         profile.email if profile else (user.email if user else None),
            "phone":         profile.phone_number if profile else None,
            "profile_image": profile.profile_image_url if profile else None,
        },
        "stats": {
            "total_courses":        total_courses,
            "ongoing_courses":      ongoing_courses,
            "completed_courses":    completed_courses,
            "attendance_percentage": attendance_percentage,
            "assignments_total":    assignments_total,
            "assignments_pending":  assignments_pending,
            "assignments_submitted": assignments_submitted,
            "tests_total":          tests_total,
            "tests_attempted":      tests_attempted,
            "average_score":        average_score,
            "live_classes":         live_classes,
        }
    }


# -------------------------------------------------------------------
# 2. OVERVIEW (compact summary card)
# GET /dashboard/student/overview
# -------------------------------------------------------------------
@router.get("/overview")
def student_overview(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    require_student(current_user)
    user_id = current_user["user_id"]

    student = db.query(User).filter(User.id == user_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    total_courses     = db.query(Enrollment).filter(Enrollment.user_id == user_id).count()
    completed_courses = db.query(Enrollment).filter(
        Enrollment.user_id == user_id, Enrollment.status == "completed"
    ).count()
    ongoing_courses   = db.query(Enrollment).filter(
        Enrollment.user_id == user_id, Enrollment.status == "ongoing"
    ).count()

    live_sessions = (
        db.query(ClassSession)
        .join(Enrollment, Enrollment.classroom_id == ClassSession.classroom_id)
        .filter(
            Enrollment.user_id == user_id,
            ClassSession.status == "live"
        ).count()
    )

    attendance_total = db.query(SessionParticipant).filter(
        SessionParticipant.user_id == user_id,
        SessionParticipant.status.in_(["present", "absent"])
    ).count()

    attendance_present = db.query(SessionParticipant).filter(
        SessionParticipant.user_id == user_id,
        SessionParticipant.status == "present"
    ).count()

    attendance_percentage = (
        round((attendance_present / attendance_total) * 100, 1)
        if attendance_total > 0 else 0
    )

    return {
        "student_id":            student.student_id,
        "student_name":          student.name,
        "email":                 student.email,
        "total_courses":         total_courses,
        "completed_courses":     completed_courses,
        "ongoing_courses":       ongoing_courses,
        "live_sessions":         live_sessions,
        "attendance_percentage": attendance_percentage,
    }


# -------------------------------------------------------------------
# 3. MY COURSES (with instructor + module/chapter counts)
# GET /dashboard/student/courses
# -------------------------------------------------------------------
@router.get("/courses")
def my_courses(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    require_student(current_user)
    user_id = current_user["user_id"]

    enrollments = db.query(Enrollment).filter(Enrollment.user_id == user_id).all()

    result = []
    for en in enrollments:
        classroom = db.query(Classroom).filter(Classroom.id == en.classroom_id).first()
        if not classroom:
            continue

        course = db.query(Course).filter(Course.id == classroom.course_id).first()

        # resolve instructor
        instructor = None
        if classroom.instructor_id:
            instructor = db.query(User).filter(User.id == classroom.instructor_id).first()

        module_count = db.query(Module).filter(
            Module.course_id == classroom.course_id
        ).count()

        chapter_count = (
            db.query(Chapter)
            .join(Module)
            .filter(Module.course_id == classroom.course_id)
            .count()
        )

        enrolled_count = db.query(Enrollment).filter(
            Enrollment.classroom_id == classroom.id
        ).count()

        result.append({
            "course_id":               course.id if course else classroom.course_id,
            "course_name":             course.name if course else None,
            "course_code":             course.course_code if course else None,
            "course_description":      course.description if course else None,
            "thumbnail_url":           getattr(course, "thumbnail_url", None),
            "batch_name":              classroom.batch_name,
            "room_name":               classroom.room_name,
            "duration_months":         course.duration_months if course else None,
            "total_lessons":           course.total_lessons if course else None,
            "total_modules":           module_count,
            "total_chapters":          chapter_count,
            "progress_percent":        en.progress_percent,
            "status":                  en.status,
            "instructor_name":         instructor.name if instructor else classroom.instructor_name,
            "instructor_email":        instructor.email if instructor else None,
            "enrolled_students_count": enrolled_count,
        })

    return result


# -------------------------------------------------------------------
# 4. LIVE CLASSES
# GET /dashboard/student/live-classes
# -------------------------------------------------------------------
@router.get("/live-classes")
def live_classes(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    require_student(current_user)
    user_id = current_user["user_id"]

    enrollments   = db.query(Enrollment).filter(Enrollment.user_id == user_id).all()
    classroom_ids = [e.classroom_id for e in enrollments]

    if not classroom_ids:
        return []

    sessions = (
        db.query(ClassSession)
        .join(Classroom)
        .filter(
            Classroom.id.in_(classroom_ids),
            ClassSession.status == "live"
        ).all()
    )

    result = []
    for s in sessions:
        classroom  = db.query(Classroom).filter(Classroom.id == s.classroom_id).first()
        course     = db.query(Course).filter(Course.id == classroom.course_id).first() if classroom else None
        instructor = None
        if classroom and classroom.instructor_id:
            instructor = db.query(User).filter(User.id == classroom.instructor_id).first()

        result.append({
            "session_id":      s.id,
            "course_name":     course.name if course else None,
            "course_code":     course.course_code if course else None,
            "batch_name":      classroom.batch_name if classroom else None,
            "room_name":       classroom.room_name if classroom else None,
            "join_url":        s.join_url,
            "start_time":      s.start_time.strftime("%Y-%m-%d %I:%M %p") if s.start_time else None,
            "status":          s.status,
            "instructor_name": instructor.name if instructor else (classroom.instructor_name if classroom else None),
        })

    return result


# -------------------------------------------------------------------
# 5. ATTENDANCE (summary + calendar + recent classes)
# GET /dashboard/student/attendance
# -------------------------------------------------------------------
@router.get("/attendance")
def attendance_overview(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    require_student(current_user)
    user_id = current_user["user_id"]

    # ── totals ────────────────────────────────────────────────────
    total_classes = db.query(SessionParticipant).filter(
        SessionParticipant.user_id == user_id,
        SessionParticipant.status.in_(["present", "absent", "late"])
    ).count()

    present_classes = db.query(SessionParticipant).filter(
        SessionParticipant.user_id == user_id,
        SessionParticipant.status.in_(["present", "late"])
    ).count()

    absent_classes = db.query(SessionParticipant).filter(
        SessionParticipant.user_id == user_id,
        SessionParticipant.status == "absent"
    ).count()

    percentage = (
        round((present_classes / total_classes) * 100, 1)
        if total_classes > 0 else 0.0
    )

    # ── calendar data (last 30 days) ──────────────────────────────
    participants = (
        db.query(SessionParticipant)
        .filter(SessionParticipant.user_id == user_id)
        .all()
    )

    # Build a map: date_str → status (first record wins per day)
    date_status_map: dict[str, str] = {}
    for p in participants:
        session = db.query(ClassSession).filter(ClassSession.id == p.session_id).first()
        if session and session.start_time:
            date_str = session.start_time.strftime("%Y-%m-%d")
            if date_str not in date_status_map:
                # Normalise: late → present for calendar display
                date_status_map[date_str] = (
                    "present" if p.status in ("present", "late") else "absent"
                )

    today         = datetime.now()
    calendar_data = []
    for i in range(29, -1, -1):                       # oldest → newest
        d        = today - timedelta(days=i)
        date_str = d.strftime("%Y-%m-%d")
        # Only mark days that actually had a session; others are "no_class"
        calendar_data.append({
            "date":   date_str,
            "status": date_status_map.get(date_str, "no_class"),
        })

    # ── recent 5 classes ─────────────────────────────────────────
    recent_parts = (
        db.query(SessionParticipant)
        .filter(SessionParticipant.user_id == user_id)
        .order_by(SessionParticipant.id.desc())
        .limit(5)
        .all()
    )

    recent_classes = []
    for p in recent_parts:
        session   = db.query(ClassSession).filter(ClassSession.id == p.session_id).first()
        classroom = db.query(Classroom).filter(Classroom.id == session.classroom_id).first() if session else None
        course    = db.query(Course).filter(Course.id == classroom.course_id).first() if classroom else None

        if session and session.start_time:
            recent_classes.append({
                "class_id": session.id,
                "title":    course.name if course else "Unknown Class",
                "date":     session.start_time.strftime("%Y-%m-%d"),
                "time":     session.start_time.strftime("%I:%M %p"),
                "status":   "present" if p.status in ("present", "late") else "absent",
            })

    return {
        "stats": {
            "total_classes":   total_classes,
            "present_classes": present_classes,
            "absent_classes":  absent_classes,
            "percentage":      percentage,
        },
        "calendar_data":  calendar_data,
        "recent_classes": recent_classes,
    }


# -------------------------------------------------------------------
# 6. MY ASSIGNMENTS (full list)
# GET /dashboard/student/assignments
# -------------------------------------------------------------------
@router.get("/assignments")
def my_assignments(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    require_student(current_user)
    user_id = current_user["user_id"]

    enrollments = db.query(Enrollment).filter(Enrollment.user_id == user_id).all()

    result = []
    seen   = set()

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
                AssignmentSubmission.assignment_id    == assignment.id,
                AssignmentSubmission.student_user_id  == user_id
            ).first()

            # Derive display status
            if submission:
                if submission.status == "graded":
                    display_status = "completed"
                elif submission.status == "submitted":
                    display_status = "submitted"
                else:
                    display_status = submission.status
            else:
                if assignment.due_date and assignment.due_date < datetime.now():
                    display_status = "overdue"
                else:
                    display_status = "pending"

            result.append({
                "assignment_id":  assignment.id,
                "title":          assignment.title,
                "description":    assignment.description,
                "objective":      assignment.objective,
                "course_name":    course.name if course else None,
                "course_code":    course.course_code if course else None,
                "module_name":    module.title if module else None,
                "batch_name":     assignment.batch_name,
                "due_date":       assignment.due_date.strftime("%Y-%m-%d") if assignment.due_date else None,
                "status":         display_status,
                "submitted_at":   (
                    submission.submitted_at.strftime("%Y-%m-%d %H:%M")
                    if submission and submission.submitted_at else None
                ),
                "grade":          submission.grade if submission else None,
                "feedback":       submission.feedback if submission else None,
            })

    # Sort: overdue first, then by due_date ascending
    priority = {"overdue": 0, "pending": 1, "submitted": 2, "completed": 3}
    result.sort(key=lambda x: (priority.get(x["status"], 9), x["due_date"] or ""))

    return result


# -------------------------------------------------------------------
# 7. ASSIGNMENTS DASHBOARD WIDGET (top 10)
# GET /dashboard/student/assignments/dashboard
# -------------------------------------------------------------------
@router.get("/assignments/dashboard")
def dashboard_assignments_widget(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    require_student(current_user)
    user_id = current_user["user_id"]

    enrollments = db.query(Enrollment).filter(
        Enrollment.user_id == user_id,
        Enrollment.status  == "ongoing"
    ).all()

    classroom_ids = [e.classroom_id for e in enrollments]
    classrooms    = db.query(Classroom).filter(Classroom.id.in_(classroom_ids)).all() if classroom_ids else []

    # Map course_id → Course
    course_map: dict[int, Course] = {}
    for cl in classrooms:
        if cl.course_id not in course_map:
            course = db.query(Course).filter(Course.id == cl.course_id).first()
            if course:
                course_map[cl.course_id] = course

    if not course_map:
        return {"data": []}

    assignments = db.query(Assignment).filter(
        Assignment.course_id.in_(list(course_map.keys()))
    ).all()

    sub_map: dict[int, AssignmentSubmission] = {
        s.assignment_id: s
        for s in db.query(AssignmentSubmission).filter(
            AssignmentSubmission.student_user_id == user_id,
            AssignmentSubmission.assignment_id.in_([a.id for a in assignments])
        ).all()
    }

    data = []
    for a in assignments:
        course = course_map.get(a.course_id)
        if not course:
            continue

        sub = sub_map.get(a.id)
        if sub:
            if sub.status == "graded":
                status = "completed"
            elif sub.status == "submitted":
                status = "submitted"
            else:
                status = "in_progress"
            grade = sub.grade
        else:
            status = "overdue" if (a.due_date and a.due_date < datetime.now()) else "pending"
            grade  = None

        data.append({
            "assignment_id": a.id,
            "course_code":   course.course_code,
            "course_name":   course.name,
            "title":         a.title,
            "due_date":      a.due_date.strftime("%Y-%m-%d") if a.due_date else None,
            "status":        status,
            "grade":         grade,
        })

    data.sort(key=lambda x: x["due_date"] or "")
    return {"data": data[:10]}


# -------------------------------------------------------------------
# 8. MY TESTS
# GET /dashboard/student/tests
# -------------------------------------------------------------------
@router.get("/tests")
def my_tests(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    require_student(current_user) # Using your existing check_student helper
    user_id = current_user["user_id"]

    enrollments = db.query(Enrollment).filter(Enrollment.user_id == user_id).all()

    result = []
    seen = set()

    for en in enrollments:
        classroom = db.query(Classroom).filter(Classroom.id == en.classroom_id).first()
        if not classroom:
            continue

        tests = db.query(Test).filter(
            Test.course_id  == classroom.course_id,
            Test.batch_name == classroom.batch_name
        ).all()

        for test in tests:
            if test.id in seen:
                continue
            seen.add(test.id)

            course = db.query(Course).filter(Course.id == test.course_id).first()
            module = db.query(Module).filter(Module.id == test.module_id).first()

            # ── FETCH QUESTION COUNT ───────────────────────────────────────
            # This directly gets the count of questions linked to this test
            total_questions = db.query(Question).filter(Question.test_id == test.id).count()

            submission = db.query(TestSubmission).filter(
                TestSubmission.test_id          == test.id,
                TestSubmission.student_user_id  == user_id
            ).first()

            result.append({
                "test_id":          test.id,
                "title":            test.title,
                "description":      test.description,
                "course_name":      course.name if course else None,
                "course_code":      course.course_code if course else None,
                "module_name":      module.title if module else None,
                "batch_name":       test.batch_name,
                
                # Added field here:
                "total_questions":  total_questions,
                
                "duration_minutes": getattr(test, "duration_minutes", 60) or 60,
                "start_time":       test.start_time.strftime("%Y-%m-%d %I:%M %p") if test.start_time else None,
                "end_time":         test.end_time.strftime("%Y-%m-%d %I:%M %p") if test.end_time else None,
                "status":           submission.status if submission else "not_attended",
                "score_percentage": submission.score_percentage if submission else None,
                "obtained_marks":   submission.obtained_marks if submission else None,
                "total_marks":      submission.total_marks if submission else None,
                "is_passed":        submission.is_passed if submission else None,
            })

    return result
# -------------------------------------------------------------------
# 9. START TEST — returns all questions (no correct answers leaked)
# GET /dashboard/student/tests/{test_id}/start
# -------------------------------------------------------------------
@router.get("/tests/{test_id}/start")
def start_test(
    test_id: int,
    db: Session  = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    require_student(current_user)
    user_id = current_user["user_id"]

    # ── fetch test ────────────────────────────────────────────────
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    # ── check enrollment via classroom ───────────────────────────
    classroom = db.query(Classroom).filter(
        Classroom.course_id  == test.course_id,
        Classroom.batch_name == test.batch_name
    ).first()

    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom for this test not found")

    enrollment = db.query(Enrollment).filter(
        Enrollment.user_id     == user_id,
        Enrollment.classroom_id == classroom.id
    ).first()

    if not enrollment:
        raise HTTPException(status_code=403, detail="You are not enrolled in this test's course/batch")

    # ── check if already submitted ────────────────────────────────
    existing = db.query(TestSubmission).filter(
        TestSubmission.test_id         == test_id,
        TestSubmission.student_user_id == user_id
    ).first()

    if existing and existing.status == "submitted":
        raise HTTPException(status_code=400, detail="You have already submitted this test")

    # ── create / reuse in_progress submission row ─────────────────
    if not existing:
        submission = TestSubmission(
            test_id          = test_id,
            student_user_id  = user_id,
            status           = "in_progress",
            started_at       = datetime.utcnow(),
        )
        db.add(submission)
        db.commit()
        db.refresh(submission)
    else:
        submission = existing

    # ── fetch questions via relationship ──────────────────────────
    questions = db.query(Question).filter(Question.test_id == test_id).all()

    questions_data = []
    for q in questions:
        options = db.query(Option).filter(Option.question_id == q.id).all()

        questions_data.append({
            "question_id":    q.id,
            "text":           q.text,
            "question_type":  q.question_type,   # mcq | checkbox | short_answer | long_answer
            "marks":          q.marks,
            "options": [
                {
                    "option_id": opt.id,
                    "text":      opt.text,
                    # ❌ is_correct is intentionally NOT included
                }
                for opt in options
            ],
        })

    module = db.query(Module).filter(Module.id == test.module_id).first()

    return {
        "test_id":          test.id,
        "title":            test.title,
        "description":      test.description,
        "module_name":      module.title if module else None,
        "duration_minutes": getattr(test, "duration_minutes", 60) or 60,
        "start_time":       test.start_time.strftime("%Y-%m-%d %I:%M %p") if test.start_time else None,
        "end_time":         test.end_time.strftime("%Y-%m-%d %I:%M %p") if test.end_time else None,
        "total_questions":  len(questions_data),
        "total_marks":      sum(q["marks"] for q in questions_data),
        "submission_id":    submission.id,
        "questions":        questions_data,
    }


# -------------------------------------------------------------------
# 10. SUBMIT TEST
# POST /dashboard/student/tests/{test_id}/submit
# -------------------------------------------------------------------
@router.post("/tests/{test_id}/submit")
def submit_test(
    test_id: int,
    payload: TestSubmitRequest,
    db: Session  = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    require_student(current_user)
    user_id = current_user["user_id"]

    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    submission = db.query(TestSubmission).filter(
        TestSubmission.test_id         == test_id,
        TestSubmission.student_user_id == user_id
    ).first()

    if not submission:
        raise HTTPException(status_code=400, detail="Test not started. Call /start first")

    if submission.status == "submitted":
        raise HTTPException(status_code=400, detail="Test already submitted")

    # ── persist each answer & auto-grade MCQ / checkbox ──────────
    total_marks    = 0.0
    obtained_marks = 0.0

    for ans in payload.answers:
        question = db.query(Question).filter(Question.id == ans.question_id).first()
        if not question:
            continue

        total_marks += question.marks
        awarded      = 0.0

        if question.question_type == "mcq" and ans.selected_option_id:
            option = db.query(Option).filter(Option.id == ans.selected_option_id).first()
            if option and option.is_correct:
                awarded = question.marks

        elif question.question_type == "checkbox" and ans.selected_option_ids:
            correct_ids = {
                str(o.id)
                for o in db.query(Option).filter(
                    Option.question_id == question.id,
                    Option.is_correct  == True
                ).all()
            }
            selected_ids = set(ans.selected_option_ids.split(","))
            if selected_ids == correct_ids:
                awarded = question.marks

        # short_answer / long_answer → instructor grades manually (awarded = 0 for now)

        obtained_marks += awarded

        student_answer = StudentAnswer(
            submission_id       = submission.id,
            question_id         = ans.question_id,
            selected_option_id  = ans.selected_option_id,
            selected_option_ids = ans.selected_option_ids,
            text_answer         = ans.text_answer,
            awarded_marks       = awarded,
            max_marks           = question.marks,
        )
        db.add(student_answer)

    # ── update submission ─────────────────────────────────────────
    submission.status          = "submitted"
    submission.submitted_at    = datetime.utcnow()
    submission.obtained_marks  = obtained_marks
    submission.total_marks     = total_marks
    submission.score_percentage = (
        round((obtained_marks / total_marks) * 100, 2) if total_marks else 0
    )
    # passing threshold: 50 %
    submission.is_passed = submission.score_percentage >= 50

    db.commit()

    return {
        "message":          "Test submitted successfully",
        "obtained_marks":   obtained_marks,
        "total_marks":      total_marks,
        "score_percentage": submission.score_percentage,
        "is_passed":        submission.is_passed,
    }


# -------------------------------------------------------------------
# 11. LESSON DETAILS (video player page)
# GET /dashboard/student/courses/{course_id}/lessons/{lesson_id}
# -------------------------------------------------------------------
@router.get("/courses/{course_id}/lessons/{lesson_id}")
def lesson_details(
    course_id: int,
    lesson_id: int,
    db: Session  = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    require_student(current_user)
    user_id = current_user["user_id"]

    chapter = db.query(Chapter).filter(Chapter.id == lesson_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Lesson not found")

    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    module = db.query(Module).filter(Module.id == chapter.module_id).first()

    # Check enrollment
    classroom = db.query(Classroom).filter(Classroom.course_id == course_id).first()
    if classroom:
        enrollment = db.query(Enrollment).filter(
            Enrollment.user_id      == user_id,
            Enrollment.classroom_id == classroom.id
        ).first()
        if not enrollment:
            raise HTTPException(status_code=403, detail="Not enrolled in this course")

    # Fetch attached resources from ChapterResource table
    db_resources = db.query(ChapterResource).filter(
        ChapterResource.chapter_id == chapter.id
    ).all()

    resources = [
        {
            "resource_id": r.id,
            "file_name":   r.file_name,
            "file_path":   r.file_path,
            "file_size":   r.file_size,
            "uploaded_at": r.uploaded_at.strftime("%Y-%m-%d") if r.uploaded_at else None,
        }
        for r in db_resources
    ]

    # Navigate to prev / next chapter within the same module
    all_chapters = (
        db.query(Chapter)
        .filter(Chapter.module_id == chapter.module_id)
        .order_by(Chapter.order)
        .all()
    )
    chapter_ids  = [c.id for c in all_chapters]
    current_idx  = chapter_ids.index(chapter.id) if chapter.id in chapter_ids else -1

    prev_lesson  = chapter_ids[current_idx - 1] if current_idx > 0 else None
    next_lesson  = chapter_ids[current_idx + 1] if current_idx < len(chapter_ids) - 1 else None

    return {
        "lesson_id":      chapter.id,
        "title":          chapter.title,
        "order":          chapter.order,
        "class_content":  chapter.class_content,
        "key_topics":     chapter.key_topics,
        "module_id":      module.id if module else None,
        "module_name":    module.title if module else None,
        "course_id":      course.id,
        "course_name":    course.name,
        "resources":      resources,
        "prev_lesson_id": prev_lesson,
        "next_lesson_id": next_lesson,
    }


# -------------------------------------------------------------------
# 12. PROFILE SUMMARY
# GET /dashboard/student/profile-summary
# -------------------------------------------------------------------
@router.get("/profile-summary")
def profile_summary(
    db: Session  = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    require_student(current_user)
    student_id = current_user["user_id"]

    user    = db.query(User).filter(User.id == student_id).first()
    profile = db.query(StudentInformation).filter(StudentInformation.user_id == student_id).first()

    enrollments   = db.query(Enrollment).filter(
        Enrollment.user_id == student_id,
        Enrollment.status  == "ongoing"
    ).all()

    classroom_ids = [e.classroom_id for e in enrollments]
    classrooms    = (
        db.query(Classroom).filter(Classroom.id.in_(classroom_ids)).all()
        if classroom_ids else []
    )
    course_ids = list({c.course_id for c in classrooms if c.course_id})

    # ── per-course breakdown ──────────────────────────────────────
    courses_data   = []
    total_modules  = 0
    total_chapters = 0

    for course_id in course_ids:
        course  = db.query(Course).filter(Course.id == course_id).first()
        modules = db.query(Module).filter(Module.course_id == course_id).all()

        m_count = len(modules)
        c_count = sum(len(m.chapters) for m in modules)

        total_modules  += m_count
        total_chapters += c_count

        courses_data.append({
            "course_id":       course.id,
            "course_code":     course.course_code,
            "course_name":     course.name,
            "duration_months": course.duration_months,
            "module_count":    m_count,
            "chapter_count":   c_count,
        })

    # ── attendance ────────────────────────────────────────────────
    total_classes = db.query(ClassSession).filter(
        ClassSession.classroom_id.in_(classroom_ids)
    ).count() if classroom_ids else 0

    attended_classes = db.query(SessionParticipant).filter(
        SessionParticipant.user_id  == student_id,
        SessionParticipant.status.in_(["present", "late"])
    ).count()

    attendance_percentage = (
        round((attended_classes / total_classes) * 100, 2)
        if total_classes > 0 else 0
    )

    # ── assignments ───────────────────────────────────────────────
    assignments = db.query(Assignment).filter(
        Assignment.course_id.in_(course_ids)
    ).all() if course_ids else []

    submissions = db.query(AssignmentSubmission).filter(
        AssignmentSubmission.student_user_id == student_id
    ).all()
    submitted_ids = {s.assignment_id for s in submissions}

    pending_assignments = sum(1 for a in assignments if a.id not in submitted_ids)

    # ── tests ─────────────────────────────────────────────────────
    tests = db.query(Test).filter(
        Test.course_id.in_(course_ids)
    ).all() if course_ids else []

    test_submissions = db.query(TestSubmission).filter(
        TestSubmission.student_user_id == student_id
    ).all()

    submitted_tests = sum(1 for t in test_submissions if t.status == "submitted")
    passed_tests    = sum(1 for t in test_submissions if t.is_passed is True)
    failed_tests    = sum(1 for t in test_submissions if t.is_passed is False)

    scores  = [t.score_percentage for t in test_submissions if t.score_percentage is not None]
    avg_score = round(sum(scores) / len(scores), 2) if scores else 0

    return {
        "profile": {
            "user_id":       user.id,
            "student_id":    user.student_id,
            "name":          user.name,
            "email":         user.email,
            "phone":         profile.phone_number if profile else None,
            "profile_image": profile.profile_image_url if profile else None,
            "status":        profile.account_status if profile else "active",
        },
        "summary": {
            "courses":              len(course_ids),
            "modules":              total_modules,
            "chapters":             total_chapters,
            "classes_total":        total_classes,
            "classes_attended":     attended_classes,
            "attendance_percentage": attendance_percentage,
            "assignments_total":    len(assignments),
            "assignments_pending":  pending_assignments,
            "assignments_submitted": len(submissions),
            "tests_total":          len(tests),
            "tests_attempted":      submitted_tests,
            "tests_passed":         passed_tests,
            "tests_failed":         failed_tests,
            "average_test_score":   avg_score,
        },
        "courses": courses_data,
    }
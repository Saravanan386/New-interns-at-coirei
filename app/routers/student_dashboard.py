from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
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
from app.models.registration_profile import StudentInformation


router = APIRouter(prefix="/dashboard/student", tags=["Student Dashboard"])


def require_student(current_user: dict):
    if current_user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Student access only")
    return True


# -------------------------------------------------------------------
# 1. DASHBOARD ASSIGNMENTS WIDGET (NEW)
# GET /assignments/dashboard
# -------------------------------------------------------------------
@router.get("/assignments/dashboard")
def dashboard_assignments(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    require_student(current_user)
    user_id = current_user["user_id"]

    enrollments = db.query(Enrollment).filter(
        Enrollment.user_id == user_id,
        Enrollment.status == "ongoing"
    ).all()

    course_ids = [e.classroom_id for e in enrollments]
    classrooms = db.query(Classroom).filter(Classroom.id.in_(course_ids)).all()
    course_map = {}
    for cl in classrooms:
        course = db.query(Course).filter(Course.id == cl.course_id).first()
        if course:
            course_map[cl.course_id] = course

    assignments = db.query(Assignment).filter(
        Assignment.course_id.in_([c.id for c in course_map.values()])
    ).all()

    submissions = db.query(AssignmentSubmission).filter(
        AssignmentSubmission.student_user_id == user_id,
        AssignmentSubmission.assignment_id.in_([a.id for a in assignments])
    ).all()
    submission_map = {s.assignment_id: s for s in submissions}

    data = []
    for a in assignments:
        course = course_map.get(a.course_id)
        if not course:
            continue

        sub = submission_map.get(a.id)
        if sub:
            status = sub.status if sub.status in ["in_progress", "completed", "overdue"] else "in_progress"
            grade = sub.grade if sub.grade is not None else None
        else:
            # Determine status based on due_date
            if a.due_date and a.due_date < datetime.now():
                status = "overdue"
            else:
                status = "in_progress"
            grade = None

        data.append({
            "assignment_id": a.id,
            "course_code": course.course_code,
            "course_name": course.name,
            "title": a.title,
            "due_date": a.due_date.strftime("%Y-%m-%d") if a.due_date else None,
            "status": status,
            "grade": grade
        })

    # Sort by due_date
    data.sort(key=lambda x: x["due_date"] or "")

    return {"data": data[:10]}  # Top 10 for dashboard


# -------------------------------------------------------------------
# 2. STUDENT ATTENDANCE OVERVIEW (ENHANCED + NEW STRUCTURE)
# GET /student/attendance
# -------------------------------------------------------------------
@router.get("/attendance")
def attendance_overview(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    require_student(current_user)
    user_id = current_user["user_id"]

    total_classes = db.query(SessionParticipant).filter(
        SessionParticipant.user_id == user_id,
        SessionParticipant.status.in_(["present", "absent"])
    ).count()

    attended = db.query(SessionParticipant).filter(
        SessionParticipant.user_id == user_id,
        SessionParticipant.status == "present"
    ).count()

    percentage = round((attended / total_classes) * 100, 1) if total_classes > 0 else 0.0

    # Calendar data: last 30 days
    from sqlalchemy import text
    calendar_data = []
    participants = db.query(SessionParticipant).filter(
        SessionParticipant.user_id == user_id
    ).all()

    date_status_map = {}
    for p in participants:
        # Assume ClassSession has start_time with date
        session = db.query(ClassSession).filter(ClassSession.id == p.session_id).first()
        if session and session.start_time:
            date_str = session.start_time.strftime("%Y-%m-%d")
            if date_str not in date_status_map:
                date_status_map[date_str] = p.status

    # Get last 30 days
    from datetime import timedelta
    today = datetime.now()
    for i in range(30):
        date = today - timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        status = date_status_map.get(date_str, "absent")
        calendar_data.append({"date": date_str, "status": status})

    calendar_data.reverse()

    # Recent classes (last 5)
    recent_classes = []
    sessions_part = db.query(SessionParticipant).filter(
        SessionParticipant.user_id == user_id
    ).order_by(SessionParticipant.id.desc()).limit(5).all()

    for p in sessions_part:
        session = db.query(ClassSession).filter(ClassSession.id == p.session_id).first()
        classroom = db.query(Classroom).filter(Classroom.id == session.classroom_id).first() if session else None
        course = db.query(Course).filter(Course.id == classroom.course_id).first() if classroom else None

        if session:
            date_str = session.start_time.strftime("%Y-%m-%d")
            time_str = session.start_time.strftime("%I:%M %p")
            recent_classes.append({
                "class_id": session.id,
                "title": course.name if course else "Unknown Class",
                "date": date_str,
                "time": time_str,
                "status": p.status if p.status == "present" else "attended" if p.status == "late" else "absent"
            })

    return {
        "stats": {
            "total_classes": total_classes,
            "attended": attended,
            "percentage": percentage
        },
        "calendar_data": calendar_data,
        "recent_classes": recent_classes
    }


# -------------------------------------------------------------------
# 3. COURSE LESSON DETAILS (VIDEO PLAYER PAGE) (NEW)
# GET /courses/{courseId}/lessons/{lessonId}
# -------------------------------------------------------------------
@router.get("/courses/{course_id}/lessons/{lesson_id}")
def lesson_details(
    course_id: int,
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    require_student(current_user)

    chapter = db.query(Chapter).filter(Chapter.id == lesson_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Lesson not found")

    module = db.query(Module).filter(Module.id == chapter.module_id).first()
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Assume video_url is stored in Chapter or you can derive from CDN
    video_url = chapter.video_url or f"https://your-cdn.com/videos/{chapter.title.lower().replace(' ', '-')}.mp4"

    resources = []
    if chapter.resources:
        # Assume resources is a list of dicts or you have a separate Resource model
        for r in chapter.resources:
            resources.append({
                "resource_id": r.get("id", 0),
                "file_name": r.get("file_name", "Unknown"),
                "file_type": r.get("file_type", "pdf")
            })

    return {
        "lesson_id": chapter.id,
        "title": chapter.title,
        "video_url": video_url,
        "duration_minutes": chapter.duration_minutes or 45,
        "description": chapter.description or f"In this lesson, we will cover {chapter.title}.",
        "transcript": chapter.transcript or "Hello everyone, welcome to...",
        "notes_html": chapter.notes_html or "<p>Key takeaways...</p>",
        "resources": resources
    }


# -------------------------------------------------------------------
# 4. FETCH TEST QUESTIONS (NEW)
# GET /tests/{test_id}/start
# -------------------------------------------------------------------
@router.get("/tests/{test_id}/start")
def start_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    require_student(current_user)

    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    # Ensure user is enrolled in this test's course
    enrollments = db.query(Enrollment).filter(
        Enrollment.user_id == current_user["user_id"],
        Enrollment.classroom_id == test.classroom_id
    ).first()
    if not enrollments:
        raise HTTPException(status_code=403, detail="Not enrolled in this test's course")

    # Fetch questions (assume Test has a questions JSON or separate Question model)
    # Here we assume test.questions is a list of dicts
    questions = []
    for q in test.questions:
        options = [
            {"id": opt["id"], "text": opt["text"]}
            for opt in q.get("options", [])
        ]
        questions.append({
            "id": q["id"],
            "text": q["text"],
            "options": options
        })

    module = db.query(Module).filter(Module.id == test.module_id).first()

    return {
        "id": test.id,
        "title": test.title,
        "module_name": module.title if module else "Unknown Module",
        "duration_minutes": test.duration_minutes or 60,
        "questions": questions
    }


# -------------------------------------------------------------------
# 5. SUBMIT TEST ANSWERS (NEW)
# POST /tests/{test_id}/submit
# -------------------------------------------------------------------
@router.post("/tests/{test_id}/submit")
def submit_test(
    test_id: int,
    answers: list,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    require_student(current_user)

    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    # Create or update TestSubmission
    submission = db.query(TestSubmission).filter(
        TestSubmission.test_id == test_id,
        TestSubmission.student_user_id == current_user["user_id"]
    ).first()

    if not submission:
        submission = TestSubmission(
            test_id=test_id,
            student_user_id=current_user["user_id"],
            status="submitted",
            answers=answers
        )
        db.add(submission)
    else:
        submission.status = "submitted"
        submission.answers = answers

    db.commit()

    return {"message": "Test submitted successfully"}


# -------------------------------------------------------------------
# EXISTING: DASHBOARD HOME (ENHANCED)
# GET /home
# -------------------------------------------------------------------
@router.get("/home")
def dashboard_home(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    require_student(current_user)
    user_id = current_user["user_id"]

    user = db.query(User).filter(User.id == user_id).first()
    profile = db.query(StudentInformation).filter(StudentInformation.user_id == user_id).first()

    enrollments = db.query(Enrollment).filter(Enrollment.user_id == user_id).all()
    classroom_ids = [e.classroom_id for e in enrollments]
    classrooms = db.query(Classroom).filter(Classroom.id.in_(classroom_ids)).all() if classroom_ids else []
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

    assignments_total = assignments_pending = assignments_submitted = tests_total = tests_attempted = average_score = 0

    if course_ids:
        assignments_total = db.query(Assignment).filter(Assignment.course_id.in_(course_ids)).count()
        tests_total = db.query(Test).filter(Test.course_id.in_(course_ids)).count()

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


# -------------------------------------------------------------------
# EXISTING: MY COURSES (ENHANCED WITH INSTRUCTOR & EXTRA DATA)
# GET /courses
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

        # Get instructor (assume Course has instructor_id or Classroom has it)
        instructor = None
        if course and course.instructor_id:
            instructor = db.query(User).filter(User.id == course.instructor_id).first()
        elif classroom and classroom.instructor_id:
            instructor = db.query(User).filter(User.id == classroom.instructor_id).first()

        instructor_name = instructor.name if instructor else None
        instructor_email = instructor.email if instructor else None

        module_count = db.query(Module).filter(Module.course_id == classroom.course_id).count()
        chapter_count = db.query(Chapter).join(Module).filter(Module.course_id == classroom.course_id).count()

        enrolled_students = db.query(Enrollment).filter(
            Enrollment.classroom_id == classroom.id
        ).count()

        result.append({
            "course_id": course.id if course else classroom.course_id,
            "course_name": course.name if course else None,
            "course_code": course.course_code if course else None,
            "batch_name": classroom.batch_name,
            "room_name": classroom.room_name,
            "duration_months": course.duration_months if course else None,
            "total_modules": module_count,
            "total_chapters": chapter_count,
            "progress_percent": en.progress_percent,
            "status": en.status,
            "course_description": course.description if course else None,
            "thumbnail_url": course.thumbnail_url if course else None,
            "instructor_name": instructor_name,
            "instructor_email": instructor_email,
            "enrolled_students_count": enrolled_students
        })

    return result


# -------------------------------------------------------------------
# EXISTING: MY ASSIGNMENTS (ENHANCED WITH GRADE)
# GET /assignments
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

            status = submission.status if submission else "pending"
            grade = submission.grade if submission and submission.grade is not None else None

            # Map status to dashboard widget statuses
            if status == "submitted":
                status = "in_progress"
            elif status == "graded":
                status = "completed"
            elif assignment.due_date and assignment.due_date < datetime.now() and not submission:
                status = "overdue"

            result.append({
                "assignment_id": assignment.id,
                "title": assignment.title,
                "course_name": course.name if course else None,
                "course_code": course.course_code if course else None,
                "module_name": module.title if module else None,
                "batch_name": assignment.batch_name,
                "due_date": assignment.due_date.strftime("%Y-%m-%d") if assignment.due_date else None,
                "status": status,
                "submitted_at": submission.submitted_at.strftime("%Y-%m-%d %H:%M") if submission and submission.submitted_at else None,
                "grade": grade
            })

    return result


# -------------------------------------------------------------------
# EXISTING: MY TESTS
# GET /tests
# -------------------------------------------------------------------
@router.get("/tests")
def my_tests(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    require_student(current_user)
    user_id = current_user["user_id"]

    enrollments = db.query(Enrollment).filter(Enrollment.user_id == user_id).all()

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
                "course_code": course.course_code if course else None,
                "module_name": module.title if module else None,
                "status": submission.status if submission else "not_attended",
                "score_percentage": submission.score_percentage if submission else None,
                "is_passed": submission.is_passed if submission else None,
                "duration_minutes": test.duration_minutes or 60
            })

    return result


# -------------------------------------------------------------------
# EXISTING: LIVE CLASSES
# GET /live-classes
# -------------------------------------------------------------------
@router.get("/live-classes")
def live_classes(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
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

        instructor = None
        if course and course.instructor_id:
            instructor = db.query(User).filter(User.id == course.instructor_id).first()

        result.append({
            "session_id": s.id,
            "course_name": course.name if course else None,
            "course_code": course.course_code if course else None,
            "batch_name": classroom.batch_name if classroom else None,
            "room_name": classroom.room_name if classroom else None,
            "join_url": s.join_url,
            "start_time": s.start_time.strftime("%Y-%m-%d %I:%M %p") if s.start_time else None,
            "status": s.status,
            "instructor_name": instructor.name if instructor else None
        })

    return result
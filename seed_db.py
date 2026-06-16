import os
import sys

sys.path.append(os.getcwd())

from app.database import SessionLocal  # noqa: E402
from app.models.classroom import Classroom  # noqa: E402
from app.models.course import Course  # noqa: E402
from app.models.enrollment import Enrollment  # noqa: E402
from app.models.instructor_enrollment import InstructorEnrollment  # noqa: E402
from app.models.user import User  # noqa: E402
from app.utils.security import hash_password  # noqa: E402

DEMO_INSTRUCTOR_EMAIL = "instructor@demo.com"
DEMO_INSTRUCTOR_PASSWORD = "Demo@12345"
DEMO_STUDENT_EMAIL = "student@demo.com"
DEMO_STUDENT_PASSWORD = "Demo@12345"

DEMO_COURSE_CODE = "DEMO101"
DEMO_COURSE_NAME = "AI / ML Frontier Demo"
DEMO_BATCH_NAME = "Batch-Demo"
DEMO_ROOM_NAME = "Demo_Conference_Room"


def _get_or_create_user(db, *, name: str, email: str, password: str, role: str):
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user

    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _get_or_create_course(db):
    course = db.query(Course).filter(Course.course_code == DEMO_COURSE_CODE).first()
    if course:
        return course

    course = Course(
        course_code=DEMO_COURSE_CODE,
        name=DEMO_COURSE_NAME,
        description="Demo course for the LMS + Jitsi self-host walkthrough.",
        duration_months=3,
        total_lessons=24,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


def _get_or_create_classroom(db, course_id: int, instructor: User):
    classroom = (
        db.query(Classroom)
        .filter(
            Classroom.course_id == course_id,
            Classroom.batch_name == DEMO_BATCH_NAME,
        )
        .first()
    )
    if classroom:
        return classroom

    classroom = Classroom(
        course_id=course_id,
        batch_name=DEMO_BATCH_NAME,
        room_name=DEMO_ROOM_NAME,
        instructor_id=instructor.id,
        instructor_name=instructor.name,
        batch_code="DEMO-BATCH",
        schedule_type="weekday",
        start_month="2026-06",
        class_days="Mon,Wed,Fri",
        start_time="10:00",
        end_time="11:30",
    )
    db.add(classroom)
    db.commit()
    db.refresh(classroom)
    return classroom


def _ensure_instructor_assignment(db, classroom: Classroom, instructor: User):
    existing = (
        db.query(InstructorEnrollment)
        .filter(
            InstructorEnrollment.user_id == instructor.id,
            InstructorEnrollment.classroom_id == classroom.id,
        )
        .first()
    )
    if existing:
        return existing

    assignment = InstructorEnrollment(
        user_id=instructor.id,
        classroom_id=classroom.id,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


def _ensure_student_enrollment(db, classroom: Classroom, student: User):
    existing = (
        db.query(Enrollment)
        .filter(
            Enrollment.user_id == student.id,
            Enrollment.classroom_id == classroom.id,
        )
        .first()
    )
    if existing:
        return existing

    enrollment = Enrollment(
        user_id=student.id,
        classroom_id=classroom.id,
        progress_percent=0,
        status="ongoing",
    )
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment


def seed():
    db = SessionLocal()
    try:
        instructor = _get_or_create_user(
            db,
            name="Demo Instructor",
            email=DEMO_INSTRUCTOR_EMAIL,
            password=DEMO_INSTRUCTOR_PASSWORD,
            role="instructor",
        )
        student = _get_or_create_user(
            db,
            name="Demo Student",
            email=DEMO_STUDENT_EMAIL,
            password=DEMO_STUDENT_PASSWORD,
            role="student",
        )
        course = _get_or_create_course(db)
        classroom = _get_or_create_classroom(db, course.id, instructor)
        _ensure_instructor_assignment(db, classroom, instructor)
        _ensure_student_enrollment(db, classroom, student)

        print("Demo data seeded successfully.")
        print(f"Instructor login: {DEMO_INSTRUCTOR_EMAIL} / {DEMO_INSTRUCTOR_PASSWORD}")
        print(f"Student login:    {DEMO_STUDENT_EMAIL} / {DEMO_STUDENT_PASSWORD}")
        print(f"Classroom:        {classroom.batch_name} ({classroom.room_name})")
    except Exception as exc:
        db.rollback()
        print(f"Error during seeding: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()

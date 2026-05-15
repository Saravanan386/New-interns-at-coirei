# app/routers/enroll.py
"""
Student Enrollment API
- Auto-generates student ID from course name prefix + sequential number
- Auto-generates a random password
- Creates user (role=student) in users table
- Creates enrollment record in enrollments table
- Returns credentials so instructor can share with the student
"""

import random
import string
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.classroom import Classroom
from app.utils.security import get_current_user, hash_password

router = APIRouter(prefix="/enroll", tags=["Enrollment"])


# ---------------------------------------------------------------------------
# Helper: generate student ID from course name
# Format: first letters of each word (max 2) + 3-digit sequence
# e.g. "Advanced AI" → "AA001", "Python" → "PY001"
# ---------------------------------------------------------------------------
def generate_student_id(course_name: str, db: Session) -> str:
    words = course_name.strip().split()
    if len(words) >= 2:
        prefix = (words[0][0] + words[1][0]).upper()
    else:
        prefix = course_name[:2].upper()

    # Count existing students whose student_id starts with this prefix
    existing = db.query(User).filter(
        User.student_id.like(f"{prefix}%")
    ).count()

    next_num = existing + 1
    return f"{prefix}{next_num:03d}"   # e.g. AI001, AI002


# ---------------------------------------------------------------------------
# Helper: generate a random 8-character password
# ---------------------------------------------------------------------------
def generate_password(length: int = 8) -> str:
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))


# ---------------------------------------------------------------------------
# GET /enroll/courses  — list all courses for the dropdown
# ---------------------------------------------------------------------------
@router.get("/courses")
def list_courses(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    courses = db.query(Course).all()
    return [
        {"course_id": c.id, "course_name": c.name}
        for c in courses
    ]


# ---------------------------------------------------------------------------
# GET /enroll/batches  — list available batches for a course (for dropdown)
# ---------------------------------------------------------------------------
@router.get("/batches")
def list_batches_for_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    classrooms = (
        db.query(Classroom.batch_name)
        .filter(Classroom.course_id == course_id, Classroom.batch_name != None)
        .distinct()
        .all()
    )

    batches = [row.batch_name for row in classrooms if row.batch_name]
    return {
        "course_id": course_id,
        "course_name": course.name,
        "batches": batches
    }


# ---------------------------------------------------------------------------
# GET /enroll/generate-id  — preview the next student ID for a course
# ---------------------------------------------------------------------------
@router.get("/generate-id")
def get_next_student_id(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    student_id = generate_student_id(course.name, db)
    return {"student_id": student_id, "course_name": course.name}


# ---------------------------------------------------------------------------
# POST /enroll/student  — create student + enroll them
# ---------------------------------------------------------------------------
@router.post("/student")
def enroll_student(
    course_id: int,
    batch_name: str,
    first_name: str,
    last_name: str,
    email: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Only instructor or admin can enroll students
    if current_user.get("role") not in ["instructor", "admin"]:
        raise HTTPException(status_code=403, detail="Only instructors can enroll students")

    # Check course exists
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Validate batch belongs to the course
    valid_batch = (
        db.query(Classroom)
        .filter(Classroom.course_id == course_id, Classroom.batch_name == batch_name)
        .first()
    )
    if not valid_batch:
        raise HTTPException(
            status_code=400,
            detail=f"Batch '{batch_name}' does not exist for this course. Use GET /enroll/batches to see available batches."
        )

    # Check email not already taken
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Check not already enrolled in same course+batch
    if existing_user:
        already_enrolled = db.query(Enrollment).filter(
            Enrollment.user_id == existing_user.id,
            Enrollment.course_id == course_id,
            Enrollment.batch_name == batch_name
        ).first()
        if already_enrolled:
            raise HTTPException(status_code=400, detail="Student already enrolled in this batch")

    # Auto-generate student ID and password
    student_id = generate_student_id(course.name, db)
    raw_password = generate_password()
    full_name = f"{first_name} {last_name}"

    # Create user
    user = User(
        name=full_name,
        email=email,
        password_hash=hash_password(raw_password),
        role="student",
        student_id=student_id
    )
    db.add(user)
    db.flush()   # get user.id without committing

    # Create enrollment
    enrollment = Enrollment(
        user_id=user.id,
        course_id=course_id,
        batch_name=batch_name,
        status="ongoing",
        progress_percent=0
    )
    db.add(enrollment)
    db.commit()
    db.refresh(user)
    db.refresh(enrollment)

    return {
        "message": "Student enrolled successfully",
        "student_id": student_id,
        "user_id": user.id,
        "name": full_name,
        "email": email,
        "auto_generated_password": raw_password,   # ← share this with the student
        "course": course.name,
        "batch_name": batch_name,
        "enrollment_id": enrollment.id
    }


# ---------------------------------------------------------------------------
# POST /enroll/reset-password  — generate a new password for a student
# ---------------------------------------------------------------------------
@router.post("/reset-password")
def reset_student_password(
    student_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Only instructor or admin can reset passwords
    if current_user.get("role") not in ["instructor", "admin"]:
        raise HTTPException(status_code=403, detail="Only instructors can reset student passwords")

    # Find student by student_id
    student = db.query(User).filter(
        User.student_id == student_id,
        User.role == "student"
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail=f"Student '{student_id}' not found")

    # Generate and save new password
    new_password = generate_password()
    student.password_hash = hash_password(new_password)
    db.commit()
    db.refresh(student)

    return {
        "message": "Password reset successfully",
        "student_id": student_id,
        "name": student.name,
        "email": student.email,
        "new_password": new_password   # ← share this with the student
    }

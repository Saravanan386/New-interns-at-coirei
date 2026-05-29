# app/routers/instructor_enroll.py
"""
Instructor Enrollment API
- Auto-generates instructor ID (INS001, INS002, …)
- Auto-generates a random password
- Creates user (role=instructor) in the users table
- Accepts multiple course+batch pairs in a single request
- Creates one InstructorEnrollment record per course+batch pair
- Returns credentials so admin can share with the instructor
"""

import random
import string
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.course import Course
from app.models.classroom import Classroom
from app.models.instructor_enrollment import InstructorEnrollment
from app.utils.security import get_current_user, hash_password

router = APIRouter(prefix="/instructor-enroll", tags=["Instructor Enrollment"])


# ---------------------------------------------------------------------------
# Pydantic schemas (inline – keeps the file self-contained)
# ---------------------------------------------------------------------------

class CourseBatchItem(BaseModel):
    """One course+batch assignment for the instructor."""
    course_id: int
    batch_name: str


class InstructorEnrollRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    course_batches: List[CourseBatchItem]   # ← multiple selections


# ---------------------------------------------------------------------------
# Helper: generate instructor ID  (INS001, INS002, …)
# ---------------------------------------------------------------------------
def generate_instructor_id(db: Session) -> str:
    existing = db.query(User).filter(
        User.student_id.like("INS%"),
        User.role == "instructor"
    ).count()
    next_num = existing + 1
    return f"INS{next_num:03d}"


# ---------------------------------------------------------------------------
# Helper: generate a random 8-character password
# ---------------------------------------------------------------------------
def generate_password(length: int = 8) -> str:
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=length))


# ---------------------------------------------------------------------------
# GET /instructor-enroll/courses  — list all courses for the dropdown
# ---------------------------------------------------------------------------
@router.get("/courses")
def list_courses(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    from app.models.course import Course as CourseModel
    courses = db.query(CourseModel).all()
    return [{"course_id": c.id, "course_name": c.name} for c in courses]


# ---------------------------------------------------------------------------
# GET /instructor-enroll/batches  — batches for a given course (dropdown)
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
    return {"course_id": course_id, "course_name": course.name, "batches": batches}


# ---------------------------------------------------------------------------
# GET /instructor-enroll/generate-id  — preview the next instructor ID
# ---------------------------------------------------------------------------
@router.get("/generate-id")
def get_next_instructor_id(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    instructor_id = generate_instructor_id(db)
    return {"instructor_id": instructor_id}


# ---------------------------------------------------------------------------
# POST /instructor-enroll/instructor  — create instructor + assign courses/batches
# ---------------------------------------------------------------------------
@router.post("/instructor")
def enroll_instructor(
    payload: InstructorEnrollRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # ---------------------------------------------------
    # ONLY ADMIN
    # ---------------------------------------------------
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admins can enroll instructors"
        )

    if not payload.course_batches:
        raise HTTPException(
            status_code=400,
            detail="At least one course+batch must be selected"
        )

    # ---------------------------------------------------
    # VALIDATE COURSE + BATCHES
    # ---------------------------------------------------
    for item in payload.course_batches:

        course = db.query(Course).filter(
            Course.id == item.course_id
        ).first()

        if not course:
            raise HTTPException(
                status_code=404,
                detail=f"Course ID {item.course_id} not found"
            )

        batch = db.query(Classroom).filter(
            Classroom.course_id == item.course_id,
            Classroom.batch_name == item.batch_name
        ).first()

        if not batch:
            raise HTTPException(
                status_code=400,
                detail=f"Batch '{item.batch_name}' not found"
            )

    # ---------------------------------------------------
    # CHECK EXISTING USER
    # ---------------------------------------------------
    existing_user = db.query(User).filter(
        User.email == payload.email
    ).first()

    # ---------------------------------------------------
    # EXISTING INSTRUCTOR
    # ---------------------------------------------------
    if existing_user:

        if existing_user.role != "instructor":
            raise HTTPException(
                status_code=400,
                detail="User already exists but is not an instructor"
            )

        user = existing_user
        instructor_id = user.student_id
        raw_password = None

    # ---------------------------------------------------
    # NEW INSTRUCTOR
    # ---------------------------------------------------
    else:

        instructor_id = generate_instructor_id(db)
        raw_password = generate_password()

        full_name = f"{payload.first_name} {payload.last_name}"

        user = User(
            name=full_name,
            email=payload.email,
            password_hash=hash_password(raw_password),
            role="instructor",
            student_id=instructor_id
        )

        db.add(user)
        db.flush()

    # ---------------------------------------------------
    # CREATE ENROLLMENTS
    # ---------------------------------------------------
    assigned = []

    for item in payload.course_batches:

        existing_assignment = db.query(
            InstructorEnrollment
        ).filter(
            InstructorEnrollment.user_id == user.id,
            InstructorEnrollment.course_id == item.course_id,
            InstructorEnrollment.batch_name == item.batch_name
        ).first()

        # skip duplicates
        if existing_assignment:
            continue

        enrollment = InstructorEnrollment(
            user_id=user.id,
            course_id=item.course_id,
            batch_name=item.batch_name
        )

        db.add(enrollment)

        assigned.append({
            "course_id": item.course_id,
            "batch_name": item.batch_name
        })

    db.commit()
    db.refresh(user)

    return {
        "message": "Instructor enrolled successfully",
        "instructor_id": instructor_id,
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
        "auto_generated_password": raw_password,
        "assigned_courses_batches": assigned
    }



    
# ---------------------------------------------------------------------------
# POST /instructor-enroll/reset-password  — generate new password for instructor
# ---------------------------------------------------------------------------
@router.post("/reset-password")
def reset_instructor_password(
    instructor_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user.get("role") not in ["admin"]:
        raise HTTPException(status_code=403, detail="Only admins can reset instructor passwords")

    instructor = db.query(User).filter(
        User.student_id == instructor_id,
        User.role == "instructor"
    ).first()
    if not instructor:
        raise HTTPException(status_code=404, detail=f"Instructor '{instructor_id}' not found")

    new_password = generate_password()
    instructor.password_hash = hash_password(new_password)
    db.commit()
    db.refresh(instructor)

    return {
        "message": "Password reset successfully",
        "instructor_id": instructor_id,
        "name": instructor.name,
        "email": instructor.email,
        "new_password": new_password
    }


# ---------------------------------------------------------------------------
# GET /instructor-enroll/list  — list all instructors with their assignments
# ---------------------------------------------------------------------------
@router.get("/list")
def list_instructors(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user.get("role") not in ["admin"]:
        raise HTTPException(status_code=403, detail="Only admins can view all instructors")

    instructors = db.query(User).filter(User.role == "instructor").all()
    result = []
    for inst in instructors:
        assignments = (
            db.query(InstructorEnrollment, Course)
            .join(Course, InstructorEnrollment.course_id == Course.id)
            .filter(InstructorEnrollment.user_id == inst.id)
            .all()
        )
        result.append({
            "instructor_id": inst.student_id,
            "user_id": inst.id,
            "name": inst.name,
            "email": inst.email,
            "course_batches": [
                {"course_id": enr.course_id, "course_name": course.name, "batch_name": enr.batch_name}
                for enr, course in assignments
            ]
        })
    return result

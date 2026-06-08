# app/routers/assignments.py
"""
Assignment API  (instructor creates, students submit)

Step 1 helpers  (dropdowns for the first screen):
  GET  /assignments/courses            → list courses
  GET  /assignments/batches?course_id  → batches for a course
  GET  /assignments/modules?course_id&batch_name → modules for course+batch

Step 2 — Create:
  POST /assignments/                   → create assignment (multipart/form-data: fields + optional files)
  POST /assignments/{id}/resources     → upload additional files to an existing assignment

Instructor views:
  GET  /assignments/                   → list all assignments (instructor)
  GET  /assignments/{id}               → get single assignment + resources
  PUT  /assignments/{id}               → edit assignment
  DELETE /assignments/{id}             → delete assignment
  GET  /assignments/{id}/submissions   → all student submissions for an assignment

Student views:
  GET  /assignments/my                 → all assignments for the logged-in student
  POST /assignments/{id}/submit        → submit text + optional file
  GET  /assignments/{id}/my-submission → view own submission

Instructor grading:
  PUT  /assignments/{id}/submissions/{sub_id}/grade  → assign grade + feedback
"""
from datetime import datetime, timezone

import os, shutil, uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import (
    APIRouter, Depends, HTTPException, UploadFile, File, Form
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.utils.security import get_current_user
from app.models.assignment import Assignment, AssignmentResource, AssignmentSubmission
from app.models.course import Course
from app.models.classroom import Classroom
from app.models.enrollment import Enrollment
from app.models.module import Module
from app.models.user import User
from app.schemas import (
    AssignmentCreate, AssignmentUpdate,
    AssignmentResponse, AssignmentResourceResponse,
    AssignmentSubmissionResponse, StudentAssignmentRow,
    StudentDashboardAssignmentItem,
)
from app.services.notifications import create_notification

router = APIRouter(prefix="/assignments", tags=["Assignments"])

UPLOAD_DIR = "uploads/assignments"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ── Role Helpers ──────────────────────────────────────────────────────────────

def require_instructor(current_user: dict):
    if current_user.get("role") != "instructor":
        raise HTTPException(status_code=403, detail="Instructor access required.")


def require_student(current_user: dict):
    if current_user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Student access required.")


def can_access_assignment(db: Session, assignment: Assignment, current_user: dict) -> bool:
    if current_user.get("role") == "instructor":
        return True

    if current_user.get("role") == "student":
        enrollment = (
            db.query(Enrollment)
            .join(Classroom, Classroom.id == Enrollment.classroom_id)
            .filter(
                Enrollment.user_id == current_user["user_id"],
                Classroom.course_id == assignment.course_id,
                Classroom.batch_name == assignment.batch_name,
                Enrollment.status == "ongoing",
            )
            .first()
        )
        return enrollment is not None

    return False


# ── Step 1 Dropdown Helpers ───────────────────────────────────────────────────

@router.get("/courses")
def list_courses(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Returns all courses for Step-1 Course Name dropdown."""
    courses = db.query(Course).all()
    return [{"course_id": c.id, "course_name": c.name} for c in courses]


@router.get("/batches")
def list_batches(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Returns available batches for the selected course (Step-1 Batch ID dropdown)."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    classrooms = (
        db.query(Classroom.batch_name)
        .filter(Classroom.course_id == course_id, Classroom.batch_name != None)
        .distinct()
        .all()
    )
    return {
        "course_id": course_id,
        "course_name": course.name,
        "batches": [row.batch_name for row in classrooms if row.batch_name]
    }


@router.get("/modules")
def list_modules(
    course_id: int,
    batch_name: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Returns modules for a course+batch (Step-1 Module dropdown)."""
    modules = db.query(Module).filter(
        Module.course_id == course_id,
        Module.batch_name == batch_name
    ).order_by(Module.order).all()

    # Fall back to all modules in the course if none are batch-specific
    if not modules:
        modules = db.query(Module).filter(
            Module.course_id == course_id
        ).order_by(Module.order).all()

    return [{"module_id": m.id, "module_name": m.title} for m in modules]


# ── Create Assignment (single multipart request: fields + optional files) ──────

@router.post("/", response_model=AssignmentResponse, status_code=201)
def create_assignment(
    # ── Assignment fields sent as form values ──
    course_id: int = Form(...),
    batch_name: str = Form(...),
    module_id: int = Form(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    objective: Optional[str] = Form(None),
    expected_outcome: Optional[str] = Form(None),
    due_date: Optional[str] = Form(None),          # ISO-8601 string, parsed below
    # ── Optional resource files uploaded at the same time ──
    files: Optional[List[UploadFile]] = File(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Creates the assignment **and** optionally attaches resource files — all in
    one multipart/form-data request.  No need to know the assignment ID before
    uploading; just include the files in the same request.

    Additional files can still be appended later via
      POST /assignments/{id}/resources
    """
    require_instructor(current_user)
    module = db.query(Module).filter(
        Module.id == module_id,
        Module.course_id == course_id
    ).first()

    if not module:
        raise HTTPException(
            status_code=404,
            detail="Module not found"
        )
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    batch_exists = db.query(Classroom).filter(
        Classroom.course_id == course_id,
        Classroom.batch_name == batch_name
    ).first()
    if not batch_exists:
        raise HTTPException(
            status_code=400,
            detail=f"Batch '{batch_name}' not found for this course."
        )

    # Parse optional due_date string
    parsed_due_date = None
    if due_date:
        try:
            parsed_due_date = datetime.fromisoformat(due_date)
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail="due_date must be a valid ISO-8601 datetime string, e.g. '2025-06-30T23:59:00'"
            )

    new_assignment = Assignment(
        course_id=course_id,
        batch_name=batch_name,
        module_id= module_id,
        title=title,
        description=description,
        objective=objective,
        expected_outcome=expected_outcome,
        due_date=parsed_due_date,
        created_by=current_user["user_id"],
    )
    db.add(new_assignment)
    db.commit()
    db.refresh(new_assignment)

    # Save any files that were uploaded alongside the assignment
    if files:
        folder = os.path.join(UPLOAD_DIR, str(new_assignment.id))
        os.makedirs(folder, exist_ok=True)

        for file in files:
            if not file.filename:          # skip empty file slots
                continue
            ext = os.path.splitext(file.filename)[1]
            unique_name = f"{uuid.uuid4().hex}{ext}"
            dest = os.path.join(folder, unique_name)

            with open(dest, "wb") as f_out:
                shutil.copyfileobj(file.file, f_out)

            resource = AssignmentResource(
                assignment_id=new_assignment.id,
                file_name=file.filename,
                file_path=dest,
                file_type=file.content_type,
            )
            db.add(resource)

        db.commit()
        db.refresh(new_assignment)

    # ── Fan-out: notify every enrolled student in this batch ──────────────────
    enrolled_students = (
        db.query(Enrollment)
        .join(Classroom, Classroom.id == Enrollment.classroom_id)
        .filter(
            Classroom.course_id == course_id,
            Classroom.batch_name == batch_name,
            Enrollment.status == "ongoing"
        )
        .all()
)

    for enrollment in enrolled_students:
        create_notification(
            db,
            user_id=enrollment.user_id,
            type="assignment",
            title="New Assignment",
            message=f"{title} has been posted for {batch_name}.",
            related_id=new_assignment.id,
        )
    if enrolled_students:
        db.commit()

    return new_assignment


# ── Upload Resources to an Assignment ────────────────────────────────────────

@router.post("/{assignment_id}/resources", response_model=List[AssignmentResourceResponse])
def upload_resources(
    assignment_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload one or more resource files to an existing assignment.
    Files are stored in uploads/assignments/{assignment_id}/.
    """
    require_instructor(current_user)

    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Ensure per-assignment folder
    folder = os.path.join(UPLOAD_DIR, str(assignment_id))
    os.makedirs(folder, exist_ok=True)

    saved = []
    for file in files:
        # Generate unique filename to avoid collisions
        ext = os.path.splitext(file.filename)[1]
        unique_name = f"{uuid.uuid4().hex}{ext}"
        dest = os.path.join(folder, unique_name)

        with open(dest, "wb") as f:
            shutil.copyfileobj(file.file, f)

        resource = AssignmentResource(
            assignment_id=assignment_id,
            file_name=file.filename,
            file_path=dest,
            file_type=file.content_type,
        )
        db.add(resource)
        db.flush()
        saved.append(resource)

    db.commit()
    for r in saved:
        db.refresh(r)
    return saved


# ── Instructor: List All Assignments ─────────────────────────────────────────

@router.get("/", response_model=List[AssignmentResponse])
def list_assignments(
    course_id: Optional[int] = None,
    batch_name: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Instructor: list all assignments they created.
    Optionally filter by course_id and/or batch_name.
    """
    require_instructor(current_user)

    q = db.query(Assignment).filter(Assignment.created_by == current_user["user_id"])
    if course_id:
        q = q.filter(Assignment.course_id == course_id)
    if batch_name:
        q = q.filter(Assignment.batch_name == batch_name)

    return q.order_by(Assignment.created_at.desc()).all()


@router.get("/dashboard", response_model=List[StudentDashboardAssignmentItem])
def student_dashboard_assignments_route(
    status: Optional[str] = None,
    date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return student_dashboard_assignments(status, date, db, current_user)


# ── Get Single Assignment ─────────────────────────────────────────────────────

@router.get("/{assignment_id}", response_model=AssignmentResponse)
def get_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Fetch a single assignment with its resources."""
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment


# ── Update Assignment ─────────────────────────────────────────────────────────

@router.put("/{assignment_id}", response_model=AssignmentResponse)
def update_assignment(
    assignment_id: int,
    data: AssignmentUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    require_instructor(current_user)

    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    if data.title is not None:
        assignment.title = data.title
    if data.description is not None:
        assignment.description = data.description
    if data.expected_outcome is not None:
        assignment.expected_outcome = data.expected_outcome
    if data.due_date is not None:
        assignment.due_date = data.due_date

    db.commit()
    db.refresh(assignment)
    return assignment


# ── Delete Assignment ─────────────────────────────────────────────────────────

@router.delete("/{assignment_id}")
def delete_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    require_instructor(current_user)

    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Remove uploaded files from disk
    folder = os.path.join(UPLOAD_DIR, str(assignment_id))
    if os.path.exists(folder):
        shutil.rmtree(folder)

    db.delete(assignment)
    db.commit()
    return {"message": "Assignment deleted successfully"}


# ── Instructor: View All Submissions for an Assignment ───────────────────────

@router.get("/{assignment_id}/submissions")
def get_submissions(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Returns all enrolled students for the batch with their submission status.
    Students who haven't submitted appear as status='pending'.
    """
    require_instructor(current_user)

    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # All enrolled students in the batch
    enrollments = (
        db.query(Enrollment)
        .join(Classroom, Classroom.id == Enrollment.classroom_id)
        .filter(
            Classroom.course_id == assignment.course_id,
            Classroom.batch_name == assignment.batch_name,
            Enrollment.status == "ongoing",
        )
        .all()
    )

    # Build submission lookup
    submissions = db.query(AssignmentSubmission).filter(
        AssignmentSubmission.assignment_id == assignment_id
    ).all()
    sub_map = {s.student_user_id: s for s in submissions}

    rows = []
    for en in enrollments:
        student = db.query(User).filter(User.id == en.user_id).first()
        if not student:
            continue
        sub = sub_map.get(en.user_id)
        rows.append(StudentAssignmentRow(
            student_id=student.student_id or str(student.id),
            student_name=student.name,
            status=sub.status if sub else "pending",
            submitted_at=sub.submitted_at if sub else None,
            grade=sub.grade if sub else None,
            submission_id=sub.id if sub else None,
        ))

    return {
        "assignment_id": assignment_id,
        "title": assignment.title,
        "batch_name": assignment.batch_name,
        "total_enrolled": len(rows),
        "total_submitted": sum(1 for r in rows if r.status in ["submitted", "graded"]),
        "students": [r.model_dump() for r in rows]
    }


# ── Student: View My Assignments ──────────────────────────────────────────────
@router.get("/my/list")
def my_assignments(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    require_student(current_user)

    enrollments = db.query(Enrollment).filter(
        Enrollment.user_id == current_user["user_id"],
        Enrollment.status == "ongoing"
    ).all()

    result = []

    for en in enrollments:

        assignments = db.query(Assignment).filter(
            Assignment.course_id == en.classroom.course_id,
            Assignment.batch_name == en.classroom.batch_name
        ).all()

        for assignment in assignments:

            course = db.query(Course).filter(
                Course.id == assignment.course_id
            ).first()

            module = db.query(Module).filter(
                Module.id == assignment.module_id
            ).first()

            result.append({
                "assignment_id": assignment.id,
                "title": assignment.title,
                "description": assignment.description,
                "course_id": assignment.course_id,
                "course_name": course.name if course else None,
                "module_id": assignment.module_id,
                "module_name": module.title if module else None,
                "batch_name": assignment.batch_name,
                "due_date": assignment.due_date,
                "created_at": assignment.created_at
            })

    return result

    

   


# ── Student: Dashboard Assignment Cards ───────────────────────────────────────

def student_dashboard_assignments(
    status: Optional[str] = None,    # 'in_progress' | 'completed' | 'overdue'
    date: Optional[str] = None,      # ISO date filter e.g. '2026-03-19' (matches due_date day)
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Student dashboard assignment list.

    Returns one card per assignment with:
      - course_code  : first token of the course name (e.g. 'AM101')
      - course_name  : full course name
      - due_date     : formatted 'Jan 15, 26'
      - due_time     : formatted '9:00 am' from the due_date time portion
      - status       : derived badge —
          'completed' → student has a submitted/graded submission
          'overdue'   → past due_date and no submission
          'in_progress' → everything else

    Optional query params:
      ?status=in_progress | completed | overdue   → filter by badge
      ?date=2026-03-19                             → show only assignments due on that day
    """
    require_student(current_user)

    now = datetime.now(timezone.utc)

    # Collect all active enrollments for this student
    enrollments = db.query(Enrollment).filter(
        Enrollment.user_id == current_user["user_id"],
        Enrollment.status == "ongoing"
    ).all()

    # Build submission lookup: {assignment_id: submission}
    all_sub = db.query(AssignmentSubmission).filter(
        AssignmentSubmission.student_user_id == current_user["user_id"]
    ).all()
    sub_map = {s.assignment_id: s for s in all_sub}

    cards: List[StudentDashboardAssignmentItem] = []

    for en in enrollments:
        classroom = db.query(Classroom).filter(Classroom.id == en.classroom_id).first()
        if not classroom:
            continue

        course = db.query(Course).filter(Course.id == classroom.course_id).first()
        if not course:
            continue

        assignments = db.query(Assignment).filter(
            Assignment.course_id == classroom.course_id,
            Assignment.batch_name == classroom.batch_name,
        ).order_by(Assignment.due_date.asc()).all()

        for a in assignments:
            # ── Derive status badge ──
            sub = sub_map.get(a.id)
            if sub and sub.status in ("submitted", "graded"):
                badge = "completed"
            elif a.due_date and a.due_date < now:
                badge = "overdue"
            else:
                badge = "in_progress"

            # ── Optional filters ──
            if status and badge != status:
                continue

            if date:
                try:
                    filter_date = datetime.fromisoformat(date).date()
                    if not a.due_date or a.due_date.date() != filter_date:
                        continue
                except ValueError:
                    pass  # ignore bad date param

            # ── Format due date / time ──
            formatted_date = None
            formatted_time = None
            if a.due_date:
                # 'Jan 15, 26' — use int() to strip leading zero cross-platform
                formatted_date = f"{a.due_date.strftime('%b')} {int(a.due_date.strftime('%d'))}, {a.due_date.strftime('%y')}"
                # '9:00 am'
                formatted_time = a.due_date.strftime("%I:%M %p").lstrip("0").lower()

            # ── Course code = first whitespace-free token of name ──
            course_code = course.name.split()[0] if course.name else ""
            module_name=a.module.title if a.module else None
            cards.append(StudentDashboardAssignmentItem(
                assignment_id=a.id,
                course_code=course_code,
                course_name=course.name,
                module_name= module_name,
                title=a.title,
                due_date=formatted_date,
                due_time=formatted_time,
                status=badge,
                submission_id=sub.id if sub else None,
                grade=sub.grade if sub else None,
            ))

    return cards


# ── Student: Submit Assignment ─────────────────────────────────────────────────

@router.post("/{assignment_id}/submit", response_model=AssignmentSubmissionResponse)
def submit_assignment(
    assignment_id: int,
    submission_text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Student submits an assignment.
    Accepts optional text and/or an uploaded file.
    Re-submitting replaces the previous submission.
    """
    require_student(current_user)

    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Verify student is enrolled in the correct batch
    enrollment = (
        db.query(Enrollment)
        .join(Classroom, Classroom.id == Enrollment.classroom_id)
        .filter(
            Enrollment.user_id == current_user["user_id"],
            Classroom.course_id == assignment.course_id,
            Classroom.batch_name == assignment.batch_name
        )
        .first()
    )
    if not enrollment:
        raise HTTPException(status_code=403, detail="Not enrolled in this assignment's batch.")

    # Upsert submission
    sub = db.query(AssignmentSubmission).filter(
        AssignmentSubmission.assignment_id == assignment_id,
        AssignmentSubmission.student_user_id == current_user["user_id"]
    ).first()

    saved_path = None
    saved_name = None
    if file:
        folder = os.path.join(UPLOAD_DIR, f"{assignment_id}_submissions")
        os.makedirs(folder, exist_ok=True)
        ext = os.path.splitext(file.filename)[1]
        unique_name = f"{current_user['user_id']}_{uuid.uuid4().hex}{ext}"
        dest = os.path.join(folder, unique_name)
        with open(dest, "wb") as f_out:
            shutil.copyfileobj(file.file, f_out)
        saved_path = dest
        saved_name = file.filename
    submitted_at=datetime.now(timezone.utc)

    if sub:
        sub.submission_text = submission_text
        sub.file_path = saved_path or sub.file_path
        sub.file_name = saved_name or sub.file_name
        sub.submitted_at = datetime.now(timezone.utc)
        sub.status = "submitted"
    else:
        sub = AssignmentSubmission(
            assignment_id=assignment_id,
            student_user_id=current_user["user_id"],
            submission_text=submission_text,
            file_path=saved_path,
            file_name=saved_name,
            submitted_at=datetime.now(timezone.utc),
            status="submitted"
        )
        db.add(sub)

    db.commit()
    db.refresh(sub)
    return sub


# ── Student: View Own Submission ──────────────────────────────────────────────

@router.get("/{assignment_id}/my-submission", response_model=AssignmentSubmissionResponse)
def my_submission(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    require_student(current_user)

    sub = db.query(AssignmentSubmission).filter(
        AssignmentSubmission.assignment_id == assignment_id,
        AssignmentSubmission.student_user_id == current_user["user_id"]
    ).first()
    if not sub:
        raise HTTPException(status_code=404, detail="No submission found yet.")
    return sub


# ── Instructor: Grade a Submission ────────────────────────────────────────────

@router.put("/{assignment_id}/submissions/{submission_id}/grade")
def grade_submission(
    assignment_id: int,
    submission_id: int,
    grade: str = Form(...),
    feedback: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Instructor assigns a grade and optional feedback to a student's submission."""
    require_instructor(current_user)

    sub = db.query(AssignmentSubmission).filter(
        AssignmentSubmission.id == submission_id,
        AssignmentSubmission.assignment_id == assignment_id
    ).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")

    sub.grade = grade
    sub.feedback = feedback
    sub.status = "graded"
    db.commit()
    db.refresh(sub)

    return {
        "message": "Graded successfully",
        "submission_id": sub.id,
        "grade": sub.grade,
        "feedback": sub.feedback
    }
from fastapi.responses import FileResponse

@router.get("/{assignment_id}/resources")
def get_assignment_resources(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    assignment = (
        db.query(Assignment)
        .filter(Assignment.id == assignment_id)
        .first()
    )

    if not assignment:
        raise HTTPException(
            status_code=404,
            detail="Assignment not found"
        )

    if not can_access_assignment(db, assignment, current_user):
        raise HTTPException(status_code=403, detail="Not authorized to access this assignment")

    resources = (
        db.query(AssignmentResource)
        .filter(
            AssignmentResource.assignment_id == assignment_id
        )
        .all()
    )

    return {
        "assignment_id": assignment.id,
        "title": assignment.title,
        "resource_count": len(resources),
        "resources": [
            {
                "resource_id": r.id,
                "file_name": r.file_name,
                "file_type": r.file_type,
                "download_url": f"/assignments/resources/{r.id}/download"
            }
            for r in resources
        ]
    }

from fastapi.responses import FileResponse

@router.get("/resources/{resource_id}/download")
def download_assignment_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    resource = (
        db.query(AssignmentResource)
        .filter(
            AssignmentResource.id == resource_id
        )
        .first()
    )

    if not resource:
        raise HTTPException(
            status_code=404,
            detail="Resource not found"
        )

    if not can_access_assignment(db, resource.assignment, current_user):
        raise HTTPException(status_code=403, detail="Not authorized to access this assignment")

    if not os.path.exists(resource.file_path):
        raise HTTPException(
            status_code=404,
            detail="File missing from server"
        )

    return FileResponse(
        path=resource.file_path,
        filename=resource.file_name,
        media_type=resource.file_type
    )

@router.get("/resources/{resource_id}/view")
def view_assignment_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    resource = (
        db.query(AssignmentResource)
        .filter(
            AssignmentResource.id == resource_id
        )
        .first()
    )

    if not resource:
        raise HTTPException(
            status_code=404,
            detail="Resource not found"
        )

    if not can_access_assignment(db, resource.assignment, current_user):
        raise HTTPException(status_code=403, detail="Not authorized to access this assignment")

    return FileResponse(
        resource.file_path,
        media_type=resource.file_type
    )

@router.get("/{assignment_id}/details")
def assignment_details(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    assignment = (
        db.query(Assignment)
        .filter(Assignment.id == assignment_id)
        .first()
    )

    if not assignment:
        raise HTTPException(
            status_code=404,
            detail="Assignment not found"
        )

    if not can_access_assignment(db, assignment, current_user):
        raise HTTPException(status_code=403, detail="Not authorized to access this assignment")

    resources = (
        db.query(AssignmentResource)
        .filter(
            AssignmentResource.assignment_id == assignment_id
        )
        .all()
    )

    return {
        "assignment_id": assignment.id,
        "title": assignment.title,
        "description": assignment.description,
        "objective": assignment.objective,
        "expected_outcome": assignment.expected_outcome,
        "due_date": assignment.due_date,
        "module_name": assignment.module.title if assignment.module else None,
        "resources": [
            {
                "resource_id": r.id,
                "file_name": r.file_name,
                "file_type": r.file_type,
                "view_url": f"/assignments/resources/{r.id}/view",
                "download_url": f"/assignments/resources/{r.id}/download"
            }
            for r in resources
        ]
    }
@router.get("/{assignment_id}/submitted-resources")
def get_assignment_submissions(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    assignment = db.query(Assignment).filter(
        Assignment.id == assignment_id
    ).first()

    if not assignment:
        raise HTTPException(
            status_code=404,
            detail="Assignment not found"
        )

    submissions = db.query(
        AssignmentSubmission
    ).filter(
        AssignmentSubmission.assignment_id ==
        assignment_id
    ).all()

    result = []

    for sub in submissions:

        student = db.query(User).filter(
            User.id == sub.student_user_id
        ).first()

        result.append({
            "submission_id": sub.id,
            "student_id": student.student_id if student else None,
            "student_name": student.name if student else None,
            "submitted_at": sub.submitted_at,
            "status": sub.status,
            "grade": sub.grade,
            "file_name": sub.file_name,
            "has_file": bool(sub.file_path)
        })

    return {
        "assignment_id": assignment.id,
        "title": assignment.title,
        "total_submissions": len(result),
        "submissions": result
    }


@router.get("/{assignment_id}/submitted-resources")
def get_assignment_submissions(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    assignment = db.query(Assignment).filter(
        Assignment.id == assignment_id
    ).first()

    if not assignment:
        raise HTTPException(
            status_code=404,
            detail="Assignment not found"
        )

    submissions = db.query(
        AssignmentSubmission
    ).filter(
        AssignmentSubmission.assignment_id ==
        assignment_id
    ).all()

    result = []

    for sub in submissions:

        student = db.query(User).filter(
            User.id == sub.student_user_id
        ).first()

        result.append({
            "submission_id": sub.id,
            "student_id": student.student_id if student else None,
            "student_name": student.name if student else None,
            "submitted_at": sub.submitted_at,
            "status": sub.status,
            "grade": sub.grade,
            "file_name": sub.file_name,
            "has_file": bool(sub.file_path)
        })

    return {
        "assignment_id": assignment.id,
        "title": assignment.title,
        "total_submissions": len(result),
        "submissions": result
    }

@router.get("/submission/{submission_id}")
def get_submission_details(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    submission = db.query(
        AssignmentSubmission
    ).filter(
        AssignmentSubmission.id == submission_id
    ).first()

    if not submission:
        raise HTTPException(
            status_code=404,
            detail="Submission not found"
        )

    student = db.query(User).filter(
        User.id == submission.student_user_id
    ).first()

    return {
        "submission_id": submission.id,
        "student_id": student.student_id if student else None,
        "student_name": student.name if student else None,
        "submission_text": submission.submission_text,
        "file_name": submission.file_name,
        "grade": submission.grade,
        "feedback": submission.feedback,
        "submitted_at": submission.submitted_at
    }
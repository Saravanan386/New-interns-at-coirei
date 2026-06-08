from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from app.database import get_db
from app.utils.security import get_current_user

from app.models.user import User
from app.models.course import Course
from app.models.classroom import Classroom
from app.models.enrollment import Enrollment
from app.models.instructor_enrollment import InstructorEnrollment
from app.models.module import Module, Chapter
from app.models.chapter_resources import ChapterResource
from app.models.assignment import Assignment, AssignmentSubmission
from app.models.test import Test, TestSubmission
from app.models.session import ClassSession
from app.models.attendance import SessionParticipant
from app.models.announcements import Announcement
from app.models.registration_profile import InstructorInformation, StudentInformation

router = APIRouter(
    prefix="/instructor",
    tags=["Instructor"]
)

def get_my_classroom_ids(db: Session, instructor_id: int) -> list[int]:
    rows = (
        db.query(InstructorEnrollment.classroom_id)
        .filter(InstructorEnrollment.user_id == instructor_id)
        .all()
    )
    return [r.classroom_id for r in rows]



@router.get("/dashboard/summary")
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    classroom_ids = get_my_classroom_ids(db, current_user["user_id"])
    
    if not classroom_ids:
        return {
            "total_students": 0,
            "total_active_batches": 0,
            "upcoming_classes": 0,
            "recent_submissions_to_grade": 0
        }

    # 1. Compute total active student metrics
    total_students = (
        db.query(func.count(Enrollment.user_id.distinct()))
        .filter(Enrollment.classroom_id.in_(classroom_ids))
        .scalar() or 0
    )
    
    # 2. Upcoming scheduled sessions tracker
    upcoming_classes = (
        db.query(ClassSession)
        .filter(
            ClassSession.classroom_id.in_(classroom_ids),
            ClassSession.start_time >= datetime.utcnow(),
            ClassSession.status == "scheduled"
        )
        .count()
    )
    
    # 3. Pull structural criteria parameters from handled classrooms
    classrooms = db.query(Classroom).filter(Classroom.id.in_(classroom_ids)).all()
    
    pending_reviews = 0
    if classrooms:
        # Build composite mapping parameters to map assignment scope correctly
        filters = []
        for c in classrooms:
            if c.course_id and c.batch_name:
                filters.append((Assignment.course_id == c.course_id) & (Assignment.batch_name == c.batch_name))
        
        if filters:
            from sqlalchemy import or_
            pending_reviews = (
                db.query(func.count(AssignmentSubmission.id))
                .join(Assignment, Assignment.id == AssignmentSubmission.assignment_id)
                .filter(
                    AssignmentSubmission.status == "submitted",
                    or_(*filters)
                )
                .scalar() or 0
            )

    return {
        "total_students": total_students,
        "total_active_batches": len(classroom_ids),
        "upcoming_classes": upcoming_classes,
        "recent_submissions_to_grade": pending_reviews
    }

@router.get("/my-assignments")
def my_assignments(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    classroom_ids = get_my_classroom_ids(db, current_user["user_id"])
    
    # Load classrooms along with their courses in an optimization step
    classrooms = db.query(Classroom).filter(Classroom.id.in_(classroom_ids)).all()
    course_ids = [c.course_id for c in classrooms if c.course_id]
    
    courses_map = {
        course.id: course 
        for course in db.query(Course).filter(Course.id.in_(course_ids)).all()
    }

    result = []
    for c in classrooms:
        course = courses_map.get(c.course_id)
        result.append({
            "classroom_id": c.id,
            "batch_name": c.batch_name,
            "course_id": course.id if course else None,
            "course_name": course.name if course else "Unknown",
            "course_code": course.course_code if course else ""
        })

    return result

@router.get("/students")
def get_students(
    search: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    classroom_ids = get_my_classroom_ids(db, current_user["user_id"])
    
    if not classroom_ids:
        return []

    # Query distinct User profiles directly to dodge JSON sorting crashes in Postgres
    query = (
        db.query(User)
        .join(Enrollment, Enrollment.user_id == User.id)
        .filter(Enrollment.classroom_id.in_(classroom_ids))
    )
    
    if search:
        search_filter = f"%{search.strip().lower()}%"
        query = query.filter(func.lower(User.name).like(search_filter))
        
    students = query.distinct().all()
    student_ids = [s.id for s in students]

    # Batch query profile metadata out of the loop to bypass N+1 performance lag
    profiles_map = {}
    if student_ids:
        profiles = (
            db.query(StudentInformation)
            .filter(StudentInformation.user_id.in_(student_ids))
            .all()
        )
        profiles_map = {p.user_id: p for p in profiles}
    
    result = []
    for s in students:
        prof = profiles_map.get(s.id)
        result.append({
            "id": s.id,
            "student_id": str(prof.id) if prof else str(s.id), 
            "name": s.name,
            "attendance_percentage": "0%", 
            "last_score": None,
            "recent_submissions": []
        })
        
    return result

@router.get("/students/{student_id}/profile")
def student_profile(
    student_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    student = db.query(User).filter(User.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    profile = db.query(StudentInformation).filter(StudentInformation.user_id == student.id).first()
    
    total_sessions = db.query(SessionParticipant).filter(SessionParticipant.user_id == student.id).count()
    attended = db.query(SessionParticipant).filter(
        SessionParticipant.user_id == student.id,
        SessionParticipant.status == "present"
    ).count()

    attendance_percent = round(attended * 100 / total_sessions, 2) if total_sessions else 0

    submissions = db.query(AssignmentSubmission).filter(AssignmentSubmission.student_user_id == student.id).all()
    tests = db.query(TestSubmission).filter(TestSubmission.student_user_id == student.id).all()

    return {
        "id": student.id,
        "student_id": profile.id if profile else student.id, # Fixed attribute missing issue
        "name": student.name,
        "email": profile.email if profile else student.email,
        "contact": profile.phone_number if profile else None,
        "stats": {
            "overall_attendance": f"{attendance_percent}%",
            "average_score": "0%",
            "live_participation": "Good",
            "classes_attended": attended
        },
        "assignment_performance": submissions,
        "test_performance": tests,
        "attendance_details": [],
        "recent_activity": []
    }

@router.get("/resources/instructor")
def instructor_resources(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    classroom_ids = get_my_classroom_ids(db, current_user["user_id"])
    classrooms = db.query(Classroom).filter(Classroom.id.in_(classroom_ids)).all()
    course_ids = [c.course_id for c in classrooms if c.course_id]

    # Scope resources strictly through modules belonging to courses the instructor handles
    resources = (
        db.query(ChapterResource)
        .join(Chapter, Chapter.id == ChapterResource.chapter_id)
        .join(Module, Module.id == Chapter.module_id)
        .filter(Module.course_id.in_(course_ids))
        .order_by(ChapterResource.uploaded_at.desc())
        .all()
    )

    return [
        {
            "resource_id": r.id,
            "name": r.file_name,
            "download_url": r.file_path,
            "uploaded_at": r.uploaded_at
        }
        for r in resources
    ]
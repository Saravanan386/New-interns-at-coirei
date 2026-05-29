from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.utils.security import get_current_user
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.schemas import (
    CourseCreate,
    CourseUpdate,
    CourseResponse
)
router = APIRouter(prefix="/courses", tags=["Courses"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/my")
def get_my_courses(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    enrollments = (
        db.query(Enrollment, Course)
        .join(Course, Course.id == Enrollment.course_id)
        .filter(Enrollment.user_id == current_user["user_id"])
        .all()
    )

    return [
        {
            "course_id": course.id,
            "course_name": course.name,
            "duration_months": course.duration_months,
            "total_lessons": course.total_lessons,
            "progress": enrollment.progress_percent,
            "status": enrollment.status
        }
        for enrollment, course in enrollments
    ]

@router.get("/")
def list_courses(db: Session = Depends(get_db)):
    return db.query(Course).all()

@router.get("/{course_id}/batches")
def get_course_batches(course_id: int, db: Session = Depends(get_db)):
    from app.models.module import Module
    enrollment_batches = db.query(Enrollment.batch_name).filter(Enrollment.course_id == course_id).distinct().all()
    module_batches = db.query(Module.batch_name).filter(Module.course_id == course_id).distinct().all()
    
    all_batches = set([b[0] for b in enrollment_batches if b[0]])
    all_batches.update([b[0] for b in module_batches if b[0]])
    
    return sorted(list(all_batches))



@router.post(
    "/create",
    response_model=CourseResponse
)
def create_course(
    data: CourseCreate,
    db: Session = Depends(get_db)
):

    existing = db.query(Course).filter(
        Course.course_code == data.course_code
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Course code already exists"
        )

    new_course = Course(
        course_code=data.course_code,
        name=data.name,
        description=data.description,
        duration_months=data.duration_months,
        total_lessons=data.total_lessons
    )

    db.add(new_course)

    db.commit()

    db.refresh(new_course)

    return new_course

@router.put(
    "/update/{course_id}",
    response_model=CourseResponse
)
def update_course(
    course_id: int,
    data: CourseUpdate,
    db: Session = Depends(get_db)
):

    course = db.query(Course).filter(
        Course.id == course_id
    ).first()

    if not course:
        raise HTTPException(
            status_code=404,
            detail="Course not found"
        )

    update_data = data.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(course, key, value)

    db.commit()

    db.refresh(course)

    return course
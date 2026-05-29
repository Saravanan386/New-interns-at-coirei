from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.classroom import Classroom
from app.models.course import Course

# IMPORTANT
from app.utils.security import get_current_user

from app.schemas import ClassroomResponse

router = APIRouter(
    prefix="/classrooms",
    tags=["Classrooms"]
)


# -------------------------------------------------------------------
# CREATE CLASSROOM
# -------------------------------------------------------------------
@router.post(
    "/",
    response_model=ClassroomResponse
)
def create_classroom(
    course_id: int = Body(...),
    batch_name: str = Body(...),
    room_name: str = Body(...),

    current_user: dict = Depends(get_current_user),

    db: Session = Depends(get_db),
):

    # AUTH CHECK
    if current_user["role"] not in ["admin", "instructor"]:
        raise HTTPException(
            status_code=403,
            detail="Not authorized"
        )

    # VALIDATE COURSE
    course = (
        db.query(Course)
        .filter(Course.id == course_id)
        .first()
    )

    if not course:
        raise HTTPException(
            status_code=404,
            detail="Course not found"
        )

    # PREVENT DUPLICATE BATCH
    existing_batch = (
        db.query(Classroom)
        .filter(
            Classroom.course_id == course_id,
            Classroom.batch_name == batch_name
        )
        .first()
    )

    if existing_batch:
        raise HTTPException(
            status_code=400,
            detail="Batch already exists for this course"
        )

    # CREATE CLASSROOM
    new_classroom = Classroom(
        course_id=course.id,
        course_name=course.name,
        batch_name=batch_name,
        room_name=room_name
    )

    db.add(new_classroom)

    db.commit()

    db.refresh(new_classroom)

    return new_classroom


# -------------------------------------------------------------------
# LIST CLASSROOMS
# -------------------------------------------------------------------
@router.get(
    "/",
    response_model=list[ClassroomResponse]
)
def list_classrooms(
    current_user: dict = Depends(get_current_user),

    db: Session = Depends(get_db),
):

    classrooms = db.query(Classroom).all()

    return classrooms
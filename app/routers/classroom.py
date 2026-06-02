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


def generate_batch_code(course_name: str, batch_name: str):
    course_part = "".join(
        word[0].upper()
        for word in course_name.split()
        if word
    )

    batch_part = batch_name.upper().replace(" ", "-")

    return f"{course_part}-{batch_part}"


@router.post("/")
def create_classroom(
    course_id: int = Body(...),
    batch_name: str = Body(...),
    room_name: str = Body(...),
    schedule_type: str = Body(None),
    start_month: str = Body(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admins can create classrooms"
        )

    course = db.query(Course).filter(
        Course.id == course_id
    ).first()

    if not course:
        raise HTTPException(
            status_code=404,
            detail="Course not found"
        )

    existing = db.query(Classroom).filter(
        Classroom.course_id == course_id,
        Classroom.batch_name == batch_name
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Batch already exists"
        )

    batch_code = generate_batch_code(
        course.name,
        batch_name
    )

    classroom = Classroom(
        course_id=course_id,
        batch_name=batch_name,
        room_name=room_name,
        instructor_id=None,
        instructor_name=None,
        batch_code=batch_code,
        schedule_type=schedule_type,
        start_month=start_month
    )

    db.add(classroom)

    db.commit()

    db.refresh(classroom)

    return classroom


    
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


@router.get("/")
def get_classrooms(
    db: Session = Depends(get_db)
):
    return db.query(Classroom).all()


@router.get("/{classroom_id}")
def get_classroom(
    classroom_id: int,
    db: Session = Depends(get_db)
):
    classroom = (
        db.query(Classroom)
        .filter(Classroom.id == classroom_id)
        .first()
    )

    if not classroom:
        raise HTTPException(
            status_code=404,
            detail="Classroom not found"
        )

    return classroom


@router.get("/course/{course_id}")
def get_course_classrooms(
    course_id: int,
    db: Session = Depends(get_db)
):
    return (
        db.query(Classroom)
        .filter(Classroom.course_id == course_id)
        .all()
    )



@router.delete("/{classroom_id}")
def delete_classroom(
    classroom_id: int,
    db: Session = Depends(get_db)
):
    classroom = (
        db.query(Classroom)
        .filter(Classroom.id == classroom_id)
        .first()
    )

    if not classroom:
        raise HTTPException(
            status_code=404,
            detail="Classroom not found"
        )

    db.delete(classroom)
    db.commit()

    return {
        "message": "Classroom deleted successfully"
    }

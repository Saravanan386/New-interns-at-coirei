from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.classroom import Classroom
from app.models.course import Course

# IMPORTANT
from app.utils.security import get_current_user

from app.schemas import ClassroomResponse

from app.models.schedule import CourseSchedule

from sqlalchemy import Date


def sync_schedule(db, classroom):

    db.query(CourseSchedule).filter(
        CourseSchedule.course_id == classroom.course_id,
        CourseSchedule.batch_name == classroom.batch_name
    ).delete()

    if not classroom.class_days:
        db.commit()
        return

    days = [
        d.strip().lower()
        for d in classroom.class_days.split(",")
    ]

    for day in days:

        db.add(
        CourseSchedule(
            course_id=classroom.course_id,
            batch_name=classroom.batch_name,
            day_of_week=day,
            session_type="class",
            start_time=classroom.start_time,
            end_time=classroom.end_time,
            instructor_name=classroom.instructor_name
        )
    )

    db.commit()



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

    class_days: str = Body(None),
    start_time: str = Body(None),
    end_time: str = Body(None),


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
        start_month=start_month,

        class_days=class_days,
        start_time=start_time,
        end_time=end_time
    )
    db.add(classroom)

    db.commit()

    db.refresh(classroom)
    sync_schedule(
        db,
        classroom
    )

    db.commit()
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
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return db.query(Classroom).all()


@router.get("/{classroom_id}")
def get_classroom(
    classroom_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
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
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return (
        db.query(Classroom)
        .filter(Classroom.course_id == course_id)
        .all()
    )



@router.delete("/{classroom_id}")
def delete_classroom(
    classroom_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admins can delete classrooms"
        )

    classroom = db.query(Classroom).filter(
        Classroom.id == classroom_id
    ).first()

    if not classroom:
        raise HTTPException(
            status_code=404,
            detail="Classroom not found"
        )

    db.query(CourseSchedule).filter(
        CourseSchedule.course_id == classroom.course_id,
        CourseSchedule.batch_name == classroom.batch_name
    ).delete()

    db.delete(classroom)

    db.commit()

    return {
        "message": "Classroom deleted successfully"
    }



@router.put("/{classroom_id}")
def update_classroom(
    classroom_id: int,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admins can update classrooms"
        )

    classroom = db.query(Classroom).filter(
        Classroom.id == classroom_id
    ).first()

    if not classroom:
        raise HTTPException(
            status_code=404,
            detail="Classroom not found"
        )

    allowed_fields = [
        "batch_name",
        "room_name",
        "schedule_type",
        "start_month",
        "class_days",
        "start_time",
        "end_time",
        "instructor_id",
        "instructor_name"
    ]

    for field in allowed_fields:

        if field in payload:

            setattr(
                classroom,
                field,
                payload[field]
            )

    db.commit()

    db.refresh(classroom)

    sync_schedule(
        db,
        classroom
    )

    db.commit()

    return {
        "message": "Classroom updated",
        "classroom": classroom
    }


@router.get("/{classroom_id}/schedule")
def get_classroom_schedule(
    classroom_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    classroom = db.query(Classroom).filter(
        Classroom.id == classroom_id
    ).first()

    if not classroom:
        raise HTTPException(
            status_code=404,
            detail="Classroom not found"
        )

    schedules = db.query(
        CourseSchedule
    ).filter(
        CourseSchedule.course_id == classroom.course_id,
        CourseSchedule.batch_name == classroom.batch_name
    ).all()

    return {
        "classroom_id": classroom.id,
        "batch_name": classroom.batch_name,
        "schedule_type": classroom.schedule_type,
        "start_time": classroom.start_time,
        "end_time": classroom.end_time,
        "days": [
            s.day_of_week
            for s in schedules
        ]
    }

@router.get("/course/{course_id}/full")
def get_course_batches(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    classrooms = db.query(
        Classroom
    ).filter(
        Classroom.course_id == course_id
    ).all()

    return [
        {
            "id": c.id,
            "batch_name": c.batch_name,
            "batch_code": c.batch_code,
            "room_name": c.room_name,
            "schedule_type": c.schedule_type,
            "class_days": c.class_days,
            "start_time": c.start_time,
            "end_time": c.end_time,
            "instructor_name": c.instructor_name
        }
        for c in classrooms
    ]
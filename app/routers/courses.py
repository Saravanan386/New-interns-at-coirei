from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.utils.security import get_current_user
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.classroom import Classroom
from app.models.session import ClassSession
from sqlalchemy import func
from datetime import datetime
from app.models.schedule import CourseSchedule
from app.models.instructor_enrollment import InstructorEnrollment
from sqlalchemy.orm import joinedload


from app.database import get_db
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

    courses = db.query(Course).all()

    response = []

    for course in courses:

        classrooms = db.query(Classroom).filter(
            Classroom.course_id == course.id
        ).all()

        classroom_ids = [c.id for c in classrooms]

        student_count = 0

        if classroom_ids:
            student_count = db.query(Enrollment).filter(
                Enrollment.classroom_id.in_(classroom_ids)
            ).count()

        instructors = list(
            set(
                [
                    c.instructor_name
                    for c in classrooms
                    if c.instructor_name
                ]
            )
        )

        response.append({
            "id": course.id,
            "name": course.name,
            "course_code": course.course_code,
            "description": course.description,
            "total_batches": len(classrooms),
            "total_students": student_count,
            "instructors": instructors
        })

    return response


@router.get("/{course_id}/classrooms")
def get_course_classrooms(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    classrooms = db.query(Classroom).filter(
        Classroom.course_id == course_id
    ).all()

    response = []

    for classroom in classrooms:

        enrollments = db.query(
            Enrollment
        ).filter(
            Enrollment.classroom_id == classroom.id
        ).all()

        student_count = len(enrollments)

        avg_completion = 0

        if enrollments:

            avg_completion = round(
                sum(
                    e.progress_percent
                    for e in enrollments
                ) / len(enrollments)
            )

        status = "active"

        response.append({
            "id": classroom.id,
            "batch_name": classroom.batch_name,
            "batch_code": classroom.batch_code,
            "room_name": classroom.room_name,

            "status": status,

            "student_count": student_count,

            "completion_count": avg_completion,

            "instructor_name": classroom.instructor_name,

            "schedule_type": classroom.schedule_type,

            "start_month": classroom.start_month
        })

    return response

@router.get("/{course_id}/batches")
def get_course_batches(course_id: int, db: Session = Depends(get_db)):
    from app.models.module import Module
    enrollment_batches = db.query(Enrollment.batch_name).filter(Enrollment.course_id == course_id).distinct().all()
    module_batches = db.query(Module.batch_name).filter(Module.course_id == course_id).distinct().all()
    
    all_batches = set([b[0] for b in enrollment_batches if b[0]])
    all_batches.update([b[0] for b in module_batches if b[0]])
    
    return sorted(list(all_batches))



@router.delete("/{course_id}")
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
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

    db.delete(course)
    db.commit()

    return {
        "message": "Course deleted successfully"
    }

@router.post(
    "/create",
    response_model=CourseResponse
)
def create_course(
    data: CourseCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
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
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
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


@router.get("/{classroom_id}/overview")
def classroom_overview(
    classroom_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    classroom = db.query(
        Classroom
    ).filter(
        Classroom.id == classroom_id
    ).first()

    if not classroom:
        raise HTTPException(
            status_code=404,
            detail="Classroom not found"
        )

    course = db.query(
        Course
    ).filter(
        Course.id == classroom.course_id
    ).first()

    enrollments = db.query(
        Enrollment
    ).filter(
        Enrollment.classroom_id == classroom.id
    ).all()

    total_students = len(enrollments)

    avg_progress = 0

    if enrollments:
        avg_progress = round(
            sum(
                e.progress_percent
                for e in enrollments
            ) / total_students
        )

    next_session = db.query(
        ClassSession
    ).filter(
        ClassSession.classroom_id == classroom.id
    ).order_by(
        ClassSession.start_time.asc()
    ).first()

    next_session_text = "No session"

    if next_session:
        next_session_text = (
            next_session.start_time.strftime(
                "%d %b %Y %I:%M %p"
            )
        )

    return {
        "batch_id": classroom.batch_code,
        "course_id": course.id,
        "course_name": course.name,
        "description": course.description,

        "stats": {
            "total_students": total_students,
            "average_progress": avg_progress,
            "next_session": next_session_text,
            "duration_months": course.duration_months
        },

        "batch": {
            "id": classroom.id,
            "batch_name": classroom.batch_name,
            "batch_code": classroom.batch_code,
            "room_name": classroom.room_name,
            "schedule_type": classroom.schedule_type,
            "class_days": classroom.class_days,
            "start_time": classroom.start_time,
            "end_time": classroom.end_time,
            "start_month": classroom.start_month
        },

        "instructor": {
            "id": classroom.instructor_id,
            "name": classroom.instructor_name
        },

        "enrollment": {
            "total": total_students,
            "average_progress": avg_progress
        },

        "upcoming_sessions": [
            {
                "id": s.id,
                "status": s.status,
                "start_time": (
                    s.start_time.isoformat()
                    if s.start_time
                    else None
                ),
                "end_time": (
                    s.end_time.isoformat()
                    if s.end_time
                    else None
                )
            }
            for s in db.query(
                ClassSession
            ).filter(
                ClassSession.classroom_id == classroom.id
            ).all()
        ]
    }



@router.get("/{course_id}/batches/{classroom_id}/overview")
def batch_overview(
    course_id: int,
    classroom_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

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

    classroom = (
        db.query(Classroom)
        .filter(
            Classroom.id == classroom_id,
            Classroom.course_id == course_id
        )
        .first()
    )

    if not classroom:
        raise HTTPException(
            status_code=404,
            detail="Batch not found"
        )

    enrollments = (
        db.query(Enrollment)
        .filter(
            Enrollment.classroom_id == classroom.id
        )
        .all()
    )

    total_students = len(enrollments)

    avg_progress = 0

    if total_students > 0:
        avg_progress = round(
            sum(
                e.progress_percent
                for e in enrollments
            ) / total_students
        )

    sessions = (
        db.query(ClassSession)
        .filter(
            ClassSession.classroom_id == classroom.id
        )
        .order_by(
            ClassSession.start_time.asc()
        )
        .all()
    )

    upcoming_sessions = []

    now = datetime.utcnow()

    for session in sessions:

        if (
            session.start_time
            and session.start_time >= now
        ):

            upcoming_sessions.append({
                "id": session.id,
                "status": session.status,
                "start_time": session.start_time.isoformat(),
                "end_time": (
                    session.end_time.isoformat()
                    if session.end_time
                    else None
                ),
                "join_url": session.join_url
            })

    next_session = None

    if upcoming_sessions:
        next_session = upcoming_sessions[0]["start_time"]

    return {
        "batch_id": classroom.id,
        "batch_code": classroom.batch_code,

        "course": {
            "id": course.id,
            "name": course.name,
            "description": course.description,
            "duration_months": course.duration_months,
            "total_lessons": course.total_lessons
        },

        "classroom": {
            "id": classroom.id,
            "batch_name": classroom.batch_name,
            "room_name": classroom.room_name,
            "schedule_type": classroom.schedule_type,
            "start_month": classroom.start_month
        },

        "stats": {
            "total_students": total_students,
            "average_progress": avg_progress,
            "next_session": next_session
        },

        "instructor": {
            "id": classroom.instructor_id,
            "name": classroom.instructor_name
        },

        "upcoming_sessions": upcoming_sessions
    }


@router.get("/{course_id}/full-overview")
def course_full_overview(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    course = db.query(Course).filter(
        Course.id == course_id
    ).first()

    if not course:
        raise HTTPException(
            status_code=404,
            detail="Course not found"
        )

    classrooms = db.query(Classroom).filter(
        Classroom.course_id == course_id
    ).all()

   

    schedules = db.query(CourseSchedule).filter(
        CourseSchedule.course_id == course_id
    ).all()

    total_students = 0
    instructor_names = set()

    batch_details = []

    for classroom in classrooms:

        enrollments = db.query(Enrollment).filter(
            Enrollment.classroom_id == classroom.id
        ).all()

        batch_students = len(enrollments)

        total_students += batch_students

        avg_progress = 0

        if batch_students:

            avg_progress = round(
                sum(
                    e.progress_percent
                    for e in enrollments
                ) / batch_students
            )

        instructor_names.add(
            classroom.instructor_name
        )

        batch_schedules = [
            {
                "day": s.day_of_week,
                "start_time": s.start_time,
                "end_time": s.end_time,
                "session_type": s.session_type
            }
            for s in schedules
            if s.batch_name == classroom.batch_name
        ]

        

        batch_details.append({

            "classroom_id": classroom.id,

            "batch_name": classroom.batch_name,

            "batch_code": classroom.batch_code,

            "room_name": classroom.room_name,

            "schedule_type": classroom.schedule_type,

            "start_month": classroom.start_month,

            "class_days": classroom.class_days,

            "start_time": classroom.start_time,

            "end_time": classroom.end_time,

            "instructor_id": classroom.instructor_id,

            "instructor_name": classroom.instructor_name,

            "student_count": batch_students,

            "average_progress": avg_progress,


            "schedule": batch_schedules
        })

    upcoming_sessions = db.query(
        ClassSession
    ).join(
        Classroom,
        Classroom.id == ClassSession.classroom_id
    ).filter(
        Classroom.course_id == course_id
    ).order_by(
        ClassSession.start_time.asc()
    ).limit(10).all()

    return {

        "course": {

            "id": course.id,

            "course_code": course.course_code,

            "name": course.name,

            "description": course.description,

            "duration_months": course.duration_months,

            "total_lessons": course.total_lessons
        },

        "stats": {

            "total_batches": len(classrooms),

            "total_students": total_students,


            "total_schedules": len(schedules),

            "instructors": list(
                instructor_names
            )
        },

        "batches": batch_details,





        "upcoming_sessions": [

            {
                "id": s.id,

                "classroom_id": s.classroom_id,

                "status": s.status,

                "join_url": s.join_url,

                "start_time": (
                    s.start_time.isoformat()
                    if s.start_time
                    else None
                ),

                "end_time": (
                    s.end_time.isoformat()
                    if s.end_time
                    else None
                )
            }

            for s in upcoming_sessions
        ]
    }
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
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
from app.models.module import Module
from app.models.module import Chapter

from app.models.assignment import Assignment
from app.models.assignment import AssignmentSubmission
from app.models.test import Test
from app.models.test import TestSubmission
from app.models.user import User
from app.schemas import (
    CourseCreate,
    CourseUpdate,
    CourseResponse
)
router = APIRouter(prefix="/courses", tags=["Courses"])

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
def get_course_batches(
    course_id: int,
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

    classrooms = db.query(Classroom).filter(
        Classroom.course_id == course_id
    ).all()

    return [
        {
            "id": classroom.id,
            "batch_name": classroom.batch_name,
            "batch_code": classroom.batch_code,
            "room_name": classroom.room_name
        }
        for classroom in classrooms
    ]

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

    update_data = data.model_dump(exclude_unset=True)

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

    attendance_rows = db.query(SessionParticipant).join(
        ClassSession,
        ClassSession.id == SessionParticipant.session_id
    ).filter(
        ClassSession.classroom_id == classroom.id
    ).all()
    attended_rows = [
        row for row in attendance_rows
        if row.status in ("present", "late")
    ]
    avg_attendance = (
        round((len(attended_rows) / len(attendance_rows)) * 100, 2)
        if attendance_rows else 0
    )

    assignments = db.query(Assignment).filter(
        Assignment.course_id == classroom.course_id,
        Assignment.batch_name == classroom.batch_name,
    ).all()
    assignment_ids = [assignment.id for assignment in assignments]
    completed_assignments = (
        db.query(AssignmentSubmission)
        .filter(
            AssignmentSubmission.assignment_id.in_(assignment_ids),
            AssignmentSubmission.status.in_(["submitted", "graded"]),
        )
        .count()
        if assignment_ids else 0
    )
    expected_assignments = len(assignments) * total_students
    assignment_completion = (
        round((completed_assignments / expected_assignments) * 100, 2)
        if expected_assignments else 0
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
            "avg_attendance": avg_attendance,
            "assignment_completion": assignment_completion,
            "assignments_completed": completed_assignments,
            "assignments_expected": expected_assignments,
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

    attendance_rows = db.query(SessionParticipant).join(
        ClassSession,
        ClassSession.id == SessionParticipant.session_id
    ).filter(
        ClassSession.classroom_id == classroom.id
    ).all()
    attended_rows = [
        row for row in attendance_rows
        if row.status in ("present", "late")
    ]
    avg_attendance = (
        round((len(attended_rows) / len(attendance_rows)) * 100, 2)
        if attendance_rows else 0
    )

    assignments = db.query(Assignment).filter(
        Assignment.course_id == classroom.course_id,
        Assignment.batch_name == classroom.batch_name,
    ).all()
    assignment_ids = [assignment.id for assignment in assignments]
    completed_assignments = (
        db.query(AssignmentSubmission)
        .filter(
            AssignmentSubmission.assignment_id.in_(assignment_ids),
            AssignmentSubmission.status.in_(["submitted", "graded"]),
        )
        .count()
        if assignment_ids else 0
    )
    expected_assignments = len(assignments) * total_students
    assignment_completion = (
        round((completed_assignments / expected_assignments) * 100, 2)
        if expected_assignments else 0
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
            "avg_attendance": avg_attendance,
            "assignment_completion": assignment_completion,
            "assignments_completed": completed_assignments,
            "assignments_expected": expected_assignments,
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

    attendance_rows = db.query(SessionParticipant).join(
        ClassSession,
        ClassSession.id == SessionParticipant.session_id
    ).join(
        Classroom,
        Classroom.id == ClassSession.classroom_id
    ).filter(
        Classroom.course_id == course_id
    ).all()

    present_rows = [
        row for row in attendance_rows
        if row.status in ("present", "late")
    ]
    avg_attendance = (
        round((len(present_rows) / len(attendance_rows)) * 100, 2)
        if attendance_rows else 0
    )

    course_assignments = db.query(Assignment).filter(
        Assignment.course_id == course_id
    ).all()
    assignment_ids = [assignment.id for assignment in course_assignments]
    completed_assignment_submissions = (
        db.query(AssignmentSubmission)
        .filter(
            AssignmentSubmission.assignment_id.in_(assignment_ids),
            AssignmentSubmission.status.in_(["submitted", "graded"]),
        )
        .count()
        if assignment_ids else 0
    )

    expected_assignment_submissions = 0
    for assignment in course_assignments:
        classroom = db.query(Classroom).filter(
            Classroom.course_id == assignment.course_id,
            Classroom.batch_name == assignment.batch_name,
        ).first()
        if classroom:
            expected_assignment_submissions += db.query(Enrollment).filter(
                Enrollment.classroom_id == classroom.id
            ).count()

    assignment_completion = (
        round((completed_assignment_submissions / expected_assignment_submissions) * 100, 2)
        if expected_assignment_submissions else 0
    )

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

            "avg_attendance": avg_attendance,

            "assignment_completion": assignment_completion,

            "assignments_completed": completed_assignment_submissions,

            "assignments_expected": expected_assignment_submissions,

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


@router.get("/{course_id}/student-overview")
def student_course_overview(
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

    # Verify student is enrolled

    enrollment = (
        db.query(Enrollment)
        .join(
            Classroom,
            Classroom.id == Enrollment.classroom_id
        )
        .filter(
            Enrollment.user_id ==
            current_user["user_id"],
            Classroom.course_id ==
            course_id
        )
        .first()
    )

    if not enrollment:
        raise HTTPException(
            status_code=403,
            detail="Not enrolled in this course"
        )

    classroom = db.query(Classroom).filter(
        Classroom.id == enrollment.classroom_id
    ).first()

    instructor = (
        db.query(User).filter(User.id == classroom.instructor_id).first()
        if classroom and classroom.instructor_id else None
    )

    modules = (
        db.query(Module)
        .filter(
            Module.course_id == course_id
        )
        .all()
    )

    module_ids = [m.id for m in modules]

    chapters = []

    if module_ids:
        chapters = (
            db.query(Chapter)
            .filter(
                Chapter.module_id.in_(module_ids)
            )
            .all()
        )

    chapter_ids = [c.id for c in chapters]

  

    assignments = (
        db.query(Assignment)
        .filter(
            Assignment.course_id == course_id
        )
        .all()
    )

    tests = (
        db.query(Test)
        .filter(
            Test.course_id == course_id
        )
        .all()
    )

    assignment_ids = [a.id for a in assignments]

    test_ids = [t.id for t in tests]

    submitted_assignments = (
        db.query(AssignmentSubmission)
        .filter(
            AssignmentSubmission.student_user_id
            ==
            current_user["user_id"]
        )
        .all()
    )

    submitted_assignment_ids = [
        s.assignment_id
        for s in submitted_assignments
    ]

    test_submissions = (
        db.query(TestSubmission)
        .filter(
            TestSubmission.student_user_id
            ==
            current_user["user_id"]
        )
        .all()
    )

    completed_test_ids = [
        t.test_id
        for t in test_submissions
    ]

    return {

        "course": {

            "id": course.id,

            "course_code":
            course.course_code,

            "name":
            course.name,

            "description":
            course.description,

            "duration_months":
            course.duration_months,

            "total_lessons":
            course.total_lessons,

            "instructor_id":
            classroom.instructor_id if classroom else None,

            "instructor_name":
            instructor.name if instructor else (classroom.instructor_name if classroom else None)
        },

        "stats": {

            "total_modules":
            len(modules),

            "total_chapters":
            len(chapters),


            "total_assignments":
            len(assignments),

            "total_tests":
            len(tests),

            "completed_assignments":
            len(submitted_assignment_ids),

            "completed_tests":
            len(completed_test_ids),

            "progress_percent":
            enrollment.progress_percent
        },

        "modules": [

            {
                "module_id": m.id,
                "title": m.title,
                "order": m.order
            }

            for m in modules
        ],

        "chapters": [

            {
                "chapter_id": c.id,
                "module_id": c.module_id,
                "title": c.title,
                "order": c.order
            }

            for c in chapters
        ],


        "assignments": [

            {
                "assignment_id": a.id,

                "module_id":
                a.module_id,

                "title":
                a.title,

                "due_date":
                a.due_date,

                "submitted":
                a.id in submitted_assignment_ids
            }

            for a in assignments
        ],

        "tests": [

            {
                "test_id":
                t.id,

                "module_id":
                t.module_id,

                "title":
                t.title,

                "start_time":
                t.start_time,

                "end_time":
                t.end_time,

                "completed":
                t.id in completed_test_ids
            }

            for t in tests
        ]
    }

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
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
from app.models.schedule import CourseSchedule
from app.models.attendance import SessionParticipant
from app.models.announcements import Announcement
from app.models.chat import ChatPost
from app.models.registration_profile import InstructorInformation, StudentInformation
from app.services.classroom_stats import (
    classroom_dashboard_metrics,
    require_classroom_access,
)

router = APIRouter(
    prefix="/instructor",
    tags=["Instructor"]
)


class ScheduleUpdateRequest(BaseModel):
    day_of_week: str | None = None
    session_type: str | None = None
    topic: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    instructor_name: str | None = None


class AnnouncementCreateRequest(BaseModel):
    course_id: int
    classroom_id: int | None = None
    topic: str
    message: str

def get_my_classroom_ids(db: Session, instructor_id: int) -> list[int]:
    rows = (
        db.query(InstructorEnrollment.classroom_id)
        .filter(InstructorEnrollment.user_id == instructor_id)
        .all()
    )
    return [r.classroom_id for r in rows]


def require_instructor_user(current_user: dict):
    if current_user.get("role") not in ("instructor", "admin"):
        raise HTTPException(status_code=403, detail="Instructor access only")


def get_my_classrooms(db: Session, current_user: dict) -> list[Classroom]:
    require_instructor_user(current_user)
    if current_user.get("role") == "admin":
        return db.query(Classroom).all()
    classroom_ids = get_my_classroom_ids(db, current_user["user_id"])
    if not classroom_ids:
        return []
    return db.query(Classroom).filter(Classroom.id.in_(classroom_ids)).all()


def get_my_classroom_or_404(
    db: Session,
    current_user: dict,
    classroom_id: int,
) -> Classroom:
    classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")
    if current_user.get("role") != "admin" and classroom.id not in get_my_classroom_ids(db, current_user["user_id"]):
        raise HTTPException(status_code=403, detail="Not assigned to this batch")
    return classroom


def module_count_for_batch(db: Session, classroom: Classroom) -> int:
    return db.query(Module).filter(
        Module.course_id == classroom.course_id,
        or_(Module.batch_name == classroom.batch_name, Module.batch_name == None),
    ).count()


def batch_completion_progress(db: Session, classroom: Classroom) -> float:
    values = [
        row.progress_percent or 0
        for row in db.query(Enrollment)
        .filter(Enrollment.classroom_id == classroom.id)
        .all()
    ]
    return round(sum(values) / len(values), 2) if values else 0



# ============================================================================
# HELPER
# ============================================================================

def get_instructor_classrooms(
    db: Session,
    user_id: int
):
    return (
        db.query(
            InstructorEnrollment,
            Classroom,
            Course
        )
        .join(
            Classroom,
            Classroom.id == InstructorEnrollment.classroom_id
        )
        .join(
            Course,
            Course.id == Classroom.course_id
        )
        .filter(
            InstructorEnrollment.user_id == user_id
        )
        .all()
    )


# ============================================================================
# DASHBOARD OVERVIEW
# ============================================================================

@router.get("/")
def instructor_dashboard(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    if current_user["role"] != "instructor":
        raise HTTPException(
            status_code=403,
            detail="Instructor access only"
        )

    user_id = current_user["user_id"]

    instructor_rows = get_instructor_classrooms(
        db,
        user_id
    )

    if not instructor_rows:
        return {
            "summary": {
                "active_courses": 0,
                "total_students": 0,
                "live_sessions": 0,
                "pending_reviews": 0
            },
            "courses": [],
            "recent_sessions": [],
            "live_classes": [],
            "recent_tests": []
        }

    classroom_ids = list({
        row.Classroom.id
        for row in instructor_rows
    })

    course_ids = list({
        row.Course.id
        for row in instructor_rows
    })

    # ------------------------------------------------------------------------
    # SUMMARY
    # ------------------------------------------------------------------------

    total_students = (
        db.query(
            func.count(
                func.distinct(Enrollment.user_id)
            )
        )
        .filter(
            Enrollment.classroom_id.in_(classroom_ids)
        )
        .scalar()
    ) or 0

    live_sessions = (
        db.query(ClassSession)
        .filter(
            ClassSession.classroom_id.in_(classroom_ids),
            ClassSession.status == "live"
        )
        .count()
    )

    pending_reviews = 0

    try:
        pending_reviews = (
            db.query(AssignmentSubmission)
            .join(
                Assignment,
                Assignment.id == AssignmentSubmission.assignment_id
            )
            .filter(
                Assignment.created_by == user_id,
                AssignmentSubmission.status == "submitted"
            )
            .count()
        )
    except:
        pass

    summary = {
        "active_courses": len(course_ids),
        "total_students": total_students,
        "live_sessions": live_sessions,
        "pending_reviews": pending_reviews
    }

    # ------------------------------------------------------------------------
    # COURSES
    # ------------------------------------------------------------------------

    courses_data = []

    for row in instructor_rows:

        classroom = row.Classroom
        course = row.Course

        student_count = (
            db.query(Enrollment)
            .filter(
                Enrollment.classroom_id == classroom.id
            )
            .count()
        )

        courses_data.append({
            "classroom_id": classroom.id,
            "course_id": course.id,
            "course_name": course.name,
            "course_code": course.course_code,
            "batch_name": classroom.batch_name,
            "room_name": classroom.room_name,
            "students": student_count,
            "total_modules": module_count_for_batch(db, classroom),
            "batch_completion_progress": batch_completion_progress(db, classroom),
        })

    # ------------------------------------------------------------------------
    # RECENT SESSIONS
    # ------------------------------------------------------------------------

    sessions = (
        db.query(ClassSession)
        .filter(
            ClassSession.classroom_id.in_(classroom_ids)
        )
        .order_by(
            ClassSession.id.desc()
        )
        .limit(5)
        .all()
    )

    recent_sessions = []

    for session in sessions:

        classroom = db.query(Classroom).filter(
            Classroom.id == session.classroom_id
        ).first()

        present_count = (
            db.query(SessionParticipant)
            .filter(
                SessionParticipant.session_id == session.id,
                SessionParticipant.status == "present"
            )
            .count()
        )

        total_enrolled = (
            db.query(Enrollment)
            .filter(
                Enrollment.classroom_id == session.classroom_id
            )
            .count()
        )

        recent_sessions.append({
            "session_id": session.id,
            "batch_name": classroom.batch_name if classroom else None,
            "status": session.status,
            "start_time": session.start_time,
            "end_time": session.end_time,
            "attendance": {
                "present": present_count,
                "total": total_enrolled
            }
        })

    # ------------------------------------------------------------------------
    # LIVE CLASSES
    # ------------------------------------------------------------------------

    live_class_rows = (
        db.query(ClassSession)
        .filter(
            ClassSession.classroom_id.in_(classroom_ids),
            ClassSession.status == "live"
        )
        .all()
    )

    live_classes = []

    for session in live_class_rows:

        classroom = db.query(Classroom).filter(
            Classroom.id == session.classroom_id
        ).first()

        live_classes.append({
            "session_id": session.id,
            "batch_name": classroom.batch_name if classroom else None,
            "join_url": session.host_url,
            "status": session.status,
            "start_time": session.start_time
        })

    # ------------------------------------------------------------------------
    # TESTS
    # ------------------------------------------------------------------------

    recent_tests = []
    seen_test_ids = set()

    try:
        classroom_rows = (
            db.query(Classroom)
            .filter(Classroom.id.in_(classroom_ids))
            .all()
        )

        for classroom in classroom_rows:
            tests = (
                db.query(Test)
                .filter(
                    Test.course_id == classroom.course_id,
                    Test.batch_name == classroom.batch_name,
                )
                .order_by(Test.id.desc())
                .limit(5)
                .all()
            )

            for test in tests:
                if test.id in seen_test_ids:
                    continue

                seen_test_ids.add(test.id)
                submissions = (
                    db.query(TestSubmission)
                    .filter(TestSubmission.test_id == test.id)
                    .count()
                )
                passed = (
                    db.query(TestSubmission)
                    .filter(
                        TestSubmission.test_id == test.id,
                        TestSubmission.is_passed == True,
                    )
                    .count()
                )

                recent_tests.append({
                    "test_id": test.id,
                    "title": test.title,
                    "course_id": test.course_id,
                    "batch_name": test.batch_name,
                    "submissions": submissions,
                    "passed": passed,
                    "failed": submissions - passed,
                })

        recent_tests = sorted(recent_tests, key=lambda item: item["test_id"], reverse=True)[:5]

    except Exception:
        pass

    return {
        "summary": summary,
        "courses": courses_data,
        "recent_sessions": recent_sessions,
        "live_classes": live_classes,
        "recent_tests": recent_tests
    }


@router.get("/classrooms/{classroom_id}/stats")
def classroom_stats(
    classroom_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    classroom = require_classroom_access(db, current_user, classroom_id)
    return classroom_dashboard_metrics(db, classroom)


@router.get("/profile/details")
def instructor_profile_details(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    require_instructor_user(current_user)
    user = db.query(User).filter(User.id == current_user["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="Instructor not found")

    profile = db.query(InstructorInformation).filter(
        InstructorInformation.user_id == user.id
    ).first()
    classrooms = get_my_classrooms(db, current_user)

    assigned = []
    for classroom in classrooms:
        course = db.query(Course).filter(Course.id == classroom.course_id).first()
        assigned.append({
            "classroom_id": classroom.id,
            "course_id": classroom.course_id,
            "course_name": course.name if course else None,
            "course_code": course.course_code if course else None,
            "batch_name": classroom.batch_name,
            "batch_code": classroom.batch_code,
            "student_count": db.query(Enrollment).filter(
                Enrollment.classroom_id == classroom.id,
                Enrollment.status == "ongoing",
            ).count(),
        })

    classroom_ids = [classroom.id for classroom in classrooms]
    total_sessions = (
        db.query(ClassSession)
        .filter(ClassSession.classroom_id.in_(classroom_ids))
        .count()
        if classroom_ids else 0
    )
    live_sessions = (
        db.query(ClassSession)
        .filter(ClassSession.classroom_id.in_(classroom_ids), ClassSession.status == "live")
        .count()
        if classroom_ids else 0
    )
    attendance_rows = (
        db.query(SessionParticipant)
        .join(ClassSession, ClassSession.id == SessionParticipant.session_id)
        .filter(ClassSession.classroom_id.in_(classroom_ids))
        .all()
        if classroom_ids else []
    )
    present_rows = [row for row in attendance_rows if row.status in ("present", "late")]

    return {
        "user_id": user.id,
        "instructor_id": user.student_id,
        "name": profile.full_name if profile else user.name,
        "email": profile.email if profile else user.email,
        "phone_number": profile.phone_number if profile else None,
        "date_joined": profile.created_at.date().isoformat() if profile and profile.created_at else None,
        "bio": profile.bio if profile else None,
        "qualifications": profile.qualifications if profile else None,
        "experience_years": profile.experience_years if profile else None,
        "skills": profile.skills if profile else None,
        "specialization": profile.specialization if profile else None,
        "profile_image_url": profile.profile_image_url if profile else None,
        "address": {
            "address_line1": profile.address_line1 if profile else None,
            "address_line2": profile.address_line2 if profile else None,
            "city": profile.city if profile else None,
            "state": profile.state if profile else None,
            "country": profile.country if profile else None,
            "postal_code": profile.postal_code if profile else None,
        },
        "social_links": profile.social_links if profile else None,
        "account_status": profile.account_status if profile else "active",
        "session_attendance": {
            "total_sessions": total_sessions,
            "live_sessions": live_sessions,
            "attendance_records": len(attendance_rows),
            "present_records": len(present_rows),
            "attendance_percentage": (
                round((len(present_rows) / len(attendance_rows)) * 100, 2)
                if attendance_rows else 0
            ),
        },
        "assigned_batches": assigned,
    }

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


@router.get("/assignment-courses")
def assignment_batch_course_list(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    classrooms = get_my_classrooms(db, current_user)
    course_ids = [c.course_id for c in classrooms if c.course_id]
    courses_map = {
        c.id: c for c in db.query(Course).filter(Course.id.in_(course_ids)).all()
    } if course_ids else {}

    return [
        {
            "classroom_id": classroom.id,
            "course_id": classroom.course_id,
            "course_name": courses_map[classroom.course_id].name if classroom.course_id in courses_map else None,
            "course_code": courses_map[classroom.course_id].course_code if classroom.course_id in courses_map else None,
            "batch_name": classroom.batch_name,
            "batch_code": classroom.batch_code,
            "module_count": module_count_for_batch(db, classroom),
            "student_count": db.query(Enrollment).filter(
                Enrollment.classroom_id == classroom.id,
                Enrollment.status == "ongoing",
            ).count(),
        }
        for classroom in classrooms
    ]


@router.get("/upcoming-schedule")
def instructor_upcoming_schedule(
    classroom_id: int | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    classrooms = (
        [get_my_classroom_or_404(db, current_user, classroom_id)]
        if classroom_id else get_my_classrooms(db, current_user)
    )
    data = []

    for classroom in classrooms:
        course = db.query(Course).filter(Course.id == classroom.course_id).first()
        schedules = db.query(CourseSchedule).filter(
            CourseSchedule.course_id == classroom.course_id,
            CourseSchedule.batch_name == classroom.batch_name,
        ).order_by(CourseSchedule.id.asc()).all()

        for schedule in schedules:
            data.append({
                "schedule_id": schedule.id,
                "classroom_id": classroom.id,
                "course_id": classroom.course_id,
                "course_name": course.name if course else None,
                "course_code": course.course_code if course else None,
                "batch_name": classroom.batch_name,
                "day_of_week": schedule.day_of_week,
                "session_type": schedule.session_type,
                "topic": schedule.topic,
                "start_time": schedule.start_time,
                "end_time": schedule.end_time,
                "instructor_name": schedule.instructor_name or classroom.instructor_name,
            })

    return {"total": len(data), "schedule": data}


@router.put("/schedule/{schedule_id}")
def edit_schedule(
    schedule_id: int,
    payload: ScheduleUpdateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    schedule = db.query(CourseSchedule).filter(CourseSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    classroom = db.query(Classroom).filter(
        Classroom.course_id == schedule.course_id,
        Classroom.batch_name == schedule.batch_name,
    ).first()
    if classroom:
        get_my_classroom_or_404(db, current_user, classroom.id)
    else:
        require_instructor_user(current_user)

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(schedule, key, value)

    db.commit()
    db.refresh(schedule)

    return {
        "message": "Schedule updated successfully",
        "schedule_id": schedule.id,
        "course_id": schedule.course_id,
        "batch_name": schedule.batch_name,
        "day_of_week": schedule.day_of_week,
        "topic": schedule.topic,
        "session_type": schedule.session_type,
        "start_time": schedule.start_time,
        "end_time": schedule.end_time,
        "instructor_name": schedule.instructor_name,
    }


@router.get("/pending-review")
def pending_review(
    classroom_id: int | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    classrooms = (
        [get_my_classroom_or_404(db, current_user, classroom_id)]
        if classroom_id else get_my_classrooms(db, current_user)
    )
    rows = []

    for classroom in classrooms:
        course = db.query(Course).filter(Course.id == classroom.course_id).first()
        assignments = db.query(Assignment).filter(
            Assignment.course_id == classroom.course_id,
            Assignment.batch_name == classroom.batch_name,
        ).all()

        for assignment in assignments:
            module = db.query(Module).filter(Module.id == assignment.module_id).first()
            submissions = db.query(AssignmentSubmission).filter(
                AssignmentSubmission.assignment_id == assignment.id,
                AssignmentSubmission.status == "submitted",
            ).all()

            for submission in submissions:
                student = db.query(User).filter(User.id == submission.student_user_id).first()
                rows.append({
                    "assignment_id": assignment.id,
                    "assignment_title": assignment.title,
                    "course_id": classroom.course_id,
                    "course_name": course.name if course else None,
                    "course_code": course.course_code if course else None,
                    "module_id": module.id if module else None,
                    "module_name": module.title if module else None,
                    "batch_name": classroom.batch_name,
                    "submission_id": submission.id,
                    "submitted_at": submission.submitted_at,
                    "student_user_id": student.id if student else None,
                    "student_id": student.student_id if student else None,
                    "student_name": student.name if student else None,
                    "file_name": submission.file_name,
                })

    rows.sort(key=lambda item: item["submitted_at"] or datetime.min, reverse=True)
    return {"total_pending": len(rows), "items": rows}


@router.get("/batch/{classroom_id}/recent-activity")
def batch_recent_activity(
    classroom_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    classroom = get_my_classroom_or_404(db, current_user, classroom_id)
    activity = []

    sessions = db.query(ClassSession).filter(
        ClassSession.classroom_id == classroom.id
    ).order_by(ClassSession.id.desc()).limit(10).all()

    for session in sessions:
        activity.append({
            "type": "session",
            "id": session.id,
            "title": f"{classroom.batch_name} session",
            "status": session.status,
            "created_at": session.start_time,
        })

    assignments = db.query(Assignment).filter(
        Assignment.course_id == classroom.course_id,
        Assignment.batch_name == classroom.batch_name,
    ).order_by(Assignment.created_at.desc()).limit(10).all()

    for assignment in assignments:
        activity.append({
            "type": "assignment",
            "id": assignment.id,
            "title": assignment.title,
            "status": assignment.status,
            "created_at": assignment.created_at,
        })

    submissions = (
        db.query(AssignmentSubmission)
        .join(Assignment, Assignment.id == AssignmentSubmission.assignment_id)
        .filter(
            Assignment.course_id == classroom.course_id,
            Assignment.batch_name == classroom.batch_name,
        )
        .order_by(AssignmentSubmission.id.desc())
        .limit(10)
        .all()
    )

    for submission in submissions:
        student = db.query(User).filter(User.id == submission.student_user_id).first()
        activity.append({
            "type": "assignment_submission",
            "id": submission.id,
            "title": f"{student.name if student else 'Student'} submitted assignment",
            "status": submission.status,
            "created_at": submission.submitted_at,
        })

    activity.sort(key=lambda item: item["created_at"] or datetime.min, reverse=True)
    return {"classroom_id": classroom.id, "recent_activity": activity[:20]}


@router.get("/students/batch")
def get_students_by_batch(
    classroom_id: int | None = None,
    course_id: int | None = None,
    batch_name: str | None = None,
    search: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    classrooms = (
        [get_my_classroom_or_404(db, current_user, classroom_id)]
        if classroom_id else get_my_classrooms(db, current_user)
    )
    if course_id is not None:
        classrooms = [c for c in classrooms if c.course_id == course_id]
    if batch_name:
        classrooms = [c for c in classrooms if c.batch_name == batch_name]

    classroom_ids = [c.id for c in classrooms]
    if not classroom_ids:
        return {"total": 0, "students": []}

    query = db.query(User, Enrollment, Classroom).join(
        Enrollment, Enrollment.user_id == User.id
    ).join(
        Classroom, Classroom.id == Enrollment.classroom_id
    ).filter(
        Enrollment.classroom_id.in_(classroom_ids)
    )
    if search:
        query = query.filter(func.lower(User.name).like(f"%{search.strip().lower()}%"))

    students = []
    for user, enrollment, classroom in query.all():
        course = db.query(Course).filter(Course.id == classroom.course_id).first()
        students.append({
            "user_id": user.id,
            "student_id": user.student_id or str(user.id),
            "name": user.name,
            "email": user.email,
            "classroom_id": classroom.id,
            "course_id": classroom.course_id,
            "course_name": course.name if course else None,
            "course_code": course.course_code if course else None,
            "batch_name": classroom.batch_name,
            "progress_percent": enrollment.progress_percent,
            "status": enrollment.status,
        })

    return {"total": len(students), "students": students}

@router.get("/students")
def get_students(
    classroom_id: int | None = None,
    course_id: int | None = None,
    batch_name: str | None = None,
    search: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    classroom_ids = get_my_classroom_ids(db, current_user["user_id"])
    classrooms = db.query(Classroom).filter(Classroom.id.in_(classroom_ids)).all()

    if classroom_id is not None:
        classrooms = [c for c in classrooms if c.id == classroom_id]
    if course_id is not None:
        classrooms = [c for c in classrooms if c.course_id == course_id]
    if batch_name:
        classrooms = [c for c in classrooms if c.batch_name == batch_name]

    classroom_ids = [c.id for c in classrooms]
    
    if not classroom_ids:
        return []

    # Query distinct User profiles directly to dodge JSON sorting crashes in Postgres
    query = (
        db.query(User, Enrollment, Classroom)
        .join(Enrollment, Enrollment.user_id == User.id)
        .join(Classroom, Classroom.id == Enrollment.classroom_id)
        .filter(Enrollment.classroom_id.in_(classroom_ids))
    )
    
    if search:
        search_filter = f"%{search.strip().lower()}%"
        query = query.filter(func.lower(User.name).like(search_filter))
        
    rows = query.distinct().all()
    student_ids = [row.User.id for row in rows]

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
    for row in rows:
        s = row.User
        enrollment = row.Enrollment
        classroom = row.Classroom
        course = db.query(Course).filter(Course.id == classroom.course_id).first()
        prof = profiles_map.get(s.id)
        display_student_id = s.student_id or (str(prof.id) if prof else str(s.id))
        result.append({
            "id": s.id,
            "student_id": display_student_id,
            "name": s.name,
            "email": s.email,
            "classroom_id": classroom.id,
            "course_id": classroom.course_id,
            "course_name": course.name if course else None,
            "course_code": course.course_code if course else None,
            "batch_name": classroom.batch_name,
            "progress_percent": enrollment.progress_percent,
            "status": enrollment.status,
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

    submissions = db.query(AssignmentSubmission).filter(
        AssignmentSubmission.student_user_id == student.id
    ).order_by(AssignmentSubmission.id.desc()).all()
    tests = db.query(TestSubmission).filter(
        TestSubmission.student_user_id == student.id
    ).order_by(TestSubmission.id.desc()).all()

    scores = [t.score_percentage for t in tests if t.score_percentage is not None]
    recent_activity = []
    assignment_performance = []

    for sub in submissions[:10]:
        assignment = db.query(Assignment).filter(Assignment.id == sub.assignment_id).first()
        course = db.query(Course).filter(Course.id == assignment.course_id).first() if assignment else None
        module = db.query(Module).filter(Module.id == assignment.module_id).first() if assignment else None
        item = {
            "submission_id": sub.id,
            "assignment_id": assignment.id if assignment else None,
            "assignment_title": assignment.title if assignment else None,
            "course_code": course.course_code if course else None,
            "course_name": course.name if course else None,
            "module_name": module.title if module else None,
            "status": sub.status,
            "grade": sub.grade,
            "submitted_at": sub.submitted_at,
        }
        assignment_performance.append(item)
        recent_activity.append({
            "type": "assignment_submission",
            "title": item["assignment_title"],
            "status": sub.status,
            "created_at": sub.submitted_at,
        })

    test_performance = []
    for test_sub in tests[:10]:
        test = db.query(Test).filter(Test.id == test_sub.test_id).first()
        course = db.query(Course).filter(Course.id == test.course_id).first() if test else None
        module = db.query(Module).filter(Module.id == test.module_id).first() if test else None
        item = {
            "submission_id": test_sub.id,
            "test_id": test.id if test else None,
            "test_title": test.title if test else None,
            "course_code": course.course_code if course else None,
            "course_name": course.name if course else None,
            "module_name": module.title if module else None,
            "status": test_sub.status,
            "score_percentage": test_sub.score_percentage,
            "is_passed": test_sub.is_passed,
            "submitted_at": test_sub.submitted_at,
        }
        test_performance.append(item)
        recent_activity.append({
            "type": "test_submission",
            "title": item["test_title"],
            "status": test_sub.status,
            "created_at": test_sub.submitted_at or test_sub.started_at,
        })

    recent_activity.sort(key=lambda item: item["created_at"] or datetime.min, reverse=True)

    return {
        "id": student.id,
        "student_id": profile.id if profile else student.id, # Fixed attribute missing issue
        "name": student.name,
        "email": profile.email if profile else student.email,
        "contact": profile.phone_number if profile else None,
        "stats": {
            "overall_attendance": f"{attendance_percent}%",
            "average_score": f"{round(sum(scores) / len(scores), 2)}%" if scores else "0%",
            "live_participation": "Good",
            "classes_attended": attended
        },
        "assignment_performance": assignment_performance,
        "test_performance": test_performance,
        "attendance_details": [],
        "recent_activity": recent_activity[:20]
    }

@router.get("/resources")
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
            "view_url": f"/resources/{r.id}/view",
            "download_url": f"/resources/{r.id}/download",
            "uploaded_at": r.uploaded_at
        }
        for r in resources
    ]


@router.get("/faqs")
def instructor_faqs(
    classroom_id: int | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    classrooms = (
        [get_my_classroom_or_404(db, current_user, classroom_id)]
        if classroom_id else get_my_classrooms(db, current_user)
    )
    faqs = []

    for classroom in classrooms:
        course = db.query(Course).filter(Course.id == classroom.course_id).first()
        posts = db.query(ChatPost).filter(
            ChatPost.course_id == classroom.course_id,
            ChatPost.batch_name == classroom.batch_name,
        ).order_by(ChatPost.is_pinned.desc(), ChatPost.created_at.desc()).all()

        for post in posts:
            author = db.query(User).filter(User.id == post.author_id).first()
            faqs.append({
                "question_id": post.id,
                "course_id": classroom.course_id,
                "course_name": course.name if course else None,
                "course_code": course.course_code if course else None,
                "batch_name": classroom.batch_name,
                "question": post.content,
                "visibility": post.visibility,
                "is_pinned": post.is_pinned,
                "reply_count": len(post.replies),
                "author_id": author.id if author else None,
                "author_name": author.name if author else None,
                "created_at": post.created_at,
            })

    return {"total": len(faqs), "faqs": faqs}


@router.get("/announcements")
def instructor_announcements(
    classroom_id: int | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    classrooms = (
        [get_my_classroom_or_404(db, current_user, classroom_id)]
        if classroom_id else get_my_classrooms(db, current_user)
    )
    classroom_ids = [c.id for c in classrooms]
    if not classroom_ids:
        return {"total": 0, "announcements": []}

    rows = db.query(Announcement).filter(
        Announcement.classroom_id.in_(classroom_ids)
    ).order_by(Announcement.created_at.desc()).all()

    return {
        "total": len(rows),
        "announcements": [
            {
                "announcement_id": row.id,
                "course_id": row.course_id,
                "classroom_id": row.classroom_id,
                "topic": row.topic,
                "message": row.message,
                "created_at": row.created_at,
            }
            for row in rows
        ],
    }


@router.post("/announcements")
def create_announcement(
    payload: AnnouncementCreateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    require_instructor_user(current_user)
    classroom = None
    if payload.classroom_id:
        classroom = get_my_classroom_or_404(db, current_user, payload.classroom_id)
        if classroom.course_id != payload.course_id:
            raise HTTPException(status_code=400, detail="Classroom does not belong to this course")

    announcement = Announcement(
        instructor_id=current_user["user_id"],
        course_id=payload.course_id,
        classroom_id=payload.classroom_id,
        topic=payload.topic,
        message=payload.message,
    )
    db.add(announcement)
    db.commit()
    db.refresh(announcement)

    return {
        "message": "Announcement created successfully",
        "announcement_id": announcement.id,
        "course_id": announcement.course_id,
        "classroom_id": announcement.classroom_id,
        "topic": announcement.topic,
        "created_at": announcement.created_at,
    }

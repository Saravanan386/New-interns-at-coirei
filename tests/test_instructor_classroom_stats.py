from datetime import datetime, timedelta

from app.models.assignment import Assignment
from app.models.attendance import SessionParticipant
from app.models.classroom import Classroom
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.instructor_enrollment import InstructorEnrollment
from app.models.module import Module
from app.models.session import ClassSession
from app.models.test import Test, TestSubmission
from app.models.user import User
from app.utils.security import hash_password


def _create_user(db_session, name: str, email: str, password: str, role: str):
    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        role=role,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _login(client, email: str, password: str) -> str:
    response = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def test_instructor_classroom_stats_and_batch_overview(client, db_session):
    instructor = _create_user(
        db_session,
        "Stats Instructor",
        "stats-instructor@example.com",
        "instructor123",
        "instructor",
    )
    student = _create_user(
        db_session,
        "Stats Student",
        "stats-student@example.com",
        "student123",
        "student",
    )

    course = Course(
        course_code="STATS101",
        name="Statistics Ready Course",
        description="Course used for dashboard stats tests",
    )
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)

    classroom = Classroom(
        course_id=course.id,
        batch_name="Batch-A",
        room_name="Stats Room",
    )
    db_session.add(classroom)
    db_session.commit()
    db_session.refresh(classroom)

    db_session.add(
        InstructorEnrollment(
            user_id=instructor.id,
            classroom_id=classroom.id,
        )
    )
    db_session.add(
        Enrollment(
            user_id=student.id,
            classroom_id=classroom.id,
            progress_percent=50,
            status="ongoing",
        )
    )

    module = Module(
        title="Module 1",
        order=1,
        status="active",
        course_id=course.id,
        batch_name=classroom.batch_name,
    )
    db_session.add(module)
    db_session.commit()
    db_session.refresh(module)

    assignment = Assignment(
        course_id=course.id,
        batch_name=classroom.batch_name,
        module_id=module.id,
        title="Assignment 1",
        description="Test assignment",
        created_by=instructor.id,
    )
    db_session.add(assignment)

    test = Test(
        title="Test 1",
        description="Test entry",
        course_id=course.id,
        batch_name=classroom.batch_name,
        module_id=module.id,
        created_by=instructor.id,
    )
    db_session.add(test)
    db_session.commit()
    db_session.refresh(assignment)
    db_session.refresh(test)

    ended_session = ClassSession(
        classroom_id=classroom.id,
        livekit_room_name="room-ended",
        host_url="http://example.com/ended",
        join_url="http://example.com/ended-join",
        status="ended",
        start_time=datetime.utcnow() - timedelta(days=1),
        end_time=datetime.utcnow() - timedelta(days=1, minutes=-45),
    )
    live_session = ClassSession(
        classroom_id=classroom.id,
        livekit_room_name="room-live",
        host_url="http://example.com/live",
        join_url="http://example.com/live-join",
        status="live",
        start_time=datetime.utcnow(),
    )
    db_session.add_all([ended_session, live_session])
    db_session.commit()
    db_session.refresh(ended_session)
    db_session.refresh(live_session)

    db_session.add(
        SessionParticipant(
            session_id=ended_session.id,
            user_id=student.id,
            join_time=datetime.utcnow() - timedelta(minutes=40),
            leave_time=datetime.utcnow() - timedelta(minutes=5),
            duration_minutes=35,
            status="present",
        )
    )
    db_session.add(
        TestSubmission(
            test_id=test.id,
            student_user_id=student.id,
            started_at=datetime.utcnow() - timedelta(hours=1),
            submitted_at=datetime.utcnow(),
            obtained_marks=88,
            total_marks=100,
            score_percentage=88.0,
            is_passed=True,
            status="submitted",
        )
    )
    db_session.commit()

    instructor_token = _login(client, "stats-instructor@example.com", "instructor123")

    stats_response = client.get(
        f"/instructor/classrooms/{classroom.id}/stats",
        headers={"Authorization": f"Bearer {instructor_token}"},
    )
    assert stats_response.status_code == 200, stats_response.text
    stats = stats_response.json()

    assert stats["classroom_id"] == classroom.id
    assert stats["course_id"] == course.id
    assert stats["total_students"] == 1
    assert stats["completed_classes"] == 1
    assert stats["total_classes"] == 2
    assert stats["assignment_count"] == 1
    assert stats["test_count"] == 1
    assert stats["attendance_percentage"] == 100.0

    overview_response = client.get(
        f"/batches/{course.id}/{classroom.batch_name}/overview",
        headers={"Authorization": f"Bearer {instructor_token}"},
    )
    assert overview_response.status_code == 200, overview_response.text
    overview = overview_response.json()

    assert overview["classes_completed"] == 1
    assert overview["classes_total"] == 2
    assert overview["total_students"] == 1
    assert overview["attendance_rate"] == 100.0
    assert overview["average_score"] == 88.0

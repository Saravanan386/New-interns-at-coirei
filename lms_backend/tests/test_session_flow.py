from app.models.classroom import Classroom
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.instructor_enrollment import InstructorEnrollment
from app.models.user import User
from app.utils.security import hash_password


def _create_user(db, name: str, email: str, password: str, role: str):
    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _login(client, email: str, password: str):
    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_complete_session_flow(client, db_session, monkeypatch):
    instructor = _create_user(
        db_session,
        "Instructor User",
        "instructor@lms.com",
        "instructor123",
        "instructor",
    )
    student = _create_user(
        db_session,
        "Student User",
        "student@lms.com",
        "student123",
        "student",
    )

    course = Course(course_code="PY101", name="Python Foundations")
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)

    classroom = Classroom(
        course_id=course.id,
        batch_name="Batch-A",
        room_name="Room A",
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
            status="ongoing",
        )
    )
    db_session.commit()

    def close_background_task(coro):
        coro.close()
        return None

    monkeypatch.setattr("app.routers.sessions.asyncio.create_task", close_background_task)

    instructor_token = _login(client, "instructor@lms.com", "instructor123")
    student_token = _login(client, "student@lms.com", "student123")

    start = client.post(
        "/sessions/start",
        params={"classroom_id": classroom.id},
        headers={"Authorization": f"Bearer {instructor_token}"},
    )

    assert start.status_code == 200

    join = client.post(
        "/sessions/join",
        params={"classroom_id": classroom.id},
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert join.status_code == 200
    assert join.json()["status"] == "joined"

    session_id = start.json()["session_id"]

    end = client.post(
        "/sessions/end",
        params={"session_id": session_id},
        headers={"Authorization": f"Bearer {instructor_token}"},
    )

    assert end.status_code == 200
    assert end.json()["session_id"] == session_id

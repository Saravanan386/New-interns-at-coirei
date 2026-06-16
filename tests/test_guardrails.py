from app.models.classroom import Classroom
from app.models.course import Course
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


def test_register_rejects_invalid_role(client):
    response = client.post(
        "/auth/register",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "password123",
            "role": "moderator",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid role"


def test_login_rejects_invalid_password(client):
    client.post(
        "/auth/register",
        json={
            "name": "Admin User",
            "email": "admin@lms.com",
            "password": "admin123",
            "role": "admin",
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "admin@lms.com",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_register_rejects_duplicate_email(client):
    first = client.post(
        "/auth/register",
        json={
            "name": "Duplicate User",
            "email": "duplicate@lms.com",
            "password": "password123",
            "role": "student",
        },
    )
    assert first.status_code == 200

    second = client.post(
        "/auth/register",
        json={
            "name": "Duplicate User Again",
            "email": "duplicate@lms.com",
            "password": "password123",
            "role": "student",
        },
    )

    assert second.status_code == 400
    assert second.json()["detail"] == "Email already registered"


def test_protected_route_requires_auth(client):
    response = client.get("/sessions/active", params={"classroom_id": 1})

    assert response.status_code in (401, 403)


def test_instructor_cannot_start_unassigned_session(client, db_session, monkeypatch):
    instructor = _create_user(
        db_session,
        "Instructor User",
        "instructor@lms.com",
        "instructor123",
        "instructor",
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

    monkeypatch.setattr(
        "app.routers.sessions.create_room",
        lambda room_name: {
            "room_id": room_name,
            "host_url": f"https://example.com/{room_name}",
            "guest_url": f"https://example.com/{room_name}",
        },
    )

    login = client.post(
        "/auth/login",
        json={
            "email": "instructor@lms.com",
            "password": "instructor123",
        },
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    response = client.post(
        "/sessions/start",
        params={"classroom_id": classroom.id},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "You are not assigned to this classroom"


def test_student_cannot_start_session(client, db_session, monkeypatch):
    student = _create_user(
        db_session,
        "Student User",
        "student-session@lms.com",
        "student123",
        "student",
    )

    course = Course(course_code="PY103", name="Python Security")
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)

    classroom = Classroom(
        course_id=course.id,
        batch_name="Batch-C",
        room_name="Room C",
    )
    db_session.add(classroom)
    db_session.commit()
    db_session.refresh(classroom)

    monkeypatch.setattr(
        "app.routers.sessions.create_room",
        lambda room_name: {
            "room_id": room_name,
            "host_url": f"https://example.com/{room_name}",
            "guest_url": f"https://example.com/{room_name}",
        },
    )

    login = client.post(
        "/auth/login",
        json={
            "email": "student-session@lms.com",
            "password": "student123",
        },
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    response = client.post(
        "/sessions/start",
        params={"classroom_id": classroom.id},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Only instructors can start sessions"


def test_instructor_can_start_assigned_session(client, db_session, monkeypatch):
    instructor = _create_user(
        db_session,
        "Instructor User",
        "assigned-instructor@lms.com",
        "instructor123",
        "instructor",
    )

    course = Course(course_code="PY102", name="Python Advanced")
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)

    classroom = Classroom(
        course_id=course.id,
        batch_name="Batch-B",
        room_name="Room B",
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
    db_session.commit()

    monkeypatch.setattr(
        "app.routers.sessions.create_room",
        lambda room_name: {
            "room_id": room_name,
            "host_url": f"https://example.com/{room_name}",
            "guest_url": f"https://example.com/{room_name}",
        },
    )

    login = client.post(
        "/auth/login",
        json={
            "email": "assigned-instructor@lms.com",
            "password": "instructor123",
        },
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    response = client.post(
        "/sessions/start",
        params={"classroom_id": classroom.id},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "live"
    assert body["classroom_id"] == classroom.id

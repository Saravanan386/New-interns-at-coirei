from urllib.parse import parse_qs, urlsplit

import jwt

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


def test_session_access_issues_jitsi_jwt(client, db_session, monkeypatch):
    import app.routers.sessions as sessions_router
    import app.services.jitsi_auth as jitsi_auth

    monkeypatch.setattr(jitsi_auth, "JITSI_APP_ID", "lms-app")
    monkeypatch.setattr(jitsi_auth, "JITSI_APP_SECRET", "lms-secret")
    monkeypatch.setattr(jitsi_auth, "JITSI_BASE_URL", "http://jitsi.localhost:8080")
    monkeypatch.setattr(jitsi_auth, "JITSI_DOMAIN", "http://jitsi.localhost:8080")
    monkeypatch.setattr(jitsi_auth, "JITSI_JWT_SUBJECT", "jitsi.localhost")
    monkeypatch.setattr(sessions_router, "JITSI_BASE_URL", "http://jitsi.localhost:8080")

    instructor = _create_user(
        db_session,
        "Jitsi Instructor",
        "jitsi-instructor@tests.com",
        "instructor123",
        "instructor",
    )
    student = _create_user(
        db_session,
        "Jitsi Student",
        "jitsi-student@tests.com",
        "student123",
        "student",
    )

    course = Course(course_code="JT101", name="Jitsi Testing")
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)

    classroom = Classroom(
        course_id=course.id,
        batch_name="Batch-J",
        room_name="Jitsi Room",
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

    instructor_token = _login(client, "jitsi-instructor@tests.com", "instructor123")
    student_token = _login(client, "jitsi-student@tests.com", "student123")

    start_response = client.post(
        "/sessions/start",
        params={"classroom_id": classroom.id},
        headers={"Authorization": f"Bearer {instructor_token}"},
    )
    assert start_response.status_code == 200, start_response.text

    start_body = start_response.json()
    assert start_body["meet_link"].startswith("http://jitsi.localhost:8080/")
    assert "jwt=" in start_body["meet_link"]

    access_response = client.post(
        f"/sessions/{start_body['session_id']}/access",
        headers={"Authorization": f"Bearer {instructor_token}"},
    )
    assert access_response.status_code == 200, access_response.text

    access_body = access_response.json()
    assert access_body["domain"] == "http://jitsi.localhost:8080"
    assert access_body["display_name"] == "Jitsi Instructor"
    assert access_body["role"] == "instructor"

    parsed = urlsplit(access_body["meeting_url"])
    token = parse_qs(parsed.query)["jwt"][0]
    claims = jwt.decode(token, "lms-secret", algorithms=["HS256"], audience="jitsi")

    assert claims["room"] == access_body["room_name"]
    assert claims["context"]["user"]["name"] == "Jitsi Instructor"
    assert claims["context"]["user"]["moderator"] is True

    join_response = client.post(
        "/sessions/join",
        params={"classroom_id": classroom.id},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert join_response.status_code == 200, join_response.text
    join_body = join_response.json()
    assert join_body["status"] == "joined"
    assert join_body["meet_link"].startswith("http://jitsi.localhost:8080/")

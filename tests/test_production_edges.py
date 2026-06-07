import os
import uuid
from datetime import datetime, timedelta, timezone

from app.models.assignment import Assignment, AssignmentResource, AssignmentSubmission
from app.models.assignment import AssignmentResource
from app.models.attendance import SessionParticipant
from app.models.classroom import Classroom
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.instructor_enrollment import InstructorEnrollment
from app.models.module import Module
from app.models.notification import Notification
from app.models.session import ClassSession
from app.models.test import Test as QuizTest
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
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def _seed_learning_context(db_session, course_code: str, batch_name: str):
    instructor = _create_user(
        db_session,
        "Instructor User",
        f"instructor-{course_code.lower()}@tests.com",
        "instructor123",
        "instructor",
    )
    student = _create_user(
        db_session,
        "Student User",
        f"student-{course_code.lower()}@tests.com",
        "student123",
        "student",
    )

    course = Course(course_code=course_code, name=f"{course_code} Course")
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)

    classroom = Classroom(
        course_id=course.id,
        batch_name=batch_name,
        room_name=f"{batch_name} Room",
    )
    db_session.add(classroom)
    db_session.commit()
    db_session.refresh(classroom)

    module = Module(
        title=f"{course_code} Module",
        order=1,
        course_id=course.id,
        batch_name=batch_name,
    )
    db_session.add(module)
    db_session.commit()
    db_session.refresh(module)

    db_session.add(
        Enrollment(
            user_id=student.id,
            classroom_id=classroom.id,
            status="ongoing",
        )
    )
    db_session.commit()

    return instructor, student, course, classroom, module


def test_assignment_grading_updates_submission_state(client, db_session):
    instructor, student, course, classroom, module = _seed_learning_context(
        db_session,
        "GR101",
        "Batch-G",
    )

    instructor_token = _login(client, "instructor-gr101@tests.com", "instructor123")
    student_token = _login(client, "student-gr101@tests.com", "student123")

    create_response = client.post(
        "/assignments/",
        data={
            "course_id": str(course.id),
            "batch_name": classroom.batch_name,
            "module_id": str(module.id),
            "title": "Grading Drill",
            "description": "Submit and grade this assignment",
            "expected_outcome": "A reviewable submission",
            "due_date": "2026-06-15T10:00:00",
        },
        headers={"Authorization": f"Bearer {instructor_token}"},
    )
    assert create_response.status_code == 201, create_response.text

    assignment = db_session.query(Assignment).filter(Assignment.title == "Grading Drill").first()
    assert assignment is not None

    submit_response = client.post(
        f"/assignments/{assignment.id}/submit",
        data={"submission_text": "Initial submission"},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert submit_response.status_code == 200

    submission = db_session.query(AssignmentSubmission).filter(
        AssignmentSubmission.assignment_id == assignment.id,
        AssignmentSubmission.student_user_id == student.id,
    ).first()
    assert submission is not None

    grade_response = client.put(
        f"/assignments/{assignment.id}/submissions/{submission.id}/grade",
        data={
            "grade": "A",
            "feedback": "Strong work",
        },
        headers={"Authorization": f"Bearer {instructor_token}"},
    )
    assert grade_response.status_code == 200
    assert grade_response.json()["grade"] == "A"

    refreshed_submission = client.get(
        f"/assignments/{assignment.id}/my-submission",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert refreshed_submission.status_code == 200
    payload = refreshed_submission.json()
    assert payload["status"] == "graded"
    assert payload["grade"] == "A"
    assert payload["feedback"] == "Strong work"

    submissions_response = client.get(
        f"/assignments/{assignment.id}/submissions",
        headers={"Authorization": f"Bearer {instructor_token}"},
    )
    assert submissions_response.status_code == 200
    rows = submissions_response.json()["students"]
    assert rows[0]["status"] == "graded"
    assert rows[0]["grade"] == "A"


def test_student_cannot_grade_assignment(client, db_session):
    instructor, student, course, classroom, module = _seed_learning_context(
        db_session,
        "GR102",
        "Batch-G2",
    )

    instructor_token = _login(client, "instructor-gr102@tests.com", "instructor123")
    student_token = _login(client, "student-gr102@tests.com", "student123")

    create_response = client.post(
        "/assignments/",
        data={
            "course_id": str(course.id),
            "batch_name": classroom.batch_name,
            "module_id": str(module.id),
            "title": "Guarded Grading",
            "description": "A submission that should not be gradeable by a student",
            "expected_outcome": "Role enforcement",
            "due_date": "2026-06-15T10:00:00",
        },
        headers={"Authorization": f"Bearer {instructor_token}"},
    )
    assert create_response.status_code == 201, create_response.json()

    assignment = db_session.query(Assignment).filter(Assignment.title == "Guarded Grading").first()
    assert assignment is not None

    submit_response = client.post(
        f"/assignments/{assignment.id}/submit",
        data={"submission_text": "Student submission"},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert submit_response.status_code == 200

    submission = db_session.query(AssignmentSubmission).filter(
        AssignmentSubmission.assignment_id == assignment.id,
        AssignmentSubmission.student_user_id == student.id,
    ).first()
    assert submission is not None

    grade_response = client.put(
        f"/assignments/{assignment.id}/submissions/{submission.id}/grade",
        data={"grade": "A"},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert grade_response.status_code == 403


def test_assignment_submission_accepts_uploaded_file(client, db_session):
    instructor, student, course, classroom, module = _seed_learning_context(
        db_session,
        "UP101",
        "Batch-U",
    )

    instructor_token = _login(client, "instructor-up101@tests.com", "instructor123")
    student_token = _login(client, "student-up101@tests.com", "student123")

    create_response = client.post(
        "/assignments/",
        data={
            "course_id": str(course.id),
            "batch_name": classroom.batch_name,
            "module_id": str(module.id),
            "title": "Upload Ready",
            "description": "Submit with an attachment",
            "expected_outcome": "A file-backed submission",
            "due_date": "2026-06-15T10:00:00",
        },
        headers={"Authorization": f"Bearer {instructor_token}"},
    )
    assert create_response.status_code == 201, create_response.json()

    assignment = db_session.query(Assignment).filter(Assignment.title == "Upload Ready").first()
    assert assignment is not None

    submit_response = client.post(
        f"/assignments/{assignment.id}/submit",
        data={"submission_text": "Here is my file"},
        files={"file": ("submission.txt", b"hello world", "text/plain")},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert submit_response.status_code == 200
    body = submit_response.json()
    assert body["status"] == "submitted"
    assert body["file_name"] == "submission.txt"
    assert body["file_path"]


def test_assignment_resource_download_is_authorized(client, db_session):
    instructor, student, course, classroom, module = _seed_learning_context(
        db_session,
        "RS101",
        "Batch-R",
    )
    outsider = _create_user(
        db_session,
        "Outside Student",
        "outside-rs101@tests.com",
        "outsider123",
        "student",
    )

    instructor_token = _login(client, "instructor-rs101@tests.com", "instructor123")
    student_token = _login(client, "student-rs101@tests.com", "student123")
    outsider_token = _login(client, "outside-rs101@tests.com", "outsider123")

    create_response = client.post(
        "/assignments/",
        data={
            "course_id": str(course.id),
            "batch_name": classroom.batch_name,
            "module_id": str(module.id),
            "title": "Resource Pack",
            "description": "Has an attachment",
            "expected_outcome": "Attachment download",
            "due_date": "2026-06-15T10:00:00",
        },
        headers={"Authorization": f"Bearer {instructor_token}"},
    )
    assert create_response.status_code == 201

    assignment = db_session.query(Assignment).filter(Assignment.title == "Resource Pack").first()
    assert assignment is not None

    resource_dir = os.path.join("uploads", "assignments", f"test-{uuid.uuid4().hex}")
    os.makedirs(resource_dir, exist_ok=True)
    resource_path = os.path.join(resource_dir, "guide.txt")
    with open(resource_path, "wb") as handle:
        handle.write(b"resource content")

    resource = AssignmentResource(
        assignment_id=assignment.id,
        file_name="guide.txt",
        file_path=resource_path,
        file_type="text/plain",
    )
    db_session.add(resource)
    db_session.commit()
    db_session.refresh(resource)

    download_response = client.get(
        f"/assignments/resources/{resource.id}/download",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert download_response.status_code == 200
    assert download_response.content == b"resource content"

    outsider_response = client.get(
        f"/assignments/resources/{resource.id}/download",
        headers={"Authorization": f"Bearer {outsider_token}"},
    )
    assert outsider_response.status_code == 403

    view_response = client.get(
        f"/assignments/resources/{resource.id}/view",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert view_response.status_code == 200
    assert view_response.content == b"resource content"


def test_notifications_are_user_scoped(client, db_session):
    owner = _create_user(
        db_session,
        "Notification Owner",
        "owner@tests.com",
        "owner123",
        "student",
    )
    other_user = _create_user(
        db_session,
        "Notification Other",
        "other@tests.com",
        "other123",
        "student",
    )

    notification = Notification(
        user_id=owner.id,
        type="assignment",
        title="Assignment Ready",
        message="Your assignment has been posted.",
        is_read=False,
        related_id=99,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(notification)
    db_session.commit()
    db_session.refresh(notification)

    owner_token = _login(client, "owner@tests.com", "owner123")
    other_token = _login(client, "other@tests.com", "other123")

    list_response = client.get(
        "/notifications/",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert list_response.status_code == 200
    payload = list_response.json()
    assert payload["unread_count"] == 1
    assert payload["groups"][0]["notifications"][0]["title"] == "Assignment Ready"

    mark_response = client.patch(
        f"/notifications/{notification.id}/read",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert mark_response.status_code == 200
    assert mark_response.json()["is_read"] is True

    updated_list = client.get(
        "/notifications/",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert updated_list.status_code == 200
    assert updated_list.json()["unread_count"] == 0

    other_mark_response = client.patch(
        f"/notifications/{notification.id}/read",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert other_mark_response.status_code == 404

    other_delete_response = client.delete(
        f"/notifications/{notification.id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert other_delete_response.status_code == 404


def test_notifications_mark_all_and_delete(client, db_session):
    owner = _create_user(
        db_session,
        "Notification Bulk Owner",
        "bulk-owner@tests.com",
        "owner123",
        "student",
    )
    other = _create_user(
        db_session,
        "Notification Bulk Other",
        "bulk-other@tests.com",
        "other123",
        "student",
    )

    first = Notification(
        user_id=owner.id,
        type="system",
        title="First",
        message="First message",
        is_read=False,
        created_at=datetime.now(timezone.utc),
    )
    second = Notification(
        user_id=owner.id,
        type="system",
        title="Second",
        message="Second message",
        is_read=False,
        created_at=datetime.now(timezone.utc),
    )
    outsider_notification = Notification(
        user_id=other.id,
        type="system",
        title="Other",
        message="Other message",
        is_read=False,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add_all([first, second, outsider_notification])
    db_session.commit()
    db_session.refresh(first)
    db_session.refresh(second)
    db_session.refresh(outsider_notification)

    owner_token = _login(client, "bulk-owner@tests.com", "owner123")
    other_token = _login(client, "bulk-other@tests.com", "other123")

    mark_all_response = client.patch(
        "/notifications/read-all",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert mark_all_response.status_code == 200
    assert "2 notification(s)" in mark_all_response.json()["message"]

    db_session.expire_all()
    refreshed = db_session.query(Notification).filter(Notification.user_id == owner.id).all()
    assert all(notification.is_read for notification in refreshed)

    delete_response = client.delete(
        f"/notifications/{first.id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert delete_response.status_code == 200

    outsider_delete_response = client.delete(
        f"/notifications/{outsider_notification.id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert outsider_delete_response.status_code == 404

    other_mark_all = client.patch(
        "/notifications/read-all",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert other_mark_all.status_code == 200


def test_session_end_marks_present_and_absent_students(client, db_session, monkeypatch):
    instructor = _create_user(
        db_session,
        "Attendance Instructor",
        "attendance-instructor@tests.com",
        "instructor123",
        "instructor",
    )
    student_present = _create_user(
        db_session,
        "Present Student",
        "present-student@tests.com",
        "student123",
        "student",
    )
    student_absent = _create_user(
        db_session,
        "Absent Student",
        "absent-student@tests.com",
        "student123",
        "student",
    )

    course = Course(course_code="AT101", name="Attendance 101")
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)

    classroom = Classroom(
        course_id=course.id,
        batch_name="Batch-Att",
        room_name="Attendance Room",
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
            user_id=student_present.id,
            classroom_id=classroom.id,
            status="ongoing",
        )
    )
    db_session.add(
        Enrollment(
            user_id=student_absent.id,
            classroom_id=classroom.id,
            status="ongoing",
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
    monkeypatch.setattr("app.routers.sessions.ATTENDANCE_THRESHOLD_MINUTES", 0)

    async def _noop_auto_mark_attendance(participant_id: int):
        return None

    monkeypatch.setattr("app.routers.sessions.auto_mark_attendance", _noop_auto_mark_attendance)

    instructor_token = _login(client, "attendance-instructor@tests.com", "instructor123")
    student_token = _login(client, "present-student@tests.com", "student123")

    start_response = client.post(
        "/sessions/start",
        params={"classroom_id": classroom.id},
        headers={"Authorization": f"Bearer {instructor_token}"},
    )
    assert start_response.status_code == 200
    session_id = start_response.json()["session_id"]

    join_response = client.post(
        "/sessions/join",
        params={"classroom_id": classroom.id},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert join_response.status_code == 200
    assert join_response.json()["status"] == "joined"

    end_response = client.post(
        "/sessions/end",
        params={"session_id": session_id},
        headers={"Authorization": f"Bearer {instructor_token}"},
    )
    assert end_response.status_code == 200

    attendance_response = client.get(
        f"/sessions/session/{session_id}",
        headers={"Authorization": f"Bearer {instructor_token}"},
    )
    assert attendance_response.status_code == 200
    attendance_rows = attendance_response.json()
    statuses = {row["student_name"]: row["attendance_status"] for row in attendance_rows}
    assert statuses["Present Student"] == "present"
    assert statuses["Absent Student"] == "absent"

    db_session.refresh(
        db_session.query(ClassSession).filter(ClassSession.id == session_id).first()
    )
    assert db_session.query(SessionParticipant).filter(SessionParticipant.session_id == session_id).count() == 2


def test_session_join_twice_and_end_twice_are_guarded(client, db_session, monkeypatch):
    instructor = _create_user(
        db_session,
        "Session Guard Instructor",
        "session-guard-instructor@tests.com",
        "instructor123",
        "instructor",
    )
    student = _create_user(
        db_session,
        "Session Guard Student",
        "session-guard-student@tests.com",
        "student123",
        "student",
    )

    course = Course(course_code="SG101", name="Session Guard")
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)

    classroom = Classroom(
        course_id=course.id,
        batch_name="Batch-SG",
        room_name="Session Guard Room",
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

    monkeypatch.setattr(
        "app.routers.sessions.create_room",
        lambda room_name: {
            "room_id": room_name,
            "host_url": f"https://example.com/{room_name}",
            "guest_url": f"https://example.com/{room_name}",
        },
    )
    monkeypatch.setattr("app.routers.sessions.ATTENDANCE_THRESHOLD_MINUTES", 30)

    async def _noop_auto_mark_attendance(participant_id: int):
        return None

    monkeypatch.setattr("app.routers.sessions.auto_mark_attendance", _noop_auto_mark_attendance)

    instructor_token = _login(client, "session-guard-instructor@tests.com", "instructor123")
    student_token = _login(client, "session-guard-student@tests.com", "student123")

    start_response = client.post(
        "/sessions/start",
        params={"classroom_id": classroom.id},
        headers={"Authorization": f"Bearer {instructor_token}"},
    )
    assert start_response.status_code == 200
    session_id = start_response.json()["session_id"]

    first_join = client.post(
        "/sessions/join",
        params={"classroom_id": classroom.id},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert first_join.status_code == 200
    assert first_join.json()["status"] == "joined"

    second_join = client.post(
        "/sessions/join",
        params={"classroom_id": classroom.id},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert second_join.status_code == 200
    assert second_join.json()["status"] == "already_joined"

    leave_without_join = client.post(
        "/sessions/leave",
        params={"session_id": 999999},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert leave_without_join.status_code == 404

    first_end = client.post(
        "/sessions/end",
        params={"session_id": session_id},
        headers={"Authorization": f"Bearer {instructor_token}"},
    )
    assert first_end.status_code == 200

    second_end = client.post(
        "/sessions/end",
        params={"session_id": session_id},
        headers={"Authorization": f"Bearer {instructor_token}"},
    )
    assert second_end.status_code == 400


def test_student_leave_session_updates_attendance(client, db_session, monkeypatch):
    instructor = _create_user(
        db_session,
        "Leave Instructor",
        "leave-instructor@tests.com",
        "instructor123",
        "instructor",
    )
    student = _create_user(
        db_session,
        "Leave Student",
        "leave-student@tests.com",
        "student123",
        "student",
    )

    course = Course(course_code="LV101", name="Leave 101")
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)

    classroom = Classroom(
        course_id=course.id,
        batch_name="Batch-L",
        room_name="Leave Room",
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

    monkeypatch.setattr(
        "app.routers.sessions.create_room",
        lambda room_name: {
            "room_id": room_name,
            "host_url": f"https://example.com/{room_name}",
            "guest_url": f"https://example.com/{room_name}",
        },
    )
    monkeypatch.setattr("app.routers.sessions.ATTENDANCE_THRESHOLD_MINUTES", 30)

    async def _noop_auto_mark_attendance(participant_id: int):
        return None

    monkeypatch.setattr("app.routers.sessions.auto_mark_attendance", _noop_auto_mark_attendance)

    instructor_token = _login(client, "leave-instructor@tests.com", "instructor123")
    student_token = _login(client, "leave-student@tests.com", "student123")

    start_response = client.post(
        "/sessions/start",
        params={"classroom_id": classroom.id},
        headers={"Authorization": f"Bearer {instructor_token}"},
    )
    assert start_response.status_code == 200
    session_id = start_response.json()["session_id"]

    join_response = client.post(
        "/sessions/join",
        params={"classroom_id": classroom.id},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert join_response.status_code == 200

    leave_response = client.post(
        "/sessions/leave",
        params={"session_id": session_id},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert leave_response.status_code == 200
    leave_body = leave_response.json()
    assert leave_body["status"] == "left"
    assert leave_body["attendance_status"] == "absent"
    assert leave_body["duration_minutes"] >= 0


def test_student_cannot_create_or_view_quiz_details(client, db_session):
    instructor, student, course, classroom, module = _seed_learning_context(
        db_session,
        "QG101",
        "Batch-QG",
    )

    instructor_token = _login(client, "instructor-qg101@tests.com", "instructor123")
    student_token = _login(client, "student-qg101@tests.com", "student123")

    create_response = client.post(
        "/tests/",
        json={
            "title": "Quiz Guardrails",
            "description": "Role checks",
            "course_id": course.id,
            "module_id": module.id,
            "batch_name": classroom.batch_name,
            "start_time": "2026-06-07T09:00:00",
            "end_time": "2026-06-07T10:00:00",
            "questions": [
                {
                    "text": "2 + 2 equals?",
                    "question_type": "mcq",
                    "marks": 5,
                    "expected_answer": None,
                    "options": [
                        {"text": "4", "is_correct": True},
                        {"text": "5", "is_correct": False},
                    ],
                }
            ],
        },
        headers={"Authorization": f"Bearer {instructor_token}"},
    )
    assert create_response.status_code == 200

    quiz = db_session.query(QuizTest).filter(QuizTest.title == "Quiz Guardrails").first()
    assert quiz is not None

    student_create_response = client.post(
        "/tests/",
        json={
            "title": "Student Cannot Create",
            "description": "Should be blocked",
            "course_id": course.id,
            "module_id": module.id,
            "batch_name": classroom.batch_name,
            "start_time": "2026-06-07T09:00:00",
            "end_time": "2026-06-07T10:00:00",
            "questions": [],
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert student_create_response.status_code == 403

    details_response = client.get(
        f"/tests/{quiz.id}/details",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert details_response.status_code == 403


def test_student_cannot_review_or_resubmit_quiz(client, db_session):
    instructor, student, course, classroom, module = _seed_learning_context(
        db_session,
        "QN101",
        "Batch-QN",
    )

    instructor_token = _login(client, "instructor-qn101@tests.com", "instructor123")
    student_token = _login(client, "student-qn101@tests.com", "student123")

    create_response = client.post(
        "/tests/",
        json={
            "title": "Quiz Negative",
            "description": "Duplicate and review guards",
            "course_id": course.id,
            "module_id": module.id,
            "batch_name": classroom.batch_name,
            "start_time": "2026-06-07T09:00:00",
            "end_time": "2026-06-07T10:00:00",
            "questions": [
                {
                    "text": "Capital of India?",
                    "question_type": "mcq",
                    "marks": 5,
                    "expected_answer": None,
                    "options": [
                        {"text": "Delhi", "is_correct": True},
                        {"text": "Mumbai", "is_correct": False},
                    ],
                }
            ],
        },
        headers={"Authorization": f"Bearer {instructor_token}"},
    )
    assert create_response.status_code == 200

    quiz = db_session.query(QuizTest).filter(QuizTest.title == "Quiz Negative").first()
    assert quiz is not None

    start_response = client.post(
        f"/tests/{quiz.id}/start",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert start_response.status_code == 200
    submission_id = start_response.json()["submission_id"]

    submit_response = client.post(
        f"/tests/{quiz.id}/submit",
        json={
            "answers": [
                {
                    "question_id": quiz.questions[0].id,
                    "selected_option_id": quiz.questions[0].options[0].id,
                    "selected_option_ids": None,
                    "text_answer": None,
                }
            ]
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert submit_response.status_code == 200

    duplicate_submit = client.post(
        f"/tests/{quiz.id}/submit",
        json={
            "answers": [
                {
                    "question_id": quiz.questions[0].id,
                    "selected_option_id": quiz.questions[0].options[0].id,
                    "selected_option_ids": None,
                    "text_answer": None,
                }
            ]
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert duplicate_submit.status_code == 400

    review_response = client.get(
        f"/tests/{quiz.id}/submission/{submission_id}",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert review_response.status_code == 403

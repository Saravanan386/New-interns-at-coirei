from app.models.assignment import Assignment
from app.models.classroom import Classroom
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.module import Module
from app.models.notification import Notification
from app.models.test import Option, Test as QuizTest, TestSubmission as QuizSubmission
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


def _seed_batch(db_session):
    instructor = _create_user(
        db_session,
        "Instructor User",
        "instructor@assignments.com",
        "instructor123",
        "instructor",
    )
    student = _create_user(
        db_session,
        "Student User",
        "student@assignments.com",
        "student123",
        "student",
    )

    course = Course(course_code="PY201", name="Python Production")
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)

    classroom = Classroom(
        course_id=course.id,
        batch_name="Batch-Z",
        room_name="Room Z",
    )
    db_session.add(classroom)
    db_session.commit()
    db_session.refresh(classroom)

    module = Module(
        title="Deployment Module",
        order=1,
        course_id=course.id,
        batch_name="Batch-Z",
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


def test_assignment_creation_notifies_enrolled_student(client, db_session):
    instructor, student, course, classroom, module = _seed_batch(db_session)

    instructor_token = _login(client, "instructor@assignments.com", "instructor123")
    student_token = _login(client, "student@assignments.com", "student123")

    response = client.post(
        "/assignments/",
        data={
            "course_id": str(course.id),
            "batch_name": classroom.batch_name,
            "module_id": str(module.id),
            "title": "Project One",
            "description": "Build a small API",
            "expected_outcome": "Working endpoint",
            "due_date": "2026-06-15T10:00:00",
        },
        headers={"Authorization": f"Bearer {instructor_token}"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Project One"

    assignment = db_session.query(Assignment).filter(Assignment.title == "Project One").first()
    assert assignment is not None

    notification = (
        db_session.query(Notification)
        .filter(Notification.user_id == student.id)
        .first()
    )
    assert notification is not None
    assert notification.type == "assignment"
    assert notification.related_id == assignment.id

    notifications_response = client.get(
        "/notifications/",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert notifications_response.status_code == 200
    payload = notifications_response.json()
    assert payload["unread_count"] == 1
    assert payload["groups"][0]["notifications"][0]["title"] == "New Assignment"


def test_student_can_submit_assignment_and_view_submission(client, db_session):
    instructor, student, course, classroom, module = _seed_batch(db_session)

    instructor_token = _login(client, "instructor@assignments.com", "instructor123")
    student_token = _login(client, "student@assignments.com", "student123")

    create_response = client.post(
        "/assignments/",
        data={
            "course_id": str(course.id),
            "batch_name": classroom.batch_name,
            "module_id": str(module.id),
            "title": "Submission Drill",
            "description": "Submit a response",
            "expected_outcome": "A saved submission",
            "due_date": "2026-06-15T10:00:00",
        },
        headers={"Authorization": f"Bearer {instructor_token}"},
    )
    assert create_response.status_code == 201

    assignment = db_session.query(Assignment).filter(Assignment.title == "Submission Drill").first()
    assert assignment is not None

    submit_response = client.post(
        f"/assignments/{assignment.id}/submit",
        data={"submission_text": "My submission text"},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert submit_response.status_code == 200
    submission_body = submit_response.json()
    assert submission_body["status"] == "submitted"

    my_submission = client.get(
        f"/assignments/{assignment.id}/my-submission",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert my_submission.status_code == 200
    assert my_submission.json()["submission_text"] == "My submission text"

    submissions = client.get(
        f"/assignments/{assignment.id}/submissions",
        headers={"Authorization": f"Bearer {instructor_token}"},
    )
    assert submissions.status_code == 200
    payload = submissions.json()
    assert payload["total_submitted"] == 1
    assert payload["students"][0]["status"] in {"submitted", "graded"}


def test_quiz_create_start_and_submit_flow(client, db_session):
    instructor = _create_user(
        db_session,
        "Quiz Instructor",
        "quiz-instructor@tests.com",
        "instructor123",
        "instructor",
    )
    student = _create_user(
        db_session,
        "Quiz Student",
        "quiz-student@tests.com",
        "student123",
        "student",
    )

    course = Course(course_code="QZ101", name="Quiz Foundations")
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)

    classroom = Classroom(
        course_id=course.id,
        batch_name="Batch-Q",
        room_name="Quiz Room",
    )
    db_session.add(classroom)
    db_session.commit()
    db_session.refresh(classroom)

    module = Module(
        title="Quiz Module",
        order=1,
        course_id=course.id,
        batch_name="Batch-Q",
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

    instructor_token = _login(client, "quiz-instructor@tests.com", "instructor123")
    student_token = _login(client, "quiz-student@tests.com", "student123")

    create_response = client.post(
        "/tests/",
        json={
            "title": "Quiz 1",
            "description": "Core concepts",
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

    quiz = db_session.query(QuizTest).filter(QuizTest.title == "Quiz 1").first()
    assert quiz is not None

    question = quiz.questions[0]
    correct_option = next(option for option in question.options if option.is_correct)

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
                    "question_id": question.id,
                    "selected_option_id": correct_option.id,
                    "selected_option_ids": None,
                    "text_answer": None,
                }
            ],
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert submit_response.status_code == 200
    submit_body = submit_response.json()
    assert submit_body["submission_id"] == submission_id
    assert submit_body["is_passed"] is True
    assert submit_body["percentage"] == 100.0

    db_submission = db_session.query(QuizSubmission).filter(QuizSubmission.id == submission_id).first()
    assert db_submission is not None
    assert db_submission.status == "submitted"

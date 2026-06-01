import httpx

BASE_URL = "http://127.0.0.1:8000"

def login(email, password):
    response = httpx.post(
        f"{BASE_URL}/auth/login",
        params={
            "email": email,
            "password": password
        }
    )

    return response.json()["access_token"]

def test_complete_session_flow():

    instructor_token = login(
        "instructor@lms.com",
        "instructor123"
    )

    student_token = login(
        "student@lms.com",
        "student123"
    )

    # START SESSION
    start = httpx.post(
        f"{BASE_URL}/sessions/start",
        params={
            "course_id": 1,
            "batch_name": "Batch-A"
        },
        headers={
            "Authorization": f"Bearer {instructor_token}"
        }
    )

    assert start.status_code == 200

    # JOIN SESSION
    join = httpx.post(
        f"{BASE_URL}/sessions/join",
        params={
            "course_id": 1,
            "batch_name": "Batch-A"
        },
        headers={
            "Authorization": f"Bearer {student_token}"
        }
    )

    assert join.status_code == 200

    session_id = start.json()["session_id"]

    # END SESSION
    end = httpx.post(
        f"{BASE_URL}/sessions/end",
        params={
            "session_id": session_id
        },
        headers={
            "Authorization": f"Bearer {instructor_token}"
        }
    )

    assert end.status_code == 200
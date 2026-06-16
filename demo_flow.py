import argparse
import json
import sys
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "http://localhost:8001"
DEFAULT_JITSI_URL = "http://localhost:8081"


class SimpleResponse:
    def __init__(self, status_code: int, content: bytes):
        self.status_code = status_code
        self._content = content
        self.text = content.decode("utf-8", errors="replace")

    def json(self):
        return json.loads(self.text or "{}")

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(self.text or f"HTTP {self.status_code}")


class SimpleClient:
    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def request(self, method: str, url: str, *, headers=None, json_body=None, params=None):
        if params:
            query = urlencode(params, doseq=True)
            url = f"{url}{'&' if '?' in url else '?'}{query}"

        request_headers = dict(headers or {})
        data = None
        if json_body is not None:
            data = json.dumps(json_body).encode("utf-8")
            request_headers.setdefault("Content-Type", "application/json")

        request = Request(url, data=data, headers=request_headers, method=method)
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return SimpleResponse(response.status, response.read())
        except HTTPError as exc:
            return SimpleResponse(exc.code, exc.read())
        except URLError as exc:
            raise RuntimeError(f"Request to {url} failed: {exc.reason}") from exc

    def get(self, url: str, *, headers=None, params=None):
        return self.request("GET", url, headers=headers, params=params)

    def post(self, url: str, *, headers=None, json=None, params=None):
        return self.request("POST", url, headers=headers, json_body=json, params=params)


def _print(title: str, payload):
    print(f"\n=== {title} ===")
    if isinstance(payload, (dict, list)):
        print(json.dumps(payload, indent=2, default=str))
    else:
        print(payload)


def _raise_for_status(response: SimpleResponse, step: str):
    try:
        response.raise_for_status()
    except RuntimeError as exc:
        detail = response.text
        raise RuntimeError(f"{step} failed with {response.status_code}: {detail}") from exc


def _login(client: SimpleClient, base_url: str, email: str, password: str) -> str:
    response = client.post(
        f"{base_url}/auth/login",
        json={"email": email, "password": password},
    )
    _raise_for_status(response, f"Login for {email}")
    return response.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _find_course(client: SimpleClient, base_url: str, token: str, course_code: str):
    response = client.get(
        f"{base_url}/courses/",
        headers=_auth_headers(token),
    )
    _raise_for_status(response, "List courses")
    for course in response.json():
        if course.get("course_code") == course_code:
            return course
    return None


def _find_batch(client: SimpleClient, base_url: str, token: str, course_id: int, batch_name: str):
    response = client.get(
        f"{base_url}/courses/{course_id}/batches",
        headers=_auth_headers(token),
    )
    _raise_for_status(response, "List batches")
    for batch in response.json():
        if batch.get("batch_name") == batch_name:
            return batch
    return None


def _get_active_session(client: SimpleClient, base_url: str, token: str, classroom_id: int):
    response = client.get(
        f"{base_url}/sessions/active",
        headers=_auth_headers(token),
        params={"classroom_id": classroom_id},
    )
    _raise_for_status(response, "Get active session")
    return response.json()


def main():
    parser = argparse.ArgumentParser(description="End-to-end LMS + Jitsi demo flow")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Backend base URL")
    parser.add_argument("--jitsi-url", default=DEFAULT_JITSI_URL, help="Jitsi URL for display")
    parser.add_argument("--course-code", default="DEMO101")
    parser.add_argument("--course-name", default="AI / ML Frontier Demo")
    parser.add_argument("--course-description", default="Demo course for the LMS + Jitsi walkthrough")
    parser.add_argument("--duration-months", type=int, default=3)
    parser.add_argument("--total-lessons", type=int, default=24)
    parser.add_argument("--batch-name", default="Batch-Demo")
    parser.add_argument("--room-name", default="Demo_Conference_Room")
    parser.add_argument("--admin-email", default="admin@lms.com")
    parser.add_argument("--admin-password", default="admin123")
    parser.add_argument("--instructor-email", default="instructor@lms.com")
    parser.add_argument("--instructor-password", default="instructor123")
    parser.add_argument("--student-email-prefix", default="student-demo")
    parser.add_argument("--student-first-name", default="Demo")
    parser.add_argument("--student-last-name", default="Student")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    jitsi_url = args.jitsi_url.rstrip("/")
    unique_suffix = datetime.now().strftime("%Y%m%d%H%M%S")
    student_email = f"{args.student_email_prefix}-{unique_suffix}@demo.com"

    with SimpleClient(timeout=30.0) as client:
        _print("Demo target", {"backend": base_url, "jitsi": jitsi_url})

        admin_token = _login(client, base_url, args.admin_email, args.admin_password)
        instructor_token = _login(client, base_url, args.instructor_email, args.instructor_password)

        course = _find_course(client, base_url, admin_token, args.course_code)
        if course:
            _print("Using existing course", course)
        else:
            create_course_resp = client.post(
                f"{base_url}/courses/create",
                headers=_auth_headers(admin_token),
                json={
                    "course_code": args.course_code,
                    "name": args.course_name,
                    "description": args.course_description,
                    "duration_months": args.duration_months,
                    "total_lessons": args.total_lessons,
                },
            )
            _raise_for_status(create_course_resp, "Create course")
            course = create_course_resp.json()
            _print("Created course", course)

        course_id = course["id"]

        batch = _find_batch(client, base_url, admin_token, course_id, args.batch_name)
        if batch:
            _print("Using existing batch", batch)
        else:
            create_batch_resp = client.post(
                f"{base_url}/classrooms/",
                headers=_auth_headers(admin_token),
                json={
                    "course_id": course_id,
                    "batch_name": args.batch_name,
                    "room_name": args.room_name,
                    "schedule_type": "weekday",
                    "start_month": "2026-06",
                    "class_days": "Mon,Wed,Fri",
                    "start_time": "10:00",
                    "end_time": "11:30",
                },
            )
            _raise_for_status(create_batch_resp, "Create batch")
            batch = create_batch_resp.json()
            _print("Created batch", batch)

        classroom_id = batch["id"]

        enroll_teacher_resp = client.post(
            f"{base_url}/instructor-enroll/instructor",
            headers=_auth_headers(admin_token),
            json={
                "first_name": "Teacher",
                "last_name": "Demo",
                "email": args.instructor_email,
                "course_batches": [
                    {"course_id": course_id, "batch_name": args.batch_name}
                ],
            },
        )
        _raise_for_status(enroll_teacher_resp, "Enroll instructor")
        _print("Instructor enrollment", enroll_teacher_resp.json())

        enroll_student_resp = client.post(
            f"{base_url}/enroll/student",
            headers=_auth_headers(admin_token),
            params={
                "course_id": course_id,
                "batch_name": args.batch_name,
                "first_name": args.student_first_name,
                "last_name": args.student_last_name,
                "email": student_email,
            },
        )
        _raise_for_status(enroll_student_resp, "Enroll student")
        enroll_student_body = enroll_student_resp.json()
        _print("Student enrollment", enroll_student_body)

        student_password = enroll_student_body.get("auto_generated_password")
        if not student_password:
            raise RuntimeError(
                "Student enrollment did not return an auto-generated password. "
                "This usually means the student email already exists."
            )

        student_token = _login(client, base_url, student_email, student_password)

        active_before_start = _get_active_session(client, base_url, instructor_token, classroom_id)
        if active_before_start.get("live"):
            old_session_id = active_before_start.get("session_id")
            if old_session_id:
                end_resp = client.post(
                    f"{base_url}/sessions/end",
                    headers=_auth_headers(instructor_token),
                    params={"session_id": old_session_id},
                )
                _raise_for_status(end_resp, "End existing session")
                _print("Closed previous live session", end_resp.json())

        start_resp = client.post(
            f"{base_url}/sessions/start",
            headers=_auth_headers(instructor_token),
            params={"classroom_id": classroom_id},
        )
        _raise_for_status(start_resp, "Start session")
        start_body = start_resp.json()
        _print("Session started", start_body)

        session_id = start_body["session_id"]

        active_body = _get_active_session(client, base_url, student_token, classroom_id)
        _print("Active session for student", active_body)

        join_resp = client.post(
            f"{base_url}/sessions/join",
            headers=_auth_headers(student_token),
            params={"classroom_id": classroom_id},
        )
        _raise_for_status(join_resp, "Join session")
        _print("Join response", join_resp.json())

        access_resp = client.post(
            f"{base_url}/sessions/{session_id}/access",
            headers=_auth_headers(instructor_token),
        )
        _raise_for_status(access_resp, "Instructor access")
        _print("Instructor access payload", access_resp.json())

        print("\n=== Demo login summary ===")
        print(f"Admin:       {args.admin_email} / {args.admin_password}")
        print(f"Instructor:   {args.instructor_email} / {args.instructor_password}")
        print(f"Student:      {student_email} / {student_password}")
        print(f"Backend docs: {base_url}/docs")
        print(f"Jitsi URL:    {jitsi_url}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        sys.exit(1)

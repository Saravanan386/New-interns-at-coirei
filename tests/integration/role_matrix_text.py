# # lms_api_tests.py
# import os
# import time
# import uuid
# import random
# from datetime import datetime, timedelta

# import requests

# BASE_URL = os.getenv("BASE_URL", "https://lms-backend-5r6q.onrender.com")
# TIMEOUT = 30

# session = requests.Session()

# state = {
#     "admin_token": None,
#     "instructor_token": None,
#     "student_token": None,
#     "course_id": None,
#     "classroom_id": None,
#     "session_id": None,
#     "module_id": None,
#     "chapter_id": None,
#     "assignment_id": None,
#     "assignment_submission_id": None,
#     "test_id": None,
#     "test_submission_id": None,
#     "course_member_user_id": None,
#     "instructor_user_id": None,
#     "student_user_id": None,
#     "dm_conversation_id": None,
#     "group_id": None,
#     "chat_post_id": None,
#     "qa_post_id": None,
#     "notification_id": None,
#     "test_questions": [],
# }

# def uniq(s):
#     return f"{s}-{int(time.time())}-{uuid.uuid4().hex[:6]}"

# def unique_email(prefix):
#     return f"{prefix}.{int(time.time())}.{uuid.uuid4().hex[:6]}@lmstest.com"

# def unique_phone():
#     return "9" + "".join(str(random.randint(0, 9)) for _ in range(9))

# ADMIN = {
#     "name": "Admin User",
#     "email": unique_email("admin"),
#     "password": "Admin@1234",
#     "role": "admin",
# }

# INSTRUCTOR = {
#     "full_name": "Test Instructor",
#     "email": unique_email("instructor"),
#     "phone_number": unique_phone(),
#     "password": "Instructor@1234",
#     "specialization": "Python & ML",
#     "experience_years": 3,
#     "skills": ["Python", "Machine Learning", "SQL"],
# }

# STUDENT = {
#     "full_name": "Test Student",
#     "email": unique_email("student"),
#     "phone_number": unique_phone(),
#     "password": "Student@1234",
#     "gender": "Male",
#     "date_of_birth": "2003-01-15",
#     "interests": ["AI", "Python"],
# }

# def auth_header(role):
#     token = state.get(f"{role}_token")
#     return {"Authorization": f"Bearer {token}"} if token else {}

# def req(method, path, *, params=None, json=None, data=None, files=None, headers=None):
#     url = f"{BASE_URL}{path}"
#     h = headers or {}
#     return session.request(method, url, params=params, json=json, data=data, files=files, headers=h, timeout=TIMEOUT)

# def ok(r, label, accept=(200, 201)):
#     passed = r.status_code in accept
#     status = "✅ PASS" if passed else f"❌ FAIL [{r.status_code}]"
#     print(f"  {status} {label}")
#     if not passed:
#         try:
#             print("     ", r.json())
#         except Exception:
#             print("     ", r.text[:300])
#     return passed

# def pick_id(body, *keys):
#     if isinstance(body, dict):
#         for k in keys:
#             if body.get(k) is not None:
#                 return body.get(k)
#     return None

# def ensure_token(role):
#     token = state.get(f"{role}_token")
#     if not token:
#         raise RuntimeError(f"Missing {role} token")
#     return token

# def test_auth():
#     print("\n── AUTH ──────────────────────────────────────────────")
#     r = req("POST", "/auth/register", json={
#         "name": ADMIN["name"],
#         "email": ADMIN["email"],
#         "password": ADMIN["password"],
#         "role": ADMIN["role"],
#     })
#     ok(r, "POST /auth/register")

#     r = req("POST", "/auth/register/instructor", json={
#         "full_name": INSTRUCTOR["full_name"],
#         "email": INSTRUCTOR["email"],
#         "phone_number": INSTRUCTOR["phone_number"],
#         "password": INSTRUCTOR["password"],
#         "specialization": INSTRUCTOR["specialization"],
#         "experience_years": INSTRUCTOR["experience_years"],
#         "skills": INSTRUCTOR["skills"],
#     })
#     ok(r, "POST /auth/register/instructor", accept=(200, 201))

#     r = req("POST", "/auth/register/student", json={
#         "full_name": STUDENT["full_name"],
#         "email": STUDENT["email"],
#         "phone_number": STUDENT["phone_number"],
#         "password": STUDENT["password"],
#         "gender": STUDENT["gender"],
#         "date_of_birth": STUDENT["date_of_birth"],
#         "interests": STUDENT["interests"],
#     })
#     ok(r, "POST /auth/register/student", accept=(200, 201))

    
#     r = req("POST", "/auth/login", json={"email": INSTRUCTOR["email"], "password": INSTRUCTOR["password"]})
#     if ok(r, "POST /auth/login (instructor)"):
#         b = r.json()
#         state["instructor_token"] = b.get("access_token") or b.get("token")
#         state["instructor_user_id"] = b.get("user_id") or b.get("id")

#     r = req("POST", "/auth/login", json={"email": STUDENT["email"], "password": STUDENT["password"]})
#     if ok(r, "POST /auth/login (student)"):
#         b = r.json()
#         state["student_token"] = b.get("access_token") or b.get("token")
#         state["student_user_id"] = b.get("user_id") or b.get("id")
#     r = req("POST", "/auth/login", json={"email": ADMIN["email"], "password": ADMIN["password"]})
#     if ok(r, "POST /auth/login (admin)"):
#         b = r.json()
#         state["admin_token"] = b.get("access_token") or b.get("token")

# def test_courses():
#     print("\n── COURSES ───────────────────────────────────────────")
#     h = auth_header("instructor")
#     r = req("POST", "/courses/create", json={
#         "course_code": uniq("PY101"),
#         "name": "Python Fundamentals",
#         "description": "Beginner Python course",
#         "duration_months": 3,
#         "total_lessons": 30,
#     }, headers=h)
#     if ok(r, "POST /courses/create", accept=(200, 201)):
#         state["course_id"] = pick_id(r.json(), "id", "course_id")

#     r = req("GET", "/courses/", headers=h)
#     ok(r, "GET /courses/")

#     r = req("GET", "/courses/my", headers=h)
#     ok(r, "GET /courses/my")

#     if state["course_id"]:
#         cid = state["course_id"]
#         r = req("GET", f"/courses/{cid}/batches")
#         ok(r, f"GET /courses/{cid}/batches")

#         r = req("PUT", f"/courses/update/{cid}", json={"description": "Updated description"}, headers=h)
#         ok(r, f"PUT /courses/update/{cid}")

#         r = req("GET", f"/courses/{cid}/full-overview", headers=h)
#         ok(r, f"GET /courses/{cid}/full-overview")

# def test_classrooms():
#     print("\n── CLASSROOMS ────────────────────────────────────────")
#     h = auth_header("instructor")
#     cid = state["course_id"]
#     if not cid:
#         print("  ⚠️ Skipped — no course_id")
#         return

#     r = req("POST", "/classrooms/", json={
#         "course_id": cid,
#         "batch_name": "Batch-A",
#         "room_name": "Room 101",
#         "schedule_type": "weekday",
#         "start_month": "2026-07",
#         "class_days": "Mon,Wed,Fri",
#         "start_time": "10:00",
#         "end_time": "12:00",
#     }, headers=h)
#     if ok(r, "POST /classrooms/", accept=(200, 201)):
#         state["classroom_id"] = pick_id(r.json(), "id", "classroom_id")

#     r = req("GET", "/classrooms/", headers=h)
#     ok(r, "GET /classrooms/")

#     if state["classroom_id"]:
#         rid = state["classroom_id"]
#         r = req("GET", f"/classrooms/{rid}", headers=h)
#         ok(r, f"GET /classrooms/{rid}")

#         r = req("GET", f"/classrooms/{rid}/schedule", headers=h)
#         ok(r, f"GET /classrooms/{rid}/schedule")

#         r = req("GET", f"/classrooms/course/{cid}", headers=h)
#         ok(r, f"GET /classrooms/course/{cid}")

#         r = req("GET", f"/classrooms/course/{cid}/full", headers=h)
#         ok(r, f"GET /classrooms/course/{cid}/full")

#         r = req("PUT", f"/classrooms/{rid}", json={"room_name": "Room 202"}, headers=h)
#         ok(r, f"PUT /classrooms/{rid}")

#         r = req("GET", f"/courses/{cid}/classrooms", headers=h)
#         ok(r, f"GET /courses/{cid}/classrooms")

# def test_enrollment():
#     print("\n── ENROLLMENT ────────────────────────────────────────")
#     h = auth_header("instructor")
#     cid = state["course_id"]
#     if not cid:
#         print("  ⚠️ Skipped — no course_id")
#         return

#     r = req("GET", "/enroll/courses", headers=h)
#     ok(r, "GET /enroll/courses")

#     r = req("GET", "/enroll/batches", params={"course_id": cid}, headers=h)
#     ok(r, "GET /enroll/batches")

#     r = req("GET", "/enroll/generate-id", params={"course_id": cid}, headers=h)
#     ok(r, "GET /enroll/generate-id")

#     enroll_email = unique_email("enrolled")
#     r = req("POST", "/enroll/student", params={
#         "course_id": cid,
#         "batch_name": "Batch-A",
#         "first_name": "Auto",
#         "last_name": "Student",
#         "email": enroll_email,
#     }, headers=h)
#     ok(r, "POST /enroll/student")

#     r = req("GET", "/instructor-enroll/courses", headers=h)
#     ok(r, "GET /instructor-enroll/courses")

#     r = req("GET", "/instructor-enroll/generate-id", headers=h)
#     ok(r, "GET /instructor-enroll/generate-id")

#     r = req("GET", "/instructor-enroll/list", headers=h)
#     ok(r, "GET /instructor-enroll/list")

# def test_sessions():
#     print("\n── SESSIONS ──────────────────────────────────────────")
#     ih = auth_header("instructor")
#     sh = auth_header("student")
#     rid = state["classroom_id"]
#     if not rid:
#         print("  ⚠️ Skipped — no classroom_id")
#         return

#     r = req("POST", "/sessions/start", params={"classroom_id": rid}, headers=ih)
#     if ok(r, "POST /sessions/start"):
#         state["session_id"] = pick_id(r.json(), "session_id", "id")

#     r = req("GET", "/sessions/active", params={"classroom_id": rid}, headers=ih)
#     ok(r, "GET /sessions/active")

#     r = req("POST", "/sessions/join", params={"classroom_id": rid}, headers=sh)
#     ok(r, "POST /sessions/join (student)")

#     r = req("GET", "/sessions/history", headers=ih)
#     ok(r, "GET /sessions/history")

#     if state["session_id"]:
#         sid = state["session_id"]
#         r = req("GET", f"/sessions/session/{sid}")
#         ok(r, f"GET /sessions/session/{sid}")

#         r = req("POST", f"/sessions/{sid}/access", headers=sh)
#         ok(r, f"POST /sessions/{sid}/access")

#         r = req("POST", "/sessions/leave", params={"session_id": sid}, headers=sh)
#         ok(r, "POST /sessions/leave")

#         r = req("POST", "/sessions/end", params={"session_id": sid}, headers=ih)
#         ok(r, "POST /sessions/end")

# def test_attendance():
#     print("\n── ATTENDANCE ────────────────────────────────────────")
#     sh = auth_header("student")
#     sid = state["session_id"]
#     if not sid:
#         print("  ⚠️ Skipped — no session_id")
#         return

#     r = req("POST", "/attendance/join", params={"session_id": sid}, headers=sh)
#     ok(r, "POST /attendance/join")

#     r = req("GET", f"/attendance/session/{sid}", headers=sh)
#     ok(r, f"GET /attendance/session/{sid}")

#     r = req("POST", "/attendance/leave", params={"session_id": sid}, headers=sh)
#     ok(r, "POST /attendance/leave")

#     r = req("GET", "/students/me/attendance/summary", headers=sh)
#     ok(r, "GET /students/me/attendance/summary")

#     r = req("GET", "/students/me/attendance/history", headers=sh)
#     ok(r, "GET /students/me/attendance/history")

#     r = req("GET", "/students/me/attendance/details", headers=sh)
#     ok(r, "GET /students/me/attendance/details")

# def test_modules():
#     print("\n── MODULES & CHAPTERS ────────────────────────────────")
#     h = auth_header("instructor")
#     cid = state["course_id"]
#     if not cid:
#         print("  ⚠️ Skipped — no course_id")
#         return

#     r = req("POST", "/modules/", json={
#         "title": "Module 1: Python Basics",
#         "order": 1,
#         "course_id": cid,
#         "batch_name": "Batch-A",
#     }, headers=h)
#     if ok(r, "POST /modules/", accept=(200, 201)):
#         state["module_id"] = pick_id(r.json(), "id", "module_id")

#     r = req("GET", "/modules/", params={"course_id": cid, "batch_name": "Batch-A"}, headers=h)
#     ok(r, "GET /modules/")

#     if state["module_id"]:
#         mid = state["module_id"]
#         r = req("POST", f"/modules/{mid}/chapters", json={"title": "Chapter 1: Variables", "order": 1}, headers=h)
#         if ok(r, f"POST /modules/{mid}/chapters", accept=(200, 201)):
#             state["chapter_id"] = pick_id(r.json(), "id", "chapter_id")

# def test_assignments():
#     print("\n── ASSIGNMENTS ───────────────────────────────────────")
#     ih = auth_header("instructor")
#     sh = auth_header("student")
#     cid = state["course_id"]
#     mid = state["module_id"]
#     if not cid or not mid:
#         print("  ⚠️ Skipped — no course_id or module_id")
#         return

#     r = req("GET", "/assignments/courses", headers=ih)
#     ok(r, "GET /assignments/courses")

#     r = req("GET", "/assignments/batches", params={"course_id": cid}, headers=ih)
#     ok(r, "GET /assignments/batches")

#     r = req("GET", "/assignments/modules", params={"course_id": cid, "batch_name": "Batch-A"}, headers=ih)
#     ok(r, "GET /assignments/modules")

#     form = {
#         "course_id": (None, str(cid)),
#         "batch_name": (None, "Batch-A"),
#         "module_id": (None, str(mid)),
#         "title": (None, "Assignment 1: Hello World"),
#         "description": (None, "Write a Hello World program"),
#         "expected_outcome": (None, "print('Hello World')"),
#         "due_date": (None, (datetime.utcnow() + timedelta(days=7)).isoformat()),
#     }
#     r = req("POST", "/assignments/", files=form, headers=ih)
#     if ok(r, "POST /assignments/", accept=(200, 201)):
#         state["assignment_id"] = pick_id(r.json(), "id", "assignment_id")

#     r = req("GET", "/assignments/", params={"course_id": cid, "batch_name": "Batch-A"}, headers=ih)
#     ok(r, "GET /assignments/")

#     if state["assignment_id"]:
#         aid = state["assignment_id"]

#         r = req("GET", f"/assignments/{aid}", headers=ih)
#         ok(r, f"GET /assignments/{aid}")

#         r = req("GET", f"/assignments/{aid}/submissions", headers=ih)
#         ok(r, f"GET /assignments/{aid}/submissions")

#         r = req("GET", "/assignments/my/list", headers=sh)
#         ok(r, "GET /assignments/my/list")

#         r = req("GET", "/assignments/dashboard", headers=sh)
#         ok(r, "GET /assignments/dashboard")

#         sub_form = {
#             "submission_text": (None, "print('Hello World')"),
#         }
#         r = req("POST", f"/assignments/{aid}/submit", files=sub_form, headers=sh)
#         if ok(r, f"POST /assignments/{aid}/submit", accept=(200, 201)):
#             state["assignment_submission_id"] = pick_id(r.json(), "id", "submission_id")

#         r = req("GET", f"/assignments/{aid}/my-submission", headers=sh)
#         ok(r, f"GET /assignments/{aid}/my-submission")

#         if state["assignment_submission_id"]:
#             subid = state["assignment_submission_id"]
#             r = req("PUT", f"/assignments/{aid}/submissions/{subid}/grade",
#                     data={"grade": "A", "feedback": "Great work!"}, headers=ih)
#             ok(r, f"PUT /assignments/{aid}/submissions/{subid}/grade")

#         r = req("PUT", f"/assignments/{aid}", json={"description": "Updated description"}, headers=ih)
#         ok(r, f"PUT /assignments/{aid}")

# def test_quiz():
#     print("\n── TESTS (QUIZZES) ───────────────────────────────────")
#     ih = auth_header("instructor")
#     sh = auth_header("student")
#     cid = state["course_id"]
#     mid = state["module_id"]
#     if not cid or not mid:
#         print("  ⚠️ Skipped — no course_id or module_id")
#         return

#     payload = {
#         "title": "Quiz 1: Python Basics",
#         "course_id": cid,
#         "batch_name": "Batch-A",
#         "module_id": mid,
#         "description": "Basic Python quiz",
#         "start_time": "2026-06-01T09:00:00",
#         "end_time": "2026-12-31T23:59:00",
#         "questions": [
#             {
#                 "text": "What is the output of print(2+2)?",
#                 "options": [
#                     {"text": "4", "is_correct": True},
#                     {"text": "22", "is_correct": False},
#                     {"text": "Error", "is_correct": False},
#                     {"text": "None", "is_correct": False},
#                 ],
#             },
#             {
#                 "text": "Which keyword defines a function in Python?",
#                 "options": [
#                     {"text": "def", "is_correct": True},
#                     {"text": "func", "is_correct": False},
#                     {"text": "fun", "is_correct": False},
#                     {"text": "function", "is_correct": False},
#                 ],
#             },
#         ],
#     }
#     r = req("POST", "/tests/", json=payload, headers=ih)
#     if ok(r, "POST /tests/", accept=(200, 201)):
#         body = r.json()
#         state["test_id"] = pick_id(body, "id", "test_id")
#         state["test_questions"] = body.get("questions", [])

#     if not state["test_id"]:
#         return

#     tid = state["test_id"]
#     r = req("PUT", f"/tests/{tid}", json={"description": "Updated quiz description"}, headers=ih)
#     ok(r, f"PUT /tests/{tid}")

#     r = req("GET", f"/tests/{tid}/details", headers=ih)
#     ok(r, f"GET /tests/{tid}/details")

#     r = req("POST", f"/tests/{tid}/start", headers=sh)
#     if ok(r, f"POST /tests/{tid}/start"):
#         state["test_submission_id"] = pick_id(r.json(), "submission_id", "id")

#     answers = []
#     for q in state.get("test_questions", []):
#         qid = q.get("id")
#         opts = q.get("options") or []
#         if qid and opts:
#             correct = next((o for o in opts if o.get("is_correct")), opts[0])
#             answers.append({"question_id": qid, "selected_option_id": correct.get("id")})

#     if answers:
#         r = req("POST", f"/tests/{tid}/submit", json={"answers": answers}, headers=sh)
#         ok(r, f"POST /tests/{tid}/submit")

#     if state["test_submission_id"]:
#         subid = state["test_submission_id"]
#         r = req("GET", f"/tests/{tid}/submission/{subid}", headers=ih)
#         ok(r, f"GET /tests/{tid}/submission/{subid}")

# def test_dashboards():
#     print("\n── DASHBOARD ─────────────────────────────────────────")
#     ih = auth_header("instructor")
#     sh = auth_header("student")
#     ah = auth_header("admin")

#     for path, h, label in [
#         ("/dashboard/courses", ih, "GET /dashboard/courses"),
#         ("/dashboard/classes-summary", ih, "GET /dashboard/classes-summary"),
#         ("/dashboard/admin/overview", ah, "GET /dashboard/admin/overview"),
#         ("/dashboard/admin/students", ah, "GET /dashboard/admin/students"),
#         ("/dashboard/admin/instructors", ah, "GET /dashboard/admin/instructors"),
#         ("/dashboard/admin/courses", ah, "GET /dashboard/admin/courses"),
#         ("/dashboard/admin/live-sessions", ah, "GET /dashboard/admin/live-sessions"),
#         ("/dashboard/admin/", ih, "GET /dashboard/admin/ (instructor)"),
#         ("/dashboard/student/overview", sh, "GET /dashboard/student/overview"),
#         ("/dashboard/student/courses", sh, "GET /dashboard/student/courses"),
#         ("/dashboard/student/live-classes", sh, "GET /dashboard/student/live-classes"),
#         ("/dashboard/student/attendance", sh, "GET /dashboard/student/attendance"),
#         ("/student/dashboard", sh, "GET /student/dashboard"),
#         ("/student/materials", sh, "GET /student/materials"),
#         ("/student/assignments", sh, "GET /student/assignments"),
#         ("/student/tests", sh, "GET /student/tests"),
#         ("/student/certificates", sh, "GET /student/certificates"),
#         ("/instructor/dashboard", ih, "GET /instructor/dashboard"),
#     ]:
#         r = req("GET", path, headers=h)
#         ok(r, label)

# def test_schedule():
#     print("\n── SCHEDULE ──────────────────────────────────────────")
#     h = auth_header("instructor")
#     cid = state["course_id"]
#     if not cid:
#         print("  ⚠️ Skipped — no course_id")
#         return

#     params = {"course_id": cid, "batch_name": "Batch-A"}
#     r = req("GET", "/schedule/", params=params, headers=h)
#     ok(r, "GET /schedule/")

#     r = req("GET", "/schedule/upcoming", params=params, headers=h)
#     ok(r, "GET /schedule/upcoming")

# def test_batch_analytics():
#     print("\n── BATCH ANALYTICS ───────────────────────────────────")
#     h = auth_header("instructor")
#     cid = state["course_id"]
#     if not cid:
#         print("  ⚠️ Skipped — no course_id")
#         return

#     r = req("GET", f"/batches/{cid}/list", headers=h)
#     ok(r, f"GET /batches/{cid}/list")

#     r = req("GET", f"/batches/{cid}/Batch-A/overview", headers=h)
#     ok(r, f"GET /batches/{cid}/Batch-A/overview")

# def test_batch_chat():
#     print("\n── BATCH CHAT ────────────────────────────────────────")
#     h = auth_header("instructor")
#     sh = auth_header("student")
#     cid = state["course_id"]
#     if not cid:
#         print("  ⚠️ Skipped — no course_id")
#         return

#     r = req("GET", f"/chat/{cid}/Batch-A", headers=h)
#     ok(r, f"GET /chat/{cid}/Batch-A")

#     r = req("POST", f"/chat/{cid}/Batch-A", json={
#         "course_id": cid,
#         "batch_name": "Batch-A",
#         "content": "Welcome to the batch! Ask your doubts here.",
#     }, headers=h)
#     if ok(r, f"POST /chat/{cid}/Batch-A", accept=(200, 201)):
#         state["chat_post_id"] = pick_id(r.json(), "id", "post_id")

#     if state["chat_post_id"]:
#         pid = state["chat_post_id"]
#         r = req("GET", f"/chat/{cid}/Batch-A/{pid}", headers=h)
#         ok(r, f"GET /chat/{cid}/Batch-A/{pid}")

#         r = req("POST", f"/chat/{cid}/Batch-A/{pid}/replies", json={"content": "Thank you sir!"}, headers=sh)
#         ok(r, f"POST /chat/{cid}/Batch-A/{pid}/replies", accept=(200, 201))

#         r = req("POST", f"/chat/{cid}/Batch-A/{pid}/like", headers=sh)
#         ok(r, f"POST /chat/{cid}/Batch-A/{pid}/like")

#         r = req("POST", f"/chat/{cid}/Batch-A/{pid}/bookmark", headers=sh)
#         ok(r, f"POST /chat/{cid}/Batch-A/{pid}/bookmark")

#         r = req("GET", f"/chat/{cid}/Batch-A/bookmarks/my", headers=sh)
#         ok(r, f"GET /chat/{cid}/Batch-A/bookmarks/my")

#         r = req("POST", f"/chat/{cid}/Batch-A/{pid}/pin", headers=h)
#         ok(r, f"POST /chat/{cid}/Batch-A/{pid}/pin")

# def test_course_qa():
#     print("\n── COURSE Q&A ────────────────────────────────────────")
#     sh = auth_header("student")
#     ih = auth_header("instructor")
#     cid = state["course_id"]
#     if not cid:
#         print("  ⚠️ Skipped — no course_id")
#         return

#     r = req("GET", f"/api/courses/{cid}/qa", params={"batch_name": "Batch-A"}, headers=sh)
#     ok(r, f"GET /api/courses/{cid}/qa")

#     r = req("POST", f"/api/courses/{cid}/qa", params={"batch_name": "Batch-A"}, json={
#         "title": "How do I run Python?",
#         "description": "I installed Python but don't know how to run it.",
#         "visibility": "public",
#     }, headers=sh)
#     if ok(r, f"POST /api/courses/{cid}/qa", accept=(200, 201)):
#         state["qa_post_id"] = pick_id(r.json(), "id", "question_id")

#     if state["qa_post_id"]:
#         qid = state["qa_post_id"]

#         r = req("POST", f"/api/courses/{cid}/qa/{qid}/like", headers=sh)
#         ok(r, f"POST /api/courses/{cid}/qa/{qid}/like")

#         r = req("PATCH", f"/api/courses/{cid}/qa/{qid}/bookmark", headers=sh)
#         ok(r, f"PATCH /api/courses/{cid}/qa/{qid}/bookmark")

#         r = req("POST", f"/api/courses/{cid}/qa/{qid}/replies", json={"content": "Open terminal and type python filename.py"}, headers=ih)
#         ok(r, f"POST /api/courses/{cid}/qa/{qid}/replies", accept=(200, 201))

#         r = req("GET", f"/api/courses/{cid}/qa/{qid}/replies", headers=sh)
#         ok(r, f"GET /api/courses/{cid}/qa/{qid}/replies")

#         r = req("PATCH", f"/api/courses/{cid}/qa/{qid}/pin", headers=ih)
#         ok(r, f"PATCH /api/courses/{cid}/qa/{qid}/pin")

#         r = req("PATCH", f"/api/courses/{cid}/qa/{qid}/visibility", json={"visibility": "public"}, headers=ih)
#         ok(r, f"PATCH /api/courses/{cid}/qa/{qid}/visibility")

# def test_dm_chat():
#     print("\n── DM CHAT ───────────────────────────────────────────")
#     sh = auth_header("student")
#     uid = state.get("instructor_user_id")
#     if not uid:
#         print("  ⚠️ Skipped — no instructor_user_id")
#         return

#     r = req("POST", "/api/chats/conversations", json={"user_id": uid}, headers=sh)
#     if ok(r, "POST /api/chats/conversations", accept=(200, 201)):
#         state["dm_conversation_id"] = pick_id(r.json(), "id", "conversation_id")

#     r = req("GET", "/api/chats/conversations", headers=sh)
#     ok(r, "GET /api/chats/conversations")

#     if state["dm_conversation_id"]:
#         cid = state["dm_conversation_id"]
#         r = req("POST", f"/api/chats/conversations/{cid}/messages", json={"text": "Hello sir, I have a question about the assignment."}, headers=sh)
#         msg_id = None
#         if ok(r, f"POST /api/chats/conversations/{cid}/messages", accept=(200, 201)):
#             msg_id = pick_id(r.json(), "id", "message_id")

#         r = req("GET", f"/api/chats/conversations/{cid}/messages", headers=sh)
#         ok(r, f"GET /api/chats/conversations/{cid}/messages")

#         r = req("PATCH", f"/api/chats/conversations/{cid}/read", headers=sh)
#         ok(r, f"PATCH /api/chats/conversations/{cid}/read")

#         if msg_id:
#             r = req("POST", f"/api/chats/messages/{msg_id}/like", headers=auth_header("instructor"))
#             ok(r, f"POST /api/chats/messages/{msg_id}/like")

#             r = req("PATCH", f"/api/chats/messages/{msg_id}/bookmark", headers=sh)
#             ok(r, f"PATCH /api/chats/messages/{msg_id}/bookmark")

# def test_group_chat():
#     print("\n── GROUP CHAT ────────────────────────────────────────")
#     ih = auth_header("instructor")
#     sh = auth_header("student")
#     cid = state["course_id"]
#     if not cid:
#         print("  ⚠️ Skipped — no course_id")
#         return

#     r = req("GET", "/api/chats/groups/by-batch", params={"course_id": cid, "batch_name": "Batch-A"}, headers=ih)
#     if ok(r, "GET /api/chats/groups/by-batch"):
#         body = r.json()
#         state["group_id"] = pick_id(body, "group_id", "id")

#     if state["group_id"]:
#         gid = state["group_id"]
#         r = req("POST", f"/api/chats/groups/{gid}/messages", json={"text": "Good morning batch! Today we cover loops."}, headers=ih)
#         gmsg_id = None
#         if ok(r, f"POST /api/chats/groups/{gid}/messages", accept=(200, 201)):
#             gmsg_id = pick_id(r.json(), "id", "message_id")

#         r = req("GET", f"/api/chats/groups/{gid}/messages", headers=ih)
#         ok(r, f"GET /api/chats/groups/{gid}/messages")

#         r = req("PATCH", f"/api/chats/groups/{gid}/read", headers=sh)
#         ok(r, f"PATCH /api/chats/groups/{gid}/read")

#         if gmsg_id:
#             r = req("POST", f"/api/chats/groups/messages/{gmsg_id}/like", headers=sh)
#             ok(r, f"POST /api/chats/groups/messages/{gmsg_id}/like")

#             r = req("PATCH", f"/api/chats/groups/messages/{gmsg_id}/bookmark", headers=sh)
#             ok(r, f"PATCH /api/chats/groups/messages/{gmsg_id}/bookmark")

#             r = req("PATCH", f"/api/chats/groups/{gid}/messages/{gmsg_id}/pin", headers=ih)
#             ok(r, f"PATCH /api/chats/groups/{gid}/messages/{gmsg_id}/pin")

# def test_notifications():
#     print("\n── NOTIFICATIONS ─────────────────────────────────────")
#     h = auth_header("instructor")
#     r = req("GET", "/notifications/", headers=h)
#     if ok(r, "GET /notifications/"):
#         data = r.json()
#         items = []
#         if isinstance(data, list):
#             items = data
#         elif isinstance(data, dict):
#             items = data.get("today", []) or data.get("notifications", [])
#         if items:
#             state["notification_id"] = items[0].get("id")

#     r = req("PATCH", "/notifications/read-all", headers=h)
#     ok(r, "PATCH /notifications/read-all")

#     if state["notification_id"]:
#         nid = state["notification_id"]
#         r = req("PATCH", f"/notifications/{nid}/read", headers=h)
#         ok(r, f"PATCH /notifications/{nid}/read")

#         r = req("DELETE", f"/notifications/{nid}", headers=h)
#         ok(r, f"DELETE /notifications/{nid}")

# def test_instructor_apis():
#     print("\n── INSTRUCTOR APIs ───────────────────────────────────")
#     h = auth_header("instructor")
#     cid = state["course_id"]
#     params_course = {"course_id": cid, "batch_name": "Batch-A"} if cid else {}

#     r = req("GET", "/instructor/sessions", params=params_course, headers=h)
#     ok(r, "GET /instructor/sessions")

#     r = req("GET", "/instructor/assignment-submissions", params={"course_id": cid} if cid else {}, headers=h)
#     ok(r, "GET /instructor/assignment-submissions")

#     r = req("GET", "/instructor/test-results", params={"course_id": cid} if cid else {}, headers=h)
#     ok(r, "GET /instructor/test-results")

# def test_resources_and_profile():
#     print("\n── RESOURCES & PROFILE ───────────────────────────────")
#     ih = auth_header("instructor")
#     sh = auth_header("student")

#     r = req("GET", "/resources", headers=ih)
#     ok(r, "GET /resources")

#     if state.get("chapter_id"):
#         chapter_file = {"files": ("chapter.txt", b"Chapter resource content", "text/plain")}
#         r = req("POST", f"/chapter-resources/{state['chapter_id']}", files={"files": [chapter_file]}, headers=ih)
#         ok(r, f"POST /chapter-resources/{state['chapter_id']}")

#     uid = state.get("student_user_id")
#     if uid:
#         r = req("GET", f"/api/users/{uid}/profile", headers=ih)
#         ok(r, f"GET /api/users/{uid}/profile")

#         r = req("GET", f"/api/users/{uid}/avatar")
#         ok(r, f"GET /api/users/{uid}/avatar")

#     cid = state.get("course_id")
#     if cid:
#         r = req("GET", f"/api/courses/{cid}/members", params={"batch_name": "Batch-A"}, headers=ih)
#         ok(r, f"GET /api/courses/{cid}/members")

# def test_cleanup():
#     print("\n── CLEANUP ───────────────────────────────────────────")
#     h = auth_header("instructor")

#     if state.get("assignment_id"):
#         r = req("DELETE", f"/assignments/{state['assignment_id']}", headers=h)
#         ok(r, f"DELETE /assignments/{state['assignment_id']}")

#     if state.get("classroom_id"):
#         r = req("DELETE", f"/classrooms/{state['classroom_id']}", headers=h)
#         ok(r, f"DELETE /classrooms/{state['classroom_id']}")

#     if state.get("course_id"):
#         r = req("DELETE", f"/courses/{state['course_id']}", headers=h)
#         ok(r, f"DELETE /courses/{state['course_id']}")

# def main():
#     print("=" * 60)
#     print("  LMS Backend Automated Test Suite")
#     print(f"  Target: {BASE_URL}")
#     print("=" * 60)

#     steps = [
#         test_auth,
#         test_courses,
#         test_classrooms,
#         test_enrollment,
#         test_sessions,
#         test_attendance,
#         test_modules,
#         test_assignments,
#         test_quiz,
#         test_dashboards,
#         test_schedule,
#         test_batch_analytics,
#         test_batch_chat,
#         test_course_qa,
#         test_dm_chat,
#         test_group_chat,
#         test_notifications,
#         test_instructor_apis,
#         test_resources_and_profile,
#         test_cleanup,
#     ]

#     for step in steps:
#         try:
#             step()
#         except Exception as e:
#             print(f"  💥 EXCEPTION in {step.__name__}: {e}")

#     print("\n" + "=" * 60)
#     print("  Test run complete. Review ✅/❌ above.")
#     print("=" * 60)

# if __name__ == "__main__":
#     main()



# lms_role_matrix.py
import json
import time
import uuid
import random
from datetime import datetime, timedelta, timezone

import requests

BASE_URL = "https://lms-backend-5r6q.onrender.com"
TIMEOUT = 30

session = requests.Session()

def uniq(prefix):
    return f"{prefix}-{int(time.time())}-{uuid.uuid4().hex[:6]}"

def unique_email(prefix):
    return f"{prefix}.{int(time.time())}.{uuid.uuid4().hex[:6]}@lmstest.com"

def unique_phone():
    return "9" + "".join(str(random.randint(0, 9)) for _ in range(9))

def safe_json(resp):
    try:
        return resp.json()
    except Exception:
        return resp.text[:500]

def fmt_result(role, resp):
    if resp is None:
        return f"{role}: no response"
    code = resp.status_code
    body = safe_json(resp)
    if code in (200, 201):
        return f"{role}: {code} works"
    if code == 403:
        detail = body.get("detail") if isinstance(body, dict) else body
        return f"{role}: 403 {detail}"
    if code == 401:
        detail = body.get("detail") if isinstance(body, dict) else body
        return f"{role}: 401 {detail}"
    if code == 400:
        detail = body.get("detail") if isinstance(body, dict) else body
        return f"{role}: 400 {detail}"
    if code == 404:
        detail = body.get("detail") if isinstance(body, dict) else body
        return f"{role}: 404 {detail}"
    if code == 500:
        return f"{role}: 500 Internal Server Error"
    return f"{role}: {code} {body}"

def request(method, path, token=None, params=None, json_body=None, data=None, files=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    url = f"{BASE_URL}{path}"
    try:
        return session.request(
            method,
            url,
            headers=headers,
            params=params,
            json=json_body,
            data=data,
            files=files,
            timeout=TIMEOUT,
        )
    except Exception as e:
        return None

def register_users():
    admin = {
        "name": "Admin User",
        "email": unique_email("admin"),
        "password": "Admin@1234",
        "role": "admin",
    }
    instructor = {
        "full_name": "Test Instructor",
        "email": unique_email("instructor"),
        "phone_number": unique_phone(),
        "password": "Instructor@1234",
        "specialization": "Python",
        "experience_years": 3,
        "skills": ["Python", "SQL"],
    }
    student = {
        "full_name": "Test Student",
        "email": unique_email("student"),
        "phone_number": unique_phone(),
        "password": "Student@1234",
        "gender": "Male",
        "date_of_birth": "2003-01-15",
        "interests": ["Python"],
    }

    r1 = request("POST", "/auth/register", json_body=admin)
    r2 = request("POST", "/auth/register/instructor", json_body=instructor)
    r3 = request("POST", "/auth/register/student", json_body=student)

    admin_login = request("POST", "/auth/login", json_body={"email": admin["email"], "password": admin["password"]})
    inst_login = request("POST", "/auth/login", json_body={"email": instructor["email"], "password": instructor["password"]})
    stu_login = request("POST", "/auth/login", json_body={"email": student["email"], "password": student["password"]})

    tokens = {
        "admin": admin_login.json().get("access_token") or admin_login.json().get("token"),
        "instructor": inst_login.json().get("access_token") or inst_login.json().get("token"),
        "student": stu_login.json().get("access_token") or stu_login.json().get("token"),
    }
    ids = {
        "admin": admin_login.json().get("user_id") or admin_login.json().get("id"),
        "instructor": inst_login.json().get("user_id") or inst_login.json().get("id"),
        "student": stu_login.json().get("user_id") or stu_login.json().get("id"),
    }
    return tokens, ids

def log_endpoint(method, path, responses_by_role):
    print(f"\n{method} {path}")
    for role in ["admin", "instructor", "student"]:
        print(fmt_result(role, responses_by_role.get(role)))

def main():
    tokens, ids = register_users()

    course = request(
        "POST",
        "/courses/create",
        token=tokens["instructor"],
        json_body={
            "course_code": uniq("PY101"),
            "name": "Python Fundamentals",
            "description": "Beginner Python course",
            "duration_months": 3,
            "total_lessons": 30,
        },
    )
    course_id = None
    if course and course.status_code in (200, 201):
        b = safe_json(course)
        if isinstance(b, dict):
            course_id = b.get("id") or b.get("course_id")

    if not course_id:
        print("Could not create course; stopping.")
        return

    endpoints = []

    endpoints.append(("GET", "/courses/my", None, None, None))
    endpoints.append(("POST", "/classrooms/", {"course_id": course_id, "batch_name": "Batch-A", "room_name": "Room 101", "schedule_type": "weekday", "start_month": "2026-07", "class_days": "Mon,Wed,Fri", "start_time": "10:00", "end_time": "12:00"}, None, None))

    batch_list = request("GET", "/courses/%s/batches" % course_id)
    batch_name = "Batch-A"
    try:
        batch_data = batch_list.json()
        if isinstance(batch_data, list) and batch_data:
            item = batch_data[0]
            batch_name = item.get("batch_name") or item.get("name") or item.get("batch") or batch_name
    except Exception:
        pass

    responses = {}

    def try_all(method, path, json_body=None, params=None, data=None, files=None):
        responses_by_role = {}
        for role in ["admin", "instructor", "student"]:
            resp = request(method, path, token=tokens[role], params=params, json_body=json_body, data=data, files=files)
            responses_by_role[role] = resp
        log_endpoint(method, path, responses_by_role)
        return responses_by_role

    try_all("GET", "/courses/my")

    try_all("POST", "/classrooms/", json_body={
        "course_id": course_id,
        "batch_name": batch_name,
        "room_name": "Room 101",
        "schedule_type": "weekday",
        "start_month": "2026-07",
        "class_days": "Mon,Wed,Fri",
        "start_time": "10:00",
        "end_time": "12:00",
    })

    try_all("GET", "/classrooms/")
    try_all("GET", f"/classrooms/course/{course_id}")
    try_all("GET", f"/classrooms/course/{course_id}/full")
    try_all("GET", f"/courses/{course_id}/classrooms")

    try_all("GET", "/enroll/courses")
    try_all("GET", "/enroll/batches", params={"course_id": course_id})
    try_all("GET", "/enroll/generate-id", params={"course_id": course_id})
    try_all("POST", "/enroll/student", params={
        "course_id": course_id,
        "batch_name": batch_name,
        "first_name": "Auto",
        "last_name": "Student",
        "email": unique_email("enrolled"),
    })

    try_all("GET", "/instructor-enroll/courses")
    try_all("GET", "/instructor-enroll/generate-id")
    try_all("GET", "/instructor-enroll/list")

    classroom_id = None
    classroom_resp = request("GET", "/classrooms/", token=tokens["admin"])
    try:
        cdata = classroom_resp.json()
        if isinstance(cdata, list) and cdata:
            classroom_id = cdata[0].get("id") or cdata[0].get("classroom_id")
    except Exception:
        pass

    if classroom_id:
        try_all("POST", f"/classrooms/{classroom_id}/start")
        try_all("GET", f"/classrooms/{classroom_id}")
        try_all("GET", f"/classrooms/{classroom_id}/schedule")
        try_all("PUT", f"/classrooms/{classroom_id}", json_body={"room_name": "Room 202"})
        try_all("DELETE", f"/classrooms/{classroom_id}")

    try_all("GET", "/dashboard/courses")
    try_all("GET", "/dashboard/classes-summary")
    try_all("GET", "/dashboard/admin/overview")
    try_all("GET", "/dashboard/admin/students")
    try_all("GET", "/dashboard/admin/instructors")
    try_all("GET", "/dashboard/admin/courses")
    try_all("GET", "/dashboard/admin/live-sessions")
    try_all("GET", "/dashboard/admin/")
    try_all("GET", "/dashboard/student/overview")
    try_all("GET", "/dashboard/student/courses")
    try_all("GET", "/dashboard/student/live-classes")
    try_all("GET", "/dashboard/student/attendance")
    try_all("GET", "/student/dashboard")
    try_all("GET", "/student/materials")
    try_all("GET", "/student/assignments")
    try_all("GET", "/student/tests")
    try_all("GET", "/student/certificates")
    try_all("GET", "/instructor/dashboard")

    if classroom_id:
        try_all("POST", "/sessions/start", params={"classroom_id": classroom_id})
        try_all("GET", "/sessions/active", params={"classroom_id": classroom_id})
        try_all("POST", "/sessions/join", params={"classroom_id": classroom_id})
        try_all("GET", "/sessions/history")
        try_all("GET", "/sessions/session/1")
        try_all("POST", "/sessions/1/access")
        try_all("POST", "/sessions/leave", params={"session_id": 1})
        try_all("POST", "/sessions/end", params={"session_id": 1})
        try_all("POST", "/attendance/join", params={"session_id": 1})
        try_all("GET", "/attendance/session/1")
        try_all("POST", "/attendance/leave", params={"session_id": 1})
        try_all("GET", "/students/me/attendance/summary")
        try_all("GET", "/students/me/attendance/history")
        try_all("GET", "/students/me/attendance/details")

    module = request("POST", "/modules/", token=tokens["instructor"], json_body={
        "title": "Module 1",
        "order": 1,
        "course_id": course_id,
        "batch_name": batch_name,
    })
    module_id = None
    if module and module.status_code in (200, 201):
        md = safe_json(module)
        if isinstance(md, dict):
            module_id = md.get("id") or md.get("module_id")

    if module_id:
        try_all("GET", "/modules/")
        try_all("POST", f"/modules/{module_id}/chapters", json_body={"title": "Chapter 1", "order": 1})

    try_all("GET", "/assignments/courses")
    try_all("GET", "/assignments/batches", params={"course_id": course_id})
    try_all("GET", "/assignments/modules", params={"course_id": course_id, "batch_name": batch_name})
    try_all("POST", "/assignments/", data={
        "title": "Homework 1",
        "description": "Solve exercises",
        "course_id": str(course_id),
        "batch_name": batch_name,
        "module_id": str(module_id or ""),
        "due_date": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
    })
    try_all("GET", "/assignments/")

    try_all("POST", "/tests/", json_body={
        "title": "Quiz 1",
        "course_id": course_id,
        "batch_name": batch_name,
        "module_id": module_id,
    })
    try_all("GET", "/resources")
    try_all("GET", "/notifications/")
    try_all("PATCH", "/notifications/read-all")

    try_all("GET", "/api/courses/%s/qa" % course_id)
    try_all("POST", "/api/courses/%s/qa" % course_id, json_body={"question": "Test question"})
    try_all("GET", f"/chat/{course_id}/{batch_name}")
    try_all("POST", f"/chat/{course_id}/{batch_name}", json_body={"content": "Hello"})
    try_all("GET", f"/chat/{course_id}/{batch_name}/1")
    try_all("POST", f"/chat/{course_id}/{batch_name}/1/replies", json_body={"content": "Reply"})
    try_all("POST", f"/chat/{course_id}/{batch_name}/1/like")
    try_all("POST", f"/chat/{course_id}/{batch_name}/1/bookmark")
    try_all("GET", f"/chat/{course_id}/{batch_name}/bookmarks/my")
    try_all("POST", f"/chat/{course_id}/{batch_name}/1/pin")

    try_all("GET", "/api/chats/groups/by-batch")
    try_all("POST", "/api/chats/groups/2/messages", json_body={"content": "hello"})
    try_all("GET", "/api/chats/groups/2/messages")
    try_all("PATCH", "/api/chats/groups/2/read")
    try_all("POST", "/api/chats/groups/messages/2/like")
    try_all("PATCH", "/api/chats/groups/messages/2/bookmark")
    try_all("PATCH", "/api/chats/groups/2/messages/2/pin")

    try_all("GET", "/instructor/sessions")
    try_all("GET", "/instructor/assignment-submissions")
    try_all("GET", "/instructor/test-results")

    try_all("DELETE", f"/courses/{course_id}")

if __name__ == "__main__":
    main()




"""
LMS Backend Automated API Test Suite
Base URL: https://lms-backend-5r6q.onrender.com

Run:
    pip install requests pytest
    pytest lms_api_tests.py -v
    or
    python lms_api_tests.py   (standalone runner at bottom)
"""

import requests
import json
import time

BASE_URL = "https://lms-backend-5r6q.onrender.com"

# ─── Shared state (populated during test run) ───────────────────────────────
state = {
    "admin_token": None,
    "instructor_token": None,
    "student_token": None,
    "course_id": None,
    "classroom_id": None,
    "session_id": None,
    "assignment_id": None,
    "module_id": None,
    "chapter_id": None,
    "test_id": None,
    "test_submission_id": None,
    "assignment_submission_id": None,
    "dm_conversation_id": None,
    "group_id": None,
    "notification_id": None,
    "qa_post_id": None,
    "chat_post_id": None,
    "instructor_user_id": None,
    "student_user_id": None,
}

# ─── Test accounts (change these to match your DB or let registration create them) ──
ADMIN = {
    "email": "admin@lmstest.com",
    "password": "Admin@1234",
    "name": "Admin User",
    "role": "admin",
}
INSTRUCTOR = {
    "email": "instructor@lmstest.com",
    "password": "Instructor@1234",
    "full_name": "Test Instructor",
    "phone_number": "9876543210",
}
STUDENT = {
    "email": "student@lmstest.com",
    "password": "Student@1234",
    "full_name": "Test Student",
    "phone_number": "9876543211",
}


# ─── Helpers ────────────────────────────────────────────────────────────────
def auth_header(role="instructor"):
    token = state.get(f"{role}_token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def post(path, json_data=None, data=None, files=None, headers=None):
    h = headers or {}
    return requests.post(f"{BASE_URL}{path}", json=json_data, data=data, files=files, headers=h, timeout=30)


def get(path, params=None, headers=None):
    return requests.get(f"{BASE_URL}{path}", params=params, headers=headers or {}, timeout=30)


def put(path, json_data=None, data=None, headers=None):
    return requests.put(f"{BASE_URL}{path}", json=json_data, data=data, headers=headers or {}, timeout=30)


def patch(path, json_data=None, headers=None):
    return requests.patch(f"{BASE_URL}{path}", json=json_data, headers=headers or {}, timeout=30)


def delete(path, headers=None):
    return requests.delete(f"{BASE_URL}{path}", headers=headers or {}, timeout=30)


def ok(r, label):
    passed = r.status_code in (200, 201)
    status = "✅ PASS" if passed else f"❌ FAIL [{r.status_code}]"
    print(f"  {status}  {label}")
    if not passed:
        try:
            print(f"         {r.json()}")
        except Exception:
            print(f"         {r.text[:200]}")
    return passed


# ════════════════════════════════════════════════════════════════════════════
# 1. AUTH
# ════════════════════════════════════════════════════════════════════════════
def test_auth():
    print("\n── AUTH ──────────────────────────────────────────────")

    # Register admin (generic)
    r = post("/auth/register", json_data={
        "name": ADMIN["name"], "email": ADMIN["email"],
        "password": ADMIN["password"], "role": ADMIN["role"]
    })
    ok(r, "POST /auth/register (admin)")

    # Register instructor
    r = post("/auth/register/instructor", json_data={
        "full_name": INSTRUCTOR["full_name"],
        "email": INSTRUCTOR["email"],
        "phone_number": INSTRUCTOR["phone_number"],
        "password": INSTRUCTOR["password"],
        "specialization": "Python & ML",
        "experience_years": 3,
        "skills": ["Python", "Machine Learning", "SQL"],
    })
    ok(r, "POST /auth/register/instructor")

    # Register student
    r = post("/auth/register/student", json_data={
        "full_name": STUDENT["full_name"],
        "email": STUDENT["email"],
        "phone_number": STUDENT["phone_number"],
        "password": STUDENT["password"],
        "gender": "Male",
        "date_of_birth": "2003-01-15",
        "interests": ["AI", "Python"],
    })
    ok(r, "POST /auth/register/student")

    # Login admin
    r = post("/auth/login", json_data={"email": ADMIN["email"], "password": ADMIN["password"]})
    if ok(r, "POST /auth/login (admin)"):
        body = r.json()
        state["admin_token"] = body.get("access_token") or body.get("token")

    # Login instructor
    r = post("/auth/login", json_data={"email": INSTRUCTOR["email"], "password": INSTRUCTOR["password"]})
    if ok(r, "POST /auth/login (instructor)"):
        body = r.json()
        state["instructor_token"] = body.get("access_token") or body.get("token")

    # Login student
    r = post("/auth/login", json_data={"email": STUDENT["email"], "password": STUDENT["password"]})
    if ok(r, "POST /auth/login (student)"):
        body = r.json()
        state["student_token"] = body.get("access_token") or body.get("token")
        state["student_user_id"] = body.get("user_id") or body.get("id")


# ════════════════════════════════════════════════════════════════════════════
# 2. COURSES
# ════════════════════════════════════════════════════════════════════════════
def test_courses():
    print("\n── COURSES ───────────────────────────────────────────")
    h = auth_header("instructor")

    r = post("/courses/create", json_data={
        "course_code": "PY101",
        "name": "Python Fundamentals",
        "description": "Beginner Python course",
        "duration_months": 3,
        "total_lessons": 30,
    }, headers=h)
    if ok(r, "POST /courses/create"):
        state["course_id"] = r.json().get("id")

    r = get("/courses/", headers=h)
    ok(r, "GET /courses/")

    r = get("/courses/my", headers=h)
    ok(r, "GET /courses/my")

    if state["course_id"]:
        cid = state["course_id"]
        r = get(f"/courses/{cid}/batches")
        ok(r, f"GET /courses/{cid}/batches")

        r = put(f"/courses/update/{cid}", json_data={"description": "Updated description"}, headers=h)
        ok(r, f"PUT /courses/update/{cid}")

        r = get(f"/courses/{cid}/full-overview", headers=h)
        ok(r, f"GET /courses/{cid}/full-overview")


# ════════════════════════════════════════════════════════════════════════════
# 3. CLASSROOMS
# ════════════════════════════════════════════════════════════════════════════
def test_classrooms():
    print("\n── CLASSROOMS ────────────────────────────────────────")
    h = auth_header("instructor")
    cid = state["course_id"]
    if not cid:
        print("  ⚠️  Skipped — no course_id")
        return

    r = post("/classrooms/", json_data={
        "course_id": cid,
        "batch_name": "Batch-A",
        "room_name": "Room 101",
        "schedule_type": "weekday",
        "start_month": "2026-07",
        "class_days": "Mon,Wed,Fri",
        "start_time": "10:00",
        "end_time": "12:00",
    }, headers=h)
    if ok(r, "POST /classrooms/"):
        state["classroom_id"] = r.json().get("id")

    r = get("/classrooms/", headers=h)
    ok(r, "GET /classrooms/")

    if state["classroom_id"]:
        rid = state["classroom_id"]
        r = get(f"/classrooms/{rid}", headers=h)
        ok(r, f"GET /classrooms/{rid}")

        r = get(f"/classrooms/{rid}/schedule", headers=h)
        ok(r, f"GET /classrooms/{rid}/schedule")

        r = get(f"/classrooms/course/{cid}", headers=h)
        ok(r, f"GET /classrooms/course/{cid}")

        r = get(f"/classrooms/course/{cid}/full", headers=h)
        ok(r, f"GET /classrooms/course/{cid}/full")

        r = put(f"/classrooms/{rid}", json_data={"room_name": "Room 202"}, headers=h)
        ok(r, f"PUT /classrooms/{rid}")

        r = get(f"/courses/{cid}/classrooms", headers=h)
        ok(r, f"GET /courses/{cid}/classrooms")


# ════════════════════════════════════════════════════════════════════════════
# 4. ENROLLMENT
# ════════════════════════════════════════════════════════════════════════════
def test_enrollment():
    print("\n── ENROLLMENT ────────────────────────────────────────")
    h = auth_header("instructor")
    cid = state["course_id"]
    if not cid:
        print("  ⚠️  Skipped — no course_id")
        return

    r = get("/enroll/courses", headers=h)
    ok(r, "GET /enroll/courses")

    r = get("/enroll/batches", params={"course_id": cid}, headers=h)
    ok(r, "GET /enroll/batches")

    r = get("/enroll/generate-id", params={"course_id": cid}, headers=h)
    ok(r, "GET /enroll/generate-id")

    r = post("/enroll/student", params={
        "course_id": cid,
        "batch_name": "Batch-A",
        "first_name": "Auto",
        "last_name": "Student",
        "email": STUDENT["email"],
    }, headers=h)
    ok(r, "POST /enroll/student")

    # Instructor enrollment
    r = get("/instructor-enroll/courses", headers=h)
    ok(r, "GET /instructor-enroll/courses")

    r = get("/instructor-enroll/generate-id", headers=h)
    ok(r, "GET /instructor-enroll/generate-id")

    r = get("/instructor-enroll/list", headers=h)
    if ok(r, "GET /instructor-enroll/list"):
        data = r.json()
        if data:
            state["instructor_user_id"] = data[0].get("user_id") or data[0].get("id")


# ════════════════════════════════════════════════════════════════════════════
# 5. SESSIONS
# ════════════════════════════════════════════════════════════════════════════
def test_sessions():
    print("\n── SESSIONS ──────────────────────────────────────────")
    h = auth_header("instructor")
    rid = state["classroom_id"]
    if not rid:
        print("  ⚠️  Skipped — no classroom_id")
        return

    r = post("/sessions/start", params={"classroom_id": rid}, headers=h)
    if ok(r, "POST /sessions/start"):
        state["session_id"] = r.json().get("session_id") or r.json().get("id")

    r = get("/sessions/active", params={"classroom_id": rid}, headers=h)
    ok(r, "GET /sessions/active")

    # Student joins
    sh = auth_header("student")
    r = post("/sessions/join", params={"classroom_id": rid}, headers=sh)
    ok(r, "POST /sessions/join (student)")

    r = get("/sessions/history", headers=h)
    ok(r, "GET /sessions/history")

    if state["session_id"]:
        sid = state["session_id"]
        r = get(f"/sessions/session/{sid}")
        ok(r, f"GET /sessions/session/{sid}")

        r = post(f"/sessions/{sid}/access", headers=sh)
        ok(r, f"POST /sessions/{sid}/access")

        # Student leaves
        r = post("/sessions/leave", params={"session_id": sid}, headers=sh)
        ok(r, "POST /sessions/leave (student)")

        # Instructor ends
        r = post("/sessions/end", params={"session_id": sid}, headers=h)
        ok(r, "POST /sessions/end")


# ════════════════════════════════════════════════════════════════════════════
# 6. ATTENDANCE
# ════════════════════════════════════════════════════════════════════════════
def test_attendance():
    print("\n── ATTENDANCE ────────────────────────────────────────")
    sh = auth_header("student")
    sid = state["session_id"]
    if not sid:
        print("  ⚠️  Skipped — no session_id")
        return

    r = post("/attendance/join", params={"session_id": sid}, headers=sh)
    ok(r, "POST /attendance/join")

    r = get(f"/attendance/session/{sid}", headers=sh)
    ok(r, f"GET /attendance/session/{sid}")

    r = post("/attendance/leave", params={"session_id": sid}, headers=sh)
    ok(r, "POST /attendance/leave")

    # Student attendance summary
    r = get("/students/me/attendance/summary", headers=sh)
    ok(r, "GET /students/me/attendance/summary")

    r = get("/students/me/attendance/history", headers=sh)
    ok(r, "GET /students/me/attendance/history")

    r = get("/students/me/attendance/details", headers=sh)
    ok(r, "GET /students/me/attendance/details")


# ════════════════════════════════════════════════════════════════════════════
# 7. MODULES & CHAPTERS
# ════════════════════════════════════════════════════════════════════════════
def test_modules():
    print("\n── MODULES & CHAPTERS ────────────────────────────────")
    h = auth_header("instructor")
    cid = state["course_id"]
    if not cid:
        print("  ⚠️  Skipped — no course_id")
        return

    r = post("/modules/", json_data={
        "title": "Module 1: Python Basics",
        "order": 1,
        "course_id": cid,
        "batch_name": "Batch-A",
    }, headers=h)
    if ok(r, "POST /modules/"):
        state["module_id"] = r.json().get("id")

    r = get("/modules/", params={"course_id": cid, "batch_name": "Batch-A"}, headers=h)
    ok(r, "GET /modules/")

    if state["module_id"]:
        mid = state["module_id"]
        r = post(f"/modules/{mid}/chapters", json_data={"title": "Chapter 1: Variables", "order": 1}, headers=h)
        if ok(r, f"POST /modules/{mid}/chapters"):
            state["chapter_id"] = r.json().get("id")


# ════════════════════════════════════════════════════════════════════════════
# 8. ASSIGNMENTS
# ════════════════════════════════════════════════════════════════════════════
def test_assignments():
    print("\n── ASSIGNMENTS ───────────────────────────────────────")
    h = auth_header("instructor")
    sh = auth_header("student")
    cid = state["course_id"]
    mid = state["module_id"]
    if not cid or not mid:
        print("  ⚠️  Skipped — no course_id or module_id")
        return

    r = get("/assignments/courses", headers=h)
    ok(r, "GET /assignments/courses")

    r = get("/assignments/batches", params={"course_id": cid}, headers=h)
    ok(r, "GET /assignments/batches")

    r = get("/assignments/modules", params={"course_id": cid, "batch_name": "Batch-A"}, headers=h)
    ok(r, "GET /assignments/modules")

    # Create assignment (multipart)
    form_data = {
        "course_id": (None, str(cid)),
        "batch_name": (None, "Batch-A"),
        "module_id": (None, str(mid)),
        "title": (None, "Assignment 1: Hello World"),
        "description": (None, "Write a Hello World program"),
        "expected_outcome": (None, "print('Hello World')"),
        "due_date": (None, "2026-07-30T23:59:00"),
    }
    r = requests.post(f"{BASE_URL}/assignments/", files=form_data, headers=h, timeout=30)
    if ok(r, "POST /assignments/"):
        state["assignment_id"] = r.json().get("id")

    r = get("/assignments/", params={"course_id": cid, "batch_name": "Batch-A"}, headers=h)
    ok(r, "GET /assignments/")

    if state["assignment_id"]:
        aid = state["assignment_id"]

        r = get(f"/assignments/{aid}", headers=h)
        ok(r, f"GET /assignments/{aid}")

        r = get(f"/assignments/{aid}/submissions", headers=h)
        ok(r, f"GET /assignments/{aid}/submissions")

        # Student views assignments
        r = get("/assignments/my/list", headers=sh)
        ok(r, "GET /assignments/my/list")

        r = get("/assignments/dashboard", headers=sh)
        ok(r, "GET /assignments/dashboard")

        # Student submits
        sub_data = {
            "submission_text": (None, "print('Hello World')"),
        }
        r = requests.post(f"{BASE_URL}/assignments/{aid}/submit", files=sub_data, headers=sh, timeout=30)
        if ok(r, f"POST /assignments/{aid}/submit"):
            state["assignment_submission_id"] = r.json().get("id")

        r = get(f"/assignments/{aid}/my-submission", headers=sh)
        ok(r, f"GET /assignments/{aid}/my-submission")

        # Instructor grades
        if state["assignment_submission_id"]:
            subid = state["assignment_submission_id"]
            r = put(
                f"/assignments/{aid}/submissions/{subid}/grade",
                data={"grade": "A", "feedback": "Great work!"},
                headers=h,
            )
            ok(r, f"PUT /assignments/{aid}/submissions/{subid}/grade")

        r = put(f"/assignments/{aid}", json_data={"description": "Updated description"}, headers=h)
        ok(r, f"PUT /assignments/{aid}")


# ════════════════════════════════════════════════════════════════════════════
# 9. TESTS (QUIZZES)
# ════════════════════════════════════════════════════════════════════════════
def test_tests():
    print("\n── TESTS (QUIZZES) ───────────────────────────────────")
    h = auth_header("instructor")
    sh = auth_header("student")
    cid = state["course_id"]
    mid = state["module_id"]
    if not cid or not mid:
        print("  ⚠️  Skipped — no course_id or module_id")
        return

    r = post("/tests/", json_data={
        "title": "Quiz 1: Python Basics",
        "course_id": cid,
        "batch_name": "Batch-A",
        "module_id": mid,
        "description": "Basic Python quiz",
        "start_time": "2026-06-01T09:00:00",
        "end_time": "2026-12-31T23:59:00",
        "questions": [
            {
                "text": "What is the output of print(2+2)?",
                "options": [
                    {"text": "4", "is_correct": True},
                    {"text": "22", "is_correct": False},
                    {"text": "Error", "is_correct": False},
                    {"text": "None", "is_correct": False},
                ],
            },
            {
                "text": "Which keyword defines a function in Python?",
                "options": [
                    {"text": "def", "is_correct": True},
                    {"text": "func", "is_correct": False},
                    {"text": "fun", "is_correct": False},
                    {"text": "function", "is_correct": False},
                ],
            },
        ],
    }, headers=h)
    if ok(r, "POST /tests/"):
        state["test_id"] = r.json().get("id")
        questions = r.json().get("questions", [])
        state["test_questions"] = questions

    if state["test_id"]:
        tid = state["test_id"]

        r = put(f"/tests/{tid}", json_data={"description": "Updated quiz description"}, headers=h)
        ok(r, f"PUT /tests/{tid}")

        r = get(f"/tests/{tid}/details", headers=h)
        ok(r, f"GET /tests/{tid}/details")

        # Student starts test
        r = post(f"/tests/{tid}/start", headers=sh)
        if ok(r, f"POST /tests/{tid}/start"):
            state["test_submission_id"] = r.json().get("submission_id") or r.json().get("id")

        # Student submits test
        questions = state.get("test_questions", [])
        answers = []
        for q in questions:
            opts = q.get("options", [])
            if opts:
                answers.append({"question_id": q["id"], "selected_option_id": opts[0]["id"]})

        if answers:
            r = post(f"/tests/{tid}/submit", json_data={"answers": answers}, headers=sh)
            ok(r, f"POST /tests/{tid}/submit")

        # Instructor reviews submission
        if state["test_submission_id"]:
            subid = state["test_submission_id"]
            r = get(f"/tests/{tid}/submission/{subid}", headers=h)
            ok(r, f"GET /tests/{tid}/submission/{subid}")


# ════════════════════════════════════════════════════════════════════════════
# 10. DASHBOARD
# ════════════════════════════════════════════════════════════════════════════
def test_dashboard():
    print("\n── DASHBOARD ─────────────────────────────────────────")
    ih = auth_header("instructor")
    sh = auth_header("student")
    ah = auth_header("admin")

    r = get("/dashboard/courses", headers=ih)
    ok(r, "GET /dashboard/courses")

    r = get("/dashboard/classes-summary", headers=ih)
    ok(r, "GET /dashboard/classes-summary")

    r = get("/dashboard/admin/overview", headers=ah)
    ok(r, "GET /dashboard/admin/overview")

    r = get("/dashboard/admin/students", headers=ah)
    ok(r, "GET /dashboard/admin/students")

    r = get("/dashboard/admin/instructors", headers=ah)
    ok(r, "GET /dashboard/admin/instructors")

    r = get("/dashboard/admin/courses", headers=ah)
    ok(r, "GET /dashboard/admin/courses")

    r = get("/dashboard/admin/live-sessions", headers=ah)
    ok(r, "GET /dashboard/admin/live-sessions")

    r = get("/dashboard/admin/", headers=ih)
    ok(r, "GET /dashboard/admin/ (instructor)")

    r = get("/dashboard/student/overview", headers=sh)
    ok(r, "GET /dashboard/student/overview")

    r = get("/dashboard/student/courses", headers=sh)
    ok(r, "GET /dashboard/student/courses")

    r = get("/dashboard/student/live-classes", headers=sh)
    ok(r, "GET /dashboard/student/live-classes")

    r = get("/dashboard/student/attendance", headers=sh)
    ok(r, "GET /dashboard/student/attendance")

    r = get("/student/dashboard", headers=sh)
    ok(r, "GET /student/dashboard")

    r = get("/student/materials", headers=sh)
    ok(r, "GET /student/materials")

    r = get("/student/assignments", headers=sh)
    ok(r, "GET /student/assignments")

    r = get("/student/tests", headers=sh)
    ok(r, "GET /student/tests")

    r = get("/student/certificates", headers=sh)
    ok(r, "GET /student/certificates")

    r = get("/instructor/dashboard", headers=ih)
    ok(r, "GET /instructor/dashboard")


# ════════════════════════════════════════════════════════════════════════════
# 11. SCHEDULE
# ════════════════════════════════════════════════════════════════════════════
def test_schedule():
    print("\n── SCHEDULE ──────────────────────────────────────────")
    h = auth_header("instructor")
    cid = state["course_id"]
    if not cid:
        print("  ⚠️  Skipped — no course_id")
        return

    params = {"course_id": cid, "batch_name": "Batch-A"}
    r = get("/schedule/", params=params, headers=h)
    ok(r, "GET /schedule/")

    r = get("/schedule/upcoming", params=params, headers=h)
    ok(r, "GET /schedule/upcoming")


# ════════════════════════════════════════════════════════════════════════════
# 12. BATCH ANALYTICS
# ════════════════════════════════════════════════════════════════════════════
def test_batch_analytics():
    print("\n── BATCH ANALYTICS ───────────────────────────────────")
    h = auth_header("instructor")
    cid = state["course_id"]
    if not cid:
        print("  ⚠️  Skipped — no course_id")
        return

    r = get(f"/batches/{cid}/list", headers=h)
    ok(r, f"GET /batches/{cid}/list")

    r = get(f"/batches/{cid}/Batch-A/overview", headers=h)
    ok(r, f"GET /batches/{cid}/Batch-A/overview")


# ════════════════════════════════════════════════════════════════════════════
# 13. CHAT / Q&A (Batch Feed)
# ════════════════════════════════════════════════════════════════════════════
def test_chat():
    print("\n── CHAT / Q&A (BATCH FEED) ───────────────────────────")
    h = auth_header("instructor")
    cid = state["course_id"]
    if not cid:
        print("  ⚠️  Skipped — no course_id")
        return

    r = post(f"/chat/{cid}/Batch-A", json_data={
        "course_id": cid,
        "batch_name": "Batch-A",
        "content": "Welcome to the batch! Ask your doubts here.",
    }, headers=h)
    if ok(r, f"POST /chat/{cid}/Batch-A"):
        state["chat_post_id"] = r.json().get("id")

    r = get(f"/chat/{cid}/Batch-A", headers=h)
    ok(r, f"GET /chat/{cid}/Batch-A")

    if state["chat_post_id"]:
        pid = state["chat_post_id"]

        r = get(f"/chat/{cid}/Batch-A/{pid}", headers=h)
        ok(r, f"GET /chat/{cid}/Batch-A/{pid}")

        r = post(f"/chat/{cid}/Batch-A/{pid}/replies",
                 json_data={"content": "Thank you sir!"}, headers=auth_header("student"))
        ok(r, f"POST /chat/{cid}/Batch-A/{pid}/replies")

        r = post(f"/chat/{cid}/Batch-A/{pid}/like", headers=auth_header("student"))
        ok(r, f"POST /chat/{cid}/Batch-A/{pid}/like (toggle)")

        r = post(f"/chat/{cid}/Batch-A/{pid}/bookmark", headers=auth_header("student"))
        ok(r, f"POST /chat/{cid}/Batch-A/{pid}/bookmark (toggle)")

        r = get(f"/chat/{cid}/Batch-A/bookmarks/my", headers=auth_header("student"))
        ok(r, f"GET /chat/{cid}/Batch-A/bookmarks/my")

        r = post(f"/chat/{cid}/Batch-A/{pid}/pin", headers=h)
        ok(r, f"POST /chat/{cid}/Batch-A/{pid}/pin (toggle)")


# ════════════════════════════════════════════════════════════════════════════
# 14. COURSE Q&A
# ════════════════════════════════════════════════════════════════════════════
def test_course_qa():
    print("\n── COURSE Q&A ────────────────────────────────────────")
    sh = auth_header("student")
    h = auth_header("instructor")
    cid = state["course_id"]
    if not cid:
        print("  ⚠️  Skipped — no course_id")
        return

    r = post(f"/api/courses/{cid}/qa", params={"batch_name": "Batch-A"}, json_data={
        "title": "How do I run Python?",
        "description": "I installed Python but don't know how to run it.",
        "visibility": "public",
    }, headers=sh)
    if ok(r, f"POST /api/courses/{cid}/qa"):
        state["qa_post_id"] = r.json().get("id")

    r = get(f"/api/courses/{cid}/qa", params={"batch_name": "Batch-A"}, headers=sh)
    ok(r, f"GET /api/courses/{cid}/qa")

    if state["qa_post_id"]:
        qid = state["qa_post_id"]

        r = post(f"/api/courses/{cid}/qa/{qid}/like", headers=sh)
        ok(r, f"POST /api/courses/{cid}/qa/{qid}/like")

        r = patch(f"/api/courses/{cid}/qa/{qid}/bookmark", headers=sh)
        ok(r, f"PATCH /api/courses/{cid}/qa/{qid}/bookmark")

        r = post(f"/api/courses/{cid}/qa/{qid}/replies",
                 json_data={"content": "Open terminal and type python filename.py"}, headers=h)
        ok(r, f"POST /api/courses/{cid}/qa/{qid}/replies")

        r = get(f"/api/courses/{cid}/qa/{qid}/replies", headers=sh)
        ok(r, f"GET /api/courses/{cid}/qa/{qid}/replies")

        r = patch(f"/api/courses/{cid}/qa/{qid}/pin", headers=h)
        ok(r, f"PATCH /api/courses/{cid}/qa/{qid}/pin")

        r = patch(f"/api/courses/{cid}/qa/{qid}/visibility",
                  json_data={"visibility": "public"}, headers=h)
        ok(r, f"PATCH /api/courses/{cid}/qa/{qid}/visibility")


# ════════════════════════════════════════════════════════════════════════════
# 15. DM CHAT
# ════════════════════════════════════════════════════════════════════════════
def test_dm_chat():
    print("\n── DM CHAT ───────────────────────────────────────────")
    sh = auth_header("student")
    uid = state.get("instructor_user_id")

    if not uid:
        print("  ⚠️  Skipped — no instructor_user_id to DM")
        return

    r = post("/api/chats/conversations", json_data={"user_id": uid}, headers=sh)
    if ok(r, "POST /api/chats/conversations"):
        state["dm_conversation_id"] = r.json().get("id")

    r = get("/api/chats/conversations", headers=sh)
    ok(r, "GET /api/chats/conversations")

    if state["dm_conversation_id"]:
        cid = state["dm_conversation_id"]

        r = post(f"/api/chats/conversations/{cid}/messages",
                 json_data={"text": "Hello sir, I have a question about the assignment."}, headers=sh)
        msg_id = None
        if ok(r, f"POST /api/chats/conversations/{cid}/messages"):
            msg_id = r.json().get("id")

        r = get(f"/api/chats/conversations/{cid}/messages", headers=sh)
        ok(r, f"GET /api/chats/conversations/{cid}/messages")

        r = patch(f"/api/chats/conversations/{cid}/read", headers=sh)
        ok(r, f"PATCH /api/chats/conversations/{cid}/read")

        if msg_id:
            r = post(f"/api/chats/messages/{msg_id}/like", headers=auth_header("instructor"))
            ok(r, f"POST /api/chats/messages/{msg_id}/like")

            r = patch(f"/api/chats/messages/{msg_id}/bookmark", headers=sh)
            ok(r, f"PATCH /api/chats/messages/{msg_id}/bookmark")


# ════════════════════════════════════════════════════════════════════════════
# 16. GROUP CHAT
# ════════════════════════════════════════════════════════════════════════════
def test_group_chat():
    print("\n── GROUP CHAT ────────────────────────────────────────")
    h = auth_header("instructor")
    cid = state["course_id"]
    if not cid:
        print("  ⚠️  Skipped — no course_id")
        return

    r = get("/api/chats/groups/by-batch", params={"course_id": cid, "batch_name": "Batch-A"}, headers=h)
    if ok(r, "GET /api/chats/groups/by-batch"):
        state["group_id"] = r.json().get("group_id") or r.json().get("id")

    if state["group_id"]:
        gid = state["group_id"]

        r = post(f"/api/chats/groups/{gid}/messages",
                 json_data={"text": "Good morning batch! Today we cover loops."}, headers=h)
        gmsg_id = None
        if ok(r, f"POST /api/chats/groups/{gid}/messages"):
            gmsg_id = r.json().get("id")

        r = get(f"/api/chats/groups/{gid}/messages", headers=h)
        ok(r, f"GET /api/chats/groups/{gid}/messages")

        r = get(f"/api/chats/groups/{gid}/members", headers=h)
        ok(r, f"GET /api/chats/groups/{gid}/members")

        r = patch(f"/api/chats/groups/{gid}/read", headers=auth_header("student"))
        ok(r, f"PATCH /api/chats/groups/{gid}/read")

        if gmsg_id:
            r = post(f"/api/chats/groups/messages/{gmsg_id}/like", headers=auth_header("student"))
            ok(r, f"POST /api/chats/groups/messages/{gmsg_id}/like")

            r = patch(f"/api/chats/groups/messages/{gmsg_id}/bookmark", headers=auth_header("student"))
            ok(r, f"PATCH /api/chats/groups/messages/{gmsg_id}/bookmark")

            r = patch(f"/api/chats/groups/{gid}/messages/{gmsg_id}/pin", headers=h)
            ok(r, f"PATCH /api/chats/groups/{gid}/messages/{gmsg_id}/pin")


# ════════════════════════════════════════════════════════════════════════════
# 17. NOTIFICATIONS
# ════════════════════════════════════════════════════════════════════════════
def test_notifications():
    print("\n── NOTIFICATIONS ─────────────────────────────────────")
    h = auth_header("instructor")

    r = get("/notifications/", headers=h)
    if ok(r, "GET /notifications/"):
        data = r.json()
        # Handle grouped or flat response
        items = data if isinstance(data, list) else data.get("today", []) or data.get("notifications", [])
        if items:
            state["notification_id"] = items[0].get("id")

    r = patch("/notifications/read-all", headers=h)
    ok(r, "PATCH /notifications/read-all")

    if state["notification_id"]:
        nid = state["notification_id"]
        r = patch(f"/notifications/{nid}/read", headers=h)
        ok(r, f"PATCH /notifications/{nid}/read")

        r = delete(f"/notifications/{nid}", headers=h)
        ok(r, f"DELETE /notifications/{nid}")


# ════════════════════════════════════════════════════════════════════════════
# 18. INSTRUCTOR APIs
# ════════════════════════════════════════════════════════════════════════════
def test_instructor_apis():
    print("\n── INSTRUCTOR APIs ───────────────────────────────────")
    h = auth_header("instructor")
    cid = state["course_id"]

    r = get("/instructor/sessions", params={"course_id": cid, "batch_name": "Batch-A"} if cid else {}, headers=h)
    ok(r, "GET /instructor/sessions")

    r = get("/instructor/assignment-submissions", params={"course_id": cid} if cid else {}, headers=h)
    ok(r, "GET /instructor/assignment-submissions")

    r = get("/instructor/test-results", params={"course_id": cid} if cid else {}, headers=h)
    ok(r, "GET /instructor/test-results")


# ════════════════════════════════════════════════════════════════════════════
# 19. RESOURCES
# ════════════════════════════════════════════════════════════════════════════
def test_resources():
    print("\n── RESOURCES ─────────────────────────────────────────")
    h = auth_header("instructor")

    r = get("/resources", headers=h)
    ok(r, "GET /resources")

    # Chapter resources (file upload — skipped automatically if no file)
    # Uncomment and provide a real file path to test:
    # chid = state["chapter_id"]
    # if chid:
    #     with open("/path/to/test.pdf", "rb") as f:
    #         r = requests.post(f"{BASE_URL}/chapter-resources/{chid}",
    #                           files={"files": f}, headers=h, timeout=30)
    #         ok(r, f"POST /chapter-resources/{chid}")


# ════════════════════════════════════════════════════════════════════════════
# 20. USER PROFILE
# ════════════════════════════════════════════════════════════════════════════
def test_user_profile():
    print("\n── USER PROFILE ──────────────────────────────────────")
    h = auth_header("instructor")
    uid = state.get("student_user_id")
    if not uid:
        print("  ⚠️  Skipped — no student_user_id")
        return

    r = get(f"/api/users/{uid}/profile", headers=h)
    ok(r, f"GET /api/users/{uid}/profile")

    r = get(f"/api/users/{uid}/avatar")
    ok(r, f"GET /api/users/{uid}/avatar")

    cid = state["course_id"]
    if cid:
        r = get(f"/api/courses/{cid}/members", params={"batch_name": "Batch-A"}, headers=h)
        ok(r, f"GET /api/courses/{cid}/members")


# ════════════════════════════════════════════════════════════════════════════
# 21. CLEANUP (optional — delete created course)
# ════════════════════════════════════════════════════════════════════════════
def test_cleanup():
    print("\n── CLEANUP ───────────────────────────────────────────")
    h = auth_header("instructor")

    if state["assignment_id"]:
        r = delete(f"/assignments/{state['assignment_id']}", headers=h)
        ok(r, f"DELETE /assignments/{state['assignment_id']}")

    if state["classroom_id"]:
        r = delete(f"/classrooms/{state['classroom_id']}", headers=h)
        ok(r, f"DELETE /classrooms/{state['classroom_id']}")

    if state["course_id"]:
        r = delete(f"/courses/{state['course_id']}", headers=h)
        ok(r, f"DELETE /courses/{state['course_id']}")


# ════════════════════════════════════════════════════════════════════════════
# RUNNER
# ════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 60)
    print("  LMS Backend Automated Test Suite")
    print(f"  Target: {BASE_URL}")
    print("=" * 60)

    steps = [
        test_auth,
        test_courses,
        test_classrooms,
        test_enrollment,
        test_sessions,
        test_attendance,
        test_modules,
        test_assignments,
        test_tests,
        test_dashboard,
        test_schedule,
        test_batch_analytics,
        test_chat,
        test_course_qa,
        test_dm_chat,
        test_group_chat,
        test_notifications,
        test_instructor_apis,
        test_resources,
        test_user_profile,
        test_cleanup,
    ]

    for step in steps:
        try:
            step()
        except Exception as e:
            print(f"  💥 EXCEPTION in {step.__name__}: {e}")

    print("\n" + "=" * 60)
    print("  Test run complete. Review ✅/❌ above.")
    print("=" * 60)
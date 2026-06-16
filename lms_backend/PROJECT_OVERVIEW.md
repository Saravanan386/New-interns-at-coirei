# LMS Backend — Complete Project Overview
> Last Updated: May 2026 | Stack: FastAPI · SQLAlchemy · Neon (PostgreSQL) · 100ms · JWT

---

## 1. What This Project Is

A backend API for a Learning Management System (LMS) used by three roles:

| Role | What they do |
|---|---|
| **Admin** | Creates courses, batches (classrooms), enrolls instructors |
| **Instructor** | Starts live classes, creates tests/assignments, manages Q&A, sets schedules |
| **Student** | Joins live classes, submits tests/assignments, participates in Q&A and chat |

The backend is built on **FastAPI** with a **Neon PostgreSQL** database (via SQLAlchemy ORM). Live video is powered by **100ms**. Real-time chat uses **WebSockets**. Auth is JWT Bearer token-based with Role-Based Access Control (RBAC).

---

## 2. Current Project Structure

```
app/
├── models/              # 13 SQLAlchemy ORM table definitions
├── routers/             # 18 HTTP + WebSocket route files
├── services/            # 3 service helpers (HMS, Auth, Attendance)
├── utils/               # security.py (JWT, hashing, role guards)
├── schemas.py           # All Pydantic request/response models
├── database.py          # SQLAlchemy engine + session
├── config.py            # Reads environment variables
└── main.py              # App entry point, middleware, router registration
```

---

## 3. What Is Currently Implemented (and Working)

| Feature | Router File | Status |
|---|---|---|
| Register / Login | `auth.py` | ✅ Works |
| Create Course | `courses.py` | ✅ (but no auth guard — see Section 6) |
| List / Update Course | `courses.py` | ✅ (same issue) |
| Create Classroom/Batch | `classroom.py` | ✅ |
| Enroll Student (auto-ID + auto-password) | `enroll.py` | ✅ |
| Enroll Instructor (assign to batches) | `instructor_enroll.py` | ✅ |
| Create/Update Module & Chapters | `modules.py` | ✅ |
| Set Weekly Schedule | `schedule.py` | ✅ |
| Get Upcoming Schedule | `schedule.py` | ✅ |
| Start / End Live Session (100ms) | `sessions.py` | ✅ |
| Student Join / Leave Session | `sessions.py` | ✅ |
| Auto Attendance Calculation | `sessions.py` | ✅ (with known bugs — see Section 6) |
| Student Attendance Summary | `student_attendance.py` | ✅ |
| Instructor Attendance Report | `sessions.py` | ✅ |
| Create Test + Questions + Options | `tests.py` | ✅ |
| Student Start / Submit Test (auto-graded) | `tests.py` | ✅ |
| Instructor Test Detail View | `tests.py` | ✅ |
| Instructor Review Submission | `tests.py` | ✅ |
| Create Assignment + Upload Resources | `assignments.py` | ✅ |
| Student Submit Assignment (file upload) | `assignments.py` | ⚠️ KeyError bug (see §6) |
| Instructor Grade Assignment | `assignments.py` | ✅ |
| Batch Analytics Overview | `batch_analytics.py` | ✅ |
| Course Q&A (post, reply, pin, like, bookmark) | `qa.py` | ✅ |
| Group Chat (per batch) | `group_chat.py` | ✅ |
| Direct Messaging (DM) | `dm_chat.py` | ✅ |
| Real-time WebSocket (DM + Group + Q&A) | `ws_chat.py` | ✅ (single-server only) |
| Notifications (list, read, delete) | `notifications.py` | ✅ |
| User Profile / Avatar | `user_profiles.py` | ✅ |

---

## 4. What Needs To Be Built To Finish The Project

### 4.1 New APIs Required

#### A. Dashboard — Fix to Return Real Data
- `GET /dashboard/courses` — currently returns hardcoded static objects. Must query the logged-in student's enrolled courses with real lesson/assignment counts.
- `GET /classes/upcoming` — currently returns fake Jitsi mock data. Must query `CourseSchedule` for the student's enrolled batches.

#### B. Session Recordings
No recording feature exists at all. Required:
- **New Model:** `SessionRecording` — stores `session_id`, `recording_url`, `duration_seconds`, `created_at`
- **New APIs:**
  - `POST /sessions/{session_id}/recording` — instructor saves recording URL after class
  - `GET /sessions/{session_id}/recording` — student fetches recording for a past session
  - `GET /courses/{course_id}/recordings?batch_name=` — list all past recordings for a batch

#### C. Announcements Module
Referenced in the documentation but not implemented:
- **New Model:** `Announcement` — `course_id`, `batch_name`, `created_by`, `title`, `content`, `is_pinned`, `created_at`
- **New APIs:**
  - `POST /announcements/` — instructor creates announcement
  - `GET /announcements/?course_id=&batch_name=` — students + instructor view announcements
  - `PATCH /announcements/{id}/pin` — pin/unpin
  - `DELETE /announcements/{id}` — delete

#### D. 100ms Webhook Handler
The codebase uses 100ms for live video but has no webhook listener for it. Required to automate participant tracking server-side:
- **New API:** `POST /webhooks/100ms`
  - Verify the 100ms webhook signature (HMAC-SHA256)
  - Handle `peer.join` → call participant_join logic
  - Handle `peer.leave` → call participant_leave logic

#### E. Module/Chapter Progress Tracking
The `Enrollment` model has a `progress_percent` field but no API updates it:
- **New APIs:**
  - `POST /modules/{module_id}/chapters/{chapter_id}/complete` — student marks chapter done
  - Auto-recalculates `progress_percent` on enrollment
  - `GET /courses/{course_id}/progress` — student sees their progress per module

#### F. Resource File Management (Course Materials)
`GET /resources` currently returns a hardcoded PDF. Need real file management:
- **New Model:** `CourseResource` — `course_id`, `batch_name`, `uploaded_by`, `file_name`, `file_path`, `file_type`, `created_at`
- **New APIs:**
  - `POST /courses/{course_id}/resources` — instructor uploads resource file
  - `GET /courses/{course_id}/resources?batch_name=` — list resources
  - `DELETE /courses/{course_id}/resources/{resource_id}` — remove resource

#### G. Auth Hardening
- `POST /auth/change-password` — allow students/instructors to change their own password
- `GET /auth/me` — return current user profile from token

### 4.2 New Tables Required

| Table | Purpose |
|---|---|
| `session_recordings` | Stores 100ms recording URLs per session |
| `announcements` | Course/batch-level announcements from instructors |
| `course_resources` | Uploaded PDF/video/file materials per course batch |
| `chapter_progress` | Tracks which chapters each student has completed |

---

## 5. Dead Code — Files and Functions With No Real Use

These exist in the codebase but serve no functional purpose in the current system. They should either be completed or deleted to reduce confusion.

### 5.1 Entire Files That Are Stubs or Dead

| File | Why It's Dead |
|---|---|
| `app/routers/classes.py` | `GET /classes/upcoming` returns hardcoded Jitsi mock data. `POST /classes/create` returns `{"message": "Class created"}` — no DB write. `GET /classes/all-users` returns `[]`. Entire file is non-functional. |
| `app/routers/resources.py` | `GET /resources` returns a single hardcoded PDF object. Not connected to any database table. |
| `app/routers/webhooks.py` | Listens on `/webhooks/jitsi` — Jitsi is not used anywhere in the codebase. The system uses 100ms. This webhook is never called. |
| `app/routers/meet.py` | Legacy "classroom-based" meet endpoint from before 100ms was integrated. Uses `classroom_id` to generate a fake room name. Superseded entirely by `sessions.py`. |
| `app/routers/attendance.py` | Duplicates `POST /sessions/join` and `POST /sessions/leave` from `sessions.py` but **does not** start the background auto-attendance timer. Any client calling these endpoints will have students stuck in `pending` status forever. This router should be removed; all attendance entry should go through `sessions.py`. |

### 5.2 Dead Functions Inside Active Files

| File | Function | Why It's Dead |
|---|---|---|
| `app/services/attendance_service.py` | `finalize_attendance()` | Calculates attendance as a ratio of session duration. Never called from any active router. Its ratio-based logic (0.7 = present, 0.5 = late) also conflicts with the 30-minute threshold system used in `sessions.py`. |
| `app/routers/auth.py` | Line 68: `return {"access_token": token, "token_type": "bearer"}` | Dead code after the `login` function — unreachable because the real return is on line 56. `token` variable is also undefined here. |
| `app/routers/auth.py` | Line 40: `return {"id": user.id, "email": user.email, "role": user.role}` | Second unreachable return in `register` — identical to line 30 which returns first. |
| `app/routers/enroll.py` | Lines 155–162: second `if existing_user:` block | The code that prevents duplicate enrollment is unreachable. The `if existing_user: raise HTTPException` on line 151 always exits before reaching it. |

### 5.3 Tables With No Active Usage

| Table | Status |
|---|---|
| `assignments_module` | The `Assignment` model references a separate `AssignmentModule` model but assignments are already scoped by `course_id` + `batch_name`. This appears to be legacy schema drift. |
| `resources_module` | No model or router uses this table. It appears in the SQL dump but nothing reads or writes to it. |

---

## 6. Known Critical Bugs (Must Fix Before Launch)

| Bug | File | Line | Fix |
|---|---|---|---|
| `NameError: func` in auto-attendance task | `sessions.py` | 62 | Add `from sqlalchemy import func` at top of file |
| `NameError: HTTPException` in courses | `courses.py` | 76 | Add `from fastapi import HTTPException` |
| `KeyError: 'id'` on assignment upload | `assignments.py` | 617 | Change `current_user['id']` → `current_user['user_id']` |
| No auth on `POST /courses/create` | `courses.py` | 62 | Add `Depends(require_roles(["admin"]))` |
| No auth on `GET /sessions/session/{id}` | `sessions.py` | 402 | Add `Depends(require_roles(["instructor"]))` |
| Open admin registration | `auth.py` | 13 | Add auth check or restrict to admin-only creation |
| Hardcoded JWT fallback secret | `security.py` | 26 | Remove fallback; raise on missing env var |
| `ZeroDivisionError` in attendance finalize | `attendance_service.py` | 55 | Guard: `if total_minutes <= 0: return` |
| Enrollment dead code / multi-course block | `enroll.py` | 155 | Restructure to separate new-user vs existing-user flows |
| Background task lost on server restart | `sessions.py` | 256 | Migrate to DB-cron or task queue (ARQ/Celery) |

---

## 7. How Joining a Class and Attendance Tracking Works — End to End

This is the complete lifecycle of a live class session, from the instructor starting it to every student's attendance being finalized.

```
INSTRUCTOR                              SERVER                              STUDENT
    │                                      │                                    │
    │  POST /sessions/start                │                                    │
    │  ?course_id=1&batch_name=Batch-A     │                                    │
    │ ─────────────────────────────────── ▶│                                    │
    │                                      │  1. Calls 100ms API: create_room() │
    │                                      │  2. Gets back: room_id,            │
    │                                      │     host_url, guest_url            │
    │                                      │  3. Saves ClassSession to DB:      │
    │                                      │     status = "live"                │
    │                                      │     start_time = now               │
    │                                      │     host_url = <100ms host link>   │
    │                                      │     join_url = <100ms guest link>  │
    │  ◀ ─────────────────────────────────│                                    │
    │  { session_id, meet_link,            │                                    │
    │    guest_link, status: "live" }      │                                    │
    │                                      │                                    │
    │  Opens meet_link in browser          │                                    │
    │  (100ms host room)                   │                                    │
    │                                      │                                    │
    │                                      │   GET /sessions/active             │
    │                                      │   ?course_id=1&batch_name=Batch-A  │
    │                                      │ ◀ ─────────────────────────────── │
    │                                      │  1. Finds live ClassSession        │
    │                                      │  2. Appends student name to URL    │
    │                                      │  3. Returns guest meet_link        │
    │                                      │ ─────────────────────────────────▶ │
    │                                      │  { live: true, session_id: 5,      │
    │                                      │    meet_link: <100ms guest URL> }  │
    │                                      │                                    │
    │                                      │   POST /sessions/join              │
    │                                      │   ?course_id=1&batch_name=Batch-A  │
    │                                      │ ◀ ─────────────────────────────── │
    │                                      │  1. Confirms student is enrolled   │
    │                                      │  2. Checks no open record exists   │
    │                                      │  3. Creates SessionParticipant:    │
    │                                      │     join_time = now                │
    │                                      │     status = "pending"             │
    │                                      │  4. Starts background task:        │
    │                                      │     asyncio.create_task(           │
    │                                      │       auto_mark_attendance(pid))   │
    │                                      │     (sleeps 30 minutes)            │
    │                                      │ ─────────────────────────────────▶ │
    │                                      │  { status: "joined" }              │
    │                                      │                                    │
    │                                      │  [Student is in 100ms room]        │
    │                                      │                                    │
    │                       ◀────── 30 minutes pass ─────────────▶             │
    │                                      │                                    │
    │                    Background Task Wakes Up                               │
    │                                      │  Queries SessionParticipant by id  │
    │                                      │  Case A: leave_time == None        │
    │                                      │    → student still in class        │
    │                                      │    → calculate duration = now - join│
    │                                      │    → status = "present" ✅          │
    │                                      │  Case B: leave_time is set         │
    │                                      │    → check cumulative duration     │
    │                                      │    → if >= 30 min: "present" ✅    │
    │                                      │    → if < 30 min: "absent" ❌      │
    │                                      │  Case C: status already "present"  │
    │                                      │    → skip (no downgrade)           │
    │                                      │                                    │
    │                                      │   POST /sessions/leave             │
    │                                      │   ?session_id=5                    │
    │                                      │ ◀ ─────────────────────────────── │
    │                                      │  1. Finds open participant record  │
    │                                      │  2. Sets leave_time = now          │
    │                                      │  3. duration = leave - join        │
    │                                      │  4. Sums ALL segments for student  │
    │                                      │     (handles rejoin cases)         │
    │                                      │  5. If status == "pending":        │
    │                                      │     total >= 30 → "present" ✅     │
    │                                      │     total < 30  → "absent" ❌      │
    │                                      │ ─────────────────────────────────▶ │
    │                                      │  { duration_minutes, status }      │
    │                                      │                                    │
    │  POST /sessions/end?session_id=5     │                                    │
    │ ─────────────────────────────────── ▶│                                    │
    │                                      │  1. ClassSession.status = "ended"  │
    │                                      │  2. For each still-open record:    │
    │                                      │     leave_time = now               │
    │                                      │     recalculate duration           │
    │                                      │     resolve "pending" → present/   │
    │                                      │     absent based on threshold      │
    │                                      │  3. For enrolled students who      │
    │                                      │     never joined at all:           │
    │                                      │     Create record with             │
    │                                      │     status = "absent" ❌           │
    │  ◀ ─────────────────────────────────│                                    │
    │  { message: "Session ended" }        │                                    │
```

### Key Rules of the Attendance System

| Rule | Detail |
|---|---|
| **Threshold** | A student must be present for **≥ 30 minutes cumulative** to be marked `present` |
| **Cumulative tracking** | A student can join, leave, and rejoin. All segments are summed. |
| **3 resolution paths** | 1) Background task (30-min timer), 2) `/leave` API, 3) `/end` session |
| **No-show handling** | When instructor calls `/sessions/end`, all enrolled students who never joined get an `absent` record automatically |
| **Status values** | `pending` → `present` or `absent` (never stays pending after resolution) |

### Attendance Reading (After Class)

- **Student view:** `GET /students/me/attendance/details` — returns calendar grouped by date + per-course attendance stats
- **Instructor view:** `GET /sessions/session/{session_id}` — lists every participant's join/leave times and final status
- **Analytics:** `GET /batches/{course_id}/{batch_name}/overview` — returns average attendance rate (%) over last 30 days

---

## 8. Completion Checklist (Summary)

### Must Do Before Launch
- [ ] Fix 7 critical bugs listed in Section 6
- [ ] Delete dead router files: `classes.py`, `resources.py`, `webhooks.py`, `meet.py`, `attendance.py`
- [ ] Remove `Base.metadata.create_all` and set up Alembic migrations
- [ ] Add missing database indexes on FK columns
- [ ] Fix `GET /dashboard/courses` to query real enrolled courses

### Should Do for Full Feature Completeness
- [ ] Build Session Recordings module (model + 3 APIs)
- [ ] Build Announcements module (model + 4 APIs)
- [ ] Build Course Resources module (model + 3 APIs)
- [ ] Build Chapter Progress Tracking (model + 2 APIs)
- [ ] Add `GET /auth/me` and `POST /auth/change-password`
- [ ] Replace 100ms webhook stub with a real verified handler
- [ ] Fix N+1 query loops in analytics and test review endpoints

### Nice to Have
- [ ] Rate limiting on `/auth/login` and `/auth/register` (use `slowapi`)
- [ ] Redis Pub/Sub for WebSocket horizontal scaling
- [ ] Course completion certificates endpoint

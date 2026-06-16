# LMS Backend Project Documentation

This document explains the current backend structure, what was added, and how to run and test the API.

## Project Structure

```text
lms_backend/
+-- app/
|   +-- main.py                  # FastAPI app entry point and router registration
|   +-- database.py              # SQLAlchemy engine, Base, and DB session
|   +-- config.py                # Environment variable config
|   +-- schemas.py               # Shared Pydantic schemas
|   +-- models/                  # Database tables
|   |   +-- user.py
|   |   +-- tenant.py            # Added tenant table
|   |   +-- classroom.py
|   |   +-- course.py
|   |   +-- module.py
|   |   +-- assignment.py
|   |   +-- test.py
|   |   +-- attendance.py
|   |   +-- ...
|   +-- routers/                 # API routes shown in Swagger
|   |   +-- auth.py              # Login, register, instructor/student register
|   |   +-- tenants.py           # Added tenant APIs
|   |   +-- admin_dashboard.py
|   |   +-- instructor_dashboard.py
|   |   +-- student_dashboard.py
|   |   +-- assignments.py
|   |   +-- courses.py
|   |   +-- modules.py
|   |   +-- resources.py
|   |   +-- ...
|   +-- services/                # Business logic helpers
|   +-- utils/                   # Security and shared helpers
+-- uploads/                     # Uploaded files
+-- tests/                       # Test files
+-- .env                         # Local environment variables
+-- requirements.txt             # Python dependencies
+-- lms.db                       # Local SQLite database, do not commit
```

## What Was Added

### Tenant Support

Added a tenant model and tenant API routes.

New file:

```text
app/models/tenant.py
app/routers/tenants.py
```

Tenant fields:

```json
{
  "id": 1,
  "user_id": 1,
  "name": "COIREI",
  "branch": ""
}
```

Tenant APIs:

```text
GET    /tenants/
GET    /tenants/list
GET    /tenants/{tenant_id}
POST   /tenants/login
POST   /tenants/
PUT    /tenants/{tenant_id}
DELETE /tenants/{tenant_id}
```

`POST /tenants/` now works like create or update:

- If the user has no tenant, it creates one.
- If the user already has a tenant, it updates that tenant and returns `200 OK`.

Example body:

```json
{
  "user_id": 1,
  "name": "COIREI",
  "branch": ""
}
```

### Register API Tenant Creation

Updated:

```text
app/routers/auth.py
```

`POST /auth/register` now accepts `tenant_name`.

Example body:

```json
{
  "name": "Admin User",
  "email": "admin1@example.com",
  "password": "admin123",
  "role": "admin",
  "tenant_name": "COIREI",
  "tenant_branch": "Chennai"
}
```

Allowed roles:

```text
admin
instructor
student
```

Response includes tenant details:

```json
{
  "id": 1,
  "email": "admin1@example.com",
  "role": "admin",
  "tenant": {
    "id": 1,
    "user_id": 1,
    "name": "COIREI",
    "branch": "Chennai"
  }
}
```

### Root API Fix

Updated:

```text
app/main.py
```

Added root route:

```text
GET /
```

Expected response:

```json
{
  "status": "ok",
  "message": "LMS Backend API is running",
  "docs": "/docs"
}
```

This fixes `GET /` returning `404 Not Found`.

### Student API Additions

Updated:

```text
app/routers/student_dashboard.py
app/routers/courses.py
app/routers/resources.py
app/routers/assignments.py
```

Added or improved:

```text
Skipped question answer
Test end status
Upcoming schedule
Test analytics
Live now
Upcoming classes with topic and instructor name
Instructor name in student overview API
Resources
FAQs
Assignment completed, due, overdue counts
Course code in assignment details
Assignment submission file view and download APIs
```

Important student routes:

```text
GET /dashboard/student/live-now
GET /dashboard/student/upcoming-classes
GET /dashboard/student/upcoming-schedule
GET /dashboard/student/assignments/summary
GET /dashboard/student/test-analytics
GET /dashboard/student/faqs
GET /courses/{course_id}/student-overview
GET /resources/{resource_id}/view
GET /resources/{resource_id}/download
GET /assignments/submissions/{submission_id}/view
GET /assignments/submissions/{submission_id}/download
```

### Instructor API Additions

Updated:

```text
app/routers/instructor_dashboard.py
app/routers/instructor.py
app/routers/assignments.py
```

Added or improved:

```text
Instructor profile details
Total module count in a batch
Batch completion progress count
Upcoming schedule
Pending review
Recent activity inside batch
Schedule edit
Batch based student list
Particular student activity in instructor side profile
Course code and module name in assignment details
expected_answer in test review API
Announcements
Resources and FAQs
Assignment batch based course list
```

Important instructor routes:

```text
GET /instructor/
GET /instructor/profile/details
GET /instructor/upcoming-schedule
PUT /instructor/schedule/{schedule_id}
GET /instructor/pending-review
GET /instructor/batch/{classroom_id}/recent-activity
GET /instructor/students
GET /instructor/students/batch
GET /instructor/students/{student_id}/profile
GET /instructor/resources
GET /instructor/faqs
GET /instructor/announcements
POST /instructor/announcements
GET /instructor/assignment-courses
```

### Admin API Additions

Updated:

```text
app/routers/admin_dashboard.py
app/routers/modules.py
app/routers/courses.py
```

Added or improved:

```text
Daily attendance in dashboard
Enrollment growth in dashboard
Send announcement
Admin access for module/chapter details
Average attendance in course overview
Assignment completion in course overview
Instructor stats
Instructor profile correct date joined and phone number
Instructor session attendance
Edit instructor profile
Deactivate instructor
Student profile correct date joined
Edit student profile
Deactivate student
```

Important admin routes:

```text
GET  /dashboard/admin/daily-attendance
GET  /dashboard/admin/enrollment-growth
POST /dashboard/admin/announcements/send
GET  /dashboard/admin/instructors/stats
GET  /dashboard/admin/instructors/{instructor_id}
PUT  /dashboard/admin/instructors/{instructor_id}/profile
PUT  /dashboard/admin/instructors/{instructor_id}/deactivate
GET  /dashboard/admin/students/{id}
PUT  /dashboard/admin/students/{id}/profile
PUT  /dashboard/admin/students/{id}/deactivate
GET  /modules/{module_id}/chapters/{chapter_id}/details
```

## Environment Setup

Use this local `.env` file inside `lms_backend/`:

```env
DATABASE_URL=sqlite:///./lms.db
JWT_SECRET=local-dev-jwt-secret
```

The local SQLite database is:

```text
lms_backend/lms.db
```

Do not commit `lms.db`.

## How To Run

Open PowerShell and run:

```powershell
cd "B:\COIREI OFFICE\LMS\lms_backend"
.\.venv\Scripts\uvicorn.exe app.main:app --reload
```

Server URL:

```text
http://127.0.0.1:8000
```

Swagger URL:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
GET /
GET /health
```

## Swagger Testing Steps

### 1. Check Server

Open:

```text
http://127.0.0.1:8000/
```

Expected:

```json
{
  "status": "ok",
  "message": "LMS Backend API is running",
  "docs": "/docs"
}
```

### 2. Register User

Swagger route:

```text
POST /auth/register
```

Body:

```json
{
  "name": "Admin User",
  "email": "admin1@example.com",
  "password": "admin123",
  "role": "admin",
  "tenant_name": "COIREI",
  "tenant_branch": "Chennai"
}
```

### 3. Login

Swagger route:

```text
POST /auth/login
```

Body:

```json
{
  "email": "admin1@example.com",
  "password": "admin123"
}
```

Copy the `access_token`.

Login response also returns tenant details for the logged-in user:

```json
{
  "access_token": "token",
  "token_type": "bearer",
  "user_id": 1,
  "tenant_id": 1,
  "tenant_name": "COIREI",
  "branch": "Chennai",
  "user": {
    "id": 1,
    "name": "Admin User",
    "email": "admin1@example.com",
    "role": "admin",
    "tenant": {
      "id": 1,
      "user_id": 1,
      "name": "COIREI",
      "branch": "Chennai"
    }
  }
}
```

### 4. Authorize Swagger

In Swagger, click `Authorize` and paste:

```text
Bearer YOUR_ACCESS_TOKEN
```

### 5. List Tenants

Swagger route:

```text
GET /tenants/list
```

Example response:

```json
[
  {
    "id": 1,
    "user_id": 1,
    "name": "COIREI",
    "branch": ""
  }
]
```

Here `id` is the tenant id.

### 6. Get Tenant By ID

Swagger route:

```text
GET /tenants/{tenant_id}
```

Use:

```text
tenant_id = 1
```

Do not use `0`. Tenant IDs start from `1`.

### 7. Create Or Update Tenant

Swagger route:

```text
POST /tenants/
```

Body:

```json
{
  "user_id": 1,
  "name": "COIREI",
  "branch": ""
}
```

Expected result:

```text
200 OK
```

### 8. Tenant Login

Swagger route:

```text
POST /tenants/login
```

Body:

```json
{
  "email": "admin1@example.com",
  "password": "admin123"
}
```

Response:

```json
{
  "access_token": "token",
  "token_type": "bearer",
  "user_id": 1,
  "tenant_id": 1,
  "tenant_name": "COIREI",
  "branch": "Chennai"
}
```

This API is shown under the `Tenants` section in Swagger. Every login returns tenant details for the logged-in user.

## Common Errors

### No module named app

Reason: command was run from the wrong folder.

Fix:

```powershell
cd "B:\COIREI OFFICE\LMS\lms_backend"
.\.venv\Scripts\uvicorn.exe app.main:app --reload
```

### DATABASE_URL environment variable is required

Reason: `.env` missing or command was run from the wrong folder.

Fix:

Make sure this file exists:

```text
B:\COIREI OFFICE\LMS\lms_backend\.env
```

With:

```env
DATABASE_URL=sqlite:///./lms.db
JWT_SECRET=local-dev-jwt-secret
```

### GET / returns 404

Fixed now. Use:

```text
GET /
```

It should return `200 OK`.

### POST /auth/register returns 400

Possible reasons:

```text
Invalid role
Email already registered
```

Use role only as:

```text
admin
instructor
student
```

Use a new email each time.

### GET /tenants/{tenant_id} returns 404

Reason: wrong tenant id.

Fix:

Run:

```text
GET /tenants/list
```

Then use the `id` from that response.

## Git Commit Steps

This project has two Git sections in VS Code:

```text
LMS
lms_backend
```

First commit inside `lms_backend`.

PowerShell:

```powershell
cd "B:\COIREI OFFICE\LMS\lms_backend"
git add .gitignore app/main.py app/models/__init__.py app/models/tenant.py app/routers/auth.py app/routers/tenants.py app/routers/admin_dashboard.py app/routers/assignments.py app/routers/courses.py app/routers/instructor.py app/routers/instructor_dashboard.py app/routers/modules.py app/routers/resources.py app/routers/student_dashboard.py app/routers/tests.py PROJECT_RUN_DOCUMENTATION.md
git commit -m "Add tenant APIs and dashboard updates"
```

Then commit root repo:

```powershell
cd "B:\COIREI OFFICE\LMS"
git add lms_backend
git commit -m "Update backend"
```

Do not commit:

```text
lms.db
.venv/
.tmp/
```

## Verification Commands

Run these from `lms_backend/`:

```powershell
.\.venv\Scripts\python.exe -m py_compile app\routers\tenants.py
.\.venv\Scripts\python.exe -c "from app.main import app; print(len(app.openapi()['paths']))"
```

If both commands run without error, the backend import and Swagger schema are working.

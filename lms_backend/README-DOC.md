# LMS Backend Documentation

## Project Overview

This project is a scalable Learning Management System (LMS) backend built using:

* Python
* FastAPI
* PostgreSQL
* SQLAlchemy
* JWT Authentication
* Jitsi Meet Integration

The system supports:

* Admin management
* Instructor management
* Student management
* Course management
* Batch/classroom management
* Session management
* Attendance tracking
* Real-time live classes
* Instructor-course-batch assignment

---

# Tech Stack

| Layer             | Technology       |
| ----------------- | ---------------- |
| Backend Framework | FastAPI          |
| Database          | PostgreSQL       |
| ORM               | SQLAlchemy       |
| Authentication    | JWT              |
| Password Hashing  | Passlib + bcrypt |
| Live Classes      | Jitsi Meet       |
| ASGI Server       | Uvicorn          |
| Language          | Python 3.13      |

---

# Project Structure

```bash
app/
│
├── main.py
├── config.py
├── database.py
│
├── models/
│   ├── user.py
│   ├── course.py
│   ├── classroom.py
│   ├── enrollment.py
│   ├── instructor_enrollment.py
│   ├── attendance.py
│   ├── session.py
│   └── announcements.py
│
├── routers/
│   ├── auth.py
│   ├── students.py
│   ├── instructors.py
│   ├── instructor_enroll.py
│   ├── courses.py
│   ├── classrooms.py
│   ├── sessions.py
│   ├── attendance.py
│   ├── dashboard.py
│   └── announcements.py
│
├── services/
│   └── jitsi_service.py
│
├── utils/
│   └── security.py
│
└── schemas/
```

---

# Authentication System

## JWT Authentication

Authentication is handled using JWT tokens.

### Login Flow

1. User logs in using email and password
2. Password verified using bcrypt
3. JWT token generated
4. Token returned to frontend
5. Frontend stores token
6. Protected routes use Bearer token authentication

---

# Roles

The project currently supports:

| Role       | Permissions                                       |
| ---------- | ------------------------------------------------- |
| admin      | Full system access                                |
| instructor | Can manage assigned classes and sessions          |
| student    | Can attend sessions and access learning resources |

---

# Database Architecture

## users

Stores:

* Admins
* Students
* Instructors

### Fields

| Field         | Description                |
| ------------- | -------------------------- |
| id            | Primary key                |
| name          | Full name                  |
| email         | User email                 |
| password_hash | Hashed password            |
| role          | User role                  |
| student_id    | Student or instructor code |

---

## courses

Stores all courses.

### Example

* Python
* AI
* Machine Learning
* Data Science

---

## classrooms

Represents batches inside a course.

### Example

| Course | Batch   |
| ------ | ------- |
| Python | Batch-A |
| Python | Batch-B |

---

## enrollments

Maps students to:

* Course
* Batch

---

## instructor_enrollments

Maps instructors to:

* Course
* Batch

This table controls:

* Which instructor can start a session
* Which instructor can end a session
* Which classes appear in instructor dashboard

---

## class_sessions

Stores live session history.

### Fields

| Field      | Description    |
| ---------- | -------------- |
| id         | Session ID     |
| course_id  | Related course |
| batch_name | Batch          |
| host_url   | Instructor URL |
| join_url   | Student URL    |
| status     | live / ended   |
| start_time | Session start  |
| end_time   | Session end    |

---

## session_participants

Tracks attendance.

### Tracks

* Join time
* Leave time
* Duration
* Attendance status

---

# Session System

## Live Session Flow

### Instructor

1. Instructor starts session
2. System verifies instructor assignment
3. Jitsi room generated
4. Session stored in DB
5. Session marked live

### Student

1. Student checks active session
2. Student joins
3. Attendance record created
4. Background attendance tracking begins
5. Leave time tracked
6. Attendance calculated automatically

---

# Attendance System

## Attendance Logic

### Present

Student cumulative duration >= threshold

### Absent

Student leaves before threshold
OR
Never joins session

---

# Current Major Features Completed

## Authentication

* Login
* JWT generation
* Role protection
* Password hashing

## Instructor Enrollment

* Auto-generated instructor IDs
* Auto-generated passwords
* Multi batch assignment
* Duplicate protection
* Password reset
* Instructor listing

## Sessions

* Start session
* Join session
* Leave session
* End session
* Attendance auto-calculation
* Jitsi integration
* Instructor authorization

## Attendance

* Join tracking
* Leave tracking
* Duration tracking
* Automatic attendance marking
* No-show detection

---

# Major Bugs Fixed

## 1. bcrypt / passlib compatibility

### Error

```python
AttributeError: module 'bcrypt' has no attribute '__about__'
```

### Fix

Installed compatible bcrypt version.

---

## 2. SQLAlchemy + Python 3.13 Typing Error

### Error

```python
AssertionError: SQLCoreOperations directly inherits TypingOnly
```

### Fix

Updated SQLAlchemy compatibility.

---

## 3. Instructor Session Security Bug

### Problem

Any instructor could start/end any class.

### Fix

Added instructor assignment validation.

---

## 4. Duplicate Batch Assignment Bug

### Problem

Instructor could not be assigned multiple batches.

### Fix

Improved instructor enrollment validation.

---

## 5. Duplicate Session Constraint Bug

### Problem

```python
duplicate key value violates unique constraint uq_course_batch
```

### Cause

Only one session allowed per course+batch.

### Fix

Session history architecture updated.

---

# Security Architecture

## Password Security

Uses:

* bcrypt hashing
* Passlib CryptContext

Passwords are never stored in plain text.

---

## Route Protection

Protected using:

```python
Depends(get_current_user)
```

Role authorization handled using:

```python
require_roles([...])
```

---

# API Modules

## Auth APIs

| Endpoint         | Purpose    |
| ---------------- | ---------- |
| POST /auth/login | User login |

---

## Instructor Enrollment APIs

| Endpoint             | Purpose                   |
| -------------------- | ------------------------- |
| GET /courses         | List courses              |
| GET /batches         | List batches              |
| GET /generate-id     | Preview instructor ID     |
| POST /instructor     | Create instructor         |
| POST /reset-password | Reset instructor password |
| GET /list            | List instructors          |

---

## Session APIs

| Endpoint                   | Purpose           |
| -------------------------- | ----------------- |
| POST /sessions/start       | Start class       |
| GET /sessions/active       | Active session    |
| POST /sessions/join        | Join class        |
| POST /sessions/leave       | Leave class       |
| POST /sessions/end         | End class         |
| GET /sessions/session/{id} | Attendance report |

---

# Planned APIs

## Dashboard APIs

* GET /dashboard/courses
* GET /classes/upcoming

## Announcement Module

* Create announcement
* List announcements
* Batch announcements
* Course announcements

## Analytics

* Attendance analytics
* Student performance
* Instructor statistics

## Recording Support

Planned:

* Jitsi recording integration
* Cloud storage support
* Playback system

---

# Jitsi Integration

Currently using:

```python
https://meet.jit.si/
```

Current implementation:

* Lightweight
* Free
* No server hosting required
* Fast setup

Future plan:

* Dedicated subdomain
* JWT secured rooms
* Recording support
* API integration

---

# Environment Variables

Create a `.env` file.

```env
DATABASE_URL=postgresql://username:password@localhost/lms_db
JWT_SECRET=supersecretkey
JWT_ALGORITHM=HS256
JITSI_DOMAIN=https://meet.jit.si
```

---

# Running the Project

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Start PostgreSQL

```bash
brew services start postgresql
```

---

## Run FastAPI Server

```bash
uvicorn app.main:app --reload
```

---

# Testing APIs

Open:

```bash
http://127.0.0.1:8000/docs
```

Swagger UI is enabled.

---

# Development Strategy

Current development style:

1. Build APIs quickly
2. Fix architecture bugs early
3. Stabilize backend
4. Integrate frontend later
5. Add production optimizations after core system stabilizes

---

# Important Architecture Decisions

## Why Jitsi?

Chosen because:

* Free
* Lightweight
* No heavy server costs
* Fast integration
* Works well during MVP stage

---

## Why FastAPI?

Chosen because:

* Extremely fast
* Async support
* Excellent Swagger docs
* Easy JWT integration
* Great for scalable APIs

---

# Current Backend Status

## Stable

* Authentication
* Instructor enrollment
* Sessions
* Attendance tracking
* Jitsi meetings
* Authorization system

## In Progress

* Dashboard APIs
* Announcements
* Session history improvements
* Recording support

---

# Git Setup

## Create New Repo

```bash
git init
```

---

## Add Remote

```bash
git remote add origin YOUR_GITHUB_REPO_URL
```

---

## Push Code

```bash
git add .
git commit -m "Initial LMS backend commit"
git branch -M main
git push -u origin main
```

---

# Suggested .gitignore

```gitignore
venv/
__pycache__/
.env
.pytest_cache/
*.pyc
.DS_Store
.idea/
.vscode/
```

---

# Future Scaling Ideas

## Short-Term

* Frontend integration
* Better dashboard APIs
* Notification system
* Announcements

## Mid-Term

* Recording system
* File uploads
* Assignment system
* Exams

## Long-Term

* AI analytics
* AI attendance insights
* Auto summaries
* LMS chatbot
* Course recommendation engine

---

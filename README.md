# LMS Backend ⚡

A robust, feature-rich Learning Management System (LMS) backend built with **FastAPI**, **SQLAlchemy**, and **100ms** integration for live video conferencing.

## 🚀 Features

### 🔐 User Management & Auth
- **JWT Authentication**: Secure login and session management.
- **Role-Based Access Control (RBAC)**: Distinct permissions for **Admin**, **Instructor**, and **Student**.
- **Profile Management**: CRUD operations for user profiles.

### 📚 Course & Content Management
- **Course Catalog**: Create and manage courses with ease.
- **Module System**: Organize courses into logical modules.
- **Learning Resources**: Upload documents, videos, and assignments.
- **Assignments**: Student submission and instructor grading workflow.

### 📹 Virtual Classroom (100ms)
- **Live Sessions**: Start and join live classes powered by **100ms SDK**.
- **Automated Attendance**: Intelligent tracking that calculates presence based on duration.
- **Host/Guest Controls**: Differentiated links for instructors (hosts) and students (guests).

### 📊 Dashboard & Stats
- **Role-Specific Dashboards**: Summary stats for enrollments, active sessions, and upcoming classes.
- **Attendance Reports**: Detailed logs for students and instructors.

### 📝 Enrollment & Scheduling
- **Batch Management**: Organize students into batches for optimized scheduling.
- **Class Schedules**: Full calendar support for recurring and one-off classes.

---

## 🛠️ Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Database**: [PostgreSQL](https://www.postgresql.org/) with [SQLAlchemy ORM](https://www.sqlalchemy.org/)
- **Asynchronous Tasks**: [asyncio](https://docs.python.org/3/library/asyncio.html)
- **Video Infrastructure**: [100ms](https://www.100ms.live/)
- **Authentication**: JWT (python-jose), Passlib (bcrypt)
- **Validation**: [Pydantic v2](https://docs.pydantic.dev/latest/)

---

## 🏗️ Project Structure

```text
├── app/
│   ├── models/       # SQLAlchemy Database models
│   ├── routers/      # API Endpoints (FastAPI)
│   ├── services/     # Business logic & External integrations (100ms, JWT)
│   ├── utils/        # Shared helpers (Security, Timezone)
│   ├── database.py   # DB Connection & Session config
│   ├── main.py       # Application entry point
│   └── schemas.py    # Pydantic models for request/response
├── migrate_*.py      # DB Migration scripts
├── seed_db.py        # Demo data generator
├── cleanup_db.py     # Database maintenance scripts
├── requirements.txt  # Python dependencies
└── .env              # Environment configuration
```

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.10+
- PostgreSQL (Local or Cloud)
- 100ms Account (for live classes)

### 1. Clone & Install
```bash
git clone <your-repo-url>
cd lms_backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Variables
Create a `.env` file in the root directory:
```env
DATABASE_URL=postgresql://user:password@localhost/lms_db
JWT_SECRET=your_super_secret_jwt_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# 100ms Credentials
HMS_ACCESS_KEY=your_access_key
HMS_SECRET=your_secret_key
HMS_TEMPLATE_ID=your_template_id
```

### 3. Initialize Database
```bash
python seed_db.py
```

### 4. Run the Server
```bash
uvicorn app.main:app --reload
```
API Documentation will be available at: `http://localhost:8000/docs`

---

## 📜 Available Scripts

- `seed_db.py`: Populates the database with initial admin users and sample courses.
- `cleanup_db.py`: Clears all tables in the database (Use with caution!).
- `selective_cleanup.py`: Selectively removes sessions or enrollments.
- `migrate_add_host_url.py`: Example migration script for updating schema.

---

## 🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License
MIT License

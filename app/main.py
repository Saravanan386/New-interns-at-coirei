from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
# Consolidated Models (Including registration_profile from new version)
from app.models import (
    user, classroom as classroom_model, session, attendance as attendance_model, 
    schedule as schedule_model, module, test as test_model, enrollment, 
    assignment as assignment_model, chat as chat_model, notification as notification_model, 
    instructor_enrollment as instructor_enrollment_model, dm_chat as dm_chat_model, 
    group_chat as group_chat_model, registration_profile as registration_profile_model
)
from app.models.module import Module, Chapter
from app.models.chapter_resources import ChapterResource
from app.routers import (
    auth,
    meet,
    webhooks,
    attendance,
    classroom,
    # Dashboards from both versions
    admin_dashboard,
    student_dashboard,
    instructor_dashboard,
    chapter_resourses,
    dashboard,
    classes,
    class_scores, # From New
    assignments,
    resources,
    sessions,
    courses,
    student, # From New
    student_attendance,
    enroll,
    instructor_enroll,
    schedule,
    modules,
    tests,
    batch_analytics,
    chat,
    notifications,
    qa,
    dm_chat,
    group_chat,
    chat_uploads,
    ws_chat,
    user_profiles,
    instructor, # From New
)

app = FastAPI(
    title="LMS Backend",
    version="0.1.0",
    description="LMS API with Jitsi video conferencing",
)


@app.get("/health")
def health_check():
    return {"status": "ok"}

# Merged allow_origins to include all URLs from both versions
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        # "https://maya-ohonogramis-dayton.ngrok-free.dev",
        # "https://lms-lime-chi.vercel.app",
        # "https://admin-lms-seven.vercel.app", 
        "https://lms-iota-ten-60.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auto-create tables

# Routers - Carefully merged to prevent duplicates
app.include_router(auth.router)
app.include_router(meet.router)
app.include_router(webhooks.router)
app.include_router(attendance.router)
app.include_router(classroom.router)
app.include_router(dashboard.router)
app.include_router(admin_dashboard.router)      # Re-added
app.include_router(student_dashboard.router)    # Re-added
app.include_router(instructor_dashboard.router) # Re-added
app.include_router(classes.router)
app.include_router(class_scores.router)         # From New
app.include_router(assignments.router)
app.include_router(resources.router)
app.include_router(chapter_resourses.router)


app.include_router(sessions.router)
app.include_router(courses.router)
app.include_router(student.router)              # From New
app.include_router(student_attendance.router)
app.include_router(enroll.router)
app.include_router(instructor_enroll.router)
app.include_router(schedule.router)
app.include_router(modules.router)
app.include_router(tests.router)
app.include_router(batch_analytics.router)
app.include_router(chat.router)
app.include_router(notifications.router)
app.include_router(qa.router)
app.include_router(dm_chat.router)
app.include_router(group_chat.router)
app.include_router(chat_uploads.router)
app.include_router(ws_chat.router)
app.include_router(user_profiles.router)
app.include_router(instructor.router)           # From New

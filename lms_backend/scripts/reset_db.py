from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

tables = [
    "session_participants",
    "class_sessions",
    "instructor_enrollments",
    "enrollments",
    "chapters",
    "modules",
    "classrooms",
    "courses",
    "users"
]

try:
    for table in tables:
        db.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE"))

    db.commit()

    print("Database reset successful")

except Exception as e:
    db.rollback()
    print("Reset failed:", e)

finally:
    db.close()
import sys
import os

sys.path.append(os.getcwd())

from app.database import SessionLocal, engine
from sqlalchemy import text

def selective_cleanup():
    db = SessionLocal()
    try:
        print("Cleaning operational data (using TRUNCATE CASCADE where possible)...")
        # We use raw SQL to handle cascades properly
        tables_to_truncate = [
            "session_participants",
            "class_sessions",
            "enrollments",
            "chapters",
            "modules",
            "course_schedules",
            "courses" # Assuming we want to clear courses too
        ]
        
        for table in tables_to_truncate:
            print(f"Truncating {table}...")
            db.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE"))
        
        print("Deleting users except kuberan@coirei.com and instructor@coirei.com...")
        preserved_emails = "('kuberan@coirei.com', 'instructor@coirei.com')"
        
        sql = f"DELETE FROM users WHERE email NOT IN {preserved_emails}"
        result = db.execute(text(sql))
        
        db.commit()
        print(f"Cleanup complete. Deleted {result.rowcount} users.")
        
        # Verify remaining
        remaining = db.execute(text("SELECT email, role FROM users")).fetchall()
        print("Remaining users:")
        for email, role in remaining:
            print(f"- {email} ({role})")
            
    except Exception as e:
        db.rollback()
        print(f"Error during cleanup: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    selective_cleanup()

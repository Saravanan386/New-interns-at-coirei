"""
One-time migration: adds host_url column to class_sessions table.
Run once: python migrate_add_host_url.py
"""
from sqlalchemy import text
from app.database import engine

with engine.connect() as conn:
    conn.execute(text(
        "ALTER TABLE class_sessions ADD COLUMN IF NOT EXISTS host_url VARCHAR;"
    ))
    conn.commit()
    print("✅ host_url column added to class_sessions table.")


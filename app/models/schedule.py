# app/models/schedule.py

from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from app.database import Base


class CourseSchedule(Base):
    """
    Stores the recurring weekly timetable for a course+batch.
    One row per scheduled day (e.g. Monday class, Wednesday class, etc.)
    """
    __tablename__ = "course_schedules"

    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    batch_name = Column(String, nullable=False)

    # Day of week as lowercase string: monday, tuesday, ..., sunday
    day_of_week = Column(String, nullable=False)

    # "class" or "doubt_clearing"
    session_type = Column(String, nullable=False, default="class")

    # 24-hour time strings e.g. "09:00", "10:00"
    start_time = Column(String, nullable=False)
    end_time = Column(String, nullable=False)

    instructor_name = Column(String, nullable=True)

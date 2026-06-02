# app/models/schedule.py

from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from app.database import Base

from sqlalchemy import Date


class CourseSchedule(Base):

    __tablename__ = "course_schedules"

    id = Column(Integer, primary_key=True)

    course_id = Column(Integer, ForeignKey("courses.id"))
    batch_name = Column(String)

    day_of_week = Column(String)

    session_type = Column(String)

    start_time = Column(String)
    end_time = Column(String)

    start_date = Column(Date)

    instructor_name = Column(String)

    topic = Column(String)
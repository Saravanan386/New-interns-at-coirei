# app/models/classroom.py

from sqlalchemy import Column, Integer, String, ForeignKey
from app.database import Base


class Classroom(Base):
    __tablename__ = "classrooms"

    id = Column(Integer, primary_key=True)

    course_id = Column(
        Integer,
        ForeignKey("courses.id"),
        nullable=False
    )

    batch_name = Column(
        String,
        nullable=False
    )

    room_name = Column(
        String,
        nullable=False
    )

    instructor_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True
    )

    instructor_name = Column(
        String,
        nullable=True
    )

    # NEW FIELDS
    batch_code = Column(
        String,
        nullable=True
    )

    schedule_type = Column(
        String,
        nullable=True
    )

    start_month = Column(
        String,
        nullable=True
    )
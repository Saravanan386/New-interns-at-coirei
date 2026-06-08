# app/models/classroom.py

from sqlalchemy import Column, Integer, String, ForeignKey
from app.database import Base
# app/models/classroom.py
from sqlalchemy.orm import relationship

class Classroom(Base):
    __tablename__ = "classrooms"

    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    batch_name = Column(String)
    room_name = Column(String)
    instructor_id = Column(Integer, ForeignKey("users.id"))
    instructor_name = Column(String)
    batch_code = Column(String)
    schedule_type = Column(String)
    start_month = Column(String)
    class_days = Column(String)
    start_time = Column(String)
    end_time = Column(String)

    course = relationship("Course")
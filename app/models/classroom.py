from sqlalchemy import Column, Integer, String, ForeignKey
from app.database import Base

class Classroom(Base):
    __tablename__ = "classrooms"

    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    course_name = Column(String)
    batch_name = Column(String)
    room_name = Column(String)


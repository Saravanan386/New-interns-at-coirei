from sqlalchemy import Column, Integer, String, Text
from app.database import Base


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True)

    course_code = Column(String, unique=True)

    name = Column(String, nullable=False)

    description = Column(Text)

    duration_months = Column(Integer)

    total_lessons = Column(Integer)
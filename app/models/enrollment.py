from sqlalchemy import Column, Integer, String, ForeignKey
from app.database import Base


class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    classroom_id = Column(
        Integer,
        ForeignKey("classrooms.id"),
        nullable=False
    )

    progress_percent = Column(Integer, default=0)

    status = Column(
        String,
        default="ongoing"
    )
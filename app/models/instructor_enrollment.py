from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from app.database import Base


class InstructorEnrollment(Base):

    __tablename__ = "instructor_enrollments"

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

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "classroom_id",
            name="uq_instructor_classroom"
        ),
    )
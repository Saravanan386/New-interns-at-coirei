from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from app.database import Base


class InstructorEnrollment(Base):
    """Maps an instructor (user) to a specific course + batch."""
    __tablename__ = "instructor_enrollments"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    batch_name = Column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "course_id", "batch_name",
                         name="uq_instructor_course_batch"),
    )

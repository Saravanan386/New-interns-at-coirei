# app/models/assignment.py

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Assignment(Base):
    """
    Created by an instructor for a specific course + batch + module.
    Once created, it is visible to all enrolled students in that batch.
    """
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    batch_name = Column(String, nullable=False)
    
    # Updated: Points properly to the modules table
    module_id = Column(Integer, ForeignKey("modules.id"), nullable=False)          

    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    objective = Column(Text, nullable=True)

    expected_outcome = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=True)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    course = relationship("Course")
    instructor = relationship("User")
    
    # Added: This allows 'a.module.title' to work cleanly!
    module = relationship("Module") 
    
    resources = relationship(
        "AssignmentResource",
        back_populates="assignment",
        cascade="all, delete-orphan"
    )
    submissions = relationship(
        "AssignmentSubmission",
        back_populates="assignment",
        cascade="all, delete-orphan"
    )
    @property
    def course_name(self) -> str:
        """Dynamically fetches the course name through the course relationship."""
        return self.course.name if self.course else ""

    @property
    def status(self) -> str:
        """
        Provides a default base status string for the assignment object 
        to satisfy the schema requirement on creation.
        """
        return "in progress"
# ... (Keep AssignmentResource and AssignmentSubmission classes exactly as they were)

class AssignmentResource(Base):
    """
    File / link attached to an assignment by the instructor.
    Files are stored on disk; only the path/url is persisted here.
    """
    __tablename__ = "assignment_resources"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False)
    file_name = Column(String, nullable=False)        # original filename
    file_path = Column(String, nullable=False)        # path on disk / served URL
    file_type = Column(String, nullable=True)         # mime type
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    assignment = relationship("Assignment", back_populates="resources")
    

class AssignmentSubmission(Base):
    """
    A student's submission for an assignment.
    """
    __tablename__ = "assignment_submissions"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False)
    student_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    submission_text = Column(Text, nullable=True)
    file_path = Column(String, nullable=True)         # uploaded file
    file_name = Column(String, nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    # 'pending' | 'submitted' | 'graded'
    status = Column(String, default="pending")
    grade = Column(String, nullable=True)             # e.g. "A", "85/100"
    feedback = Column(Text, nullable=True)

    assignment = relationship("Assignment", back_populates="submissions")
    student = relationship("User")

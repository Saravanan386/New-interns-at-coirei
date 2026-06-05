# app/models/test.py

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
from sqlalchemy import Text

class Test(Base):
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    batch_name = Column(String, nullable=False)
    module_id = Column(
        Integer,
        ForeignKey("modules.id"),
        nullable=False
    )

    module = relationship("Module")

    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )
    # Relationships
    course = relationship("Course")
    questions = relationship("Question", back_populates="test", cascade="all, delete-orphan")
    submissions = relationship("TestSubmission", back_populates="test", cascade="all, delete-orphan")

class Question(Base):
    __tablename__ = "test_questions"

    id = Column(Integer, primary_key=True, index=True)

    test_id = Column(
        Integer,
        ForeignKey("tests.id"),
        nullable=False
    )

    text = Column(Text, nullable=False)

    # mcq | checkbox | short_answer | long_answer
    question_type = Column(
        String,
        nullable=False,
        default="mcq"
    )

    marks = Column(
        Float,
        default=1
    )

    # instructor answer for text questions
    expected_answer = Column(
        Text,
        nullable=True
    )

    test = relationship("Test", back_populates="questions")

    options = relationship(
        "Option",
        back_populates="question",
        cascade="all, delete-orphan"
    )

class Option(Base):
    __tablename__ = "question_options"

    id = Column(Integer, primary_key=True)

    question_id = Column(
        Integer,
        ForeignKey("test_questions.id"),
        nullable=False
    )

    text = Column(String, nullable=False)

    is_correct = Column(
        Boolean,
        default=False
    )

    question = relationship(
        "Question",
        back_populates="options"
    )

# ── New submission tracking ──────────────────────────────────────────────────

class TestSubmission(Base):
    """One row per student per test attempt."""
    __tablename__ = "test_submissions"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)
    student_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    started_at = Column(DateTime, nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    # score as percentage (0–100), null until submitted
    obtained_marks = Column(Float, default=0)

    total_marks = Column(Float, default=0)

    score_percentage = Column(Float)
    # True = passed, False = failed, None = not submitted yet
    is_passed = Column(Boolean, nullable=True)
    # 'in_progress' | 'submitted' | 'not_attended'
    status = Column(String, default="in_progress")

    test = relationship("Test", back_populates="submissions")
    student = relationship("User")
    answers = relationship("StudentAnswer", back_populates="submission", cascade="all, delete-orphan")
    __table_args__ = (
        UniqueConstraint(
            "test_id",
            "student_user_id",
            name="uq_test_student"
        ),
    )

class StudentAnswer(Base):
    __tablename__ = "student_answers"

    id = Column(Integer, primary_key=True)

    submission_id = Column(
        Integer,
        ForeignKey("test_submissions.id"),
        nullable=False
    )

    question_id = Column(
        Integer,
        ForeignKey("test_questions.id"),
        nullable=False
    )

    # MCQ
    selected_option_id = Column(
        Integer,
        ForeignKey("question_options.id"),
        nullable=True
    )

    # Checkbox
    selected_option_ids = Column(
        String,
        nullable=True
    )

    # Short / Long answer
    text_answer = Column(
        Text,
        nullable=True
    )

    awarded_marks = Column(
        Float,
        default=0
    )

    max_marks = Column(
        Float,
        default=0
    )

    submission = relationship(
        "TestSubmission",
        back_populates="answers"
    )
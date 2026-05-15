from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional

from app.database import get_db
from app.utils.security import get_current_user
from app.models.test import Test, Question, Option, TestSubmission, StudentAnswer
from app.models.user import User
from app.models.enrollment import Enrollment
from app.schemas import (
    TestCreate, TestResponse, TestUpdate,
    TestSubmitRequest,
    TestDetailResponse, StudentRowResponse,
    SubmissionReviewResponse, AnswerReviewItem,
)

router = APIRouter(prefix="/tests", tags=["Tests"])

PASS_THRESHOLD = 60.0  # percentage needed to pass


# ── Helpers ──────────────────────────────────────────────────────────────────

def check_instructor(current_user: dict):
    if current_user.get("role") != "instructor":
        raise HTTPException(status_code=403, detail="Not authorized. Instructor only.")


def check_student(current_user: dict):
    if current_user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Not authorized. Student only.")


def fmt_time(dt: Optional[datetime]) -> str:
    """Format datetime to '10:00 am' style, or '---' if None."""
    if dt is None:
        return "---"
    return dt.strftime("%-I:%M %p").lower() if hasattr(dt, "strftime") else "---"


def fmt_date(dt: Optional[datetime]) -> Optional[str]:
    """Format datetime to 'Jan 21, 2026' style."""
    if dt is None:
        return None
    return dt.strftime("%b %d, %Y")


def duration_minutes(start: Optional[datetime], end: Optional[datetime]) -> Optional[int]:
    if start and end:
        delta = end - start
        return int(delta.total_seconds() // 60)
    return None


# ── Existing: Create Test ────────────────────────────────────────────────────

@router.post("/", response_model=TestResponse)
def create_test(
    test: TestCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_instructor(current_user)

    new_test = Test(
        title=test.title,
        course_id=test.course_id,
        batch_name=test.batch_name,
        module_name=test.module_name,
        description=test.description,
        start_time=test.start_time,
        end_time=test.end_time
    )
    db.add(new_test)
    db.flush()

    if test.questions:
        for q in test.questions:
            new_question = Question(test_id=new_test.id, text=q.text)
            db.add(new_question)
            db.flush()
            for o in q.options:
                new_option = Option(question_id=new_question.id, text=o.text, is_correct=o.is_correct)
                db.add(new_option)

    db.commit()
    db.refresh(new_test)
    return new_test


# ── Existing: Update Test ────────────────────────────────────────────────────

@router.put("/{test_id}", response_model=TestResponse)
def update_test(
    test_id: int,
    test_data: TestUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_instructor(current_user)

    db_test = db.query(Test).filter(Test.id == test_id).first()
    if not db_test:
        raise HTTPException(status_code=404, detail="Test not found")

    if test_data.description is not None:
        db_test.description = test_data.description
    if test_data.start_time is not None:
        db_test.start_time = test_data.start_time
    if test_data.end_time is not None:
        db_test.end_time = test_data.end_time

    if test_data.questions is not None:
        db.query(Question).filter(Question.test_id == test_id).delete()
        for q in test_data.questions:
            new_question = Question(test_id=test_id, text=q.text)
            db.add(new_question)
            db.flush()
            for o in q.options:
                new_option = Option(question_id=new_question.id, text=o.text, is_correct=o.is_correct)
                db.add(new_option)

    db.commit()
    db.refresh(db_test)
    return db_test


# ── Student: Start Test ──────────────────────────────────────────────────────

@router.post("/{test_id}/start")
def start_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Student calls this when they begin the test.
    Creates a TestSubmission record with status='in_progress'.
    If the student already started, returns the existing submission id.
    """
    check_student(current_user)

    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    student_user_id = current_user["user_id"]

    # Idempotent: don't create duplicate submissions
    existing = db.query(TestSubmission).filter(
        TestSubmission.test_id == test_id,
        TestSubmission.student_user_id == student_user_id
    ).first()

    if existing:
        return {
            "message": "Test already started",
            "submission_id": existing.id,
            "status": existing.status,
            "started_at": existing.started_at
        }

    submission = TestSubmission(
        test_id=test_id,
        student_user_id=student_user_id,
        started_at=datetime.utcnow(),
        status="in_progress"
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    return {
        "message": "Test started successfully",
        "submission_id": submission.id,
        "started_at": submission.started_at
    }


# ── Student: Submit Test ─────────────────────────────────────────────────────

@router.post("/{test_id}/submit")
def submit_test(
    test_id: int,
    payload: TestSubmitRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Student submits answers. Auto-grades the test.
    Score = (correct answers / total questions) * 100.
    Pass if score >= PASS_THRESHOLD (60%).
    """
    check_student(current_user)

    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    student_user_id = current_user["user_id"]

    submission = db.query(TestSubmission).filter(
        TestSubmission.test_id == test_id,
        TestSubmission.student_user_id == student_user_id
    ).first()

    if not submission:
        raise HTTPException(
            status_code=400,
            detail="You must call POST /tests/{test_id}/start before submitting."
        )

    if submission.status == "submitted":
        raise HTTPException(status_code=400, detail="Test already submitted.")

    # Delete any prior partial answers before saving final answers
    db.query(StudentAnswer).filter(
        StudentAnswer.submission_id == submission.id
    ).delete()

    # Save answers
    total_questions = len(test.questions)
    correct_count = 0

    for answer in payload.answers:
        # Validate question belongs to test
        question = db.query(Question).filter(
            Question.id == answer.question_id,
            Question.test_id == test_id
        ).first()
        if not question:
            continue  # skip invalid question ids

        selected_opt = None
        if answer.selected_option_id:
            selected_opt = db.query(Option).filter(
                Option.id == answer.selected_option_id,
                Option.question_id == answer.question_id
            ).first()
            if selected_opt and selected_opt.is_correct:
                correct_count += 1

        student_answer = StudentAnswer(
            submission_id=submission.id,
            question_id=answer.question_id,
            selected_option_id=answer.selected_option_id if selected_opt else None
        )
        db.add(student_answer)

    # Calculate score
    score = (correct_count / total_questions * 100) if total_questions > 0 else 0.0
    is_passed = score >= PASS_THRESHOLD

    submission.submitted_at = datetime.utcnow()
    submission.score = round(score, 2)
    submission.is_passed = is_passed
    submission.status = "submitted"

    db.commit()
    db.refresh(submission)

    return {
        "message": "Test submitted successfully",
        "submission_id": submission.id,
        "score": submission.score,
        "is_passed": submission.is_passed,
        "correct": correct_count,
        "total": total_questions
    }


# ── Instructor: Real-Time Test Details ──────────────────────────────────────

@router.get("/{test_id}/details", response_model=TestDetailResponse)
def get_test_details(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Returns the full instructor view for a test:
    - Test metadata (title, module, date, duration)
    - Summary: total enrolled, submitted, passed, failed
    - Per-student table rows (status, mark, start/end time)

    Students who haven't started appear with status='not_attended'.
    """
    check_instructor(current_user)

    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    # All students enrolled in the same course + batch as this test
    enrollments = db.query(Enrollment).filter(
        Enrollment.course_id == test.course_id,
        Enrollment.batch_name == test.batch_name
    ).all()

    # Build a lookup: student_user_id → TestSubmission
    submissions = db.query(TestSubmission).filter(
        TestSubmission.test_id == test_id
    ).all()
    sub_map = {s.student_user_id: s for s in submissions}

    total_enrolled = len(enrollments)
    total_submitted = sum(1 for s in submissions if s.status == "submitted")
    total_passed = sum(1 for s in submissions if s.is_passed is True)
    total_failed = sum(1 for s in submissions if s.is_passed is False)

    student_rows = []
    for idx, enrollment in enumerate(enrollments, start=1):
        student = db.query(User).filter(User.id == enrollment.user_id).first()
        if not student:
            continue

        sub = sub_map.get(enrollment.user_id)

        if sub and sub.status == "submitted":
            status_str = "submitted"
            start_str = fmt_time(sub.started_at)
            end_str = fmt_time(sub.submitted_at)
            mark = sub.score
            sub_id = sub.id
        elif sub and sub.status == "in_progress":
            status_str = "in_progress"
            start_str = fmt_time(sub.started_at)
            end_str = "---"
            mark = None
            sub_id = sub.id
        else:
            status_str = "not_attended"
            start_str = "---"
            end_str = "---"
            mark = None
            sub_id = None

        student_rows.append(StudentRowResponse(
            sno=idx,
            student_id=student.student_id or str(student.id),
            student_name=student.name,
            start_time=start_str,
            end_time=end_str,
            status=status_str,
            mark=mark,
            submission_id=sub_id
        ))

    return TestDetailResponse(
        test_id=test.id,
        title=test.title,
        module_name=test.module_name,
        date=fmt_date(test.start_time),
        duration_minutes=duration_minutes(test.start_time, test.end_time),
        start_time=fmt_time(test.start_time),
        end_time=fmt_time(test.end_time),
        total_enrolled=total_enrolled,
        total_submitted=total_submitted,
        total_passed=total_passed,
        total_failed=total_failed,
        students=student_rows
    )


# ── Instructor: Review One Student's Submission ──────────────────────────────

@router.get("/{test_id}/submission/{submission_id}", response_model=SubmissionReviewResponse)
def review_submission(
    test_id: int,
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Full answer-by-answer review of a student's submission.
    Shows the question text, selected answer, whether it was correct,
    and what the correct answer was.
    Used when the instructor clicks the "Review" button.
    """
    check_instructor(current_user)

    submission = db.query(TestSubmission).filter(
        TestSubmission.id == submission_id,
        TestSubmission.test_id == test_id
    ).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    student = db.query(User).filter(User.id == submission.student_user_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Build answer review items
    review_items = []
    questions = db.query(Question).filter(Question.test_id == test_id).all()

    student_answers = {a.question_id: a for a in submission.answers}

    for question in questions:
        # Find the correct option for this question
        correct_option = next(
            (o for o in question.options if o.is_correct), None
        )
        sa = student_answers.get(question.id)

        selected_opt = None
        if sa and sa.selected_option_id:
            selected_opt = db.query(Option).filter(Option.id == sa.selected_option_id).first()

        is_correct = None
        if sa and selected_opt:
            is_correct = selected_opt.is_correct

        review_items.append(AnswerReviewItem(
            question_id=question.id,
            question_text=question.text,
            selected_option_id=sa.selected_option_id if sa else None,
            selected_option_text=selected_opt.text if selected_opt else None,
            is_correct=is_correct,
            correct_option_text=correct_option.text if correct_option else None
        ))

    return SubmissionReviewResponse(
        submission_id=submission.id,
        test_id=test_id,
        student_id=student.student_id or str(student.id),
        student_name=student.name,
        started_at=submission.started_at,
        submitted_at=submission.submitted_at,
        score=submission.score,
        is_passed=submission.is_passed,
        status=submission.status,
        answers=review_items
    )

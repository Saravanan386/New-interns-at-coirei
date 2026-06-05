from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional

import re
from app.services.test_evaluator import evaluate_question
from app.database import get_db
from app.utils.security import get_current_user
from app.models.test import Test, Question, Option, TestSubmission, StudentAnswer
from app.models.user import User
from app.models.enrollment import Enrollment
from app.models.classroom import Classroom
from app.schemas import (
    TestCreate, TestResponse, TestUpdate,
    TestSubmitRequest,
    TestDetailResponse, StudentRowResponse,
    SubmissionReviewResponse, AnswerReviewItem,TestSubmitResponse,SubmissionReviewResponse
)
from rapidfuzz import fuzz
from app.models.module import Module

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

    module = db.query(Module).filter(
        Module.id == test.module_id,
        Module.course_id == test.course_id
    ).first()

    if not module:
        raise HTTPException(
            status_code=404,
            detail="Module not found"
        )

    new_test = Test(
        title=test.title,
        description=test.description,
        course_id=test.course_id,
        module_id=test.module_id,
        batch_name=test.batch_name,
        start_time=test.start_time,
        end_time=test.end_time,
        created_by=current_user["user_id"]
    )

    db.add(new_test)
    db.flush()

    for q in test.questions:

        question = Question(
            test_id=new_test.id,
            text=q.text,
            question_type=q.question_type,
            marks=q.marks,
            expected_answer=q.expected_answer
        )

        db.add(question)
        db.flush()

        if q.question_type in ["mcq", "checkbox"]:

            for option in q.options:
                db.add(
                    Option(
                        question_id=question.id,
                        text=option.text,
                        is_correct=option.is_correct
                    )
                )

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
        question_ids = [
            question_id
            for (question_id,) in db.query(Question.id)
            .filter(Question.test_id == test_id)
            .all()
        ]
        if question_ids:
            db.query(Option).filter(Option.question_id.in_(question_ids)).delete()
            db.query(Question).filter(Question.id.in_(question_ids)).delete()
            db.flush()

        for q in test_data.questions:
            new_question = Question(
                test_id=test_id,
                text=q.text,
                question_type=q.question_type,
                marks=q.marks,
                expected_answer=q.expected_answer
            )
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
        started_at=datetime.now(timezone.utc),
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
    enrollments = db.query(Enrollment).join(
        Classroom,
        Classroom.id == Enrollment.classroom_id
    ).filter(
        Classroom.course_id == test.course_id,
        Classroom.batch_name == test.batch_name,
        Enrollment.status == "ongoing"
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
            mark = sub.score_percentage
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
        module_name=test.module.title if test.module else None,
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

@router.get(
    "/{test_id}/submission/{submission_id}",
    response_model=SubmissionReviewResponse
)
def review_submission(
    test_id: int,
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_instructor(current_user)

    submission = db.query(TestSubmission).filter(
        TestSubmission.id == submission_id,
        TestSubmission.test_id == test_id
    ).first()

    if not submission:
        raise HTTPException(
            status_code=404,
            detail="Submission not found"
        )

    student = db.query(User).filter(
        User.id == submission.student_user_id
    ).first()

    review_items = []

    questions = db.query(Question).filter(
        Question.test_id == test_id
    ).all()

    answer_map = {
        a.question_id: a
        for a in submission.answers
    }

    for question in questions:

        sa = answer_map.get(question.id)

        student_answer = None

        if sa:

            if question.question_type == "mcq":

                if sa.selected_option_id:

                    option = db.query(Option).filter(
                        Option.id == sa.selected_option_id
                    ).first()

                    student_answer = (
                        option.text
                        if option
                        else None
                    )

            elif question.question_type == "checkbox":

                student_answer = (
                    sa.selected_option_ids
                )

            else:

                student_answer = sa.text_answer

        review_items.append(
            AnswerReviewItem(
                question_id=question.id,
                question_text=question.text,
                question_type=question.question_type,
                student_answer=student_answer,
                expected_answer=question.expected_answer,
                awarded_marks=sa.awarded_marks if sa else 0,
                max_marks=question.marks,
                feedback=None
            )
        )

    return SubmissionReviewResponse(
        submission_id=submission.id,
        test_id=test_id,

        student_id=student.student_id or str(student.id),
        student_name=student.name,

        started_at=submission.started_at,
        submitted_at=submission.submitted_at,

        obtained_marks=submission.obtained_marks,
        total_marks=submission.total_marks,
        percentage=submission.score_percentage,

        is_passed=submission.is_passed,
        status=submission.status,

        answers=review_items
    )

@router.post(
    "/{test_id}/submit",
    response_model=TestSubmitResponse
)
def submit_test(
    test_id: int,
    payload: TestSubmitRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_student(current_user)

    test = db.query(Test).filter(
        Test.id == test_id
    ).first()

    if not test:
        raise HTTPException(
            status_code=404,
            detail="Test not found"
        )

    submission = db.query(TestSubmission).filter(
        TestSubmission.test_id == test_id,
        TestSubmission.student_user_id == current_user["user_id"]
    ).first()

    if not submission:
        raise HTTPException(
            status_code=400,
            detail="Start test first"
        )

    if submission.status == "submitted":
        raise HTTPException(
            status_code=400,
            detail="Test already submitted"
        )

    db.query(StudentAnswer).filter(
        StudentAnswer.submission_id == submission.id
    ).delete()

    total_marks = 0
    obtained_marks = 0

    for answer in payload.answers:

        question = db.query(Question).filter(
            Question.id == answer.question_id,
            Question.test_id == test_id
        ).first()

        if not question:
            continue

        total_marks += question.marks

        awarded_marks = evaluate_question(
            db,
            question,
            answer
        )

        obtained_marks += awarded_marks

        db.add(
            StudentAnswer(
                submission_id=submission.id,
                question_id=question.id,
                selected_option_id=answer.selected_option_id,
                selected_option_ids=",".join(
                    map(
                        str,
                        answer.selected_option_ids or []
                    )
                ),
                text_answer=answer.text_answer,
                awarded_marks=awarded_marks,
                max_marks=question.marks
            )
        )

    percentage = 0

    if total_marks > 0:
        percentage = (
            obtained_marks /
            total_marks
        ) * 100

    submission.obtained_marks = round(
        obtained_marks,
        2
    )

    submission.total_marks = round(
        total_marks,
        2
    )

    submission.score_percentage = round(
        percentage,
        2
    )

    submission.is_passed = (
        percentage >= PASS_THRESHOLD
    )

    submission.status = "submitted"

    submission.submitted_at = datetime.now(
        timezone.utc
    )

    db.commit()
    db.refresh(submission)

    return TestSubmitResponse(
        submission_id=submission.id,
        obtained_marks=submission.obtained_marks,
        total_marks=submission.total_marks,
        percentage=submission.score_percentage,
        is_passed=submission.is_passed
    )


@router.get("/student")
def get_student_tests(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_student(current_user)

    submissions = (
        db.query(TestSubmission)
        .filter(
            TestSubmission.student_user_id ==
            current_user["user_id"]
        )
        .all()
    )

    result = []

    for sub in submissions:

        test = sub.test

        result.append({
            "test_id": test.id,
            "title": test.title,
            "module": test.module.title if test.module else None,
            "status": sub.status,
            "obtained_marks": sub.obtained_marks,
            "total_marks": sub.total_marks,
            "percentage": sub.score_percentage,
            "is_passed": sub.is_passed,
            "submitted_at": sub.submitted_at
        })

    return result

@router.get("/student/{test_id}/result")
def student_result(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_student(current_user)

    submission = (
        db.query(TestSubmission)
        .filter(
            TestSubmission.test_id == test_id,
            TestSubmission.student_user_id ==
            current_user["user_id"]
        )
        .first()
    )

    if not submission:
        raise HTTPException(
            status_code=404,
            detail="Result not found"
        )

    answers = []

    for ans in submission.answers:

        question = (
            db.query(Question)
            .filter(
                Question.id == ans.question_id
            )
            .first()
        )

        student_answer = None
        correct_answer = None

        if question.question_type == "mcq":

            selected = (
                db.query(Option)
                .filter(
                    Option.id ==
                    ans.selected_option_id
                )
                .first()
            )

            correct = (
                db.query(Option)
                .filter(
                    Option.question_id ==
                    question.id,
                    Option.is_correct == True
                )
                .first()
            )

            student_answer = (
                selected.text
                if selected else None
            )

            correct_answer = (
                correct.text
                if correct else None
            )

        else:

            student_answer = ans.text_answer
            correct_answer = question.expected_answer

        answers.append({
            "question_id": question.id,
            "question": question.text,
            "student_answer": student_answer,
            "correct_answer": correct_answer,
            "awarded_marks": ans.awarded_marks,
            "max_marks": ans.max_marks
        })

    return {
        "test_id": test_id,
        "title": submission.test.title,
        "obtained_marks": submission.obtained_marks,
        "total_marks": submission.total_marks,
        "percentage": submission.score_percentage,
        "answers": answers
    }

@router.get("/student/performance")
def student_performance(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_student(current_user)

    submissions = (
        db.query(TestSubmission)
        .filter(
            TestSubmission.student_user_id ==
            current_user["user_id"],
            TestSubmission.status == "submitted"
        )
        .all()
    )

    if not submissions:
        return {
            "total_tests": 0
        }

    scores = [
        s.score_percentage
        for s in submissions
    ]

    return {
        "total_tests": len(submissions),
        "passed": len(
            [s for s in submissions if s.is_passed]
        ),
        "failed": len(
            [s for s in submissions if not s.is_passed]
        ),
        "average_score": round(
            sum(scores) / len(scores),
            2
        ),
        "highest_score": max(scores),
        "lowest_score": min(scores)
    }


@router.get("/instructor")
def instructor_tests(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_instructor(current_user)

    tests = (
        db.query(Test)
        .filter(
            Test.created_by ==
            current_user["user_id"]
        )
        .all()
    )

    result = []

    for test in tests:

        submissions = test.submissions

        avg = 0

        if submissions:

            avg = round(
                sum(
                    s.score_percentage or 0
                    for s in submissions
                ) / len(submissions),
                2
            )

        result.append({
            "test_id": test.id,
            "title": test.title,
            "students": len(submissions),
            "average_score": avg,
            "passed": len(
                [
                    s for s in submissions
                    if s.is_passed
                ]
            ),
            "failed": len(
                [
                    s for s in submissions
                    if s.is_passed is False
                ]
            )
        })

    return result

@router.get("/instructor/{test_id}/analytics")
def test_analytics(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_instructor(current_user)

    submissions = (
        db.query(TestSubmission)
        .filter(
            TestSubmission.test_id ==
            test_id,
            TestSubmission.status ==
            "submitted"
        )
        .all()
    )

    if not submissions:
        return {}

    scores = [
        s.score_percentage
        for s in submissions
    ]

    return {
        "test_id": test_id,
        "average_score": round(
            sum(scores) / len(scores),
            2
        ),
        "highest_score": max(scores),
        "lowest_score": min(scores),
        "pass_rate": round(
            (
                len(
                    [
                        s
                        for s in submissions
                        if s.is_passed
                    ]
                )
                /
                len(submissions)
            ) * 100,
            2
        )
    }

@router.get("/instructor/{test_id}/question-analysis")
def question_analysis(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_instructor(current_user)

    questions = (
        db.query(Question)
        .filter(
            Question.test_id == test_id
        )
        .all()
    )

    result = []

    for question in questions:

        answers = (
            db.query(StudentAnswer)
            .filter(
                StudentAnswer.question_id ==
                question.id
            )
            .all()
        )

        attempted = len(answers)

        correct = len([
            a
            for a in answers
            if a.awarded_marks >= question.marks
        ])

        success_rate = 0

        if attempted:
            success_rate = round(
                (correct / attempted) * 100,
                2
            )

        result.append({
            "question_id": question.id,
            "question": question.text,
            "attempted": attempted,
            "correct": correct,
            "incorrect": attempted - correct,
            "success_rate": success_rate
        })

    return result
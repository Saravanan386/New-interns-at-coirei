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
from app.models.course import Course

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
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional, List
 
from app.models.module      import Module, Chapter
from app.models.chapter_resources import ChapterResource
from app.models.assignment  import Assignment, AssignmentResource, AssignmentSubmission
from app.models.test        import (
    Test, Question, Option,
    TestSubmission, StudentAnswer
)

from collections import Counter
import statistics
 
def check_student(current_user: dict):
    if current_user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Student access only")
 
 
def check_instructor(current_user: dict):
    if current_user.get("role") != "instructor":
        raise HTTPException(status_code=403, detail="Instructor access only")
 
 
def _fmt_dt(dt: Optional[datetime]) -> Optional[str]:
    if not dt:
        return None
    return dt.strftime("%Y-%m-%d %I:%M %p")
 
 
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


@router.get("/instructor/dashboard")
def instructor_test_dashboard(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_instructor(current_user)

    tests = (
        db.query(Test)
        .filter(Test.created_by == current_user["user_id"])
        .all()
    )

    result = []

    for test in tests:

        submissions = test.submissions

        enrolled = (
            db.query(Enrollment)
            .join(
                Classroom,
                Classroom.id == Enrollment.classroom_id
            )
            .filter(
                Classroom.course_id == test.course_id,
                Classroom.batch_name == test.batch_name,
                Enrollment.status == "ongoing"
            )
            .count()
        )

        submitted = len([
            s for s in submissions
            if s.status == "submitted"
        ])

        avg_score = 0

        if submissions:
            avg_score = round(
                sum(
                    s.score_percentage or 0
                    for s in submissions
                ) / len(submissions),
                2
            )

        result.append({

            "test_id": test.id,

            "title": test.title,

            "description": test.description,

            "course_id": test.course_id,

            "course_name":
                test.course.name
                if test.course else None,

            "module_id":
                test.module_id,

            "module_name":
                test.module.title
                if test.module else None,

            "batch_name":
                test.batch_name,

            "start_time":
                test.start_time,

            "end_time":
                test.end_time,

            "total_questions":
                len(test.questions),

            "total_enrolled":
                enrolled,

            "total_submitted":
                submitted,

            "pending":
                enrolled - submitted,

            "average_score":
                avg_score,

            "passed":
                len([
                    s for s in submissions
                    if s.is_passed
                ]),

            "failed":
                len([
                    s for s in submissions
                    if s.is_passed is False
                ]),

            "created_at":
                test.created_at
        })

    return result



@router.get("/legacy/instructor/{test_id}/analytics", include_in_schema=False)
def legacy_test_analytics(
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


@router.get("/instructor/{test_id}/overview")
def test_overview(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_instructor(current_user)

    test = (
        db.query(Test)
        .filter(Test.id == test_id)
        .first()
    )

    if not test:
        raise HTTPException(
            status_code=404,
            detail="Test not found"
        )

    enrollments = (
        db.query(Enrollment)
        .join(
            Classroom,
            Classroom.id == Enrollment.classroom_id
        )
        .filter(
            Classroom.course_id == test.course_id,
            Classroom.batch_name == test.batch_name,
            Enrollment.status == "ongoing"
        )
        .all()
    )

    submissions = (
        db.query(TestSubmission)
        .filter(
            TestSubmission.test_id == test.id,
            TestSubmission.status == "submitted"
        )
        .all()
    )

    scores = [
        s.score_percentage
        for s in submissions
        if s.score_percentage is not None
    ]

    return {

        "test_id": test.id,
        "title": test.title,
        "description": test.description,

        "course": {
            "id": test.course.id if test.course else None,
            "name": test.course.name if test.course else None
        },

        "module": {
            "id": test.module.id if test.module else None,
            "name": test.module.title if test.module else None
        },

        "batch_name": test.batch_name,

        "start_time": test.start_time,
        "end_time": test.end_time,

        "total_questions": len(test.questions),

        "total_students": len(enrollments),

        "submitted_students": len(submissions),

        "pending_students":
            len(enrollments) - len(submissions),

        "passed_students": len([
            s for s in submissions
            if s.is_passed
        ]),

        "failed_students": len([
            s for s in submissions
            if s.is_passed is False
        ]),

        "average_score":
            round(sum(scores) / len(scores), 2)
            if scores else 0,

        "highest_score":
            max(scores)
            if scores else 0,

        "lowest_score":
            min(scores)
            if scores else 0,

        "pass_rate":
            round(
                (
                    len([
                        s
                        for s in submissions
                        if s.is_passed
                    ])
                    /
                    len(submissions)
                ) * 100,
                2
            ) if submissions else 0
    }

@router.get("/instructor/{test_id}/students")
def test_students(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_instructor(current_user)

    test = (
        db.query(Test)
        .filter(Test.id == test_id)
        .first()
    )

    if not test:
        raise HTTPException(
            status_code=404,
            detail="Test not found"
        )

    enrollments = (
        db.query(Enrollment)
        .join(
            Classroom,
            Classroom.id == Enrollment.classroom_id
        )
        .filter(
            Classroom.course_id == test.course_id,
            Classroom.batch_name == test.batch_name,
            Enrollment.status == "ongoing"
        )
        .all()
    )

    submissions = (
        db.query(TestSubmission)
        .filter(
            TestSubmission.test_id == test.id
        )
        .all()
    )

    submission_map = {
        s.student_user_id: s
        for s in submissions
    }

    result = []

    for enrollment in enrollments:

        student = (
            db.query(User)
            .filter(
                User.id == enrollment.user_id
            )
            .first()
        )

        if not student:
            continue

        submission = submission_map.get(student.id)

        duration = None

        if (
            submission
            and submission.started_at
            and submission.submitted_at
        ):
            duration = int(
                (
                    submission.submitted_at
                    - submission.started_at
                ).total_seconds() / 60
            )

        result.append({

            "student_user_id": student.id,

            "student_id":
                student.student_id,

            "student_name":
                student.name,

            "email":
                student.email,

            "status":
                submission.status
                if submission
                else "not_attempted",

            "started_at":
                submission.started_at
                if submission
                else None,

            "submitted_at":
                submission.submitted_at
                if submission
                else None,

            "duration_minutes":
                duration,

            "obtained_marks":
                submission.obtained_marks
                if submission
                else None,

            "total_marks":
                submission.total_marks
                if submission
                else None,

            "percentage":
                submission.score_percentage
                if submission
                else None,

            "is_passed":
                submission.is_passed
                if submission
                else None
        })

    return result





@router.get("/instructor/all-tests-metadata")
def get_instructor_tests_metadata(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Fetch all tests created by the instructor with comprehensive relational information:
    - Test ID & Title
    - Course ID & Name
    - Module ID & Name
    - Classroom ID & Batch Name
    - Creator (User ID & Name)
    """
    # 1. Verify that the user is an instructor
    check_instructor(current_user)

    # 2. Query tests created by this instructor
    tests = (
        db.query(Test)
        .filter(Test.created_by == current_user["user_id"])
        .all()
    )

    result = []

    for test in tests:
        # Find the specific classroom tied to this test via course and batch mapping
        classroom = (
            db.query(Classroom)
            .filter(
                Classroom.course_id == test.course_id,
                Classroom.batch_name == test.batch_name
            )
            .first()
        )

        # Safely extract instructor details if needed
        instructor_user = db.query(User).filter(User.id == test.created_by).first()

        result.append({
            # Test Core Info
            "test_id": test.id,
            "test_title": test.title,
            "test_description": test.description,
            
            # Course Mapping
            "course_id": test.course_id,
            "course_name": test.course.name if test.course else None,
            
            # Module Mapping
            "module_id": test.module_id,
            "module_name": test.module.title if test.module else None,
            
            # Classroom / Batch Mapping
            "classroom_id": classroom.id if classroom else None,
            "batch_name": test.batch_name,
            
            # User / Instructor Mapping
            "user_id": test.created_by,
            "instructor_name": instructor_user.name if instructor_user else None,
            
            # Metadata Timestamps
            "start_time": test.start_time,
            "end_time": test.end_time,
            "created_at": test.created_at
        })

    return result

 
# ── shared helpers ────────────────────────────────────────────────────────────

 
# ─────────────────────────────────────────────────────────────────────────────
#  ROUTER 1 – Tests  (prefix="/tests")
# ─────────────────────────────────────────────────────────────────────────────
 

# ── 1. Student: full result with answers ─────────────────────────────────────
 
@router.get("/student/{test_id}/result")
def student_test_result(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Returns every question with:
    - what the student answered
    - the correct answer
    - marks awarded vs max marks
    - overall score / pass status
    """
    check_student(current_user)
    user_id = current_user["user_id"]
 
    submission = db.query(TestSubmission).filter(
        TestSubmission.test_id          == test_id,
        TestSubmission.student_user_id  == user_id
    ).first()
 
    if not submission:
        raise HTTPException(status_code=404, detail="No submission found for this test")
 
    test   = db.query(Test).filter(Test.id == test_id).first()
    module = db.query(Module).filter(Module.id == test.module_id).first() if test else None
    course = db.query(Course).filter(Course.id == test.course_id).first() if test else None
 
    # Build answer lookup: question_id → StudentAnswer
    answer_map = {a.question_id: a for a in submission.answers}
 
    questions_data = []
    for question in db.query(Question).filter(Question.test_id == test_id).all():
 
        sa = answer_map.get(question.id)
 
        # ── resolve student's answer as human-readable text ──────
        student_answer_text  = None
        student_answer_id    = None
 
        if sa:
            if question.question_type == "mcq" and sa.selected_option_id:
                opt = db.query(Option).filter(Option.id == sa.selected_option_id).first()
                student_answer_text = opt.text if opt else None
                student_answer_id   = sa.selected_option_id
 
            elif question.question_type == "checkbox" and sa.selected_option_ids:
                ids = [
                    int(i) for i in sa.selected_option_ids.split(",")
                    if i.strip().isdigit()
                ]
                opts = db.query(Option).filter(Option.id.in_(ids)).all()
                student_answer_text = ", ".join(o.text for o in opts)
                student_answer_id   = sa.selected_option_ids
 
            else:
                student_answer_text = sa.text_answer
 
        # ── resolve correct answer ────────────────────────────────
        correct_answer_text = None
        correct_option_ids  = []
 
        if question.question_type in ("mcq", "checkbox"):
            correct_opts = db.query(Option).filter(
                Option.question_id == question.id,
                Option.is_correct  == True
            ).all()
            correct_answer_text = ", ".join(o.text for o in correct_opts)
            correct_option_ids  = [o.id for o in correct_opts]
        else:
            correct_answer_text = question.expected_answer
 
        # ── is this answer correct? ───────────────────────────────
        is_correct = bool(sa and sa.awarded_marks and sa.awarded_marks >= question.marks)
 
        # ── all options (for MCQ/checkbox display) ────────────────
        all_options = []
        if question.question_type in ("mcq", "checkbox"):
            for opt in db.query(Option).filter(Option.question_id == question.id).all():
                all_options.append({
                    "option_id":  opt.id,
                    "text":       opt.text,
                    "is_correct": opt.is_correct,
                })
 
        questions_data.append({
            "question_id":          question.id,
            "question_text":        question.text,
            "question_type":        question.question_type,
            "max_marks":            question.marks,
            "awarded_marks":        sa.awarded_marks if sa else 0,
            "is_correct":           is_correct,
 
            # What the student picked / wrote
            "student_answer":       student_answer_text,
            "student_answer_id":    student_answer_id,
 
            # Ground truth
            "correct_answer":       correct_answer_text,
            "correct_option_ids":   correct_option_ids,
 
            # Full option list so frontend can highlight
            "options":              all_options,
        })
 
    return {
        "test_id":          test_id,
        "title":            test.title if test else None,
        "description":      test.description if test else None,
        "course_name":      course.name if course else None,
        "module_name":      module.title if module else None,
 
        "submission_id":    submission.id,
        "status":           submission.status,
        "started_at":       _fmt_dt(submission.started_at),
        "submitted_at":     _fmt_dt(submission.submitted_at),
 
        "obtained_marks":   submission.obtained_marks,
        "total_marks":      submission.total_marks,
        "score_percentage": submission.score_percentage,
        "is_passed":        submission.is_passed,
 
        "total_questions":  len(questions_data),
        "correct_count":    sum(1 for q in questions_data if q["is_correct"]),
        "wrong_count":      sum(1 for q in questions_data if not q["is_correct"]),
 
        "questions":        questions_data,
    }
 
 
# ── 2. Student: available tests (with obtainable_marks) ──────────────────────
 
@router.get("/student/available")
def student_available_tests(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    All tests for the student's enrolled batches.
    Includes obtainable_marks (sum of all question marks) and
    submission status/score if already attempted.
    """
    check_student(current_user)
    user_id = current_user["user_id"]
 
    enrollments = (
        db.query(Enrollment)
        .join(Classroom, Classroom.id == Enrollment.classroom_id)
        .filter(
            Enrollment.user_id   == user_id,
            Enrollment.status    == "ongoing"
        ).all()
    )
 
    results = []
    seen    = set()
 
    for en in enrollments:
        classroom = db.query(Classroom).filter(Classroom.id == en.classroom_id).first()
        if not classroom:
            continue
 
        tests = db.query(Test).filter(
            Test.course_id  == classroom.course_id,
            Test.batch_name == classroom.batch_name
        ).all()
 
        for test in tests:
            if test.id in seen:
                continue
            seen.add(test.id)
 
            course = db.query(Course).filter(Course.id == test.course_id).first()
            module = db.query(Module).filter(Module.id == test.module_id).first()
 
            # Sum all question marks to get obtainable_marks
            questions = db.query(Question).filter(Question.test_id == test.id).all()
            obtainable_marks = sum(q.marks for q in questions)
 
            submission = db.query(TestSubmission).filter(
                TestSubmission.test_id          == test.id,
                TestSubmission.student_user_id  == user_id
            ).first()
 
            if not submission:
                status = "not_started"
            elif submission.status == "in_progress":
                status = "in_progress"
            else:
                status = "completed"
 
            results.append({
                "test_id":           test.id,
                "title":             test.title,
                "description":       test.description,
 
                "course": {
                    "id":   course.id   if course else None,
                    "name": course.name if course else None,
                    "code": course.course_code if course else None,
                },
                "module": {
                    "id":   module.id    if module else None,
                    "name": module.title if module else None,
                },
 
                "batch_name":        test.batch_name,
                "start_time":        _fmt_dt(test.start_time),
                "end_time":          _fmt_dt(test.end_time),
 
                "total_questions":   len(questions),
                "obtainable_marks":  obtainable_marks,   # ← NEW
 
                "status":            status,
                "submission_id":     submission.id               if submission else None,
                "obtained_marks":    submission.obtained_marks   if submission else None,
                "total_marks":       submission.total_marks      if submission else None,
                "score_percentage":  submission.score_percentage if submission else None,
                "is_passed":         submission.is_passed        if submission else None,
                "submitted_at":      _fmt_dt(submission.submitted_at) if submission else None,
            })
 
    return results
 


@router.get("/instructor/{test_id}/analytics")
def test_analytics(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Returns:
    - Overall stats (avg, highest, lowest, pass rate)
    - Score distribution in 10-point buckets (0-10, 11-20 … 91-100)
    - Per-question analysis (attempt rate, success rate, most common wrong answer)
    """
    check_instructor(current_user)
 
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
 
    submissions = db.query(TestSubmission).filter(
        TestSubmission.test_id == test_id,
        TestSubmission.status  == "submitted"
    ).all()
 
    if not submissions:
        return {
            "test_id":    test_id,
            "title":      test.title,
            "message":    "No submissions yet",
            "total_submitted": 0,
        }
 
    scores = [s.score_percentage for s in submissions if s.score_percentage is not None]
 
    # ── score distribution ────────────────────────────────────────
    buckets = {f"{i}-{i+9}": 0 for i in range(0, 100, 10)}
    buckets["100"] = 0
    for sc in scores:
        if sc == 100:
            buckets["100"] += 1
        else:
            bucket_key = f"{int(sc // 10) * 10}-{int(sc // 10) * 10 + 9}"
            if bucket_key in buckets:
                buckets[bucket_key] += 1
 
    score_distribution = [
        {"range": k, "count": v}
        for k, v in buckets.items()
    ]
 
    # ── per-question analysis ─────────────────────────────────────
    questions      = db.query(Question).filter(Question.test_id == test_id).all()
    total_students = len(submissions)
 
    question_analysis = []
    for q in questions:
        answers = db.query(StudentAnswer).filter(StudentAnswer.question_id == q.id).all()
 
        attempted = len(answers)
        correct   = sum(1 for a in answers if a.awarded_marks and a.awarded_marks >= q.marks)
        skipped   = total_students - attempted
 
        # Most common wrong answer (MCQ only)
        most_common_wrong = None
        if q.question_type == "mcq":
            wrong_answers = [
                a.selected_option_id for a in answers
                if a.awarded_marks == 0 and a.selected_option_id
            ]
            if wrong_answers:
                from collections import Counter
                most_common_id = Counter(wrong_answers).most_common(1)[0][0]
                opt = db.query(Option).filter(Option.id == most_common_id).first()
                most_common_wrong = opt.text if opt else None
 
        question_analysis.append({
            "question_id":        q.id,
            "question_text":      q.text,
            "question_type":      q.question_type,
            "max_marks":          q.marks,
            "attempted":          attempted,
            "skipped":            skipped,
            "correct":            correct,
            "incorrect":          attempted - correct,
            "attempt_rate":       round((attempted / total_students) * 100, 1) if total_students else 0,
            "success_rate":       round((correct   / attempted)      * 100, 1) if attempted      else 0,
            "most_common_wrong":  most_common_wrong,
        })
 
    return {
        "test_id":   test_id,
        "title":     test.title,
 
        # ── overall stats ────────────────────────────────────────
        "overall": {
            "total_submitted": len(submissions),
            "passed":          sum(1 for s in submissions if s.is_passed),
            "failed":          sum(1 for s in submissions if s.is_passed is False),
            "average_score":   round(sum(scores) / len(scores), 2) if scores else 0,
            "highest_score":   max(scores) if scores else 0,
            "lowest_score":    min(scores) if scores else 0,
            "pass_rate":       round(
                sum(1 for s in submissions if s.is_passed) / len(submissions) * 100, 2
            ),
        },
 
        # ── distribution ─────────────────────────────────────────
        "score_distribution": score_distribution,
 
        # ── per-question breakdown ────────────────────────────────
        "question_analysis": question_analysis,
    }
  

@router.get("/legacy/student/{test_id}/analytics", include_in_schema=False)
def legacy_student_test_analytics(
    test_id: int,
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
        TestSubmission.student_user_id == current_user["user_id"],
        TestSubmission.status == "submitted"
    ).first()

    if not submission:
        raise HTTPException(
            status_code=404,
            detail="Submission not found"
        )

    all_submissions = db.query(TestSubmission).filter(
        TestSubmission.test_id == test_id,
        TestSubmission.status == "submitted"
    ).all()

    scores = [
        s.score_percentage
        for s in all_submissions
        if s.score_percentage is not None
    ]

    higher = sum(
        1 for s in scores
        if s > submission.score_percentage
    )

    student_answers = db.query(StudentAnswer).filter(
        StudentAnswer.submission_id == submission.id
    ).all()

    total_questions = db.query(Question).filter(
        Question.test_id == test_id
    ).count()

    correct = sum(
        1 for a in student_answers
        if a.awarded_marks and a.awarded_marks > 0
    )

    incorrect = len(student_answers) - correct
    skipped = total_questions - len(student_answers)

    return {
        "summary": {
            "score": submission.score_percentage,
            "obtained_marks": submission.total_marks,
            "correct_answers": correct,
            "incorrect_answers": incorrect,
            "skipped_questions": skipped,
            "passed": submission.is_passed,
            "submitted_at": submission.submitted_at
        },

        "comparison": {
            "class_average": round(sum(scores) / len(scores), 2),
            "highest_score": max(scores),
            "lowest_score": min(scores),
            "student_rank": higher + 1,
            "total_students": len(scores),
            "percentile": round(
                ((len(scores) - higher) / len(scores)) * 100,
                2
            )
        },

        "score_breakdown": [
            {
                "label": "Correct",
                "value": correct
            },
            {
                "label": "Incorrect",
                "value": incorrect
            },
            {
                "label": "Skipped",
                "value": skipped
            }
        ]
    }



@router.get("/instructor/{test_id}/overall-analytics")
def overall_test_analytics(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Complete Test Analytics

    Returns:
    - Test Summary
    - Student Statistics
    - Score Distribution
    - Performance Bands
    - Leaderboard
    - Submission Timeline
    - Question Analytics
    - Module Analytics
    """

    check_instructor(current_user)

    # --------------------------------------------------------
    # Test
    # --------------------------------------------------------

    test = db.query(Test).filter(Test.id == test_id).first()

    if not test:
        raise HTTPException(
            status_code=404,
            detail="Test not found"
        )

    submissions = (
        db.query(TestSubmission)
        .filter(
            TestSubmission.test_id == test_id,
            TestSubmission.status == "submitted"
        )
        .all()
    )

    if not submissions:
        return {
            "test_id": test.id,
            "title": test.title,
            "message": "No submissions yet"
        }

    scores = [
        s.score_percentage or 0
        for s in submissions
    ]

    total_submitted = len(submissions)

    passed = sum(
        1 for s in submissions
        if s.is_passed
    )

    failed = total_submitted - passed

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    summary = {

        "total_students": total_submitted,

        "submitted": total_submitted,

        "passed": passed,

        "failed": failed,

        "pass_rate": round(
            (passed / total_submitted) * 100,
            2
        ),

        "average_score": round(
            sum(scores) / len(scores),
            2
        ),

        "highest_score": max(scores),

        "lowest_score": min(scores),

        "median_score": statistics.median(scores),

        "standard_deviation": (
            round(statistics.stdev(scores), 2)
            if len(scores) > 1 else 0
        )
    }

    # --------------------------------------------------------
    # Score Distribution
    # --------------------------------------------------------

    bucket_map = {}

    for i in range(0, 100, 10):
        bucket_map[f"{i}-{i+9}"] = 0

    bucket_map["100"] = 0

    for score in scores:

        if score == 100:
            bucket_map["100"] += 1

        else:

            start = int(score // 10) * 10

            key = f"{start}-{start+9}"

            if key in bucket_map:
                bucket_map[key] += 1

    score_distribution = [

        {
            "range": k,
            "count": v
        }

        for k, v in bucket_map.items()

    ]

    # --------------------------------------------------------
    # Performance Bands
    # --------------------------------------------------------

    performance_bands = {

        "excellent": len(
            [x for x in scores if x >= 90]
        ),

        "good": len(
            [x for x in scores if 75 <= x < 90]
        ),

        "average": len(
            [x for x in scores if 50 <= x < 75]
        ),

        "poor": len(
            [x for x in scores if x < 50]
        )

    }

    # --------------------------------------------------------
    # Submission Timeline
    # --------------------------------------------------------

    timeline = {}

    for sub in submissions:

        if sub.submitted_at:

            key = sub.submitted_at.strftime("%H:00")

            timeline[key] = timeline.get(key, 0) + 1

    submission_timeline = [

        {
            "hour": k,
            "count": v
        }

        for k, v in sorted(timeline.items())

    ]

    # --------------------------------------------------------
    # Leaderboard
    # --------------------------------------------------------

    leaderboard = []

    ranked = sorted(
        submissions,
        key=lambda x: x.score_percentage or 0,
        reverse=True
    )

    for rank, sub in enumerate(ranked, start=1):

        student = db.query(User).filter(
            User.id == sub.student_user_id
        ).first()

        leaderboard.append({

            "rank": rank,

            "student_user_id": student.id if student else None,

            "student_id": student.student_id if student else None,

            "student_name": student.name if student else "Unknown",

            "score": sub.score_percentage,

            "obtained_marks": sub.total_score,

            "submitted_at": sub.submitted_at

        })

    # --------------------------------------------------------
    # Question Analytics
    # --------------------------------------------------------

    questions = db.query(Question).filter(
        Question.test_id == test_id
    ).all()

    question_analysis = []

    total_correct = 0
    total_attempted = 0

    for question in questions:

        answers = db.query(StudentAnswer).filter(
            StudentAnswer.question_id == question.id
        ).all()

        attempted = len(answers)

        correct = sum(
            1
            for a in answers
            if (
                a.awarded_marks is not None
                and a.awarded_marks >= question.marks
            )
        )

        incorrect = attempted - correct

        skipped = total_submitted - attempted

        total_correct += correct
        total_attempted += attempted

        wrong_answer = None

        if question.question_type == "mcq":

            wrong_ids = [

                a.selected_option_id

                for a in answers

                if (
                    a.awarded_marks == 0
                    and a.selected_option_id
                )

            ]

            if wrong_ids:

                common = Counter(
                    wrong_ids
                ).most_common(1)[0][0]

                option = db.query(Option).filter(
                    Option.id == common
                ).first()

                if option:
                    wrong_answer = option.text

        question_analysis.append({

            "question_id": question.id,

            "question_text": question.text,

            "question_type": question.question_type,

            "module_id": question.module_id,

            "max_marks": question.marks,

            "attempted": attempted,

            "correct": correct,

            "incorrect": incorrect,

            "skipped": skipped,

            "attempt_rate": round(
                attempted / total_submitted * 100,
                2
            ) if total_submitted else 0,

            "success_rate": round(
                correct / attempted * 100,
                2
            ) if attempted else 0,

            "most_common_wrong_answer": wrong_answer

        })

    # --------------------------------------------------------
    # Module Analytics
    # --------------------------------------------------------

    module_stats = {}

    for q in questions:

        module = db.query(Module).filter(
            Module.id == q.module_id
        ).first()

        module_name = module.title if module else "Unknown"

        if module_name not in module_stats:

            module_stats[module_name] = {

                "module_id": module.id if module else None,

                "module_name": module_name,

                "questions": 0,

                "attempted": 0,

                "correct": 0,

                "marks": 0

            }

        module_stats[module_name]["questions"] += 1

        answers = db.query(StudentAnswer).filter(
            StudentAnswer.question_id == q.id
        ).all()

        module_stats[module_name]["attempted"] += len(answers)

        module_stats[module_name]["correct"] += sum(

            1

            for a in answers

            if (
                a.awarded_marks is not None
                and a.awarded_marks >= q.marks
            )

        )

        module_stats[module_name]["marks"] += q.marks

    module_analysis = []

    for item in module_stats.values():

        module_analysis.append({

            **item,

            "success_rate": round(

                item["correct"] / item["attempted"] * 100,

                2

            ) if item["attempted"] else 0

        })

    # --------------------------------------------------------
    # Top / Bottom Performers
    # --------------------------------------------------------

    top_5 = leaderboard[:5]

    bottom_5 = sorted(
        leaderboard,
        key=lambda x: x["score"] or 0
    )[:5]

    # --------------------------------------------------------
    # Final Response
    # --------------------------------------------------------

    return {

        "test": {

            "id": test.id,

            "title": test.title,

            "course_id": test.course_id,

            "module_id": test.module_id,

            "passing_percentage": test.passing_percentage,

            "duration_minutes": test.duration_minutes

        },

        "summary": summary,

        "score_distribution": score_distribution,

        "performance_bands": performance_bands,

        "submission_timeline": submission_timeline,

        "leaderboard": leaderboard,

        "top_performers": top_5,

        "bottom_performers": bottom_5,

        "question_analysis": question_analysis,

        "module_analysis": module_analysis,

        "overall_question_accuracy": round(
            total_correct / total_attempted * 100,
            2
        ) if total_attempted else 0

    }




@router.get("/student/{test_id}/analytics")
def student_test_analytics(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Student Test Analytics

    Returns:
    - Student Summary
    - Comparison with class
    - Score breakdown
    - Question analysis
    - Module analysis
    - Performance trends
    """

    check_student(current_user)

    # --------------------------------------------------------
    # Test
    # --------------------------------------------------------

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
        TestSubmission.student_user_id == current_user["user_id"],
        TestSubmission.status == "submitted"
    ).first()

    if not submission:
        raise HTTPException(
            status_code=404,
            detail="You have not submitted this test"
        )

    # --------------------------------------------------------
    # Class statistics
    # --------------------------------------------------------

    all_submissions = db.query(TestSubmission).filter(
        TestSubmission.test_id == test_id,
        TestSubmission.status == "submitted"
    ).all()

    scores = [
        s.score_percentage or 0
        for s in all_submissions
    ]

    ranked = sorted(
        scores,
        reverse=True
    )

    student_rank = ranked.index(submission.score_percentage) + 1

    percentile = round(
        ((len(scores) - student_rank + 1) / len(scores)) * 100,
        2
    )

    # --------------------------------------------------------
    # Student Answers
    # --------------------------------------------------------

    answers = db.query(StudentAnswer).filter(
        StudentAnswer.submission_id == submission.id
    ).all()

    questions = db.query(Question).filter(
        Question.test_id == test_id
    ).all()

    total_questions = len(questions)

    correct = 0
    incorrect = 0
    skipped = 0

    question_analysis = []

    module_stats = {}

    for q in questions:

        answer = next(
            (
                a for a in answers
                if a.question_id == q.id
            ),
            None
        )

        module = db.query(Module).filter(
            Module.id == q.module_id
        ).first()

        module_name = module.title if module else "Unknown"

        if module_name not in module_stats:

            module_stats[module_name] = {

                "module_id": module.id if module else None,

                "module_name": module_name,

                "questions": 0,

                "correct": 0,

                "obtained_marks": 0,

                "total_marks": 0

            }

        module_stats[module_name]["questions"] += 1
        module_stats[module_name]["total_marks"] += q.marks

        if answer is None:

            skipped += 1

            question_analysis.append({

                "question_id": q.id,

                "question_text": q.text,

                "question_type": q.question_type,

                "module": module_name,

                "status": "Skipped",

                "obtained_marks": 0,

                "max_marks": q.marks

            })

            continue

        obtained = answer.awarded_marks or 0

        module_stats[module_name]["obtained_marks"] += obtained

        is_correct = obtained >= q.marks

        if is_correct:
            correct += 1
            module_stats[module_name]["correct"] += 1
        else:
            incorrect += 1

        selected_option = None
        correct_option = None

        if q.question_type == "mcq":

            if answer.selected_option_id:

                option = db.query(Option).filter(
                    Option.id == answer.selected_option_id
                ).first()

                if option:
                    selected_option = option.text

            correct_opt = db.query(Option).filter(
                Option.question_id == q.id,
                Option.is_correct == True
            ).first()

            if correct_opt:
                correct_option = correct_opt.text

        question_analysis.append({

            "question_id": q.id,

            "question_text": q.text,

            "module": module_name,

            "question_type": q.question_type,

            "status": "Correct" if is_correct else "Incorrect",

            "obtained_marks": obtained,

            "max_marks": q.marks,

            "selected_option": selected_option,

            "correct_option": correct_option

        })

    # --------------------------------------------------------
    # Module Analytics
    # --------------------------------------------------------

    module_analysis = []

    for item in module_stats.values():

        module_analysis.append({

            **item,

            "success_rate": round(

                item["correct"] /

                item["questions"] * 100,

                2

            ) if item["questions"] else 0,

            "percentage": round(

                item["obtained_marks"] /

                item["total_marks"] * 100,

                2

            ) if item["total_marks"] else 0

        })

    # --------------------------------------------------------
    # Score Breakdown
    # --------------------------------------------------------

    score_breakdown = {

        "correct": correct,

        "incorrect": incorrect,

        "skipped": skipped

    }

    # --------------------------------------------------------
    # Previous Attempts
    # --------------------------------------------------------

    previous_attempts = db.query(TestSubmission).filter(
        TestSubmission.student_user_id == current_user["user_id"],
        TestSubmission.test_id == test_id,
        TestSubmission.status == "submitted"
    ).order_by(
        TestSubmission.submitted_at
    ).all()

    performance_history = [

        {

            "attempt": i + 1,

            "score": s.score_percentage,

            "submitted_at": s.submitted_at

        }

        for i, s in enumerate(previous_attempts)

    ]

    # --------------------------------------------------------
    # Weakest / Strongest Module
    # --------------------------------------------------------

    strongest_module = None
    weakest_module = None

    if module_analysis:

        strongest_module = max(
            module_analysis,
            key=lambda x: x["percentage"]
        )

        weakest_module = min(
            module_analysis,
            key=lambda x: x["percentage"]
        )

    # --------------------------------------------------------
    # Return
    # --------------------------------------------------------

    return {

        "test": {

            "id": test.id,

            "title": test.title,

            "course_id": test.course_id,

            "module_id": test.module_id,

            "passing_percentage": test.passing_percentage,

            "duration_minutes": test.duration_minutes

        },

        "summary": {

            "score": submission.score_percentage,

            "obtained_marks": submission.total_score,

            "submitted_at": submission.submitted_at,

            "passed": submission.is_passed,

            "correct": correct,

            "incorrect": incorrect,

            "skipped": skipped,

            "accuracy": round(

                correct /

                total_questions * 100,

                2

            ) if total_questions else 0

        },

        "comparison": {

            "rank": student_rank,

            "percentile": percentile,

            "class_average": round(

                statistics.mean(scores),

                2

            ),

            "highest_score": max(scores),

            "lowest_score": min(scores),

            "median_score": statistics.median(scores)

        },

        "score_breakdown": score_breakdown,

        "module_analysis": module_analysis,

        "question_analysis": question_analysis,

        "performance_history": performance_history,

        "strongest_module": strongest_module,

        "weakest_module": weakest_module

    }

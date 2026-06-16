from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.classroom import Classroom
from app.models.enrollment import Enrollment
from app.models.test import Test, TestSubmission
from app.models.user import User

router = APIRouter(prefix="/classes", tags=["Class Scores"])


def _get_classroom(db: Session, class_id: int) -> Classroom:
    classroom = db.query(Classroom).filter(Classroom.id == class_id).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Class not found")
    return classroom


@router.get("/{class_id}/average-score")
def get_average_score(class_id: int, db: Session = Depends(get_db)):
    classroom = _get_classroom(db, class_id)

    avg_score = (
        db.query(func.avg(TestSubmission.score))
        .join(Test, Test.id == TestSubmission.test_id)
        .filter(
            Test.course_id == classroom.course_id,
            Test.batch_name == classroom.batch_name,
            TestSubmission.status == "submitted",
            TestSubmission.score != None,
        )
        .scalar()
    )

    if avg_score is None:
        return {
            "class_id": class_id,
            "course_id": classroom.course_id,
            "batch_name": classroom.batch_name,
            "average_score": 0,
            "total_marks": 100,
            "submitted_count": 0,
        }

    submitted_count = (
        db.query(TestSubmission.id)
        .join(Test, Test.id == TestSubmission.test_id)
        .filter(
            Test.course_id == classroom.course_id,
            Test.batch_name == classroom.batch_name,
            TestSubmission.status == "submitted",
            TestSubmission.score != None,
        )
        .count()
    )

    return {
        "class_id": class_id,
        "course_id": classroom.course_id,
        "batch_name": classroom.batch_name,
        "average_score": round(float(avg_score), 2),
        "total_marks": 100,
        "submitted_count": submitted_count,
    }


@router.get("/{class_id}/score-details")
def get_score_details(class_id: int, db: Session = Depends(get_db)):
    classroom = _get_classroom(db, class_id)

    enrollments = db.query(Enrollment).filter(
        Enrollment.course_id == classroom.course_id,
        Enrollment.batch_name == classroom.batch_name,
        Enrollment.status == "ongoing",
    ).all()

    tests = db.query(Test).filter(
        Test.course_id == classroom.course_id,
        Test.batch_name == classroom.batch_name,
    ).all()

    submissions = (
        db.query(TestSubmission)
        .join(Test, Test.id == TestSubmission.test_id)
        .filter(
            Test.course_id == classroom.course_id,
            Test.batch_name == classroom.batch_name,
        )
        .all()
    )
    submission_by_student_test = {
        (submission.student_user_id, submission.test_id): submission
        for submission in submissions
    }

    results = []
    for enrollment in enrollments:
        student = db.query(User).filter(User.id == enrollment.user_id).first()
        student_scores = []

        for test in tests:
            submission = submission_by_student_test.get((enrollment.user_id, test.id))
            student_scores.append({
                "test_id": test.id,
                "test_title": test.title,
                "score": submission.score if submission else None,
                "status": submission.status if submission else "not_attended",
                "submitted_at": submission.submitted_at if submission else None,
            })

        numeric_scores = [
            item["score"]
            for item in student_scores
            if item["score"] is not None
        ]

        results.append({
            "student_user_id": enrollment.user_id,
            "student_id": student.student_id if student else str(enrollment.user_id),
            "student_name": student.name if student else "Unknown",
            "average_score": round(sum(numeric_scores) / len(numeric_scores), 2) if numeric_scores else None,
            "tests": student_scores,
        })

    return {
        "class_id": class_id,
        "course_id": classroom.course_id,
        "batch_name": classroom.batch_name,
        "total_students": len(results),
        "total_tests": len(tests),
        "results": results,
    }

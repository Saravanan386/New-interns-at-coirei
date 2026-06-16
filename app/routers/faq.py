from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.utils.security import get_current_user
from app.models.faq import FAQ
from app.schemas import FAQCreate, FAQUpdate

router = APIRouter(
    prefix="/faqs",
    tags=["FAQs"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_instructor(current_user: dict):
    if current_user.get("role") != "instructor":
        raise HTTPException(
            status_code=403,
            detail="Instructor access only"
        )


def check_student(current_user: dict):
    if current_user.get("role") != "student":
        raise HTTPException(
            status_code=403,
            detail="Student access only"
        )


def check_admin(current_user: dict):
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access only"
        )

@router.post("/")
def create_faq( body: FAQCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    check_instructor(current_user)
    
    faq = FAQ(
        course_id=body.course_id,
        question=body.question,
        answer=body.answer
    )

    db.add(faq)
    db.commit()
    db.refresh(faq)

    return {
        "status": "success",
        "message": "FAQ created successfully.",
        "data": faq
    }

@router.get("/")
def get_faqs(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_instructor(current_user)

    faqs = db.query(FAQ).filter(
        FAQ.course_id == course_id
    ).all()

    return {
        "status": "success",
        "data": faqs
    }

@router.put("/{faq_id}")
def update_faq(
    faq_id: int,
    body: FAQUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_instructor(current_user)

    faq = db.query(FAQ).filter(
        FAQ.id == faq_id
    ).first()

    if not faq:
        raise HTTPException(
            status_code=404,
            detail="FAQ not found."
        )

    if body.question is not None:
        faq.question = body.question

    if body.answer is not None:
        faq.answer = body.answer

    db.commit()
    db.refresh(faq)

    return {
        "status": "success",
        "message": "FAQ updated successfully.",
        "data": faq
    }

@router.delete("/{faq_id}")
def delete_faq(
    faq_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_instructor(current_user)

    faq = db.query(FAQ).filter(
        FAQ.id == faq_id
    ).first()

    if not faq:
        raise HTTPException(
            status_code=404,
            detail="FAQ not found."
        )

    db.delete(faq)
    db.commit()

    return {
        "status": "success",
        "message": "FAQ deleted successfully."
    }

@router.get("/student")
def get_student_faqs(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_student(current_user)

    faqs = db.query(FAQ).filter(
        FAQ.course_id == course_id
    ).all()

    return faqs


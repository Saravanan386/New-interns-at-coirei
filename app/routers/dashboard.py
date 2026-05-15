from fastapi import APIRouter, Depends
from app.utils.security import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/courses")
def get_dashboard_courses(user=Depends(get_current_user)):
    return [
        {
            "course_id": 1,
            "code": "AM101",
            "title": "AI / ML Frontier AI Engineer",
            "duration_months": 3,
            "lessons": 5,
            "assignments": 3,
            "thumbnail_url": "https://placehold.co/600x400"
        },
        {
            "course_id": 2,
            "code": "SS102",
            "title": "System and Software System Pro",
            "duration_months": 3,
            "lessons": 4,
            "assignments": 2,
            "thumbnail_url": "https://placehold.co/600x400"
        }
    ]


from app.database import SessionLocal
from app.models.session import ClassSession
from app.models.attendance import SessionParticipant
from sqlalchemy.orm import Session

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/classes-summary")
def classes_summary(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    user_id = user["user_id"]
    
    total = db.query(ClassSession).count()
    attended = db.query(SessionParticipant).filter(
        SessionParticipant.user_id == user_id,
        SessionParticipant.status == "present"
    ).count()
    
    return {
        "total": total,
        "attended": attended
    }

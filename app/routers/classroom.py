from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.classroom import Classroom
from app.services.jwt_service import get_current_user

router = APIRouter(prefix="/classrooms", tags=["Classrooms"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/")
def create_classroom(
    name: str,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user["role"] not in ["admin", "instructor"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    classroom = Classroom(name=name)
    db.add(classroom)
    db.commit()
    db.refresh(classroom)

    return {
        "id": classroom.id,
        "name": classroom.name
    }


@router.get("/")
def list_classrooms(
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(Classroom).all()

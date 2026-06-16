# app/routers/meet.py
"""
Legacy classroom-based meet endpoint.
Now generates a 100ms auth token for the classroom room.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.services.jwt_service import get_current_user
from app.services.hms_service import generate_auth_token

router = APIRouter()


@router.get("/classrooms/{classroom_id}/start")
def start_class(
    classroom_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if user["role"] not in ["admin", "instructor"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    db_user = db.query(User).filter(User.id == user["user_id"]).first()
    user_name = db_user.name if db_user else f"User_{user['user_id']}"

    room_id = f"classroom_{classroom_id}"   # use as 100ms room identifier
    role = "host" if user["role"] in ["admin", "instructor"] else "guest"

    token = generate_auth_token(
        room_id=room_id,
        user_id=user["user_id"],
        user_name=user_name,
        role=role
    )

    return {
        "room_id": room_id,
        "token": token,
        "role": role
    }

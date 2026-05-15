from fastapi import APIRouter, Depends
from app.utils.security import get_current_user, require_roles
import os

router = APIRouter(prefix="/classes", tags=["Classes"])

JITSI_BASE_URL = os.getenv("JITSI_BASE_URL", "https://localhost:8443")


@router.get("/upcoming")
def upcoming_classes(user=Depends(get_current_user)):
    return [
        {
            "class_id": 55,
            "course": "AI / ML Frontier AI Engineer",
            "time": "17:30",
            "can_join": True,
            "join_url": f"{JITSI_BASE_URL}/classroom_55"
        },
        {
            "class_id": 56,
            "course": "System and Software System Pro",
            "time": "20:30",
            "can_join": False,
            "join_url": None
        }
    ]
    
@router.post("/create")
def create_class(
    data: dict,
    user=Depends(require_roles(["instructor"]))
):
    return {"message": "Class created"}

@router.get("/all-users")
def list_users(user=Depends(require_roles(["admin"]))):
    return []


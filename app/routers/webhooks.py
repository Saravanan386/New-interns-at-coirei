from fastapi import APIRouter, Request
from app.database import SessionLocal
from app.services.attendance_service import participant_join, participant_leave

router = APIRouter()

@router.post("/webhooks/jitsi")
async def jitsi_webhook(request: Request):
    payload = await request.json()

    event = payload.get("event")
    session_id = payload.get("session_id")
    user_id = payload.get("user_id")

    db = SessionLocal()

    try:
        if event == "participant_joined":
            participant_join(db, session_id, user_id)

        elif event == "participant_left":
            participant_leave(db, session_id, user_id)
    finally:
        db.close()

    return {"ok": True}

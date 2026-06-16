from fastapi import APIRouter, HTTPException, Request
from app.services.attendance_service import participant_join, participant_leave
from app.services.tenant_database import get_tenant_session_local

router = APIRouter()

@router.post("/webhooks/jitsi")
async def jitsi_webhook(request: Request):
    payload = await request.json()

    event = payload.get("event")
    session_id = payload.get("session_id")
    user_id = payload.get("user_id")
    tenant_database_name = (
        payload.get("tenant_database_name")
        or payload.get("database_name")
        or request.headers.get("X-Tenant-Database")
    )

    if not tenant_database_name:
        raise HTTPException(
            status_code=400,
            detail="tenant_database_name is required for webhook routing",
        )

    tenant_session = get_tenant_session_local(tenant_database_name)
    db = tenant_session()

    try:
        if event == "participant_joined":
            participant_join(db, session_id, user_id)

        elif event == "participant_left":
            participant_leave(db, session_id, user_id)
    finally:
        db.close()

    return {"ok": True}

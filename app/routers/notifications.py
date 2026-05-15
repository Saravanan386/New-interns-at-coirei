# app/routers/notifications.py
"""
Notification endpoints (student & instructor)

  GET    /notifications/           → list current user's notifications (grouped)
  PATCH  /notifications/read-all   → mark all as read
  PATCH  /notifications/{id}/read  → mark one as read
  DELETE /notifications/{id}       → delete one notification
"""

from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.utils.security import get_current_user
from app.models.notification import Notification
from app.schemas import NotificationResponse

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def _utc_now() -> datetime:
    return datetime.utcnow()


# ── List Notifications ────────────────────────────────────────────────────────

@router.get("/", summary="Get my notifications")
def get_notifications(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Returns the current user's notifications sorted newest-first,
    grouped into Today / Yesterday / Older.
    Also returns the total unread count (for the badge number on the bell icon).
    """
    user_id = current_user["user_id"]

    all_notifs = (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .all()
    )

    unread_count = sum(1 for n in all_notifs if not n.is_read)

    now = _utc_now().date()
    yesterday = now - timedelta(days=1)

    today_list    = []
    yesterday_list = []
    older_list    = []

    for n in all_notifs:
        day = n.created_at.date()
        item = NotificationResponse.from_orm(n)
        if day == now:
            today_list.append(item)
        elif day == yesterday:
            yesterday_list.append(item)
        else:
            older_list.append(item)

    return {
        "unread_count": unread_count,
        "groups": [
            {"label": "Today",     "notifications": [i.dict() for i in today_list]},
            {"label": "Yesterday", "notifications": [i.dict() for i in yesterday_list]},
            {"label": "Older",     "notifications": [i.dict() for i in older_list]},
        ]
    }


# ── Mark All As Read ──────────────────────────────────────────────────────────

@router.patch("/read-all", summary="Mark all notifications as read")
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Marks every unread notification for the current user as read."""
    updated = (
        db.query(Notification)
        .filter(
            Notification.user_id == current_user["user_id"],
            Notification.is_read == False,        # noqa: E712
        )
        .all()
    )
    for n in updated:
        n.is_read = True
    db.commit()
    return {"message": f"{len(updated)} notification(s) marked as read."}


# ── Mark One As Read ──────────────────────────────────────────────────────────

@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_one_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    notif = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user["user_id"],
    ).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    notif.is_read = True
    db.commit()
    db.refresh(notif)
    return notif


# ── Delete One Notification ───────────────────────────────────────────────────

@router.delete("/{notification_id}", summary="Delete a notification")
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    notif = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user["user_id"],
    ).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    db.delete(notif)
    db.commit()
    return {"message": "Notification deleted."}

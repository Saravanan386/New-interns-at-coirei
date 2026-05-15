# app/services/notifications.py
"""
Thin helper used by any router to fire an in-app notification.
Callers are responsible for db.commit() after calling this so they
can batch multiple notifications in one transaction.
"""

from sqlalchemy.orm import Session
from app.models.notification import Notification


def create_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    type: str = "system",
    related_id: int = None,
) -> Notification:
    """
    Append a notification row.  Does NOT commit – caller commits.

    Example
    -------
    create_notification(db, user_id=42, type="assignment",
                        title="New Assignment",
                        message="Module 1 – Task 1 has been posted",
                        related_id=assignment_id)
    db.commit()
    """
    notif = Notification(
        user_id=user_id,
        type=type,
        title=title,
        message=message,
        related_id=related_id,
    )
    db.add(notif)
    return notif

# app/models/notification.py

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Notification(Base):
    """
    In-app notification record for a single user.

    type values: 'assignment' | 'test_score' | 'schedule' | 'system'
    related_id : assignment_id / test_id etc. for deep-linking from the card
    """
    __tablename__ = "notifications"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type       = Column(String,  nullable=False, default="system")
    title      = Column(String,  nullable=False)
    message    = Column(String,  nullable=False)
    is_read    = Column(Boolean, default=False,  nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    related_id = Column(Integer, nullable=True)   # assignment_id / test_id

    user = relationship("User")

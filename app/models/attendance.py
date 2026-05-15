from sqlalchemy import Column, Integer, ForeignKey, DateTime, Float, String
from app.database import Base
from datetime import datetime

class SessionParticipant(Base):
    __tablename__ = "session_participants"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("class_sessions.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

    join_time = Column(DateTime, nullable=True)  # None for students who never joined
    leave_time = Column(DateTime, nullable=True)

    duration_minutes = Column(Float, default=0)
    status = Column(String)  # present | late | absent

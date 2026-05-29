# app/models/session.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from app.database import Base
from datetime import datetime

class ClassSession(Base):
    __tablename__ = "class_sessions"

    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    batch_name = Column(String, nullable=False)

    # 100ms room ID (returned from 100ms API on room creation)
    livekit_room_name = Column(String, nullable=True)   # stores 100ms room_id

    # Guest/student join URL (100ms prebuilt UI link with guest room code)
    join_url = Column(String, nullable=True)

    # Host/instructor join URL (100ms prebuilt UI link with host room code)
    host_url = Column(String, nullable=True)

    status = Column(String, default="ended")  # live | ended
    start_time = Column(DateTime)
    end_time = Column(DateTime)

   

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey
)

from app.database import Base


class ClassSession(Base):

    __tablename__ = "class_sessions"

    id = Column(Integer, primary_key=True)

    classroom_id = Column(
        Integer,
        ForeignKey("classrooms.id"),
        nullable=False
    )

    livekit_room_name = Column(String)

    join_url = Column(String)

    host_url = Column(String)

    status = Column(
        String,
        default="ended"
    )

    start_time = Column(DateTime)

    end_time = Column(DateTime)


    
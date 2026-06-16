# app/models/module.py

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey
)
from sqlalchemy.orm import relationship

from app.database import Base


class Module(Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String, nullable=False)

    order = Column(Integer, default=1)

    status = Column(String, default="active")

    course_id = Column(
        Integer,
        ForeignKey("courses.id"),
        nullable=False
    )

    batch_name = Column(String, nullable=True)

    chapters = relationship(
        "Chapter",
        back_populates="module",
        cascade="all, delete-orphan"
    )
    

class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String, nullable=False)

    order = Column(Integer, default=1)

    # NEW FIELDS
    class_content = Column(String, nullable=True)

    key_topics = Column(String, nullable=True)

    module_id = Column(
        Integer,
        ForeignKey("modules.id", ondelete="CASCADE"),
        nullable=False
    )

    module = relationship(
        "Module",
        back_populates="chapters"
    )

    resources = relationship(
        "ChapterResource",
        back_populates="chapter",
        cascade="all, delete-orphan"
    )
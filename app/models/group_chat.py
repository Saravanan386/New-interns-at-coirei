# app/models/group_chat.py
"""
Group / Batch Chat Models
- GroupChat        : one per course+batch (created lazily on first use)
- GroupMessage     : a message in the group chat
- GroupMessageLike : like on a group message
- GroupMessageBookmark : bookmark on a group message
"""

from sqlalchemy import (
    Column, Integer, String, ForeignKey, DateTime, Boolean, Text, UniqueConstraint
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class GroupChat(Base):
    """
    One group chat per course+batch.
    Created lazily when the first message is sent (or first fetch occurs).
    """
    __tablename__ = "group_chats"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    batch_name = Column(String, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("course_id", "batch_name", name="uq_group_chat"),
    )

    course = relationship("Course")
    messages = relationship("GroupMessage", back_populates="group", cascade="all, delete-orphan")


class GroupMessage(Base):
    """A message in a group/batch chat."""
    __tablename__ = "group_messages"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("group_chats.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sender_role = Column(String, nullable=False)  # 'student' | 'instructor'

    text = Column(Text, nullable=True)
    attachment_url = Column(String, nullable=True)
    attachment_name = Column(String, nullable=True)

    # Pinning (instructor only)
    is_pinned = Column(Boolean, default=False)
    pinned_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)  # soft-delete

    group = relationship("GroupChat", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])
    likes = relationship("GroupMessageLike", back_populates="message", cascade="all, delete-orphan")
    bookmarks = relationship("GroupMessageBookmark", back_populates="message", cascade="all, delete-orphan")


class GroupMessageLike(Base):
    """One like per user per group message."""
    __tablename__ = "group_message_likes"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("group_messages.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("message_id", "user_id", name="uq_group_like"),
    )

    message = relationship("GroupMessage", back_populates="likes")


class GroupMessageBookmark(Base):
    """One bookmark per user per group message."""
    __tablename__ = "group_message_bookmarks"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("group_messages.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("message_id", "user_id", name="uq_group_bookmark"),
    )

    message = relationship("GroupMessage", back_populates="bookmarks")

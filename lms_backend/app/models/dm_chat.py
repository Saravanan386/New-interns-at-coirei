# app/models/dm_chat.py
"""
1-to-1 Direct Message (DM) Chat Models
- DMConversation : a pair of users
- DMMessage      : a message in a conversation
- DMMessageLike  : like on a DM message
- DMMessageBookmark : bookmark on a DM message
"""

from sqlalchemy import (
    Column, Integer, String, ForeignKey, DateTime, Boolean, Text, UniqueConstraint
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class DMConversation(Base):
    """
    Represents a 1-to-1 conversation between two users.
    user_a_id < user_b_id (always sorted so there's exactly one row per pair).
    """
    __tablename__ = "dm_conversations"

    id = Column(Integer, primary_key=True, index=True)

    user_a_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user_b_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Unread counters
    unread_a = Column(Integer, default=0)   # unread count for user_a
    unread_b = Column(Integer, default=0)   # unread count for user_b

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Ensure only one conversation per pair
    __table_args__ = (
        UniqueConstraint("user_a_id", "user_b_id", name="uq_dm_pair"),
    )

    user_a = relationship("User", foreign_keys=[user_a_id])
    user_b = relationship("User", foreign_keys=[user_b_id])
    messages = relationship("DMMessage", back_populates="conversation", cascade="all, delete-orphan")


class DMMessage(Base):
    """A single message inside a DMConversation."""
    __tablename__ = "dm_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("dm_conversations.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    text = Column(Text, nullable=True)
    attachment_url = Column(String, nullable=True)   # URL returned by /api/uploads/chat
    attachment_name = Column(String, nullable=True)  # original filename

    created_at = Column(DateTime, default=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)     # soft-delete

    conversation = relationship("DMConversation", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])
    likes = relationship("DMMessageLike", back_populates="message", cascade="all, delete-orphan")
    bookmarks = relationship("DMMessageBookmark", back_populates="message", cascade="all, delete-orphan")


class DMMessageLike(Base):
    """One like per user per DM message."""
    __tablename__ = "dm_message_likes"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("dm_messages.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("message_id", "user_id", name="uq_dm_like"),
    )

    message = relationship("DMMessage", back_populates="likes")


class DMMessageBookmark(Base):
    """One bookmark per user per DM message."""
    __tablename__ = "dm_message_bookmarks"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("dm_messages.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("message_id", "user_id", name="uq_dm_bookmark"),
    )

    message = relationship("DMMessage", back_populates="bookmarks")

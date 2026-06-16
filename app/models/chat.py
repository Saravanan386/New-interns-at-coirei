# app/models/chat.py
# Updated: added visibility to ChatPost, ChatReplyLike model
"""
Course Q&A Chat System
- ChatPost   : top-level question/message from a student or instructor
- ChatReply  : threaded reply (can be from student or instructor)
- ChatLike   : one like per user per post
- ChatBookmark: one bookmark per user per post
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class ChatPost(Base):
    """
    A top-level post (question) in the batch Q&A feed.
    Scoped to course_id + batch_name so only students of that batch see it.
    """
    __tablename__ = "chat_posts"

    id = Column(Integer, primary_key=True, index=True)

    # Scope: which batch this post belongs to
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    batch_name = Column(String, nullable=False)

    # Author
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # Cached for quick display (student | instructor)
    author_role = Column(String, nullable=False)

    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Visibility: 'public' (all batch students) or 'private' (DM to instructor only)
    visibility = Column(String, default="public", nullable=False)

    # Instructor can pin a post
    is_pinned = Column(Boolean, default=False)
    pinned_at = Column(DateTime, nullable=True)

    # Relationships
    author = relationship("User", foreign_keys=[author_id])
    replies = relationship("ChatReply", back_populates="post", cascade="all, delete-orphan")
    likes = relationship("ChatLike", back_populates="post", cascade="all, delete-orphan")
    bookmarks = relationship("ChatBookmark", back_populates="post", cascade="all, delete-orphan")
    course = relationship("Course")


class ChatReply(Base):
    """
    A reply to a top-level ChatPost.
    Instructor replies get is_instructor=True → blue badge on the frontend.
    """
    __tablename__ = "chat_replies"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("chat_posts.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    author_role = Column(String, nullable=False)   # 'student' | 'instructor'

    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    post = relationship("ChatPost", back_populates="replies")
    author = relationship("User", foreign_keys=[author_id])
    reply_likes = relationship("ChatReplyLike", back_populates="reply", cascade="all, delete-orphan")


class ChatLike(Base):
    """One like per user per post (unique constraint enforced in app logic)."""
    __tablename__ = "chat_likes"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("chat_posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    post = relationship("ChatPost", back_populates="likes")


class ChatBookmark(Base):
    """One bookmark per user per post."""
    __tablename__ = "chat_bookmarks"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("chat_posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    post = relationship("ChatPost", back_populates="bookmarks")


class ChatReplyLike(Base):
    """One like per user per reply."""
    __tablename__ = "chat_reply_likes"

    id = Column(Integer, primary_key=True, index=True)
    reply_id = Column(Integer, ForeignKey("chat_replies.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    reply = relationship("ChatReply", back_populates="reply_likes")

# app/routers/dm_chat.py
"""
Individual 1-to-1 DM Chat API
==============================
URL prefix: /api/chats

Endpoints:
  GET    /api/chats/conversations                                         → list all DM conversations
  POST   /api/chats/conversations                                         → start a new 1-1 conversation
  GET    /api/chats/conversations/{conversation_id}/messages              → paginated messages
  POST   /api/chats/conversations/{conversation_id}/messages              → send a message
  DELETE /api/chats/conversations/{conversation_id}/messages/{message_id} → delete own message
  PATCH  /api/chats/conversations/{conversation_id}/read                  → mark as read
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.utils.security import get_current_user
from app.models.dm_chat import DMConversation, DMMessage, DMMessageLike, DMMessageBookmark
from app.models.user import User
from app.schemas import (
    DMMessageCreate, DMMessageResponse, DMConversationResponse, StartConversationRequest
)

router = APIRouter(prefix="/api/chats", tags=["Individual Chat (DM)"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_conversation_or_404(db: Session, conversation_id: int, user_id: int) -> DMConversation:
    conv = db.query(DMConversation).filter(DMConversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conv.user_a_id != user_id and conv.user_b_id != user_id:
        raise HTTPException(status_code=403, detail="Not part of this conversation")
    return conv


def _build_dm_message(msg: DMMessage, current_user_id: int, db: Session) -> DMMessageResponse:
    sender = db.query(User).filter(User.id == msg.sender_id).first()
    like_count = len([l for l in msg.likes])
    is_liked = any(l.user_id == current_user_id for l in msg.likes)
    is_bookmarked = any(b.user_id == current_user_id for b in msg.bookmarks)
    return DMMessageResponse(
        id=msg.id,
        conversation_id=msg.conversation_id,
        sender_id=msg.sender_id,
        sender_name=sender.name if sender else "Unknown",
        sender_role=sender.role if sender else "student",
        text=msg.text,
        attachment_url=msg.attachment_url,
        attachment_name=msg.attachment_name,
        created_at=msg.created_at,
        is_deleted=msg.deleted_at is not None,
        like_count=like_count,
        is_liked_by_me=is_liked,
        is_bookmarked_by_me=is_bookmarked,
    )


def _build_conv_response(conv: DMConversation, current_user_id: int, db: Session) -> DMConversationResponse:
    """Build conversation response from perspective of current_user."""
    if conv.user_a_id == current_user_id:
        other_id = conv.user_b_id
        unread = conv.unread_a
    else:
        other_id = conv.user_a_id
        unread = conv.unread_b

    other = db.query(User).filter(User.id == other_id).first()

    # Last visible message
    last_msg = (
        db.query(DMMessage)
        .filter(DMMessage.conversation_id == conv.id, DMMessage.deleted_at == None)
        .order_by(DMMessage.created_at.desc())
        .first()
    )

    return DMConversationResponse(
        id=conv.id,
        other_user_id=other_id,
        other_user_name=other.name if other else "Unknown",
        other_user_role=other.role if other else "student",
        other_user_student_id=other.student_id if other else None,
        unread_count=unread,
        last_message_text=last_msg.text if last_msg else None,
        last_message_at=last_msg.created_at if last_msg else None,
    )


# ── GET /api/chats/conversations ──────────────────────────────────────────────

@router.get("/conversations", response_model=List[DMConversationResponse])
def list_conversations(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all 1-1 conversations (sidebar list). Returns last message + unread count."""
    user_id = current_user["user_id"]
    convs = db.query(DMConversation).filter(
        (DMConversation.user_a_id == user_id) | (DMConversation.user_b_id == user_id)
    ).order_by(DMConversation.updated_at.desc()).all()

    return [_build_conv_response(c, user_id, db) for c in convs]


# ── POST /api/chats/conversations ─────────────────────────────────────────────

@router.post("/conversations", response_model=DMConversationResponse, status_code=201)
def start_conversation(
    body: StartConversationRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Start a new 1-1 conversation with a user (by userId)."""
    user_id = current_user["user_id"]
    other_id = body.user_id

    if user_id == other_id:
        raise HTTPException(status_code=400, detail="Cannot start a conversation with yourself")

    # Validate other user exists
    other = db.query(User).filter(User.id == other_id).first()
    if not other:
        raise HTTPException(status_code=404, detail="User not found")

    # Normalize pair so user_a < user_b (ensures uniqueness)
    a_id, b_id = sorted([user_id, other_id])

    existing = db.query(DMConversation).filter(
        DMConversation.user_a_id == a_id,
        DMConversation.user_b_id == b_id
    ).first()

    if existing:
        return _build_conv_response(existing, user_id, db)

    conv = DMConversation(user_a_id=a_id, user_b_id=b_id)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return _build_conv_response(conv, user_id, db)


# ── GET /api/chats/conversations/{conversation_id}/messages ───────────────────

@router.get("/conversations/{conversation_id}/messages", response_model=List[DMMessageResponse])
def get_messages(
    conversation_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Fetch messages in a 1-1 conversation (paginated). Oldest-first within page."""
    user_id = current_user["user_id"]
    conv = _get_conversation_or_404(db, conversation_id, user_id)

    messages = (
        db.query(DMMessage)
        .filter(DMMessage.conversation_id == conversation_id)
        .order_by(DMMessage.created_at.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return [_build_dm_message(m, user_id, db) for m in messages]


# ── POST /api/chats/conversations/{conversation_id}/messages ──────────────────

@router.post("/conversations/{conversation_id}/messages", response_model=DMMessageResponse, status_code=201)
def send_message(
    conversation_id: int,
    body: DMMessageCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Send a message. Body: text, attachments (images/files as base64 or URL)."""
    user_id = current_user["user_id"]
    conv = _get_conversation_or_404(db, conversation_id, user_id)

    if not body.text and not body.attachment_url:
        raise HTTPException(status_code=400, detail="Message must have text or attachment")

    msg = DMMessage(
        conversation_id=conversation_id,
        sender_id=user_id,
        text=body.text,
        attachment_url=body.attachment_url,
        attachment_name=body.attachment_name,
    )
    db.add(msg)

    # Increment unread for the OTHER user
    if conv.user_a_id == user_id:
        conv.unread_b = (conv.unread_b or 0) + 1
    else:
        conv.unread_a = (conv.unread_a or 0) + 1

    conv.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(msg)

    return _build_dm_message(msg, user_id, db)


# ── DELETE /api/chats/conversations/{conversation_id}/messages/{message_id} ───

@router.delete("/conversations/{conversation_id}/messages/{message_id}")
def delete_message(
    conversation_id: int,
    message_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete own message (soft delete)."""
    user_id = current_user["user_id"]
    _get_conversation_or_404(db, conversation_id, user_id)

    msg = db.query(DMMessage).filter(
        DMMessage.id == message_id,
        DMMessage.conversation_id == conversation_id
    ).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    if msg.sender_id != user_id:
        raise HTTPException(status_code=403, detail="Cannot delete another user's message")

    msg.deleted_at = datetime.utcnow()
    msg.text = "This message was deleted"
    db.commit()
    return {"message": "Message deleted"}


# ── PATCH /api/chats/conversations/{conversation_id}/read ─────────────────────

@router.patch("/conversations/{conversation_id}/read")
def mark_conversation_read(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Mark conversation as read. Clears unread badge count."""
    user_id = current_user["user_id"]
    conv = _get_conversation_or_404(db, conversation_id, user_id)

    if conv.user_a_id == user_id:
        conv.unread_a = 0
    else:
        conv.unread_b = 0

    db.commit()
    return {"message": "Marked as read", "conversation_id": conversation_id}


# ── POST /api/chats/messages/{message_id}/like ───────────────────────────────
# These are in a separate reactions router below but added here for DM messages

@router.post("/messages/{message_id}/like")
def like_dm_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Like a DM message."""
    user_id = current_user["user_id"]
    msg = db.query(DMMessage).filter(DMMessage.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    # Ensure user is part of conversation
    conv = db.query(DMConversation).filter(DMConversation.id == msg.conversation_id).first()
    if conv.user_a_id != user_id and conv.user_b_id != user_id:
        raise HTTPException(status_code=403, detail="Not part of this conversation")

    existing = db.query(DMMessageLike).filter(
        DMMessageLike.message_id == message_id,
        DMMessageLike.user_id == user_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already liked")

    db.add(DMMessageLike(message_id=message_id, user_id=user_id))
    db.commit()
    like_count = db.query(DMMessageLike).filter(DMMessageLike.message_id == message_id).count()
    return {"liked": True, "like_count": like_count}


@router.delete("/messages/{message_id}/like")
def unlike_dm_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Remove like from a DM message."""
    user_id = current_user["user_id"]
    existing = db.query(DMMessageLike).filter(
        DMMessageLike.message_id == message_id,
        DMMessageLike.user_id == user_id
    ).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Like not found")

    db.delete(existing)
    db.commit()
    like_count = db.query(DMMessageLike).filter(DMMessageLike.message_id == message_id).count()
    return {"liked": False, "like_count": like_count}


@router.patch("/messages/{message_id}/bookmark")
def bookmark_dm_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Bookmark / unbookmark a DM message."""
    user_id = current_user["user_id"]
    msg = db.query(DMMessage).filter(DMMessage.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    existing = db.query(DMMessageBookmark).filter(
        DMMessageBookmark.message_id == message_id,
        DMMessageBookmark.user_id == user_id
    ).first()
    if existing:
        db.delete(existing)
        db.commit()
        return {"bookmarked": False}
    else:
        db.add(DMMessageBookmark(message_id=message_id, user_id=user_id))
        db.commit()
        return {"bookmarked": True}

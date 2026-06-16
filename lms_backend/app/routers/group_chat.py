# app/routers/group_chat.py
"""
Group / Batch Chat API
======================
URL prefix: /api/chats/groups

Endpoints:
  GET    /api/chats/groups/{group_id}/messages                      → paginated messages (pinned first)
  POST   /api/chats/groups/{group_id}/messages                      → post a message
  DELETE /api/chats/groups/{group_id}/messages/{message_id}         → delete own or any (instructor)
  PATCH  /api/chats/groups/{group_id}/messages/{message_id}/pin     → pin a message (instructor)
  GET    /api/chats/groups/{group_id}/members                       → member list
  PATCH  /api/chats/groups/{group_id}/read                          → mark group as read

Helper:
  GET    /api/chats/groups/by-batch?course_id=&batch_name=         → get or create group for a batch
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.utils.security import get_current_user
from app.models.group_chat import GroupChat, GroupMessage, GroupMessageLike, GroupMessageBookmark
from app.models.enrollment import Enrollment
from app.models.instructor_enrollment import InstructorEnrollment
from app.models.user import User
from app.models.course import Course
from app.schemas import (
    GroupMessageCreate, GroupMessageResponse, GroupMemberResponse
)

router = APIRouter(prefix="/api/chats/groups", tags=["Group / Batch Chat"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _verify_group_access(group: GroupChat, current_user: dict, db: Session):
    """Allow access if user is enrolled in the group's batch or is instructor/admin."""
    role = current_user.get("role")
    user_id = current_user["user_id"]

    if role in ("instructor", "admin"):
        return True

    enrolled = db.query(Enrollment).filter(
        Enrollment.user_id == user_id,
        Enrollment.course_id == group.course_id,
        Enrollment.batch_name == group.batch_name,
        Enrollment.status == "ongoing"
    ).first()
    if not enrolled:
        raise HTTPException(status_code=403, detail="You are not enrolled in this batch chat group.")
    return True


def _get_or_create_group(course_id: int, batch_name: str, db: Session) -> GroupChat:
    """Lazy creation of group chat for a batch."""
    group = db.query(GroupChat).filter(
        GroupChat.course_id == course_id,
        GroupChat.batch_name == batch_name
    ).first()
    if not group:
        group = GroupChat(course_id=course_id, batch_name=batch_name)
        db.add(group)
        db.commit()
        db.refresh(group)
    return group


def _build_group_message(msg: GroupMessage, current_user_id: int, db: Session) -> GroupMessageResponse:
    sender = db.query(User).filter(User.id == msg.sender_id).first()
    like_count = len(msg.likes)
    is_liked = any(l.user_id == current_user_id for l in msg.likes)
    is_bookmarked = any(b.user_id == current_user_id for b in msg.bookmarks)

    return GroupMessageResponse(
        id=msg.id,
        group_id=msg.group_id,
        sender_id=msg.sender_id,
        sender_name=sender.name if sender else "Unknown",
        sender_role=msg.sender_role,
        text=msg.text if msg.deleted_at is None else "This message was deleted",
        attachment_url=msg.attachment_url if msg.deleted_at is None else None,
        attachment_name=msg.attachment_name if msg.deleted_at is None else None,
        is_pinned=msg.is_pinned,
        pinned_at=msg.pinned_at,
        created_at=msg.created_at,
        is_deleted=msg.deleted_at is not None,
        like_count=like_count,
        is_liked_by_me=is_liked,
        is_bookmarked_by_me=is_bookmarked,
    )


def _get_group_or_404(db: Session, group_id: int) -> GroupChat:
    group = db.query(GroupChat).filter(GroupChat.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group chat not found")
    return group


# ── GET /api/chats/groups/by-batch ───────────────────────────────────────────

@router.get("/by-batch", response_model=dict)
def get_group_by_batch(
    course_id: int = Query(...),
    batch_name: str = Query(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get (or lazily create) the group chat for a specific batch. Returns group_id."""
    group = _get_or_create_group(course_id, batch_name, db)
    _verify_group_access(group, current_user, db)
    return {"group_id": group.id, "course_id": group.course_id, "batch_name": group.batch_name}


# ── GET /api/chats/groups/{group_id}/messages ─────────────────────────────────

@router.get("/{group_id}/messages", response_model=List[GroupMessageResponse])
def get_group_messages(
    group_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Fetch group/batch messages (paginated). Includes pinned messages at top."""
    group = _get_group_or_404(db, group_id)
    _verify_group_access(group, current_user, db)

    # First page gets pinned messages prepended
    user_id = current_user["user_id"]

    if page == 1:
        pinned = (
            db.query(GroupMessage)
            .filter(GroupMessage.group_id == group_id, GroupMessage.is_pinned == True, GroupMessage.deleted_at == None)
            .order_by(GroupMessage.pinned_at.desc())
            .all()
        )
        pinned_ids = {m.id for m in pinned}
        regular = (
            db.query(GroupMessage)
            .filter(GroupMessage.group_id == group_id, GroupMessage.id.notin_(pinned_ids))
            .order_by(GroupMessage.created_at.desc())
            .offset(0)
            .limit(page_size)
            .all()
        )
        messages = pinned + regular
    else:
        pinned_ids_subq = (
            db.query(GroupMessage.id)
            .filter(GroupMessage.group_id == group_id, GroupMessage.is_pinned == True)
            .scalar_subquery()
        )
        messages = (
            db.query(GroupMessage)
            .filter(GroupMessage.group_id == group_id, GroupMessage.id.notin_(pinned_ids_subq))
            .order_by(GroupMessage.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

    return [_build_group_message(m, user_id, db) for m in messages]


# ── POST /api/chats/groups/{group_id}/messages ────────────────────────────────

@router.post("/{group_id}/messages", response_model=GroupMessageResponse, status_code=201)
def post_group_message(
    group_id: int,
    body: GroupMessageCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Post a message to the group. Body: text, attachments."""
    group = _get_group_or_404(db, group_id)
    _verify_group_access(group, current_user, db)

    if not body.text and not body.attachment_url:
        raise HTTPException(status_code=400, detail="Message must have text or attachment")

    msg = GroupMessage(
        group_id=group_id,
        sender_id=current_user["user_id"],
        sender_role=current_user.get("role", "student"),
        text=body.text,
        attachment_url=body.attachment_url,
        attachment_name=body.attachment_name,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return _build_group_message(msg, current_user["user_id"], db)


# ── DELETE /api/chats/groups/{group_id}/messages/{message_id} ────────────────

@router.delete("/{group_id}/messages/{message_id}")
def delete_group_message(
    group_id: int,
    message_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete own message (or any message if instructor). Soft delete."""
    user_id = current_user["user_id"]
    group = _get_group_or_404(db, group_id)
    _verify_group_access(group, current_user, db)

    msg = db.query(GroupMessage).filter(
        GroupMessage.id == message_id,
        GroupMessage.group_id == group_id
    ).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    is_instructor = current_user.get("role") == "instructor"
    if msg.sender_id != user_id and not is_instructor:
        raise HTTPException(status_code=403, detail="Cannot delete another user's message")

    msg.deleted_at = datetime.utcnow()
    db.commit()
    return {"message": "Message deleted"}


# ── PATCH /api/chats/groups/{group_id}/messages/{message_id}/pin ──────────────

@router.patch("/{group_id}/messages/{message_id}/pin")
def pin_group_message(
    group_id: int,
    message_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Pin a message in group chat. Students see it pinned at top. Instructor only."""
    if current_user.get("role") != "instructor":
        raise HTTPException(status_code=403, detail="Only instructors can pin messages")

    msg = db.query(GroupMessage).filter(
        GroupMessage.id == message_id,
        GroupMessage.group_id == group_id
    ).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    msg.is_pinned = not msg.is_pinned
    msg.pinned_at = datetime.utcnow() if msg.is_pinned else None
    db.commit()
    db.refresh(msg)

    return {
        "message_id": msg.id,
        "is_pinned": msg.is_pinned,
        "message": "Message pinned" if msg.is_pinned else "Message unpinned"
    }


# ── GET /api/chats/groups/{group_id}/members ──────────────────────────────────

@router.get("/{group_id}/members", response_model=List[GroupMemberResponse])
def get_group_members(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get member list for the group (right panel — name, avatar, role)."""
    group = _get_group_or_404(db, group_id)
    _verify_group_access(group, current_user, db)

    # Students enrolled in this batch
    enrollments = db.query(Enrollment).filter(
        Enrollment.course_id == group.course_id,
        Enrollment.batch_name == group.batch_name,
        Enrollment.status == "ongoing"
    ).all()

    members = []
    for e in enrollments:
        user = db.query(User).filter(User.id == e.user_id).first()
        if user:
            members.append(GroupMemberResponse(
                user_id=user.id,
                name=user.name,
                role=user.role,
                student_id=user.student_id,
                avatar_url=f"/api/users/{user.id}/avatar"
            ))

    # Also add instructors enrolled in this batch
    try:
        instructor_enrollments = db.query(InstructorEnrollment).filter(
            InstructorEnrollment.course_id == group.course_id,
            InstructorEnrollment.batch_name == group.batch_name
        ).all()
        for ie in instructor_enrollments:
            user = db.query(User).filter(User.id == ie.instructor_id).first()
            if user and not any(m.user_id == user.id for m in members):
                members.append(GroupMemberResponse(
                    user_id=user.id,
                    name=user.name,
                    role="instructor",
                    student_id=None,
                    avatar_url=f"/api/users/{user.id}/avatar"
                ))
    except Exception:
        pass  # InstructorEnrollment table may not exist in older deployments

    return members


# ── PATCH /api/chats/groups/{group_id}/read ───────────────────────────────────

@router.patch("/{group_id}/read")
def mark_group_read(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Mark group as read. Clears unread badge."""
    group = _get_group_or_404(db, group_id)
    _verify_group_access(group, current_user, db)
    # In a production system this would update a GroupReadReceipt table.
    # For now, return success — frontend tracks this client-side.
    return {"message": "Group marked as read", "group_id": group_id}


# ── Reactions on group messages ───────────────────────────────────────────────

@router.post("/messages/{message_id}/like")
def like_group_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Like a group message."""
    user_id = current_user["user_id"]
    msg = db.query(GroupMessage).filter(GroupMessage.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    _verify_group_access(_get_group_or_404(db, msg.group_id), current_user, db)

    existing = db.query(GroupMessageLike).filter(
        GroupMessageLike.message_id == message_id,
        GroupMessageLike.user_id == user_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already liked")

    db.add(GroupMessageLike(message_id=message_id, user_id=user_id))
    db.commit()
    like_count = db.query(GroupMessageLike).filter(GroupMessageLike.message_id == message_id).count()
    return {"liked": True, "like_count": like_count}


@router.delete("/messages/{message_id}/like")
def unlike_group_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Remove like from a group message."""
    user_id = current_user["user_id"]
    existing = db.query(GroupMessageLike).filter(
        GroupMessageLike.message_id == message_id,
        GroupMessageLike.user_id == user_id
    ).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Like not found")

    db.delete(existing)
    db.commit()
    like_count = db.query(GroupMessageLike).filter(GroupMessageLike.message_id == message_id).count()
    return {"liked": False, "like_count": like_count}


@router.patch("/messages/{message_id}/bookmark")
def bookmark_group_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Bookmark / unbookmark a group message."""
    user_id = current_user["user_id"]
    msg = db.query(GroupMessage).filter(GroupMessage.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    existing = db.query(GroupMessageBookmark).filter(
        GroupMessageBookmark.message_id == message_id,
        GroupMessageBookmark.user_id == user_id
    ).first()
    if existing:
        db.delete(existing)
        db.commit()
        return {"bookmarked": False}
    else:
        db.add(GroupMessageBookmark(message_id=message_id, user_id=user_id))
        db.commit()
        return {"bookmarked": True}

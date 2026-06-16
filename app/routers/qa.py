# app/routers/qa.py
"""
Course Q&A – New API (matching Claude's spec)
=============================================
URL: /api/courses/{course_id}/qa

Endpoints:
  GET    /api/courses/{course_id}/qa                                     → paginated Q&A feed
  POST   /api/courses/{course_id}/qa                                     → post a new question
  DELETE /api/courses/{course_id}/qa/{question_id}                       → delete question
  PATCH  /api/courses/{course_id}/qa/{question_id}/pin                   → pin/unpin (instructor)
  PATCH  /api/courses/{course_id}/qa/{question_id}/bookmark              → bookmark/unbookmark
  PATCH  /api/courses/{course_id}/qa/{question_id}/visibility            → change visibility (instructor)
  POST   /api/courses/{course_id}/qa/{question_id}/like                  → like a question
  DELETE /api/courses/{course_id}/qa/{question_id}/like                  → unlike a question

  GET    /api/courses/{course_id}/qa/{question_id}/replies               → get all replies
  POST   /api/courses/{course_id}/qa/{question_id}/replies               → post a reply
  DELETE /api/courses/{course_id}/qa/{question_id}/replies/{reply_id}    → delete own reply
  POST   /api/courses/{course_id}/qa/{question_id}/replies/{reply_id}/like   → like a reply
  DELETE /api/courses/{course_id}/qa/{question_id}/replies/{reply_id}/like   → unlike a reply
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict

from app.database import get_db
from app.utils.security import get_current_user
from app.models.chat import ChatPost, ChatReply, ChatLike, ChatBookmark, ChatReplyLike
from app.models.enrollment import Enrollment
from app.models.user import User
from app.schemas import (
    ChatPostCreate, ChatPostResponse, ChatReplyCreate, ChatReplyResponse,
    ChatAuthor, QAVisibilityUpdate
)

router = APIRouter(prefix="/api/courses", tags=["Course Q&A"])


# ── Inline schema for new-style post creation ─────────────────────────────────

class QAPostCreate(BaseModel):
    title: Optional[str] = None
    description: str
    visibility: str = "public"  # 'public' | 'private'


class QAPostResponse(BaseModel):
    id: int
    course_id: int
    batch_name: str
    title: Optional[str]
    content: str
    visibility: str
    created_at: datetime
    updated_at: datetime
    is_pinned: bool
    pinned_at: Optional[datetime]
    author: ChatAuthor
    is_instructor: bool
    like_count: int
    reply_count: int
    is_liked_by_me: bool
    is_bookmarked_by_me: bool

    model_config = ConfigDict(from_attributes=True)


class QAReplyResponse(BaseModel):
    id: int
    post_id: int
    content: str
    created_at: datetime
    updated_at: datetime
    is_instructor: bool
    like_count: int
    is_liked_by_me: bool
    author: ChatAuthor

    model_config = ConfigDict(from_attributes=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_or_fail(db: Session, course_id: int) -> None:
    """Check that the course exists."""
    from app.models.course import Course
    c = db.query(Course).filter(Course.id == course_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Course not found")


def _verify_access(course_id: int, batch_name: str, current_user: dict, db: Session):
    role = current_user.get("role")
    if role in ("instructor", "admin"):
        return True
    enrolled = db.query(Enrollment).filter(
        Enrollment.user_id == current_user["user_id"],
        Enrollment.course_id == course_id,
        Enrollment.batch_name == batch_name,
        Enrollment.status == "ongoing"
    ).first()
    if not enrolled:
        raise HTTPException(status_code=403, detail="You are not enrolled in this batch.")
    return True


def _build_author(user: User) -> ChatAuthor:
    return ChatAuthor(id=user.id, name=user.name, role=user.role, student_id=user.student_id)


def _build_reply_response(reply: ChatReply, current_user_id: int, db: Session) -> QAReplyResponse:
    author = db.query(User).filter(User.id == reply.author_id).first()
    like_count = len(reply.reply_likes)
    is_liked = any(lk.user_id == current_user_id for lk in reply.reply_likes)
    return QAReplyResponse(
        id=reply.id,
        post_id=reply.post_id,
        content=reply.content,
        created_at=reply.created_at,
        updated_at=reply.updated_at,
        is_instructor=(reply.author_role == "instructor"),
        like_count=like_count,
        is_liked_by_me=is_liked,
        author=_build_author(author) if author else ChatAuthor(id=reply.author_id, name="Unknown", role=reply.author_role, student_id=None)
    )


def _build_post_response(post: ChatPost, current_user_id: int, db: Session) -> QAPostResponse:
    like_count = len(post.likes)
    reply_count = len(post.replies)
    is_liked = any(lk.user_id == current_user_id for lk in post.likes)
    is_bookmarked = any(bk.user_id == current_user_id for bk in post.bookmarks)
    author = db.query(User).filter(User.id == post.author_id).first()

    return QAPostResponse(
        id=post.id,
        course_id=post.course_id,
        batch_name=post.batch_name,
        title=None,   # ChatPost model has no title field yet – use content as description
        content=post.content,
        visibility=getattr(post, "visibility", "public"),
        created_at=post.created_at,
        updated_at=post.updated_at,
        is_pinned=post.is_pinned,
        pinned_at=post.pinned_at,
        author=_build_author(author) if author else ChatAuthor(id=post.author_id, name="Unknown", role=post.author_role, student_id=None),
        is_instructor=(post.author_role == "instructor"),
        like_count=like_count,
        reply_count=reply_count,
        is_liked_by_me=is_liked,
        is_bookmarked_by_me=is_bookmarked,
    )


# ── GET /api/courses/{course_id}/qa ──────────────────────────────────────────

@router.get("/{course_id}/qa", response_model=List[QAPostResponse])
def get_qa_feed(
    course_id: int,
    batch_name: str = Query(..., description="Filter by batch name"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter: 'pinned' | 'bookmarked'"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Fetch all Q&A posts (paginated). Filter by date & status.
    Visibility: instructors see all; students only see 'public' posts.
    """
    _get_or_fail(db, course_id)
    _verify_access(course_id, batch_name, current_user, db)

    q = db.query(ChatPost).filter(
        ChatPost.course_id == course_id,
        ChatPost.batch_name == batch_name
    )

    # Students only see public posts
    if current_user.get("role") == "student":
        q = q.filter(ChatPost.visibility == "public")

    if status == "pinned":
        q = q.filter(ChatPost.is_pinned == True)
    elif status == "bookmarked":
        bookmarked_ids = [
            b.post_id for b in db.query(ChatBookmark).filter(
                ChatBookmark.user_id == current_user["user_id"]
            ).all()
        ]
        q = q.filter(ChatPost.id.in_(bookmarked_ids))

    q = q.order_by(ChatPost.is_pinned.desc(), ChatPost.created_at.desc())
    posts = q.offset((page - 1) * page_size).limit(page_size).all()

    return [_build_post_response(p, current_user["user_id"], db) for p in posts]


# ── POST /api/courses/{course_id}/qa ─────────────────────────────────────────

@router.post("/{course_id}/qa", response_model=QAPostResponse, status_code=201)
def create_qa_post(
    course_id: int,
    body: QAPostCreate,
    batch_name: str = Query(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Post a new question.
    visibility='public'  → all batch students can see.
    visibility='private' → only instructor sees (sent as DM to instructor).
    """
    _get_or_fail(db, course_id)
    _verify_access(course_id, batch_name, current_user, db)

    post = ChatPost(
        course_id=course_id,
        batch_name=batch_name,
        author_id=current_user["user_id"],
        author_role=current_user.get("role", "student"),
        content=body.description,
        visibility=body.visibility,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return _build_post_response(post, current_user["user_id"], db)


# ── DELETE /api/courses/{course_id}/qa/{question_id} ─────────────────────────

@router.delete("/{course_id}/qa/{question_id}")
def delete_qa_post(
    course_id: int,
    question_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a question (own post or instructor)."""
    post = db.query(ChatPost).filter(
        ChatPost.id == question_id,
        ChatPost.course_id == course_id
    ).first()
    if not post:
        raise HTTPException(status_code=404, detail="Question not found")

    is_instructor = current_user.get("role") == "instructor"
    if post.author_id != current_user["user_id"] and not is_instructor:
        raise HTTPException(status_code=403, detail="Cannot delete another user's question.")

    db.delete(post)
    db.commit()
    return {"message": "Question deleted"}


# ── PATCH /api/courses/{course_id}/qa/{question_id}/pin ──────────────────────

@router.patch("/{course_id}/qa/{question_id}/pin")
def pin_qa_post(
    course_id: int,
    question_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Pin / unpin a question. Instructor only."""
    if current_user.get("role") != "instructor":
        raise HTTPException(status_code=403, detail="Only instructors can pin questions.")

    post = db.query(ChatPost).filter(
        ChatPost.id == question_id,
        ChatPost.course_id == course_id
    ).first()
    if not post:
        raise HTTPException(status_code=404, detail="Question not found")

    post.is_pinned = not post.is_pinned
    post.pinned_at = datetime.utcnow() if post.is_pinned else None
    db.commit()
    db.refresh(post)

    return {"question_id": post.id, "is_pinned": post.is_pinned,
            "message": "Pinned" if post.is_pinned else "Unpinned"}


# ── PATCH /api/courses/{course_id}/qa/{question_id}/bookmark ─────────────────

@router.patch("/{course_id}/qa/{question_id}/bookmark")
def bookmark_qa_post(
    course_id: int,
    question_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Bookmark / unbookmark a question for self."""
    post = db.query(ChatPost).filter(ChatPost.id == question_id, ChatPost.course_id == course_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Question not found")

    existing = db.query(ChatBookmark).filter(
        ChatBookmark.post_id == question_id,
        ChatBookmark.user_id == current_user["user_id"]
    ).first()

    if existing:
        db.delete(existing)
        db.commit()
        return {"bookmarked": False}
    else:
        db.add(ChatBookmark(post_id=question_id, user_id=current_user["user_id"]))
        db.commit()
        return {"bookmarked": True}


# ── PATCH /api/courses/{course_id}/qa/{question_id}/visibility ───────────────

@router.patch("/{course_id}/qa/{question_id}/visibility")
def update_qa_visibility(
    course_id: int,
    question_id: int,
    body: QAVisibilityUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Change visibility of a question after posting. Instructor only."""
    if current_user.get("role") != "instructor":
        raise HTTPException(status_code=403, detail="Only instructors can change visibility.")

    if body.visibility not in ("public", "private"):
        raise HTTPException(status_code=400, detail="visibility must be 'public' or 'private'")

    post = db.query(ChatPost).filter(
        ChatPost.id == question_id,
        ChatPost.course_id == course_id
    ).first()
    if not post:
        raise HTTPException(status_code=404, detail="Question not found")

    post.visibility = body.visibility
    db.commit()
    return {"question_id": post.id, "visibility": post.visibility}


# ── POST /api/courses/{course_id}/qa/{question_id}/like ──────────────────────

@router.post("/{course_id}/qa/{question_id}/like")
def like_qa_post(
    course_id: int,
    question_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Like a question post."""
    post = db.query(ChatPost).filter(ChatPost.id == question_id, ChatPost.course_id == course_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Question not found")

    existing = db.query(ChatLike).filter(
        ChatLike.post_id == question_id, ChatLike.user_id == current_user["user_id"]
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already liked")

    db.add(ChatLike(post_id=question_id, user_id=current_user["user_id"]))
    db.commit()
    like_count = db.query(ChatLike).filter(ChatLike.post_id == question_id).count()
    return {"liked": True, "like_count": like_count}


# ── DELETE /api/courses/{course_id}/qa/{question_id}/like ────────────────────

@router.delete("/{course_id}/qa/{question_id}/like")
def unlike_qa_post(
    course_id: int,
    question_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Unlike a question post."""
    existing = db.query(ChatLike).filter(
        ChatLike.post_id == question_id, ChatLike.user_id == current_user["user_id"]
    ).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Like not found")

    db.delete(existing)
    db.commit()
    like_count = db.query(ChatLike).filter(ChatLike.post_id == question_id).count()
    return {"liked": False, "like_count": like_count}


# ── GET /api/courses/{course_id}/qa/{question_id}/replies ────────────────────

@router.get("/{course_id}/qa/{question_id}/replies", response_model=List[QAReplyResponse])
def get_qa_replies(
    course_id: int,
    question_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all replies/answers for a question."""
    post = db.query(ChatPost).filter(ChatPost.id == question_id, ChatPost.course_id == course_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Question not found")

    replies = db.query(ChatReply).filter(
        ChatReply.post_id == question_id
    ).order_by(ChatReply.created_at.asc()).all()

    return [_build_reply_response(r, current_user["user_id"], db) for r in replies]


# ── POST /api/courses/{course_id}/qa/{question_id}/replies ───────────────────

@router.post("/{course_id}/qa/{question_id}/replies", response_model=QAReplyResponse, status_code=201)
def post_qa_reply(
    course_id: int,
    question_id: int,
    body: ChatReplyCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Post an answer/reply to a question."""
    post = db.query(ChatPost).filter(ChatPost.id == question_id, ChatPost.course_id == course_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Question not found")

    role = current_user.get("role", "student")
    reply = ChatReply(
        post_id=question_id,
        author_id=current_user["user_id"],
        author_role=role,
        content=body.content,
    )
    db.add(reply)
    db.commit()
    db.refresh(reply)

    return _build_reply_response(reply, current_user["user_id"], db)


# ── DELETE /api/courses/{course_id}/qa/{question_id}/replies/{reply_id} ──────

@router.delete("/{course_id}/qa/{question_id}/replies/{reply_id}")
def delete_qa_reply(
    course_id: int,
    question_id: int,
    reply_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete own reply."""
    reply = db.query(ChatReply).filter(
        ChatReply.id == reply_id, ChatReply.post_id == question_id
    ).first()
    if not reply:
        raise HTTPException(status_code=404, detail="Reply not found")

    is_instructor = current_user.get("role") == "instructor"
    if reply.author_id != current_user["user_id"] and not is_instructor:
        raise HTTPException(status_code=403, detail="Cannot delete another user's reply.")

    db.delete(reply)
    db.commit()
    return {"message": "Reply deleted"}


# ── POST /api/courses/{course_id}/qa/{question_id}/replies/{reply_id}/like ───

@router.post("/{course_id}/qa/{question_id}/replies/{reply_id}/like")
def like_qa_reply(
    course_id: int,
    question_id: int,
    reply_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Like a reply."""
    reply = db.query(ChatReply).filter(
        ChatReply.id == reply_id, ChatReply.post_id == question_id
    ).first()
    if not reply:
        raise HTTPException(status_code=404, detail="Reply not found")

    existing = db.query(ChatReplyLike).filter(
        ChatReplyLike.reply_id == reply_id,
        ChatReplyLike.user_id == current_user["user_id"]
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already liked")

    db.add(ChatReplyLike(reply_id=reply_id, user_id=current_user["user_id"]))
    db.commit()
    like_count = db.query(ChatReplyLike).filter(ChatReplyLike.reply_id == reply_id).count()
    return {"liked": True, "like_count": like_count}


# ── DELETE /api/courses/{course_id}/qa/{question_id}/replies/{reply_id}/like ─

@router.delete("/{course_id}/qa/{question_id}/replies/{reply_id}/like")
def unlike_qa_reply(
    course_id: int,
    question_id: int,
    reply_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Unlike a reply."""
    existing = db.query(ChatReplyLike).filter(
        ChatReplyLike.reply_id == reply_id,
        ChatReplyLike.user_id == current_user["user_id"]
    ).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Like not found")

    db.delete(existing)
    db.commit()
    like_count = db.query(ChatReplyLike).filter(ChatReplyLike.reply_id == reply_id).count()
    return {"liked": False, "like_count": like_count}

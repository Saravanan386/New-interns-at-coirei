# app/routers/chat.py
"""
Course Q&A Chat API
====================
Batch-scoped Q&A feed – only students enrolled in the batch (and the course instructor)
can post and view messages.

Endpoints:
  GET  /chat/{course_id}/{batch_name}                    → paginated post feed
  POST /chat/{course_id}/{batch_name}                    → create a new post
  GET  /chat/{course_id}/{batch_name}/{post_id}          → single post + replies
  DELETE /chat/{course_id}/{batch_name}/{post_id}        → delete own post (or instructor deletes any)

  POST /chat/{course_id}/{batch_name}/{post_id}/replies  → reply to a post
  DELETE /chat/{course_id}/{batch_name}/replies/{reply_id} → delete reply

  POST /chat/{course_id}/{batch_name}/{post_id}/like     → toggle like
  POST /chat/{course_id}/{batch_name}/{post_id}/bookmark → toggle bookmark
  GET  /chat/{course_id}/{batch_name}/bookmarks          → logged-in user's bookmarked posts

  POST /chat/{course_id}/{batch_name}/{post_id}/pin      → instructor pin/unpin
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.utils.security import get_current_user
from app.models.chat import ChatPost, ChatReply, ChatLike, ChatBookmark
from app.models.enrollment import Enrollment
from app.models.user import User
from app.models.course import Course
from app.schemas import ChatPostCreate, ChatPostResponse, ChatReplyCreate, ChatReplyResponse, ChatAuthor

router = APIRouter(prefix="/chat", tags=["Chat / Q&A"])


# ── Access Control ────────────────────────────────────────────────────────────

def _verify_access(course_id: int, batch_name: str, current_user: dict, db: Session):
    """
    Allow access if:
      - User is instructor (can post to any batch)
      - User is admin
      - User is a student enrolled in this specific course + batch
    """
    role = current_user.get("role")
    if role in ("instructor", "admin"):
        return True

    # Student must be enrolled in the batch
    enrolled = db.query(Enrollment).filter(
        Enrollment.user_id == current_user["user_id"],
        Enrollment.course_id == course_id,
        Enrollment.batch_name == batch_name,
        Enrollment.status == "ongoing"
    ).first()

    if not enrolled:
        raise HTTPException(
            status_code=403,
            detail="You are not enrolled in this batch."
        )
    return True


def _build_author(user: User) -> ChatAuthor:
    return ChatAuthor(
        id=user.id,
        name=user.name,
        role=user.role,
        student_id=user.student_id
    )


def _build_post_response(
    post: ChatPost,
    current_user_id: int,
    db: Session
) -> ChatPostResponse:
    """Construct the full ChatPostResponse including computed fields."""
    like_count = len(post.likes)
    reply_count = len(post.replies)
    is_liked = any(lk.user_id == current_user_id for lk in post.likes)
    is_bookmarked = any(bk.user_id == current_user_id for bk in post.bookmarks)

    replies = []
    for r in sorted(post.replies, key=lambda x: x.created_at):
        author = db.query(User).filter(User.id == r.author_id).first()
        replies.append(ChatReplyResponse(
            id=r.id,
            post_id=r.post_id,
            content=r.content,
            created_at=r.created_at,
            updated_at=r.updated_at,
            is_instructor=(r.author_role == "instructor"),
            author=_build_author(author) if author else ChatAuthor(id=r.author_id, name="Unknown", role=r.author_role, student_id=None)
        ))

    post_author = db.query(User).filter(User.id == post.author_id).first()

    return ChatPostResponse(
        id=post.id,
        course_id=post.course_id,
        batch_name=post.batch_name,
        content=post.content,
        created_at=post.created_at,
        updated_at=post.updated_at,
        is_pinned=post.is_pinned,
        pinned_at=post.pinned_at,
        author=_build_author(post_author) if post_author else ChatAuthor(id=post.author_id, name="Unknown", role=post.author_role, student_id=None),
        is_instructor=(post.author_role == "instructor"),
        like_count=like_count,
        reply_count=reply_count,
        is_liked_by_me=is_liked,
        is_bookmarked_by_me=is_bookmarked,
        replies=replies
    )


# ── Feed: List Posts ──────────────────────────────────────────────────────────

@router.get("/{course_id}/{batch_name}", response_model=List[ChatPostResponse])
def get_post_feed(
    course_id: int,
    batch_name: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    pinned_first: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Returns the batch Q&A feed (paginated).
    Pinned posts appear first by default (matching the 'Pinned by Instructor' badge in UI).
    Every post includes: author info, is_instructor flag, like count, reply count,
    is_liked_by_me, is_bookmarked_by_me, and all replies.
    """
    _verify_access(course_id, batch_name, current_user, db)

    q = db.query(ChatPost).filter(
        ChatPost.course_id == course_id,
        ChatPost.batch_name == batch_name
    )

    if pinned_first:
        q = q.order_by(ChatPost.is_pinned.desc(), ChatPost.created_at.desc())
    else:
        q = q.order_by(ChatPost.created_at.desc())

    offset = (page - 1) * page_size
    posts = q.offset(offset).limit(page_size).all()

    return [_build_post_response(p, current_user["user_id"], db) for p in posts]


# ── Create Post ───────────────────────────────────────────────────────────────

@router.post("/{course_id}/{batch_name}", response_model=ChatPostResponse, status_code=201)
def create_post(
    course_id: int,
    batch_name: str,
    body: ChatPostCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new Q&A post in the batch feed.
    - Students can only post to batches they are enrolled in.
    - Instructor can post to any batch (their posts get the blue 'Instructor' badge).
    """
    _verify_access(course_id, batch_name, current_user, db)

    post = ChatPost(
        course_id=course_id,
        batch_name=batch_name,
        author_id=current_user["user_id"],
        author_role=current_user.get("role", "student"),
        content=body.content,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return _build_post_response(post, current_user["user_id"], db)


# ── Get Single Post + Replies ─────────────────────────────────────────────────

@router.get("/{course_id}/{batch_name}/{post_id}", response_model=ChatPostResponse)
def get_post(
    course_id: int,
    batch_name: str,
    post_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    _verify_access(course_id, batch_name, current_user, db)

    post = db.query(ChatPost).filter(
        ChatPost.id == post_id,
        ChatPost.course_id == course_id,
        ChatPost.batch_name == batch_name
    ).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    return _build_post_response(post, current_user["user_id"], db)


# ── Delete Post ───────────────────────────────────────────────────────────────

@router.delete("/{course_id}/{batch_name}/{post_id}")
def delete_post(
    course_id: int,
    batch_name: str,
    post_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Author can delete own post; instructor can delete any post."""
    _verify_access(course_id, batch_name, current_user, db)

    post = db.query(ChatPost).filter(
        ChatPost.id == post_id,
        ChatPost.course_id == course_id,
        ChatPost.batch_name == batch_name
    ).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    is_instructor = current_user.get("role") == "instructor"
    if post.author_id != current_user["user_id"] and not is_instructor:
        raise HTTPException(status_code=403, detail="Cannot delete another student's post.")

    db.delete(post)
    db.commit()
    return {"message": "Post deleted"}


# ── Reply to a Post ───────────────────────────────────────────────────────────

@router.post("/{course_id}/{batch_name}/{post_id}/replies", response_model=ChatReplyResponse, status_code=201)
def add_reply(
    course_id: int,
    batch_name: str,
    post_id: int,
    body: ChatReplyCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Reply to a post.
    - Instructor replies are flagged is_instructor=True → shown with the blue badge.
    - Students can only reply in their own batch.
    """
    _verify_access(course_id, batch_name, current_user, db)

    post = db.query(ChatPost).filter(
        ChatPost.id == post_id,
        ChatPost.course_id == course_id,
        ChatPost.batch_name == batch_name
    ).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    role = current_user.get("role", "student")
    reply = ChatReply(
        post_id=post_id,
        author_id=current_user["user_id"],
        author_role=role,
        content=body.content,
    )
    db.add(reply)
    db.commit()
    db.refresh(reply)

    author = db.query(User).filter(User.id == reply.author_id).first()
    return ChatReplyResponse(
        id=reply.id,
        post_id=reply.post_id,
        content=reply.content,
        created_at=reply.created_at,
        updated_at=reply.updated_at,
        is_instructor=(role == "instructor"),
        author=_build_author(author)
    )


# ── Delete Reply ──────────────────────────────────────────────────────────────

@router.delete("/{course_id}/{batch_name}/replies/{reply_id}")
def delete_reply(
    course_id: int,
    batch_name: str,
    reply_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    reply = db.query(ChatReply).filter(ChatReply.id == reply_id).first()
    if not reply:
        raise HTTPException(status_code=404, detail="Reply not found")

    is_instructor = current_user.get("role") == "instructor"
    if reply.author_id != current_user["user_id"] and not is_instructor:
        raise HTTPException(status_code=403, detail="Cannot delete another user's reply.")

    db.delete(reply)
    db.commit()
    return {"message": "Reply deleted"}


# ── Like / Unlike (Toggle) ────────────────────────────────────────────────────

@router.post("/{course_id}/{batch_name}/{post_id}/like")
def toggle_like(
    course_id: int,
    batch_name: str,
    post_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Toggle like on a post.
    Returns { liked: true, like_count: N } or { liked: false, like_count: N }.
    """
    _verify_access(course_id, batch_name, current_user, db)

    post = db.query(ChatPost).filter(ChatPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    existing = db.query(ChatLike).filter(
        ChatLike.post_id == post_id,
        ChatLike.user_id == current_user["user_id"]
    ).first()

    if existing:
        db.delete(existing)
        db.commit()
        liked = False
    else:
        db.add(ChatLike(post_id=post_id, user_id=current_user["user_id"]))
        db.commit()
        liked = True

    like_count = db.query(ChatLike).filter(ChatLike.post_id == post_id).count()
    return {"liked": liked, "like_count": like_count}


# ── Bookmark / Unbookmark (Toggle) ────────────────────────────────────────────

@router.post("/{course_id}/{batch_name}/{post_id}/bookmark")
def toggle_bookmark(
    course_id: int,
    batch_name: str,
    post_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Toggle bookmark on a post."""
    _verify_access(course_id, batch_name, current_user, db)

    post = db.query(ChatPost).filter(ChatPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    existing = db.query(ChatBookmark).filter(
        ChatBookmark.post_id == post_id,
        ChatBookmark.user_id == current_user["user_id"]
    ).first()

    if existing:
        db.delete(existing)
        db.commit()
        bookmarked = False
    else:
        db.add(ChatBookmark(post_id=post_id, user_id=current_user["user_id"]))
        db.commit()
        bookmarked = True

    return {"bookmarked": bookmarked}


# ── My Bookmarks ──────────────────────────────────────────────────────────────

@router.get("/{course_id}/{batch_name}/bookmarks/my", response_model=List[ChatPostResponse])
def my_bookmarks(
    course_id: int,
    batch_name: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Returns all posts the current user has bookmarked in this batch."""
    _verify_access(course_id, batch_name, current_user, db)

    bookmarks = db.query(ChatBookmark).filter(
        ChatBookmark.user_id == current_user["user_id"]
    ).all()
    post_ids = [b.post_id for b in bookmarks]

    posts = db.query(ChatPost).filter(
        ChatPost.id.in_(post_ids),
        ChatPost.course_id == course_id,
        ChatPost.batch_name == batch_name
    ).order_by(ChatPost.created_at.desc()).all()

    return [_build_post_response(p, current_user["user_id"], db) for p in posts]


# ── Pin / Unpin Post (Instructor only) ───────────────────────────────────────

@router.post("/{course_id}/{batch_name}/{post_id}/pin")
def toggle_pin(
    course_id: int,
    batch_name: str,
    post_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Instructor only: toggle pin on a post.
    Pinned posts appear at the top with 'Pinned by Instructor' badge.
    """
    if current_user.get("role") != "instructor":
        raise HTTPException(status_code=403, detail="Only instructors can pin posts.")

    post = db.query(ChatPost).filter(
        ChatPost.id == post_id,
        ChatPost.course_id == course_id,
        ChatPost.batch_name == batch_name
    ).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    post.is_pinned = not post.is_pinned
    post.pinned_at = datetime.utcnow() if post.is_pinned else None
    db.commit()
    db.refresh(post)

    return {
        "post_id": post.id,
        "is_pinned": post.is_pinned,
        "message": "Post pinned" if post.is_pinned else "Post unpinned"
    }

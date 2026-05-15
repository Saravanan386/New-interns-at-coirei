# app/routers/chat_uploads.py
"""
Chat File / Image Upload API
============================
URL prefix: /api/uploads

Endpoints:
  POST /api/uploads/chat              → Upload image or file before sending. Returns file URL.
  GET  /api/uploads/{file_id}         → Retrieve/preview an uploaded file by its ID.
"""

import os
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse

from app.utils.security import get_current_user
from app.schemas import ChatUploadResponse

router = APIRouter(prefix="/api/uploads", tags=["Chat File Upload"])

# Base upload directory (relative to project root)
UPLOAD_BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", "chat")
MAX_FILE_SIZE_MB = 20
ALLOWED_TYPES = {
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "application/pdf", "text/plain",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/zip",
}

os.makedirs(UPLOAD_BASE_DIR, exist_ok=True)


# ── POST /api/uploads/chat ────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatUploadResponse, status_code=201)
async def upload_chat_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload image or file before sending a chat message.
    Returns a file URL to include in the message body.
    Body: multipart/form-data with 'file' field. Max size 20MB.
    """
    # Validate content type
    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"File type '{content_type}' not allowed. Allowed: images, PDF, Word, Excel, ZIP."
        )

    # Read file content
    content = await file.read()
    file_size = len(content)

    if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE_MB}MB."
        )

    if file_size == 0:
        raise HTTPException(status_code=400, detail="Empty file not allowed")

    # Generate a unique file ID and preserve extension
    ext = os.path.splitext(file.filename or "file")[1] or ""
    file_id = str(uuid.uuid4())
    save_name = f"{file_id}{ext}"
    save_path = os.path.join(UPLOAD_BASE_DIR, save_name)

    with open(save_path, "wb") as f:
        f.write(content)

    file_url = f"/api/uploads/{file_id}"

    return ChatUploadResponse(
        file_id=file_id,
        file_url=file_url,
        file_name=file.filename or save_name,
        file_size=file_size,
        content_type=content_type,
    )


# ── GET /api/uploads/{file_id} ───────────────────────────────────────────────

@router.get("/{file_id}")
def get_uploaded_file(
    file_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Retrieve / preview an uploaded file by its ID.
    Works for images (inline preview) and other files (download).
    """
    # Basic UUID validation to prevent path traversal
    try:
        uuid.UUID(file_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file ID")

    # Search for the file (any extension)
    matched_file = None
    for fname in os.listdir(UPLOAD_BASE_DIR):
        if fname.startswith(file_id):
            matched_file = fname
            break

    if not matched_file:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = os.path.join(UPLOAD_BASE_DIR, matched_file)
    return FileResponse(path=file_path, filename=matched_file)

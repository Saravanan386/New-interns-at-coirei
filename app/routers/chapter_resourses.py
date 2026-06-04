import os
import uuid
import shutil

from typing import List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File
)

from fastapi.responses import FileResponse

from sqlalchemy.orm import Session

from app.database import get_db

from app.models.module import Chapter
from app.models.chapter_resources import ChapterResource

from app.schemas import (
    ChapterResourceResponse
)

from app.utils.security import get_current_user
def require_instructor(current_user: dict):
    if current_user.get("role") != "instructor":
        raise HTTPException(status_code=403, detail="Instructor access required.")



router = APIRouter(
    prefix="/chapter-resources",
    tags=["Chapter Resources"]
)

UPLOAD_DIR = "uploads/chapters"




@router.post(
    "/{chapter_id}",
    response_model=List[ChapterResourceResponse]
)
def upload_chapter_resources(
    chapter_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    require_instructor(current_user)

    chapter = (
        db.query(Chapter)
        .filter(Chapter.id == chapter_id)
        .first()
    )

    if not chapter:
        raise HTTPException(
            status_code=404,
            detail="Chapter not found"
        )

    folder = os.path.join(
        UPLOAD_DIR,
        str(chapter_id)
    )

    os.makedirs(folder, exist_ok=True)

    saved = []

    for file in files:

        ext = os.path.splitext(file.filename)[1]

        unique_name = (
            f"{uuid.uuid4().hex}{ext}"
        )

        destination = os.path.join(
            folder,
            unique_name
        )

        with open(destination, "wb") as buffer:
            shutil.copyfileobj(
                file.file,
                buffer
            )

        resource = ChapterResource(
            chapter_id=chapter_id,
            file_name=file.filename,
            file_path=destination,
            file_size=str(file.size)
            if hasattr(file, "size")
            else None
        )

        db.add(resource)
        db.flush()

        saved.append(resource)

    db.commit()

    for item in saved:
        db.refresh(item)

    return saved



@router.post(
    "/{chapter_id}",
    response_model=List[ChapterResourceResponse]
)
def upload_chapter_resources(
    chapter_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    require_instructor(current_user)

    chapter = (
        db.query(Chapter)
        .filter(Chapter.id == chapter_id)
        .first()
    )

    if not chapter:
        raise HTTPException(
            status_code=404,
            detail="Chapter not found"
        )

    folder = os.path.join(
        UPLOAD_DIR,
        str(chapter_id)
    )

    os.makedirs(folder, exist_ok=True)

    saved = []

    for file in files:

        ext = os.path.splitext(file.filename)[1]

        unique_name = (
            f"{uuid.uuid4().hex}{ext}"
        )

        destination = os.path.join(
            folder,
            unique_name
        )

        with open(destination, "wb") as buffer:
            shutil.copyfileobj(
                file.file,
                buffer
            )

        resource = ChapterResource(
            chapter_id=chapter_id,
            file_name=file.filename,
            file_path=destination,
            file_size=str(file.size)
            if hasattr(file, "size")
            else None
        )

        db.add(resource)
        db.flush()

        saved.append(resource)

    db.commit()

    for item in saved:
        db.refresh(item)

    return saved


@router.get("/download/{resource_id}")
def download_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    resource = (
        db.query(ChapterResource)
        .filter(
            ChapterResource.id == resource_id
        )
        .first()
    )

    if not resource:
        raise HTTPException(
            status_code=404,
            detail="Resource not found"
        )

    if not os.path.exists(resource.file_path):
        raise HTTPException(
            status_code=404,
            detail="File missing on server"
        )

    return FileResponse(
        path=resource.file_path,
        filename=resource.file_name
    )
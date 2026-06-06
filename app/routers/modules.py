from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.assignment import Assignment
from app.models.module import Chapter, Module
from app.schemas import (
    ChapterCreate,
    ChapterResponse,
    ModuleCreate,
    ModuleResponse,
)
from app.utils.security import get_current_user


router = APIRouter(prefix="/modules", tags=["Modules"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_instructor(current_user: dict):
    if current_user.get("role") != "instructor":
        raise HTTPException(status_code=403, detail="Not authorized. Instructor only.")


@router.post("/", response_model=ModuleResponse)
def create_module(
    module: ModuleCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    check_instructor(current_user)

    new_module = Module(
        title=module.title,
        order=module.order,
        course_id=module.course_id,
        batch_name=module.batch_name,
    )
    db.add(new_module)
    db.commit()
    db.refresh(new_module)
    return new_module


@router.post("/{module_id}/chapters", response_model=ChapterResponse)
def add_chapter(
    module_id: int,
    chapter: ChapterCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    check_instructor(current_user)

    db_module = db.query(Module).filter(Module.id == module_id).first()
    if not db_module:
        raise HTTPException(status_code=404, detail="Module not found")

    new_chapter = Chapter(
        title=chapter.title,
        order=chapter.order,
        class_content=chapter.class_content,
        key_topics=chapter.key_topics,
        module_id=module_id,
    )
    db.add(new_chapter)
    db.commit()
    db.refresh(new_chapter)
    return new_chapter


@router.get("/", response_model=List[ModuleResponse])
def get_modules(
    course_id: int = Query(..., description="Course ID to fetch modules for"),
    batch_name: Optional[str] = Query(None, description="Optional batch name to filter modules"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    query = db.query(Module).filter(Module.course_id == course_id)

    if batch_name:
        query = query.filter(or_(Module.batch_name == batch_name, Module.batch_name == None))

    return query.order_by(Module.order).all()


@router.put("/chapters/{chapter_id}", response_model=ChapterResponse)
def update_chapter(
    chapter_id: int,
    chapter: ChapterCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    check_instructor(current_user)

    db_chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not db_chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    db_chapter.title = chapter.title
    db_chapter.order = chapter.order
    db_chapter.class_content = chapter.class_content
    db_chapter.key_topics = chapter.key_topics

    db.commit()
    db.refresh(db_chapter)
    return db_chapter


@router.delete("/chapters/{chapter_id}")
def delete_chapter(
    chapter_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    check_instructor(current_user)

    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    db.delete(chapter)
    db.commit()

    return {"message": "Chapter deleted successfully"}


@router.get("/{module_id}/overview")
def module_overview(
    module_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    chapters = (
        db.query(Chapter)
        .filter(Chapter.module_id == module_id)
        .order_by(Chapter.order)
        .all()
    )

    return {
        "module_id": module.id,
        "title": module.title,
        "order": module.order,
        "course_id": module.course_id,
        "batch_name": module.batch_name,
        "total_chapters": len(chapters),
        "chapters": [
            {
                "chapter_id": chapter.id,
                "title": chapter.title,
                "order": chapter.order,
            }
            for chapter in chapters
        ],
    }


@router.delete("/{module_id}")
def delete_module(
    module_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    check_instructor(current_user)

    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    db.query(Assignment).filter(Assignment.module_id == module_id).delete(
        synchronize_session=False
    )
    db.delete(module)
    db.commit()

    return {"message": "Module and its associated assignments deleted successfully"}


@router.put("/{module_id}", response_model=ModuleResponse)
def update_module(
    module_id: int,
    module: ModuleCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    check_instructor(current_user)

    db_module = db.query(Module).filter(Module.id == module_id).first()
    if not db_module:
        raise HTTPException(status_code=404, detail="Module not found")

    db_module.title = module.title
    db_module.order = module.order
    db_module.batch_name = module.batch_name
    db_module.course_id = module.course_id

    db.commit()
    db.refresh(db_module)

    return db_module

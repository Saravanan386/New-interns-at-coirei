from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import SessionLocal
from app.utils.security import get_current_user
from app.models.module import Module, Chapter
from app.models.user import User
from app.schemas import (
    ModuleCreate, ModuleResponse,
    ChapterCreate, ChapterResponse
)

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

# --- INSTRUCTOR APIs ---

@router.post("/", response_model=ModuleResponse)
def create_module(
    module: ModuleCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_instructor(current_user)
    
    new_module = Module(
        title=module.title,
        order=module.order,
        course_id=module.course_id,
        batch_name=module.batch_name
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
    current_user: dict = Depends(get_current_user)
):
    check_instructor(current_user)
    
    db_module = db.query(Module).filter(Module.id == module_id).first()
    if not db_module:
        raise HTTPException(status_code=404, detail="Module not found")
        
    new_chapter = Chapter(title=chapter.title, order=chapter.order, module_id=module_id)
    db.add(new_chapter)
    db.commit()
    db.refresh(new_chapter)
    return new_chapter


# --- READ APIs (Instructor and Student) ---

@router.get("/", response_model=List[ModuleResponse])
def get_modules(
    course_id: int = Query(..., description="Course ID to fetch modules for"),
    batch_name: Optional[str] = Query(None, description="Optional batch name to filter modules"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Returns modules for a specific course (and optionally batch).
    Includes nested chapters due to SQLAlchemy relationships and Pydantic schemas.
    Does not compute or return the average score as requested.
    """
    
    query = db.query(Module).filter(Module.course_id == course_id)
    
    if batch_name:
        # Some modules might be course-wide (batch_name is null) and some might be batch-specific.
        # But if the user provides a batch_name, we can filter for modules specific to that batch,
        # or modules that apply to the whole course.
        # It depends on how the user creates them. Let's return modules matching the batch AND modules with no batch set.
        from sqlalchemy import or_
        query = query.filter(or_(Module.batch_name == batch_name, Module.batch_name == None))
        
    # Sort modules by order
    modules = query.order_by(Module.order).all()
    
    return modules

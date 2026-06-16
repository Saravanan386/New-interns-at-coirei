from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, Dict, Any

from sqlalchemy import or_
from sqlalchemy.orm import Session
from datetime import datetime
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

from app.models.module      import Module, Chapter
from app.models.chapter_resources import ChapterResource
from app.models.assignment  import Assignment, AssignmentResource, AssignmentSubmission
from app.models.test        import (
    Test, Question, Option,
    TestSubmission, StudentAnswer
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


def check_student(current_user: dict):
    if current_user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Student access only")
 
 
def check_instructor(current_user: dict):
    if current_user.get("role") != "instructor":
        raise HTTPException(status_code=403, detail="Instructor access only")
 
 
def _fmt_dt(dt: Optional[datetime]) -> Optional[str]:
    if not dt:
        return None
    return dt.strftime("%Y-%m-%d %I:%M %p")
 
 


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


@router.get("/{module_id}/full-overview")
def module_full_overview(
    module_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Everything inside a module in one response:
 
    ├── module metadata
    ├── course context
    ├── chapters[]
    │   └── resources[] per chapter
    ├── assignments[]
    │   ├── assignment resources[]
    │   └── submission_count / graded_count
    ├── tests[]
    │   └── question_count / submission_count / pass_count
    └── summary counts
    """
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
 
    course = db.query(Course).filter(Course.id == module.course_id).first()
 
    # ── CHAPTERS ──────────────────────────────────────────────────
    chapters_db = (
        db.query(Chapter)
        .filter(Chapter.module_id == module_id)
        .order_by(Chapter.order)
        .all()
    )
 
    chapters_data = []
    total_resources = 0
 
    for ch in chapters_db:
        res = db.query(ChapterResource).filter(
            ChapterResource.chapter_id == ch.id
        ).all()
        total_resources += len(res)
 
        chapters_data.append({
            "chapter_id":    ch.id,
            "title":         ch.title,
            "order":         ch.order,
            "class_content": ch.class_content,
            "key_topics":    ch.key_topics,
            "resources": [
                {
                    "resource_id": r.id,
                    "file_name":   r.file_name,
                    "file_path":   r.file_path,
                    "file_size":   r.file_size,
                    "uploaded_at": r.uploaded_at.strftime("%Y-%m-%d") if r.uploaded_at else None,
                }
                for r in res
            ],
        })
 
    # ── ASSIGNMENTS ───────────────────────────────────────────────
    assignments_db = db.query(Assignment).filter(
        Assignment.module_id  == module_id,
        Assignment.course_id  == module.course_id,
    ).all()
 
    assignments_data = []
 
    for asgn in assignments_db:
        asgn_resources = db.query(AssignmentResource).filter(
            AssignmentResource.assignment_id == asgn.id
        ).all()
 
        submission_count = db.query(AssignmentSubmission).filter(
            AssignmentSubmission.assignment_id == asgn.id
        ).count()
 
        graded_count = db.query(AssignmentSubmission).filter(
            AssignmentSubmission.assignment_id == asgn.id,
            AssignmentSubmission.status        == "graded"
        ).count()
 
        pending_count = db.query(AssignmentSubmission).filter(
            AssignmentSubmission.assignment_id == asgn.id,
            AssignmentSubmission.status        == "submitted"
        ).count()
 
        assignments_data.append({
            "assignment_id":      asgn.id,
            "title":              asgn.title,
            "description":        asgn.description,
            "objective":          asgn.objective,
            "expected_outcome":   asgn.expected_outcome,
            "batch_name":         asgn.batch_name,
            "due_date":           asgn.due_date.strftime("%Y-%m-%d") if asgn.due_date else None,
            "created_at":         asgn.created_at.strftime("%Y-%m-%d") if asgn.created_at else None,
 
            "submission_count":   submission_count,
            "graded_count":       graded_count,
            "pending_review":     pending_count,
 
            "resources": [
                {
                    "resource_id": r.id,
                    "file_name":   r.file_name,
                    "file_path":   r.file_path,
                    "file_type":   r.file_type,
                    "uploaded_at": r.uploaded_at.strftime("%Y-%m-%d") if r.uploaded_at else None,
                }
                for r in asgn_resources
            ],
        })
 
    # ── TESTS ─────────────────────────────────────────────────────
    tests_db = db.query(Test).filter(
        Test.module_id  == module_id,
        Test.course_id  == module.course_id,
    ).all()
 
    tests_data = []
 
    for test in tests_db:
        questions = db.query(Question).filter(Question.test_id == test.id).all()
        obtainable_marks = sum(q.marks for q in questions)
 
        submissions = db.query(TestSubmission).filter(
            TestSubmission.test_id == test.id,
            TestSubmission.status  == "submitted"
        ).all()
 
        pass_count  = sum(1 for s in submissions if s.is_passed is True)
        fail_count  = sum(1 for s in submissions if s.is_passed is False)
        scores      = [s.score_percentage for s in submissions if s.score_percentage is not None]
 
        tests_data.append({
            "test_id":           test.id,
            "title":             test.title,
            "description":       test.description,
            "batch_name":        test.batch_name,
            "start_time":        _fmt_dt(test.start_time),
            "end_time":          _fmt_dt(test.end_time),
            "created_at":        test.created_at.strftime("%Y-%m-%d") if test.created_at else None,
 
            "total_questions":   len(questions),
            "obtainable_marks":  obtainable_marks,
 
            "total_submitted":   len(submissions),
            "passed":            pass_count,
            "failed":            fail_count,
            "average_score":     round(sum(scores) / len(scores), 1) if scores else None,
        })
 
    # ── SUMMARY ───────────────────────────────────────────────────
    return {
        "module_id":    module.id,
        "title":        module.title,
        "order":        module.order,
        "status":       module.status,
        "batch_name":   module.batch_name,
 
        "course": {
            "course_id":   course.id          if course else None,
            "course_code": course.course_code if course else None,
            "course_name": course.name        if course else None,
        },
 
        # ── counts at a glance ────────────────────────────────────
        "summary": {
            "total_chapters":    len(chapters_data),
            "total_resources":   total_resources,
            "total_assignments": len(assignments_data),
            "total_tests":       len(tests_data),
        },
 
        # ── full data ─────────────────────────────────────────────
        "chapters":    chapters_data,
        "assignments": assignments_data,
        "tests":       tests_data,
    }



# Ensure your models are imported completely


# Reusing the existing prefix router context
# router = APIRouter(prefix="/modules", tags=["Modules"])

@router.get("/{module_id}/chapters/{chapter_id}/details")
def get_chapter_details_by_role(
    module_id: int,
    chapter_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Fetch unified chapter details tailored by user role:
    - Verifies module and chapter alignment context.
    - Instructors receive structural data and backend storage paths.
    - Students receive sanitized access strings and consumer-safe download payloads.
    """
    # 1. Validate parent Module context integrity
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module context not found")

    # 2. Extract precise Chapter details bounded by the validated Module ID
    chapter = db.query(Chapter).filter(
        Chapter.id == chapter_id, 
        Chapter.module_id == module_id
    ).first()
    
    if not chapter:
        raise HTTPException(
            status_code=404, 
            detail=f"Chapter with ID {chapter_id} not found inside Module {module_id}"
        )

    # 3. Pull associated assets/resources mapped to this specific Chapter
    resources_db = db.query(ChapterResource).filter(
        ChapterResource.chapter_id == chapter.id
    ).all()

    # 4. Extract User contextual role
    user_role = current_user.get("role")

    # ── INSTRUCTOR VIEW DATA STREAM ──────────────────────────────────────────
    if user_role in ("instructor", "admin"):
        return {
            "view_mode": user_role,
            "module_context": {
                "module_id": module.id,
                "module_title": module.title,
                "course_id": module.course_id,
                "batch_name": module.batch_name
            },
            "chapter_details": {
                "chapter_id": chapter.id,
                "title": chapter.title,
                "order": chapter.order,
                "class_content": chapter.class_content,
                "key_topics": chapter.key_topics,
            },
            "resources": [
                {
                    "resource_id": r.id,
                    "file_name": r.file_name,
                    "file_path": r.file_path,  # Raw tracking path exposed securely to management
                    "file_size": r.file_size,
                    "uploaded_at": r.uploaded_at.strftime("%Y-%m-%d %I:%M %p") if r.uploaded_at else None
                }
                for r in resources_db
            ]
        }

    # ── STUDENT VIEW DATA STREAM ─────────────────────────────────────────────
    elif user_role == "student":
        # Enforce structural boundaries: Match student batch visibility to module boundaries
        if module.batch_name and current_user.get("batch_name") != module.batch_name:
             raise HTTPException(status_code=403, detail="Access denied. Batch mismatch.")

        return {
            "view_mode": "student",
            "chapter_title": chapter.title,
            "class_content": chapter.class_content,
            "key_topics": chapter.key_topics,
            "downloadable_materials": [
                {
                    "resource_id": r.id,
                    "display_name": r.file_name,
                    "size": r.file_size,
                    # Hides internal system paths, providing a clean delivery point
                    "download_url": f"/api/v1/resources/download/{r.id}" 
                }
                for r in resources_db
            ]
        }

    # ── FALLBACK BOUNDARY PROTECTION ────────────────────────────────────────
    else:
        raise HTTPException(status_code=403, detail="Unrecognized functional role profile.")

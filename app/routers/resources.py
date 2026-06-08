# app/routers/resources.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.utils.security import get_current_user

from app.models.enrollment import Enrollment
from app.models.classroom import Classroom
from app.models.module import Module, Chapter
from app.models.chapter_resources import ChapterResource
from app.models.course import Course

router = APIRouter(
    prefix="/resources",
    tags=["Resources"]
)


@router.get("/my")
def my_resources(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    student_id = current_user["user_id"]

    enrollments = (
        db.query(Enrollment)
        .filter(
            Enrollment.user_id == student_id
        )
        .all()
    )

    classroom_ids = [e.classroom_id for e in enrollments]

    classrooms = (
        db.query(Classroom)
        .filter(
            Classroom.id.in_(classroom_ids)
        )
        .all()
    )

    resources = []

    for classroom in classrooms:

        modules = (
            db.query(Module)
            .filter(
                Module.course_id == classroom.course_id
            )
            .all()
        )

        for module in modules:

            chapters = (
                db.query(Chapter)
                .filter(
                    Chapter.module_id == module.id
                )
                .all()
            )

            for chapter in chapters:

                files = (
                    db.query(ChapterResource)
                    .filter(
                        ChapterResource.chapter_id == chapter.id
                    )
                    .all()
                )

                for file in files:

                    resources.append({
                        "resource_id": file.id,
                        "course_id": classroom.course_id,
                        "batch_name": classroom.batch_name,
                        "module_id": module.id,
                        "module_title": module.title,
                        "chapter_id": chapter.id,
                        "chapter_title": chapter.title,
                        "file_name": file.file_name,
                        "file_path": file.file_path,
                        "uploaded_at": file.uploaded_at
                    })

    return {
        "total_resources": len(resources),
        "resources": resources
    }


@router.get("/instructor")
def instructor_resources(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    instructor_id = current_user["user_id"]

    classrooms = (
        db.query(Classroom)
        .filter(
            Classroom.instructor_id == instructor_id
        )
        .all()
    )

    results = []

    for classroom in classrooms:

        modules = (
            db.query(Module)
            .filter(
                Module.course_id == classroom.course_id
            )
            .all()
        )

        for module in modules:

            chapters = (
                db.query(Chapter)
                .filter(
                    Chapter.module_id == module.id
                )
                .all()
            )

            for chapter in chapters:

                resources = (
                    db.query(ChapterResource)
                    .filter(
                        ChapterResource.chapter_id == chapter.id
                    )
                    .all()
                )

                for resource in resources:

                    results.append({
                        "resource_id": resource.id,
                        "course_id": classroom.course_id,
                        "batch_name": classroom.batch_name,
                        "module_id": module.id,
                        "module_title": module.title,
                        "chapter_id": chapter.id,
                        "chapter_title": chapter.title,
                        "file_name": resource.file_name,
                        "file_path": resource.file_path,
                        "uploaded_at": resource.uploaded_at
                    })

    return {
        "total_resources": len(results),
        "resources": results
    }
# app/routers/resources.py

import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
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


def can_access_resource(db: Session, resource: ChapterResource, current_user: dict) -> bool:
    if current_user.get("role") in ("instructor", "admin"):
        return True

    chapter = db.query(Chapter).filter(Chapter.id == resource.chapter_id).first()
    module = db.query(Module).filter(Module.id == chapter.module_id).first() if chapter else None
    if not module:
        return False

    return (
        db.query(Enrollment)
        .join(Classroom, Classroom.id == Enrollment.classroom_id)
        .filter(
            Enrollment.user_id == current_user["user_id"],
            Classroom.course_id == module.course_id,
        )
        .first()
        is not None
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
        course = db.query(Course).filter(Course.id == classroom.course_id).first()

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
                        "course_code": course.course_code if course else None,
                        "course_name": course.name if course else None,
                        "batch_name": classroom.batch_name,
                        "module_id": module.id,
                        "module_title": module.title,
                        "chapter_id": chapter.id,
                        "chapter_title": chapter.title,
                        "file_name": file.file_name,
                        "file_path": file.file_path,
                        "view_url": f"/resources/{file.id}/view",
                        "download_url": f"/resources/{file.id}/download",
                        "uploaded_at": file.uploaded_at
                    })

    return {
        "total_resources": len(resources),
        "resources": resources
    }


@router.get("/{resource_id}/view")
def view_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    resource = db.query(ChapterResource).filter(ChapterResource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    if not can_access_resource(db, resource, current_user):
        raise HTTPException(status_code=403, detail="Not authorized to access this resource")
    if not os.path.exists(resource.file_path):
        raise HTTPException(status_code=404, detail="File missing from server")

    return FileResponse(resource.file_path, filename=resource.file_name)


@router.get("/{resource_id}/download")
def download_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    resource = db.query(ChapterResource).filter(ChapterResource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    if not can_access_resource(db, resource, current_user):
        raise HTTPException(status_code=403, detail="Not authorized to access this resource")
    if not os.path.exists(resource.file_path):
        raise HTTPException(status_code=404, detail="File missing from server")

    return FileResponse(
        path=resource.file_path,
        filename=resource.file_name,
    )


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

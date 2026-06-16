import os
import uuid
import shutil
from fastapi import UploadFile


BASE_UPLOAD_DIR = "uploads"

os.makedirs(BASE_UPLOAD_DIR, exist_ok=True)


def save_file(
    file: UploadFile,
    folder: str
):
    """
    Save uploaded file and return metadata.
    """

    upload_folder = os.path.join(BASE_UPLOAD_DIR, folder)

    os.makedirs(upload_folder, exist_ok=True)

    ext = os.path.splitext(file.filename)[1]

    unique_name = f"{uuid.uuid4().hex}{ext}"

    file_path = os.path.join(
        upload_folder,
        unique_name
    )

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "file_name": file.filename,
        "stored_name": unique_name,
        "file_path": file_path,
        "content_type": file.content_type
    }


def delete_file(file_path: str):
    if file_path and os.path.exists(file_path):
        os.remove(file_path)
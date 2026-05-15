from fastapi import APIRouter, Depends
from app.utils.security import get_current_user

router = APIRouter(prefix="/resources", tags=["Resources"])


@router.get("")
def get_resources(user=Depends(get_current_user)):
    return [
        {
            "resource_id": 1,
            "name": "important_formulae.pdf",
            "size_kb": 576,
            "download_url": "/files/important_formulae.pdf"
        }
    ]

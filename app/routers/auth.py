from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas import (
    InstructorRegistrationRequest,
    RegistrationResponse,
    StudentRegistrationRequest,
)
from app.services.auth_service import create_access_token
from app.services.registration_service import register_instructor, register_student
from app.utils.security import hash_password, verify_password


router = APIRouter(prefix="/auth")


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str
    tenant_name: str | None = None
    tenant_branch: str = ""


class LoginRequest(BaseModel):
    email: str
    password: str


def _registration_response(profile, role: str):
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "full_name": profile.full_name,
        "email": profile.email,
        "phone_number": profile.phone_number,
        "role": role,
        "account_status": profile.account_status,
        "created_at": profile.created_at,
    }


def _get_or_create_tenant(db: Session, user: User) -> Tenant:
    tenant = db.query(Tenant).filter(Tenant.user_id == user.id).first()

    if tenant:
        return tenant

    tenant = Tenant(
        user_id=user.id,
        name=user.name,
        branch="",
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    return tenant


def _tenant_response(tenant: Tenant):
    return {
        "id": tenant.id,
        "user_id": tenant.user_id,
        "name": tenant.name,
        "branch": tenant.branch,
    }


@router.post(
    "/register/instructor",
    response_model=RegistrationResponse,
    status_code=201,
)
def register_instructor_api(
    payload: InstructorRegistrationRequest,
    db: Session = Depends(get_db),
):
    profile = register_instructor(db, payload)
    return _registration_response(profile, "instructor")


@router.post(
    "/register/student",
    response_model=RegistrationResponse,
    status_code=201,
)
def register_student_api(
    payload: StudentRegistrationRequest,
    db: Session = Depends(get_db),
):
    profile = register_student(db, payload)
    return _registration_response(profile, "student")


@router.post("/register")
def register(payload: RegisterRequest):
    role = payload.role.strip().lower()
    email = payload.email.strip().lower()
    tenant_name = payload.tenant_name.strip() if payload.tenant_name else payload.name
    tenant_branch = payload.tenant_branch.strip()

    if role not in ["admin", "instructor", "student"]:
        raise HTTPException(status_code=400, detail="Invalid role")

    db = SessionLocal()
    try:
        user = User(
            name=payload.name,
            email=email,
            password_hash=hash_password(payload.password),
            role=role,
        )
        db.add(user)
        db.flush()

        tenant = Tenant(
            user_id=user.id,
            name=tenant_name,
            branch=tenant_branch,
        )
        db.add(tenant)
        db.commit()
        db.refresh(user)
        db.refresh(tenant)

        return {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "tenant": _tenant_response(tenant),
        }

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already registered")

    finally:
        db.close()


@router.post("/login")
def login(payload: LoginRequest):
    db = SessionLocal()
    try:
        email = payload.email.strip().lower()
        user = db.query(User).filter(User.email == email).first()

        if not user or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        tenant = _get_or_create_tenant(db, user)

        access_token = create_access_token({
            "user_id": user.id,
            "role": user.role,
            "tenant_id": tenant.id,
            "tenant_branch": tenant.branch,
        })

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "tenant_id": tenant.id,
            "tenant_name": tenant.name,
            "branch": tenant.branch,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "tenant": _tenant_response(tenant),
            },
        }
    finally:
        db.close()

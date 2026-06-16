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
from app.services.tenant_database import (
    build_tenant_database_name,
    ensure_tenant_database,
    get_tenant_session_local,
)
from app.utils.security import hash_password, require_roles, verify_password


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
        database_name=build_tenant_database_name(user.name, ""),
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    ensure_tenant_database(tenant.database_name)

    return tenant


def _tenant_response(tenant: Tenant):
    return {
        "id": tenant.id,
        "user_id": tenant.user_id,
        "name": tenant.name,
        "branch": tenant.branch,
        "database_name": tenant.database_name,
    }


def _admin_access_role(role: str) -> str:
    return "admin" if role == "tenant" else role


def _create_login_token(user: User, tenant: Tenant | None):
    token_data = {
        "user_id": user.id,
        "role": _admin_access_role(user.role),
        "account_role": user.role,
    }
    if tenant:
        token_data.update({
            "tenant_id": tenant.id,
            "tenant_branch": tenant.branch,
            "tenant_database_name": tenant.database_name,
        })
    return create_access_token(token_data)


def _copy_tenant_owner_to_tenant_db(user: User, tenant: Tenant) -> None:
    tenant_session = get_tenant_session_local(tenant.database_name)
    tenant_db = tenant_session()
    try:
        existing = tenant_db.query(User).filter(User.id == user.id).first()
        if existing:
            return

        tenant_user = User(
            id=user.id,
            name=user.name,
            email=user.email,
            password_hash=user.password_hash,
            role=user.role,
            student_id=user.student_id,
        )
        tenant_db.add(tenant_user)
        tenant_db.commit()
    finally:
        tenant_db.close()


def _find_login_user(db: Session, email: str, password: str):
    system_user = db.query(User).filter(User.email == email).first()
    if system_user and verify_password(password, system_user.password_hash):
        tenant = db.query(Tenant).filter(Tenant.user_id == system_user.id).first()
        if not tenant and system_user.role in {"admin", "tenant"}:
            tenant = _get_or_create_tenant(db, system_user)
        return system_user, tenant

    tenants = db.query(Tenant).filter(Tenant.database_name.isnot(None)).all()
    for tenant in tenants:
        tenant_session = get_tenant_session_local(tenant.database_name)
        tenant_db = tenant_session()
        try:
            tenant_user = tenant_db.query(User).filter(User.email == email).first()
            if tenant_user and verify_password(password, tenant_user.password_hash):
                return tenant_user, tenant
        finally:
            tenant_db.close()

    return None, None


def _require_tenant_admin(current_user: dict = Depends(require_roles(["admin"]))):
    if not current_user.get("tenant_database_name"):
        raise HTTPException(
            status_code=400,
            detail="Tenant database context is required to register users",
        )
    return current_user


@router.post(
    "/register/instructor",
    response_model=RegistrationResponse,
    status_code=201,
)
def register_instructor_api(
    payload: InstructorRegistrationRequest,
    current_user: dict = Depends(_require_tenant_admin),
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
    current_user: dict = Depends(_require_tenant_admin),
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

    if role not in ["admin", "tenant", "instructor", "student"]:
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

        database_name = build_tenant_database_name(tenant_name, tenant_branch)
        tenant = Tenant(
            user_id=user.id,
            name=tenant_name,
            branch=tenant_branch,
            database_name=database_name,
        )
        db.add(tenant)
        db.commit()
        db.refresh(user)
        db.refresh(tenant)
        ensure_tenant_database(database_name)
        _copy_tenant_owner_to_tenant_db(user, tenant)

        return {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "database_name": database_name,
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
        user, tenant = _find_login_user(db, email, payload.password)

        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        access_token = _create_login_token(user, tenant)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "tenant_id": tenant.id if tenant else None,
            "tenant_name": tenant.name if tenant else None,
            "branch": tenant.branch if tenant else "",
            "database_name": tenant.database_name if tenant else None,
            "access_role": _admin_access_role(user.role),
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "tenant": _tenant_response(tenant) if tenant else None,
            },
        }
    finally:
        db.close()

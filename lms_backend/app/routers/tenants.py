from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.tenant import Tenant
from app.models.user import User
from app.services.auth_service import create_access_token
from app.services.tenant_database import build_tenant_database_name, ensure_tenant_database
from app.utils.security import verify_password


router = APIRouter(prefix="/tenants", tags=["Tenants"])


class TenantCreate(BaseModel):
    user_id: int = Field(
        ...,
        description="User id for the tenant owner. One user can have only one tenant.",
        examples=[1],
    )
    name: str = Field(
        ...,
        min_length=2,
        max_length=150,
        description="Tenant or organization name.",
        examples=["COIREI"],
    )
    branch: str = Field(
        default="",
        max_length=150,
        description="Branch name. Keep empty when there is no branch yet.",
        examples=[""],
    )


class TenantUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
        description="Updated tenant or organization name.",
        examples=["COIREI Academy"],
    )
    branch: str | None = Field(
        default=None,
        max_length=150,
        description="Updated branch name. Use empty string for no branch.",
        examples=["Chennai"],
    )


class TenantLoginRequest(BaseModel):
    email: str = Field(..., examples=["admin1@example.com"])
    password: str = Field(..., examples=["admin123"])


class TenantResponse(BaseModel):
    id: int
    user_id: int
    name: str
    branch: str
    database_name: str | None = None

    model_config = {"from_attributes": True}


def _tenant_response(tenant: Tenant):
    return {
        "id": tenant.id,
        "user_id": tenant.user_id,
        "name": tenant.name,
        "branch": tenant.branch,
        "database_name": tenant.database_name,
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


def _admin_access_role(role: str) -> str:
    return "admin" if role == "tenant" else role


@router.get("/", response_model=list[TenantResponse])
def list_tenants(db: Session = Depends(get_db)):
    return db.query(Tenant).order_by(Tenant.id.asc()).all()


@router.get("/list", response_model=list[TenantResponse])
def list_tenants_api(db: Session = Depends(get_db)):
    return db.query(Tenant).order_by(Tenant.id.asc()).all()


@router.post("/login")
def tenant_login(payload: TenantLoginRequest, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    tenant = _get_or_create_tenant(db, user)

    access_token = create_access_token({
        "user_id": user.id,
        "role": _admin_access_role(user.role),
        "account_role": user.role,
        "tenant_id": tenant.id,
        "tenant_branch": tenant.branch,
        "tenant_database_name": tenant.database_name,
    })

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "tenant_id": tenant.id,
        "tenant_name": tenant.name,
        "branch": tenant.branch,
        "database_name": tenant.database_name,
        "access_role": _admin_access_role(user.role),
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "tenant": _tenant_response(tenant),
        },
    }


@router.get("/{tenant_id}", response_model=TenantResponse)
def get_tenant(tenant_id: int, db: Session = Depends(get_db)):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return tenant


@router.post("/", response_model=TenantResponse)
def create_tenant(payload: TenantCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == payload.user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    existing_tenant = db.query(Tenant).filter(Tenant.user_id == payload.user_id).first()

    if existing_tenant:
        existing_tenant.name = payload.name
        existing_tenant.branch = payload.branch
        existing_tenant.database_name = (
            existing_tenant.database_name
            or build_tenant_database_name(payload.name, payload.branch)
        )
        db.commit()
        db.refresh(existing_tenant)
        ensure_tenant_database(existing_tenant.database_name)
        return existing_tenant

    database_name = build_tenant_database_name(payload.name, payload.branch)
    tenant = Tenant(
        user_id=payload.user_id,
        name=payload.name,
        branch=payload.branch,
        database_name=database_name,
    )

    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    ensure_tenant_database(database_name)
    return tenant


@router.put("/{tenant_id}", response_model=TenantResponse)
def update_tenant(
    tenant_id: int,
    payload: TenantUpdate,
    db: Session = Depends(get_db),
):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    update_data = payload.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(tenant, key, value)

    if not tenant.database_name:
        tenant.database_name = build_tenant_database_name(tenant.name, tenant.branch)

    db.commit()
    db.refresh(tenant)
    ensure_tenant_database(tenant.database_name)

    return tenant


@router.delete("/{tenant_id}")
def delete_tenant(tenant_id: int, db: Session = Depends(get_db)):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    db.delete(tenant)
    db.commit()

    return {"message": "Tenant deleted successfully"}

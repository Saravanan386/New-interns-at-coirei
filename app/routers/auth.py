from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from app.database import SessionLocal
from app.models.user import User
from app.utils.security import hash_password, verify_password
from app.services.auth_service import create_access_token




router = APIRouter(prefix="/auth")

@router.post("/register")
def register(name: str, email: str, password: str, role: str):
    if role not in ["admin", "instructor", "student"]:
        raise HTTPException(status_code=400, detail="Invalid role")

    db = SessionLocal()
    try:
        user = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            role=role
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        return {"id": user.id, "email": user.email, "role": user.role}

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already registered")

    finally:
        db.close()


    return {"id": user.id, "email": user.email, "role": user.role}


@router.post("/login")
def login(email: str, password: str):
    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    print(password)
    print(len(password))
    access_token = create_access_token({
        "user_id": user.id,
        "role": user.role
    })

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
    }


    return {"access_token": token, "token_type": "bearer"}




from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.database import get_db
from app.models.user import User
from app.schemas import (
    InstructorRegistrationRequest,
    RegistrationResponse,
    StudentRegistrationRequest,
)
from app.services.registration_service import register_instructor, register_student
from app.utils.security import hash_password, verify_password
from app.services.auth_service import create_access_token


router = APIRouter(prefix="/auth")


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str


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
    if payload.role not in ["admin", "instructor", "student"]:
        raise HTTPException(status_code=400, detail="Invalid role")

    db = SessionLocal()
    try:
        user = User(
            name=payload.name,
            email=payload.email,
            password_hash=hash_password(payload.password),
            role=payload.role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        return {"id": user.id, "email": user.email, "role": user.role}

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already registered")

    finally:
        db.close()


@router.post("/login")
def login(payload: LoginRequest):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == payload.email).first()

        if not user or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        access_token = create_access_token({
            "user_id": user.id,
            "role": user.role
        })

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role
            }
        }
    finally:
        db.close()



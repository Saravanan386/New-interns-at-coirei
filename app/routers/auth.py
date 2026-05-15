from fastapi import APIRouter, HTTPException
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

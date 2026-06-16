from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.registration_profile import InstructorInformation, StudentInformation
from app.models.user import User
from app.schemas import (
    InstructorRegistrationRequest,
    StudentRegistrationRequest,
)
from app.utils.security import hash_password


def _ensure_registration_available(db: Session, email: str, phone_number: str) -> None:
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    instructor_phone_exists = (
        db.query(InstructorInformation)
        .filter(InstructorInformation.phone_number == phone_number)
        .first()
    )
    student_phone_exists = (
        db.query(StudentInformation)
        .filter(StudentInformation.phone_number == phone_number)
        .first()
    )
    if instructor_phone_exists or student_phone_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Phone number already registered",
        )


def register_instructor(db: Session, payload: InstructorRegistrationRequest) -> InstructorInformation:
    _ensure_registration_available(db, payload.email, payload.phone_number)

    user = User(
        name=payload.full_name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role="instructor",
    )
    profile = InstructorInformation(
        user=user,
        full_name=payload.full_name,
        email=payload.email,
        phone_number=payload.phone_number,
        bio=payload.bio,
        qualifications=payload.qualifications,
        experience_years=payload.experience_years,
        skills=payload.skills,
        specialization=payload.specialization,
        profile_image_url=payload.profile_image_url,
        address_line1=payload.address_line1,
        address_line2=payload.address_line2,
        city=payload.city,
        state=payload.state,
        country=payload.country,
        postal_code=payload.postal_code,
        social_links=payload.social_links,
        account_status=payload.account_status,
    )

    return _commit_registration(db, profile)


def register_student(db: Session, payload: StudentRegistrationRequest) -> StudentInformation:
    _ensure_registration_available(db, payload.email, payload.phone_number)

    user = User(
        name=payload.full_name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role="student",
    )
    profile = StudentInformation(
        user=user,
        full_name=payload.full_name,
        email=payload.email,
        phone_number=payload.phone_number,
        date_of_birth=payload.date_of_birth,
        gender=payload.gender,
        education_details=payload.education_details,
        interests=payload.interests,
        profile_image_url=payload.profile_image_url,
        address_line1=payload.address_line1,
        address_line2=payload.address_line2,
        city=payload.city,
        state=payload.state,
        country=payload.country,
        postal_code=payload.postal_code,
        account_status=payload.account_status,
    )

    return _commit_registration(db, profile)


def _commit_registration(db: Session, profile):
    try:
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Registration already exists",
        ) from exc

from app.database import SessionLocal
from app.models.user import User
from app.utils.security import hash_password

db = SessionLocal()

users = [
    {
        "name": "Admin User",
        "email": "admin@lms.com",
        "password": "admin123",
        "role": "admin"
    },
    {
        "name": "Instructor User",
        "email": "instructor@lms.com",
        "password": "instructor123",
        "role": "instructor"
    },
    {
        "name": "Student User",
        "email": "student@lms.com",
        "password": "student123",
        "role": "student"
    }
]

for u in users:
    exists = db.query(User).filter(User.email == u["email"]).first()

    if not exists:
        user = User(
            name=u["name"],
            email=u["email"],
            password_hash=hash_password(u["password"]),
            role=u["role"]
        )
        db.add(user)

db.commit()

print("Users seeded successfully")
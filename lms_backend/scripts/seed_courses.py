from app.database import SessionLocal
from app.models.course import Course
from app.models.classroom import Classroom

db = SessionLocal()

try:

    course = Course(
        name="AI/ML Frontier Engineer",
        duration_months=3,
        total_lessons=40
    )

    db.add(course)
    db.commit()
    db.refresh(course)

    classroom = Classroom(
        course_id=course.id,
        course_name=course.name,
        batch_name="Batch-A",
        room_name="AI_ML_ROOM"
    )

    db.add(classroom)

    db.commit()

    print("Courses seeded")

except Exception as e:
    db.rollback()
    print(e)

finally:
    db.close()
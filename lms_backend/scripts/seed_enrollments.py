from app.database import SessionLocal
from app.models.user import User
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.instructor_enrollment import InstructorEnrollment

db = SessionLocal()

try:

    student = db.query(User).filter(
        User.email == "student@lms.com"
    ).first()

    instructor = db.query(User).filter(
        User.email == "instructor@lms.com"
    ).first()

    course = db.query(Course).first()

    student_enrollment = Enrollment(
        user_id=student.id,
        course_id=course.id,
        batch_name="Batch-A",
        progress_percent=0,
        status="ongoing"
    )

    db.add(student_enrollment)

    instructor_assignment = InstructorEnrollment(
        user_id=instructor.id,
        course_id=course.id,
        batch_name="Batch-A"
    )

    db.add(instructor_assignment)

    db.commit()

    print("Enrollments seeded")

except Exception as e:
    db.rollback()
    print(e)

finally:
    db.close()  
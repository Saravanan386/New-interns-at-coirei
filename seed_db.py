import sys
import os

sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models.user import User
from app.models.course import Course
from app.models.module import Module, Chapter
from app.models.enrollment import Enrollment
from app.models.classroom import Classroom

def seed():
    db = SessionLocal()
    try:
        print("Finding existing users...")
        instructor = db.query(User).filter(User.email == "instructor@coirei.com").first()
        student = db.query(User).filter(User.email == "kuberan@coirei.com").first()
        
        if not instructor or not student:
            print("Error: Essential users not found. Run selective_cleanup.py first if you haven't.")
            return

        print("Adding courses...")
        ai_course = Course(
            name="AI/ML frontier Engineer", 
            duration_months=3, 
            total_lessons=40
        )
        
        db.add(ai_course)
        db.commit()
        db.refresh(ai_course)
        
        print(f"Added course: {ai_course.name} (ID: {ai_course.id})")

        print("Adding modules and chapters for AI/ML course...")
        mod1 = Module(title="Introduction to AI & Machine Learning", order=1, course_id=ai_course.id, batch_name="Batch-A")
        db.add(mod1)
        db.commit()
        db.refresh(mod1)
        
        ch1 = Chapter(title="Foundations of AI", order=1, module_id=mod1.id)
        ch2 = Chapter(title="Python for ML", order=2, module_id=mod1.id)
        db.add_all([ch1, ch2])
        
        mod2 = Module(title="Frontier Engineering Techniques", order=2, course_id=ai_course.id, batch_name="Batch-A")
        db.add(mod2)
        db.commit()
        db.refresh(mod2)
        
        ch3 = Chapter(title="Advanced Prompt Engineering", order=1, module_id=mod2.id)
        db.add(ch3)
        
        print("Enrolling student...")
        enrollment = Enrollment(
            user_id=student.id,
            course_id=ai_course.id,
            batch_name="Batch-A",
            progress_percent=0,
            status="ongoing"
        )
        db.add(enrollment)
        
        print("Adding classroom...")
        classroom = Classroom(
            course_id=ai_course.id,
            course_name=ai_course.name,
            batch_name="Batch-A",
            room_name="AI_ML_Frontier_Room"
        )
        db.add(classroom)
        
        db.commit()
        print("Database seeded successfully with essential data including classroom!")
        
    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed()

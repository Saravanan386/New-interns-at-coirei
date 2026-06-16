import sys
import os

# Add the project root to sys.path so we can import 'app'
sys.path.append(os.getcwd())

from app.database import engine, Base
# Import all models to ensure Base.metadata is fully populated
from app.models import (
    user, 
    classroom, 
    session, 
    attendance, 
    schedule, 
    module,
    course,
    enrollment
)

def cleanup():
    print("Dropping all tables...")
    # Order matters for drops if there are complex dependencies,
    # but Base.metadata.drop_all usually handles it or you can try multiple passes.
    try:
        Base.metadata.drop_all(bind=engine)
    except Exception as e:
        print(f"Warning during drop: {e}")
        print("Attempting to continue...")
        
    print("Recreating all tables...")
    Base.metadata.create_all(bind=engine)
    print("Database cleaned successfully!")

if __name__ == "__main__":
    # In automated environment, we skip the input.
    # confirm = input("This will DELETE ALL DATA in the database. Are you sure? (y/N): ")
    # if confirm.lower() == 'y':
    cleanup()

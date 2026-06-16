from app.database import Base, engine
import app.models  # noqa: F401


def main():
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")


if __name__ == "__main__":
    main()

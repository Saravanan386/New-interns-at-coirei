import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET"] = "test-readiness-secret"

import app.database as database_module  # noqa: E402

test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
test_session_local = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)

database_module.engine = test_engine
database_module.SessionLocal = test_session_local

from app.database import Base, SessionLocal, engine  # noqa: E402
import app.models  # noqa: E402,F401
import app.models.user  # noqa: E402,F401
import app.models.course  # noqa: E402,F401
import app.models.classroom  # noqa: E402,F401
import app.models.enrollment  # noqa: E402,F401
import app.models.instructor_enrollment  # noqa: E402,F401
import app.models.session  # noqa: E402,F401
import app.models.attendance  # noqa: E402,F401
import app.models.module  # noqa: E402,F401
import app.models.assignment  # noqa: E402,F401
import app.models.schedule  # noqa: E402,F401
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    try:
        yield
    finally:
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client

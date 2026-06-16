from typing import Optional

from fastapi import HTTPException, Request, status
from jose import JWTError, jwt
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import DATABASE_URL, JWT_SECRET

JWT_ALGORITHM = "HS256"
POSTGRES_SCHEMES = (
    "postgresql://",
    "postgresql+psycopg://",
    "postgresql+psycopg2://",
)

if not DATABASE_URL.startswith(POSTGRES_SCHEMES):
    raise RuntimeError(
        "DATABASE_URL must be a PostgreSQL URL. "
        "Example: postgresql+psycopg://postgres@localhost:5432/lms_db"
    )

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=5,
    max_overflow=10,
    connect_args={
        "connect_timeout": 10,
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 5,
        "keepalives_count": 5,
    }
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


SYSTEM_DB_PATHS = {
    "/auth/login",
    "/auth/register",
}
SYSTEM_DB_PREFIXES = (
    "/tenants",
)


def _uses_system_db(path: str) -> bool:
    return path in SYSTEM_DB_PATHS or any(
        path.startswith(prefix) for prefix in SYSTEM_DB_PREFIXES
    )


def _tenant_database_from_request(request: Optional[Request]) -> str | None:
    if request is None:
        return None

    if _uses_system_db(request.url.path):
        return None

    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return payload.get("tenant_database_name")


def _session_for_request(request: Optional[Request]):
    if request is not None and _uses_system_db(request.url.path):
        return SessionLocal()

    database_name = _tenant_database_from_request(request)
    if not database_name:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant database context is required",
        )

    from app.services.tenant_database import get_tenant_session_local

    return get_tenant_session_local(database_name)()


def ensure_system_schema() -> None:
    inspector = inspect(engine)
    if "tenants" not in inspector.get_table_names():
        return

    tenant_columns = {column["name"] for column in inspector.get_columns("tenants")}
    if "database_name" not in tenant_columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE tenants ADD COLUMN database_name VARCHAR"))


def get_db(request: Request = None):
    db = _session_for_request(request)
    try:
        yield db
    finally:
        db.close()

import re

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import sessionmaker

from app.config import DATABASE_URL
from app.database import Base

_tenant_engines = {}
_tenant_sessionmakers: dict[str, sessionmaker] = {}


def build_tenant_database_name(name: str, branch: str) -> str:
    raw = f"{name}_{branch}_db" if branch else f"{name}_db"
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", raw).strip("_").lower()
    if not normalized:
        normalized = "tenant_db"
    if normalized[0].isdigit():
        normalized = f"tenant_{normalized}"
    return normalized[:63]


def tenant_database_url(database_name: str) -> str:
    url = make_url(DATABASE_URL)
    return str(url.set(database=database_name))


def _postgres_admin_url(url: URL) -> str:
    admin_database = "postgres"
    if url.database == admin_database:
        admin_database = "template1"
    return str(url.set(database=admin_database))


def _create_postgres_database(database_name: str) -> None:
    url = make_url(DATABASE_URL)
    admin_engine = create_engine(
        _postgres_admin_url(url),
        isolation_level="AUTOCOMMIT",
        pool_pre_ping=True,
    )
    safe_name = database_name.replace('"', '""')
    try:
        with admin_engine.connect() as connection:
            exists = connection.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :database_name"),
                {"database_name": database_name},
            ).scalar()
            if not exists:
                connection.execute(text(f'CREATE DATABASE "{safe_name}"'))
    finally:
        admin_engine.dispose()


def ensure_tenant_database(database_name: str) -> None:
    _create_postgres_database(database_name)

    engine = get_tenant_engine(database_name)

    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_tenant_engine(database_name: str):
    if database_name in _tenant_engines:
        return _tenant_engines[database_name]

    url = tenant_database_url(database_name)
    engine_kwargs = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "connect_args": {
            "connect_timeout": 10,
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 5,
            "keepalives_count": 5,
        },
    }

    engine = create_engine(url, **engine_kwargs)
    _tenant_engines[database_name] = engine
    return engine


def get_tenant_session_local(database_name: str):
    if database_name not in _tenant_sessionmakers:
        ensure_tenant_database(database_name)
        _tenant_sessionmakers[database_name] = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=get_tenant_engine(database_name),
        )
    return _tenant_sessionmakers[database_name]

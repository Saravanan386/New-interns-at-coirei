from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    # ── Neon serverless fixes ─────────────────────────────────────────────
    pool_pre_ping=True,      # test connection before using it (detects drops)
    pool_recycle=300,        # recycle connections every 5 min (before Neon drops them)
    pool_size=5,             # max persistent connections (fits Neon free tier)
    max_overflow=10,         # extra connections allowed under high load
    connect_args={
        "connect_timeout": 10,           # fail fast if Neon is sleeping
        "keepalives": 1,                 # enable TCP keepalives
        "keepalives_idle": 30,           # send keepalive after 30s idle
        "keepalives_interval": 5,        # retry every 5s
        "keepalives_count": 5,           # give up after 5 retries
    }
)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

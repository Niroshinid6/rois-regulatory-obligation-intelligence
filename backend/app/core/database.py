from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool
from app.core.config import settings


def normalize_database_url(database_url: str) -> str:
    return settings.normalize_database_url(database_url)


def is_postgresql_url(database_url: str) -> bool:
    normalized = normalize_database_url(database_url)
    return normalized.startswith(("postgresql://", "postgresql+psycopg://"))


def is_supabase_transaction_pooler(database_url: str) -> bool:
    normalized = normalize_database_url(database_url).lower()
    return ":6543/" in normalized or "pgbouncer=true" in normalized


def get_serverless_connect_args(database_url: str) -> dict:
    resolved_url = normalize_database_url(database_url)
    if resolved_url.startswith("sqlite"):
        return {"check_same_thread": False}
    if is_supabase_transaction_pooler(resolved_url):
        return {"prepare_threshold": 0}
    return {}


def build_engine(database_url: str | None = None):
    resolved_url = normalize_database_url(database_url or settings.DATABASE_URL)
    connect_args = get_serverless_connect_args(resolved_url)
    engine_kwargs = {}

    if resolved_url.startswith("sqlite"):
        engine_kwargs["pool_pre_ping"] = True
    else:
        engine_kwargs["pool_pre_ping"] = True
        if settings.DATABASE_SERVERLESS:
            engine_kwargs["poolclass"] = NullPool

    return create_engine(
        resolved_url,
        connect_args=connect_args,
        **engine_kwargs,
    )


engine = build_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

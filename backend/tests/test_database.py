from sqlalchemy.pool import NullPool, QueuePool
import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.core.database import (
    build_engine,
    get_serverless_connect_args,
    is_postgresql_url,
    is_supabase_transaction_pooler,
)


def test_sqlite_engine_initialization(tmp_path):
    url = f"sqlite:///{tmp_path / 'database.db'}"
    engine = build_engine(url)
    try:
        assert str(engine.url).startswith("sqlite:")
        assert get_serverless_connect_args(url)["check_same_thread"] is False
    finally:
        engine.dispose()


def test_postgresql_url_normalization():
    assert Settings.normalize_database_url(
        "postgres://user:password@db.example.com:5432/rois"
    ) == "postgresql+psycopg://user:password@db.example.com:5432/rois"
    assert Settings.normalize_database_url(
        "postgresql://user:password@db.example.com:5432/rois"
    ) == "postgresql+psycopg://user:password@db.example.com:5432/rois"
    assert is_postgresql_url("postgresql://db.example.com/rois")


def test_supabase_transaction_pooler_detection():
    url = "postgresql+psycopg://user:password@db.example.com:6543/rois"
    assert is_supabase_transaction_pooler(url)
    assert get_serverless_connect_args(url)["prepare_threshold"] == 0


def test_direct_postgresql_connection_has_no_pooler_settings():
    url = "postgresql+psycopg://user@db.example.com:5432/rois"
    assert not is_supabase_transaction_pooler(url)
    assert get_serverless_connect_args(url) == {}


def test_non_serverless_postgresql_does_not_use_nullpool(monkeypatch):
    monkeypatch.setattr("app.core.database.settings.DATABASE_SERVERLESS", False)
    engine = build_engine(
        "postgresql+psycopg://user@db.example.com:5432/rois"
    )
    try:
        assert isinstance(engine.pool, QueuePool)
    finally:
        engine.dispose()


def test_sqlite_ignores_serverless_setting(monkeypatch, tmp_path):
    monkeypatch.setattr("app.core.database.settings.DATABASE_SERVERLESS", False)
    url = f"sqlite:///{tmp_path / 'database.db'}"
    engine = build_engine(url)
    try:
        assert str(engine.url).startswith("sqlite:")
        assert get_serverless_connect_args(url)["check_same_thread"] is False
    finally:
        engine.dispose()


def test_postgresql_serverless_engine_uses_nullpool():
    engine = build_engine(
        "postgresql+psycopg://user:password@db.example.com:5432/rois"
    )
    try:
        assert isinstance(engine.pool, NullPool)
    finally:
        engine.dispose()


def test_session_lifecycle_works_with_sqlite(tmp_path):
    engine = build_engine(f"sqlite:///{tmp_path / 'session.db'}")
    try:
        connection = engine.connect()
        assert connection.closed is False
        connection.close()
        assert connection.closed is True
    finally:
        engine.dispose()


def test_migration_database_url_selection():
    configured = Settings(
        _env_file=None,
        ROIS_ENV="development",
        SECRET_KEY="test-secret-key-that-is-at-least-32-characters",
        DATABASE_URL="sqlite:///./rois.db",
        MIGRATION_DATABASE_URL="postgresql://migration-user@db.example.com:5432/rois",
    )
    assert configured.normalized_migration_database_url.startswith(
        "postgresql+psycopg://"
    )
    assert configured.normalized_database_url == "sqlite:///./rois.db"


def test_production_validation_does_not_expose_database_password():
    fake_password_marker = "FAKE_DATABASE_PASSWORD"
    fake_url = (
        "postgresql://rois:"
        f"{fake_password_marker}"
        "@db.example.com:5432/rois"
    )
    with pytest.raises(ValidationError) as exc:
        Settings(
            _env_file=None,
            ROIS_ENV="production",
            SECRET_KEY="valid-fake-secret-key-for-testing-only-32chars",
            DATABASE_URL=fake_url,
            CORS_ORIGINS="http://localhost:5173",
        )
    assert fake_password_marker not in str(exc.value)

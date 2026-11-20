import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import get_password_hash
from app.main import app
from app.models import ControlCategory, User


@pytest.fixture
def api_client(tmp_path):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    test_session = sessionmaker(bind=engine)
    db = test_session()
    db.add(User(
        email="test-admin@rois.internal",
        hashed_password=get_password_hash("test-password"),
        full_name="ROIS Test Administrator",
        role="admin",
    ))
    db.add_all([
        ControlCategory(code="CDD-01", name="Customer Due Diligence"),
        ControlCategory(code="GOV-01", name="Corporate Governance"),
        ControlCategory(code="REP-01", name="Regulatory Reporting"),
    ])
    db.commit()
    db.close()

    original_upload_dir = settings.UPLOAD_DIR
    settings.UPLOAD_DIR = str(tmp_path / "uploads")

    def override_get_db():
        session = test_session()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            login = client.post(
                "/api/v1/auth/login",
                json={
                    "email": "test-admin@rois.internal",
                    "password": "test-password",
                },
            )
            assert login.status_code == 200
            yield client, {
                "Authorization": f"Bearer {login.json()['access_token']}",
            }
    finally:
        app.dependency_overrides.pop(get_db, None)
        settings.UPLOAD_DIR = original_upload_dir
        engine.dispose()

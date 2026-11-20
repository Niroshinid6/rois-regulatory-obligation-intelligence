from io import BytesIO

import pytest
from pydantic import ValidationError
from reportlab.pdfgen import canvas
from pypdf import PdfWriter

from app.core.config import Settings


def _create_demo_pdf() -> bytes:
    content = BytesIO()
    pdf = canvas.Canvas(content)
    pdf.drawString(
        48,
        760,
        "DEMONSTRATION DOCUMENT - NOT AN OFFICIAL IFSCA CIRCULAR",
    )
    pdf.drawString(
        48,
        720,
        "All IFSC Banking Units (IBUs) shall establish an AML framework",
    )
    pdf.drawString(48, 704, "within 30 days of circular issuance.")
    pdf.save()
    return content.getvalue()


def _upload_document(client, headers):
    response = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        data={
            "title": "[DEMONSTRATION ONLY] API test circular",
            "regulator": "ROIS Demo",
        },
        files={"file": ("demo.pdf", _create_demo_pdf(), "application/pdf")},
    )
    assert response.status_code == 200
    return response.json()


def test_health(api_client):
    client, _ = api_client
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "online"


def test_protected_route_rejects_anonymous_user(api_client):
    client, _ = api_client
    response = client.get("/api/v1/documents/")
    assert response.status_code == 401


def test_login_failure(api_client):
    client, _ = api_client
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test-admin@rois.internal", "password": "incorrect"},
    )
    assert response.status_code == 401


def test_login_success_and_me(api_client):
    client, _ = api_client
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test-admin@rois.internal",
            "password": "test-password",
        },
    )
    assert response.status_code == 200
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}

    profile = client.get("/api/v1/auth/me", headers=headers)
    assert profile.status_code == 200
    assert profile.json()["email"] == "test-admin@rois.internal"
    assert profile.json()["role"] == "admin"


def test_dashboard_metrics_use_database_records(api_client):
    client, headers = api_client
    response = client.get("/api/v1/dashboard/metrics", headers=headers)

    assert response.status_code == 200
    assert response.json()["total_documents"] == 0
    assert response.json()["total_obligations"] == 0
    assert response.json()["recent_documents"] == []


def test_documents_list_and_pages(api_client):
    client, headers = api_client
    document = _upload_document(client, headers)

    listing = client.get("/api/v1/documents/", headers=headers)
    assert listing.status_code == 200
    assert listing.json()["total"] == 1
    assert listing.json()["items"][0]["id"] == document["id"]

    pages = client.get(
        f"/api/v1/documents/{document['id']}/pages",
        headers=headers,
    )
    assert pages.status_code == 200
    assert len(pages.json()) == 1
    assert pages.json()[0]["page_number"] == 1
    assert "shall establish" in pages.json()[0]["extracted_text"]


def test_document_pdf_stream(api_client):
    client, headers = api_client
    document = _upload_document(client, headers)

    response = client.get(
        f"/api/v1/documents/{document['id']}/pdf",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


def test_obligations_review_and_evidence(api_client):
    client, headers = api_client
    document = _upload_document(client, headers)
    obligations = client.get(
        "/api/v1/obligations/",
        headers=headers,
        params={"document_id": document["id"]},
    )
    assert obligations.status_code == 200
    obligation = obligations.json()["items"][0]

    evidence = client.get(
        f"/api/v1/evidence/{obligation['id']}",
        headers=headers,
    )
    assert evidence.status_code == 200
    evidence_data = evidence.json()
    assert evidence_data["evidence_span"]["exact_text"] in evidence_data["source_page"]["extracted_text"]

    review = client.put(
        f"/api/v1/obligations/{obligation['id']}/review",
        headers=headers,
        json={"action": "approved", "comments": "Verified in API test."},
    )
    assert review.status_code == 200
    assert review.json()["review_status"] == "approved"


def test_comparison_list_starts_empty(api_client):
    client, headers = api_client
    response = client.get("/api/v1/comparisons/", headers=headers)

    assert response.status_code == 200
    assert response.json() == []


def test_control_categories_and_mappings(api_client):
    client, headers = api_client
    categories = client.get("/api/v1/controls/categories", headers=headers)
    mappings = client.get("/api/v1/controls/mappings", headers=headers)

    assert categories.status_code == 200
    assert len(categories.json()) == 3
    assert mappings.status_code == 200
    assert mappings.json() == []


def test_reports_start_empty(api_client):
    client, headers = api_client
    response = client.get("/api/v1/reports/", headers=headers)

    assert response.status_code == 200
    assert response.json() == []


def test_audit_logs_include_login(api_client):
    client, headers = api_client
    response = client.get("/api/v1/audit/", headers=headers)

    assert response.status_code == 200
    assert any(log["action"] == "user_login" for log in response.json())


def test_production_rejects_placeholder_secret():
    with pytest.raises(ValidationError, match="unique SECRET_KEY"):
        Settings(
            _env_file=None,
            ROIS_ENV="production",
            SECRET_KEY="replace-with-a-random-secret-of-at-least-32-characters",
        )


def test_production_rejects_sqlite_database():
    with pytest.raises(ValidationError, match="requires PostgreSQL"):
        Settings(
            _env_file=None,
            ROIS_ENV="production",
            SECRET_KEY="unique-production-secret-key-at-least-32-characters",
            DATABASE_URL="sqlite:///./production.db",
            CORS_ORIGINS="https://demo.example.com",
        )


def test_production_accepts_postgres_and_https_cors():
    configured = Settings(
        _env_file=None,
        ROIS_ENV="production",
        SECRET_KEY="unique-production-secret-key-at-least-32-characters",
        DATABASE_URL="postgresql+psycopg://rois_user:placeholder@db.example.com/rois",
        CORS_ORIGINS="https://demo.example.com",
    )
    assert configured.DATABASE_URL.startswith("postgresql+psycopg://")


def test_legacy_postgres_url_is_normalized():
    configured = Settings(
        _env_file=None,
        ROIS_ENV="production",
        SECRET_KEY="unique-production-secret-key-at-least-32-characters",
        DATABASE_URL="postgres://user@db.example.com:5432/rois",
        CORS_ORIGINS="https://demo.example.com",
    )
    assert configured.normalized_database_url.startswith("postgresql+psycopg://")


def test_separate_migration_url_is_validated_in_production():
    configured = Settings(
        _env_file=None,
        ROIS_ENV="production",
        SECRET_KEY="unique-production-secret-key-at-least-32-characters",
        DATABASE_URL="postgresql://app-user@db.example.com:6543/rois",
        MIGRATION_DATABASE_URL="postgresql://migration-user@db.example.com:5432/rois",
        CORS_ORIGINS="https://demo.example.com",
    )
    assert configured.normalized_migration_database_url.startswith(
        "postgresql+psycopg://"
    )


def test_supabase_storage_requires_configuration_placeholders():
    with pytest.raises(ValidationError, match="SUPABASE_URL"):
        Settings(
            _env_file=None,
            ROIS_ENV="development",
            DOCUMENT_STORAGE_PROVIDER="supabase",
            SUPABASE_URL="",
            SUPABASE_SERVICE_ROLE_KEY="",
            SUPABASE_STORAGE_BUCKET="rois-documents",
        )


def test_rejects_non_pdf_signature(api_client):
    client, headers = api_client
    response = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        data={"title": "Invalid upload"},
        files={"file": ("malicious.pdf", b"not a pdf", "application/pdf")},
    )
    assert response.status_code == 400
    assert "signature" in response.json()["detail"].lower()


def test_rejects_corrupted_pdf(api_client):
    client, headers = api_client
    response = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        data={"title": "Corrupted upload"},
        files={"file": ("broken.pdf", b"%PDF-1.7\nnot really a pdf", "application/pdf")},
    )
    assert response.status_code == 400


def test_rejects_password_protected_pdf(api_client):
    client, headers = api_client
    source = BytesIO()
    pdf = canvas.Canvas(source)
    pdf.drawString(48, 720, "Protected demonstration text.")
    pdf.save()

    writer = PdfWriter()
    writer.append(BytesIO(source.getvalue()))
    writer.encrypt("test-password")
    protected = BytesIO()
    writer.write(protected)

    response = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        data={"title": "Protected upload"},
        files={"file": ("protected.pdf", protected.getvalue(), "application/pdf")},
    )
    assert response.status_code == 400
    assert "password-protected" in response.json()["detail"].lower()


def test_duplicate_upload_is_rejected(api_client):
    client, headers = api_client
    first = _upload_document(client, headers)
    original = client.get(f"/api/v1/documents/{first['id']}/pdf", headers=headers)
    assert original.status_code == 200
    duplicate = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        data={"title": "Duplicate title"},
        files={"file": ("different-name.pdf", original.content, "application/pdf")},
    )
    assert first["id"] > 0
    assert duplicate.status_code == 409


def test_same_upload_id_is_idempotent(api_client):
    client, headers = api_client
    payload = _create_demo_pdf()
    response = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        data={
            "title": "[DEMONSTRATION ONLY] Idempotent upload",
            "upload_id": "idempotent-upload-test",
        },
        files={"file": ("demo.pdf", payload, "application/pdf")},
    )
    assert response.status_code == 200
    first = response.json()

    retry = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        data={
            "title": "[DEMONSTRATION ONLY] Idempotent upload",
            "upload_id": "idempotent-upload-test",
        },
        files={"file": ("demo.pdf", payload, "application/pdf")},
    )
    assert retry.status_code == 200
    assert retry.json()["id"] == first["id"]


def test_new_upload_id_with_duplicate_content_is_rejected(api_client):
    client, headers = api_client
    payload = _create_demo_pdf()
    first = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        data={"title": "[DEMONSTRATION ONLY] First hash", "upload_id": "upload-id-one"},
        files={"file": ("demo.pdf", payload, "application/pdf")},
    )
    assert first.status_code == 200

    duplicate = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        data={"title": "[DEMONSTRATION ONLY] Second hash", "upload_id": "upload-id-two"},
        files={"file": ("demo.pdf", payload, "application/pdf")},
    )
    assert duplicate.status_code == 409


def test_document_delete_removes_record(api_client):
    client, headers = api_client
    document = _upload_document(client, headers)

    response = client.delete(
        f"/api/v1/documents/{document['id']}",
        headers=headers,
    )
    assert response.status_code == 200
    listing = client.get("/api/v1/documents/", headers=headers)
    assert listing.status_code == 200
    assert all(item["id"] != document["id"] for item in listing.json()["items"])


def test_logout_revokes_token(api_client):
    client, headers = api_client
    logout = client.post("/api/v1/auth/logout", headers=headers)
    assert logout.status_code == 200

    profile = client.get("/api/v1/auth/me", headers=headers)
    assert profile.status_code == 401

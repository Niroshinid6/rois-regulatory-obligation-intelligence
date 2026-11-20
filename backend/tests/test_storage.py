import asyncio
from io import BytesIO

import pytest
import httpx
from storage3.exceptions import StorageApiError

from app.models.storage_cleanup import StorageCleanupTask
from app.services.pdf_extractor import PDFExtractionService
from app.services.storage.base import (
    StorageDownloadError,
    StorageNotFoundError,
    StorageUploadError,
)
from app.services.storage.local import LocalStorageProvider
from app.services.storage.supabase import SupabaseStorageProvider


def run(coro):
    return asyncio.run(coro)


def test_local_storage_upload_open_delete(tmp_path):
    provider = LocalStorageProvider(str(tmp_path / "documents"))
    key = "documents/1/12345678-" + ("a" * 64) + ".pdf"
    payload = b"%PDF-1.7\nDEMONSTRATION\n%%EOF"

    uploaded = run(
        provider.upload(
            key,
            BytesIO(payload),
            "application/pdf",
            len(payload),
        )
    )
    assert uploaded.key == key
    assert uploaded.size == len(payload)

    downloaded = run(provider.open(key))
    try:
        assert downloaded.stream.read() == payload
    finally:
        downloaded.stream.close()

    assert run(provider.exists(key)) is True
    run(provider.delete(key))
    assert run(provider.exists(key)) is False

    with pytest.raises(StorageNotFoundError):
        run(provider.open(key))


def test_local_storage_rejects_path_traversal(tmp_path):
    provider = LocalStorageProvider(str(tmp_path / "documents"))
    with pytest.raises(StorageUploadError):
        run(
            provider.upload(
                "../outside.pdf",
                BytesIO(b"%PDF-1.7\n%%EOF"),
                "application/pdf",
                15,
            )
        )


def test_local_storage_detects_size_mismatch(tmp_path):
    provider = LocalStorageProvider(str(tmp_path / "documents"))
    key = "documents/1/size-check-12345678901234567890123456789012.pdf"
    with pytest.raises(StorageUploadError):
        run(
            provider.upload(
                key,
                BytesIO(b"%PDF-1.7"),
                "application/pdf",
                99,
            )
        )


def test_pdf_extractor_accepts_seekable_stream(tmp_path):
    from reportlab.pdfgen import canvas

    pdf_path = tmp_path / "stream.pdf"
    pdf = canvas.Canvas(str(pdf_path))
    pdf.drawString(48, 720, "DEMONSTRATION DOCUMENT")
    pdf.drawString(48, 704, "All entities shall submit a report within 30 days.")
    pdf.save()

    with pdf_path.open("rb") as stream:
        extracted = PDFExtractionService.extract_document(stream)

    assert extracted["page_count"] == 1
    assert "shall submit" in extracted["pages"][0]["text"]


class _MockSession:
    async def aclose(self):
        return None


class _MockBucket:
    def __init__(self, objects=None):
        self.objects = objects if objects is not None else {}

    async def exists(self, key):
        return key in self.objects

    async def upload(self, key, payload, file_options):
        self.objects[key] = payload
        return {"Key": key}

    async def download(self, key):
        if key not in self.objects:
            raise StorageApiError("Object not found", "404", 404)
        return self.objects[key]

    async def remove(self, paths):
        for key in paths:
            self.objects.pop(key, None)
        return []


class _MockSupabaseClient:
    def __init__(self, bucket):
        self.bucket = bucket
        self.session = _MockSession()

    def from_(self, bucket_name):
        return self.bucket


def test_supabase_provider_upload_open_delete_with_mock():
    objects = {}
    bucket = _MockBucket(objects)
    client = _MockSupabaseClient(bucket)
    provider = SupabaseStorageProvider(
        "https://example.supabase.co",
        "FAKE_SERVICE_ROLE_KEY_NOT_A_REAL_SECRET",
        "rois-documents",
        client_factory=lambda headers: client,
    )
    key = "documents/1/12345678-" + ("a" * 64) + ".pdf"
    payload = b"%PDF-1.7\nDEMONSTRATION\n%%EOF"

    uploaded = run(
        provider.upload(
            key,
            BytesIO(payload),
            "application/pdf",
            len(payload),
        )
    )
    assert uploaded.size == len(payload)
    assert objects[key] == payload

    downloaded = run(provider.open(key))
    try:
        assert downloaded.stream.read() == payload
    finally:
        downloaded.stream.close()

    run(provider.delete(key))
    assert key not in objects


def test_supabase_provider_missing_object():
    bucket = _MockBucket({})
    client = _MockSupabaseClient(bucket)
    provider = SupabaseStorageProvider(
        "https://example.supabase.co",
        "FAKE_SERVICE_ROLE_KEY_NOT_A_REAL_SECRET",
        "rois-documents",
        client_factory=lambda headers: client,
    )
    with pytest.raises(StorageNotFoundError):
        run(
            provider.open(
                "documents/1/12345678-" + ("a" * 64) + ".pdf"
            )
        )


def test_supabase_provider_timeout_is_translated():
    class TimeoutBucket:
        async def download(self, key):
            raise httpx.TimeoutException("timed out")

    class TimeoutClient:
        session = _MockSession()

        def from_(self, bucket_name):
            return TimeoutBucket()

    provider = SupabaseStorageProvider(
        "https://example.supabase.co",
        "FAKE_SERVICE_ROLE_KEY_NOT_A_REAL_SECRET",
        "rois-documents",
        client_factory=lambda headers: TimeoutClient(),
    )
    with pytest.raises(StorageDownloadError):
        run(
            provider.open(
                "documents/1/12345678-" + ("a" * 64) + ".pdf"
            )
        )

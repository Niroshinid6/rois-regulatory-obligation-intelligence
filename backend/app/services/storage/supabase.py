import hashlib
import re
import tempfile
from typing import BinaryIO, Callable

import httpx
from storage3 import AsyncStorageClient
from storage3.exceptions import StorageApiError

from app.services.storage.base import (
    StorageDeleteError,
    StorageDownloadError,
    StorageDownloadResult,
    StorageNotFoundError,
    StorageUploadError,
    StorageUploadResult,
)


VALID_KEY = re.compile(r"^documents/[A-Za-z0-9_-]+/[A-Za-z0-9_-]+-[A-Fa-f0-9]{64}\.pdf$")


class SupabaseStorageProvider:
    def __init__(
        self,
        url: str,
        service_role_key: str,
        bucket: str,
        timeout_seconds: float = 30.0,
        client_factory: Callable[..., AsyncStorageClient] | None = None,
    ):
        if not url.strip().startswith("https://"):
            raise StorageUploadError("Supabase URL must use HTTPS.")
        if not service_role_key.strip():
            raise StorageUploadError("Supabase service-role key is required.")
        if not bucket.strip():
            raise StorageUploadError("Supabase storage bucket is required.")

        self.url = url.rstrip("/")
        self.service_role_key = service_role_key
        self.bucket = bucket.strip()
        self.timeout_seconds = timeout_seconds
        self.client_factory = client_factory

    def _validate_key(self, key: str) -> None:
        if not VALID_KEY.fullmatch(key):
            raise StorageUploadError("Invalid storage object key.")

    def _create_client(self) -> tuple[AsyncStorageClient, httpx.AsyncClient | None]:
        headers = {
            "apiKey": self.service_role_key,
            "Authorization": f"Bearer {self.service_role_key}",
        }
        if self.client_factory is not None:
            return self.client_factory(headers=headers), None

        http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout_seconds),
            follow_redirects=True,
        )
        client = AsyncStorageClient(
            f"{self.url}/storage/v1",
            headers,
            http_client=http_client,
        )
        return client, http_client

    @staticmethod
    def _is_missing_error(exc: Exception) -> bool:
        if isinstance(exc, StorageApiError):
            status = getattr(exc, "status", None)
            code = getattr(exc, "code", None)
            return str(status) == "404" or str(code) == "404"
        return False

    async def upload(
        self,
        key: str,
        content: BinaryIO,
        content_type: str,
        content_length: int,
    ) -> StorageUploadResult:
        self._validate_key(key)
        client, http_client = self._create_client()
        try:
            content.seek(0)
            payload = content.read(content_length)
            size = len(payload)
            if size != content_length:
                raise StorageUploadError("Uploaded size did not match the declared size.")

            sha256 = hashlib.sha256(payload).hexdigest()
            bucket = client.from_(self.bucket)
            if await bucket.exists(key):
                existing = await bucket.download(key)
                if len(existing) != size or hashlib.sha256(existing).hexdigest() != sha256:
                    raise StorageUploadError("Existing object conflicts with upload content.")
                return StorageUploadResult(key=key, size=size, sha256=sha256)

            await bucket.upload(
                key,
                payload,
                {
                    "content-type": content_type,
                    "cache-control": "3600",
                    "upsert": "false",
                },
            )
            return StorageUploadResult(key=key, size=size, sha256=sha256)
        except StorageUploadError:
            raise
        except StorageApiError as exc:
            if self._is_missing_error(exc):
                raise StorageUploadError("Supabase Storage object was missing during upload.") from exc
            raise StorageUploadError("Supabase Storage rejected the upload.") from exc
        except (httpx.TimeoutException, httpx.HTTPError, TimeoutError) as exc:
            raise StorageUploadError("Supabase Storage upload timed out or failed.") from exc
        except Exception as exc:
            raise StorageUploadError("Supabase Storage upload failed.") from exc
        finally:
            await client.session.aclose()
            if http_client is not None:
                await http_client.aclose()

    async def open(self, key: str) -> StorageDownloadResult:
        self._validate_key(key)
        client, http_client = self._create_client()
        try:
            bucket = client.from_(self.bucket)
            payload = await bucket.download(key)
            sha256 = hashlib.sha256(payload).hexdigest()
            stream = tempfile.SpooledTemporaryFile(max_size=8 * 1024 * 1024, mode="w+b")
            stream.write(payload)
            stream.seek(0)
            return StorageDownloadResult(
                key=key,
                content_type="application/pdf",
                size=len(payload),
                sha256=sha256,
                stream=stream,
            )
        except StorageApiError as exc:
            if self._is_missing_error(exc):
                raise StorageNotFoundError("The stored PDF was not found.") from exc
            raise StorageDownloadError("Supabase Storage download failed.") from exc
        except (httpx.TimeoutException, httpx.HTTPError, TimeoutError) as exc:
            raise StorageDownloadError("Supabase Storage download timed out or failed.") from exc
        except Exception as exc:
            raise StorageDownloadError("Supabase Storage download failed.") from exc
        finally:
            await client.session.aclose()
            if http_client is not None:
                await http_client.aclose()

    async def exists(self, key: str) -> bool:
        self._validate_key(key)
        client, http_client = self._create_client()
        try:
            return await client.from_(self.bucket).exists(key)
        except StorageApiError as exc:
            if self._is_missing_error(exc):
                return False
            raise StorageDownloadError("Could not verify the Supabase Storage object.") from exc
        except (httpx.TimeoutException, httpx.HTTPError, TimeoutError) as exc:
            raise StorageDownloadError("Supabase Storage verification timed out or failed.") from exc
        finally:
            await client.session.aclose()
            if http_client is not None:
                await http_client.aclose()

    async def delete(self, key: str) -> None:
        self._validate_key(key)
        client, http_client = self._create_client()
        try:
            await client.from_(self.bucket).remove([key])
        except StorageApiError as exc:
            if self._is_missing_error(exc):
                return
            raise StorageDeleteError("Supabase Storage deletion failed.") from exc
        except (httpx.TimeoutException, httpx.HTTPError, TimeoutError) as exc:
            raise StorageDeleteError("Supabase Storage deletion timed out or failed.") from exc
        except Exception as exc:
            raise StorageDeleteError("Supabase Storage deletion failed.") from exc
        finally:
            await client.session.aclose()
            if http_client is not None:
                await http_client.aclose()

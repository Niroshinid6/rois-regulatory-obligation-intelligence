import hashlib
import re
from pathlib import Path
from typing import BinaryIO

from app.services.storage.base import (
    StorageDeleteError,
    StorageDownloadError,
    StorageDownloadResult,
    StorageNotFoundError,
    StorageUploadError,
    StorageUploadResult,
)


VALID_KEY = re.compile(r"^documents/[A-Za-z0-9_-]+/[A-Za-z0-9_-]+-[A-Fa-f0-9]{64}\.pdf$")


class LocalStorageProvider:
    def __init__(self, root: str):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, key: str) -> Path:
        if not VALID_KEY.fullmatch(key):
            raise StorageUploadError("Invalid storage object key.")
        return self.root / key

    async def upload(
        self,
        key: str,
        content: BinaryIO,
        content_type: str,
        content_length: int,
    ) -> StorageUploadResult:
        try:
            destination = self._resolve(key)
            destination.parent.mkdir(parents=True, exist_ok=True)
            content.seek(0)
            hasher = hashlib.sha256()
            size = 0
            mode = "xb" if not destination.exists() else "wb"
            with destination.open(mode) as output:
                while True:
                    chunk = content.read(64 * 1024)
                    if not chunk:
                        break
                    output.write(chunk)
                    hasher.update(chunk)
                    size += len(chunk)
            if size != content_length:
                destination.unlink(missing_ok=True)
                raise StorageUploadError("Uploaded size did not match the declared size.")
            return StorageUploadResult(key=key, size=size, sha256=hasher.hexdigest())
        except StorageUploadError:
            raise
        except Exception as exc:
            raise StorageUploadError("Could not store the PDF.") from exc

    async def open(self, key: str) -> StorageDownloadResult:
        try:
            path = self._resolve(key)
            if not path.is_file():
                raise StorageNotFoundError("The stored PDF was not found.")
            stream = path.open("rb")
            size = path.stat().st_size
            hasher = hashlib.sha256()
            with path.open("rb") as source:
                for chunk in iter(lambda: source.read(64 * 1024), b""):
                    hasher.update(chunk)
            return StorageDownloadResult(
                key=key,
                content_type="application/pdf",
                size=size,
                sha256=hasher.hexdigest(),
                stream=stream,
            )
        except StorageNotFoundError:
            raise
        except Exception as exc:
            raise StorageDownloadError("Could not open the stored PDF.") from exc

    async def exists(self, key: str) -> bool:
        try:
            return self._resolve(key).is_file()
        except StorageUploadError:
            return False

    async def delete(self, key: str) -> None:
        try:
            path = self._resolve(key)
            path.unlink(missing_ok=True)
        except Exception as exc:
            raise StorageDeleteError("Could not delete the stored PDF.") from exc

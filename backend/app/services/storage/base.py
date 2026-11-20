from dataclasses import dataclass
from typing import BinaryIO, Protocol


@dataclass
class StorageUploadResult:
    key: str
    size: int
    sha256: str


@dataclass
class StorageDownloadResult:
    key: str
    content_type: str
    size: int
    sha256: str | None
    stream: BinaryIO


class StorageError(Exception):
    pass


class StorageNotFoundError(StorageError):
    pass


class StorageUploadError(StorageError):
    pass


class StorageDownloadError(StorageError):
    pass


class StorageDeleteError(StorageError):
    pass


class StorageVerificationError(StorageError):
    pass


class StorageProvider(Protocol):
    async def upload(
        self,
        key: str,
        content: BinaryIO,
        content_type: str,
        content_length: int,
    ) -> StorageUploadResult:
        ...

    async def open(self, key: str) -> StorageDownloadResult:
        ...

    async def exists(self, key: str) -> bool:
        ...

    async def delete(self, key: str) -> None:
        ...

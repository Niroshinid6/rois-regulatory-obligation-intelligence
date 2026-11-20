from app.core.config import settings
from app.services.storage.base import StorageError
from app.services.storage.local import LocalStorageProvider
from app.services.storage.supabase import SupabaseStorageProvider


class SupabaseStorageNotImplemented(StorageError):
    pass


def get_storage_provider():
    provider = settings.DOCUMENT_STORAGE_PROVIDER.strip().lower()
    if provider == "local":
        return LocalStorageProvider(settings.UPLOAD_DIR)
    if provider == "supabase":
        return SupabaseStorageProvider(
            url=settings.SUPABASE_URL,
            service_role_key=settings.SUPABASE_SERVICE_ROLE_KEY,
            bucket=settings.SUPABASE_STORAGE_BUCKET,
        )
    raise StorageError("Unsupported document storage provider.")

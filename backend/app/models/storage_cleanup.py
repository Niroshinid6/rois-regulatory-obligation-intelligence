from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.core.database import Base


class StorageCleanupTask(Base):
    __tablename__ = "storage_cleanup_tasks"

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, nullable=True, index=True)
    storage_provider = Column(String(20), nullable=False)
    storage_object_key = Column(String(1000), nullable=False)
    operation = Column(String(20), nullable=False, default="delete")
    status = Column(String(32), nullable=False, default="pending", index=True)
    attempts = Column(Integer, nullable=False, default=0)
    next_retry_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    object_deleted_at = Column(DateTime, nullable=True)
    database_deleted_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow(), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.utcnow(),
        onupdate=lambda: datetime.utcnow(),
        nullable=False,
    )

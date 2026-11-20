"""add document storage metadata and cleanup tasks

Revision ID: 8f2c3d4e5a61
Revises: 7c1d5b4e8a33
Create Date: 2026-11-20
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8f2c3d4e5a61"
down_revision: Union[str, None] = "7c1d5b4e8a33"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("documents") as batch_op:
        batch_op.alter_column("file_path", existing_type=sa.String(length=1000), nullable=True)
        batch_op.add_column(sa.Column("storage_provider", sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column("storage_object_key", sa.String(length=1000), nullable=True))
        batch_op.add_column(
            sa.Column("storage_status", sa.String(length=32), nullable=False, server_default="legacy")
        )
        batch_op.add_column(sa.Column("storage_migrated_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("storage_upload_id", sa.String(length=64), nullable=True))
        batch_op.add_column(
            sa.Column("processing_status", sa.String(length=32), nullable=False, server_default="not_started")
        )
        batch_op.create_index(
            "ix_documents_storage_upload_id",
            ["storage_upload_id"],
            unique=True,
        )

    op.execute(
        "UPDATE documents SET storage_provider = 'local', "
        "storage_status = 'legacy', processing_status = CASE "
        "WHEN status = 'processed' THEN 'completed' "
        "WHEN status = 'requires_ocr' THEN 'requires_ocr' "
        "WHEN status = 'failed' THEN 'processing_failed' "
        "WHEN status = 'processing' THEN 'processing' "
        "WHEN status = 'queued' THEN 'pending' "
        "ELSE 'not_started' END "
        "WHERE storage_status = 'legacy'"
    )

    op.create_table(
        "storage_cleanup_tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=True),
        sa.Column("storage_provider", sa.String(length=20), nullable=False),
        sa.Column("storage_object_key", sa.String(length=1000), nullable=False),
        sa.Column("operation", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("next_retry_at", sa.DateTime(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("object_deleted_at", sa.DateTime(), nullable=True),
        sa.Column("database_deleted_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_storage_cleanup_tasks_document_id",
        "storage_cleanup_tasks",
        ["document_id"],
        unique=False,
    )
    op.create_index(
        "ix_storage_cleanup_tasks_status",
        "storage_cleanup_tasks",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    raise RuntimeError(
        "Downgrade refused: storage metadata and cleanup tasks are non-destructive "
        "and must be preserved for object recovery."
    )

"""add document page OCR metadata

Revision ID: 2c6c4a9f4d21
Revises: 45055afc12b2
Create Date: 2026-11-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2c6c4a9f4d21"
down_revision: Union[str, None] = "45055afc12b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "document_pages",
        sa.Column("extraction_method", sa.String(length=20), nullable=False, server_default="pdf_text"),
    )
    op.add_column("document_pages", sa.Column("ocr_confidence", sa.Float(), nullable=True))
    op.add_column(
        "document_pages",
        sa.Column("requires_human_review", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("document_pages", "requires_human_review")
    op.drop_column("document_pages", "ocr_confidence")
    op.drop_column("document_pages", "extraction_method")

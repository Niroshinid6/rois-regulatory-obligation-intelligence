"""add durable revoked token registry

Revision ID: 7c1d5b4e8a33
Revises: 2c6c4a9f4d21
Create Date: 2026-11-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7c1d5b4e8a33"
down_revision: Union[str, None] = "2c6c4a9f4d21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "revoked_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("jti", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("jti"),
    )
    op.create_index(op.f("ix_revoked_tokens_id"), "revoked_tokens", ["id"], unique=False)
    op.create_index(op.f("ix_revoked_tokens_jti"), "revoked_tokens", ["jti"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_revoked_tokens_jti"), table_name="revoked_tokens")
    op.drop_index(op.f("ix_revoked_tokens_id"), table_name="revoked_tokens")
    op.drop_table("revoked_tokens")

"""Move status to users table

Revision ID: 1a2b3c4d5e6f
Revises: 7b3f2a9a9e12
Create Date: 2025-02-01 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from modules.models.types import DocumentStatusEnum

# revision identifiers, used by Alembic.
revision: str = "1a2b3c4d5e6f"
down_revision: Union[str, None] = "7b3f2a9a9e12"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "status",
            sa.Enum(DocumentStatusEnum, name="document_status_enum", native_enum=False),
            nullable=False,
            server_default=DocumentStatusEnum.DRAFT.value,
        ),
    )
    op.add_column("users", sa.Column("rejection_reason", sa.String(), nullable=True))

    op.drop_column("user_documents", "status")
    op.drop_column("user_documents", "rejection_reason")


def downgrade() -> None:
    op.add_column(
        "user_documents",
        sa.Column(
            "rejection_reason",
            sa.String(),
            nullable=True,
        ),
    )
    op.add_column(
        "user_documents",
        sa.Column(
            "status",
            sa.Enum(DocumentStatusEnum, name="document_status_enum", native_enum=False),
            nullable=False,
            server_default=DocumentStatusEnum.DRAFT.value,
        ),
    )

    op.drop_column("users", "rejection_reason")
    op.drop_column("users", "status")
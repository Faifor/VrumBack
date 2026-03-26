"""add email verification requests

Revision ID: 8e1a2c7d4f90
Revises: 2f4a6c8e9b10
Create Date: 2026-03-26 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8e1a2c7d4f90"
down_revision: Union[str, None] = "2f4a6c8e9b10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "email_verification_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_used", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_email_verification_requests_email"),
        "email_verification_requests",
        ["email"],
        unique=False,
    )
    op.create_index(
        op.f("ix_email_verification_requests_id"),
        "email_verification_requests",
        ["id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_email_verification_requests_id"),
        table_name="email_verification_requests",
    )
    op.drop_index(
        op.f("ix_email_verification_requests_email"),
        table_name="email_verification_requests",
    )
    op.drop_table("email_verification_requests")

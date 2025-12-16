"""Add login attempt tracking to users

Revision ID: f5d2b1c4a8e7
Revises: c5b9a4b7d9e2
Create Date: 2025-07-19 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f5d2b1c4a8e7"
down_revision: Union[str, None] = "c5b9a4b7d9e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "failed_login_attempts",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "last_failed_login_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "last_failed_login_at")
    op.drop_column("users", "failed_login_attempts")
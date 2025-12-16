"""Change selected fields to numeric types

Revision ID: 3a7d9f0e9b5f
Revises: f5d2b1c4a8e7
Create Date: 2025-07-20 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3a7d9f0e9b5f"
down_revision: Union[str, None] = "f5d2b1c4a8e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Existing data may be encrypted strings; null them to allow type change.
    op.execute(
        """
        UPDATE users
        SET inn = NULL, passport = NULL, bank_account = NULL
        """
    )
    op.execute("UPDATE user_documents SET amount = NULL")

    op.alter_column(
        "users",
        "inn",
        type_=sa.BigInteger(),
        existing_nullable=True,
        postgresql_using="inn::bigint",
    )
    op.alter_column(
        "users",
        "passport",
        type_=sa.BigInteger(),
        existing_nullable=True,
        postgresql_using="passport::bigint",
    )
    op.alter_column(
        "users",
        "bank_account",
        type_=sa.Numeric(precision=32, scale=0),
        existing_nullable=True,
        postgresql_using="bank_account::numeric",
    )
    op.alter_column(
        "user_documents",
        "amount",
        type_=sa.Numeric(precision=18, scale=0),
        existing_nullable=True,
        postgresql_using="amount::numeric",
    )


def downgrade() -> None:
    op.alter_column("user_documents", "amount", type_=sa.String(), existing_nullable=True)
    op.alter_column("users", "bank_account", type_=sa.String(), existing_nullable=True)
    op.alter_column("users", "passport", type_=sa.String(), existing_nullable=True)
    op.alter_column("users", "inn", type_=sa.String(), existing_nullable=True)
"""Move personal data to users table

Revision ID: 9c9e7f4913f3
Revises: e964c9e93a58
Create Date: 2024-07-03 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9c9e7f4913f3"
down_revision: Union[str, None] = "e964c9e93a58"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("full_name", sa.String(), nullable=True))
    op.add_column("users", sa.Column("address", sa.String(), nullable=True))
    op.add_column("users", sa.Column("passport", sa.String(), nullable=True))
    op.add_column("users", sa.Column("phone", sa.String(), nullable=True))
    op.add_column("users", sa.Column("bank_account", sa.String(), nullable=True))

    op.drop_column("user_documents", "full_name")
    op.drop_column("user_documents", "address")
    op.drop_column("user_documents", "passport")
    op.drop_column("user_documents", "phone")
    op.drop_column("user_documents", "bank_account")


def downgrade() -> None:
    op.add_column("user_documents", sa.Column("bank_account", sa.String(), nullable=True))
    op.add_column("user_documents", sa.Column("phone", sa.String(), nullable=False))
    op.add_column("user_documents", sa.Column("passport", sa.String(), nullable=False))
    op.add_column("user_documents", sa.Column("address", sa.String(), nullable=False))
    op.add_column("user_documents", sa.Column("full_name", sa.String(), nullable=False))

    op.drop_column("users", "bank_account")
    op.drop_column("users", "phone")
    op.drop_column("users", "passport")
    op.drop_column("users", "address")
    op.drop_column("users", "full_name")
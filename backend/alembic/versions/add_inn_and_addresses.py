"""Add INN and split address fields on users

Revision ID: 7b3f2a9a9e12
Revises: 9c9e7f4913f3
Create Date: 2025-01-01 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7b3f2a9a9e12"
down_revision: Union[str, None] = "9c9e7f4913f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("inn", sa.String(), nullable=True))
    op.add_column("users", sa.Column("registration_address", sa.String(), nullable=True))
    op.add_column("users", sa.Column("residential_address", sa.String(), nullable=True))

    op.execute(
        """
        UPDATE users
        SET registration_address = COALESCE(address, registration_address),
            residential_address = COALESCE(address, residential_address),
            full_name = COALESCE(full_name, TRIM(COALESCE(first_name, '') || ' ' || COALESCE(last_name, '')))
        """
    )

    op.drop_column("users", "address")
    op.drop_column("users", "first_name")
    op.drop_column("users", "last_name")


def downgrade() -> None:
    op.add_column("users", sa.Column("last_name", sa.String(), nullable=False, server_default=""))
    op.add_column("users", sa.Column("first_name", sa.String(), nullable=False, server_default=""))
    op.add_column("users", sa.Column("address", sa.String(), nullable=True))

    op.execute(
        """
        UPDATE users
        SET address = COALESCE(registration_address, residential_address, address),
            first_name = COALESCE(NULLIF(full_name, ''), first_name),
            last_name = ''
        """
    )

    op.drop_column("users", "residential_address")
    op.drop_column("users", "registration_address")
    op.drop_column("users", "inn")
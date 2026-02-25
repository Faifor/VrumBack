"""add inventory tables

Revision ID: 7f3c2d1a9e4b
Revises: 4b7f6c2e1a9d
Create Date: 2026-02-25 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7f3c2d1a9e4b"
down_revision: Union[str, None] = "4b7f6c2e1a9d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "locations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("address", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_locations_id"), "locations", ["id"], unique=False)

    op.create_table(
        "bikes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("number", sa.String(), nullable=False),
        sa.Column("vin", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), server_default="free", nullable=False),
        sa.Column("purchase_date", sa.Date(), nullable=True),
        sa.Column("last_service_date", sa.Date(), nullable=True),
        sa.Column("next_service_date", sa.Date(), nullable=True),
        sa.Column("location_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("number"),
        sa.UniqueConstraint("vin"),
    )
    op.create_index(op.f("ix_bikes_id"), "bikes", ["id"], unique=False)
    op.create_index(op.f("ix_bikes_number"), "bikes", ["number"], unique=False)
    op.create_index(op.f("ix_bikes_vin"), "bikes", ["vin"], unique=False)

    op.create_table(
        "batteries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("number", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("voltage", sa.Integer(), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(), server_default="free", nullable=False),
        sa.Column("purchase_date", sa.Date(), nullable=True),
        sa.Column("location_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("number"),
    )
    op.create_index(op.f("ix_batteries_id"), "batteries", ["id"], unique=False)
    op.create_index(op.f("ix_batteries_number"), "batteries", ["number"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_batteries_number"), table_name="batteries")
    op.drop_index(op.f("ix_batteries_id"), table_name="batteries")
    op.drop_table("batteries")

    op.drop_index(op.f("ix_bikes_vin"), table_name="bikes")
    op.drop_index(op.f("ix_bikes_number"), table_name="bikes")
    op.drop_index(op.f("ix_bikes_id"), table_name="bikes")
    op.drop_table("bikes")

    op.drop_index(op.f("ix_locations_id"), table_name="locations")
    op.drop_table("locations")
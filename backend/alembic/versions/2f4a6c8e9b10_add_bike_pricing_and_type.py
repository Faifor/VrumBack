"""add bike pricing table and bike type_id

Revision ID: 2f4a6c8e9b10
Revises: 6d9a2b4c1f8e
Create Date: 2026-02-27
"""

from typing import Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2f4a6c8e9b10"
down_revision: Union[str, None] = "6d9a2b4c1f8e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("bikes", sa.Column("type_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_bikes_type_id"), "bikes", ["type_id"], unique=False)

    op.create_table(
        "bike_pricing",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("type_id", sa.Integer(), nullable=False),
        sa.Column("name_type", sa.String(), nullable=False),
        sa.Column("min_weeks_count", sa.Integer(), nullable=False),
        sa.Column("max_weeks_count", sa.Integer(), nullable=False),
        sa.Column("amount_weeks", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bike_pricing_id"), "bike_pricing", ["id"], unique=False)
    op.create_index(op.f("ix_bike_pricing_type_id"), "bike_pricing", ["type_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_bike_pricing_type_id"), table_name="bike_pricing")
    op.drop_index(op.f("ix_bike_pricing_id"), table_name="bike_pricing")
    op.drop_table("bike_pricing")

    op.drop_index(op.f("ix_bikes_type_id"), table_name="bikes")
    op.drop_column("bikes", "type_id")
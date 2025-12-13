"""Add activity flag and date fields to user documents

Revision ID: c5b9a4b7d9e2
Revises: 1a2b3c4d5e6f
Create Date: 2025-05-19 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c5b9a4b7d9e2"
down_revision: Union[str, None] = "1a2b3c4d5e6f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("user_documents")
    op.create_table(
        "user_documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("contract_number", sa.String(), nullable=True),
        sa.Column("bike_serial", sa.String(), nullable=True),
        sa.Column("akb1_serial", sa.String(), nullable=True),
        sa.Column("akb2_serial", sa.String(), nullable=True),
        sa.Column("akb3_serial", sa.String(), nullable=True),
        sa.Column("amount", sa.String(), nullable=True),
        sa.Column("amount_text", sa.String(), nullable=True),
        sa.Column("weeks_count", sa.Integer(), nullable=True),
        sa.Column("filled_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("contract_text", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_documents_id"), "user_documents", ["id"], unique=False)
    op.create_index("ix_user_documents_user_id", "user_documents", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_user_documents_user_id", table_name="user_documents")
    op.drop_index(op.f("ix_user_documents_id"), table_name="user_documents")
    op.drop_table("user_documents")
    op.create_table(
        "user_documents",
        sa.Column("id", sa.INTEGER(), nullable=False),
        sa.Column("user_id", sa.INTEGER(), nullable=False),
        sa.Column("contract_number", sa.VARCHAR(), nullable=True),
        sa.Column("bike_serial", sa.VARCHAR(), nullable=True),
        sa.Column("akb1_serial", sa.VARCHAR(), nullable=True),
        sa.Column("akb2_serial", sa.VARCHAR(), nullable=True),
        sa.Column("akb3_serial", sa.VARCHAR(), nullable=True),
        sa.Column("amount", sa.VARCHAR(), nullable=True),
        sa.Column("amount_text", sa.VARCHAR(), nullable=True),
        sa.Column("weeks_count", sa.INTEGER(), nullable=True),
        sa.Column("filled_date", sa.VARCHAR(), nullable=True),
        sa.Column("end_date", sa.VARCHAR(), nullable=True),
        sa.Column("contract_text", sa.TEXT(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_user_documents_id"), "user_documents", ["id"], unique=False)
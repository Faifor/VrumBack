"""add return acts and damage payment metadata

Revision ID: 6d9a2b4c1f8e
Revises: 7f3c2d1a9e4b
Create Date: 2026-02-27 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "6d9a2b4c1f8e"
down_revision: Union[str, None] = "7f3c2d1a9e4b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("contract_payments", sa.Column("description", sa.String(length=255), nullable=True))
    op.add_column(
        "contract_payments",
        sa.Column("payment_type", sa.String(length=32), nullable=False, server_default="rent"),
    )
    op.create_index(op.f("ix_contract_payments_payment_type"), "contract_payments", ["payment_type"], unique=False)

    op.create_table(
        "return_acts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("return_act_number", sa.String(length=128), nullable=False),
        sa.Column("contract_number", sa.String(), nullable=False),
        sa.Column("rent_end_date", sa.Date(), nullable=False),
        sa.Column("filled_date", sa.Date(), nullable=False),
        sa.Column("bike_serial", sa.String(), nullable=False),
        sa.Column("akb1_serial", sa.String(), nullable=True),
        sa.Column("akb2_serial", sa.String(), nullable=True),
        sa.Column("is_fix_bike", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_fix_akb_1", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_fix_akb_2", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("damage_description", sa.Text(), nullable=True),
        sa.Column("damage_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("debt_term_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("debt_due_date", sa.Date(), nullable=False),
        sa.Column("damage_schedule_payment_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["damage_schedule_payment_id"], ["contract_payments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["document_id"], ["user_documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(op.f("ix_return_acts_id"), "return_acts", ["id"], unique=False)
    op.create_index(op.f("ix_return_acts_user_id"), "return_acts", ["user_id"], unique=False)
    op.create_index(op.f("ix_return_acts_document_id"), "return_acts", ["document_id"], unique=False)
    op.create_index(
        op.f("ix_return_acts_damage_schedule_payment_id"),
        "return_acts",
        ["damage_schedule_payment_id"],
        unique=False,
    )
    op.create_index(op.f("ix_return_acts_return_act_number"), "return_acts", ["return_act_number"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_return_acts_return_act_number"), table_name="return_acts")
    op.drop_index(op.f("ix_return_acts_damage_schedule_payment_id"), table_name="return_acts")
    op.drop_index(op.f("ix_return_acts_document_id"), table_name="return_acts")
    op.drop_index(op.f("ix_return_acts_user_id"), table_name="return_acts")
    op.drop_index(op.f("ix_return_acts_id"), table_name="return_acts")
    op.drop_table("return_acts")

    op.drop_index(op.f("ix_contract_payments_payment_type"), table_name="contract_payments")
    op.drop_column("contract_payments", "payment_type")
    op.drop_column("contract_payments", "description")

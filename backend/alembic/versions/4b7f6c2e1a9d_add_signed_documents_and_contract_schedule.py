"""add signed documents and contract schedule

Revision ID: 4b7f6c2e1a9d
Revises: d2f7c1a9b8e4
Create Date: 2026-02-19 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "4b7f6c2e1a9d"
down_revision: Union[str, None] = "d2f7c1a9b8e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_documents",
        sa.Column("signed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )

    op.create_table(
        "contract_payments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("payment_number", sa.Integer(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("order_id", sa.Integer(), nullable=True),
        sa.Column("payment_id", sa.Integer(), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["user_documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(op.f("ix_contract_payments_id"), "contract_payments", ["id"], unique=False)
    op.create_index(op.f("ix_contract_payments_user_id"), "contract_payments", ["user_id"], unique=False)
    op.create_index(op.f("ix_contract_payments_document_id"), "contract_payments", ["document_id"], unique=False)
    op.create_index(op.f("ix_contract_payments_status"), "contract_payments", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_contract_payments_status"), table_name="contract_payments")
    op.drop_index(op.f("ix_contract_payments_document_id"), table_name="contract_payments")
    op.drop_index(op.f("ix_contract_payments_user_id"), table_name="contract_payments")
    op.drop_index(op.f("ix_contract_payments_id"), table_name="contract_payments")
    op.drop_table("contract_payments")

    op.drop_column("user_documents", "signed")
"""Encrypt numeric personal fields and allow encrypted storage

Revision ID: b538a7f0a7a4
Revises: 3a7d9f0e9b5f
Create Date: 2025-08-28 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b538a7f0a7a4"
down_revision: Union[str, None] = "3a7d9f0e9b5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _get_cipher():
    # Import lazily to avoid issues when Alembic loads config.
    from modules.utils.config import settings
    from modules.utils.document_security import SensitiveDataCipher

    return SensitiveDataCipher(settings.ENCRYPTION_KEY)


def _encrypt_value(value: str | int | None, cipher) -> str | None:
    if value is None:
        return None
    return cipher.encrypt(str(value))


def _decrypt_numeric_value(value: str | None, cipher) -> str | None:
    if value is None:
        return None

    decrypted = cipher.decrypt(str(value))
    normalized = str(decrypted).strip()
    return normalized if normalized.isdigit() else None


def upgrade() -> None:
    op.alter_column("users", "inn", type_=sa.String(), existing_nullable=True)
    op.alter_column("users", "passport", type_=sa.String(), existing_nullable=True)
    op.alter_column("users", "bank_account", type_=sa.String(), existing_nullable=True)
    op.alter_column("user_documents", "amount", type_=sa.String(), existing_nullable=True)

    bind = op.get_bind()
    metadata = sa.MetaData()
    users = sa.Table("users", metadata, autoload_with=bind)
    user_documents = sa.Table("user_documents", metadata, autoload_with=bind)
    cipher = _get_cipher()

    users_result = bind.execute(
        sa.select(users.c.id, users.c.inn, users.c.passport, users.c.bank_account)
    ).fetchall()

    for row in users_result:
        row_map = row._mapping
        updates = {
            field: _encrypt_value(row_map[field], cipher)
            for field in ("inn", "passport", "bank_account")
            if row_map[field] is not None
        }
        if updates:
            bind.execute(users.update().where(users.c.id == row_map["id"]).values(**updates))

    documents_result = bind.execute(
        sa.select(user_documents.c.id, user_documents.c.amount)
    ).fetchall()

    for row in documents_result:
        row_map = row._mapping
        if row_map["amount"] is None:
            continue

        encrypted_amount = _encrypt_value(row_map["amount"], cipher)
        bind.execute(
            user_documents.update()
            .where(user_documents.c.id == row_map["id"])
            .values(amount=encrypted_amount)
        )


def downgrade() -> None:
    bind = op.get_bind()
    metadata = sa.MetaData()
    users = sa.Table("users", metadata, autoload_with=bind)
    user_documents = sa.Table("user_documents", metadata, autoload_with=bind)
    cipher = _get_cipher()

    users_result = bind.execute(
        sa.select(users.c.id, users.c.inn, users.c.passport, users.c.bank_account)
    ).fetchall()

    for row in users_result:
        row_map = row._mapping
        updates = {}
        for field in ("inn", "passport", "bank_account"):
            decrypted_value = _decrypt_numeric_value(row_map[field], cipher)
            if decrypted_value is not None:
                updates[field] = decrypted_value
        if updates:
            bind.execute(users.update().where(users.c.id == row_map["id"]).values(**updates))

    documents_result = bind.execute(
        sa.select(user_documents.c.id, user_documents.c.amount)
    ).fetchall()

    for row in documents_result:
        row_map = row._mapping
        decrypted_amount = _decrypt_numeric_value(row_map["amount"], cipher)
        if decrypted_amount is None:
            continue

        bind.execute(
            user_documents.update()
            .where(user_documents.c.id == row_map["id"])
            .values(amount=decrypted_amount)
        )

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
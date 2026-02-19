from datetime import timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from modules.models.payment import ContractPayment
from modules.models.user_document import UserDocument
from modules.utils.document_security import decrypt_document_fields, get_sensitive_data_cipher


def rebuild_schedule_for_document(db: Session, document: UserDocument) -> list[ContractPayment]:
    cipher = get_sensitive_data_cipher()
    decrypted = decrypt_document_fields(document, cipher)

    amount = decrypted.get("amount")
    weeks_count = document.weeks_count
    filled_date = document.filled_date

    if amount is None or not weeks_count or not filled_date:
        raise ValueError("В подписанном договоре должны быть amount, weeks_count и filled_date")

    db.query(ContractPayment).filter(ContractPayment.user_id == document.user_id).delete()

    rows: list[ContractPayment] = []
    for idx in range(weeks_count):
        row = ContractPayment(
            user_id=document.user_id,
            document_id=document.id,
            payment_number=idx + 1,
            due_date=filled_date + timedelta(days=7 * idx),
            amount=Decimal(amount),
            status="pending",
        )
        db.add(row)
        rows.append(row)

    db.flush()
    return rows
from datetime import timedelta


from sqlalchemy.orm import Session

from modules.models.payment import ContractPayment
from modules.models.user_document import UserDocument
from modules.utils.document_security import decrypt_document_fields, get_sensitive_data_cipher
from modules.utils.pricing import resolve_weekly_amount


def rebuild_schedule_for_document(db: Session, document: UserDocument) -> list[ContractPayment]:
    cipher = get_sensitive_data_cipher()
    decrypted = decrypt_document_fields(document, cipher)

    bike_serial = decrypted.get("bike_serial")
    weeks_count = document.weeks_count
    filled_date = document.filled_date

    if not weeks_count or not filled_date:
        raise ValueError("В подписанном договоре должны быть weeks_count и filled_date")

    weekly_amount = resolve_weekly_amount(db, bike_serial, weeks_count)

    db.query(ContractPayment).filter(ContractPayment.user_id == document.user_id).delete()

    rows: list[ContractPayment] = []
    for idx in range(weeks_count):
        row = ContractPayment(
            user_id=document.user_id,
            document_id=document.id,
            payment_number=idx + 1,
            due_date=filled_date + timedelta(days=7 * idx),
            amount=weekly_amount,
            description=f"Платеж по договору #{idx + 1}",
            payment_type="rent",
            status="pending",
        )
        db.add(row)
        rows.append(row)

    db.flush()
    return rows
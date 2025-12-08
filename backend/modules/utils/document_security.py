from __future__ import annotations

from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, TYPE_CHECKING

from cryptography.fernet import Fernet, InvalidToken
from docx import Document as DocxDocument
from docx.text.paragraph import Paragraph

from modules.utils.config import settings

if TYPE_CHECKING:
    from modules.models.user import User
    from modules.models.user_document import UserDocument


_SENSITIVE_DOCUMENT_FIELDS = {
    "full_name",
    "address",
    "passport",
    "phone",
    "bank_account",
    "contract_number",
    "bike_serial",
    "akb1_serial",
    "akb2_serial",
    "akb3_serial",
    "amount",
    "amount_text",
    "filled_date",
    "end_date",
}

_SECURE_TEMPLATE_SUBDIR = "templates"
_SECURE_CONTRACTS_SUBDIR = "generated_contracts"
_ENCRYPTED_PREFIX = "enc:"
_CONTRACT_CITY = "Великий Новгород"


def _ensure_secure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    try:
        path.chmod(0o700)
    except PermissionError:
        # Best-effort hardening for environments where chmod is allowed.
        pass
    return path


def get_contract_template_path() -> Path:
    template_dir = _ensure_secure_dir(
        settings.SECURE_STORAGE_DIR / _SECURE_TEMPLATE_SUBDIR
    )
    return template_dir / settings.CONTRACT_TEMPLATE_FILENAME


def get_generated_contracts_dir() -> Path:
    return _ensure_secure_dir(settings.SECURE_STORAGE_DIR / _SECURE_CONTRACTS_SUBDIR)


def get_generated_contract_path(user_id: int) -> Path:
    return get_generated_contracts_dir() / f"contract_user_{user_id}.docx"


class SensitiveDataCipher:
    def __init__(self, key: str):
        try:
            self._fernet = Fernet(key.encode())
        except (TypeError, ValueError) as exc:
            raise ValueError("Invalid ENCRYPTION_KEY provided") from exc

    def encrypt(self, value: str | None) -> str | None:
        if value is None:
            return None
        if value.startswith(_ENCRYPTED_PREFIX):
            return value

        token = self._fernet.encrypt(value.encode())
        return f"{_ENCRYPTED_PREFIX}{token.decode()}"

    def decrypt(self, value: str | None) -> str | None:
        if value is None:
            return None
        if not value.startswith(_ENCRYPTED_PREFIX):
            return value

        token = value[len(_ENCRYPTED_PREFIX) :]
        try:
            return self._fernet.decrypt(token.encode()).decode()
        except InvalidToken:
            # If the token cannot be decrypted, return it unchanged to avoid data loss.
            return value


@lru_cache
def get_sensitive_data_cipher() -> SensitiveDataCipher:
    return SensitiveDataCipher(settings.ENCRYPTION_KEY)


def encrypt_document_fields(
    data: Mapping[str, Any], cipher: SensitiveDataCipher
) -> dict[str, str | None]:
    encrypted: dict[str, str | None] = {}
    for field in _SENSITIVE_DOCUMENT_FIELDS:
        value = data.get(field)
        encrypted[field] = cipher.encrypt(value if value is None else str(value))
    return encrypted


def decrypt_document_fields(
    doc: "UserDocument", cipher: SensitiveDataCipher
) -> dict[str, str | None]:
    decrypted: dict[str, str | None] = {}
    for field in _SENSITIVE_DOCUMENT_FIELDS:
        decrypted[field] = cipher.decrypt(getattr(doc, field))
    return decrypted


def serialize_document_for_response(
    doc: "UserDocument", cipher: SensitiveDataCipher
) -> dict[str, Any]:
    decrypted = decrypt_document_fields(doc, cipher)
    return {
        "id": doc.id,
        "full_name": decrypted.get("full_name") or "",
        "address": decrypted.get("address") or "",
        "passport": decrypted.get("passport") or "",
        "phone": decrypted.get("phone") or "",
        "bank_account": decrypted.get("bank_account"),
        "contract_number": decrypted.get("contract_number"),
        "bike_serial": decrypted.get("bike_serial"),
        "akb1_serial": decrypted.get("akb1_serial"),
        "akb2_serial": decrypted.get("akb2_serial"),
        "akb3_serial": decrypted.get("akb3_serial"),
        "amount": decrypted.get("amount"),
        "amount_text": decrypted.get("amount_text"),
        "weeks_count": doc.weeks_count,
        "filled_date": decrypted.get("filled_date"),
        "end_date": decrypted.get("end_date"),
        "status": doc.status.value if hasattr(doc.status, "value") else str(doc.status),
        "rejection_reason": doc.rejection_reason,
        "contract_text": doc.contract_text,
    }


def _replace_in_paragraph(paragraph: Paragraph, values: dict[str, Any]) -> None:
    if not paragraph.runs:
        return

    full_text = "".join(run.text for run in paragraph.runs)
    new_text = full_text

    for key, val in values.items():
        placeholder = f"{{{key}}}"
        if placeholder in new_text:
            new_text = new_text.replace(placeholder, str(val))

    if new_text == full_text:
        return

    paragraph.runs[0].text = new_text
    for run in paragraph.runs[1:]:
        run.text = ""


def _replace_placeholders_in_docx(doc: DocxDocument, values: dict[str, Any]) -> None:
    for paragraph in doc.paragraphs:
        _replace_in_paragraph(paragraph, values)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    _replace_in_paragraph(paragraph, values)

    for section in doc.sections:
        header = section.header
        for paragraph in header.paragraphs:
            _replace_in_paragraph(paragraph, values)

        footer = section.footer
        for paragraph in footer.paragraphs:
            _replace_in_paragraph(paragraph, values)


def _week_word(n: int | None) -> str:
    if n is None:
        return ""
    n_abs = abs(n)
    last_two = n_abs % 100
    last = n_abs % 10
    if 11 <= last_two <= 14:
        return "недель"
    if last == 1:
        return "неделю"
    if 2 <= last <= 4:
        return "недели"
    return "недель"


def render_contract_docx(
    user: "User", doc: "UserDocument", decrypted_fields: Mapping[str, Any]
) -> str:
    template_path = get_contract_template_path()
    if not template_path.exists():
        raise FileNotFoundError(
            f"DOCX-шаблон не найден по пути: {template_path}. "
            "Поместите контрактный шаблон в SECURE_STORAGE_DIR/templates "
            "и обновите CONTRACT_TEMPLATE_FILENAME при необходимости."
        )

    document = DocxDocument(template_path)

    today_str = datetime.utcnow().strftime("%d.%m.%Y")
    week_word = _week_word(doc.weeks_count)

    values: dict[str, Any] = {
        "CITY": _CONTRACT_CITY,
        "DATE": today_str,
        "FULL_NAME": decrypted_fields.get("full_name") or "",
        "ФИО": decrypted_fields.get("full_name") or "",
        "ADDRESS": decrypted_fields.get("address") or "",
        "PASSPORT": decrypted_fields.get("passport") or "",
        "PHONE": decrypted_fields.get("phone") or "",
        "EMAIL": user.email or "",
        "BANK_ACCOUNT": decrypted_fields.get("bank_account") or "-",
        "№_договора": decrypted_fields.get("contract_number") or "",
        "Номер_приложения": "1",
        "Серийный_номер_велик": decrypted_fields.get("bike_serial") or "",
        "Серийный_нормер_АКБ_1": decrypted_fields.get("akb1_serial") or "",
        "Серийный_нормер_АКБ_2": decrypted_fields.get("akb2_serial") or "",
        "Серийный_нормер_АКБ_3": decrypted_fields.get("akb3_serial") or "",
        "Сумма": decrypted_fields.get("amount") or "",
        "Сумма_пропись": decrypted_fields.get("amount_text") or "",
        "Кол_во_недель": str(doc.weeks_count) if doc.weeks_count is not None else "",
        "неделю": week_word,
        "Дата_аполнения": decrypted_fields.get("filled_date") or today_str,
        "Дата_заполнения": decrypted_fields.get("filled_date") or today_str,
        "Дат_конец_аренды": decrypted_fields.get("end_date") or "",
    }

    _replace_placeholders_in_docx(document, values)

    out_path = get_generated_contract_path(user.id)
    document.save(out_path)
    return str(out_path)
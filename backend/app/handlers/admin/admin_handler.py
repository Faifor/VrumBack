from decimal import Decimal, InvalidOperation

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from num2words import num2words


from modules.connection_to_db.database import get_session
from modules.models.user import User
from modules.models.user_document import UserDocument
from modules.models.types import DocumentStatusEnum
from modules.schemas.document_schemas import (
    DocumentRejectRequest,
    DocumentStatus,
    UserDocumentAdminUpdate,
    UserDocumentAdminUpdateInput,
    UserDocumentRead,
    UserWithDocumentSummary,
)
from modules.utils.admin_utils import get_current_admin
from modules.utils.document_security import (
    decrypt_document_fields,
    decrypt_user_fields,
    encrypt_document_fields,
    get_sensitive_data_cipher,
    render_contract_docx,
    serialize_document_for_response,
)


_PERSONAL_FIELDS = {
    "full_name",
    "inn",
    "registration_address",
    "residential_address",
    "passport",
    "phone",
    "bank_account",
}

_ADMIN_DOCUMENT_FIELDS = {
    "contract_number",
    "bike_serial",
    "akb1_serial",
    "akb2_serial",
    "akb3_serial",
    "amount",
    "amount_text",
}


class AdminHandler:
    def __init__(
        self,
        db: Session = Depends(get_session),
        admin: User = Depends(get_current_admin),
    ):
        self.db = db
        self.admin = admin
        self.cipher = get_sensitive_data_cipher()

    def list_users(
        self, status_filter: DocumentStatusEnum | None = None
    ) -> list[UserWithDocumentSummary]:
        query = self.db.query(User).filter(User.role == "user")
        if status_filter is not None:
            query = query.filter(User.status == status_filter)
        users = query.all()
        result: list[UserWithDocumentSummary] = []

        for u in users:
            result.append(self._build_user_summary(u))
        return result

    def get_user_summary(self, user_id: int) -> UserWithDocumentSummary:
        user = self._get_user_or_404(user_id)
        return self._build_user_summary(user)

    def get_user_document(self, user_id: int, document_id: int) -> UserDocumentRead:
        user = self._get_user_or_404(user_id)
        self._ensure_user_approved(user)

        doc = self._get_user_document_or_404(user_id, document_id)
        return UserDocumentRead(**serialize_document_for_response(doc, self.cipher))

    def list_user_contracts(self, user_id: int):
        user = self._get_user_or_404(user_id)
        self._ensure_user_approved(user)
        docs = UserDocument.refresh_user_documents_status(self.db, user_id)
        return [
            {
                **serialize_document_for_response(doc, self.cipher, user),
                "contract_docx_url": f"/admin/users/{user_id}/contract-docx/{doc.id}",
            }
            for doc in docs
        ]

    def update_user_document(
        self, user_id: int, body: UserDocumentAdminUpdateInput
    ) -> UserDocumentRead:
        user = self._get_user_or_404(user_id)
        self._ensure_user_approved(user)

        update_payload = body.model_dump(exclude_unset=True)
        update_payload.pop("contract_number", None)
        has_updates = bool(update_payload)

        doc = self._get_latest_user_document(user_id)

        if not doc:
            if not has_updates:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Нет данных для создания договора",
                )
            doc = self._create_document(user_id, user)
        elif not doc.active and has_updates:
            doc = self._create_document(user_id, user)

        if not has_updates:
            return UserDocumentRead(**serialize_document_for_response(doc, self.cipher))

        if "amount" in update_payload:
            generated_amount_text = self._generate_amount_text(
                update_payload.get("amount")
            )
            if generated_amount_text:
                update_payload["amount_text"] = generated_amount_text

        encrypted_data = encrypt_document_fields(
            update_payload,
            self.cipher,
            allowed_fields=_ADMIN_DOCUMENT_FIELDS,
        )

        for field, value in encrypted_data.items():
            setattr(doc, field, value)

        if body.weeks_count is not None or "weeks_count" in body.model_fields_set:
            doc.weeks_count = body.weeks_count

        if body.filled_date is not None or "filled_date" in body.model_fields_set:
            doc.filled_date = body.filled_date

        doc.refresh_dates_and_status(update_active=False)
        self._ensure_contract_number(doc)

        self.db.commit()
        UserDocument.refresh_user_documents_status(self.db, user_id)
        self.db.refresh(doc)
        return UserDocumentRead(**serialize_document_for_response(doc, self.cipher))

    def approve_document(self, user_id: int) -> UserDocumentRead:
        user = self._get_user_or_404(user_id)
        doc = self._get_latest_user_document(user_id)
        self._ensure_personal_data_filled(user)

        user.status = DocumentStatusEnum.APPROVED
        user.rejection_reason = None

        self.db.commit()
        self.db.refresh(user)
        if doc:
            self.db.refresh(doc)
        return UserDocumentRead(
            **serialize_document_for_response(doc, self.cipher, user)
        )

    def reject_document(
        self, user_id: int, body: DocumentRejectRequest
    ) -> UserDocumentRead:
        user = self._get_user_or_404(user_id)
        doc = self._get_latest_user_document(user_id)

        user.status = DocumentStatusEnum.REJECTED
        user.rejection_reason = body.reason
        if doc:
            doc.contract_text = None
            doc.weeks_count = None
            doc.filled_date = None
            doc.end_date = None
            doc.active = False

        for field in _PERSONAL_FIELDS:
            setattr(user, field, None)

        if doc:
            for field in _ADMIN_DOCUMENT_FIELDS:
                setattr(doc, field, None)

        self.db.commit()
        self.db.refresh(user)
        if doc:
            self.db.refresh(doc)
        return UserDocumentRead(**serialize_document_for_response(doc, self.cipher, user))

    def get_contract_docx_path(self, user_id: int, document_id: int) -> str:
        user = self._get_user_or_404(user_id)
        doc = self._get_user_document_or_404(user_id, document_id)

        if user.status != DocumentStatusEnum.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Данные пользователя не одобрены",
            )

        decrypted_fields = {
            **decrypt_user_fields(user, self.cipher),
            **decrypt_document_fields(doc, self.cipher),
        }
        return render_contract_docx(user, doc, decrypted_fields)

    def _get_user_or_404(self, user_id: int) -> User:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден",
            )
        return user

    def _build_user_summary(self, user: User) -> UserWithDocumentSummary:
        personal_data = decrypt_user_fields(user, self.cipher)
        return UserWithDocumentSummary(
            id=user.id,
            email=user.email,
            full_name=personal_data.get("full_name"),
            inn=personal_data.get("inn"),
            registration_address=personal_data.get("registration_address"),
            residential_address=personal_data.get("residential_address"),
            passport=personal_data.get("passport"),
            phone=personal_data.get("phone"),
            bank_account=personal_data.get("bank_account"),
            role=user.role,
            status=DocumentStatus(user.status),
            rejection_reason=user.rejection_reason,
        )

    def _get_user_document_or_404(
        self, user_id: int, document_id: int | None = None
    ) -> UserDocument:
        doc = self._get_latest_user_document(user_id, document_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Документ не найден",
            )
        return doc

    def _get_latest_user_document(
        self, user_id: int, document_id: int | None = None
    ) -> UserDocument | None:
        docs = UserDocument.refresh_user_documents_status(self.db, user_id)
        if document_id is not None:
            return next((doc for doc in docs if doc.id == document_id), None)
        return docs[0] if docs else None

    def _create_document(self, user_id: int, user: User) -> UserDocument:
        new_doc = UserDocument(user_id=user_id)
        new_doc.user = user
        self.db.add(new_doc)
        return new_doc

    def _ensure_contract_number(self, doc: UserDocument) -> None:
        if doc.contract_number:
            return

        if doc.id is None:
            self.db.flush()

        total_user_documents = (
            self.db.query(UserDocument)
            .filter(UserDocument.user_id == doc.user_id)
            .count()
        )

        contract_number = f"{doc.user_id}.{doc.id}.{total_user_documents}"
        doc.contract_number = self.cipher.encrypt(contract_number)

    def _generate_amount_text(self, amount: str | int | float | None) -> str | None:
        if amount is None:
            return None

        normalized = (
            str(amount)
            .strip()
            .replace(" ", "")
            .replace("\u00a0", "")
            .replace(",", "")
        )

        if not normalized:
            return None

        try:
            numeric_value = int(Decimal(normalized))
        except (InvalidOperation, ValueError):
            return None

        return num2words(numeric_value, lang="ru")
    
    def _ensure_user_approved(self, user: User) -> None:
        if user.status != DocumentStatusEnum.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Данные пользователя не одобрены",
            )

    def _ensure_personal_data_filled(self, user: User) -> None:
        personal_data = decrypt_user_fields(user, self.cipher)
        missing_fields = [field for field in _PERSONAL_FIELDS if not personal_data.get(field)]

        if missing_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Недостаточно данных пользователя для подтверждения",
            )
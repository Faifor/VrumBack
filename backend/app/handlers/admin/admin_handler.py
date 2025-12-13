from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session


from modules.connection_to_db.database import get_session
from modules.models.user import User
from modules.models.user_document import UserDocument
from modules.models.types import DocumentStatusEnum
from modules.schemas.document_schemas import (
    DocumentRejectRequest,
    DocumentStatus,
    UserDocumentAdminUpdate,
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
    "filled_date",
    "end_date",
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

    def list_users(self) -> list[UserWithDocumentSummary]:
        users = self.db.query(User).filter(User.role == "user").all()
        result: list[UserWithDocumentSummary] = []

        for u in users:
            personal_data = decrypt_user_fields(u, self.cipher)
            result.append(
                UserWithDocumentSummary(
                    id=u.id,
                    email=u.email,
                    full_name=personal_data.get("full_name"),
                    inn=personal_data.get("inn"),
                    registration_address=personal_data.get("registration_address"),
                    residential_address=personal_data.get("residential_address"),
                    passport=personal_data.get("passport"),
                    phone=personal_data.get("phone"),
                    bank_account=personal_data.get("bank_account"),
                    role=u.role,
                    status=DocumentStatus(u.status),
                    rejection_reason=u.rejection_reason,
                )
            )
        return result

    def get_user_document(self, user_id: int) -> UserDocumentRead:
        user = self._get_user_or_404(user_id)
        self._ensure_user_approved(user)

        doc = self._get_user_document_or_404(user_id)
        return UserDocumentRead(**serialize_document_for_response(doc, self.cipher))

    def update_user_document(
        self, user_id: int, body: UserDocumentAdminUpdate
    ) -> UserDocumentRead:
        user = self._get_user_or_404(user_id)
        self._ensure_user_approved(user)

        doc = self._get_user_document_or_404(user_id)

        encrypted_data = encrypt_document_fields(
            body.model_dump(exclude_unset=True),
            self.cipher,
            allowed_fields=_ADMIN_DOCUMENT_FIELDS,
        )

        for field, value in encrypted_data.items():
            setattr(doc, field, value)

        if body.weeks_count is not None or "weeks_count" in body.model_fields_set:
            doc.weeks_count = body.weeks_count

        self.db.commit()
        self.db.refresh(doc)
        return UserDocumentRead(**serialize_document_for_response(doc, self.cipher))

    def approve_document(self, user_id: int) -> UserDocumentRead:
        user = self._get_user_or_404(user_id)
        doc = self._get_user_document_or_404(user_id)
        self._ensure_personal_data_filled(user)

        user.status = DocumentStatusEnum.APPROVED
        user.rejection_reason = None

        self.db.commit()
        self.db.refresh(doc)
        self.db.refresh(user)
        return UserDocumentRead(**serialize_document_for_response(doc, self.cipher))

    def reject_document(
        self, user_id: int, body: DocumentRejectRequest
    ) -> UserDocumentRead:
        user = self._get_user_or_404(user_id)
        doc = self._get_user_document_or_404(user_id)

        user.status = DocumentStatusEnum.REJECTED
        user.rejection_reason = body.reason
        doc.contract_text = None
        doc.weeks_count = None

        for field in _PERSONAL_FIELDS:
            setattr(user, field, None)

        for field in _ADMIN_DOCUMENT_FIELDS:
            setattr(doc, field, None)

        self.db.commit()
        self.db.refresh(doc)
        self.db.refresh(user)
        return UserDocumentRead(**serialize_document_for_response(doc, self.cipher))

    def get_contract_docx_path(self, user_id: int) -> str:
        user = self._get_user_or_404(user_id)
        doc = self._get_user_document_or_404(user_id)

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

    def _get_user_document_or_404(self, user_id: int) -> UserDocument:
        doc = (
            self.db.query(UserDocument).filter(UserDocument.user_id == user_id).first()
        )
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Документ не найден",
            )
        return doc

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
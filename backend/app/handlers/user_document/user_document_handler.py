from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from modules.connection_to_db.database import get_session
from modules.models.user import User
from modules.models.user_document import UserDocument
from modules.models.types import DocumentStatusEnum
from modules.schemas.document_schemas import UserDocumentUserUpdate
from modules.utils.document_security import (
    decrypt_document_fields,
    decrypt_user_fields,
    encrypt_document_fields,
    get_sensitive_data_cipher,
    render_contract_docx,
    serialize_document_for_response,
)
from modules.utils.jwt_utils import get_current_user


_PERSONAL_FIELDS = {
    "full_name",
    "inn",
    "registration_address",
    "residential_address",
    "passport",
    "phone",
    "bank_account",
}


class UserDocumentHandler:
    def __init__(
        self,
        db: Session = Depends(get_session),
        current_user: User = Depends(get_current_user),
    ):
        self.db = db
        self.user = current_user
        self.cipher = get_sensitive_data_cipher()

    def _get_my_document(self) -> UserDocument | None:
        return (
            self.db.query(UserDocument)
            .filter(UserDocument.user_id == self.user.id)
            .first()
        )

    def get_my_document(self):
        doc = self._get_my_document()
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Документ не найден",
            )
        return serialize_document_for_response(doc, self.cipher)

    def upsert_my_document(self, data: UserDocumentUserUpdate):
        doc = self._get_my_document()
        encrypted_data = encrypt_document_fields(
            data.model_dump(exclude_unset=True),
            self.cipher,
            allowed_fields=_PERSONAL_FIELDS,
        )

        if not doc:
            doc = UserDocument(
                user_id=self.user.id,
                status=DocumentStatusEnum.DRAFT,
            )
            self.db.add(doc)
        for field, value in encrypted_data.items():
            setattr(self.user, field, value)

        doc.user = self.user

        doc.status = DocumentStatusEnum.DRAFT
        doc.rejection_reason = None
        doc.contract_text = None

        self.db.commit()
        self.db.refresh(doc)
        self.db.refresh(self.user)
        return serialize_document_for_response(doc, self.cipher)

    def submit_my_document(self):
        doc = self._get_my_document()
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Сначала заполните документ",
            )

        doc.status = DocumentStatusEnum.PENDING
        doc.rejection_reason = None

        self.db.commit()
        self.db.refresh(doc)
        return serialize_document_for_response(doc, self.cipher)

    def get_my_contract_docx_path(self) -> str:
        doc = self._get_my_document()
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Документ не найден",
            )

        if doc.status != DocumentStatusEnum.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Договор еще не одобрен",
            )

        decrypted_fields = {
            **decrypt_user_fields(self.user, self.cipher),
            **decrypt_document_fields(doc, self.cipher),
        }
        return render_contract_docx(self.user, doc, decrypted_fields)
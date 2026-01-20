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

    def _get_my_document(self, document_id: int | None = None) -> UserDocument | None:
        query = self.db.query(UserDocument).filter(
            UserDocument.user_id == self.user.id
        )

        if document_id is not None:
            query = query.filter(UserDocument.id == document_id)
        else:
            query = query.order_by(
                UserDocument.created_at.desc(), UserDocument.id.desc()
            )

        doc = query.first()
        if doc and doc.refresh_dates_and_status():
            self.db.commit()
            self.db.refresh(doc)
        return doc

    def get_my_document(self, document_id: int):
        doc = self._get_my_document(document_id)
        return serialize_document_for_response(doc, self.cipher, self.user)

    def upsert_my_document(self, data: UserDocumentUserUpdate):
        doc = self._get_my_document()
        if self.user.status == DocumentStatusEnum.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Данные отправлены на проверку и не могут быть изменены",
            )
        if self.user.status == DocumentStatusEnum.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Данные одобрены и не могут быть изменены",
            )
        encrypted_data = encrypt_document_fields(
            data.model_dump(exclude_unset=True),
            self.cipher,
            allowed_fields=_PERSONAL_FIELDS,
        )
        encrypted_data = encrypt_document_fields(
            data.model_dump(exclude_unset=True),
            self.cipher,
            allowed_fields=_PERSONAL_FIELDS,
        )

        for field, value in encrypted_data.items():
            setattr(self.user, field, value)

        self.user.status = DocumentStatusEnum.DRAFT
        self.user.rejection_reason = None

        self.db.commit()
        self.db.refresh(self.user)
        return serialize_document_for_response(doc, self.cipher, self.user)

    def submit_my_document(self):
        doc = self._get_my_document()
        if self.user.status == DocumentStatusEnum.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Данные уже отправлены на проверку",
            )
        if self.user.status == DocumentStatusEnum.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Данные уже одобрены",
            )

        personal_data = decrypt_user_fields(self.user, self.cipher)
        missing_fields = [field for field in _PERSONAL_FIELDS if not personal_data.get(field)]
        if missing_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Заполните все персональные данные перед отправкой",
            )


        self.user.status = DocumentStatusEnum.PENDING
        self.user.rejection_reason = None

        self.db.commit()
        self.db.refresh(self.user)
        return serialize_document_for_response(doc, self.cipher, self.user)

    def get_my_contract_docx_path(self, document_id: int) -> str:
        doc = self._get_my_document(document_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Документ не найден",
            )

        if self.user.status != DocumentStatusEnum.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Договор еще не одобрен",
            )

        decrypted_fields = {
            **decrypt_user_fields(self.user, self.cipher),
            **decrypt_document_fields(doc, self.cipher),
        }
        return render_contract_docx(self.user, doc, decrypted_fields)
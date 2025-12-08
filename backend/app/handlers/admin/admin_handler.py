from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session


from modules.connection_to_db.database import get_session
from modules.models.user import User
from modules.models.user_document import UserDocument
from modules.models.types import DocumentStatusEnum
from modules.schemas.document_schemas import (

    DocumentRejectRequest,
    DocumentStatus,
    UserDocumentRead,
    UserWithDocumentSummary,
)
from modules.utils.admin_utils import get_current_admin
from modules.utils.document_security import (
    decrypt_document_fields,
    get_sensitive_data_cipher,
    render_contract_docx,
    serialize_document_for_response,
)


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
            doc = (
                self.db.query(UserDocument).filter(UserDocument.user_id == u.id).first()
            )
            result.append(
                UserWithDocumentSummary(
                    id=u.id,
                    email=u.email,
                    first_name=u.first_name,
                    last_name=u.last_name,
                    role=u.role,
                    document_status=DocumentStatus(doc.status) if doc else None,
                )
            )
        return result

    def get_user_document(self, user_id: int) -> UserDocumentRead:
        doc = (
            self.db.query(UserDocument).filter(UserDocument.user_id == user_id).first()
        )
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Документ не найден",
            )
        return UserDocumentRead(**serialize_document_for_response(doc, self.cipher))

    def approve_document(self, user_id: int) -> UserDocumentRead:
        doc = (
            self.db.query(UserDocument).filter(UserDocument.user_id == user_id).first()
        )
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Документ не найден",
            )

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден",
            )

        doc.status = DocumentStatusEnum.APPROVED
        doc.rejection_reason = None
        doc.contract_text = "Договор успешно сформирован"

        self.db.commit()
        self.db.refresh(doc)
        return UserDocumentRead(**serialize_document_for_response(doc, self.cipher))

    def reject_document(
        self, user_id: int, body: DocumentRejectRequest
    ) -> UserDocumentRead:
        doc = (
            self.db.query(UserDocument).filter(UserDocument.user_id == user_id).first()
        )
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Документ не найден",
            )

        doc.status = DocumentStatusEnum.REJECTED
        doc.rejection_reason = body.reason
        doc.contract_text = None

        self.db.commit()
        self.db.refresh(doc)
        return UserDocumentRead(**serialize_document_for_response(doc, self.cipher))

    def get_contract_docx_path(self, user_id: int) -> str:
        doc = (
            self.db.query(UserDocument).filter(UserDocument.user_id == user_id).first()
        )
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

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден",
            )

        decrypted_fields = decrypt_document_fields(doc, self.cipher)
        return render_contract_docx(user, doc, decrypted_fields)
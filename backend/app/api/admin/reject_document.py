from fastapi import APIRouter, Depends

from app.handlers.admin.admin_handler import AdminHandler
from modules.schemas.document_schemas import (
    UserDocumentRead,
    DocumentRejectRequest,
)

router = APIRouter()


@router.post("/admin/users/{user_id}/document/reject", response_model=UserDocumentRead)
def admin_reject_document(
    user_id: int,
    body: DocumentRejectRequest,
    handler: AdminHandler = Depends(AdminHandler),
):
    return handler.reject_document(user_id, body)

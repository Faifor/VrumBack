from fastapi import APIRouter, Depends

from app.handlers.admin.admin_handler import AdminHandler
from modules.schemas.document_schemas import UserDocumentRead

router = APIRouter()


@router.post("/admin/users/{user_id}/documents/{document_id}/sign", response_model=UserDocumentRead)
def admin_sign_user_document(
    user_id: int,
    document_id: int,
    handler: AdminHandler = Depends(AdminHandler),
):
    return handler.sign_user_document(user_id, document_id)
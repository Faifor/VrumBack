from fastapi import APIRouter, Depends, Query

from app.handlers.admin.admin_handler import AdminHandler
from modules.schemas.document_schemas import (
    UserDocumentAdminUpdateInput,
    UserDocumentRead,
)

router = APIRouter()


@router.put("/admin/users/{user_id}/document", response_model=UserDocumentRead)
def admin_update_user_document(
    user_id: int,
    body: UserDocumentAdminUpdateInput,
    document_id: int = Query(..., description="ID договора для обновления"),
    handler: AdminHandler = Depends(AdminHandler),
):
    return handler.update_user_document(user_id, document_id, body)
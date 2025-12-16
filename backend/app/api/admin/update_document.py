from fastapi import APIRouter, Depends

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
    handler: AdminHandler = Depends(AdminHandler),
):
    return handler.update_user_document(user_id, body)
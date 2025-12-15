from fastapi import APIRouter, Depends

from app.handlers.admin.admin_handler import AdminHandler
from modules.schemas.document_schemas import UserDocumentRead

router = APIRouter()


@router.get(
    "/admin/users/{user_id}/document/{document_id}", response_model=UserDocumentRead
)
def admin_get_user_document(
    user_id: int,
    document_id: int,
    handler: AdminHandler = Depends(AdminHandler),
):
    return handler.get_user_document(user_id, document_id)

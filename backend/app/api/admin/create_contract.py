from fastapi import APIRouter, Depends

from app.handlers.admin.admin_handler import AdminHandler
from modules.schemas.document_schemas import UserDocumentAdminUpdateInput, UserDocumentRead

router = APIRouter()


@router.post("/admin/users/{user_id}/contracts", response_model=UserDocumentRead)
def admin_create_user_contract(
    user_id: int,
    body: UserDocumentAdminUpdateInput,
    handler: AdminHandler = Depends(AdminHandler),
):
    return handler.create_user_contract(user_id, body)
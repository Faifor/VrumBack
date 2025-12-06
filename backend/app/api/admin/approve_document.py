from fastapi import APIRouter, Depends

from app.handlers.admin.admin_handler import AdminHandler
from modules.schemas.document_schemas import UserDocumentRead

router = APIRouter()


@router.post("/admin/users/{user_id}/document/approve", response_model=UserDocumentRead)
def admin_approve_document(
    user_id: int,
    handler: AdminHandler = Depends(AdminHandler),
):
    return handler.approve_document(user_id)

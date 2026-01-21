from fastapi import APIRouter, Depends

from app.handlers.admin.admin_handler import AdminHandler
from modules.schemas.document_schemas import UserWithDocumentSummary

router = APIRouter()


@router.get("/admin/users/{user_id}", response_model=UserWithDocumentSummary)
def admin_get_user_summary(
    user_id: int,
    handler: AdminHandler = Depends(AdminHandler),
):
    return handler.get_user_summary(user_id)
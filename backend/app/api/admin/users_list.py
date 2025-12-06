from fastapi import APIRouter, Depends

from app.handlers.admin.admin_handler import AdminHandler
from modules.schemas.document_schemas import UserWithDocumentSummary

router = APIRouter()


@router.get("/admin/users", response_model=list[UserWithDocumentSummary])
def admin_list_users(
    handler: AdminHandler = Depends(AdminHandler),
):
    return handler.list_users()

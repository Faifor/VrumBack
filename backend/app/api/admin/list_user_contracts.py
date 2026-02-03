from fastapi import APIRouter, Depends

from app.handlers.admin.admin_handler import AdminHandler
from modules.schemas.document_schemas import UserContractItem

router = APIRouter()


@router.get("/admin/users/{user_id}/documents", response_model=list[UserContractItem])
def admin_list_user_contracts(
    user_id: int, handler: AdminHandler = Depends(AdminHandler)
):
    return handler.list_user_contracts(user_id)
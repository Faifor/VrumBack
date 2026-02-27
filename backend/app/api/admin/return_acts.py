from fastapi import APIRouter, Depends

from app.handlers.admin.admin_handler import AdminHandler
from modules.schemas.return_act_schemas import ReturnActCreateRequest, ReturnActRead

router = APIRouter()


@router.post(
    "/admin/users/{user_id}/contracts/{document_id}/return-acts",
    response_model=ReturnActRead,
)
def admin_create_return_act(
    user_id: int,
    document_id: int,
    body: ReturnActCreateRequest,
    handler: AdminHandler = Depends(AdminHandler),
):
    return handler.create_return_act(user_id, document_id, body)


@router.get("/admin/users/{user_id}/return-acts", response_model=list[ReturnActRead])
def admin_list_return_acts(
    user_id: int,
    handler: AdminHandler = Depends(AdminHandler),
):
    return handler.list_user_return_acts(user_id)


@router.get("/admin/users/{user_id}/return-acts/{act_id}", response_model=ReturnActRead)
def admin_get_return_act(
    user_id: int,
    act_id: int,
    handler: AdminHandler = Depends(AdminHandler),
):
    return handler.get_user_return_act(user_id, act_id)
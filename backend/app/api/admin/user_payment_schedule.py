from fastapi import APIRouter, Depends

from app.handlers.admin.admin_handler import AdminHandler
from modules.schemas.payment_schemas import ContractPaymentRead

router = APIRouter()


@router.get("/admin/users/{user_id}/payment-schedule", response_model=list[ContractPaymentRead])
def admin_user_payment_schedule(
    user_id: int,
    handler: AdminHandler = Depends(AdminHandler),
):
    return handler.get_user_payment_schedule(user_id)
from fastapi import APIRouter, Depends, Header, Request

from app.handlers.payment_handler import PaymentHandler
from modules.models.user import User
from modules.schemas.payment_schemas import (
    AutopayChargeRequest,
    AutopayEnableRequest,
    CreatePaymentRequest,
    CreatePaymentResponse,
    ContractPaymentRead,
    OrderRead,
    RecalcRequest,
    WebhookResponse,
)
from modules.utils.jwt_utils import get_current_user

router = APIRouter()

@router.get("/payments/schedule", response_model=list[ContractPaymentRead])
async def my_schedule(
    current_user: User = Depends(get_current_user),
    handler: PaymentHandler = Depends(),
):
    return await handler.list_my_schedule(current_user)


@router.get("/payments/schedule/{schedule_payment_id}", response_model=ContractPaymentRead)
async def my_schedule_item(
    schedule_payment_id: int,
    current_user: User = Depends(get_current_user),
    handler: PaymentHandler = Depends(),
):
    return await handler.get_my_schedule_item(schedule_payment_id, current_user)

@router.post("/payments/create", response_model=CreatePaymentResponse)
async def create_payment(
    data: CreatePaymentRequest,
    current_user: User = Depends(get_current_user),
    handler: PaymentHandler = Depends(),
):
    return await handler.create_payment(data, current_user)

@router.get("/yookassa/webhook", response_model=WebhookResponse)
@router.get("/yookassa/webhook/", response_model=WebhookResponse, include_in_schema=False)
async def yookassa_webhook_health():
    return {"detail": "ok"}

@router.post("/yookassa/webhook", response_model=WebhookResponse)
@router.post("/yookassa/webhook/", response_model=WebhookResponse, include_in_schema=False)
async def yookassa_webhook(
    request: Request,
    authorization: str | None = Header(default=None),
    handler: PaymentHandler = Depends(),
):
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    if not isinstance(payload, dict):
        payload = {}

    return await handler.webhook(payload, authorization)


@router.post("/autopay/enable")
async def enable_autopay(
    data: AutopayEnableRequest,
    current_user: User = Depends(get_current_user),
    handler: PaymentHandler = Depends(),
):
    return await handler.enable_autopay(data, current_user)


@router.post("/autopay/disable")
async def disable_autopay(
    current_user: User = Depends(get_current_user),
    handler: PaymentHandler = Depends(),
):
    return await handler.disable_autopay(current_user)


@router.post("/autopay/charge", response_model=CreatePaymentResponse)
async def charge_autopay(
    data: AutopayChargeRequest,
    current_user: User = Depends(get_current_user),
    handler: PaymentHandler = Depends(),
):
    return await handler.charge_autopay(data, current_user)


@router.post("/recalc/{order_id}")
async def recalc_order(
    order_id: int,
    data: RecalcRequest,
    current_user: User = Depends(get_current_user),
    handler: PaymentHandler = Depends(),
):
    return await handler.recalc(order_id, data, current_user)


@router.get("/orders/{order_id}", response_model=OrderRead)
async def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    handler: PaymentHandler = Depends(),
):
    return await handler.get_order(order_id, current_user)
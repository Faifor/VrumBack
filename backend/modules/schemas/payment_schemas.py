from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CreatePaymentRequest(BaseModel):
    order_id: int | None = Field(default=None)
    schedule_payment_id: int | None = Field(default=None)
    amount: Decimal | None = Field(default=None, gt=0)
    currency: str = Field(default="RUB", min_length=3, max_length=3)
    description: str | None = Field(default=None)
    save_payment_method: bool = Field(default=False)
    return_url: str | None = Field(default=None)


class CreatePaymentResponse(BaseModel):
    order_id: int
    payment_id: int
    yookassa_payment_id: str | None
    status: str
    confirmation_url: str | None


class WebhookResponse(BaseModel):
    detail: str


class AutopayEnableRequest(BaseModel):
    payment_method_id: str | None = Field(default=None)


class AutopayChargeRequest(BaseModel):
    order_id: int | None = Field(default=None)
    schedule_payment_id: int | None = Field(default=None)
    amount: Decimal | None = Field(default=None, gt=0)
    currency: str = Field(default="RUB", min_length=3, max_length=3)
    description: str | None = Field(default="Автоплатёж")


class RecalcRequest(BaseModel):
    target_amount: Decimal = Field(..., gt=0)
    description: str | None = Field(default=None)


class PaymentRead(BaseModel):
    id: int
    yookassa_payment_id: str | None
    status: str
    amount: Decimal
    currency: str
    confirmation_url: str | None
    payment_method_id: str | None
    save_payment_method: bool
    is_autopay: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class OrderRead(BaseModel):
    id: int
    user_id: int
    amount: Decimal
    currency: str
    status: str
    description: str | None
    created_at: datetime
    updated_at: datetime
    payments: list[PaymentRead]

    model_config = {"from_attributes": True}


class ContractPaymentRead(BaseModel):
    id: int
    document_id: int
    payment_number: int
    due_date: date
    amount: Decimal
    status: str
    order_id: int | None
    payment_id: int | None
    paid_at: datetime | None

    model_config = {"from_attributes": True}
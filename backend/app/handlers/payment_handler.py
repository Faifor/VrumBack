import json
from decimal import Decimal

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from modules.connection_to_db.database import get_session
from modules.models.payment import Order, Payment
from modules.models.user import User
from modules.schemas.payment_schemas import (
    AutopayChargeRequest,
    AutopayEnableRequest,
    CreatePaymentRequest,
    CreatePaymentResponse,
    OrderRead,
    RecalcRequest,
)
from modules.utils.config import settings
from modules.utils.yookassa_client import YooKassaClient


class PaymentHandler:
    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    async def create_payment(self, data: CreatePaymentRequest, current_user: User) -> CreatePaymentResponse:
        order = self._get_or_create_order(current_user, data.order_id, data.amount, data.currency, data.description)
        receipt = self._build_receipt(
            user=current_user,
            amount=data.amount,
            currency=data.currency,
            description=data.description or f"Order #{order.id}",
        )

        payload = {
            "amount": {"value": f"{data.amount:.2f}", "currency": data.currency.upper()},
            "capture": True,
            "confirmation": {
                "type": "redirect",
                "return_url": data.return_url or settings.YOOKASSA_RETURN_URL or "https://example.com/return",
            },
            "description": data.description or f"Order #{order.id}",
            "save_payment_method": data.save_payment_method,
            "metadata": {"order_id": str(order.id), "user_id": str(current_user.id)},
            "receipt": receipt,
        }

        result = YooKassaClient().create_payment(payload)
        payment = self._store_payment(order, current_user, data.amount, data.currency, result, data.save_payment_method, is_autopay=False)

        self._sync_order_status(order, payment.status)
        self.session.commit()
        self.session.refresh(payment)

        return CreatePaymentResponse(
            order_id=order.id,
            payment_id=payment.id,
            yookassa_payment_id=payment.yookassa_payment_id,
            status=payment.status,
            confirmation_url=payment.confirmation_url,
        )

    async def webhook(self, payload: dict, authorization: str | None) -> dict:
        if settings.YOOKASSA_WEBHOOK_SECRET and authorization != f"Bearer {settings.YOOKASSA_WEBHOOK_SECRET}":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook token")

        payment_object = payload.get("object", {})
        yookassa_payment_id = payment_object.get("id")
        if not yookassa_payment_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing payment id")

        payment = self.session.query(Payment).filter(Payment.yookassa_payment_id == yookassa_payment_id).first()
        if not payment:
            return {"detail": "Payment not found, ignored"}

        payment.status = payment_object.get("status", payment.status)
        payment.raw_payload = json.dumps(payload, ensure_ascii=False)

        payment_method = payment_object.get("payment_method", {})
        if payment_method.get("id"):
            payment.payment_method_id = payment_method["id"]

        order = self.session.query(Order).filter(Order.id == payment.order_id).first()
        if order:
            self._sync_order_status(order, payment.status)

        self.session.commit()
        return {"detail": "ok"}

    async def enable_autopay(self, data: AutopayEnableRequest, current_user: User) -> dict:
        payment_method_id = data.payment_method_id or current_user.autopay_payment_method_id
        if not payment_method_id:
            latest_payment = (
                self.session.query(Payment)
                .filter(
                    Payment.user_id == current_user.id,
                    Payment.status == "succeeded",
                    Payment.payment_method_id.isnot(None),
                )
                .order_by(Payment.created_at.desc())
                .first()
            )
            payment_method_id = latest_payment.payment_method_id if latest_payment else None

        if not payment_method_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No saved payment method found. Complete payment with save_payment_method=true first.",
            )

        current_user.autopay_enabled = True
        current_user.autopay_payment_method_id = payment_method_id
        self.session.commit()
        return {"detail": "autopay enabled", "payment_method_id": payment_method_id}

    async def disable_autopay(self, current_user: User) -> dict:
        current_user.autopay_enabled = False
        self.session.commit()
        return {"detail": "autopay disabled"}

    async def charge_autopay(self, data: AutopayChargeRequest, current_user: User) -> CreatePaymentResponse:
        if not current_user.autopay_enabled or not current_user.autopay_payment_method_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Autopay is not enabled")

        order = self._get_or_create_order(current_user, data.order_id, data.amount, data.currency, data.description)
        receipt = self._build_receipt(
            user=current_user,
            amount=data.amount,
            currency=data.currency,
            description=data.description or f"Autopay order #{order.id}",
        )
        payload = {
            "amount": {"value": f"{data.amount:.2f}", "currency": data.currency.upper()},
            "capture": True,
            "payment_method_id": current_user.autopay_payment_method_id,
            "description": data.description or f"Autopay order #{order.id}",
            "metadata": {"order_id": str(order.id), "user_id": str(current_user.id), "autopay": "1"},
            "receipt": receipt,
        }

        result = YooKassaClient().create_payment(payload)
        payment = self._store_payment(order, current_user, data.amount, data.currency, result, True, is_autopay=True)

        self._sync_order_status(order, payment.status)
        self.session.commit()
        self.session.refresh(payment)

        return CreatePaymentResponse(
            order_id=order.id,
            payment_id=payment.id,
            yookassa_payment_id=payment.yookassa_payment_id,
            status=payment.status,
            confirmation_url=payment.confirmation_url,
        )

    async def recalc(self, order_id: int, data: RecalcRequest, current_user: User) -> dict:
        order = self._get_order_for_user(order_id, current_user.id)

        successful_total = (
            self.session.query(Payment)
            .filter(Payment.order_id == order.id, Payment.status == "succeeded")
            .with_entities(Payment.amount)
            .all()
        )
        paid = sum((item[0] for item in successful_total), Decimal("0"))

        target = data.target_amount
        if paid == target:
            order.amount = target
            order.status = "succeeded"
            self.session.commit()
            return {"detail": "No recalculation needed", "order_status": order.status}

        if paid > target:
            delta = paid - target
            order.amount = target
            order.status = "refund_required"
            self.session.commit()
            return {"detail": "Refund required", "refund_amount": f"{delta:.2f}", "order_status": order.status}

        delta = target - paid
        order.amount = target
        order.status = "requires_payment"
        self.session.commit()
        return {
            "detail": "Additional payment required",
            "additional_amount": f"{delta:.2f}",
            "order_status": order.status,
        }

    async def get_order(self, order_id: int, current_user: User) -> OrderRead:
        order = self._get_order_for_user(order_id, current_user.id)
        return OrderRead.model_validate(order)

    def _get_order_for_user(self, order_id: int, user_id: int) -> Order:
        order = self.session.query(Order).filter(Order.id == order_id, Order.user_id == user_id).first()
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        return order

    def _get_or_create_order(self, user: User, order_id: int | None, amount: Decimal, currency: str, description: str | None) -> Order:
        if order_id is not None:
            order = self.session.query(Order).filter(Order.id == order_id, Order.user_id == user.id).first()
            if order:
                order.amount = amount
                order.currency = currency.upper()
                if description is not None:
                    order.description = description
                return order

        order = Order(
            user_id=user.id,
            amount=amount,
            currency=currency.upper(),
            description=description,
            status="pending",
        )
        self.session.add(order)
        self.session.flush()
        return order

    def _store_payment(
        self,
        order: Order,
        user: User,
        amount: Decimal,
        currency: str,
        result: dict,
        save_payment_method: bool,
        is_autopay: bool,
    ) -> Payment:
        payment_method = result.get("payment_method", {})
        payment = Payment(
            order_id=order.id,
            user_id=user.id,
            yookassa_payment_id=result.get("id"),
            status=result.get("status", "pending"),
            amount=amount,
            currency=currency.upper(),
            confirmation_url=result.get("confirmation", {}).get("confirmation_url"),
            payment_method_id=payment_method.get("id"),
            save_payment_method=save_payment_method,
            is_autopay=is_autopay,
            raw_payload=json.dumps(result, ensure_ascii=False),
        )
        self.session.add(payment)

        if save_payment_method and payment.payment_method_id:
            user.autopay_payment_method_id = payment.payment_method_id

        return payment

    def _sync_order_status(self, order: Order, payment_status: str) -> None:
        mapping = {
            "pending": "pending",
            "waiting_for_capture": "pending",
            "succeeded": "succeeded",
            "canceled": "canceled",
        }
        order.status = mapping.get(payment_status, payment_status)

    def _build_receipt(self, user: User, amount: Decimal, currency: str, description: str) -> dict:
        customer: dict[str, str] = {}
        if user.email:
            customer["email"] = user.email
        if user.phone:
            customer["phone"] = user.phone

        if not customer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="YooKassa receipt requires user email or phone",
            )

        return {
            "customer": customer,
            "items": [
                {
                    "description": description[:128],
                    "quantity": "1.00",
                    "amount": {"value": f"{amount:.2f}", "currency": currency.upper()},
                    "vat_code": 1,
                    "payment_mode": "full_payment",
                    "payment_subject": "service",
                }
            ],
        }
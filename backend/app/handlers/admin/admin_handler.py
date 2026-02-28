from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from fastapi import Depends, HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from num2words import num2words


from modules.connection_to_db.database import get_session
from modules.models.inventory import Battery, Bike
from modules.models.payment import ContractPayment
from modules.models.return_act import ReturnAct
from modules.models.user import User
from modules.models.user_document import UserDocument
from modules.models.types import DocumentStatusEnum
from modules.schemas.document_schemas import (
    DocumentRejectRequest,
    DocumentStatus,
    UserDocumentAdminUpdate,
    UserDocumentAdminUpdateInput,
    UserDocumentRead,
    UserWithDocumentSummary,
)
from modules.schemas.return_act_schemas import ReturnActCreateRequest, ReturnActRead
from modules.utils.admin_utils import get_current_admin
from modules.utils.document_security import (
    decrypt_document_fields,
    decrypt_user_fields,
    encrypt_document_fields,
    get_sensitive_data_cipher,
    render_contract_docx,
    render_return_act_docx,
    serialize_document_for_response,
)
from modules.utils.payment_schedule import rebuild_schedule_for_document
from modules.utils.pricing import calc_total_amount, resolve_weekly_amount


_PERSONAL_FIELDS = {
    "full_name",
    "inn",
    "registration_address",
    "residential_address",
    "passport",
    "phone",
    "bank_account",
}

_ADMIN_DOCUMENT_FIELDS = {
    "contract_number",
    "bike_serial",
    "akb1_serial",
    "akb2_serial",
    "akb3_serial",
    "amount",
    "amount_text",
}


class AdminHandler:
    def __init__(
        self,
        db: Session = Depends(get_session),
        admin: User = Depends(get_current_admin),
    ):
        self.db = db
        self.admin = admin
        self.cipher = get_sensitive_data_cipher()

    def list_users(
        self, status_filter: DocumentStatusEnum | None = None
    ) -> list[UserWithDocumentSummary]:
        query = self.db.query(User).filter(User.role == "user")
        if status_filter is not None:
            query = query.filter(User.status == status_filter)
        users = query.all()
        result: list[UserWithDocumentSummary] = []

        for u in users:
            result.append(self._build_user_summary(u))
        return result

    def get_user_summary(self, user_id: int) -> UserWithDocumentSummary:
        user = self._get_user_or_404(user_id)
        return self._build_user_summary(user)

    def get_user_document(self, user_id: int, document_id: int) -> UserDocumentRead:
        user = self._get_user_or_404(user_id)
        self._ensure_user_approved(user)

        doc = self._get_user_document_or_404(user_id, document_id)
        return UserDocumentRead(**serialize_document_for_response(doc, self.cipher))

    def list_user_contracts(self, user_id: int):
        user = self._get_user_or_404(user_id)
        self._ensure_user_approved(user)
        docs = UserDocument.refresh_user_documents_status(self.db, user_id)
        return [
            {
                **serialize_document_for_response(doc, self.cipher, user),
                "contract_docx_url": f"/admin/users/{user_id}/contract-docx/{doc.id}",
            }
            for doc in docs
        ]

    def update_user_document(
        self, user_id: int, body: UserDocumentAdminUpdateInput
    ) -> UserDocumentRead:
        user = self._get_user_or_404(user_id)
        self._ensure_user_approved(user)

        update_payload = body.model_dump(exclude_unset=True)
        update_payload.pop("contract_number", None)
        has_updates = bool(update_payload)

        doc = self._get_latest_user_document(user_id)

        if not doc:
            if not has_updates:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Нет данных для создания договора",
                )
            doc = self._create_document(user_id, user)
        elif not doc.active and has_updates:
            doc = self._create_document(user_id, user)

        if not has_updates:
            return UserDocumentRead(**serialize_document_for_response(doc, self.cipher))

        update_payload.pop("amount", None)
        update_payload.pop("amount_text", None)

        encrypted_data = encrypt_document_fields(
            update_payload,
            self.cipher,
            allowed_fields=_ADMIN_DOCUMENT_FIELDS,
        )

        for field, value in encrypted_data.items():
            setattr(doc, field, value)

        if body.weeks_count is not None or "weeks_count" in body.model_fields_set:
            doc.weeks_count = body.weeks_count

        if body.filled_date is not None or "filled_date" in body.model_fields_set:
            doc.filled_date = body.filled_date

        needs_amount_refresh = bool(
            {"bike_serial", "weeks_count", "filled_date", "amount"}
            & body.model_fields_set
        )
        self._recalculate_contract_amount(doc, require_data=needs_amount_refresh)

        doc.refresh_dates_and_status(update_active=False)
        self._ensure_contract_number(doc)

        self.db.commit()
        UserDocument.refresh_user_documents_status(self.db, user_id)
        self.db.refresh(doc)
        return UserDocumentRead(**serialize_document_for_response(doc, self.cipher))

    def approve_document(self, user_id: int) -> UserDocumentRead:
        user = self._get_user_or_404(user_id)
        doc = self._get_latest_user_document(user_id)
        self._ensure_personal_data_filled(user)

        user.status = DocumentStatusEnum.APPROVED
        user.rejection_reason = None

        self.db.commit()
        self.db.refresh(user)
        if doc:
            self.db.refresh(doc)
        return UserDocumentRead(
            **serialize_document_for_response(doc, self.cipher, user)
        )

    def reject_document(
        self, user_id: int, body: DocumentRejectRequest
    ) -> UserDocumentRead:
        user = self._get_user_or_404(user_id)
        doc = self._get_latest_user_document(user_id)

        user.status = DocumentStatusEnum.REJECTED
        user.rejection_reason = body.reason
        if doc:
            doc.contract_text = None
            doc.weeks_count = None
            doc.filled_date = None
            doc.end_date = None
            doc.active = False

        for field in _PERSONAL_FIELDS:
            setattr(user, field, None)

        if doc:
            for field in _ADMIN_DOCUMENT_FIELDS:
                setattr(doc, field, None)

        self.db.query(ContractPayment).filter(ContractPayment.user_id == user_id).delete()
        self.db.query(UserDocument).filter(UserDocument.user_id == user_id).update({"signed": False})

        self.db.commit()
        self.db.refresh(user)
        if doc:
            self.db.refresh(doc)
        return UserDocumentRead(**serialize_document_for_response(doc, self.cipher, user))


    def sign_user_document(self, user_id: int, document_id: int) -> UserDocumentRead:
        user = self._get_user_or_404(user_id)
        self._ensure_user_approved(user)

        docs = UserDocument.refresh_user_documents_status(self.db, user_id)
        target_doc = next((doc for doc in docs if doc.id == document_id), None)
        if not target_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Документ не найден",
            )

        for doc in docs:
            doc.signed = doc.id == document_id

        self._recalculate_contract_amount(target_doc, require_data=True)

        rebuild_schedule_for_document(self.db, target_doc)
        self.db.flush()
        self._sync_inventory_statuses_for_user_documents(docs)

        self.db.commit()
        self.db.refresh(target_doc)
        return UserDocumentRead(**serialize_document_for_response(target_doc, self.cipher, user))

    def _sync_inventory_statuses_for_user_documents(
        self, docs: list[UserDocument]
    ) -> None:
        candidate_bike_numbers: set[str] = set()
        candidate_battery_numbers: set[str] = set()

        for doc in docs:
            decrypted_doc = decrypt_document_fields(doc, self.cipher)
            bike_number = self._normalize_asset_number(decrypted_doc.get("bike_serial"))
            if bike_number:
                candidate_bike_numbers.add(bike_number)

            for field in ("akb1_serial", "akb2_serial", "akb3_serial"):
                battery_number = self._normalize_asset_number(decrypted_doc.get(field))
                if battery_number:
                    candidate_battery_numbers.add(battery_number)

        if not candidate_bike_numbers and not candidate_battery_numbers:
            return

        signed_active_docs = (
            self.db.query(UserDocument)
            .filter(UserDocument.signed.is_(True))
            .all()
        )

        rented_bike_numbers: set[str] = set()
        rented_battery_numbers: set[str] = set()

        for doc in signed_active_docs:
            decrypted_doc = decrypt_document_fields(doc, self.cipher)
            bike_number = self._normalize_asset_number(decrypted_doc.get("bike_serial"))
            if bike_number:
                rented_bike_numbers.add(bike_number)

            for field in ("akb1_serial", "akb2_serial", "akb3_serial"):
                battery_number = self._normalize_asset_number(decrypted_doc.get(field))
                if battery_number:
                    rented_battery_numbers.add(battery_number)

        if candidate_bike_numbers:
            bikes = (
                self.db.query(Bike)
                .filter(
                    or_(
                        Bike.number.in_(candidate_bike_numbers),
                        Bike.vin.in_(candidate_bike_numbers),
                    )
                )
                .all()
            )
            for bike in bikes:
                bike_number = self._normalize_asset_number(bike.number)
                bike_vin = self._normalize_asset_number(bike.vin)
                bike.status = (
                    "rented"
                    if bike_number in rented_bike_numbers or bike_vin in rented_bike_numbers
                    else "free"
                )

        if candidate_battery_numbers:
            batteries = (
                self.db.query(Battery)
                .filter(Battery.number.in_(candidate_battery_numbers))
                .all()
            )
            for battery in batteries:
                battery_number = self._normalize_asset_number(battery.number)
                battery.status = (
                    "rented" if battery_number in rented_battery_numbers else "free"
                )

    @staticmethod
    def _normalize_asset_number(value: object) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None

    def create_return_act(
        self, user_id: int, document_id: int, body: ReturnActCreateRequest
    ) -> ReturnActRead:
        user = self._get_user_or_404(user_id)
        self._ensure_user_approved(user)

        doc = self._get_user_document_or_404(user_id, document_id)
        if not doc.signed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Акт возврата можно создать только для подписанного договора",
            )

        decrypted_doc = decrypt_document_fields(doc, self.cipher)
        contract_number = decrypted_doc.get("contract_number")
        rent_end_date = decrypted_doc.get("end_date")
        bike_serial = self._normalize_asset_number(decrypted_doc.get("bike_serial"))
        akb1_serial = self._normalize_asset_number(decrypted_doc.get("akb1_serial"))
        akb2_serial = self._normalize_asset_number(decrypted_doc.get("akb2_serial"))

        if not contract_number or not rent_end_date or not bike_serial:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="В договоре недостаточно данных для формирования акта возврата",
            )

        existing_act = (
            self.db.query(ReturnAct)
            .filter(ReturnAct.user_id == user_id, ReturnAct.document_id == document_id)
            .first()
        )
        if existing_act:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Акт возврата для данного договора уже создан",
            )

        filled_date = date.today()
        debt_due_date = filled_date + timedelta(days=body.debt_term_days)

        act = ReturnAct(
            user_id=user_id,
            document_id=document_id,
            return_act_number="",
            contract_number=str(contract_number),
            rent_end_date=rent_end_date,
            filled_date=filled_date,
            bike_serial=bike_serial,
            akb1_serial=akb1_serial,
            akb2_serial=akb2_serial,
            is_fix_bike=body.is_fix_bike,
            is_fix_akb_1=body.is_fix_AKB_1,
            is_fix_akb_2=body.is_fix_AKB_2,
            damage_description=body.damage_description,
            damage_amount=body.damage_amount,
            debt_term_days=body.debt_term_days,
            debt_due_date=debt_due_date,
        )
        self.db.add(act)
        self.db.flush()

        act.return_act_number = f"{contract_number}-{act.id}"

        if body.damage_amount > 0:
            payment_number = (
                self.db.query(ContractPayment)
                .filter(ContractPayment.user_id == user_id)
                .count()
                + 1
            )
            damage_schedule = ContractPayment(
                user_id=user_id,
                document_id=document_id,
                payment_number=payment_number,
                due_date=debt_due_date,
                amount=Decimal(body.damage_amount),
                description=(
                    f"Оплата повреждений по акту возврата {act.return_act_number}. "
                    f"Срок оплаты до {debt_due_date.isoformat()}"
                ),
                payment_type="damage",
                status="pending",
            )
            self.db.add(damage_schedule)
            self.db.flush()
            act.damage_schedule_payment_id = damage_schedule.id

        used_days = (filled_date - doc.filled_date).days if doc.filled_date else 0
        used_weeks = max(1, (used_days + 6) // 7)
        weekly_amount_recalc = resolve_weekly_amount(self.db, bike_serial, used_weeks)
        recalculated_total = calc_total_amount(weekly_amount_recalc, used_weeks)

        pending_future_rent_rows = (
            self.db.query(ContractPayment)
            .filter(
                ContractPayment.user_id == user_id,
                ContractPayment.document_id == document_id,
                ContractPayment.payment_type == "rent",
                ContractPayment.status == "pending",
                ContractPayment.due_date > filled_date,
            )
            .all()
        )
        for payment_row in pending_future_rent_rows:
            self.db.delete(payment_row)

        accrued_rent_amount = (
            self.db.query(func.coalesce(func.sum(ContractPayment.amount), 0))
            .filter(
                ContractPayment.user_id == user_id,
                ContractPayment.document_id == document_id,
                ContractPayment.payment_type == "rent",
                ContractPayment.due_date <= filled_date,
            )
            .scalar()
        )
        accrued_rent_amount_decimal = Decimal(accrued_rent_amount)

        if recalculated_total > accrued_rent_amount_decimal:
            payment_number = (
                self.db.query(ContractPayment)
                .filter(ContractPayment.user_id == user_id)
                .count()
                + 1
            )
            debt_diff = recalculated_total - accrued_rent_amount_decimal
            recalc_schedule = ContractPayment(
                user_id=user_id,
                document_id=document_id,
                payment_number=payment_number,
                due_date=debt_due_date,
                amount=debt_diff,
                description=(
                    f"Перерасчет аренды по акту возврата {act.return_act_number}: "
                    f"фактический срок {used_weeks} нед."
                ),
                payment_type="recalculation",
                status="pending",
            )
            self.db.add(recalc_schedule)

        self._update_inventory_after_return_act(act)

        self.db.commit()
        self.db.refresh(act)
        return ReturnActRead(
            id=act.id,
            return_act_number=act.return_act_number,
            contract_number=act.contract_number,
            rent_end_date=act.rent_end_date,
            filled_date=act.filled_date,
            bike_serial=act.bike_serial,
            akb1_serial=act.akb1_serial,
            akb2_serial=act.akb2_serial,
            is_fix_bike=act.is_fix_bike,
            is_fix_AKB_1=act.is_fix_akb_1,
            is_fix_AKB_2=act.is_fix_akb_2,
            damage_description=act.damage_description,
            damage_amount=act.damage_amount,
            debt_term_days=act.debt_term_days,
            debt_due_date=act.debt_due_date,
            damage_schedule_payment_id=act.damage_schedule_payment_id,
        )

    def list_user_return_acts(self, user_id: int) -> list[ReturnActRead]:
        self._get_user_or_404(user_id)
        acts = (
            self.db.query(ReturnAct)
            .filter(ReturnAct.user_id == user_id)
            .order_by(ReturnAct.created_at.desc())
            .all()
        )
        return [self._serialize_return_act(act) for act in acts]

    def get_user_return_act(self, user_id: int, act_id: int) -> ReturnActRead:
        self._get_user_or_404(user_id)
        act = self._get_return_act_or_404(user_id, act_id)
        return self._serialize_return_act(act)

    def _get_return_act_or_404(self, user_id: int, act_id: int) -> ReturnAct:
        act = (
            self.db.query(ReturnAct)
            .filter(ReturnAct.id == act_id, ReturnAct.user_id == user_id)
            .first()
        )
        if not act:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Акт возврата не найден",
            )
        return act

    def _serialize_return_act(self, act: ReturnAct) -> ReturnActRead:
        return ReturnActRead(
            id=act.id,
            return_act_number=act.return_act_number,
            contract_number=act.contract_number,
            rent_end_date=act.rent_end_date,
            filled_date=act.filled_date,
            bike_serial=act.bike_serial,
            akb1_serial=act.akb1_serial,
            akb2_serial=act.akb2_serial,
            is_fix_bike=act.is_fix_bike,
            is_fix_AKB_1=act.is_fix_akb_1,
            is_fix_AKB_2=act.is_fix_akb_2,
            damage_description=act.damage_description,
            damage_amount=act.damage_amount,
            debt_term_days=act.debt_term_days,
            debt_due_date=act.debt_due_date,
            damage_schedule_payment_id=act.damage_schedule_payment_id,
        )

    def _update_inventory_after_return_act(self, act: ReturnAct) -> None:
        bike_status = "free" if act.is_fix_bike else "repair"
        bike = (
            self.db.query(Bike)
            .filter(or_(Bike.number == act.bike_serial, Bike.vin == act.bike_serial))
            .first()
        )
        if bike:
            bike.status = bike_status

        if act.akb1_serial:
            akb1 = self.db.query(Battery).filter(Battery.number == act.akb1_serial).first()
            if akb1:
                akb1.status = "free" if act.is_fix_akb_1 else "repair"

        if act.akb2_serial:
            akb2 = self.db.query(Battery).filter(Battery.number == act.akb2_serial).first()
            if akb2:
                akb2.status = "free" if act.is_fix_akb_2 else "repair"

    def get_user_payment_schedule(self, user_id: int) -> list[ContractPayment]:
        self._get_user_or_404(user_id)
        return (
            self.db.query(ContractPayment)
            .filter(ContractPayment.user_id == user_id)
            .order_by(ContractPayment.payment_number.asc())
            .all()
        )

    def get_contract_docx_path(self, user_id: int, document_id: int) -> str:
        user = self._get_user_or_404(user_id)
        doc = self._get_user_document_or_404(user_id, document_id)

        if user.status != DocumentStatusEnum.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Данные пользователя не одобрены",
            )

        decrypted_fields = {
            **decrypt_user_fields(user, self.cipher),
            **decrypt_document_fields(doc, self.cipher),
        }
        return render_contract_docx(user, doc, decrypted_fields)

    def get_return_act_docx_path(self, user_id: int, act_id: int) -> str:
        self._get_user_or_404(user_id)
        act = self._get_return_act_or_404(user_id, act_id)

        values = {
            "№_Акта_возврата": act.return_act_number,
            "Дат_конец_аренды": act.rent_end_date.strftime("%d.%m.%Y"),
            "№_договора": act.contract_number,
            "Дата_заполнения": act.filled_date.strftime("%d.%m.%Y"),
            "Серийный_номер_велик": act.bike_serial,
            "Серийный_нормер_АКБ_1": act.akb1_serial or "",
            "Серийный_нормер_АКБ_2": act.akb2_serial or "",
            "is_fix_bike": str(act.is_fix_bike),
            "is_fix_AKB_1": str(act.is_fix_akb_1),
            "is_fix_AKB_2": str(act.is_fix_akb_2),
            "Описание_повреждений": act.damage_description or "",
            "Сумма_повреждений": act.damage_amount,
            "Срок_долга": act.debt_term_days,
        }
        return render_return_act_docx(values, user_id=user_id, act_id=act.id)

    def _get_user_or_404(self, user_id: int) -> User:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден",
            )
        return user

    def _build_user_summary(self, user: User) -> UserWithDocumentSummary:
        personal_data = decrypt_user_fields(user, self.cipher)
        return UserWithDocumentSummary(
            id=user.id,
            email=user.email,
            full_name=personal_data.get("full_name"),
            inn=personal_data.get("inn"),
            registration_address=personal_data.get("registration_address"),
            residential_address=personal_data.get("residential_address"),
            passport=personal_data.get("passport"),
            phone=personal_data.get("phone"),
            bank_account=personal_data.get("bank_account"),
            role=user.role,
            status=DocumentStatus(user.status),
            rejection_reason=user.rejection_reason,
        )

    def _get_user_document_or_404(
        self, user_id: int, document_id: int | None = None
    ) -> UserDocument:
        doc = self._get_latest_user_document(user_id, document_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Документ не найден",
            )
        return doc

    def _get_latest_user_document(
        self, user_id: int, document_id: int | None = None
    ) -> UserDocument | None:
        docs = UserDocument.refresh_user_documents_status(self.db, user_id)
        if document_id is not None:
            return next((doc for doc in docs if doc.id == document_id), None)
        return docs[0] if docs else None

    def _create_document(self, user_id: int, user: User) -> UserDocument:
        new_doc = UserDocument(user_id=user_id)
        new_doc.user = user
        self.db.add(new_doc)
        return new_doc

    def _ensure_contract_number(self, doc: UserDocument) -> None:
        if doc.contract_number:
            return

        if doc.id is None:
            self.db.flush()

        total_user_documents = (
            self.db.query(UserDocument)
            .filter(UserDocument.user_id == doc.user_id)
            .count()
        )

        contract_number = f"{doc.user_id}.{doc.id}.{total_user_documents}"
        doc.contract_number = self.cipher.encrypt(contract_number)

    def _generate_amount_text(self, amount: str | int | float | None) -> str | None:
        if amount is None:
            return None

        normalized = (
            str(amount)
            .strip()
            .replace(" ", "")
            .replace("\u00a0", "")
            .replace(",", "")
        )

        if not normalized:
            return None

        try:
            numeric_value = int(Decimal(normalized))
        except (InvalidOperation, ValueError):
            return None

        return num2words(numeric_value, lang="ru")

    def _recalculate_contract_amount(
        self, doc: UserDocument, require_data: bool = False
    ) -> None:
        decrypted_doc = decrypt_document_fields(doc, self.cipher)
        bike_serial = self._normalize_asset_number(decrypted_doc.get("bike_serial"))

        if not bike_serial or not doc.weeks_count:
            if require_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Для автоподсчета amount требуются bike_serial и weeks_count",
                )
            return

        weekly_amount = resolve_weekly_amount(self.db, bike_serial, doc.weeks_count)
        total_amount = int(calc_total_amount(weekly_amount, doc.weeks_count))
        encrypted_amount = encrypt_document_fields(
            {
                "amount": total_amount,
                "amount_text": self._generate_amount_text(total_amount),
            },
            self.cipher,
            allowed_fields={"amount", "amount_text"},
        )
        for field, value in encrypted_amount.items():
            setattr(doc, field, value)
    
    def _ensure_user_approved(self, user: User) -> None:
        if user.status != DocumentStatusEnum.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Данные пользователя не одобрены",
            )

    def _ensure_personal_data_filled(self, user: User) -> None:
        personal_data = decrypt_user_fields(user, self.cipher)
        missing_fields = [field for field in _PERSONAL_FIELDS if not personal_data.get(field)]

        if missing_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Недостаточно данных пользователя для подтверждения",
            )
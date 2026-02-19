from datetime import date
from enum import Enum
from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    FieldValidationInfo,
    field_validator,
)

class DocumentStatus(str, Enum):
    draft = "draft"
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


def _validate_digits_only(value: str | int | None, field_name: str) -> int | None:
    if value is None:
        return None

    normalized = (
        str(value)
        .strip()
        .replace(" ", "")
        .replace("\u00a0", "")
        .replace(",", "")
    )
    if not normalized.isdigit():
        raise ValueError(f"{field_name} должен содержать только целые числа")
    return int(normalized)


class UserDocumentUserUpdate(BaseModel):
    full_name: str
    inn: int = Field(
        ...,
        description="Только цифры",
        examples=[0],
    )
    registration_address: str
    residential_address: str
    passport: int = Field(
        ...,
        description="Только цифры",
        examples=[0],
    )
    phone: str = Field(
        ...,
        description="Начинается с '+' и содержит только цифры",
        examples=["+79991234567"],
    )
    bank_account: int | None = Field(
        default=None,
        description="Только цифры, заполняется пользователем при наличии",
        examples=[0],
    )

    @field_validator("inn", "passport", "bank_account", mode="before")
    @classmethod
    def validate_digits(cls, value: str | int | None, info: FieldValidationInfo):
        return _validate_digits_only(value, info.field_name)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None):
        if value is None:
            return None

        normalized = str(value).strip()

        if not normalized.startswith("+"):
            raise ValueError("phone должен начинаться с символа '+'")

        digits_only = normalized[1:]
        if not digits_only.isdigit():
            raise ValueError("phone должен содержать только цифры после '+'")

        return normalized



class UserDocumentAdminUpdate(BaseModel):
    contract_number: str | None = Field(
        default=None,
        description="Генерируется автоматически — не заполняйте вручную",
        json_schema_extra={"readOnly": True},
    )
    bike_serial: str | None = None
    akb1_serial: str | None = None
    akb2_serial: str | None = None
    akb3_serial: str | None = None
    amount: int | None = Field(
        default=None,
        description="Только цифры",
        examples=[0],
    )
    amount_text: str | None = Field(
        default=None,
        description="Генерируется автоматически из суммы — не заполняйте вручную",
        json_schema_extra={"readOnly": True},
    )
    weeks_count: int | None = None
    filled_date: date | None = None
    end_date: date | None = Field(
        default=None,
        description="Вычисляется автоматически — не заполняйте вручную",
        json_schema_extra={"readOnly": True},
    )

    @field_validator("amount", mode="before")
    @classmethod
    def validate_amount(cls, value: str | int | None):
        return _validate_digits_only(value, "amount")


class UserDocumentAdminUpdateInput(UserDocumentAdminUpdate):
    @field_validator("contract_number", "amount_text", "end_date")
    @classmethod
    def forbid_manual(cls, value, info: FieldValidationInfo):
        if value is not None:
            raise ValueError(
                f"{info.field_name} заполняется автоматически и не должен передаваться"
            )
        return value


class UserDocumentBase(UserDocumentUserUpdate, UserDocumentAdminUpdate):
    pass


class UserDocumentRead(UserDocumentBase):
    full_name: str | None = None
    inn: int | None = None
    registration_address: str | None = None
    residential_address: str | None = None
    passport: int | None = None
    phone: str | None = None
    bank_account: int | None = None
    id: int | None = None
    status: DocumentStatus
    rejection_reason: str | None = None
    active: bool = False
    signed: bool = False
    contract_text: str | None = None

    model_config = ConfigDict(from_attributes=True)


class UserContractItem(UserDocumentRead):
    contract_docx_url: str | None = None


class DocumentRejectRequest(BaseModel):
    reason: str


class UserWithDocumentSummary(BaseModel):
    id: int
    email: EmailStr
    full_name: str | None = None
    inn: int | None = None
    registration_address: str | None = None
    residential_address: str | None = None
    passport: int | None = None
    phone: str | None = None
    bank_account: int | None = None
    role: str
    status: DocumentStatus
    rejection_reason: str | None = None

    model_config = ConfigDict(from_attributes=True)

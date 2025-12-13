from datetime import date
from enum import Enum
from typing import List

from pydantic import BaseModel, EmailStr, ConfigDict


class DocumentStatus(str, Enum):
    draft = "draft"
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class UserDocumentUserUpdate(BaseModel):
    full_name: str
    inn: str
    registration_address: str
    residential_address: str
    passport: str
    phone: str
    bank_account: str | None = None



class UserDocumentAdminUpdate(BaseModel):
    contract_number: str | None = None
    bike_serial: str | None = None
    akb1_serial: str | None = None
    akb2_serial: str | None = None
    akb3_serial: str | None = None
    amount: str | None = None
    amount_text: str | None = None
    weeks_count: int | None = None
    filled_date: date | None = None
    end_date: date | None = None


class UserDocumentBase(UserDocumentUserUpdate, UserDocumentAdminUpdate):
    pass


class UserDocumentRead(UserDocumentBase):
    id: int | None = None
    status: DocumentStatus
    rejection_reason: str | None = None
    active: bool = False
    contract_text: str | None = None

    model_config = ConfigDict(from_attributes=True)


class DocumentRejectRequest(BaseModel):
    reason: str


class UserWithDocumentSummary(BaseModel):
    id: int
    email: EmailStr
    full_name: str | None = None
    inn: str | None = None
    registration_address: str | None = None
    residential_address: str | None = None
    passport: str | None = None
    phone: str | None = None
    bank_account: str | None = None
    role: str
    status: DocumentStatus
    rejection_reason: str | None = None

    model_config = ConfigDict(from_attributes=True)

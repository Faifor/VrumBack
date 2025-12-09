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
    address: str
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
    filled_date: str | None = None
    end_date: str | None = None


class UserDocumentBase(UserDocumentUserUpdate, UserDocumentAdminUpdate):
    pass


class UserDocumentRead(UserDocumentBase):
    id: int
    status: DocumentStatus
    rejection_reason: str | None = None
    contract_text: str | None = None

    model_config = ConfigDict(from_attributes=True)


class DocumentRejectRequest(BaseModel):
    reason: str


class UserWithDocumentSummary(BaseModel):
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    role: str
    document_status: DocumentStatus | None = None

    model_config = ConfigDict(from_attributes=True)

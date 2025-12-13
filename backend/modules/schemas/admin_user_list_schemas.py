from pydantic import BaseModel, EmailStr, Field
from typing import Literal


DocumentStatus = Literal["draft", "pending", "approved", "rejected"]


class UserWithDocumentSummary(BaseModel):
    id: int = Field(...)
    email: EmailStr = Field(...)
    full_name: str | None = Field(default=None)
    inn: str | None = Field(default=None)
    registration_address: str | None = Field(default=None)
    residential_address: str | None = Field(default=None)
    passport: str | None = Field(default=None)
    phone: str | None = Field(default=None)
    bank_account: str | None = Field(default=None)
    role: str = Field(...)
    status: DocumentStatus = Field(...)
    rejection_reason: str | None = Field(default=None)

    model_config = {"from_attributes": True}

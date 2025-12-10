from pydantic import BaseModel, EmailStr, Field
from typing import Literal


DocumentStatus = Literal["draft", "pending", "approved", "rejected"]


class UserWithDocumentSummary(BaseModel):
    id: int = Field(...)
    email: EmailStr = Field(...)
    full_name: str | None = Field(default=None)
    role: str = Field(...)
    document_status: DocumentStatus | None = Field(default=None)

    model_config = {"from_attributes": True}

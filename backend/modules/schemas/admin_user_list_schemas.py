from pydantic import BaseModel, EmailStr, Field
from typing import Literal


DocumentStatus = Literal["draft", "pending", "approved", "rejected"]


class UserWithDocumentSummary(BaseModel):
    id: int = Field(...)
    email: EmailStr = Field(...)
    first_name: str = Field(...)
    last_name: str = Field(...)
    role: str = Field(...)
    document_status: DocumentStatus | None = Field(default=None)

    model_config = {"from_attributes": True}

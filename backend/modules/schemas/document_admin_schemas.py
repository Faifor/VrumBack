from pydantic import BaseModel, Field


class DocumentRejectRequest(BaseModel):
    reason: str = Field(...)

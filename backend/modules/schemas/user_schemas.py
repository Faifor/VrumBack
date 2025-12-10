from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr = Field(...)
    password: str = Field(...)


class UserRead(BaseModel):
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

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None)
    inn: str | None = Field(default=None)
    registration_address: str | None = Field(default=None)
    residential_address: str | None = Field(default=None)
    passport: str | None = Field(default=None)
    phone: str | None = Field(default=None)
    bank_account: str | None = Field(default=None)

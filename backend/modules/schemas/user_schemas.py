from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr = Field(...)
    password: str = Field(...)


class UserRead(BaseModel):
    id: int = Field(...)
    email: EmailStr = Field(...)
    full_name: str | None = Field(default=None)
    inn: int | None = Field(default=None, description="Только цифры")
    registration_address: str | None = Field(default=None)
    residential_address: str | None = Field(default=None)
    passport: int | None = Field(default=None, description="Только цифры")
    phone: str | None = Field(default=None)
    bank_account: int | None = Field(default=None, description="Только цифры")
    role: str = Field(...)

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None)
    inn: int | None = Field(default=None, description="Только цифры")
    registration_address: str | None = Field(default=None)
    residential_address: str | None = Field(default=None)
    passport: int | None = Field(default=None, description="Только цифры")
    phone: str | None = Field(default=None)
    bank_account: int | None = Field(default=None, description="Только цифры")

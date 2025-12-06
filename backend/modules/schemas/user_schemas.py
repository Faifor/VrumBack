from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr = Field(...)
    password: str = Field(...)
    first_name: str = Field(...)
    last_name: str = Field(...)


class UserRead(BaseModel):
    id: int = Field(...)
    email: EmailStr = Field(...)
    first_name: str = Field(...)
    last_name: str = Field(...)
    role: str = Field(...)

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    first_name: str | None = Field(default=None)
    last_name: str | None = Field(default=None)

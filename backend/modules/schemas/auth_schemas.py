from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str = Field(...)
    token_type: str = Field(default="bearer")


class TokenData(BaseModel):
    sub: str | None = Field(default=None)


class UserAuthRequest(BaseModel):
    email: EmailStr = Field(...)
    password: str = Field(...)

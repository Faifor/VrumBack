from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str = Field(...)
    refresh_token: str = Field(...)
    token_type: str = Field(default="bearer")


class TokenData(BaseModel):
    sub: str | None = Field(default=None)


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(...)


class UserAuthRequest(BaseModel):
    email: EmailStr = Field(...)
    password: str = Field(...)


class PasswordResetRequest(BaseModel):
    email: EmailStr = Field(...)


class PasswordResetConfirm(BaseModel):
    email: EmailStr = Field(...)
    code: str = Field(...)
    new_password: str = Field(...)

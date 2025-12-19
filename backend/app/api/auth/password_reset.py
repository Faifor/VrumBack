from fastapi import APIRouter, Depends

from app.handlers.auth.auth_handler import AuthHandler
from modules.schemas.auth_schemas import (
    PasswordResetConfirm,
    PasswordResetRequest,
)


router = APIRouter()


@router.post("/password/forgot")
async def request_password_reset(
    req: PasswordResetRequest, handler: AuthHandler = Depends()
):
    return await handler.request_password_reset(req)


@router.post("/password/reset")
async def reset_password(
    req: PasswordResetConfirm, handler: AuthHandler = Depends()
):
    return await handler.reset_password(req)

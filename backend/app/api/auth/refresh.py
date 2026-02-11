from fastapi import APIRouter, Depends

from app.handlers.auth.auth_handler import AuthHandler
from modules.schemas.auth_schemas import RefreshTokenRequest, Token

router = APIRouter()


@router.post("/refresh", response_model=Token)
async def refresh_token(
    payload: RefreshTokenRequest,
    handler: AuthHandler = Depends(),
):
    return await handler.refresh(payload.refresh_token)
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from modules.schemas.auth_schemas import Token
from app.handlers.auth.auth_handler import AuthHandler

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    handler: AuthHandler = Depends(),
):
    return await handler.login(form)

from fastapi import APIRouter, Depends

from app.handlers.auth.auth_handler import AuthHandler
from modules.schemas.auth_schemas import RegistrationCodeRequest
from modules.schemas.user_schemas import UserCreate, UserRead

router = APIRouter()


@router.post('/register/code')
async def request_registration_code(
    req: RegistrationCodeRequest,
    handler: AuthHandler = Depends(),
):
    return await handler.request_registration_code(req)


@router.post('/register', response_model=UserRead)
async def register(
    req: UserCreate,
    handler: AuthHandler = Depends(),
):
    return await handler.register(req)

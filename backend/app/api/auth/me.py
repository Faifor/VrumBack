from fastapi import APIRouter, Depends
from modules.schemas.user_schemas import UserRead
from app.handlers.auth.auth_handler import AuthHandler
from modules.utils.jwt_utils import get_current_user
from modules.models.user import User

router = APIRouter()


@router.get("/me", response_model=UserRead)
async def me(
    current_user: User = Depends(get_current_user),
    handler: AuthHandler = Depends(),
):
    return await handler.me(current_user)

from fastapi import APIRouter, Depends
from modules.schemas.user_schemas import UserCreate, UserRead
from app.handlers.auth.auth_handler import AuthHandler

router = APIRouter()


@router.post("/register", response_model=UserRead)
async def register(
    req: UserCreate,
    handler: AuthHandler = Depends(),
):
    return await handler.register(req)

from fastapi import APIRouter

from .register import router as register_router
from .login import router as login_router
from .me import router as me_router
from .password_reset import router as password_reset_router
from .refresh import router as refresh_router

auth_router = APIRouter(prefix="/auth", tags=["Auth"])

auth_router.include_router(register_router)
auth_router.include_router(login_router)
auth_router.include_router(me_router)
auth_router.include_router(password_reset_router)
auth_router.include_router(refresh_router)

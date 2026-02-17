from fastapi import APIRouter

from .routes import router

payments_router = APIRouter(prefix="/api", tags=["Payments"])
payments_router.include_router(router)
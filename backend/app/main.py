from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.admin import admin_router
from app.api.auth import auth_router
from app.api.user_document import user_document_router
from modules.utils.config import settings
from modules.utils.logging_utils import install_logging_filters


app = FastAPI(
    title="Bike API",
    version="1.0.0",
)

install_logging_filters()

if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.TRUSTED_HOSTS,
)

app.include_router(admin_router)
app.include_router(auth_router)
app.include_router(user_document_router)


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "ok"}

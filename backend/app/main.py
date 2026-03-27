import logging
import logging.handlers
from pathlib import Path

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from app.api.admin import admin_router
from app.api.auth import auth_router
from app.api.payments.routes import router as payments_router
from app.api.user_document import user_document_router


def _setup_logging() -> None:
    log_dir = Path("/backend/logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Rotate at midnight, keep 5 days
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=log_dir / "app.log",
        when="midnight",
        interval=1,
        backupCount=5,
        encoding="utf-8",
        utc=True,
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


_setup_logging()

openapi_tags = [
    {"name": "Auth", "description": "Авторизация, регистрация и управление токенами."},
    {"name": "User Documents", "description": "Работа пользователя со своей анкетой/документом."},
    {"name": "User Contracts", "description": "Контракты и файлы договоров пользователя."},
    {"name": "Payments", "description": "Платежи и график платежей пользователя."},
    {"name": "Autopay", "description": "Подключение и списание автоплатежей."},
    {"name": "Orders", "description": "Операции с заказами и перерасчетами."},
    {"name": "YooKassa Webhook", "description": "Webhook-эндпоинты интеграции с YooKassa."},
    {"name": "Admin Users", "description": "Администрирование пользователей."},
    {"name": "Admin Documents", "description": "Проверка и модерация документов пользователей."},
    {"name": "Admin Contracts", "description": "Контракты пользователей и действия с ними."},
    {"name": "Admin Payments", "description": "Платежные данные пользователей для администратора."},
    {"name": "Admin Inventory", "description": "Управление локациями, велосипедами и батареями."},
    {"name": "Admin System", "description": "Служебные административные операции."},
]

app = FastAPI(
    title="Bike API",
    version="1.0.0",
    openapi_tags=openapi_tags,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_router)
app.include_router(auth_router)
app.include_router(user_document_router)
app.include_router(payments_router, prefix="/api")


@app.get("/health", status_code=status.HTTP_200_OK, tags=["Admin System"])
async def health_check():
    return {"status": "ok"}
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    ENCRYPTION_KEY: str
    SMTP_HOST: str = Field(default="localhost")
    SMTP_PORT: int = Field(default=465)
    SMTP_USERNAME: str | None = Field(default=None)
    SMTP_PASSWORD: str | None = Field(default=None)
    SMTP_USE_TLS: bool = Field(default=True)
    SMTP_USE_SSL: bool = Field(default=False)
    EMAIL_FROM: str = Field(default="noreply@vrum53.ru")
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = Field(default=15)
    PASSWORD_RESET_MAX_ATTEMPTS: int = Field(default=3)
    PASSWORD_RESET_LOCKOUT_SECONDS: int = Field(default=20)
    SECURE_STORAGE_DIR: Path = BASE_DIR / "secure_storage"
    CONTRACT_TEMPLATE_FILENAME: str = "contract_template.docx"

    class Config:
        # Use the project-level .env file regardless of the working directory
        env_file = BASE_DIR / ".env"
        env_file_encoding = "utf-8"
        # extra = "ignore"


settings = Settings()

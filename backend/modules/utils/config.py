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
    SECURE_STORAGE_DIR: Path = BASE_DIR / "secure_storage"
    CONTRACT_TEMPLATE_FILENAME: str = "contract_template.docx"

    class Config:
        # Use the project-level .env file regardless of the working directory
        env_file = BASE_DIR / ".env"
        env_file_encoding = "utf-8"
        # extra = "ignore"


settings = Settings()

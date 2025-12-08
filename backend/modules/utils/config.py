from pydantic import Field, model_validator
from pydantic_settings import BaseSettings



class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    PII_ENCRYPTION_KEY: str
    CORS_ORIGINS: list[str] = Field(default_factory=list)
    TRUSTED_HOSTS: list[str] = Field(
        default_factory=lambda: ["localhost", "127.0.0.1"]
    )

    @model_validator(mode="before")
    @classmethod
    def parse_comma_separated_lists(cls, values: dict):
        if values is None:
            return values

        for key in ("CORS_ORIGINS", "TRUSTED_HOSTS"):
            raw_value = values.get(key)
            if isinstance(raw_value, str):
                values[key] = [item.strip() for item in raw_value.split(",") if item.strip()]

        return values

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

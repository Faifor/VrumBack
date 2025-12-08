from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, EnvSettingsSource, SettingsConfigDict


class LenientEnvSettingsSource(EnvSettingsSource):
    """Env source that tolerates empty strings and non-JSON list values."""

    def decode_complex_value(self, field_name, field, value):
        if value == "":
            # Treat empty env vars as missing so defaults remain intact.
            return None

        try:
            return super().decode_complex_value(field_name, field, value)
        except ValueError:
            # Fall back to raw value (e.g., comma-separated string) instead of
            # raising when JSON decoding fails.
            return value


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    DATABASE_URL: str = "sqlite:///./app.db"
    SECRET_KEY: str = "dev-secret-key-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    PII_ENCRYPTION_KEY: str = "Q60CFF6sFR0FPBqzTJv71V7J7rBZ3ABF53h8zCHUzqg="
    CORS_ORIGINS: list[str] | str | None = Field(default_factory=list)
    TRUSTED_HOSTS: list[str] | str | None = Field(
        default_factory=lambda: ["localhost", "127.0.0.1"]
    )

    @field_validator("CORS_ORIGINS", "TRUSTED_HOSTS", mode="before")
    @classmethod
    def parse_comma_separated_strings(cls, value):
        if value is None:
            return value

        if isinstance(value, list):
            return value

        if isinstance(value, str):
            if value.strip() == "":
                return None
            return [item.strip() for item in value.split(",") if item.strip()]

        return value

    @model_validator(mode="after")
    def ensure_defaults(self):
        if self.CORS_ORIGINS is None:
            self.CORS_ORIGINS = []

        if self.TRUSTED_HOSTS is None or not self.TRUSTED_HOSTS:
            self.TRUSTED_HOSTS = ["localhost", "127.0.0.1"]

        return self

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        return (
            init_settings,
            dotenv_settings,
            LenientEnvSettingsSource(settings_cls),
            file_secret_settings,
        )

settings = Settings()

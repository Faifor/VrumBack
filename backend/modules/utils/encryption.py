from __future__ import annotations

import logging
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.types import String, TypeDecorator

from modules.utils.config import settings


logger = logging.getLogger(__name__)


class EncryptedString(TypeDecorator):
    """Encrypts/decrypts string fields at the SQLAlchemy column layer."""

    impl = String
    cache_ok = True

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._fernet = Fernet(settings.PII_ENCRYPTION_KEY.encode())

    def process_bind_param(self, value: str | None, dialect: Any) -> str | None:  # noqa: ARG002
        if value is None:
            return None
        token = self._fernet.encrypt(value.encode("utf-8"))
        return token.decode("utf-8")

    def process_result_value(self, value: str | None, dialect: Any) -> str | None:  # noqa: ARG002
        if value is None:
            return None

        try:
            decrypted = self._fernet.decrypt(value.encode("utf-8"))
            return decrypted.decode("utf-8")
        except InvalidToken:
            logger.warning("Failed to decrypt column value; returning raw string")
            return value
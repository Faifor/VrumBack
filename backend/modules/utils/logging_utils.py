from __future__ import annotations

import logging
import re
from typing import Iterable


SENSITIVE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"Bearer\s+[A-Za-z0-9._\-]+", flags=re.IGNORECASE),
    re.compile(r"token=[^\s]+", flags=re.IGNORECASE),
    re.compile(r"passport=[^\s]+", flags=re.IGNORECASE),
    re.compile(r"address=[^\s]+", flags=re.IGNORECASE),
)


class RedactPIIFilter(logging.Filter):
    """Removes obvious PII and tokens from log messages."""

    def __init__(self, patterns: Iterable[re.Pattern[str]] | None = None) -> None:
        super().__init__()
        self.patterns = tuple(patterns or SENSITIVE_PATTERNS)

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        for pattern in self.patterns:
            message = pattern.sub("[REDACTED]", message)
        record.msg = message
        record.args = ()
        return True


def install_logging_filters() -> None:
    redact_filter = RedactPIIFilter()
    for logger_name in ("uvicorn.access", "uvicorn.error", "uvicorn"):
        logger = logging.getLogger(logger_name)
        logger.addFilter(redact_filter)
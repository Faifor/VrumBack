from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, Integer, String, func, text

from modules.connection_to_db.database import Base


class EmailVerificationRequest(Base):
    __tablename__ = "email_verification_requests"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, index=True)
    code = Column(String, nullable=False)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expires_at = Column(DateTime(timezone=True), nullable=False)
    attempts = Column(Integer, nullable=False, default=0, server_default="0")
    locked_until = Column(DateTime(timezone=True), nullable=True)
    is_used = Column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )

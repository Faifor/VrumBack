from sqlalchemy import BigInteger, Boolean, Column, DateTime, Enum, Integer, Numeric, String, text
from sqlalchemy.orm import relationship

from modules.connection_to_db.database import Base
from .types import DocumentStatusEnum


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    full_name = Column(String, nullable=True)
    inn = Column(String, nullable=True)
    registration_address = Column(String, nullable=True)
    residential_address = Column(String, nullable=True)
    passport = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    bank_account = Column(String, nullable=True)
    failed_login_attempts = Column(Integer, nullable=False, default=0, server_default="0")
    last_failed_login_at = Column(DateTime(timezone=True), nullable=True)

    status = Column(
        Enum(DocumentStatusEnum, name="document_status_enum", native_enum=False),
        nullable=False,
        default=DocumentStatusEnum.DRAFT,
        server_default=DocumentStatusEnum.DRAFT.value,
    )
    rejection_reason = Column(String, nullable=True)

    role = Column(String, nullable=False, default="user")

    autopay_enabled = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    autopay_payment_method_id = Column(String, nullable=True)

    documents = relationship(
        "UserDocument",
        back_populates="user",
        uselist=True,
        cascade="all, delete-orphan",
        lazy="joined",
    )

    password_reset_requests = relationship(
        "PasswordResetRequest",
        back_populates="user",
        uselist=True,
        cascade="all, delete-orphan",
    )

    orders = relationship("Order", back_populates="user", uselist=True, cascade="all, delete-orphan")

    payments = relationship("Payment", back_populates="user", uselist=True, cascade="all, delete-orphan")
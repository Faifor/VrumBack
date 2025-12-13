from sqlalchemy import Column, Integer, String, Enum
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

    status = Column(
        Enum(DocumentStatusEnum, name="document_status_enum", native_enum=False),
        nullable=False,
        default=DocumentStatusEnum.DRAFT,
        server_default=DocumentStatusEnum.DRAFT.value,
    )
    rejection_reason = Column(String, nullable=True)

    role = Column(String, nullable=False, default="user")

    document = relationship(
        "UserDocument",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="joined",
    )

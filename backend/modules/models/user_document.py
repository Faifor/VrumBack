from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from modules.connection_to_db.database import Base
from .types import DocumentStatusEnum


class UserDocument(Base):
    __tablename__ = "user_documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    full_name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    passport = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    bank_account = Column(String, nullable=True)

    contract_number = Column(String, nullable=True)
    bike_serial = Column(String, nullable=True)
    akb1_serial = Column(String, nullable=True)
    akb2_serial = Column(String, nullable=True)
    akb3_serial = Column(String, nullable=True)
    amount = Column(String, nullable=True)
    amount_text = Column(String, nullable=True)
    weeks_count = Column(Integer, nullable=True)
    filled_date = Column(String, nullable=True)
    end_date = Column(String, nullable=True)

    status = Column(
        Enum(DocumentStatusEnum, name="document_status_enum", native_enum=False),
        default=DocumentStatusEnum.DRAFT,
        nullable=False,
    )

    rejection_reason = Column(String, nullable=True)
    contract_text = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="document")

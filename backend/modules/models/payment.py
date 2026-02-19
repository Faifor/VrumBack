from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.orm import relationship

from modules.connection_to_db.database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="RUB", server_default="RUB")
    status = Column(String(32), nullable=False, default="pending", server_default="pending", index=True)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="orders")
    payments = relationship(
        "Payment",
        back_populates="order",
        uselist=True,
        cascade="all, delete-orphan",
        order_by="Payment.created_at.desc()",
    )


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    yookassa_payment_id = Column(String(64), nullable=True, unique=True, index=True)
    status = Column(String(32), nullable=False, default="pending", server_default="pending", index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="RUB", server_default="RUB")
    confirmation_url = Column(Text, nullable=True)
    payment_method_id = Column(String(64), nullable=True)
    save_payment_method = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    is_autopay = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    raw_payload = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    order = relationship("Order", back_populates="payments")
    user = relationship("User", back_populates="payments")


class ContractPayment(Base):
    __tablename__ = "contract_payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("user_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    payment_number = Column(Integer, nullable=False)
    due_date = Column(Date, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(32), nullable=False, default="pending", server_default="pending", index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="SET NULL"), nullable=True)
    payment_id = Column(Integer, ForeignKey("payments.id", ondelete="SET NULL"), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")
    document = relationship("UserDocument")
    order = relationship("Order")
    payment = relationship("Payment")
from datetime import datetime

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from modules.connection_to_db.database import Base


class ReturnAct(Base):
    __tablename__ = "return_acts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("user_documents.id", ondelete="CASCADE"), nullable=False, index=True)

    return_act_number = Column(String(128), nullable=False, unique=True, index=True)
    contract_number = Column(String, nullable=False)
    rent_end_date = Column(Date, nullable=False)
    filled_date = Column(Date, nullable=False)

    bike_serial = Column(String, nullable=False)
    akb1_serial = Column(String, nullable=True)
    akb2_serial = Column(String, nullable=True)

    is_fix_bike = Column(Boolean, nullable=False, default=True)
    is_fix_akb_1 = Column(Boolean, nullable=False, default=True)
    is_fix_akb_2 = Column(Boolean, nullable=False, default=True)

    damage_description = Column(Text, nullable=True)
    damage_amount = Column(Integer, nullable=False, default=0)
    debt_term_days = Column(Integer, nullable=False, default=0)
    debt_due_date = Column(Date, nullable=False)

    damage_schedule_payment_id = Column(
        Integer,
        ForeignKey("contract_payments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")
    document = relationship("UserDocument")
    damage_schedule_payment = relationship("ContractPayment")
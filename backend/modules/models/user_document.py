from datetime import date, timedelta

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from modules.connection_to_db.database import Base


class UserDocument(Base):
    __tablename__ = "user_documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    contract_number = Column(String, nullable=True)
    bike_serial = Column(String, nullable=True)
    akb1_serial = Column(String, nullable=True)
    akb2_serial = Column(String, nullable=True)
    akb3_serial = Column(String, nullable=True)
    amount = Column(String, nullable=True)
    amount_text = Column(String, nullable=True)
    weeks_count = Column(Integer, nullable=True)
    filled_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    active = Column(Boolean, nullable=False, default=False, server_default="0")

    contract_text = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="documents")

    def refresh_dates_and_status(self) -> bool:
        """Calculate ``end_date`` and ``active`` flags based on stored dates.

        Returns ``True`` when either value has changed, so callers can decide
        whether the object needs to be persisted.
        """

        changed = False

        if self.filled_date and self.weeks_count is not None:
            new_end_date = self.filled_date + timedelta(weeks=self.weeks_count)
            if self.end_date != new_end_date:
                self.end_date = new_end_date
                changed = True
        elif self.end_date is not None:
            self.end_date = None
            changed = True

        today = date.today()
        new_active = bool(
            self.filled_date
            and self.end_date
            and self.filled_date <= today <= self.end_date
        )
        if self.active is None or self.active != new_active:
            self.active = new_active
            changed = True

        return changed

from datetime import date, timedelta

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import Session, relationship

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
    signed = Column(Boolean, nullable=False, default=False, server_default="0")

    contract_text = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="documents")

    def refresh_dates_and_status(self, update_active: bool = True) -> bool:
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

        if update_active:
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

    @classmethod
    def refresh_user_documents_status(
        cls, db: Session, user_id: int
    ) -> list["UserDocument"]:
        docs = (
            db.query(cls)
            .filter(cls.user_id == user_id)
            .order_by(cls.created_at.desc(), cls.id.desc())
            .all()
        )

        today = date.today()
        changed = False
        for doc in docs:
            if doc.refresh_dates_and_status(update_active=False):
                changed = True

        active_set = False
        for doc in docs:
            in_range = bool(
                doc.filled_date
                and doc.end_date
                and doc.filled_date <= today <= doc.end_date
            )
            new_active = in_range and not active_set
            if new_active:
                active_set = True
            if doc.active != new_active:
                doc.active = new_active
                changed = True

        if changed:
            db.commit()
            for doc in docs:
                db.refresh(doc)

        return docs

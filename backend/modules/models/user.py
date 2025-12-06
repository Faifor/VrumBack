from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from modules.connection_to_db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)

    role = Column(String, nullable=False, default="user")

    document = relationship(
        "UserDocument",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="joined",
    )

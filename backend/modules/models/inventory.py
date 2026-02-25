from sqlalchemy import Column, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from modules.connection_to_db.database import Base


class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    address = Column(Text, nullable=False)

    bikes = relationship("Bike", back_populates="location", uselist=True)
    batteries = relationship("Battery", back_populates="location", uselist=True)


class Bike(Base):
    __tablename__ = "bikes"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(String, nullable=False, unique=True, index=True)
    vin = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="free", server_default="free")
    purchase_date = Column(Date, nullable=True)
    last_service_date = Column(Date, nullable=True)
    next_service_date = Column(Date, nullable=True)
    location_id = Column(Integer, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)

    location = relationship("Location", back_populates="bikes")


class Battery(Base):
    __tablename__ = "batteries"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    voltage = Column(Integer, nullable=True)
    capacity = Column(Integer, nullable=True)
    status = Column(String, nullable=False, default="free", server_default="free")
    purchase_date = Column(Date, nullable=True)
    location_id = Column(Integer, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)

    location = relationship("Location", back_populates="batteries")
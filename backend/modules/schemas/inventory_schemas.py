from datetime import date
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class AssetStatus(str, Enum):
    RENTED = "rented"
    FREE = "free"
    REPAIR = "repair"
    DECOMMISSIONED = "decommissioned"


class ActiveContractInfo(BaseModel):
    contract_number: str | None = None
    user_full_name: str | None = None
    rental_start: date | None = None
    rental_end: date | None = None


class LocationBase(BaseModel):
    name: str
    address: str


class LocationCreate(LocationBase):
    pass


class LocationUpdate(BaseModel):
    name: str | None = None
    address: str | None = None


class LocationRead(LocationBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class BikeBase(BaseModel):
    number: str
    vin: str
    name: str
    description: str | None = None
    status: AssetStatus = AssetStatus.FREE
    purchase_date: date | None = None
    last_service_date: date | None = None
    next_service_date: date | None = None
    type_id: int | None = None
    location_id: int | None = None


class BikeCreate(BikeBase):
    pass


class BikeUpdate(BaseModel):
    number: str | None = None
    vin: str | None = None
    name: str | None = None
    description: str | None = None
    status: AssetStatus | None = None
    purchase_date: date | None = None
    last_service_date: date | None = None
    next_service_date: date | None = None
    type_id: int | None = None
    location_id: int | None = Field(default=None)


class BikeRead(BikeBase):
    id: int
    location: LocationRead | None = None
    active_contract: ActiveContractInfo | None = None

    model_config = ConfigDict(from_attributes=True)


class BatteryBase(BaseModel):
    number: str
    name: str
    description: str | None = None
    voltage: int | None = None
    capacity: int | None = None
    status: AssetStatus = AssetStatus.FREE
    purchase_date: date | None = None
    location_id: int | None = None


class BatteryCreate(BatteryBase):
    pass


class BatteryUpdate(BaseModel):
    number: str | None = None
    name: str | None = None
    description: str | None = None
    voltage: int | None = None
    capacity: int | None = None
    status: AssetStatus | None = None
    purchase_date: date | None = None
    location_id: int | None = Field(default=None)


class BatteryRead(BatteryBase):
    id: int
    location: LocationRead | None = None
    active_contract: ActiveContractInfo | None = None

    model_config = ConfigDict(from_attributes=True)


class BikePricingBase(BaseModel):
    type_id: int
    name_type: str
    min_weeks_count: int = Field(ge=1)
    max_weeks_count: int = Field(ge=1)
    amount_weeks: int = Field(ge=0)


class BikePricingCreate(BikePricingBase):
    pass


class BikePricingUpdate(BaseModel):
    type_id: int | None = None
    name_type: str | None = None
    min_weeks_count: int | None = Field(default=None, ge=1)
    max_weeks_count: int | None = Field(default=None, ge=1)
    amount_weeks: int | None = Field(default=None, ge=0)


class BikePricingRead(BikePricingBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
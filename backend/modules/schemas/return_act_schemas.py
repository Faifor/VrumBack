from datetime import date

from pydantic import BaseModel, Field


class ReturnActCreateRequest(BaseModel):
    is_fix_bike: bool
    is_fix_AKB_1: bool | None = None
    is_fix_AKB_2: bool | None = None
    damage_description: str | None = None
    damage_amount: int = Field(ge=0)
    debt_term_days: int = Field(ge=0)


class ReturnActRead(BaseModel):
    id: int
    return_act_number: str
    contract_number: str
    rent_end_date: date
    filled_date: date
    bike_serial: str
    akb1_serial: str | None
    akb2_serial: str | None
    is_fix_bike: bool
    is_fix_AKB_1: bool
    is_fix_AKB_2: bool
    damage_description: str | None
    damage_amount: int
    debt_term_days: int
    debt_due_date: date
    damage_schedule_payment_id: int | None

    model_config = {"from_attributes": True}

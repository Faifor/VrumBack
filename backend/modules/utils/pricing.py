from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from modules.models.inventory import Bike, BikePricing


def resolve_weekly_amount(db: Session, bike_serial: str | None, weeks_count: int | None) -> Decimal:
    if not bike_serial or not weeks_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Для расчета цены нужны bike_serial и weeks_count",
        )

    bike = (
        db.query(Bike)
        .filter((Bike.number == bike_serial) | (Bike.vin == bike_serial))
        .first()
    )
    if not bike:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Велосипед из договора не найден в инвентаре",
        )

    if bike.type_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Для выбранного велосипеда не указан type_id",
        )

    pricing = (
        db.query(BikePricing)
        .filter(
            BikePricing.type_id == bike.type_id,
            BikePricing.min_weeks_count <= weeks_count,
            BikePricing.max_weeks_count >= weeks_count,
        )
        .order_by(BikePricing.min_weeks_count.asc())
        .first()
    )

    if not pricing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не найдено ценообразование для типа велосипеда и срока аренды",
        )

    return Decimal(pricing.amount_weeks)


def calc_total_amount(weekly_amount: Decimal, weeks_count: int) -> Decimal:
    return weekly_amount * Decimal(weeks_count)
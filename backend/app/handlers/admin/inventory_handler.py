from datetime import date

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from modules.connection_to_db.database import get_session
from modules.models.inventory import Battery, Bike, BikePricing, Location
from modules.models.user_document import UserDocument
from modules.models.user import User
from modules.schemas.inventory_schemas import (
    ActiveContractInfo,
    AssetStatus,
    BatteryCreate,
    BatteryRead,
    BatteryStatusUpdate,
    BatteryUpdate,
    BikeCreate,
    BikePricingCreate,
    BikePricingRead,
    BikePricingUpdate,
    BikeRead,
    BikeStatusUpdate,
    BikeUpdate,
    LocationCreate,
    LocationRead,
    LocationUpdate,
)
from modules.utils.admin_utils import get_current_admin
from modules.utils.document_security import (
    decrypt_document_fields,
    decrypt_user_fields,
    get_sensitive_data_cipher,
)


class InventoryHandler:
    def __init__(
        self,
        db: Session = Depends(get_session),
        admin: User = Depends(get_current_admin),
    ):
        self.db = db
        self.admin = admin
        self.cipher = get_sensitive_data_cipher()

    def list_locations(self) -> list[Location]:
        return self.db.query(Location).order_by(Location.id.asc()).all()

    def get_location(self, location_id: int) -> Location:
        location = self.db.query(Location).filter(Location.id == location_id).first()
        if not location:
            raise HTTPException(status_code=404, detail="Локация не найдена")
        return location

    def create_location(self, body: LocationCreate) -> Location:
        location = Location(**body.model_dump())
        self.db.add(location)
        self.db.commit()
        self.db.refresh(location)
        return location

    def update_location(self, location_id: int, body: LocationUpdate) -> Location:
        location = self.get_location(location_id)
        for field, value in body.model_dump(exclude_unset=True).items():
            setattr(location, field, value)
        self.db.commit()
        self.db.refresh(location)
        return location

    def delete_location(self, location_id: int) -> None:
        location = self.get_location(location_id)
        self.db.delete(location)
        self.db.commit()

    def list_bikes(self, status_filter: AssetStatus | None = None) -> list[BikeRead]:
        query = self.db.query(Bike)
        if status_filter:
            query = query.filter(Bike.status == status_filter.value)
        bikes = query.order_by(Bike.id.asc()).all()
        bike_contracts, _ = self._get_active_contract_maps()

        return [self._to_bike_read(bike, bike_contracts.get(bike.vin)) for bike in bikes]

    def get_bike(self, bike_id: int) -> BikeRead:
        bike = self.db.query(Bike).filter(Bike.id == bike_id).first()
        if not bike:
            raise HTTPException(status_code=404, detail="Велосипед не найден")
        bike_contracts, _ = self._get_active_contract_maps()
        return self._to_bike_read(bike, bike_contracts.get(bike.vin))

    def create_bike(self, body: BikeCreate) -> BikeRead:
        self._ensure_location_exists(body.location_id)
        self._ensure_unique_bike_fields(number=body.number, vin=body.vin)
        bike = Bike(**body.model_dump())
        bike.status = body.status.value
        self.db.add(bike)
        self.db.commit()
        self.db.refresh(bike)
        return self._to_bike_read(bike, None)

    def update_bike(self, bike_id: int, body: BikeUpdate) -> BikeRead:
        bike = self.db.query(Bike).filter(Bike.id == bike_id).first()
        if not bike:
            raise HTTPException(status_code=404, detail="Велосипед не найден")

        payload = body.model_dump(exclude_unset=True)
        if "location_id" in payload:
            self._ensure_location_exists(payload["location_id"])
        if "status" in payload and payload["status"] is not None:
            payload["status"] = payload["status"].value
        if "number" in payload or "vin" in payload:
            self._ensure_unique_bike_fields(
                number=payload.get("number", bike.number),
                vin=payload.get("vin", bike.vin),
                exclude_bike_id=bike.id,
            )

        for field, value in payload.items():
            setattr(bike, field, value)

        self.db.commit()
        self.db.refresh(bike)
        bike_contracts, _ = self._get_active_contract_maps()
        return self._to_bike_read(bike, bike_contracts.get(bike.vin))

    def update_bike_status(self, bike_id: int, body: BikeStatusUpdate) -> BikeRead:
        bike = self.db.query(Bike).filter(Bike.id == bike_id).first()
        if not bike:
            raise HTTPException(status_code=404, detail="Велосипед не найден")

        bike.status = body.status.value
        self.db.commit()
        self.db.refresh(bike)
        bike_contracts, _ = self._get_active_contract_maps()
        return self._to_bike_read(bike, bike_contracts.get(bike.vin))

    def delete_bike(self, bike_id: int) -> None:
        bike = self.db.query(Bike).filter(Bike.id == bike_id).first()
        if not bike:
            raise HTTPException(status_code=404, detail="Велосипед не найден")
        self.db.delete(bike)
        self.db.commit()

    def list_batteries(self, status_filter: AssetStatus | None = None) -> list[BatteryRead]:
        query = self.db.query(Battery)
        if status_filter:
            query = query.filter(Battery.status == status_filter.value)
        batteries = query.order_by(Battery.id.asc()).all()
        _, battery_contracts = self._get_active_contract_maps()
        return [
            self._to_battery_read(battery, battery_contracts.get(battery.number))
            for battery in batteries
        ]

    def get_battery(self, battery_id: int) -> BatteryRead:
        battery = self.db.query(Battery).filter(Battery.id == battery_id).first()
        if not battery:
            raise HTTPException(status_code=404, detail="АКБ не найден")
        _, battery_contracts = self._get_active_contract_maps()
        return self._to_battery_read(battery, battery_contracts.get(battery.number))

    def create_battery(self, body: BatteryCreate) -> BatteryRead:
        self._ensure_location_exists(body.location_id)
        self._ensure_unique_battery_number(number=body.number)
        battery = Battery(**body.model_dump())
        battery.status = body.status.value
        self.db.add(battery)
        self.db.commit()
        self.db.refresh(battery)
        return self._to_battery_read(battery, None)

    def update_battery(self, battery_id: int, body: BatteryUpdate) -> BatteryRead:
        battery = self.db.query(Battery).filter(Battery.id == battery_id).first()
        if not battery:
            raise HTTPException(status_code=404, detail="АКБ не найден")

        payload = body.model_dump(exclude_unset=True)
        if "location_id" in payload:
            self._ensure_location_exists(payload["location_id"])
        if "status" in payload and payload["status"] is not None:
            payload["status"] = payload["status"].value
        if "number" in payload:
            self._ensure_unique_battery_number(
                number=payload["number"],
                exclude_battery_id=battery.id,
            )

        for field, value in payload.items():
            setattr(battery, field, value)

        self.db.commit()
        self.db.refresh(battery)
        _, battery_contracts = self._get_active_contract_maps()
        return self._to_battery_read(battery, battery_contracts.get(battery.number))

    def update_battery_status(
        self, battery_id: int, body: BatteryStatusUpdate
    ) -> BatteryRead:
        battery = self.db.query(Battery).filter(Battery.id == battery_id).first()
        if not battery:
            raise HTTPException(status_code=404, detail="АКБ не найден")

        battery.status = body.status.value
        self.db.commit()
        self.db.refresh(battery)
        _, battery_contracts = self._get_active_contract_maps()
        return self._to_battery_read(battery, battery_contracts.get(battery.number))

    def delete_battery(self, battery_id: int) -> None:
        battery = self.db.query(Battery).filter(Battery.id == battery_id).first()
        if not battery:
            raise HTTPException(status_code=404, detail="АКБ не найден")
        self.db.delete(battery)
        self.db.commit()

    def list_bike_pricing(self, type_id: int | None = None) -> list[BikePricing]:
        query = self.db.query(BikePricing)
        if type_id is not None:
            query = query.filter(BikePricing.type_id == type_id)
        return query.order_by(
            BikePricing.type_id.asc(),
            BikePricing.min_weeks_count.asc(),
            BikePricing.id.asc(),
        ).all()

    def get_bike_pricing(self, pricing_id: int) -> BikePricing:
        pricing = self.db.query(BikePricing).filter(BikePricing.id == pricing_id).first()
        if not pricing:
            raise HTTPException(status_code=404, detail="Тариф ценообразования не найден")
        return pricing

    def create_bike_pricing(self, body: BikePricingCreate) -> BikePricingRead:
        self._ensure_pricing_weeks_range(body.min_weeks_count, body.max_weeks_count)
        self._ensure_pricing_range_not_overlapping(
            type_id=body.type_id,
            min_weeks_count=body.min_weeks_count,
            max_weeks_count=body.max_weeks_count,
        )
        pricing = BikePricing(**body.model_dump())
        self.db.add(pricing)
        self.db.commit()
        self.db.refresh(pricing)
        return BikePricingRead.model_validate(pricing)

    def update_bike_pricing(self, pricing_id: int, body: BikePricingUpdate) -> BikePricingRead:
        pricing = self.get_bike_pricing(pricing_id)
        payload = body.model_dump(exclude_unset=True)

        type_id = payload.get("type_id", pricing.type_id)
        min_weeks = payload.get("min_weeks_count", pricing.min_weeks_count)
        max_weeks = payload.get("max_weeks_count", pricing.max_weeks_count)
        self._ensure_pricing_weeks_range(min_weeks, max_weeks)
        self._ensure_pricing_range_not_overlapping(
            type_id=type_id,
            min_weeks_count=min_weeks,
            max_weeks_count=max_weeks,
            exclude_pricing_id=pricing.id,
        )

        for field, value in payload.items():
            setattr(pricing, field, value)

        self.db.commit()
        self.db.refresh(pricing)
        return BikePricingRead.model_validate(pricing)

    def delete_bike_pricing(self, pricing_id: int) -> None:
        pricing = self.get_bike_pricing(pricing_id)
        self.db.delete(pricing)
        self.db.commit()

    def _ensure_pricing_weeks_range(self, min_weeks_count: int, max_weeks_count: int) -> None:
        if min_weeks_count <= 0 or max_weeks_count <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="min_weeks_count и max_weeks_count должны быть положительными числами",
            )
        if min_weeks_count >= max_weeks_count:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="min_weeks_count должен быть строго меньше max_weeks_count",
            )

    def _ensure_unique_bike_fields(
        self,
        number: str,
        vin: str,
        exclude_bike_id: int | None = None,
    ) -> None:
        number_query = self.db.query(Bike).filter(Bike.number == number)
        vin_query = self.db.query(Bike).filter(Bike.vin == vin)
        if exclude_bike_id is not None:
            number_query = number_query.filter(Bike.id != exclude_bike_id)
            vin_query = vin_query.filter(Bike.id != exclude_bike_id)

        if number_query.first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Велосипед с таким number уже существует",
            )
        if vin_query.first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Велосипед с таким vin уже существует",
            )

    def _ensure_unique_battery_number(
        self,
        number: str,
        exclude_battery_id: int | None = None,
    ) -> None:
        query = self.db.query(Battery).filter(Battery.number == number)
        if exclude_battery_id is not None:
            query = query.filter(Battery.id != exclude_battery_id)
        if query.first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="АКБ с таким number уже существует",
            )

    def _ensure_pricing_range_not_overlapping(
        self,
        type_id: int,
        min_weeks_count: int,
        max_weeks_count: int,
        exclude_pricing_id: int | None = None,
    ) -> None:
        query = self.db.query(BikePricing).filter(BikePricing.type_id == type_id)
        if exclude_pricing_id is not None:
            query = query.filter(BikePricing.id != exclude_pricing_id)

        existing_ranges = query.all()
        for item in existing_ranges:
            ranges_intersect = not (
                max_weeks_count < item.min_weeks_count
                or min_weeks_count > item.max_weeks_count
            )
            if ranges_intersect:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Для одного type_id диапазоны min_weeks_count/max_weeks_count "
                        "не должны пересекаться"
                    ),
                )

    def _ensure_location_exists(self, location_id: int | None) -> None:
        if location_id is None:
            return
        location = self.db.query(Location).filter(Location.id == location_id).first()
        if not location:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Указанная локация не существует",
            )

    def _get_active_contract_maps(
        self,
    ) -> tuple[dict[str, ActiveContractInfo], dict[str, ActiveContractInfo]]:
        today = date.today()
        docs = (
            self.db.query(UserDocument)
            .join(User)
            .filter(
                UserDocument.filled_date.is_not(None),
                UserDocument.end_date.is_not(None),
                UserDocument.filled_date <= today,
                UserDocument.end_date >= today,
            )
            .order_by(UserDocument.created_at.desc(), UserDocument.id.desc())
            .all()
        )

        bike_contracts: dict[str, ActiveContractInfo] = {}
        battery_contracts: dict[str, ActiveContractInfo] = {}

        for doc in docs:
            decrypted_doc = decrypt_document_fields(doc, self.cipher)
            decrypted_user = decrypt_user_fields(doc.user, self.cipher)

            contract_info = ActiveContractInfo(
                contract_number=decrypted_doc.get("contract_number"),
                user_full_name=decrypted_user.get("full_name") or doc.user.email,
                rental_start=doc.filled_date,
                rental_end=doc.end_date,
            )

            bike_serial = decrypted_doc.get("bike_serial")
            if bike_serial and bike_serial not in bike_contracts:
                bike_contracts[bike_serial] = contract_info

            for field in ("akb1_serial", "akb2_serial", "akb3_serial"):
                akb_serial = decrypted_doc.get(field)
                if akb_serial and akb_serial not in battery_contracts:
                    battery_contracts[akb_serial] = contract_info

        return bike_contracts, battery_contracts

    def _to_bike_read(self, bike: Bike, contract: ActiveContractInfo | None) -> BikeRead:
        return BikeRead(
            id=bike.id,
            number=bike.number,
            vin=bike.vin,
            name=bike.name,
            description=bike.description,
            status=AssetStatus(bike.status),
            purchase_date=bike.purchase_date,
            last_service_date=bike.last_service_date,
            next_service_date=bike.next_service_date,
            type_id=bike.type_id,
            location_id=bike.location_id,
            location=LocationRead.model_validate(bike.location) if bike.location else None,
            active_contract=contract,
        )

    def _to_battery_read(
        self, battery: Battery, contract: ActiveContractInfo | None
    ) -> BatteryRead:
        return BatteryRead(
            id=battery.id,
            number=battery.number,
            name=battery.name,
            description=battery.description,
            voltage=battery.voltage,
            capacity=battery.capacity,
            status=AssetStatus(battery.status),
            purchase_date=battery.purchase_date,
            location_id=battery.location_id,
            location=LocationRead.model_validate(battery.location)
            if battery.location
            else None,
            active_contract=contract,
        )

from fastapi import APIRouter, Depends, Query

from app.handlers.admin.inventory_handler import InventoryHandler
from modules.schemas.inventory_schemas import (
    AssetStatus,
    BatteryCreate,
    BikePricingCreate,
    BikePricingRead,
    BikePricingUpdate,
    BatteryRead,
    BatteryUpdate,
    BikeCreate,
    BikeRead,
    BikeUpdate,
    LocationCreate,
    LocationRead,
    LocationUpdate,
)

router = APIRouter()


@router.get("/admin/locations", response_model=list[LocationRead])
def admin_list_locations(handler: InventoryHandler = Depends(InventoryHandler)):
    return handler.list_locations()


@router.post("/admin/locations", response_model=LocationRead)
def admin_create_location(
    body: LocationCreate,
    handler: InventoryHandler = Depends(InventoryHandler),
):
    return handler.create_location(body)


@router.get("/admin/locations/{location_id}", response_model=LocationRead)
def admin_get_location(
    location_id: int,
    handler: InventoryHandler = Depends(InventoryHandler),
):
    return handler.get_location(location_id)


@router.put("/admin/locations/{location_id}", response_model=LocationRead)
def admin_update_location(
    location_id: int,
    body: LocationUpdate,
    handler: InventoryHandler = Depends(InventoryHandler),
):
    return handler.update_location(location_id, body)


@router.get("/admin/bikes", response_model=list[BikeRead])
def admin_list_bikes(
    status_filter: AssetStatus | None = Query(default=None, alias="status"),
    handler: InventoryHandler = Depends(InventoryHandler),
):
    return handler.list_bikes(status_filter)


@router.post("/admin/bikes", response_model=BikeRead)
def admin_create_bike(
    body: BikeCreate,
    handler: InventoryHandler = Depends(InventoryHandler),
):
    return handler.create_bike(body)


@router.get("/admin/bikes/{bike_id}", response_model=BikeRead)
def admin_get_bike(
    bike_id: int,
    handler: InventoryHandler = Depends(InventoryHandler),
):
    return handler.get_bike(bike_id)


@router.put("/admin/bikes/{bike_id}", response_model=BikeRead)
def admin_update_bike(
    bike_id: int,
    body: BikeUpdate,
    handler: InventoryHandler = Depends(InventoryHandler),
):
    return handler.update_bike(bike_id, body)


@router.get("/admin/batteries", response_model=list[BatteryRead])
def admin_list_batteries(
    status_filter: AssetStatus | None = Query(default=None, alias="status"),
    handler: InventoryHandler = Depends(InventoryHandler),
):
    return handler.list_batteries(status_filter)


@router.post("/admin/batteries", response_model=BatteryRead)
def admin_create_battery(
    body: BatteryCreate,
    handler: InventoryHandler = Depends(InventoryHandler),
):
    return handler.create_battery(body)


@router.get("/admin/batteries/{battery_id}", response_model=BatteryRead)
def admin_get_battery(
    battery_id: int,
    handler: InventoryHandler = Depends(InventoryHandler),
):
    return handler.get_battery(battery_id)


@router.put("/admin/batteries/{battery_id}", response_model=BatteryRead)
def admin_update_battery(
    battery_id: int,
    body: BatteryUpdate,
    handler: InventoryHandler = Depends(InventoryHandler),
):
    return handler.update_battery(battery_id, body)


@router.get("/admin/bike-pricing", response_model=list[BikePricingRead])
def admin_list_bike_pricing(
    type_id: int | None = Query(default=None),
    handler: InventoryHandler = Depends(InventoryHandler),
):
    items = handler.list_bike_pricing(type_id=type_id)
    return [BikePricingRead.model_validate(item) for item in items]


@router.post("/admin/bike-pricing", response_model=BikePricingRead)
def admin_create_bike_pricing(
    body: BikePricingCreate,
    handler: InventoryHandler = Depends(InventoryHandler),
):
    return handler.create_bike_pricing(body)


@router.get("/admin/bike-pricing/{pricing_id}", response_model=BikePricingRead)
def admin_get_bike_pricing(
    pricing_id: int,
    handler: InventoryHandler = Depends(InventoryHandler),
):
    return BikePricingRead.model_validate(handler.get_bike_pricing(pricing_id))


@router.put("/admin/bike-pricing/{pricing_id}", response_model=BikePricingRead)
def admin_update_bike_pricing(
    pricing_id: int,
    body: BikePricingUpdate,
    handler: InventoryHandler = Depends(InventoryHandler),
):
    return handler.update_bike_pricing(pricing_id, body)
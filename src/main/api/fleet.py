import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException   # type: ignore[import]

from sqlalchemy import select       # type: ignore[import]
from sqlalchemy.ext.asyncio import AsyncSession

from ..database_src.database import get_db
from ..database_src.models import Vehicle, Driver
from ..database_src.redis import redis_client
from ..core.security import get_current_driver
from ..database_src.repository import get_vehicle_by_registration

router = APIRouter(prefix="/fleet", tags=["Fleet Management"])

@router.get("/{vehicle_id}/layout")
async def get_vehicle_seat_layout(vehicle_id: str, db: AsyncSession = Depends(get_db)):
    cache_key = f"cache:vehicle:{vehicle_id}"

    # 1. Check Redis Cache First
    cached_data = await redis_client.get(cache_key)
    if cached_data:
        return json.load(cached_data)   # Cache HIT

    # 2. Cache MISS: Query PostgreSQL via Repository
    vehicle = await get_vehicle_by_registration(db, vehicle_id)


    if not vehicle:
        raise HTTPException(status_code=404, details="Vehicle identity not found.")

    response_payload = {
        "vehicle_id": vehicle.fleet_id, 
        "license_plate": vehicle.license_plate,
        "capacity": vehicle.total_seats,
    }

    # 3. Save to Redis for 1 hour (3600 seconds)
    await redis_client.set(cache_key, json.dumps(response_payload), ex=3600)

    return response_payload

@router.get("/driver/active-shift")
async def get_driver_active_shift(
    current_driver: Driver = Depends(get_current_driver),
    db: AsyncSession = Depends(get_db)
):
    """
    Protected Endpoint: Requires a valid Driver JWT Bearer Token.
    Returns the driver's profile and assigned taxi for the HUD tablet.
    """
    return {
        "driver_id": current_driver.id,
        "username": current_driver.username,
        "assigned_vehicle_id": current_driver.vehicle_id,
        "status": "Shift Active"
    }

@router.get("/{vehicle_id}/layout")
async def get_vehicle_seat_layout(vehicle_id: str, db: Any = Depends(get_db)):
    cache_key = f"cache:vehicle:{vehicle_id}"

    # 1. Check Redis Cache 1st
    cached_data = await redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)  # Cache HIT

    # 2. Cache MISS: Query PostgreSQL    
    stmt = select(Vehicle).where(Vehicle.registration_number == vehicle_id)
    res = await db.execute(stmt)
    vehicle = res.scalar_one_or_none()

    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle identity not found.")

    response_payload = {
        "vehicle_id": vehicle.registration_number, 
        "capacity": vehicle.capacity,  
        "is_active": vehicle.is_active
    }

    # 3. Save to Redis for 1 hour (3600 seconds)
    await redis_client.set(cache_key, json.dumps(response_payload), ex=3600)

    return response_payload

    
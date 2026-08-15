from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from ..database_src.database import get_async_session
from ..database_src.models import Vehicle

router = APIRouter(prefix="/fleet", tags=["Fleet Management"])

@router.get("/{vehicle_id}/layout")
async def get_vehicle_seat_layout(vehicle_id: str, session: AsyncSession = Depends(get_async_session)):
    stmt = select(Vehicle).where(Vehicle.registration_number == vehicle_id)
    res = await session.execute(stmt)
    vehicle = res.scalars().first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle identity not found.")

    return {
        "vehicle_id": vehicle.registration_number, 
        "capacity": vehicle.capacity, 
        "layout": vehicle.seat_layout, 
        "is_active": vehicle.is_active
    }
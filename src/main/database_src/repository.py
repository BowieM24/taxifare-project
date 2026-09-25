from decimal import Decimal
from typing import List, Oprional, Tuple

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Commuter, Vehicle, Transaction, Driver


# --------- COMMUTER PERSISTENCE ---------
async def get_or_create_commuter(db: AsyncSession, phone_number: str) -> Commuter:
    """ Fetches a commuter by phone number, or auto-provisions a new record."""
    stmt = select(Commuter).where(Commuter.phone_number == phone_number)
    result = await db.execute(stmt)
    commuter = result.scalar_one_or_none()

    if not commuter:
        commuter = Commuter(
            phone_number=phone_number,
            name="Passenger",
            wallet_balance=Decimal("0.00")

        )
        db.add(commuter)
        await db.commit()
        await db.refresh(commuter)

    return commuter


# ----- VEHICLE PERSISTENCE ------
async def get_vehicle_by_registration(db: AsyncSession, fleet_id: str) -> Optional[Vehicle]:
    """ Fetches a vehicle profile using parameterized lookup."""
    stmt select(Vehicle).where(Vehicle.fleet_id == fleet_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def get_or_create_vehicle(
    db: AsyncSession, 
    fleet_id: str,
    license_plate: str = "ND 351-6540",
    total_seats: int = 14
) -> Vehicle:
    """ Ensures a vehicle record exists before attaching forgiegn-key transactions."""
    vehicle = await get_vehicle_by_registration(db, fleet_id)
    if not vehicle:
        vehicle = Vehicle(
            fleet_id=fleet_id,
            license_plate=license_plate,
            total_seats=total_seats
        )
        db.add(vehicle)
        await db.commit()
        await db.refresh(vehicle)
    return vehicle


# --------- TRANSACTION PERSISTENCE -------
async def create_transaction(
    db: AsyncSession, 
    commuter_id: int, 
    vehicle_id: int, 
    seat_number: int, 
    amount: float, 
    payment_method: str, 
    status: str = "PEENDING"
) -> Transaction:
    new_tx = Transaction(
        commuter_id=commuter_id,
        vehicle_id=vehicle_id,
        amount=Decimal(str(amount)),
        seat_number=seat_number,
        payment_method=payment_method,
        status=status,
    )
    db.add(new_tx)
    await db.commit()
    await db.refresh(new_tx)
    return new_tx

async def update_transaction_status(
    db: AsyncSession, 
    transaction_id: int, 
    new_status: str
    ) -> Optional[Transaction]:
    """Updates transaction status (e.g., PENDING -> SUCCESS) when webhook fires."""
    stmt = (
        update(Transaction)
        .where(Transaction.id == transaction_id)
        .values(status=new_status)
        .returning(Transaction)
        )
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one_or_none()


async def get_recent_rides(
    db: AsyncSession, 
    commuter_id: int, 
    limit: int = 3
    ) -> List[Tuple[Transaction, Vehicle]]: 
    """Returns the last N rides joined with Vehicle info for USSD history."""
    stmt = (
        select(Transaction, Vehicle)
        .join(Vehicle, Transaction.vehicle_id == Vehicle.id)
        .where(Transaction.commuter_id == commuter_id)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
        )
    result = await db.execute(stmt)
    return list(result.all())
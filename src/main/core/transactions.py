from decimal import Decimal
import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.main.database_src.models import Commuter, Transaction


async def execute_wallet_deduction(db_session: AsyncSession, commuter_id: uuid.UUID, vehicle_id: uuid.UUID, amount: Decimal, seat_number: int, payment_method: str = "WALLET"):
    """ Executes a thread-safe wallet deduction using row-level locking."""
    # 1. Lock commuter row
    stmt = select(Commuter).where(Commuter.id == commuter_id).with_for_update()
    commuter = (await db_session.execute(stmt)).scalar_one_or_none()

    if not commuter:
        await db_session.rollback()
        raise HTTPException(status_code=404, detail="Commuter not found")

    if commuter.wallet_balance < amount:
        await db_session.rollback()
        raise HTTPException(status_code=400, detail="Insufficient funds")

    # 2. Process deduction and log transaction
    commuter.wallet_balance -= amount
    tx = Transaction(
        commuter_id=commuter.id,
        vehicle_id=vehicle_id,
        seat_number=seat_number,
        amount=amount,
        payment_status="COMPLETED",
        payment_method=payment_method
    )
    db_session.add(tx)
    await db_session.commit()
    # 3. Refresh to get the genratee primary key and timestamps
    await db_session.fresh(tx)
    return tx



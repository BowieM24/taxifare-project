import pytest
import pytest_asyncio

from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.main.database_src.models import Commuter, Vehicle, Transaction

@pytest_asyncio.fixture(scope="function")
async def seed_commuter_and_vehicle(test_db_session):
    """
    Fixture to insert a test commuter and vehicle for relational testing.
    """
    commuter = Commuter(
        phone_number="+27831234567",
        wallet_balance=Decimal("150.00")
    )
    vehicle = Vehicle(
        registration_number="bree-quantum-789",
        capacity=15,
        is_active=True
    )

    test_db_session.add_all([commuter, vehicle])
    await test_db_session.commit()
    await test_db_session.refresh(commuter)
    await test_db_session.refresh(vehicle)

    return commuter, vehicle

# ======================================================================
# 1. Commuter Model Tests
# ======================================================================

@pytest.mark.asyncio
async def test_create_retrieve_commuter(test_db_session):
    """
    Verify creating and fetching a commuter record works as expected.
    """
    commuter = Commuter(
        phone_number="+2771000000",
        wallet_balance=Decimal("50.50")
    )
    test_db_session.add(commuter)
    await test_db_session.commit()

    stmt = select(Commuter).where(Commuter.phone_number == "+2771000000")
    result = await test_db_session.execute(stmt)
    fetched_commuter = result.scalar_one_or_none()

    assert fetched_commuter.phone_number == "+27710000000"
    assert fetched_commuter.wallet_balance == Decimal("50.50")


@pytest.mark.asyncio
async def test_commuter_phone_uniqueness_constraint(test_db_session):
    """
    Ensure duplicate phone numbers raise an IntegrityError.
    """
    commuter1 = Commuter(phone_number="+27839998888", wallet_balance=Decimal("0.00"))
    commuter2 = Commuter(phone_number="+27839998888", wallet_balance=Decimal("10.00"))

    test_db_session.add(commuter1)
    await test_db_session.commit()

    test_db_session.add(commuter2)
    with pytest.raises(IntegrityError):
        await test_db_session.commit()


# ====================================================================================
# 2. Vehicle Model Tests
# ====================================================================================

@pytest.mark.asyncio
async def test_create_vehicle_record(test_db_session):
    """
    Verify creation and query of vehicle entity.
    """
    vehicle = Vehicle(
        registration_numbers="randburg-quantum-123",
        capacity=22,
        is_active=True
    )
    test_db_session.add(vehicle)
    await test_db_session.commit()

    stmt = select(Vehicle).where(Vehicle.registration_number == "randburg-quantum-123")
    res = await test_db_session.execute(stmt)
    fetched_vehicle = res.scalar_one_or_none()

    assert fetched_vehicle is not None
    assert fetched_vehicle.capacity == 22
    assert fetched_vehicle.is_active is True


# =============================================================================
# 3. Transaction Model & Relational Integrity Tests
# =============================================================================

@pytest.mark.asyncio
async def test_create_transaction_relational_mappting(test_db_session, seed_commuter_and_vehicle):
    """
    Verify transaction records associate correctly with Commuter and Vehicle.
    """
    commuter, vehicle = seed_commuter_and_vehicle

    transaction = Transaction(
        commuter_id=commuter.id,
        vehicle_id=vehicle.id,
        seat_number=4,
        fare_amount=Decimal("22.50"),
        status="COMPLETED"
    )
    test_db_session.add(transaction)
    await test_db_session.commit()
    await test_db_session.refresh(transaction)

    # Fetch transaction and check foreign keys
    stmt = select(Transaction).where(Transaction.id == transaction.id)
    res = await test_db_session.execute(stmt)
    fetched_tx = res.scalar_one_or_none()

    assert fetched_tx is not None
    assert fetched_tx.commuter_id == commuter.id
    assert fetched_tx.vehicle_id == vehicle.id
    assert fetched_tx.seat_number == 4
    assert fetched_tx.fare_amount == Decimal("22.50")


@pytest.mark.asyncio
async def test_transaction_numeric_precision(test_db_session, seed_commuter_and_vehicle):
    """
    Ensure fare amounts preserve exact Decimal currency values without floating-point drift.
    """
    commuter, vehicle = seed_commuter_and_vehicle

    tx = Transaction(
        commuter_id=commuter.id,
        vehicle_id=vehicle.id,
        seat_number=1,
        fare_amount=Decimal("17.80"),
        status="PENDING"
    )

    test_db_session.add(tx)
    await test_db_session.commit()

    stmt = select(Transaction).where(Transaction.id == tx.id)
    res = await test_db_session.execute(stmt)
    fetched_tx = res.scalar_one()

    assert isinstance(fetched_tx.fare_amount, Decimal)
    assert fetched_tx.fare_amount == Decimal("17.80")
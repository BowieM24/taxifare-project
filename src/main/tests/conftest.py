import pytest               # type: ignore[reportMissingImports]
import pytest_asyncio       # type: ignore[reportMissingImports]

from httpx import AsyncClient, ASGITransport        # type: ignore[reportMissingImports]
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker        # type: ignore[reportMissingImports]
from unittest.mock import AsyncMock, patch

from src.main.app import app
from src.main.database_src.database import Base, get_db

# In-memory or isolated test DB URI (or test Postgres instance)
TEST_DATABSE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """
    Creates the table in RAM once for the entire test session.
    """
    engine = create_async_engine(TEST_DATABSE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def test_db_session(test_engine):
    """
    Create a fresh databse session for a test and rolls it back after.
    Uses savepoints so test commits don't persist across tests.
    """
    async with test_engine.connect() as conn:
        # Start a root transaction
        transaction = await conn.begin()

        # Bind session to connection and force savepoints
        async_session = AsyncSession(bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False)

        yield async_session
        # Clean up and rollback root transaction(wipes data)
        await async_session.close()
        await transaction.rollback()

@pytest_asyncio.fixture
async def client(test_db_session):
    """Test client that overrides the database dependency..
    """
    async def _override_get_db():
        yield test_db_session

    app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
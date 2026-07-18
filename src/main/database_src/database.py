import os

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Database connection URL - Fallback to a local dev string if env vars aren't set
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+assyncpg://postgres:postgres@localhost:5432/taxifare"
)

# Initilize the Asynchronous Engine with tuned connection pool parameters
async_engine = create_async_engine(
    DATABASE_URL,
    echo=False,             # Set to True only during deep SQL debugging sessions
    pool_size=20,           # Maintain up to 20 persistant connections in the pool
    max_overflow=10,        # Allow up to 10 bursting connections beyond pool_size under high load
    pool_timeout=30,        # Seconds to wait before throwing a timeout error if pool is exhausted
    pool_recycle=1800,      # Recycle connections after 30 minutes to prevent stale/dropped sockets
    pool_pre_ping=True      # Run an internal health check ("PING") before handing a connection out
)

# Session factory for generating isolated transaction workloads
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False      # Prevents attributes from expiring after a commit (crucial for async)
)

# Declarative base class that our relational schemas will inherit from
Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI Dependency injection provider yielding scoped database sessions.
    Automatically closes or rolls back sessions when requests complete.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
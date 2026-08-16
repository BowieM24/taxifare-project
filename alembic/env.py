import asyncio
from logging.config import fileConfig

from sqlalchemy import pool                 # type: ignore[import]
from sqlalchemy.engine import Connection                        # type: ignore[import]
from sqlalchemy.ext.asyncio import async_engine_from_config     # type: ignore[import]

from alembic import context                 # type: ignore[import]

# 1. Import settings and Base metadata
from src.main.config import settings
from src.main.database_src.database import Base
# Import all models so Alembic can detect them
from src.main.database_src.models import Commuter, Vehicle, Transaction


config = context.config

# 2. Dynamically set the database URL from config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)


# Configure logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 3. Point target_metadata to SQLAlchemy Base
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations using an existing connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )

    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    """Run migrations using the async databse engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()



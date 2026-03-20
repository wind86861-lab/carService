from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from bot.config import DATABASE_URL

engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=10,
    echo=False,
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Run migration SQL to create all tables if they do not exist.
    Uses a PostgreSQL advisory lock (key=42) so that web and bot
    containers never run migrations concurrently and deadlock.
    """
    from bot.database.models import RUN_MIGRATIONS_SQL
    from sqlalchemy import text
    async with engine.begin() as conn:
        await conn.execute(text("SELECT pg_advisory_xact_lock(42)"))
        for statement in RUN_MIGRATIONS_SQL:
            await conn.execute(statement)


async def close_db():
    """Dispose the engine and release all connections."""
    await engine.dispose()

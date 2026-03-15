import asyncio
import hashlib
import hmac
import time
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text

from bot.database.models import RUN_MIGRATIONS_SQL
from web.auth import create_access_token

# ---------------------------------------------------------------------------
# Test database URL — use a separate test database
# ---------------------------------------------------------------------------
import os
TEST_DB_URL = os.getenv(
    "TEST_DATABASE_URL",
    os.getenv("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/autoservice_test"),
)

# ---------------------------------------------------------------------------
# Engine & session factory pointing at test DB
# ---------------------------------------------------------------------------
test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


# ---------------------------------------------------------------------------
# Patch connection module to use test engine BEFORE app is imported
# ---------------------------------------------------------------------------
import bot.database.connection as _conn

_conn.engine = test_engine
_conn.async_session = TestSession


# ---------------------------------------------------------------------------
# Import app after patching so it picks up test engine
# ---------------------------------------------------------------------------
from web.main import app  # noqa: E402


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def test_db():
    """Create all tables once per session; drop them at teardown."""
    async with test_engine.begin() as conn:
        for stmt in RUN_MIGRATIONS_SQL:
            await conn.execute(stmt)
    yield
    async with test_engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
    await test_engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def clean_tables():
    """Truncate all data tables between tests to keep tests independent."""
    yield
    async with test_engine.begin() as conn:
        await conn.execute(text(
            "TRUNCATE users, cars, orders, order_photos, order_logs, "
            "feedbacks, broadcasts RESTART IDENTITY CASCADE"
        ))
        await conn.execute(text("UPDATE counters SET value = 0 WHERE name = 'order_seq'"))


@pytest_asyncio.fixture
async def test_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


# ---------------------------------------------------------------------------
# User helpers
# ---------------------------------------------------------------------------

async def _create_db_user(telegram_id: int, full_name: str, phone: str, role: str):
    async with TestSession() as session:
        await session.execute(
            text(
                "INSERT INTO users (telegram_id, full_name, phone, role) "
                "VALUES (:tid, :name, :phone, :role) ON CONFLICT DO NOTHING"
            ),
            {"tid": telegram_id, "name": full_name, "phone": phone, "role": role},
        )
        await session.commit()
        result = await session.execute(
            text("SELECT id FROM users WHERE telegram_id = :tid"), {"tid": telegram_id}
        )
        return result.scalar_one()


@pytest_asyncio.fixture
async def master_user():
    uid = await _create_db_user(1001, "Test Master", "+998901234567", "master")
    return {"id": uid, "telegram_id": 1001, "role": "master"}


@pytest_asyncio.fixture
async def admin_user():
    uid = await _create_db_user(1002, "Test Admin", "+998901234568", "admin")
    return {"id": uid, "telegram_id": 1002, "role": "admin"}


@pytest_asyncio.fixture
async def client_user():
    uid = await _create_db_user(1003, "Test Client", "+998901234569", "client")
    return {"id": uid, "telegram_id": 1003, "role": "client"}


@pytest_asyncio.fixture
async def master_token(master_user):
    return create_access_token(master_user["id"], "master")


@pytest_asyncio.fixture
async def admin_token(admin_user):
    return create_access_token(admin_user["id"], "admin")


# ---------------------------------------------------------------------------
# Telegram auth helper
# ---------------------------------------------------------------------------

def make_telegram_auth_payload(bot_token: str, user_id: int = 42, age_seconds: int = 0) -> dict:
    """Build a valid Telegram Login Widget payload with correct HMAC hash."""
    auth_date = int(time.time()) - age_seconds
    data = {
        "id": user_id,
        "first_name": "Test",
        "auth_date": auth_date,
    }
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    hash_value = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return {**data, "hash": hash_value}


# ---------------------------------------------------------------------------
# Sample order fixture
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def sample_order(master_user):
    """Create a complete order; return order_number."""
    from bot.database.models import create_car, create_order, get_next_order_number
    order_number = await get_next_order_number()
    car_id = await create_car(
        order_number=order_number,
        brand="Toyota",
        model="Camry",
        plate="01A123BC",
        color="White",
        year=2020,
    )
    await create_order(
        order_number=order_number,
        car_id=car_id,
        master_id=master_user["id"],
        client_name="Sample Client",
        client_phone="+998901234567",
        problem="Engine check light is on",
        work_desc="Diagnostic and oil change",
        agreed_price=Decimal("500000"),
        paid_amount=Decimal("0"),
    )
    return order_number

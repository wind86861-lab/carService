import asyncio
from decimal import Decimal

import pytest
import pytest_asyncio

from bot.database.models import (
    add_payment,
    add_photo,
    auto_confirm_order,
    close_order,
    confirm_client_receipt,
    count_photos,
    create_car,
    create_feedback,
    create_order,
    create_user,
    get_car_by_order_number,
    get_dashboard_stats,
    get_feedback_by_order,
    get_financial_report,
    get_next_order_number,
    get_order_by_number,
    get_order_logs,
    get_orders_by_master,
    get_orders_by_plate,
    get_orders_closed_without_feedback,
    get_photos_by_order,
    get_user_by_id,
    get_user_by_telegram_id,
    get_visits_by_plate,
    link_client_to_order,
    update_order_status,
    update_user_phone,
    update_user_role,
)

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _make_user(tid: int, name: str = "User", phone: str = "+998901234567", role: str = "client"):
    return await create_user(telegram_id=tid, full_name=name, phone=phone, role=role)


async def _make_order(master_id: int, plate: str = "01A001AA", price: int = 500000) -> str:
    num = await get_next_order_number()
    car_id = await create_car(num, "Toyota", "Camry", plate, "White", 2020)
    await create_order(num, car_id, master_id, "Client", "+998901234567",
                       "Engine problem description here", "Replaced filter and oil",
                       Decimal(str(price)), Decimal("0"))
    return num


# ---------------------------------------------------------------------------
# TestUsers
# ---------------------------------------------------------------------------

class TestUsers:
    async def test_create_user(self):
        u = await create_user(5001, "Alice", "+998901111111", "client")
        assert u["telegram_id"] == 5001
        assert u["full_name"] == "Alice"
        assert u["role"] == "client"
        assert u["is_active"] is True

    async def test_create_user_duplicate(self):
        await create_user(5002, "Bob", "+998901111112", "client")
        u2 = await create_user(5002, "Bob Duplicate", "+998901111112", "client")
        # ON CONFLICT DO NOTHING — original name unchanged
        assert u2["full_name"] == "Bob"

    async def test_get_user_by_telegram_id_found(self):
        await create_user(5003, "Carol", "+998901111113", "client")
        u = await get_user_by_telegram_id(5003)
        assert u is not None
        assert u["telegram_id"] == 5003

    async def test_get_user_by_telegram_id_not_found(self):
        u = await get_user_by_telegram_id(99999999)
        assert u is None

    async def test_update_user_role(self):
        await create_user(5004, "Dave", "+998901111114", "client")
        await update_user_role(5004, "master")
        u = await get_user_by_telegram_id(5004)
        assert u["role"] == "master"

    async def test_update_user_phone(self):
        await create_user(5005, "Eve", None, "client")
        await update_user_phone(5005, "+998907777777")
        u = await get_user_by_telegram_id(5005)
        assert u["phone"] == "+998907777777"

    async def test_block_user(self):
        from bot.database.models import block_user
        await create_user(5006, "Frank", "+998901111116", "client")
        u = await get_user_by_telegram_id(5006)
        await block_user(u["id"])
        u2 = await get_user_by_id(u["id"])
        assert u2["is_active"] is False

    async def test_unblock_user(self):
        from bot.database.models import block_user, unblock_user
        await create_user(5007, "Grace", "+998901111117", "client")
        u = await get_user_by_telegram_id(5007)
        await block_user(u["id"])
        await unblock_user(u["id"])
        u2 = await get_user_by_id(u["id"])
        assert u2["is_active"] is True


# ---------------------------------------------------------------------------
# TestCounters
# ---------------------------------------------------------------------------

class TestCounters:
    async def test_get_next_order_number_format(self):
        num = await get_next_order_number()
        assert num.startswith("A-")
        assert len(num) == 6  # "A-0001"

    async def test_get_next_order_number_sequential(self):
        nums = [await get_next_order_number() for _ in range(10)]
        int_parts = [int(n.split("-")[1]) for n in nums]
        for i in range(1, len(int_parts)):
            assert int_parts[i] == int_parts[i - 1] + 1

    async def test_get_next_order_number_concurrent(self):
        nums = await asyncio.gather(*[get_next_order_number() for _ in range(20)])
        assert len(set(nums)) == 20


# ---------------------------------------------------------------------------
# TestCars
# ---------------------------------------------------------------------------

class TestCars:
    async def test_create_car(self):
        num = await get_next_order_number()
        car_id = await create_car(num, "BMW", "X5", "01B001BB", "Black", 2022)
        assert isinstance(car_id, int)
        car = await get_car_by_order_number(num)
        assert car["brand"] == "BMW"
        assert car["plate"] == "01B001BB"
        assert car["visit_count"] == 1

    async def test_create_car_repeat_visit(self):
        num1 = await get_next_order_number()
        await create_car(num1, "Honda", "Civic", "01C001CC", "Red", 2021)
        num2 = await get_next_order_number()
        car2_id = await create_car(num2, "Honda", "Civic", "01C001CC", "Red", 2021)
        car2 = await get_car_by_order_number(num2)
        assert car2["visit_count"] == 2

    async def test_get_car_by_order_number(self):
        num = await get_next_order_number()
        await create_car(num, "Audi", "A4", "01D001DD", "Silver", 2019)
        car = await get_car_by_order_number(num)
        assert car["order_number"] == num

    async def test_get_visits_by_plate(self):
        master = await _make_user(6001, "Master A", role="master")
        for _ in range(3):
            await _make_order(master["id"], plate="01E001EE")
        visits = await get_visits_by_plate("01E001EE")
        assert len(visits) == 3


# ---------------------------------------------------------------------------
# TestOrders
# ---------------------------------------------------------------------------

class TestOrders:
    async def test_create_order(self):
        master = await _make_user(6010, "Master B", role="master")
        num = await get_next_order_number()
        car_id = await create_car(num, "VW", "Polo", "01F001FF", "Blue", 2018)
        order_id = await create_order(
            num, car_id, master["id"], "Bob", "+998901234567",
            "Brake pads worn down completely", "Replaced brake pads front",
            Decimal("300000"), Decimal("150000"),
        )
        order = await get_order_by_number(num)
        assert order["order_number"] == num
        assert order["status"] == "new"
        assert float(order["agreed_price"]) == 300000

    async def test_get_order_by_number_not_found(self):
        o = await get_order_by_number("Z-9999")
        assert o is None

    async def test_get_orders_by_master(self):
        m1 = await _make_user(6011, "Master C", role="master")
        m2 = await _make_user(6012, "Master D", role="master")
        for _ in range(3):
            await _make_order(m1["id"])
        for _ in range(2):
            await _make_order(m2["id"])
        orders1 = await get_orders_by_master(m1["id"])
        orders2 = await get_orders_by_master(m2["id"])
        assert len(orders1) == 3
        assert len(orders2) == 2

    async def test_update_order_status_writes_log(self):
        master = await _make_user(6013, "Master E", role="master")
        num = await _make_order(master["id"])
        await update_order_status(num, "preparation", note="Work started", changed_by=master["id"])
        order = await get_order_by_number(num)
        assert order["status"] == "preparation"
        logs = await get_order_logs(order["id"])
        statuses = [l["status"] for l in logs]
        assert "preparation" in statuses

    async def test_update_order_status_sets_ready_at(self):
        master = await _make_user(6014, "Master F", role="master")
        num = await _make_order(master["id"])
        await update_order_status(num, "preparation")
        await update_order_status(num, "in_process")
        await update_order_status(num, "ready")
        order = await get_order_by_number(num)
        assert order["ready_at"] is not None

    async def test_link_client_to_order(self):
        master = await _make_user(6015, "Master G", role="master")
        client = await _make_user(6016, "Client A", role="client")
        num = await _make_order(master["id"])
        await link_client_to_order(num, client["id"])
        order = await get_order_by_number(num)
        assert order["client_id"] == client["id"]

    async def test_link_client_updates_car(self):
        master = await _make_user(6017, "Master H", role="master")
        client = await _make_user(6018, "Client B", role="client")
        num = await _make_order(master["id"])
        await link_client_to_order(num, client["id"])
        car = await get_car_by_order_number(num)
        assert car["client_id"] == client["id"]

    async def test_close_order_financials(self):
        master = await _make_user(6019, "Master I", role="master")
        num = await _make_order(master["id"], price=1000000)
        await update_order_status(num, "preparation")
        await update_order_status(num, "in_process")
        await update_order_status(num, "ready")
        await close_order(num, Decimal("300000"), Decimal("700000"),
                          Decimal("280000"), Decimal("420000"), changed_by=master["id"])
        order = await get_order_by_number(num)
        assert float(order["profit"]) == 700000
        assert float(order["master_share"]) == 280000
        assert float(order["service_share"]) == 420000
        assert order["status"] == "closed"

    async def test_close_order_negative_profit(self):
        master = await _make_user(6020, "Master J", role="master")
        num = await _make_order(master["id"], price=200000)
        await close_order(num, Decimal("350000"), Decimal("-150000"),
                          Decimal("-60000"), Decimal("-90000"), changed_by=master["id"])
        order = await get_order_by_number(num)
        assert float(order["profit"]) == -150000

    async def test_confirm_client_receipt(self):
        master = await _make_user(6021, "Master K", role="master")
        num = await _make_order(master["id"])
        await confirm_client_receipt(num)
        order = await get_order_by_number(num)
        assert order["client_confirmed"] is True

    async def test_add_payment(self):
        master = await _make_user(6022, "Master L", role="master")
        num = await _make_order(master["id"], price=500000)
        await add_payment(num, Decimal("200000"))
        await add_payment(num, Decimal("100000"))
        order = await get_order_by_number(num)
        assert float(order["paid_amount"]) == 300000


# ---------------------------------------------------------------------------
# TestPhotos
# ---------------------------------------------------------------------------

class TestPhotos:
    async def test_add_photo(self):
        master = await _make_user(6030, "Master M", role="master")
        num = await _make_order(master["id"])
        order = await get_order_by_number(num)
        await add_photo(order["id"], "file_id_1")
        await add_photo(order["id"], "file_id_2")
        photos = await get_photos_by_order(order["id"])
        assert len(photos) == 2

    async def test_max_photos_not_enforced_at_db_level(self):
        master = await _make_user(6031, "Master N", role="master")
        num = await _make_order(master["id"])
        order = await get_order_by_number(num)
        for i in range(3):
            await add_photo(order["id"], f"file_id_{i}")
        photos = await get_photos_by_order(order["id"])
        assert len(photos) == 3


# ---------------------------------------------------------------------------
# TestFeedbacks
# ---------------------------------------------------------------------------

class TestFeedbacks:
    async def test_create_feedback_full(self):
        master = await _make_user(6040, "Master O", role="master")
        client = await _make_user(6041, "Client C", role="client")
        num = await _make_order(master["id"])
        order = await get_order_by_number(num)
        await create_feedback(order["id"], client["id"], 8, "Quality", "Great service")
        fb = await get_feedback_by_order(order["id"])
        assert fb["rating"] == 8
        assert fb["category"] == "Quality"
        assert fb["comment"] == "Great service"

    async def test_create_feedback_minimal(self):
        master = await _make_user(6042, "Master P", role="master")
        client = await _make_user(6043, "Client D", role="client")
        num = await _make_order(master["id"])
        order = await get_order_by_number(num)
        await create_feedback(order["id"], client["id"], 9)
        fb = await get_feedback_by_order(order["id"])
        assert fb["rating"] == 9
        assert fb["category"] is None
        assert fb["comment"] is None

    async def test_get_feedback_by_order_not_found(self):
        master = await _make_user(6044, "Master Q", role="master")
        num = await _make_order(master["id"])
        order = await get_order_by_number(num)
        fb = await get_feedback_by_order(order["id"])
        assert fb is None

    async def test_get_orders_closed_without_feedback(self):
        master = await _make_user(6045, "Master R", role="master")
        client = await _make_user(6046, "Client E", role="client")

        num1 = await _make_order(master["id"])
        num2 = await _make_order(master["id"])

        for num in [num1, num2]:
            await link_client_to_order(num, client["id"])
            await close_order(num, Decimal("0"), Decimal("500000"),
                              Decimal("200000"), Decimal("300000"))

        # Force closed_at to be more than 1 hour ago for both
        from tests.conftest import TestSession
        from sqlalchemy import text as sqlt
        async with TestSession() as session:
            await session.execute(sqlt(
                "UPDATE orders SET closed_at = NOW() - INTERVAL '2 hours' "
                "WHERE order_number = ANY(:nums)"
            ), {"nums": [num1, num2]})
            await session.commit()

        # Add feedback to only the first order
        order1 = await get_order_by_number(num1)
        await create_feedback(order1["id"], client["id"], 7)

        pending = await get_orders_closed_without_feedback()
        pending_nums = [p["order_number"] for p in pending]
        assert num1 not in pending_nums
        assert num2 in pending_nums


# ---------------------------------------------------------------------------
# TestFinancials
# ---------------------------------------------------------------------------

class TestFinancials:
    async def test_get_financial_report_totals(self):
        master = await _make_user(6050, "Master S", role="master")
        for i in range(5):
            num = await _make_order(master["id"], price=1000000)
            await close_order(num, Decimal("300000"), Decimal("700000"),
                              Decimal("280000"), Decimal("420000"),
                              changed_by=master["id"])
        report = await get_financial_report({})
        summary = report["summary"]
        assert float(summary["total_revenue"]) == pytest.approx(5_000_000, rel=0.01)
        assert float(summary["total_profit"]) == pytest.approx(3_500_000, rel=0.01)

    async def test_get_financial_report_master_filter(self):
        m1 = await _make_user(6051, "Master T", role="master")
        m2 = await _make_user(6052, "Master U", role="master")
        for _ in range(3):
            num = await _make_order(m1["id"], price=1000000)
            await close_order(num, Decimal("0"), Decimal("1000000"),
                              Decimal("400000"), Decimal("600000"), changed_by=m1["id"])
        for _ in range(2):
            num = await _make_order(m2["id"], price=1000000)
            await close_order(num, Decimal("0"), Decimal("1000000"),
                              Decimal("400000"), Decimal("600000"), changed_by=m2["id"])

        report = await get_financial_report({"master_id": m1["id"]})
        assert len(report["orders"]) == 3

    async def test_get_dashboard_stats(self):
        master = await _make_user(6053, "Master V", role="master")
        await _make_order(master["id"])  # new
        num2 = await _make_order(master["id"])
        await update_order_status(num2, "preparation")
        await update_order_status(num2, "in_process")
        await update_order_status(num2, "ready")  # ready

        stats = await get_dashboard_stats()
        assert stats["active_orders"] >= 1
        assert stats["ready_orders"] >= 1

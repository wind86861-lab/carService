import hashlib
import hmac
import io
import os
import time
from decimal import Decimal

import pytest
import pytest_asyncio

from tests.conftest import make_telegram_auth_payload

pytestmark = pytest.mark.asyncio

BOT_TOKEN = os.getenv("BOT_TOKEN", "fake_token_for_tests")

VALID_ORDER = {
    "brand": "Toyota",
    "model": "Camry",
    "plate": "01A123BC",
    "color": "White",
    "year": 2020,
    "client_name": "John Doe",
    "client_phone": "+998901234567",
    "problem": "Engine check light keeps coming on",
    "work_desc": "Run full diagnostic and oil change",
    "agreed_price": "500000",
    "paid_amount": "0",
}


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class TestHealth:
    async def test_health_returns_200(self, test_client):
        resp = await test_client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class TestAuth:
    async def test_telegram_auth_valid(self, test_client):
        payload = make_telegram_auth_payload(BOT_TOKEN, user_id=9001)
        resp = await test_client.post("/api/auth/telegram", json={
            "id": payload["id"],
            "first_name": payload["first_name"],
            "auth_date": payload["auth_date"],
            "hash": payload["hash"],
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    async def test_telegram_auth_invalid_hash(self, test_client):
        payload = make_telegram_auth_payload(BOT_TOKEN, user_id=9002)
        payload["hash"] = "deadbeef" * 8
        resp = await test_client.post("/api/auth/telegram", json={
            "id": payload["id"],
            "first_name": "Test",
            "auth_date": payload["auth_date"],
            "hash": payload["hash"],
        })
        assert resp.status_code == 401

    async def test_telegram_auth_old_auth_date(self, test_client):
        payload = make_telegram_auth_payload(BOT_TOKEN, user_id=9003, age_seconds=90000)
        resp = await test_client.post("/api/auth/telegram", json={
            "id": payload["id"],
            "first_name": "Test",
            "auth_date": payload["auth_date"],
            "hash": payload["hash"],
        })
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Order endpoints — master
# ---------------------------------------------------------------------------

class TestOrders:
    async def test_create_order_success(self, test_client, master_token):
        resp = await test_client.post(
            "/api/orders",
            json=VALID_ORDER,
            headers={"Authorization": f"Bearer {master_token}"},
        )
        assert resp.status_code == 201
        assert "order_number" in resp.json()

    async def test_create_order_missing_fields(self, test_client, master_token):
        resp = await test_client.post(
            "/api/orders",
            json={"brand": "Toyota"},
            headers={"Authorization": f"Bearer {master_token}"},
        )
        assert resp.status_code == 422

    async def test_create_order_invalid_price(self, test_client, master_token):
        body = {**VALID_ORDER, "agreed_price": "-100"}
        resp = await test_client.post(
            "/api/orders",
            json=body,
            headers={"Authorization": f"Bearer {master_token}"},
        )
        assert resp.status_code == 422

    async def test_create_order_invalid_year(self, test_client, master_token):
        body = {**VALID_ORDER, "year": 1800}
        resp = await test_client.post(
            "/api/orders",
            json=body,
            headers={"Authorization": f"Bearer {master_token}"},
        )
        assert resp.status_code == 422

    async def test_get_orders_empty(self, test_client, master_token):
        resp = await test_client.get(
            "/api/orders",
            headers={"Authorization": f"Bearer {master_token}"},
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_get_orders_filters_by_status(self, test_client, master_token):
        for _ in range(3):
            await test_client.post(
                "/api/orders",
                json=VALID_ORDER,
                headers={"Authorization": f"Bearer {master_token}"},
            )
        resp = await test_client.get(
            "/api/orders?status=new",
            headers={"Authorization": f"Bearer {master_token}"},
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 3

    async def test_get_order_detail_found(self, test_client, master_token, sample_order):
        resp = await test_client.get(
            f"/api/orders/{sample_order}",
            headers={"Authorization": f"Bearer {master_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["order_number"] == sample_order

    async def test_get_order_detail_not_found(self, test_client, master_token):
        resp = await test_client.get(
            "/api/orders/Z-9999",
            headers={"Authorization": f"Bearer {master_token}"},
        )
        assert resp.status_code == 404

    async def test_get_order_detail_wrong_master(self, test_client, sample_order):
        from bot.database.models import create_user
        from web.auth import create_access_token
        other = await create_user(7001, "Other Master", "+998907001000", "master")
        other_token = create_access_token(other["id"], "master")
        resp = await test_client.get(
            f"/api/orders/{sample_order}",
            headers={"Authorization": f"Bearer {other_token}"},
        )
        assert resp.status_code == 403

    async def test_update_status_valid_transition(self, test_client, master_token, sample_order):
        resp = await test_client.patch(
            f"/api/orders/{sample_order}/status",
            json={"status": "preparation"},
            headers={"Authorization": f"Bearer {master_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "preparation"

    async def test_update_status_invalid_transition(self, test_client, master_token, sample_order):
        resp = await test_client.patch(
            f"/api/orders/{sample_order}/status",
            json={"status": "ready"},
            headers={"Authorization": f"Bearer {master_token}"},
        )
        assert resp.status_code == 400

    async def test_update_status_backwards(self, test_client, master_token, sample_order):
        await test_client.patch(
            f"/api/orders/{sample_order}/status",
            json={"status": "preparation"},
            headers={"Authorization": f"Bearer {master_token}"},
        )
        await test_client.patch(
            f"/api/orders/{sample_order}/status",
            json={"status": "in_process"},
            headers={"Authorization": f"Bearer {master_token}"},
        )
        resp = await test_client.patch(
            f"/api/orders/{sample_order}/status",
            json={"status": "preparation"},
            headers={"Authorization": f"Bearer {master_token}"},
        )
        assert resp.status_code == 400

    async def test_close_order_success(self, test_client, master_token, sample_order):
        for st in ["preparation", "in_process", "ready"]:
            await test_client.patch(
                f"/api/orders/{sample_order}/status",
                json={"status": st},
                headers={"Authorization": f"Bearer {master_token}"},
            )
        resp = await test_client.post(
            f"/api/orders/{sample_order}/close",
            json={"parts_cost": "150000"},
            headers={"Authorization": f"Bearer {master_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert float(data["profit"]) == pytest.approx(350000, rel=0.01)
        assert float(data["master_share"]) == pytest.approx(140000, rel=0.01)
        assert float(data["service_share"]) == pytest.approx(210000, rel=0.01)

    async def test_close_order_requires_ready_status(self, test_client, master_token, sample_order):
        resp = await test_client.post(
            f"/api/orders/{sample_order}/close",
            json={"parts_cost": "0"},
            headers={"Authorization": f"Bearer {master_token}"},
        )
        assert resp.status_code == 400

    async def test_upload_photos_wrong_format(self, test_client, master_token, sample_order):
        resp = await test_client.post(
            f"/api/orders/{sample_order}/photos",
            files={"files": ("test.txt", b"hello", "text/plain")},
            headers={"Authorization": f"Bearer {master_token}"},
        )
        assert resp.status_code == 400

    async def test_add_payment_success(self, test_client, master_token, sample_order):
        resp = await test_client.post(
            f"/api/orders/{sample_order}/payment",
            json={"amount": "100000"},
            headers={"Authorization": f"Bearer {master_token}"},
        )
        assert resp.status_code == 200
        assert float(resp.json()["paid_amount"]) == pytest.approx(100000, rel=0.01)

    async def test_add_payment_exceeds_price(self, test_client, master_token, sample_order):
        resp = await test_client.post(
            f"/api/orders/{sample_order}/payment",
            json={"amount": "9999999"},
            headers={"Authorization": f"Bearer {master_token}"},
        )
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Car endpoints
# ---------------------------------------------------------------------------

class TestCars:
    async def test_get_car_history_found(self, test_client, master_token):
        for _ in range(3):
            body = {**VALID_ORDER, "plate": "99Z999ZZ"}
            await test_client.post(
                "/api/orders",
                json=body,
                headers={"Authorization": f"Bearer {master_token}"},
            )
        resp = await test_client.get(
            "/api/cars/99Z999ZZ",
            headers={"Authorization": f"Bearer {master_token}"},
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 3

    async def test_get_car_history_not_found(self, test_client, master_token):
        resp = await test_client.get(
            "/api/cars/NOPLATE",
            headers={"Authorization": f"Bearer {master_token}"},
        )
        assert resp.status_code == 200
        assert resp.json() == []


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------

class TestAdmin:
    async def test_admin_dashboard_requires_admin(self, test_client, master_token):
        resp = await test_client.get(
            "/api/admin/dashboard",
            headers={"Authorization": f"Bearer {master_token}"},
        )
        assert resp.status_code == 403

    async def test_admin_dashboard_success(self, test_client, admin_token):
        resp = await test_client.get(
            "/api/admin/dashboard",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "active_orders" in data
        assert "month_revenue" in data

    async def test_admin_force_close(self, test_client, admin_token, sample_order):
        resp = await test_client.patch(
            f"/api/admin/orders/{sample_order}/force-close",
            json={"parts_cost": "0"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200

        from bot.database.models import get_order_by_number, get_order_logs
        order = await get_order_by_number(sample_order)
        assert order["status"] == "closed"
        logs = await get_order_logs(order["id"])
        notes = [l["note"] for l in logs]
        assert any("Force closed by admin" in (n or "") for n in notes)

    async def test_admin_block_client(self, test_client, admin_token, client_user):
        resp = await test_client.post(
            f"/api/admin/users/{client_user['id']}/block",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        from bot.database.models import get_user_by_id
        u = await get_user_by_id(client_user["id"])
        assert u["is_active"] is False

    async def test_admin_unblock_client(self, test_client, admin_token, client_user):
        await test_client.post(
            f"/api/admin/users/{client_user['id']}/block",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        resp = await test_client.post(
            f"/api/admin/users/{client_user['id']}/unblock",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        from bot.database.models import get_user_by_id
        u = await get_user_by_id(client_user["id"])
        assert u["is_active"] is True

    async def test_admin_promote_client(self, test_client, admin_token, client_user):
        resp = await test_client.post(
            f"/api/admin/users/{client_user['id']}/role",
            json={"role": "master"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        from bot.database.models import get_user_by_id
        u = await get_user_by_id(client_user["id"])
        assert u["role"] == "master"

    async def test_admin_demote_master(self, test_client, admin_token, master_user):
        resp = await test_client.post(
            f"/api/admin/users/{master_user['id']}/role",
            json={"role": "client"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        from bot.database.models import get_user_by_id
        u = await get_user_by_id(master_user["id"])
        assert u["role"] == "client"

    async def test_admin_financial_report_totals(self, test_client, admin_token, master_user, sample_order):
        for st in ["preparation", "in_process", "ready"]:
            await test_client.patch(
                f"/api/orders/{sample_order}/status",
                json={"status": st},
                headers={"Authorization": f"Bearer {create_master_token(master_user)}"},
            )
        await test_client.post(
            f"/api/orders/{sample_order}/close",
            json={"parts_cost": "100000"},
            headers={"Authorization": f"Bearer {create_master_token(master_user)}"},
        )
        resp = await test_client.get(
            "/api/admin/financials",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "summary" in data
        assert float(data["summary"]["total_revenue"]) >= 500000

    async def test_admin_export_excel(self, test_client, admin_token):
        resp = await test_client.get(
            "/api/admin/financials/export?format=xlsx",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert "spreadsheetml" in resp.headers.get("content-type", "")

    async def test_admin_export_pdf(self, test_client, admin_token):
        resp = await test_client.get(
            "/api/admin/financials/export?format=pdf",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert "pdf" in resp.headers.get("content-type", "")

    async def test_admin_feedbacks_stats(self, test_client, admin_token, master_user):
        from bot.database.models import (
            create_feedback, create_user, get_next_order_number,
            create_car, create_order, get_order_by_number,
        )
        client = await create_user(8001, "Stats Client", "+998908001000", "client")
        for rating in [8, 9, 10, 3, 4]:
            num = await get_next_order_number()
            car_id = await create_car(num, "Ford", "Focus", f"ST{rating}000ST", "Red", 2019)
            await create_order(num, car_id, master_user["id"], "Name", "+998901234567",
                               "Problem description long enough", "Work description long",
                               Decimal("200000"), Decimal("0"))
            o = await get_order_by_number(num)
            await create_feedback(o["id"], client["id"], rating)

        resp = await test_client.get(
            "/api/admin/feedbacks/stats",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "avg_rating" in data
        assert float(data["avg_rating"]) == pytest.approx((8+9+10+3+4)/5, rel=0.01)


def create_master_token(master_user):
    from web.auth import create_access_token
    return create_access_token(master_user["id"], "master")

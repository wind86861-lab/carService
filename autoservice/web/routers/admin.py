import io
import secrets
import string
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile, status
from fastapi.responses import StreamingResponse

from bot.database.models import (
    add_payment,
    block_user,
    create_car,
    create_order,
    force_close_order,
    get_all_clients,
    get_all_feedbacks,
    get_all_masters,
    get_all_orders,
    get_broadcasts,
    get_client_profile,
    get_dashboard_stats,
    get_expenses_by_order,
    get_feedback_stats,
    get_financial_report,
    get_master_profile,
    get_next_order_number,
    get_order_by_number,
    get_order_detail,
    get_order_logs,
    get_photos_by_order,
    get_visits_by_plate,
    set_user_role,
    unblock_user,
)
from web.auth import require_admin
from web.utils.broadcast import send_broadcast
from web.utils.export import generate_excel_report, generate_pdf_report
from web.utils.notify import notify_receipt_request

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


@router.get("/dashboard")
async def admin_dashboard(_admin=Depends(require_admin)):
    return await get_dashboard_stats()


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------


@router.get("/orders")
async def admin_get_orders(
    status: Optional[str] = None,
    master_id: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _admin=Depends(require_admin),
):
    filters = {
        "status": status,
        "master_id": master_id,
        "date_from": date_from,
        "date_to": date_to,
        "search": search,
    }
    return await get_all_orders({k: v for k, v in filters.items() if v is not None}, page, page_size)


@router.get("/orders/{order_number}")
async def admin_get_order(order_number: str, _admin=Depends(require_admin)):
    detail = await get_order_detail(order_number)
    if not detail:
        raise HTTPException(status_code=404, detail="Order not found")
    order = dict(detail)
    from web.utils.photos import get_photo_url
    logs = await get_order_logs(order["id"])
    order["logs"] = [
        {**dict(l), "receipt_url": get_photo_url(l["receipt_file_id"]) if l.get("receipt_file_id") else None}
        for l in logs
    ]
    photos = await get_photos_by_order(order["id"])
    order["photos"] = [
        {"id": p["id"], "file_id": p["file_id"], "url": get_photo_url(p["file_id"]), "uploaded_at": p["uploaded_at"]}
        for p in photos
    ]
    expenses = await get_expenses_by_order(order["id"])
    order["expenses"] = [
        {
            "id": e["id"], "item_name": e["item_name"], "amount": float(e["amount"]),
            "receipt_url": get_photo_url(e["receipt_file_id"]) if e.get("receipt_file_id") else None,
            "added_by_name": e.get("added_by_name"), "created_at": e["created_at"],
        }
        for e in expenses
    ]
    return order


@router.get("/masters-list")
async def admin_masters_list(_admin=Depends(require_admin)):
    """Simple list of all masters for dropdowns."""
    from sqlalchemy import text
    from bot.database.db import async_session
    async with async_session() as session:
        result = await session.execute(
            text("SELECT id, full_name, username, phone FROM users WHERE role = 'master' AND is_blocked = false ORDER BY full_name")
        )
        return [dict(r) for r in result.mappings().all()]


@router.post("/orders", status_code=status.HTTP_201_CREATED)
async def admin_create_order(body: dict, admin=Depends(require_admin)):
    from decimal import Decimal

    master_id = body.get("master_id")
    if not master_id:
        raise HTTPException(status_code=400, detail="Ustani tanlang")

    required = ["brand", "model", "plate", "color", "year", "client_name", "client_phone", "problem", "work_desc", "agreed_price"]
    for f in required:
        if not body.get(f):
            raise HTTPException(status_code=400, detail=f"'{f}' majburiy maydon")

    agreed_price = Decimal(str(body["agreed_price"]))
    paid_amount = Decimal(str(body.get("paid_amount", 0)))
    if paid_amount > agreed_price:
        raise HTTPException(status_code=400, detail="To'langan summa kelishilgan narxdan oshmasligi kerak")

    order_number = await get_next_order_number()
    car_id = await create_car(
        order_number=order_number,
        brand=body["brand"],
        model=body["model"],
        plate=body["plate"].upper(),
        color=body["color"],
        year=int(body["year"]),
    )
    order_id = await create_order(
        order_number=order_number,
        car_id=car_id,
        master_id=int(master_id),
        client_name=body["client_name"],
        client_phone=body["client_phone"],
        problem=body["problem"],
        work_desc=body["work_desc"],
        agreed_price=agreed_price,
        paid_amount=paid_amount,
    )
    return {"order_number": order_number, "order_id": order_id}


@router.post("/orders/{order_number}/photos")
async def admin_upload_photos(
    order_number: str,
    files: list[UploadFile] = File(...),
    _admin=Depends(require_admin),
):
    from web.utils.photos import save_upload_file, validate_image, get_photo_url
    from bot.database.models import add_photo, count_photos

    order = await get_order_by_number(order_number)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    existing = await count_photos(order["id"])
    if existing >= 2:
        raise HTTPException(status_code=400, detail="Maximum 2 photos per order")
    if existing + len(files) > 2:
        raise HTTPException(status_code=400, detail=f"Can only add {2 - existing} more photo(s)")

    results = []
    for file in files:
        validate_image(file)
        filename = await save_upload_file(file)
        photo_id = await add_photo(order["id"], filename)
        results.append({"id": photo_id, "file_id": filename, "url": get_photo_url(filename)})
    return results


@router.patch("/orders/{order_number}/force-close")
async def admin_force_close(
    order_number: str,
    body: dict,
    admin=Depends(require_admin),
):
    parts_cost = float(body.get("parts_cost", 0))
    result = await force_close_order(order_number, parts_cost, admin["id"])
    if not result:
        raise HTTPException(status_code=404, detail="Order not found")
    order = await get_order_by_number(order_number)
    if order and order.get("client_id"):
        from bot.database.models import get_user_by_id
        client = await get_user_by_id(order["client_id"])
        if client:
            await notify_receipt_request(client["telegram_id"], order_number)
    return result


@router.post("/orders/{order_number}/payment")
async def admin_record_payment(
    order_number: str,
    description: str = Form(...),
    amount: float = Form(...),
    receipt: UploadFile = File(...),
    admin=Depends(require_admin),
):
    from web.utils.photos import save_upload_file, validate_image

    order = await get_order_by_number(order_number)
    if not order:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi")
    if not description.strip():
        raise HTTPException(status_code=400, detail="To'lov nomi majburiy")
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Summani kiriting")

    validate_image(receipt)
    receipt_filename = await save_upload_file(receipt)

    await add_payment(order_number, amount, changed_by=admin["id"], description=description.strip(), receipt_file_id=receipt_filename)
    updated = await get_order_by_number(order_number)
    return {"paid_amount": float(updated["paid_amount"])}


# ---------------------------------------------------------------------------
# Clients
# ---------------------------------------------------------------------------


@router.get("/clients")
async def admin_get_clients(
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _admin=Depends(require_admin),
):
    return await get_all_clients(search, is_active, page, page_size)


@router.get("/clients/{client_id}")
async def admin_get_client(client_id: int, _admin=Depends(require_admin)):
    profile = await get_client_profile(client_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Client not found")
    return profile


@router.patch("/clients/{client_id}/block")
async def admin_block_client(client_id: int, _admin=Depends(require_admin)):
    result = await block_user(client_id)
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return result


@router.patch("/clients/{client_id}/unblock")
async def admin_unblock_client(client_id: int, _admin=Depends(require_admin)):
    result = await unblock_user(client_id)
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return result


# ---------------------------------------------------------------------------
# Masters
# ---------------------------------------------------------------------------


@router.get("/masters")
async def admin_get_masters(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _admin=Depends(require_admin),
):
    return await get_all_masters(page, page_size)


@router.get("/masters/{master_id}")
async def admin_get_master(
    master_id: int,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    _admin=Depends(require_admin),
):
    df = datetime.fromisoformat(date_from).replace(hour=0, minute=0, second=0, microsecond=0) if date_from else None
    dt = datetime.fromisoformat(date_to).replace(hour=23, minute=59, second=59, microsecond=999999) if date_to else None
    profile = await get_master_profile(master_id, df, dt)
    if not profile:
        raise HTTPException(status_code=404, detail="Master not found")
    return profile


@router.patch("/masters/{master_id}/promote")
async def admin_promote(master_id: int, _admin=Depends(require_admin)):
    import httpx
    from sqlalchemy import text
    from bot.database.connection import async_session
    from web.auth import hash_password
    from web.config import BOT_TOKEN

    result = await set_user_role(master_id, "master")
    if not result:
        raise HTTPException(status_code=404, detail="User not found")

    async with async_session() as session:
        row = await session.execute(
            text("SELECT id, full_name, telegram_id, username FROM users WHERE id = :id"),
            {"id": master_id},
        )
        user = row.mappings().first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        username = user["username"]
        password = None
        if not username:
            base = (user["full_name"] or "master").lower().replace(" ", "")[:10]
            username = base + str(master_id)
            password = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(10))
            password_hash = hash_password(password)
            await session.execute(
                text("UPDATE users SET username = :u, password_hash = :p WHERE id = :id"),
                {"u": username, "p": password_hash, "id": master_id},
            )
            await session.commit()

        tg_id = user["telegram_id"]
        if tg_id and password:
            msg = (
                "Tabriklaymiz! Siz usta sifatida tayinlandingiz.\n\n"
                "Web panelga kirish:\n"
                "http://155.212.139.74/login\n\n"
                "Username: " + username + "\n"
                "Password: " + password + "\n\n"
                "Tizimga kirgach parolingizni ozgartiring."
            )
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                        json={"chat_id": tg_id, "text": msg},
                        timeout=5.0,
                    )
            except Exception:
                pass

        return {"username": username, "password_generated": password is not None, "role": "master"}


@router.patch("/masters/{master_id}/demote")
async def admin_demote(master_id: int, _admin=Depends(require_admin)):
    result = await set_user_role(master_id, "client")
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return result


@router.patch("/masters/{master_id}/block")
async def admin_block_master(master_id: int, _admin=Depends(require_admin)):
    result = await block_user(master_id)
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return result


@router.patch("/masters/{master_id}/unblock")
async def admin_unblock_master(master_id: int, _admin=Depends(require_admin)):
    result = await unblock_user(master_id)
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return result



class CreateMasterSchema(BaseModel):
    full_name: str
    username: str
    password: str
    phone: str = None


@router.post("/masters")
async def admin_create_master(data: CreateMasterSchema, _admin=Depends(require_admin)):
    from sqlalchemy import text
    from bot.database.connection import async_session
    from web.auth import hash_password
    import time

    async with async_session() as session:
        existing = await session.execute(
            text("SELECT id FROM users WHERE username = :u"),
            {"u": data.username},
        )
        if existing.first():
            raise HTTPException(status_code=400, detail="Username already taken")

        password_hash = hash_password(data.password)
        result = await session.execute(
            text(
                "INSERT INTO users (telegram_id, full_name, phone, role, username, password_hash, is_active) "
                "VALUES (:tid, :name, :phone, 'master', :username, :hash, true) "
                "RETURNING id, full_name, username, role"
            ),
            {
                "tid": int(time.time() * 1000),
                "name": data.full_name,
                "phone": data.phone,
                "username": data.username,
                "hash": password_hash,
            },
        )
        await session.commit()
        row = result.first()
        return {"id": row[0], "full_name": row[1], "username": row[2], "role": row[3]}


# ---------------------------------------------------------------------------
# Financials
# ---------------------------------------------------------------------------


@router.get("/financials")
async def admin_financials(
    master_id: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    _admin=Depends(require_admin),
):
    df = datetime.fromisoformat(date_from).replace(hour=0, minute=0, second=0, microsecond=0) if date_from else None
    dt = datetime.fromisoformat(date_to).replace(hour=23, minute=59, second=59, microsecond=999999) if date_to else None
    return await get_financial_report(master_id, df, dt)


@router.get("/financials/export")
async def admin_financials_export(
    master_id: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    export_format: str = Query("xlsx", pattern="^(xlsx|pdf)$"),
    _admin=Depends(require_admin),
):
    df = datetime.fromisoformat(date_from).replace(hour=0, minute=0, second=0, microsecond=0) if date_from else None
    dt = datetime.fromisoformat(date_to).replace(hour=23, minute=59, second=59, microsecond=999999) if date_to else None
    report = await get_financial_report(master_id, df, dt)
    orders = [dict(o) for o in report["orders"]]
    summary = report["summary"]
    period = f"{date_from or 'start'} — {date_to or 'now'}"

    if export_format == "xlsx":
        data = generate_excel_report(orders, summary)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = "financial_report.xlsx"
    else:
        data = generate_pdf_report(orders, summary, period)
        media_type = "application/pdf"
        filename = "financial_report.pdf"

    return Response(
        content=data,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# Broadcast
# ---------------------------------------------------------------------------


@router.post("/broadcast")
async def admin_broadcast(body: dict, admin=Depends(require_admin)):
    target = body.get("target", "all")
    message = body.get("message", "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    if target not in ("all", "clients", "masters"):
        raise HTTPException(status_code=400, detail="Invalid target")
    return await send_broadcast(target, message, admin["id"])


@router.get("/broadcasts")
async def admin_get_broadcasts(_admin=Depends(require_admin)):
    return await get_broadcasts()


# ---------------------------------------------------------------------------
# Feedbacks
# ---------------------------------------------------------------------------


@router.get("/feedbacks")
async def admin_get_feedbacks(
    master_id: Optional[int] = None,
    rating_max: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _admin=Depends(require_admin),
):
    filters = {
        "master_id": master_id,
        "rating_max": rating_max,
        "date_from": date_from,
        "date_to": date_to,
    }
    return await get_all_feedbacks({k: v for k, v in filters.items() if v is not None}, page, page_size)


@router.get("/feedbacks/stats")
async def admin_feedback_stats(_admin=Depends(require_admin)):
    return await get_feedback_stats()


# ---------------------------------------------------------------------------
# Car history
# ---------------------------------------------------------------------------


@router.get("/cars/{plate}")
async def admin_car_history(plate: str, _admin=Depends(require_admin)):
    visits = await get_visits_by_plate(plate)
    return list(visits)

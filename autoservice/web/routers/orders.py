from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status

from bot.database.models import (
    add_payment,
    add_photo,
    close_order,
    count_photos,
    create_car,
    create_order,
    create_order_expense,
    get_expenses_by_order,
    get_next_order_number,
    get_order_by_number,
    get_order_detail,
    get_order_logs,
    get_orders_by_master,
    get_photos_by_order,
    update_order_status,
    update_parts_cost,
)
from web.auth import require_master
from web.schemas import (
    OrderCloseSchema,
    OrderCreateSchema,
    OrderUpdateStatusSchema,
    PaymentSchema,
)
from web.utils.calculations import calculate_order_financials, validate_financials
from web.utils.notify import notify_receipt_request, notify_status_changed
from web.utils.photos import get_photo_url, save_upload_file, validate_image

router = APIRouter(tags=["orders"])

ALLOWED_TRANSITIONS = {
    "new": "preparation",
    "preparation": "in_process",
    "in_process": "ready",
    "ready": "closed",
}

VALID_STATUSES = {"new", "preparation", "in_process", "ready"}


@router.post("/orders", status_code=status.HTTP_201_CREATED)
async def create_new_order(body: OrderCreateSchema, master=Depends(require_master)):
    if body.paid_amount > body.agreed_price:
        raise HTTPException(status_code=400, detail="Paid amount cannot exceed agreed price")

    order_number = await get_next_order_number()
    car_id = await create_car(
        order_number=order_number,
        brand=body.brand,
        model=body.model,
        plate=body.plate,
        color=body.color,
        year=body.year,
    )
    order_id = await create_order(
        order_number=order_number,
        car_id=car_id,
        master_id=master["id"],
        client_name=body.client_name,
        client_phone=body.client_phone,
        problem=body.problem,
        work_desc=body.work_desc,
        agreed_price=body.agreed_price,
        paid_amount=body.paid_amount,
    )
    return {"order_number": order_number, "order_id": order_id}


@router.get("/orders")
async def list_orders(
    status_filter: Optional[str] = Query(None, alias="status"),
    master=Depends(require_master),
):
    orders = await get_orders_by_master(master["id"], status=status_filter)
    return [dict(o) for o in orders]


@router.get("/orders/{order_number}")
async def get_order(order_number: str, master=Depends(require_master)):
    detail = await get_order_detail(order_number)
    if not detail:
        raise HTTPException(status_code=404, detail="Order not found")
    order = dict(detail)
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


@router.patch("/orders/{order_number}/status")
async def update_status(
    order_number: str,
    body: OrderUpdateStatusSchema,
    master=Depends(require_master),
):
    order = await get_order_by_number(order_number)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if body.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Noto'g'ri holat: {body.status}",
        )
    if body.status == order["status"]:
        raise HTTPException(
            status_code=400,
            detail="Buyurtma allaqachon shu holatda",
        )

    await update_order_status(
        order_number, body.status, note=body.note, changed_by=master["id"]
    )

    if order.get("client_id"):
        from bot.database.models import get_user_by_id
        client = await get_user_by_id(order["client_id"])
        if client and client.get("telegram_id"):
            car_info = f"{order.get('brand', '')} {order.get('model', '')}".strip() or "—"
            await notify_status_changed(client["telegram_id"], order_number, body.status, car_info)
            if body.status == "ready":
                agreed = int(order.get("agreed_price") or 0)
                paid = int(order.get("paid_amount") or 0)
                remaining = max(0, agreed - paid)
                from bot.utils.formatters import format_money
                await notify_receipt_request(
                    client["telegram_id"], order_number,
                    car_info=car_info,
                    agreed_price=format_money(agreed),
                    paid_amount=format_money(paid),
                    remaining=format_money(remaining),
                )

    updated = await get_order_by_number(order_number)
    return dict(updated)


@router.post("/orders/{order_number}/close")
async def close_order_endpoint(
    order_number: str,
    body: OrderCloseSchema,
    master=Depends(require_master),
):
    order = await get_order_by_number(order_number)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order["status"] == "closed":
        raise HTTPException(status_code=400, detail="Order is already closed")
    
    # Masters can only mark order as ready with financials, not fully close it
    # Client must confirm receipt via Telegram before order is truly closed
    if order["status"] != "ready":
        raise HTTPException(
            status_code=400, 
            detail="Order must be in 'ready' status before closing. Change status to 'ready' first."
        )

    agreed = Decimal(str(order["agreed_price"]))
    try:
        validate_financials(agreed, body.parts_cost)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    from bot.database.models import get_master_total_earnings as _get_total
    master_total = await _get_total(master["id"])
    financials = calculate_order_financials(agreed, body.parts_cost, master_total)
    await close_order(
        order_number=order_number,
        parts_cost=body.parts_cost,
        profit=financials.profit,
        master_share=financials.master_share,
        service_share=financials.service_share,
        changed_by=master["id"],
    )

    if order.get("client_id"):
        from bot.database.models import get_user_by_id
        client = await get_user_by_id(order["client_id"])
        if client:
            await notify_receipt_request(client["telegram_id"], order_number)

    return {
        "order_number": order_number,
        "profit": float(financials.profit),
        "master_share": float(financials.master_share),
        "service_share": float(financials.service_share),
        "status": "closed",
        "note": "Order closed. Waiting for client confirmation via Telegram.",
    }


@router.post("/orders/{order_number}/photos")
async def upload_photos(
    order_number: str,
    files: list[UploadFile] = File(...),
    master=Depends(require_master),
):
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


@router.get("/orders/{order_number}/photos")
async def list_photos(order_number: str, master=Depends(require_master)):
    order = await get_order_by_number(order_number)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    photos = await get_photos_by_order(order["id"])
    return [
        {"id": p["id"], "file_id": p["file_id"], "url": get_photo_url(p["file_id"]), "uploaded_at": p["uploaded_at"]}
        for p in photos
    ]


@router.post("/orders/{order_number}/expenses", status_code=201)
async def add_expense(
    order_number: str,
    item_name: str,
    amount: float,
    master=Depends(require_master),
):
    order = await get_order_by_number(order_number)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order["status"] == "closed":
        raise HTTPException(status_code=400, detail="Cannot add expense to a closed order")
    await create_order_expense(
        order_id=order["id"],
        item_name=item_name,
        amount=int(amount),
        added_by=master["id"],
    )
    await update_parts_cost(order_number, int(amount), changed_by=master["id"])
    updated = await get_order_by_number(order_number)
    return {"parts_cost": float(updated["parts_cost"])}


@router.post("/orders/{order_number}/payment")
async def record_payment(
    order_number: str,
    description: str = Form(...),
    amount: float = Form(...),
    receipt: UploadFile = File(...),
    master=Depends(require_master),
):
    order = await get_order_by_number(order_number)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order["status"] == "closed" and order["client_confirmed"]:
        raise HTTPException(status_code=400, detail="Cannot add payment to a fully closed order")
    if not description.strip():
        raise HTTPException(status_code=400, detail="To'lov nomi majburiy")
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Summani kiriting")

    validate_image(receipt)
    receipt_filename = await save_upload_file(receipt)

    await add_payment(order_number, amount, changed_by=master["id"], description=description.strip(), receipt_file_id=receipt_filename)
    updated = await get_order_by_number(order_number)
    remaining = Decimal(str(updated["agreed_price"])) - Decimal(str(updated["paid_amount"]))
    return {"paid_amount": float(updated["paid_amount"]), "remaining": float(remaining)}

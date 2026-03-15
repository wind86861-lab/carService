import io
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse

from bot.database.models import (
    block_user,
    force_close_order,
    get_all_clients,
    get_all_feedbacks,
    get_all_masters,
    get_all_orders,
    get_broadcasts,
    get_client_profile,
    get_dashboard_stats,
    get_feedback_stats,
    get_financial_report,
    get_master_profile,
    get_order_by_number,
    get_order_detail,
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
    return detail


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
    profile = await get_master_profile(master_id, date_from, date_to)
    if not profile:
        raise HTTPException(status_code=404, detail="Master not found")
    return profile


@router.patch("/masters/{master_id}/promote")
async def admin_promote(master_id: int, _admin=Depends(require_admin)):
    result = await set_user_role(master_id, "master")
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return result


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
    return await get_financial_report(master_id, date_from, date_to)


@router.get("/financials/export")
async def admin_financials_export(
    master_id: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    export_format: str = Query("xlsx", pattern="^(xlsx|pdf)$"),
    _admin=Depends(require_admin),
):
    report = await get_financial_report(master_id, date_from, date_to)
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

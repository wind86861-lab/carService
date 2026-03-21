from datetime import date, datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query

from bot.database.models import get_financial_summary_by_master, get_orders_by_master
from web.auth import require_master

router = APIRouter(tags=["financials"])


def _parse_period(period: str, from_date: Optional[str], to_date: Optional[str]):
    now = datetime.now()
    if period == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif period == "week":
        start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif period == "month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif period == "custom" and from_date and to_date:
        start = datetime.fromisoformat(from_date).replace(hour=0, minute=0, second=0, microsecond=0)
        end = datetime.fromisoformat(to_date).replace(hour=23, minute=59, second=59, microsecond=999999)
    else:
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = now
    return start, end


@router.get("/financials/summary")
async def financial_summary(
    period: str = Query("month"),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    master=Depends(require_master),
):
    start, end = _parse_period(period, from_date, to_date)
    summary = await get_financial_summary_by_master(master["id"], start, end)
    if not summary:
        return {"order_count": 0, "total_price": 0, "total_parts": 0, "total_profit": 0, "total_master_share": 0}
    return {
        "order_count": summary["order_count"],
        "total_price": float(summary["total_price"]),
        "total_parts": float(summary["total_parts"]),
        "total_profit": float(summary["total_profit"]),
        "total_master_share": float(summary["total_master_share"]),
    }


@router.get("/financials/orders")
async def financial_orders(
    period: str = Query("month"),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    master=Depends(require_master),
):
    start, end = _parse_period(period, from_date, to_date)
    all_orders = await get_orders_by_master(master["id"], status="closed")
    result = []
    for o in all_orders:
        closed_at = o.get("closed_at")
        if closed_at:
            closed_naive = closed_at.replace(tzinfo=None) if closed_at.tzinfo else closed_at
            if start <= closed_naive <= end:
                result.append({
                    "order_number": o["order_number"],
                    "brand": o.get("brand"),
                    "model": o.get("model"),
                    "plate": o.get("plate"),
                    "agreed_price": float(o.get("agreed_price") or 0),
                    "parts_cost": float(o.get("parts_cost") or 0),
                    "profit": float(o.get("profit") or 0),
                    "master_share": float(o.get("master_share") or 0),
                    "closed_at": o["closed_at"],
                })
    return result

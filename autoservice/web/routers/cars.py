from fastapi import APIRouter, Depends

from bot.database.models import get_orders_by_plate
from web.auth import require_master

router = APIRouter(tags=["cars"])


@router.get("/cars/plate/{plate}")
async def car_history(plate: str, master=Depends(require_master)):
    """Return all previous orders for a given plate number."""
    orders = await get_orders_by_plate(plate)
    return [dict(o) for o in orders]

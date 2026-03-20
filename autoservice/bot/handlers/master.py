import logging
import math

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from bot.config import WEB_URL
from bot.database.models import (
    get_financial_summary_by_master,
    get_order_detail,
    get_orders_by_master,
    update_order_status,
)
from bot.keyboards.inline import (
    get_master_order_detail_keyboard,
    get_master_order_list_keyboard,
)
from bot.keyboards.reply import get_main_keyboard
from bot.utils.formatters import format_datetime, format_money, format_order_status

logger = logging.getLogger(__name__)

router = Router()

_PAGE = 8
_ACTIVE = ["new", "preparation", "in_process", "ready"]


# ---------------------------------------------------------------------------
# New Order (web redirect)
# ---------------------------------------------------------------------------

@router.message(F.text == "🆕 Yangi buyurtma")
async def master_new_order_handler(message: Message, db_user: dict):
    url = f"{WEB_URL}/new-order"
    await message.answer(
        f"🆕 <b>Yangi buyurtma yaratish</b>\n\nYangi buyurtma yaratish uchun veb panelni oching:\n{url}",
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


# ---------------------------------------------------------------------------
# My Orders — paginated inline list
# ---------------------------------------------------------------------------

async def _build_order_list_message(master_id: int, page: int = 1):
    all_orders = await get_orders_by_master(master_id)
    active = [dict(o) for o in all_orders if o["status"] in _ACTIVE]
    total = len(active)
    total_pages = max(1, math.ceil(total / _PAGE))
    page = max(1, min(page, total_pages))
    page_items = active[(page - 1) * _PAGE: page * _PAGE]
    return active, page_items, total, total_pages, page


@router.message(F.text == "📋 Mening buyurtmalarim")
async def master_my_orders_handler(message: Message, db_user: dict):
    if not isinstance(db_user, dict) or db_user.get("role") not in ("master", "admin"):
        return
    active, page_items, total, total_pages, page = await _build_order_list_message(db_user["id"])
    if not active:
        await message.answer("📋 <b>Faol buyurtmalar yo'q.</b>", parse_mode="HTML")
        return
    await message.answer(
        f"📋 <b>Mening buyurtmalarim</b> ({total} ta faol)\nSahifa {page}/{total_pages}",
        parse_mode="HTML",
        reply_markup=get_master_order_list_keyboard(page_items, page, total_pages),
    )


@router.callback_query(F.data.startswith("mst_order_page:"))
async def master_orders_page_callback(callback: CallbackQuery, db_user: dict):
    if not isinstance(db_user, dict) or db_user.get("role") not in ("master", "admin"):
        await callback.answer("Ruxsat yo'q.")
        return
    page = int(callback.data.split(":")[1])
    active, page_items, total, total_pages, page = await _build_order_list_message(db_user["id"], page)
    await callback.message.edit_text(
        f"📋 <b>Mening buyurtmalarim</b> ({total} ta faol)\nSahifa {page}/{total_pages}",
        parse_mode="HTML",
        reply_markup=get_master_order_list_keyboard(page_items, page, total_pages),
    )
    await callback.answer()


@router.callback_query(F.data == "mst_orders_back")
async def master_orders_back_callback(callback: CallbackQuery, db_user: dict):
    if not isinstance(db_user, dict) or db_user.get("role") not in ("master", "admin"):
        await callback.answer("Ruxsat yo'q.")
        return
    active, page_items, total, total_pages, _ = await _build_order_list_message(db_user["id"])
    await callback.message.edit_text(
        f"📋 <b>Mening buyurtmalarim</b> ({total} ta faol)\nSahifa 1/{total_pages}",
        parse_mode="HTML",
        reply_markup=get_master_order_list_keyboard(page_items, 1, total_pages),
    )
    await callback.answer()


# ---------------------------------------------------------------------------
# Order detail
# ---------------------------------------------------------------------------

def _format_order_detail(order: dict) -> str:
    car = f"{order.get('brand', '') or ''} {order.get('model', '') or ''}".strip() or "—"
    client = order.get("client_full_name") or order.get("client_name") or "—"
    txt = (
        f"📋 <b>{order['order_number']}</b>\n"
        f"Holat: {format_order_status(order['status'])}\n"
        f"Mashina: {car} | {order.get('plate', '—')}\n"
        f"Mijoz: {client}\n"
        f"Muammo: {order.get('problem') or '—'}\n"
        f"Ish tavsifi: {order.get('work_desc') or '—'}\n"
        f"Narx: {format_money(order.get('agreed_price', 0))}\n"
        f"Sana: {format_datetime(order.get('created_at'))}"
    )
    return txt


@router.callback_query(F.data.startswith("mst_order_view:"))
async def master_order_view_callback(callback: CallbackQuery, db_user: dict):
    if not isinstance(db_user, dict) or db_user.get("role") not in ("master", "admin"):
        await callback.answer("Ruxsat yo'q.")
        return
    order_number = callback.data.split(":", 1)[1]
    order = await get_order_detail(order_number)
    if not order:
        await callback.answer("Buyurtma topilmadi.")
        return
    order = dict(order)
    await callback.message.edit_text(
        _format_order_detail(order),
        parse_mode="HTML",
        reply_markup=get_master_order_detail_keyboard(order["order_number"], order["status"]),
    )
    await callback.answer()


# ---------------------------------------------------------------------------
# Status change
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("mst_status:"))
async def master_status_change_callback(callback: CallbackQuery, db_user: dict):
    if not isinstance(db_user, dict) or db_user.get("role") not in ("master", "admin"):
        await callback.answer("Ruxsat yo'q.")
        return
    parts = callback.data.split(":")
    order_number = parts[1]
    new_status = parts[2]

    valid = {"new": "preparation", "preparation": "in_process", "in_process": "ready"}
    order_now = await get_order_detail(order_number)
    if not order_now:
        await callback.answer("Buyurtma topilmadi.")
        return
    current = order_now["status"]
    if valid.get(current) != new_status:
        await callback.answer("Bu holat o'zgartirib bo'lmaydi.")
        return

    try:
        await update_order_status(
            order_number, new_status,
            note=f"Master changed status to {new_status}",
            changed_by=db_user["id"],
        )
    except Exception:
        logger.exception("Failed to update order status")
        await callback.answer("❌ Xato yuz berdi.")
        return

    order = await get_order_detail(order_number)
    order = dict(order)
    await callback.message.edit_text(
        f"✅ Holat yangilandi!\n\n" + _format_order_detail(order),
        parse_mode="HTML",
        reply_markup=get_master_order_detail_keyboard(order["order_number"], order["status"]),
    )
    await callback.answer("✅ Holat yangilandi!")


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

@router.message(F.text == "📊 Statistika")
async def master_statistics_handler(message: Message, db_user: dict):
    from datetime import datetime
    now = datetime.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    summary = await get_financial_summary_by_master(db_user["id"], month_start, now)

    if not summary or summary["order_count"] == 0:
        await message.answer("Bu oy hali yopilgan buyurtmalar yo'q.")
        return

    txt = (
        "📊 <b>Shu oygi statistikangiz:</b>\n\n"
        f"Yopilgan buyurtmalar: <b>{summary['order_count']}</b>\n"
        f"Jami daromad:         <b>{format_money(summary['total_price'])}</b>\n"
        f"Ehtiyot qismlar:      <b>{format_money(summary['total_parts'])}</b>\n"
        f"Foyda:                <b>{format_money(summary['total_profit'])}</b>\n"
        f"Sizning ulushingiz:   <b>{format_money(summary['total_master_share'])}</b>"
    )
    await message.answer(txt, parse_mode="HTML")

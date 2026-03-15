from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import MagicData

from bot.config import BOT_USERNAME, WEB_URL
from bot.database.models import get_financial_summary_by_master, get_orders_by_master
from bot.utils.formatters import format_money, format_order_status

router = Router()
router.message.filter(MagicData(F.db_user["role"] == "master"))


@router.message(F.text == "New Order")
async def master_new_order_handler(message: Message, db_user: dict):
    url = f"{WEB_URL}/new-order"
    await message.answer(
        f"Open the web interface to create a new order:\n\n"
        f"<a href='{url}'>{url}</a>",
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


@router.message(F.text == "My Orders")
async def master_my_orders_handler(message: Message, db_user: dict):
    active_statuses = ["new", "preparation", "in_process", "ready"]
    orders = await get_orders_by_master(db_user["id"])
    active = [o for o in orders if o["status"] in active_statuses]

    if not active:
        url = f"{WEB_URL}/dashboard"
        await message.answer(
            f"You have no active orders.\n\nView all orders on the dashboard:\n<a href='{url}'>{url}</a>",
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
        return

    lines = [f"<b>Your active orders ({len(active)}):</b>\n"]
    for o in active[:5]:
        car = f"{o.get('brand', '')} {o.get('model', '')}".strip() or "—"
        lines.append(f"• <b>{o['order_number']}</b> | {car} | {format_order_status(o['status'])}")

    if len(active) > 5:
        lines.append(f"... and {len(active) - 5} more")

    url = f"{WEB_URL}/dashboard"
    lines.append(f"\n<a href='{url}'>Open full dashboard →</a>")
    await message.answer("\n".join(lines), parse_mode="HTML", disable_web_page_preview=True)


@router.message(F.text == "Statistics")
async def master_statistics_handler(message: Message, db_user: dict):
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    summary = await get_financial_summary_by_master(db_user["id"], month_start, now)

    if not summary or summary["order_count"] == 0:
        await message.answer("No closed orders this month yet.")
        return

    url = f"{WEB_URL}/statistics"
    text = (
        "<b>📊 Your statistics this month:</b>\n\n"
        f"Orders closed:   <b>{summary['order_count']}</b>\n"
        f"Total revenue:   <b>{format_money(summary['total_price'])}</b>\n"
        f"Parts cost:      <b>{format_money(summary['total_parts'])}</b>\n"
        f"Profit:          <b>{format_money(summary['total_profit'])}</b>\n"
        f"Your share:      <b>{format_money(summary['total_master_share'])}</b>\n\n"
        f"<a href='{url}'>View full statistics →</a>"
    )
    await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)

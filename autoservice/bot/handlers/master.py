from aiogram import Router, F
from aiogram.types import Message

from bot.config import BOT_USERNAME, WEB_URL
from bot.database.models import get_financial_summary_by_master, get_orders_by_master
from bot.utils.formatters import format_money, format_order_status

router = Router()


async def _is_master(message: Message, db_user: dict) -> bool:
    return isinstance(db_user, dict) and db_user.get("role") == "master"


@router.message(F.text == "🆕 Yangi buyurtma")
async def master_new_order_handler(message: Message, db_user: dict):
    url = f"{WEB_URL}/new-order"
    await message.answer(
        f"🆕 <b>Yangi buyurtma yaratish</b>\n\nYangi buyurtma yaratish uchun veb panelni oching:\n{url}",
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


@router.message(F.text == "📋 Mening buyurtmalarim", _is_master)
async def master_my_orders_handler(message: Message, db_user: dict):
    active_statuses = ["new", "preparation", "in_process", "ready"]
    orders = await get_orders_by_master(db_user["id"])
    active = [o for o in orders if o["status"] in active_statuses]

    if not active:
        url = f"{WEB_URL}/dashboard"
        await message.answer(
            f"Faol buyurtmalaringiz yo'q.\n\nBarcha buyurtmalarni ko'rish uchun:\n<a href='{url}'>{url}</a>",
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
        return

    lines = [f"<b>Faol buyurtmalaringiz ({len(active)}):</b>\n"]
    for o in active[:5]:
        car = f"{o.get('brand', '')} {o.get('model', '')}".strip() or "—"
        lines.append(f"• <b>{o['order_number']}</b> | {car} | {format_order_status(o['status'])}")

    if len(active) > 5:
        lines.append(f"... va yana {len(active) - 5} ta")

    url = f"{WEB_URL}/dashboard"
    lines.append(f"\n<a href='{url}'>To'liq boshqaruv panelini ochish \u2192</a>")
    await message.answer("\n".join(lines), parse_mode="HTML", disable_web_page_preview=True)


@router.message(F.text == "📊 Statistika")
async def master_statistics_handler(message: Message, db_user: dict):
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    summary = await get_financial_summary_by_master(db_user["id"], month_start, now)

    if not summary or summary["order_count"] == 0:
        await message.answer("Bu oy hali yopilgan buyurtmalar yo'q.")
        return

    url = f"{WEB_URL}/statistics"
    text = (
        "<b>\ud83d\udcca Shu oygi statistikangiz:</b>\n\n"
        f"Yopilgan buyurtmalar: <b>{summary['order_count']}</b>\n"
        f"Jami daromad:         <b>{format_money(summary['total_price'])}</b>\n"
        f"Ehtiyot qismlar:      <b>{format_money(summary['total_parts'])}</b>\n"
        f"Foyda:                <b>{format_money(summary['total_profit'])}</b>\n"
        f"Sizning ulushingiz:   <b>{format_money(summary['total_master_share'])}</b>\n\n"
        f"<a href='{url}'>To'liq statistikani ko'rish \u2192</a>"
    )
    await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)

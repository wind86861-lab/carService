import logging

from aiogram import F, Router
from aiogram.filters import MagicData, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config import WEB_URL
from bot.database.models import get_dashboard_stats
from bot.keyboards.inline import get_broadcast_confirm_keyboard, get_broadcast_target_keyboard
from bot.states import AdminBroadcast
from bot.utils.formatters import format_money

logger = logging.getLogger(__name__)

router = Router()
router.message.filter(MagicData(F.db_user["role"] == "admin"))
router.callback_query.filter(MagicData(F.db_user["role"] == "admin"))


@router.message(F.text == "📊 Boshqaruv paneli")
async def admin_dashboard_handler(message: Message, db_user: dict):
    try:
        stats = await get_dashboard_stats()
        text = (
            "<b>📊 Boshqaruv paneli</b>\n\n"
            f"🔄 Faol buyurtmalar: <b>{stats['active_orders']}</b>\n"
            f"✅ Tayyor buyurtmalar: <b>{stats['ready_orders']}</b>\n\n"
            f"💰 Shu oy daromad: <b>{format_money(stats['month_revenue'])}</b>\n"
            f"📈 Shu oy foyda: <b>{format_money(stats['month_profit'])}</b>\n\n"
            f"👤 Faol mijozlar: <b>{stats['total_clients']}</b>\n"
            f"🔧 Faol ustalar: <b>{stats['total_masters']}</b>\n\n"
            f"<a href='{WEB_URL}/admin'>Admin panelni ochish →</a>"
        )
    except Exception:
        logger.exception("Failed to load dashboard stats")
        text = f"Admin panel: {WEB_URL}/admin"
    await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)


@router.message(F.text == "📋 Barcha buyurtmalar")
async def admin_all_orders_handler(message: Message, db_user: dict):
    await message.answer(
        f"📋 <b>Barcha buyurtmalar</b>\n\nBarcha buyurtmalarni boshqarish uchun admin panelni oching:\n{WEB_URL}/admin/orders",
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


@router.message(F.text == "👥 Mijozlar")
async def admin_clients_handler(message: Message, db_user: dict):
    await message.answer(
        f"👥 <b>Mijozlarni boshqarish</b>\n\nMijozlarni boshqarish uchun admin panelni oching:\n{WEB_URL}/admin/clients",
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


@router.message(F.text == "🔧 Ustalar")
async def admin_masters_handler(message: Message, db_user: dict):
    await message.answer(
        f"🔧 <b>Ustalarni boshqarish</b>\n\nUstalarni boshqarish uchun admin panelni oching:\n{WEB_URL}/admin/masters",
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


@router.message(F.text == "📢 Xabar yuborish")
async def admin_broadcast_handler(message: Message, state: FSMContext):
    await state.set_state(AdminBroadcast.waiting_for_target)
    await message.answer(
        "📢 <b>Ommaviy xabar</b>\n\nMaqsadli auditoriyani tanlang:",
        parse_mode="HTML",
        reply_markup=get_broadcast_target_keyboard(),
    )


@router.callback_query(F.data.startswith("broadcast_target:"), AdminBroadcast.waiting_for_target)
async def admin_broadcast_target_callback(callback: CallbackQuery, state: FSMContext):
    target = callback.data.split(":", 1)[1]
    labels = {"all": "All Users", "clients": "Clients Only", "masters": "Masters Only"}
    await state.update_data(target=target)
    await state.set_state(AdminBroadcast.waiting_for_message)
    await callback.message.edit_text(
        f"Target: <b>{labels.get(target, target)}</b>\n\nNow type the message to send:",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminBroadcast.waiting_for_message)
async def admin_broadcast_message_handler(message: Message, state: FSMContext):
    await state.update_data(message_text=message.text)
    await state.set_state(AdminBroadcast.waiting_for_confirm)
    data = await state.get_data()
    labels = {"all": "All Users", "clients": "Clients Only", "masters": "Masters Only"}
    preview = (
        f"📢 <b>Confirm Broadcast</b>\n\n"
        f"Target: <b>{labels.get(data['target'], data['target'])}</b>\n\n"
        f"Message preview:\n<i>{message.text[:500]}</i>\n\n"
        "Send this message?"
    )
    await message.answer(preview, parse_mode="HTML", reply_markup=get_broadcast_confirm_keyboard())


@router.callback_query(F.data == "broadcast_confirm", AdminBroadcast.waiting_for_confirm)
async def admin_broadcast_confirm_callback(callback: CallbackQuery, state: FSMContext, db_user: dict):
    data = await state.get_data()
    await state.clear()
    await callback.message.edit_text("⏳ Sending broadcast…")
    try:
        from web.utils.broadcast import send_broadcast
        result = await send_broadcast(data["target"], data["message_text"], db_user["id"])
        await callback.message.edit_text(
            f"✅ <b>Broadcast sent!</b>\n\n"
            f"Delivered: <b>{result['sent_count']}</b>\n"
            f"Failed: <b>{result['failed_count']}</b>",
            parse_mode="HTML",
        )
    except Exception:
        logger.exception("Broadcast failed")
        await callback.message.edit_text("❌ Broadcast failed. Check logs.")
    await callback.answer()


@router.callback_query(F.data == "broadcast_cancel", AdminBroadcast.waiting_for_confirm)
async def admin_broadcast_cancel_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Broadcast cancelled.")
    await callback.answer()

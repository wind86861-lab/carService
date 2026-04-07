import asyncio
import logging

from aiogram import Bot

from bot.database.models import (
    get_feedback_by_order,
    get_user_by_telegram_id,
    get_users_by_role,
)
from bot.i18n import t, lang_of
from bot.keyboards.inline import get_confirmation_keyboard, get_rating_keyboard
from bot.utils.formatters import format_order_status

logger = logging.getLogger(__name__)


def _q():
    from bot.utils.notification_queue import notification_queue
    return notification_queue


async def _lang_for(telegram_id: int) -> str:
    """Look up a user's language preference by telegram_id."""
    try:
        user = await get_user_by_telegram_id(telegram_id)
        return lang_of(user) if user else "uz"
    except Exception:
        return "uz"


def notify_client_status_changed(
    client_telegram_id: int,
    order_number: str,
    new_status: str,
    car_info: str,
    lang: str = "uz",
) -> None:
    """Enqueue a status-change notification to the client."""
    key_map = {
        "preparation": "notif_preparation",
        "in_process": "notif_in_process",
        "ready": "notif_ready",
    }
    key = key_map.get(new_status, "notif_status_generic")
    if key == "notif_status_generic":
        text = t(key, lang, order_number=order_number, status=format_order_status(new_status))
    else:
        text = t(key, lang, order_number=order_number, car_info=car_info)
    _q().enqueue(telegram_id=client_telegram_id, message=text)


def notify_client_receipt_request(
    client_telegram_id: int, order_number: str,
    car_info: str = "—", agreed_price: str = "0",
    paid_amount: str = "0", remaining: str = "0",
    lang: str = "uz",
) -> None:
    """Enqueue the receipt confirmation message with confirmation keyboard."""
    text = t("notif_receipt_request", lang,
             order_number=order_number, car_info=car_info,
             agreed_price=agreed_price, paid_amount=paid_amount,
             remaining=remaining)
    _q().enqueue(
        telegram_id=client_telegram_id,
        message=text,
        reply_markup=get_confirmation_keyboard(order_number, remaining=remaining, lang=lang),
    )


def notify_master_receipt_confirmed(
    master_telegram_id: int, order_number: str,
    paid_amount: str = "0", lang: str = "uz",
) -> None:
    """Enqueue notification to master that client confirmed receipt."""
    _q().enqueue(
        telegram_id=master_telegram_id,
        message=t("notif_master_receipt_confirmed", lang,
                   order_number=order_number, paid_amount=paid_amount),
    )


def notify_master_dispute(
    master_telegram_id: int, order_number: str, client_name: str, lang: str = "uz"
) -> None:
    """Enqueue dispute notification to master."""
    _q().enqueue(
        telegram_id=master_telegram_id,
        message=t("notif_master_dispute", lang, order_number=order_number, client_name=client_name),
    )


async def notify_admin_dispute(order_number: str, client_name: str, master_name: str) -> None:
    """Enqueue dispute notification to all admins (always UZ + RU)."""
    try:
        admins = await get_users_by_role("admin")
        for admin in admins:
            lang = lang_of(admin)
            text = (
                f"⚠️ <b>{'Shikoyat' if lang == 'uz' else 'Жалоба'} — {order_number}</b>\n\n"
                f"{'Mijoz' if lang == 'uz' else 'Клиент'}: {client_name}\n"
                f"{'Usta' if lang == 'uz' else 'Мастер'}: {master_name}\n\n"
                f"{'Mijoz buyurtma yopilgandan so\'ng muammo haqida xabar berdi.' if lang == 'uz' else 'Клиент сообщил о проблеме после завершения заказа.'}"
            )
            _q().enqueue(telegram_id=admin["telegram_id"], message=text)
    except Exception:
        logger.exception("Failed to fetch admins for dispute notification")


def notify_master_dispute_with_text(
    master_telegram_id: int, order_number: str, client_name: str, issue_text: str, lang: str = "uz"
) -> None:
    """Enqueue dispute notification to master with client's issue description."""
    _q().enqueue(
        telegram_id=master_telegram_id,
        message=t("notif_master_dispute_text", lang,
                   order_number=order_number, client_name=client_name, issue_text=issue_text),
    )


async def notify_admin_dispute_with_text(
    order_number: str, client_name: str, master_name: str, issue_text: str
) -> None:
    """Enqueue dispute notification with issue text to all admins and admin group."""
    try:
        admins = await get_users_by_role("admin")
        for admin in admins:
            lang = lang_of(admin)
            header = "Shikoyat" if lang == "uz" else "Жалоба"
            client_lbl = "Mijoz" if lang == "uz" else "Клиент"
            master_lbl = "Usta" if lang == "uz" else "Мастер"
            issue_lbl = "Muammo" if lang == "uz" else "Проблема"
            text = (
                f"⚠️ <b>{header} — {order_number}</b>\n\n"
                f"{client_lbl}: {client_name}\n"
                f"{master_lbl}: {master_name}\n"
                f"{issue_lbl}: <i>{issue_text}</i>\n\n"
                f"{'Buyurtma holati «jarayonda» ga qaytarildi.' if lang == 'uz' else 'Статус заказа возвращён на «в процессе».'}'"
            )
            _q().enqueue(telegram_id=admin["telegram_id"], message=text)
        
        # Also send to admin group chat if configured
        from bot.config import ADMIN_GROUP_CHAT_ID
        if ADMIN_GROUP_CHAT_ID:
            group_text = (
                f"⚠️ <b>SHIKOYAT — {order_number}</b>\n\n"
                f"Mijoz: {client_name}\n"
                f"Usta: {master_name}\n"
                f"Muammo: <i>{issue_text}</i>\n\n"
                f"⚡ Buyurtma holati «jarayonda» ga qaytarildi.\n"
                f"Iltimos, mijoz bilan bog'laning!"
            )
            _q().enqueue(telegram_id=int(ADMIN_GROUP_CHAT_ID), message=group_text)
    except Exception:
        logger.exception("Failed to fetch admins for dispute notification")


async def schedule_feedback_request(
    bot: Bot, client_telegram_id: int, order_id: int, order_number: str, dp
) -> None:
    """Schedule a feedback request one hour after order closure via the queue."""
    async def _send_feedback():
        await asyncio.sleep(3600)
        try:
            existing = await get_feedback_by_order(order_id)
            if existing:
                return

            lang = await _lang_for(client_telegram_id)

            from aiogram.fsm.context import FSMContext
            from aiogram.fsm.storage.base import StorageKey
            storage_key = StorageKey(
                bot_id=bot.id,
                chat_id=client_telegram_id,
                user_id=client_telegram_id,
            )
            state = FSMContext(storage=dp.storage, key=storage_key)
            await state.update_data(feedback_order_id=order_id)

            _q().enqueue(
                telegram_id=client_telegram_id,
                message=t("feedback_request", lang, order_number=order_number),
                reply_markup=get_rating_keyboard(),
            )
        except Exception:
            logger.exception("Failed to schedule feedback request for client %s", client_telegram_id)

    asyncio.create_task(_send_feedback())

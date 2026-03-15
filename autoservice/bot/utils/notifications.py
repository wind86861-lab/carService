import asyncio
import logging

from aiogram import Bot

from bot.database.models import (
    get_feedback_by_order,
    get_users_by_role,
)
from bot.keyboards.inline import get_confirmation_keyboard, get_rating_keyboard
from bot.utils.formatters import format_order_status

logger = logging.getLogger(__name__)


def _q():
    from bot.utils.notification_queue import notification_queue
    return notification_queue


def notify_client_status_changed(
    client_telegram_id: int,
    order_number: str,
    new_status: str,
    car_info: str,
) -> None:
    """Enqueue a status-change notification to the client."""
    status_messages = {
        "preparation": (
            f"🔧 <b>Order {order_number}</b> ({car_info})\n\n"
            "Your car repair has started. We are preparing for the work."
        ),
        "in_process": (
            f"⚙️ <b>Order {order_number}</b> ({car_info})\n\n"
            "Work on your car is currently in progress."
        ),
        "ready": (
            f"✅ <b>Order {order_number}</b> ({car_info})\n\n"
            "Your car is ready. You can come pick it up."
        ),
    }
    text = status_messages.get(new_status) or (
        f"<b>Order {order_number}</b> ({car_info})\n\n"
        f"Status updated to: {format_order_status(new_status)}"
    )
    _q().enqueue(telegram_id=client_telegram_id, message=text)


def notify_client_receipt_request(client_telegram_id: int, order_number: str) -> None:
    """Enqueue the receipt confirmation message with confirmation keyboard."""
    text = (
        f"<b>Order {order_number}</b>\n\n"
        "The master has marked your order as complete. "
        "Have you received your car?"
    )
    _q().enqueue(
        telegram_id=client_telegram_id,
        message=text,
        reply_markup=get_confirmation_keyboard(order_number),
    )


def notify_master_receipt_confirmed(master_telegram_id: int, order_number: str) -> None:
    """Enqueue notification to master that client confirmed receipt."""
    _q().enqueue(
        telegram_id=master_telegram_id,
        message=(
            f"✅ <b>Order {order_number}</b>\n\n"
            "The client has confirmed receipt. The order is now fully closed."
        ),
    )


def notify_master_dispute(master_telegram_id: int, order_number: str, client_name: str) -> None:
    """Enqueue dispute notification to master."""
    _q().enqueue(
        telegram_id=master_telegram_id,
        message=(
            f"⚠️ <b>Order {order_number}</b>\n\n"
            f"Client {client_name} reported a problem with the order. "
            "Please contact them to resolve the issue."
        ),
    )


async def notify_admin_dispute(order_number: str, client_name: str, master_name: str) -> None:
    """Enqueue dispute notification to all admins."""
    text = (
        f"⚠️ <b>Dispute — Order {order_number}</b>\n\n"
        f"Client: {client_name}\n"
        f"Master: {master_name}\n\n"
        "The client reported a problem after order completion."
    )
    try:
        admins = await get_users_by_role("admin")
        for admin in admins:
            _q().enqueue(telegram_id=admin["telegram_id"], message=text)
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
                message=(
                    f"<b>Order {order_number}</b>\n\n"
                    "How would you rate our service? Please select a score from 1 to 10."
                ),
                reply_markup=get_rating_keyboard(),
            )
        except Exception:
            logger.exception("Failed to schedule feedback request for client %s", client_telegram_id)

    asyncio.create_task(_send_feedback())

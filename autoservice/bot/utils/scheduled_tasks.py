import asyncio
import logging

from aiogram import Bot

logger = logging.getLogger(__name__)

_feedback_sent: set[int] = set()


async def feedback_scheduler(bot: Bot, dp):
    """Poll every 60 seconds and send rating keyboard to clients with closed-but-unrated orders."""
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.storage.base import StorageKey
    from bot.database.models import get_orders_closed_without_feedback
    from bot.keyboards.inline import get_rating_keyboard

    while True:
        try:
            orders = await get_orders_closed_without_feedback()
            for order in orders:
                order_id = order["id"]
                if order_id in _feedback_sent:
                    continue
                client_tg_id = order["client_telegram_id"]
                try:
                    storage_key = StorageKey(
                        bot_id=bot.id,
                        chat_id=client_tg_id,
                        user_id=client_tg_id,
                    )
                    state = FSMContext(storage=dp.storage, key=storage_key)
                    await state.update_data(feedback_order_id=order_id)

                    await bot.send_message(
                        client_tg_id,
                        f"<b>Order {order['order_number']}</b>\n\n"
                        "How would you rate our service? Please select a score from 1 to 10.",
                        parse_mode="HTML",
                        reply_markup=get_rating_keyboard(),
                    )
                    _feedback_sent.add(order_id)
                    logger.info("Sent feedback request for order %s to user %s", order["order_number"], client_tg_id)
                except Exception:
                    logger.exception("Failed to send feedback for order %s", order["order_number"])
        except Exception:
            logger.exception("Error in feedback_scheduler")
        await asyncio.sleep(60)


async def auto_confirm_scheduler(bot: Bot):
    """Poll every hour and auto-confirm orders with no client response after 72 hours."""
    from bot.database.models import auto_confirm_order, get_orders_pending_auto_confirm

    while True:
        try:
            orders = await get_orders_pending_auto_confirm()
            for order in orders:
                try:
                    await auto_confirm_order(order["order_number"])
                    client_tg_id = order["client_telegram_id"]
                    await bot.send_message(
                        client_tg_id,
                        f"<b>Order {order['order_number']}</b>\n\n"
                        "Your order has been automatically confirmed after 72 hours. "
                        "Thank you for using AutoService!",
                        parse_mode="HTML",
                    )
                    logger.info("Auto-confirmed order %s", order["order_number"])
                except Exception:
                    logger.exception("Failed to auto-confirm order %s", order["order_number"])
        except Exception:
            logger.exception("Error in auto_confirm_scheduler")
        await asyncio.sleep(3600)

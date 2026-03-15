import asyncio
import logging

from aiogram import Bot

from bot.database.models import (
    get_feedback_by_order,
    get_masters_with_unlinked_ready_orders,
    get_orders_closed_without_feedback,
    get_orders_pending_auto_confirm,
    auto_confirm_order,
)
from bot.keyboards.inline import get_rating_keyboard
from bot.utils.notification_queue import notification_queue

logger = logging.getLogger(__name__)


class Scheduler:
    """Replaces the separate scheduled_tasks polling loops from Step 4."""

    def __init__(self):
        self._seen_feedback: set[int] = set()

    def start(self, bot: Bot, dp) -> None:
        asyncio.create_task(self._feedback_loop(bot, dp))
        asyncio.create_task(self._auto_confirm_loop(bot))
        asyncio.create_task(self._unlinked_ready_loop(bot))
        logger.info("Scheduler started (3 tasks)")

    async def _feedback_loop(self, bot: Bot, dp) -> None:
        """Every 60 s: send rating keyboard to clients who haven't rated yet."""
        while True:
            await asyncio.sleep(60)
            try:
                orders = await get_orders_closed_without_feedback()
                for row in orders:
                    order_id = row["id"]
                    if order_id in self._seen_feedback:
                        continue
                    existing = await get_feedback_by_order(order_id)
                    if existing:
                        self._seen_feedback.add(order_id)
                        continue
                    client_tid = row.get("client_telegram_id")
                    if not client_tid:
                        self._seen_feedback.add(order_id)
                        continue

                    from aiogram.fsm.context import FSMContext
                    from aiogram.fsm.storage.base import StorageKey
                    storage_key = StorageKey(
                        bot_id=bot.id, chat_id=client_tid, user_id=client_tid
                    )
                    state = FSMContext(storage=dp.storage, key=storage_key)
                    await state.update_data(feedback_order_id=order_id)

                    notification_queue.enqueue(
                        telegram_id=client_tid,
                        message=(
                            f"<b>Order {row['order_number']}</b>\n\n"
                            "How would you rate our service? Please select a score from 1 to 10."
                        ),
                        reply_markup=get_rating_keyboard(),
                    )
                    self._seen_feedback.add(order_id)
            except Exception:
                logger.exception("feedback_loop error")

    async def _auto_confirm_loop(self, bot: Bot) -> None:
        """Every hour: auto-confirm orders closed more than 72 h ago."""
        while True:
            await asyncio.sleep(3600)
            try:
                orders = await get_orders_pending_auto_confirm()
                for row in orders:
                    await auto_confirm_order(row["order_number"])
                    client_tid = row.get("client_telegram_id")
                    if client_tid:
                        notification_queue.enqueue(
                            telegram_id=client_tid,
                            message=(
                                f"<b>Order {row['order_number']}</b>\n\n"
                                "Your order has been automatically confirmed after 72 hours. "
                                "Thank you for using our service!"
                            ),
                        )
                    logger.info("Auto-confirmed order %s", row["order_number"])
            except Exception:
                logger.exception("auto_confirm_loop error")

    async def _unlinked_ready_loop(self, bot: Bot) -> None:
        """Every hour: remind masters of ready orders with no linked client after 24 h."""
        while True:
            await asyncio.sleep(3600)
            try:
                rows = await get_masters_with_unlinked_ready_orders()
                for row in rows:
                    master_tid = row.get("master_telegram_id")
                    if master_tid:
                        notification_queue.enqueue(
                            telegram_id=master_tid,
                            message=(
                                f"⚠️ <b>Order {row['order_number']}</b>\n\n"
                                "This order has been ready for over 24 hours, "
                                "but no client has connected yet. "
                                "Please send them the invite link."
                            ),
                        )
            except Exception:
                logger.exception("unlinked_ready_loop error")

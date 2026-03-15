import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter

logger = logging.getLogger(__name__)


class NotificationQueue:
    """Thread-safe queue for sending Telegram notifications with retry logic."""

    def __init__(self):
        self._queue: asyncio.Queue = asyncio.Queue()

    def enqueue(
        self,
        telegram_id: int,
        message: str,
        reply_markup=None,
        parse_mode: str = "HTML",
    ) -> None:
        """Non-blocking enqueue of a notification job."""
        self._queue.put_nowait(
            {
                "telegram_id": telegram_id,
                "message": message,
                "reply_markup": reply_markup,
                "parse_mode": parse_mode,
            }
        )

    async def worker(self, bot: Bot) -> None:
        """Consume jobs forever. Handles rate limits and forbidden errors gracefully."""
        while True:
            job = await self._queue.get()
            tid = job["telegram_id"]
            try:
                await bot.send_message(
                    tid,
                    job["message"],
                    parse_mode=job.get("parse_mode", "HTML"),
                    reply_markup=job.get("reply_markup"),
                )
            except TelegramForbiddenError:
                logger.warning("User %s has blocked the bot — skipping notification", tid)
            except TelegramRetryAfter as e:
                logger.warning("Rate limit hit, retrying after %s s", e.retry_after)
                await asyncio.sleep(e.retry_after)
                self._queue.put_nowait(job)
            except Exception:
                logger.exception("Notification to %s failed — retrying once", tid)
                await asyncio.sleep(5)
                try:
                    await bot.send_message(
                        tid,
                        job["message"],
                        parse_mode=job.get("parse_mode", "HTML"),
                        reply_markup=job.get("reply_markup"),
                    )
                except Exception:
                    logger.exception("Retry also failed for %s — discarding", tid)
            finally:
                self._queue.task_done()


notification_queue = NotificationQueue()

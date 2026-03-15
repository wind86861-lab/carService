import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import BOT_TOKEN
from bot.database.connection import close_db, init_db
from bot.handlers import admin, client, common, master
from bot.middlewares.auth import AuthMiddleware
from bot.utils.notification_queue import notification_queue
from bot.utils.scheduler import Scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def main():
    logger.info("Starting bot...")

    await init_db()
    logger.info("Database initialized.")

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())

    dp.include_router(master.router)
    dp.include_router(client.router)
    dp.include_router(admin.router)
    dp.include_router(common.router)

    await bot.delete_webhook(drop_pending_updates=True)

    asyncio.create_task(notification_queue.worker(bot))
    Scheduler().start(bot, dp)
    logger.info("Notification worker and scheduler started.")

    try:
        logger.info("Bot is polling...")
        await dp.start_polling(bot)
    finally:
        await close_db()
        await bot.session.close()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())

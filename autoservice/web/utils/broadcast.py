import asyncio
import logging

import httpx

from bot.database.models import get_all_users, get_users_by_role, get_filtered_clients, save_broadcast
from web.config import BOT_TOKEN

logger = logging.getLogger(__name__)

_TG_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


async def send_broadcast(target: str, message: str, sender_id: int, filters: dict | None = None) -> dict:
    """Send a broadcast message to the target audience and record it in the DB."""
    if target == "all":
        users = await get_all_users()
    elif target == "filtered" and filters:
        visit_count = filters.get("visit_count")
        if visit_count is not None:
            visit_count = int(visit_count) if visit_count else None
        users = await get_filtered_clients(
            date_from=filters.get("date_from"),
            date_to=filters.get("date_to"),
            visit_count=visit_count
        )
    else:
        role = "client" if target == "clients" else "master"
        users = await get_users_by_role(role)

    sent_count = 0
    failed_count = 0

    async with httpx.AsyncClient(timeout=10) as client:
        for user in users:
            tid = user.get("telegram_id")
            if not tid:
                continue
            try:
                resp = await client.post(
                    f"{_TG_API}/sendMessage",
                    json={"chat_id": tid, "text": message, "parse_mode": "HTML"},
                )
                if resp.status_code == 200:
                    sent_count += 1
                else:
                    failed_count += 1
                    logger.warning("Broadcast send failed for %s: %s", tid, resp.text)
            except Exception:
                failed_count += 1
                logger.exception("Broadcast send exception for %s", tid)
            await asyncio.sleep(0.05)

    await save_broadcast(sender_id, target, message, sent_count)
    return {"sent_count": sent_count, "failed_count": failed_count}

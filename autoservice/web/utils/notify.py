import logging

import httpx

from web.config import BOT_TOKEN
from bot.keyboards.inline import get_confirmation_keyboard, get_rating_keyboard

logger = logging.getLogger(__name__)

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


async def send_bot_notification(
    chat_id: int,
    text: str,
    reply_markup: dict | None = None,
) -> bool:
    """Send a Telegram message directly via Bot API. Returns True on success."""
    payload: dict = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        import json
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(f"{TELEGRAM_API}/sendMessage", json=payload)
            if not resp.is_success:
                logger.warning("Telegram API error %s: %s", resp.status_code, resp.text)
                return False
            return True
    except Exception:
        logger.exception("Failed to send bot notification to %s", chat_id)
        return False


def _confirmation_keyboard_dict(order_number: str, remaining: str = "0", lang: str = "uz") -> dict:
    """Serialize confirmation inline keyboard to Telegram API format."""
    kb = get_confirmation_keyboard(order_number, remaining=remaining, lang=lang)
    return {
        "inline_keyboard": [
            [{"text": btn.text, "callback_data": btn.callback_data} for btn in row]
            for row in kb.inline_keyboard
        ]
    }


async def notify_status_changed(client_telegram_id: int, order_number: str, status: str, car_info: str):
    messages = {
        "preparation": f"🔧 <b>Order {order_number}</b> ({car_info})\n\nYour car repair has started. We are preparing for the work.",
        "in_process": f"⚙️ <b>Order {order_number}</b> ({car_info})\n\nWork on your car is currently in progress.",
        "ready": f"✅ <b>Order {order_number}</b> ({car_info})\n\nYour car is ready. You can come pick it up.",
    }
    text = messages.get(status, f"<b>Order {order_number}</b>\n\nStatus updated to: {status}")
    await send_bot_notification(client_telegram_id, text)


async def notify_receipt_request(
    client_telegram_id: int, order_number: str,
    car_info: str = "—", agreed_price: str = "0",
    paid_amount: str = "0", remaining: str = "0",
):
    text = (
        f"📋 <b>Order {order_number}</b>\n"
        f"🚗 {car_info}\n\n"
        f"💰 Price: <b>{agreed_price}</b>\n"
        f"✅ Paid: <b>{paid_amount}</b>\n"
        f"💵 Remaining: <b>{remaining}</b>\n\n"
        f"Did you pay <b>{remaining}</b> and receive your car?"
    )
    keyboard = _confirmation_keyboard_dict(order_number, remaining=remaining)
    await send_bot_notification(client_telegram_id, text, reply_markup=keyboard)

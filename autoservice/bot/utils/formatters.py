from datetime import datetime
from decimal import Decimal


def format_money(amount) -> str:
    """Format a number as a readable money string, e.g. 1500000 -> '1 500 000 UZS'."""
    if amount is None:
        return "0 UZS"
    num = int(Decimal(str(amount)))
    if num < 0:
        sign = "-"
        num = -num
    else:
        sign = ""
    s = str(num)
    groups = []
    while s:
        groups.append(s[-3:])
        s = s[:-3]
    return sign + " ".join(reversed(groups)) + " UZS"


def format_datetime(dt) -> str:
    """Format a datetime as 'DD.MM.YYYY HH:MM'. Returns a dash if None."""
    if dt is None:
        return "—"
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except (ValueError, TypeError):
            return "—"
    return dt.strftime("%d.%m.%Y %H:%M")


def format_order_status(status: str) -> str:
    """Map a status string to a human-readable label with emoji."""
    mapping = {
        "new": "🆕 New",
        "preparation": "🔧 Preparation",
        "in_process": "⚙️ In Process",
        "ready": "✅ Ready",
        "closed": "🏁 Closed",
    }
    return mapping.get(status, status)


def build_order_card(order: dict, car: dict) -> str:
    """Build a formatted multi-line order status card for the client. Uses HTML parse mode."""
    car_brand = car["brand"] if car and car["brand"] else "—"
    car_model = car["model"] if car and car["model"] else ""
    car_name = f"{car_brand} {car_model}".strip()
    plate = car["plate"] if car and car["plate"] else "—"

    lines = [
        f"<b>Order: {order['order_number']}</b>",
        "──────────────────────",
        f"Car:     {car_name}",
        f"Plate:   {plate}",
        "──────────────────────",
        f"Problem:   {order['problem'] or '—'}",
        f"Work:      {order['work_desc'] or '—'}",
        "──────────────────────",
        f"Status:    {format_order_status(order['status'])}",
        f"Price:     {format_money(order['agreed_price'])}",
        f"Paid:      {format_money(order['paid_amount'])}",
        f"Created:   {format_datetime(order['created_at'])}",
    ]
    return "\n".join(lines)


def build_order_summary(order: dict, car: dict) -> str:
    """Build a short one-line summary for order lists."""
    car_brand = car["brand"] if car and car["brand"] else "—"
    car_model = car["model"] if car and car["model"] else ""
    car_name = f"{car_brand} {car_model}".strip()
    status = format_order_status(order["status"])
    date = format_datetime(order["created_at"])
    return f"<b>{order['order_number']}</b> | {car_name} | {status} | {date}"

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


def format_order_status(status: str, lang: str = "uz") -> str:
    """Map a status string to a human-readable label with emoji."""
    from bot.i18n import t
    key = f"status_{status}"
    result = t(key, lang)
    return result if result != key else status


def build_order_card(order: dict, car: dict, lang: str = "uz", expenses: list = None) -> str:
    """Build a formatted multi-line order status card for the client. Uses HTML parse mode."""
    from bot.i18n import t
    car_brand = car["brand"] if car and car["brand"] else "—"
    car_model = car["model"] if car and car["model"] else ""
    car_name = f"{car_brand} {car_model}".strip() or "—"
    plate = car["plate"] if car and car["plate"] else "—"

    card = t(
        "order_card", lang,
        order_number=order["order_number"],
        car_name=car_name,
        plate=plate,
        problem=order.get("problem") or "—",
        work_desc=order.get("work_desc") or "—",
        status=format_order_status(order["status"], lang),
        price=format_money(order.get("agreed_price")),
        paid=format_money(order.get("paid_amount")),
        date=format_datetime(order.get("created_at")),
    )

    if expenses:
        lines = "\n".join(
            f"  • {e['item_name']}: {format_money(e['amount'])}" for e in expenses
        )
        card += t("order_card_expenses", lang, expenses=lines)

    return card


def build_order_summary(order: dict, car: dict, lang: str = "uz") -> str:
    """Build a short one-line summary for order lists."""
    from bot.i18n import t
    car_brand = car["brand"] if car and car["brand"] else "—"
    car_model = car["model"] if car and car["model"] else ""
    car_name = f"{car_brand} {car_model}".strip() or "—"
    status = format_order_status(order["status"], lang)
    date = format_datetime(order.get("created_at"))
    return t("order_summary", lang, order_number=order["order_number"], car_name=car_name, status=status, date=date)

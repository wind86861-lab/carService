from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_skip_inline() -> InlineKeyboardMarkup:
    """Return an inline keyboard with a single 'Skip' button."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Skip", callback_data="skip")]
        ]
    )


def get_order_card_keyboard(order_number: str) -> InlineKeyboardMarkup:
    """Return an inline keyboard with a 'View Photos' button."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="View Photos", callback_data=f"photos:{order_number}")]
        ]
    )


def get_confirmation_keyboard(order_number: str) -> InlineKeyboardMarkup:
    """Return an inline keyboard with receipt confirmation / dispute buttons."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Yes, I received it",
                    callback_data=f"confirm_receipt:{order_number}",
                ),
                InlineKeyboardButton(
                    text="No, there is a problem",
                    callback_data=f"dispute:{order_number}",
                ),
            ]
        ]
    )


def get_rating_keyboard() -> InlineKeyboardMarkup:
    """Return an inline keyboard with rating buttons 1-10 in two rows of five."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=str(i), callback_data=f"rating:{i}")
                for i in range(1, 6)
            ],
            [
                InlineKeyboardButton(text=str(i), callback_data=f"rating:{i}")
                for i in range(6, 11)
            ],
        ]
    )


def get_feedback_category_keyboard() -> InlineKeyboardMarkup:
    """Return an inline keyboard with feedback category options and a Skip button."""
    categories = ["Communication", "Time", "Quality", "Price"]
    buttons = [
        [InlineKeyboardButton(text=cat, callback_data=f"category:{cat}")]
        for cat in categories
    ]
    buttons.append(
        [InlineKeyboardButton(text="Skip", callback_data="category:skip")]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_comment_skip_inline() -> InlineKeyboardMarkup:
    """Return an inline keyboard with a Skip button for the comment step."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Skip", callback_data="comment:skip")]
        ]
    )


def get_broadcast_target_keyboard() -> InlineKeyboardMarkup:
    """Return an inline keyboard for selecting broadcast target audience."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 All Users", callback_data="broadcast_target:all")],
            [InlineKeyboardButton(text="👤 Clients Only", callback_data="broadcast_target:clients")],
            [InlineKeyboardButton(text="🔧 Masters Only", callback_data="broadcast_target:masters")],
        ]
    )


def get_broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    """Return an inline keyboard for confirming or cancelling a broadcast."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Confirm", callback_data="broadcast_confirm"),
                InlineKeyboardButton(text="❌ Cancel", callback_data="broadcast_cancel"),
            ]
        ]
    )


def get_load_more_keyboard(offset: int) -> InlineKeyboardMarkup:
    """Return an inline keyboard with a 'Load more' button for order pagination."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Load more", callback_data=f"orders_page:{offset}")]
        ]
    )


def get_admin_order_keyboard(order_number: str, status: str) -> InlineKeyboardMarkup:
    """Return admin inline keyboard for an order."""
    buttons = []
    if status not in ("closed",):
        buttons.append([InlineKeyboardButton(text="🔒 Majburiy yopish", callback_data=f"adm_force_close:{order_number}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None


_STATUS_ICON = {
    "new": "🆕", "preparation": "🔧", "in_process": "⚙️", "ready": "✅", "closed": "🔒",
}


def get_admin_orders_keyboard(orders: list, page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Paginated order list — each order is a clickable inline button."""
    buttons = []
    for o in orders:
        icon = _STATUS_ICON.get(o.get("status", ""), "❓")
        plate = o.get("plate") or "—"
        client = (o.get("client_name") or "—")[:12]
        label = f"{icon} {o['order_number']} | {plate} | {client}"
        buttons.append([InlineKeyboardButton(text=label[:60], callback_data=f"adm_order_view:{o['order_number']}")])
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"adm_orders_page:{page - 1}"))
    nav.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"adm_orders_page:{page + 1}"))
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton(text="🔍 Qidirish", callback_data="adm_order_search")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_order_detail_keyboard(order_number: str, status: str) -> InlineKeyboardMarkup:
    """Order detail action buttons for admin."""
    buttons = []
    if status not in ("closed",):
        buttons.append([InlineKeyboardButton(text="🔒 Majburiy yopish", callback_data=f"adm_force_close:{order_number}")])
    buttons.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="adm_orders_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_clients_for_master_keyboard(clients: list, page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Client list for selecting who to promote to master."""
    buttons = []
    for c in clients:
        icon = "✅" if c["is_active"] else "🚫"
        label = f"{icon} {c['full_name']} | {c.get('phone') or '—'}"
        buttons.append([InlineKeyboardButton(text=label[:60], callback_data=f"adm_pick_client:{c['id']}")])
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"adm_nm_page:{page - 1}"))
    nav.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"adm_nm_page:{page + 1}"))
    if nav:
        buttons.append(nav)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


_NEXT_STATUS = {
    "new": ("preparation", "🔧 Tayyorlashga olish"),
    "preparation": ("in_process", "⚙️ Ishga kirishish"),
    "in_process": ("ready", "✅ Tayyor deb belgilash"),
}


def get_master_order_list_keyboard(orders: list, page: int = 1, total_pages: int = 1) -> InlineKeyboardMarkup:
    """Master's order list with each order as a clickable button."""
    buttons = []
    for o in orders:
        icon = _STATUS_ICON.get(o.get("status", ""), "❓")
        car = f"{o.get('brand', '') or ''} {o.get('model', '') or ''}".strip() or "—"
        label = f"{icon} {o['order_number']} | {car}"
        buttons.append([InlineKeyboardButton(text=label[:60], callback_data=f"mst_order_view:{o['order_number']}")])
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"mst_order_page:{page - 1}"))
    nav.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"mst_order_page:{page + 1}"))
    if nav:
        buttons.append(nav)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_master_order_detail_keyboard(
    order_number: str, current_status: str, client_confirmed: bool = False
) -> InlineKeyboardMarkup:
    """Status change + financial close + back button for a master's order."""
    buttons = []
    if current_status in _NEXT_STATUS:
        next_st, next_label = _NEXT_STATUS[current_status]
        buttons.append([InlineKeyboardButton(text=next_label, callback_data=f"mst_status:{order_number}:{next_st}")])
    if current_status == "ready" and client_confirmed:
        buttons.append([InlineKeyboardButton(text="💰 Moliyaviy hisobotni yopish", callback_data=f"mst_close:{order_number}")])
    buttons.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="mst_orders_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_user_keyboard(user_id: int, role: str, is_active: bool) -> InlineKeyboardMarkup:
    """Return admin inline keyboard for a user (client or master)."""
    buttons = []
    if role == "client":
        buttons.append([InlineKeyboardButton(text="⬆️ Ustaga ko'tarish", callback_data=f"adm_promote:{user_id}")])
    if role == "master":
        buttons.append([InlineKeyboardButton(text="⬇️ Mijozga tushirish", callback_data=f"adm_demote:{user_id}")])
    if is_active:
        buttons.append([InlineKeyboardButton(text="🚫 Bloklash", callback_data=f"adm_block:{user_id}")])
    else:
        buttons.append([InlineKeyboardButton(text="✅ Blokdan chiqarish", callback_data=f"adm_unblock:{user_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_confirm_keyboard(action: str, target_id: str) -> InlineKeyboardMarkup:
    """Return confirm/cancel keyboard for admin actions."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha", callback_data=f"adm_confirm:{action}:{target_id}"),
                InlineKeyboardButton(text="❌ Yo'q", callback_data="adm_cancel"),
            ]
        ]
    )


def get_admin_period_keyboard() -> InlineKeyboardMarkup:
    """Return period selector for financials."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Bugun", callback_data="adm_period:today"),
             InlineKeyboardButton(text="Hafta", callback_data="adm_period:week")],
            [InlineKeyboardButton(text="Oy", callback_data="adm_period:month"),
             InlineKeyboardButton(text="Yil", callback_data="adm_period:year")],
        ]
    )


def get_admin_page_keyboard(page: int, total_pages: int, entity: str) -> InlineKeyboardMarkup:
    """Return pagination keyboard for admin lists."""
    buttons = []
    row = []
    if page > 1:
        row.append(InlineKeyboardButton(text="⬅️", callback_data=f"adm_page:{entity}:{page - 1}"))
    row.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        row.append(InlineKeyboardButton(text="➡️", callback_data=f"adm_page:{entity}:{page + 1}"))
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)

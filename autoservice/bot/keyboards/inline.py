from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.i18n import t


def get_skip_inline() -> InlineKeyboardMarkup:
    """Return an inline keyboard with a single 'Skip' button."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Skip", callback_data="skip")]
        ]
    )


def get_order_card_keyboard(order_number: str, lang: str = "uz") -> InlineKeyboardMarkup:
    """Return an inline keyboard with a 'View Photos' button."""
    label = "📷 Rasmlar" if lang == "uz" else "📷 Фото"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, callback_data=f"photos:{order_number}")]
        ]
    )


def get_confirmation_keyboard(order_number: str, lang: str = "uz") -> InlineKeyboardMarkup:
    """Return an inline keyboard with receipt confirmation / dispute buttons."""
    yes = "✅ Ha, oldim" if lang == "uz" else "✅ Да, получил"
    no = "⚠️ Yo'q, muammo bor" if lang == "uz" else "⚠️ Нет, есть проблема"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=yes, callback_data=f"confirm_receipt:{order_number}"),
                InlineKeyboardButton(text=no, callback_data=f"dispute:{order_number}"),
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


def get_feedback_category_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    """Return negative feedback category keyboard."""
    if lang == "ru":
        cats = [("💬 Общение", "communication"), ("⏱ Время", "time"),
                ("🔧 Качество", "quality"), ("💰 Цена", "price"),
                ("📝 Другое", "other")]
        skip = "⏭ Пропустить"
    else:
        cats = [("💬 Muloqot", "communication"), ("⏱ Vaqt", "time"),
                ("🔧 Sifat", "quality"), ("💰 Narx", "price"),
                ("📝 Boshqa", "other")]
        skip = "⏭ O'tkazib yuborish"
    buttons = [[InlineKeyboardButton(text=label, callback_data=f"category:{key}")] for label, key in cats]
    buttons.append([InlineKeyboardButton(text=skip, callback_data="category:skip")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_positive_category_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    """Return positive feedback category keyboard for rating > 5."""
    if lang == "ru":
        cats = [("✅ Качество", "pos_quality"), ("⚡ Скорость", "pos_speed"),
                ("💰 Цена", "pos_price"), ("💬 Общение", "pos_communication")]
        skip = "⏭ Пропустить"
    else:
        cats = [("✅ Sifat", "pos_quality"), ("⚡ Tezlik", "pos_speed"),
                ("💰 Narx", "pos_price"), ("💬 Muloqot", "pos_communication")]
        skip = "⏭ O'tkazib yuborish"
    buttons = [[InlineKeyboardButton(text=label, callback_data=f"pos_category:{key}")] for label, key in cats]
    buttons.append([InlineKeyboardButton(text=skip, callback_data="pos_category:skip")])
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
    buttons.append([InlineKeyboardButton(text="🔍", callback_data="adm_order_search")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_order_detail_keyboard(order_number: str, status: str) -> InlineKeyboardMarkup:
    """Order detail action buttons for admin."""
    buttons = []
    if status not in ("closed",):
        buttons.append([InlineKeyboardButton(text="🔒 Force close", callback_data=f"adm_force_close:{order_number}")])
    buttons.append([InlineKeyboardButton(text="◀️ Back", callback_data="adm_orders_back")])
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


_NEXT_STATUS_KEY = {
    "new": ("preparation", "🔧", "status_preparation"),
    "preparation": ("in_process", "⚙️", "status_in_process"),
    "in_process": ("ready", "✅", "status_ready"),
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
    order_number: str, current_status: str, client_confirmed: bool = False,
    has_client: bool = False, lang: str = "uz",
) -> InlineKeyboardMarkup:
    """Status change + parts cost + financial close + share + back button for a master's order."""
    from bot.config import BOT_USERNAME
    buttons = []
    if current_status in _NEXT_STATUS_KEY:
        next_st, icon, label_key = _NEXT_STATUS_KEY[current_status]
        next_label = f"{icon} {t(label_key, lang)}"
        buttons.append([InlineKeyboardButton(text=next_label, callback_data=f"mst_status:{order_number}:{next_st}")])
    if current_status not in ("closed", "ready"):
        add_label = "🔩 Qismlar narxini qo'shish" if lang == "uz" else "🔩 Добавить запчасти"
        buttons.append([InlineKeyboardButton(text=add_label, callback_data=f"mst_add_parts:{order_number}")])
    if current_status == "ready" and client_confirmed:
        close_label = "💰 Moliyaviy hisobotni yopish" if lang == "uz" else "💰 Закрыть финансово"
        buttons.append([InlineKeyboardButton(text=close_label, callback_data=f"mst_close:{order_number}")])
    if current_status != "closed" and BOT_USERNAME:
        url = f"https://t.me/{BOT_USERNAME}?start={order_number}"
        share_label = t("share_btn_linked" if has_client else "share_btn", lang)
        buttons.append([InlineKeyboardButton(text=share_label, url=url)])
    back_label = "◄️ Orqaga" if lang == "uz" else "◄️ Назад"
    buttons.append([InlineKeyboardButton(text=back_label, callback_data="mst_orders_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_share_order_keyboard(order_number: str, has_client: bool = False, lang: str = "uz") -> InlineKeyboardMarkup:
    """Return inline keyboard with a URL deep-link button for sharing the order with a client."""
    from bot.config import BOT_USERNAME
    url = f"https://t.me/{BOT_USERNAME}?start={order_number}"
    label = t("share_btn_linked" if has_client else "share_btn", lang)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=label, url=url)],
    ])


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

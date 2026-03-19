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

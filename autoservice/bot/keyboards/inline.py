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

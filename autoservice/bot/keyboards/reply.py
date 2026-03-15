from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_keyboard(role: str) -> ReplyKeyboardMarkup:
    """Return the appropriate main menu keyboard for the given role."""
    if role == "master":
        buttons = [
            [KeyboardButton(text="New Order"), KeyboardButton(text="My Orders")],
            [KeyboardButton(text="Statistics")],
        ]
    elif role == "admin":
        buttons = [
            [KeyboardButton(text="Dashboard"), KeyboardButton(text="All Orders")],
            [KeyboardButton(text="Clients"), KeyboardButton(text="Masters")],
            [KeyboardButton(text="Send Message")],
        ]
    else:
        # client (default)
        buttons = [
            [KeyboardButton(text="Car Status"), KeyboardButton(text="Link to Order")],
            [KeyboardButton(text="My Orders")],
        ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def get_phone_keyboard() -> ReplyKeyboardMarkup:
    """Return a keyboard with a single 'Share Phone Number' contact-request button."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Share Phone Number", request_contact=True)]
        ],
        resize_keyboard=True,
    )


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Return a keyboard with a single 'Cancel' button."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Cancel")]],
        resize_keyboard=True,
    )

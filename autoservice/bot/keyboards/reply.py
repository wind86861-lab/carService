from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def get_main_keyboard(role: str) -> ReplyKeyboardMarkup:
    """Return the appropriate main menu keyboard for the given role."""
    if role == "master":
        buttons = [
            [KeyboardButton(text="🆕 Yangi buyurtma"), KeyboardButton(text="📋 Mening buyurtmalarim")],
            [KeyboardButton(text="� Yopilgan buyurtmalar"), KeyboardButton(text="�📊 Statistika")],
        ]
    elif role == "admin":
        buttons = [
            [KeyboardButton(text="📊 Boshqaruv paneli"), KeyboardButton(text="📋 Barcha buyurtmalar")],
            [KeyboardButton(text="👥 Mijozlar"), KeyboardButton(text="🔧 Ustalar")],
            [KeyboardButton(text="� Moliya"), KeyboardButton(text="🚗 Mashina tarixi")],
            [KeyboardButton(text="➕ Yangi usta"), KeyboardButton(text="�📢 Xabar yuborish")],
        ]
    else:
        # client (default)
        buttons = [
            [KeyboardButton(text="🚗 Mashina holati"), KeyboardButton(text="🔗 Buyurtmaga bog'lanish")],
            [KeyboardButton(text="📋 Mening buyurtmalarim")],
        ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def get_phone_keyboard() -> ReplyKeyboardMarkup:
    """Return a keyboard with a single 'Share Phone Number' contact-request button."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]
        ],
        resize_keyboard=True,
    )


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Return a keyboard with a single 'Cancel' button."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True,
    )


def get_language_keyboard() -> InlineKeyboardMarkup:
    """Return an inline keyboard for language selection."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="set_lang:uz"),
         InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_lang:ru")],
    ])

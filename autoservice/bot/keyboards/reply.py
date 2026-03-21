from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from bot.i18n import t


def get_main_keyboard(role: str, lang: str = "uz") -> ReplyKeyboardMarkup:
    """Return the appropriate main menu keyboard for the given role and language."""
    if role == "master":
        buttons = [
            [KeyboardButton(text=t("btn_new_order", lang)), KeyboardButton(text=t("btn_my_orders", lang))],
            [KeyboardButton(text=t("btn_closed_orders", lang)), KeyboardButton(text=t("btn_statistics", lang))],
        ]
    elif role == "admin":
        buttons = [
            [KeyboardButton(text=t("btn_dashboard", lang)), KeyboardButton(text=t("btn_all_orders", lang))],
            [KeyboardButton(text=t("btn_clients", lang)), KeyboardButton(text=t("btn_masters", lang))],
            [KeyboardButton(text=t("btn_finance", lang)), KeyboardButton(text=t("btn_car_history", lang))],
            [KeyboardButton(text=t("btn_new_master", lang)), KeyboardButton(text=t("btn_broadcast", lang))],
        ]
    else:
        buttons = [
            [KeyboardButton(text=t("btn_car_status", lang)), KeyboardButton(text=t("btn_link_order", lang))],
            [KeyboardButton(text=t("btn_my_orders", lang))],
        ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def get_phone_keyboard(lang: str = "uz") -> ReplyKeyboardMarkup:
    """Return a keyboard with a single 'Share Phone Number' contact-request button."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t("btn_send_phone", lang), request_contact=True)]
        ],
        resize_keyboard=True,
    )


def get_cancel_keyboard(lang: str = "uz") -> ReplyKeyboardMarkup:
    """Return a keyboard with a single 'Cancel' button."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t("btn_cancel", lang))]],
        resize_keyboard=True,
    )


def get_language_keyboard() -> InlineKeyboardMarkup:
    """Return an inline keyboard for language selection."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="set_lang:uz"),
         InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_lang:ru")],
    ])

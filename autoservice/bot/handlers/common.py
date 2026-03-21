import logging

from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from bot.i18n import t, lang_of
from bot.states import Registration
from bot.keyboards.reply import get_language_keyboard, get_main_keyboard, get_phone_keyboard
from bot.keyboards.inline import get_order_card_keyboard
from bot.database.models import (
    set_user_language,
    update_user_phone,
    get_order_by_number,
    link_client_to_order,
    get_car_by_order_number,
)
from bot.utils.formatters import build_order_card

logger = logging.getLogger(__name__)

router = Router()


async def _try_link_order(message: Message, order_number: str, db_user: dict):
    """Attempt to link a deep-linked order number. Returns True if linked."""
    order = await get_order_by_number(order_number)
    if not order:
        logger.warning("Deep link order %s not found", order_number)
        return False
    await link_client_to_order(order_number, db_user["id"])
    car = await get_car_by_order_number(order_number)
    lang = lang_of(db_user)
    card = build_order_card(order, car, lang=lang)
    await message.answer(t("car_linked_ok", lang))
    await message.answer(card, parse_mode="HTML", reply_markup=get_order_card_keyboard(order_number))
    return True


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext, db_user: dict):
    """Handle /start. New users pick language first, then share phone."""
    pending_order = None
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        deep_link = args[1].strip()
        if deep_link.startswith("A-") and len(deep_link) >= 6:
            pending_order = deep_link.upper()

    lang = lang_of(db_user)

    # First-time users: no phone yet → language selection first
    if not db_user.get("phone"):
        if pending_order:
            await state.update_data(pending_order_number=pending_order)
        await state.set_state(Registration.waiting_for_language)
        await message.answer(
            t("choose_language", lang),
            reply_markup=get_language_keyboard(),
        )
        return

    if pending_order and db_user.get("role") == "client":
        await _try_link_order(message, pending_order, db_user)

    role = db_user["role"]
    name = db_user["full_name"]
    key = f"welcome_{role}" if role in ("admin", "master") else "welcome_client"
    await message.answer(t(key, lang, name=name), reply_markup=get_main_keyboard(role, lang))


@router.callback_query(F.data.startswith("set_lang:"))
async def set_language_callback(callback: CallbackQuery, state: FSMContext, db_user: dict):
    """Handle language selection inline button."""
    lang = callback.data.split(":")[1]
    await set_user_language(callback.from_user.id, lang)
    # Refresh db_user language in current state data
    current_state = await state.get_state()
    await callback.message.edit_text(t("language_saved", lang))

    if current_state == Registration.waiting_for_language:
        await state.set_state(Registration.waiting_for_phone)
        await callback.message.answer(
            t("ask_phone", lang),
            reply_markup=get_phone_keyboard(lang),
        )
    else:
        # /language command outside registration — just confirm
        role = db_user.get("role", "client")
        key = f"welcome_{role}" if role in ("admin", "master") else "welcome_client"
        await callback.message.answer(
            t(key, lang, name=db_user.get("full_name", "")),
            reply_markup=get_main_keyboard(role, lang),
        )
    await callback.answer()


@router.message(Registration.waiting_for_phone, F.contact)
async def phone_handler(message: Message, state: FSMContext, db_user: dict):
    """Save phone number from shared contact."""
    phone = message.contact.phone_number
    await update_user_phone(message.from_user.id, phone)
    data = await state.get_data()
    pending_order = data.get("pending_order_number")
    await state.clear()
    lang = lang_of(db_user)
    role = db_user["role"]
    if pending_order:
        await _try_link_order(message, pending_order, db_user)
    await message.answer(t("phone_saved", lang), reply_markup=get_main_keyboard(role, lang))


@router.message(Command("language"))
async def language_command(message: Message, db_user: dict):
    """Allow user to change language at any time."""
    lang = lang_of(db_user)
    await message.answer(t("choose_language", lang), reply_markup=get_language_keyboard())


@router.message(Command("help"))
async def help_handler(message: Message, db_user: dict):
    """Send role-appropriate help text."""
    lang = lang_of(db_user)
    role = db_user["role"]
    key = f"help_{role}" if role in ("admin", "master") else "help_client"
    await message.answer(t(key, lang))


@router.message()
async def unknown_handler(message: Message, db_user: dict):
    """Catch-all for unrecognized text messages."""
    lang = lang_of(db_user)
    await message.answer(t("unknown_message", lang))

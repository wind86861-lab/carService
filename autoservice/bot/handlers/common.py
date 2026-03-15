import logging

from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.states import Registration
from bot.keyboards.reply import get_main_keyboard, get_phone_keyboard
from bot.keyboards.inline import get_order_card_keyboard
from bot.database.models import (
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
    card = build_order_card(order, car)
    await message.answer("Your car has been linked successfully.")
    await message.answer(
        card,
        parse_mode="HTML",
        reply_markup=get_order_card_keyboard(order_number),
    )
    return True


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext, db_user: dict):
    """Handle /start command. Optionally extract deep link argument."""
    pending_order = None
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        deep_link = args[1].strip()
        logger.info("Deep link argument received: %s (user %s)", deep_link, message.from_user.id)
        if deep_link.startswith("A-") and len(deep_link) >= 6:
            pending_order = deep_link.upper()

    role = db_user["role"]
    name = db_user["full_name"]

    if not db_user["phone"]:
        if pending_order:
            await state.update_data(pending_order_number=pending_order)
        await state.set_state(Registration.waiting_for_phone)
        await message.answer(
            "Welcome to AutoService Bot! To get started, please share your phone number.",
            reply_markup=get_phone_keyboard(),
        )
        return

    if pending_order:
        await _try_link_order(message, pending_order, db_user)

    if role == "admin":
        text = f"Welcome, {name}! You are logged in as an administrator."
    elif role == "master":
        text = f"Welcome, {name}! You are logged in as a master."
    else:
        text = f"Welcome back, {name}! Use the menu below to track your car."

    await message.answer(text, reply_markup=get_main_keyboard(role))


@router.message(Registration.waiting_for_phone, F.contact)
async def phone_handler(message: Message, state: FSMContext, db_user: dict):
    """Save phone number from shared contact, then auto-link pending order if any."""
    phone = message.contact.phone_number
    await update_user_phone(message.from_user.id, phone)

    data = await state.get_data()
    pending_order = data.get("pending_order_number")
    await state.clear()

    role = db_user["role"]

    if pending_order:
        await _try_link_order(message, pending_order, db_user)

    await message.answer(
        "Phone number saved! Use the menu below.",
        reply_markup=get_main_keyboard(role),
    )


@router.message(Command("help"))
async def help_handler(message: Message, db_user: dict):
    """Send role-appropriate help text."""
    role = db_user["role"]
    if role == "admin":
        text = (
            "/start — restart the bot\n"
            "/help — show this help\n\n"
            "Menu buttons:\n"
            "Dashboard — view summary statistics\n"
            "All Orders — browse all orders\n"
            "Clients — manage clients\n"
            "Masters — manage masters\n"
            "Send Message — broadcast a message"
        )
    elif role == "master":
        text = (
            "/start — restart the bot\n"
            "/help — show this help\n\n"
            "Menu buttons:\n"
            "New Order — create a new order\n"
            "My Orders — view your assigned orders\n"
            "Statistics — view your performance stats"
        )
    else:
        text = (
            "/start — restart the bot\n"
            "/help — show this help\n\n"
            "Menu buttons:\n"
            "Car Status — check the status of your car\n"
            "Link to Order — link yourself to an existing order\n"
            "My Orders — view your order history"
        )
    await message.answer(text)


@router.message()
async def unknown_handler(message: Message):
    """Catch-all for unrecognized text messages."""
    await message.answer("Sorry, I did not understand that. Type /help to see available commands.")

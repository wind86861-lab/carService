import logging

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.filters import MagicData
from aiogram.fsm.context import FSMContext

from bot.states import ClientLinkOrder, ClientFeedback
from bot.keyboards.reply import get_main_keyboard, get_cancel_keyboard
from bot.keyboards.inline import (
    get_order_card_keyboard,
    get_feedback_category_keyboard,
    get_comment_skip_inline,
    get_load_more_keyboard,
)
from bot.database.models import (
    get_order_by_number,
    get_orders_by_client,
    link_client_to_order,
    get_car_by_order_number,
    get_photos_by_order,
    confirm_client_receipt,
    update_order_status,
    get_user_by_id,
    create_feedback,
)
from bot.utils.formatters import (
    build_order_card,
    build_order_summary,
    format_order_status,
)
from bot.utils.notifications import (
    notify_master_receipt_confirmed,
    notify_master_dispute,
    notify_admin_dispute,
    schedule_feedback_request,
)

logger = logging.getLogger(__name__)

router = Router()
router.message.filter(MagicData(F.db_user["role"] == "client"))

PAGE_SIZE = 5


# ------------------------------------------------------------------
# Link to Order flow
# ------------------------------------------------------------------


@router.message(F.text == "Link to Order")
async def client_link_handler(message: Message, state: FSMContext, db_user: dict):
    await state.set_state(ClientLinkOrder.waiting_for_order_number)
    await message.answer(
        "Please enter your order number (for example: A-0042).",
        reply_markup=get_cancel_keyboard(),
    )


@router.message(ClientLinkOrder.waiting_for_order_number)
async def client_order_number_handler(
    message: Message, state: FSMContext, db_user: dict, bot: Bot
):
    if message.text and message.text.strip().lower() == "cancel":
        await state.clear()
        await message.answer(
            "Cancelled.", reply_markup=get_main_keyboard("client")
        )
        return

    order_number = message.text.strip().upper() if message.text else ""
    order = await get_order_by_number(order_number)
    if not order:
        await message.answer(
            "Order not found. Please check the number and try again."
        )
        return

    await link_client_to_order(order_number, db_user["id"])
    await state.clear()

    car = await get_car_by_order_number(order_number)
    card = build_order_card(order, car)
    await message.answer("Your car has been linked successfully.")
    await message.answer(
        card,
        parse_mode="HTML",
        reply_markup=get_order_card_keyboard(order_number),
    )
    await message.answer("Menu:", reply_markup=get_main_keyboard("client"))


# ------------------------------------------------------------------
# Car Status
# ------------------------------------------------------------------


@router.message(F.text == "Car Status")
async def client_status_handler(message: Message, db_user: dict):
    orders = await get_orders_by_client(db_user["id"])
    if not orders:
        await message.answer(
            "You have no linked orders yet. Tap Link to Order to connect your car."
        )
        return

    active = [o for o in orders if o["status"] in ("new", "preparation", "in_process", "ready")]
    to_show = active if active else [orders[0]]

    for order in to_show:
        car = await get_car_by_order_number(order["order_number"])
        card = build_order_card(order, car)
        await message.answer(
            card,
            parse_mode="HTML",
            reply_markup=get_order_card_keyboard(order["order_number"]),
        )


# ------------------------------------------------------------------
# My Orders (paginated)
# ------------------------------------------------------------------


@router.message(F.text == "My Orders")
async def client_my_orders_handler(message: Message, db_user: dict):
    orders = await get_orders_by_client(db_user["id"])
    if not orders:
        await message.answer(
            "You have no linked orders yet. Tap Link to Order to connect your car."
        )
        return

    page = orders[:PAGE_SIZE]
    lines = []
    for order in page:
        car = await get_car_by_order_number(order["order_number"])
        lines.append(build_order_summary(order, car))

    text = "\n\n".join(lines)
    if len(orders) > PAGE_SIZE:
        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=get_load_more_keyboard(PAGE_SIZE),
        )
    else:
        await message.answer(text, parse_mode="HTML")


@router.callback_query(F.data.startswith("orders_page:"))
async def orders_page_callback(callback: CallbackQuery, db_user: dict):
    offset = int(callback.data.split(":")[1])
    orders = await get_orders_by_client(db_user["id"])
    page = orders[offset : offset + PAGE_SIZE]

    if not page:
        await callback.answer("No more orders.")
        return

    lines = []
    for order in page:
        car = await get_car_by_order_number(order["order_number"])
        lines.append(build_order_summary(order, car))

    text = "\n\n".join(lines)
    next_offset = offset + PAGE_SIZE
    if next_offset < len(orders):
        await callback.message.answer(
            text,
            parse_mode="HTML",
            reply_markup=get_load_more_keyboard(next_offset),
        )
    else:
        await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()


# ------------------------------------------------------------------
# View Photos callback
# ------------------------------------------------------------------


@router.callback_query(F.data.startswith("photos:"))
async def view_photos_callback(callback: CallbackQuery, db_user: dict):
    order_number = callback.data.split(":", 1)[1]
    order = await get_order_by_number(order_number)
    if not order:
        await callback.answer("Order not found.", show_alert=True)
        return

    photos = await get_photos_by_order(order["id"])
    if not photos:
        await callback.answer("No photos available for this order.", show_alert=True)
        return

    media = [InputMediaPhoto(media=p["file_id"]) for p in photos]
    await callback.message.answer_media_group(media)
    await callback.answer()


# ------------------------------------------------------------------
# Confirm receipt
# ------------------------------------------------------------------


@router.callback_query(F.data.startswith("confirm_receipt:"))
async def confirm_receipt_callback(callback: CallbackQuery, db_user: dict, bot: Bot):
    order_number = callback.data.split(":", 1)[1]

    order = await get_order_by_number(order_number)
    if order and order["client_confirmed"]:
        await callback.answer("You have already confirmed receipt for this order.", show_alert=True)
        return

    await confirm_client_receipt(order_number)

    new_text = callback.message.text + "\n\n✅ You have confirmed receipt. The order is now closed."
    await callback.message.edit_text(new_text, reply_markup=None)

    order = await get_order_by_number(order_number)
    if order and order["master_id"]:
        master = await get_user_by_id(order["master_id"])
        if master:
            notify_master_receipt_confirmed(master["telegram_id"], order_number)

    if order:
        from aiogram import Dispatcher
        dp = Dispatcher.get_current()
        await schedule_feedback_request(
            bot, db_user["telegram_id"], order["id"], order_number, dp
        )
    await callback.answer()


# ------------------------------------------------------------------
# Dispute
# ------------------------------------------------------------------


@router.callback_query(F.data.startswith("dispute:"))
async def dispute_callback(callback: CallbackQuery, db_user: dict, bot: Bot):
    order_number = callback.data.split(":", 1)[1]
    new_text = callback.message.text + "\n\n⚠️ We have notified the master about your concern."
    await callback.message.edit_text(new_text, reply_markup=None)

    order = await get_order_by_number(order_number)
    client_name = db_user["full_name"]
    master_name = "Unknown"

    await update_order_status(
        order_number,
        "ready",
        note=f"Dispute raised by client {client_name}",
        changed_by=db_user["id"],
    )

    if order and order["master_id"]:
        master = await get_user_by_id(order["master_id"])
        if master:
            master_name = master["full_name"]
            notify_master_dispute(
                master["telegram_id"], order_number, client_name
            )

    await notify_admin_dispute(order_number, client_name, master_name)
    await callback.answer()


# ------------------------------------------------------------------
# Feedback — rating
# ------------------------------------------------------------------


@router.callback_query(F.data.startswith("rating:"))
async def feedback_rating_callback(
    callback: CallbackQuery, state: FSMContext, db_user: dict
):
    rating = int(callback.data.split(":")[1])
    data = await state.get_data()
    order_id = data.get("feedback_order_id")

    await state.update_data(feedback_rating=rating)
    await callback.message.edit_text(f"You rated this service: {rating}/10")

    if rating >= 5:
        if order_id:
            await create_feedback(order_id, db_user["id"], rating)
        await state.clear()
        await callback.message.answer("Thank you for your feedback!")
    else:
        await state.set_state(ClientFeedback.waiting_for_category)
        await callback.message.answer(
            "We are sorry to hear that. What was the main issue?",
            reply_markup=get_feedback_category_keyboard(),
        )
    await callback.answer()


# ------------------------------------------------------------------
# Feedback — category
# ------------------------------------------------------------------


@router.callback_query(F.data.startswith("category:"))
async def feedback_category_callback(
    callback: CallbackQuery, state: FSMContext, db_user: dict
):
    label = callback.data.split(":", 1)[1]
    data = await state.get_data()
    order_id = data.get("feedback_order_id")
    rating = data.get("feedback_rating", 1)

    if label == "skip":
        if order_id:
            await create_feedback(order_id, db_user["id"], rating)
        await state.clear()
        await callback.message.edit_text("Thank you for your feedback.")
        await callback.answer()
        return

    await state.update_data(feedback_category=label)
    await callback.message.edit_text(f"Category: {label}")
    await state.set_state(ClientFeedback.waiting_for_comment)
    await callback.message.answer(
        "Would you like to add a comment? Type it below or tap Skip.",
        reply_markup=get_comment_skip_inline(),
    )
    await callback.answer()


# ------------------------------------------------------------------
# Feedback — comment (text)
# ------------------------------------------------------------------


@router.message(ClientFeedback.waiting_for_comment)
async def feedback_comment_handler(message: Message, state: FSMContext, db_user: dict):
    data = await state.get_data()
    order_id = data.get("feedback_order_id")
    rating = data.get("feedback_rating", 1)
    category = data.get("feedback_category")

    if order_id:
        await create_feedback(order_id, db_user["id"], rating, category, message.text)
    await state.clear()
    await message.answer(
        "Thank you! Your feedback has been saved.",
        reply_markup=get_main_keyboard("client"),
    )


# ------------------------------------------------------------------
# Feedback — comment skip callback
# ------------------------------------------------------------------


@router.callback_query(F.data == "comment:skip")
async def feedback_comment_skip_callback(
    callback: CallbackQuery, state: FSMContext, db_user: dict
):
    data = await state.get_data()
    order_id = data.get("feedback_order_id")
    rating = data.get("feedback_rating", 1)
    category = data.get("feedback_category")

    if order_id:
        await create_feedback(order_id, db_user["id"], rating, category)
    await state.clear()
    await callback.message.edit_text("Thank you for your feedback.")
    await callback.answer()

import logging

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.types import FSInputFile
from aiogram.fsm.context import FSMContext

from bot.i18n import t, lang_of, all_variants
from bot.states import ClientDispute, ClientLinkOrder, ClientFeedback
from bot.keyboards.reply import get_main_keyboard, get_cancel_keyboard
from bot.keyboards.inline import (
    get_order_card_keyboard,
    get_feedback_category_keyboard,
    get_positive_category_keyboard,
    get_comment_skip_inline,
    get_load_more_keyboard,
    get_rating_keyboard,
    get_link_confirm_keyboard,
)
from bot.database.models import (
    get_expenses_by_order,
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
    format_money,
    format_order_status,
)
from bot.utils.notifications import (
    notify_master_receipt_confirmed,
    notify_master_dispute,
    notify_admin_dispute,
    notify_master_dispute_with_text,
    notify_admin_dispute_with_text,
    schedule_feedback_request,
)

logger = logging.getLogger(__name__)

router = Router()


async def _is_client(message: Message, db_user: dict) -> bool:
    return isinstance(db_user, dict) and db_user.get("role") == "client"


PAGE_SIZE = 5


async def _build_card(order, db_user: dict):
    """Build order card with expenses. Returns (text, keyboard)."""
    lang = lang_of(db_user)
    car = await get_car_by_order_number(order["order_number"])
    expenses = None
    try:
        exp_rows = await get_expenses_by_order(order["id"])
        if exp_rows:
            expenses = [dict(e) for e in exp_rows]
    except Exception:
        pass
    card = build_order_card(order, car, lang=lang, expenses=expenses)
    kb = get_order_card_keyboard(order["order_number"], lang=lang)
    return card, kb


# ------------------------------------------------------------------
# Link to Order flow
# ------------------------------------------------------------------


@router.message(F.text.in_(all_variants("btn_link_order")))
async def client_link_handler(message: Message, state: FSMContext, db_user: dict):
    lang = lang_of(db_user)
    await state.set_state(ClientLinkOrder.waiting_for_plate)
    await message.answer(t("enter_plate", lang), reply_markup=get_cancel_keyboard(lang))


@router.message(ClientLinkOrder.waiting_for_plate)
async def client_plate_handler(message: Message, state: FSMContext, db_user: dict):
    lang = lang_of(db_user)
    if message.text and message.text.strip() in all_variants("btn_cancel"):
        await state.clear()
        await message.answer(t("cancelled", lang), reply_markup=get_main_keyboard("client", lang))
        return
    plate = message.text.strip().upper() if message.text else ""
    await state.update_data(link_plate=plate)
    data = await state.get_data()
    pending = data.get("link_order_number_pending")
    if pending:
        await _verify_and_show_confirm(message, state, db_user, pending)
        return
    await state.set_state(ClientLinkOrder.waiting_for_order_number)
    await message.answer(t("enter_order_number", lang))


async def _verify_and_show_confirm(message: Message, state: FSMContext, db_user: dict, order_number: str):
    """Verify plate matches order, show details, ask for confirmation."""
    lang = lang_of(db_user)
    order = await get_order_by_number(order_number)
    if not order:
        await message.answer(t("order_not_found", lang))
        await state.clear()
        await message.answer("📱", reply_markup=get_main_keyboard("client", lang))
        return
    if order.get("client_id") == db_user["id"]:
        await state.clear()
        await message.answer(t("already_linked", lang), reply_markup=get_main_keyboard("client", lang))
        return
    car = await get_car_by_order_number(order_number)
    data = await state.get_data()
    plate_input = data.get("link_plate", "")
    car_plate = (car["plate"] if car and car.get("plate") else "").upper()
    if not car_plate or plate_input != car_plate:
        await message.answer(t("plate_mismatch", lang))
        await state.set_state(ClientLinkOrder.waiting_for_plate)
        await message.answer(t("enter_plate", lang))
        return
    car_name = f"{car.get('brand', '') or ''} {car.get('model', '') or ''}".strip() or "\u2014"
    car_full = f"{car_name} | {car_plate}"
    master_name = "\u2014"
    if order.get("master_id"):
        master = await get_user_by_id(order["master_id"])
        if master:
            master_name = master["full_name"]
    await state.update_data(link_order_number=order_number)
    await state.set_state(ClientLinkOrder.waiting_for_confirm)
    await message.answer(
        t("link_confirm_prompt", lang,
          order_number=order_number,
          car=car_full,
          problem=order.get("problem") or "\u2014",
          status=format_order_status(order["status"], lang),
          master=master_name),
        parse_mode="HTML",
        reply_markup=get_link_confirm_keyboard(order_number, lang),
    )


@router.message(ClientLinkOrder.waiting_for_order_number)
async def client_order_number_handler(message: Message, state: FSMContext, db_user: dict):
    lang = lang_of(db_user)
    if message.text and message.text.strip() in all_variants("btn_cancel"):
        await state.clear()
        await message.answer(t("cancelled", lang), reply_markup=get_main_keyboard("client", lang))
        return
    order_number = message.text.strip().upper() if message.text else ""
    order = await get_order_by_number(order_number)
    if not order:
        await message.answer(t("order_not_found", lang))
        return
    await _verify_and_show_confirm(message, state, db_user, order_number)


@router.callback_query(F.data.startswith("link_confirm:"))
async def client_link_confirm_callback(callback: CallbackQuery, state: FSMContext, db_user: dict):
    lang = lang_of(db_user)
    order_number = callback.data.split(":", 1)[1]
    order = await get_order_by_number(order_number)
    if not order:
        await callback.answer(t("order_not_found", lang), show_alert=True); return
    await link_client_to_order(order_number, db_user["id"])
    await state.clear()
    await callback.message.edit_text(
        (callback.message.text or "") + "\n\n" + t("link_confirmed", lang),
        reply_markup=None,
    )
    card, kb = await _build_card(order, db_user)
    await callback.message.answer(card, parse_mode="HTML", reply_markup=kb)
    await callback.message.answer("\u2705", reply_markup=get_main_keyboard("client", lang))
    await callback.answer()


@router.callback_query(F.data == "link_cancel")
async def client_link_cancel_callback(callback: CallbackQuery, state: FSMContext, db_user: dict):
    lang = lang_of(db_user)
    await state.clear()
    await callback.message.edit_text(
        (callback.message.text or "") + "\n\n" + t("link_cancelled", lang),
        reply_markup=None,
    )
    await callback.message.answer("\u2705", reply_markup=get_main_keyboard("client", lang))
    await callback.answer()


# ------------------------------------------------------------------
# Car Status
# ------------------------------------------------------------------


@router.message(F.text.in_(all_variants("btn_car_status")))
async def client_status_handler(message: Message, db_user: dict):
    lang = lang_of(db_user)
    orders = await get_orders_by_client(db_user["id"])
    active = [o for o in (orders or []) if o["status"] not in ("closed", "cancelled")]
    if not active:
        await message.answer(t("no_active_orders", lang), reply_markup=get_main_keyboard("client", lang))
        return
    card, kb = await _build_card(active[0], db_user)
    await message.answer(card, parse_mode="HTML", reply_markup=kb)


# ------------------------------------------------------------------
# My Orders (paginated)
# ------------------------------------------------------------------


def _is_client_role(message: Message, **kwargs) -> bool:
    db_user = kwargs.get("db_user")
    return isinstance(db_user, dict) and db_user.get("role") == "client"


@router.message(F.text.in_(all_variants("btn_my_orders")), _is_client_role)
async def client_my_orders_handler(message: Message, db_user: dict):
    lang = lang_of(db_user)
    orders = await get_orders_by_client(db_user["id"])
    if not orders:
        await message.answer(t("no_orders", lang), reply_markup=get_main_keyboard("client", lang))
        return
    page = orders[:PAGE_SIZE]
    lines = []
    for order in page:
        car = await get_car_by_order_number(order["order_number"])
        lines.append(build_order_summary(order, car, lang=lang))
    text = "\n\n".join(lines)
    if len(orders) > PAGE_SIZE:
        await message.answer(text, parse_mode="HTML", reply_markup=get_load_more_keyboard(PAGE_SIZE))
    else:
        await message.answer(text, parse_mode="HTML")


@router.callback_query(F.data.startswith("orders_page:"))
async def orders_page_callback(callback: CallbackQuery, db_user: dict):
    lang = lang_of(db_user)
    offset = int(callback.data.split(":")[1])
    orders = await get_orders_by_client(db_user["id"])
    page = orders[offset: offset + PAGE_SIZE]
    if not page:
        await callback.answer("—")
        return
    lines = []
    for order in page:
        car = await get_car_by_order_number(order["order_number"])
        lines.append(build_order_summary(order, car, lang=lang))
    text = "\n\n".join(lines)
    next_offset = offset + PAGE_SIZE
    if next_offset < len(orders):
        await callback.message.answer(text, parse_mode="HTML", reply_markup=get_load_more_keyboard(next_offset))
    else:
        await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()


# ------------------------------------------------------------------
# View Photos callback
# ------------------------------------------------------------------


def _is_tg_file_id(value: str) -> bool:
    """A Telegram file_id is a long (>40 chars) alphanumeric string without a file extension."""
    if not value:
        return False
    if '.' in value.split('/')[-1]:
        return False
    return len(value) > 40


@router.callback_query(F.data.startswith("photos:"))
async def view_photos_callback(callback: CallbackQuery, db_user: dict):
    import os
    lang = lang_of(db_user)
    order_number = callback.data.split(":", 1)[1]
    order = await get_order_by_number(order_number)
    if not order:
        await callback.answer("❌", show_alert=True); return
    photos = await get_photos_by_order(order["id"])
    if not photos:
        msg = "📷 Rasmlar yo'q" if lang == "uz" else "📷 Фото нет"
        await callback.answer(msg, show_alert=True); return

    media = []
    for p in photos:
        fid = p["file_id"]
        if _is_tg_file_id(fid):
            media.append(InputMediaPhoto(media=fid))
        else:
            # Local file uploaded via web interface
            local_path = f"/app/uploads/{os.path.basename(fid)}"
            if os.path.exists(local_path):
                media.append(InputMediaPhoto(media=FSInputFile(local_path)))
            else:
                logger.warning("Photo file not found: %s", local_path)

    if not media:
        msg = "📷 Rasmlar yo'q" if lang == "uz" else "📷 Фото нет"
        await callback.answer(msg, show_alert=True); return

    try:
        await callback.message.answer_media_group(media)
    except Exception as exc:
        logger.exception("Failed to send photos for order %s: %s", order_number, exc)
        err = "❌ Rasmlarni yuborishda xato" if lang == "uz" else "❌ Ошибка при отправке фото"
        await callback.answer(err, show_alert=True)
    await callback.answer()


# ------------------------------------------------------------------
# Confirm receipt
# ------------------------------------------------------------------


@router.callback_query(F.data.startswith("confirm_receipt:"))
async def confirm_receipt_callback(callback: CallbackQuery, state: FSMContext, db_user: dict, bot: Bot):
    lang = lang_of(db_user)
    order_number = callback.data.split(":", 1)[1]
    order = await get_order_by_number(order_number)
    if order and order["client_confirmed"]:
        await callback.answer(t("already_confirmed", lang), show_alert=True); return
    agreed = order.get("agreed_price", 0) or 0
    parts = order.get("parts_cost", 0) or 0
    profit = max(0, agreed - parts)
    ratio = 0.40
    if order and order.get("master_id"):
        from bot.database.models import get_master_total_earnings
        total = await get_master_total_earnings(order["master_id"])
        if total >= 15_000_000:
            ratio = 0.50
        elif total >= 10_000_000:
            ratio = 0.45
    master_share = int(profit * ratio)
    service_share = profit - master_share
    await confirm_client_receipt(order_number, profit=profit,
                                 master_share=master_share, service_share=service_share)
    new_text = (callback.message.text or "") + "\n\n" + t("confirm_receipt_done", lang)
    await callback.message.edit_text(new_text, reply_markup=None)
    order = await get_order_by_number(order_number)
    if order and order["master_id"]:
        master = await get_user_by_id(order["master_id"])
        if master:
            master_lang = master.get("language") or "uz"
            paid_total = format_money(int(order.get("agreed_price") or 0))
            notify_master_receipt_confirmed(
                master["telegram_id"], order_number,
                paid_amount=paid_total, lang=master_lang,
            )
    if order:
        from bot.database.models import get_feedback_by_order
        existing = await get_feedback_by_order(order["id"])
        if not existing:
            await state.update_data(feedback_order_id=order["id"])
            await callback.message.answer(
                t("feedback_request", lang, order_number=order_number),
                reply_markup=get_rating_keyboard(),
            )
    await callback.answer()


# ------------------------------------------------------------------
# Dispute
# ------------------------------------------------------------------


@router.callback_query(F.data.startswith("dispute:"))
async def dispute_callback(callback: CallbackQuery, state: FSMContext, db_user: dict):
    lang = lang_of(db_user)
    order_number = callback.data.split(":", 1)[1]
    await callback.message.edit_text(
        (callback.message.text or "") + "\n\n" + t("dispute_ask_reason", lang),
        reply_markup=None,
    )
    await state.set_state(ClientDispute.waiting_for_issue_text)
    await state.update_data(dispute_order_number=order_number)
    await callback.answer()


@router.message(ClientDispute.waiting_for_issue_text, F.text)
async def dispute_issue_text_handler(message: Message, state: FSMContext, db_user: dict, bot: Bot):
    lang = lang_of(db_user)
    data = await state.get_data()
    order_number = data.get("dispute_order_number")
    await state.clear()
    if not order_number:
        return
    issue_text = message.text.strip()
    order = await get_order_by_number(order_number)
    client_name = db_user["full_name"]
    master_name = "—"
    await update_order_status(order_number, "in_process",
        note=f"Dispute: {issue_text}", changed_by=db_user["id"])
    if order and order["master_id"]:
        master = await get_user_by_id(order["master_id"])
        if master:
            master_name = master["full_name"]
            master_lang = master.get("language") or "uz"
            notify_master_dispute_with_text(
                master["telegram_id"], order_number, client_name, issue_text, lang=master_lang
            )
    await notify_admin_dispute_with_text(order_number, client_name, master_name, issue_text)
    await message.answer(t("dispute_reported", lang), reply_markup=get_main_keyboard("client", lang))


# ------------------------------------------------------------------
# Feedback — rating
# ------------------------------------------------------------------


@router.callback_query(F.data.startswith("rating:"))
async def feedback_rating_callback(callback: CallbackQuery, state: FSMContext, db_user: dict):
    lang = lang_of(db_user)
    rating = int(callback.data.split(":")[1])
    data = await state.get_data()
    order_id = data.get("feedback_order_id")
    await state.update_data(feedback_rating=rating)
    await callback.message.edit_text(t("feedback_rated", lang, rating=rating))
    if rating > 5:
        # Ask about positive aspects
        await state.set_state(ClientFeedback.waiting_for_category)
        await state.update_data(feedback_positive=True)
        await callback.message.answer(
            t("feedback_ask_positive", lang),
            reply_markup=get_positive_category_keyboard(lang),
        )
    elif rating == 5:
        if order_id:
            await create_feedback(order_id, db_user["id"], rating)
        await state.clear()
        await callback.message.answer(t("feedback_thanks", lang))
    else:
        await state.set_state(ClientFeedback.waiting_for_category)
        await state.update_data(feedback_positive=False)
        await callback.message.answer(
            t("feedback_ask_negative", lang),
            reply_markup=get_feedback_category_keyboard(lang),
        )
    await callback.answer()


# ------------------------------------------------------------------
# Feedback — positive category (rating > 5)
# ------------------------------------------------------------------


@router.callback_query(F.data.startswith("pos_category:"))
async def feedback_positive_category_callback(callback: CallbackQuery, state: FSMContext, db_user: dict):
    lang = lang_of(db_user)
    label = callback.data.split(":", 1)[1]
    data = await state.get_data()
    order_id = data.get("feedback_order_id")
    rating = data.get("feedback_rating", 6)
    if label == "skip":
        if order_id:
            await create_feedback(order_id, db_user["id"], rating)
        await state.clear()
        await callback.message.edit_text(t("feedback_thanks", lang))
        await callback.answer(); return
    await state.update_data(feedback_category=label)
    await callback.message.edit_text(f"✅ {label}")
    await state.set_state(ClientFeedback.waiting_for_comment)
    await callback.message.answer(t("feedback_ask_comment", lang), reply_markup=get_comment_skip_inline())
    await callback.answer()


# ------------------------------------------------------------------
# Feedback — negative category (rating <= 4)
# ------------------------------------------------------------------


@router.callback_query(F.data.startswith("category:"))
async def feedback_category_callback(callback: CallbackQuery, state: FSMContext, db_user: dict):
    lang = lang_of(db_user)
    label = callback.data.split(":", 1)[1]
    data = await state.get_data()
    order_id = data.get("feedback_order_id")
    rating = data.get("feedback_rating", 1)
    if label == "skip":
        if order_id:
            await create_feedback(order_id, db_user["id"], rating)
        await state.clear()
        await callback.message.edit_text(t("feedback_thanks", lang))
        await callback.answer(); return
    await state.update_data(feedback_category=label)
    await callback.message.edit_text(f"📝 {label}")
    await state.set_state(ClientFeedback.waiting_for_comment)
    await callback.message.answer(t("feedback_ask_comment", lang), reply_markup=get_comment_skip_inline())
    await callback.answer()


# ------------------------------------------------------------------
# Feedback — comment (text)
# ------------------------------------------------------------------


@router.message(ClientFeedback.waiting_for_comment)
async def feedback_comment_handler(message: Message, state: FSMContext, db_user: dict):
    lang = lang_of(db_user)
    data = await state.get_data()
    order_id = data.get("feedback_order_id")
    rating = data.get("feedback_rating", 1)
    category = data.get("feedback_category")
    if order_id:
        await create_feedback(order_id, db_user["id"], rating, category, message.text)
    await state.clear()
    await message.answer(t("feedback_saved", lang), reply_markup=get_main_keyboard("client", lang))


# ------------------------------------------------------------------
# Feedback — comment skip
# ------------------------------------------------------------------


@router.callback_query(F.data == "comment:skip")
async def feedback_comment_skip_callback(callback: CallbackQuery, state: FSMContext, db_user: dict):
    lang = lang_of(db_user)
    data = await state.get_data()
    order_id = data.get("feedback_order_id")
    rating = data.get("feedback_rating", 1)
    category = data.get("feedback_category")
    if order_id:
        await create_feedback(order_id, db_user["id"], rating, category)
    await state.clear()
    await callback.message.edit_text(t("feedback_thanks", lang))
    await callback.answer()

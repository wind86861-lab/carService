import logging
import math

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.database.models import (
    add_photo,
    close_order,
    create_car,
    create_order,
    create_order_expense,
    get_financial_summary_by_master,
    get_master_total_earnings,
    get_next_order_number,
    get_order_by_number,
    get_order_detail,
    get_orders_by_master,
    get_user_by_id,
    get_users_by_role,
    update_order_status,
    update_parts_cost,
)
from bot.i18n import all_variants, lang_of, t
from bot.keyboards.inline import (
    get_master_order_detail_keyboard,
    get_master_order_list_keyboard,
    get_share_order_keyboard,
)
from bot.keyboards.reply import get_cancel_keyboard, get_main_keyboard
from bot.states import MasterCloseOrder, MasterCreateOrder, MasterUpdateParts
from bot.utils.formatters import format_datetime, format_money, format_order_status
from bot.utils.notifications import notify_client_receipt_request

logger = logging.getLogger(__name__)

router = Router()

_PAGE = 8
_ACTIVE = ["new", "preparation", "in_process", "ready"]


async def _master_share_ratio(master_id: int) -> float:
    """Dynamic master share: 40% base, +5% if >10M total, +10% if >15M total."""
    total = await get_master_total_earnings(master_id)
    if total >= 15_000_000:
        return 0.50
    if total >= 10_000_000:
        return 0.45
    return 0.40


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CANCEL_TEXTS = all_variants("btn_cancel")


def _cancel_check(text: str) -> bool:
    return text in _CANCEL_TEXTS


async def _cancel(message: Message, state: FSMContext, lang: str = "uz"):
    await state.clear()
    await message.answer(t("cancelled", lang), reply_markup=get_main_keyboard("master", lang))


def _parse_amount(text: str):
    """Return int from a money string, or None if invalid."""
    clean = text.strip().replace(" ", "").replace(",", "").replace("_", "")
    return int(clean) if clean.isdigit() else None


def _confirm_yes(text: str) -> bool:
    return text.lower().strip() in ("ha", "yes", "y", "ok", "+", "да", "д")


def _confirm_no(text: str) -> bool:
    return text.lower().strip() in ("yo'q", "yoq", "no", "n", "нет", "н")


# ---------------------------------------------------------------------------
# New Order — full FSM flow in Telegram
# ---------------------------------------------------------------------------

@router.message(F.text.in_(all_variants("btn_new_order")))
async def master_new_order_handler(message: Message, db_user: dict, state: FSMContext):
    if not isinstance(db_user, dict) or db_user.get("role") not in ("master", "admin"):
        return
    lang = lang_of(db_user)
    await state.set_state(MasterCreateOrder.waiting_for_brand)
    await message.answer(
        t("new_order_title", lang),
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard(lang),
    )


@router.message(MasterCreateOrder.waiting_for_brand)
async def master_order_brand(message: Message, state: FSMContext, db_user: dict):
    lang = lang_of(db_user)
    if _cancel_check(message.text):
        await _cancel(message, state, lang); return
    await state.update_data(brand=message.text.strip())
    await state.set_state(MasterCreateOrder.waiting_for_model)
    await message.answer(t("step_model", lang), parse_mode="HTML")


@router.message(MasterCreateOrder.waiting_for_model)
async def master_order_model(message: Message, state: FSMContext, db_user: dict):
    lang = lang_of(db_user)
    if _cancel_check(message.text):
        await _cancel(message, state, lang); return
    await state.update_data(model=message.text.strip())
    await state.set_state(MasterCreateOrder.waiting_for_plate)
    await message.answer(t("step_plate", lang), parse_mode="HTML")


@router.message(MasterCreateOrder.waiting_for_plate)
async def master_order_plate(message: Message, state: FSMContext, db_user: dict):
    lang = lang_of(db_user)
    if _cancel_check(message.text):
        await _cancel(message, state, lang); return
    await state.update_data(plate=message.text.strip().upper())
    await state.set_state(MasterCreateOrder.waiting_for_color)
    await message.answer(t("step_color", lang), parse_mode="HTML")


@router.message(MasterCreateOrder.waiting_for_color)
async def master_order_color(message: Message, state: FSMContext, db_user: dict):
    lang = lang_of(db_user)
    if _cancel_check(message.text):
        await _cancel(message, state, lang); return
    color = None if message.text.strip() == "/skip" else message.text.strip()
    await state.update_data(color=color)
    await state.set_state(MasterCreateOrder.waiting_for_year)
    await message.answer(t("step_year", lang), parse_mode="HTML")


@router.message(MasterCreateOrder.waiting_for_year)
async def master_order_year(message: Message, state: FSMContext, db_user: dict):
    lang = lang_of(db_user)
    if _cancel_check(message.text):
        await _cancel(message, state, lang); return
    txt = message.text.strip()
    year = None
    if txt != "/skip":
        if txt.isdigit() and 1900 < int(txt) < 2100:
            year = int(txt)
        else:
            await message.answer(t("err_invalid_year", lang))
            return
    await state.update_data(year=year)
    await state.set_state(MasterCreateOrder.waiting_for_client_name)
    await message.answer(t("step_client_name", lang), parse_mode="HTML")


@router.message(MasterCreateOrder.waiting_for_client_name)
async def master_order_client_name(message: Message, state: FSMContext, db_user: dict):
    lang = lang_of(db_user)
    if _cancel_check(message.text):
        await _cancel(message, state, lang); return
    await state.update_data(client_name=message.text.strip())
    await state.set_state(MasterCreateOrder.waiting_for_client_phone)
    await message.answer(t("step_client_phone", lang), parse_mode="HTML")


@router.message(MasterCreateOrder.waiting_for_client_phone)
async def master_order_client_phone(message: Message, state: FSMContext, db_user: dict):
    lang = lang_of(db_user)
    if _cancel_check(message.text):
        await _cancel(message, state, lang); return
    phone = message.text.strip()
    if len(phone) < 7 or not any(c.isdigit() for c in phone):
        await message.answer(t("err_invalid_phone", lang))
        return
    await state.update_data(client_phone=phone)
    await state.set_state(MasterCreateOrder.waiting_for_problem)
    await message.answer(t("step_problem", lang), parse_mode="HTML")


@router.message(MasterCreateOrder.waiting_for_problem)
async def master_order_problem(message: Message, state: FSMContext, db_user: dict):
    lang = lang_of(db_user)
    if _cancel_check(message.text):
        await _cancel(message, state, lang); return
    await state.update_data(problem=message.text.strip())
    await state.set_state(MasterCreateOrder.waiting_for_work_desc)
    await message.answer(t("step_work_desc", lang), parse_mode="HTML")


@router.message(MasterCreateOrder.waiting_for_work_desc)
async def master_order_work_desc(message: Message, state: FSMContext, db_user: dict):
    lang = lang_of(db_user)
    if _cancel_check(message.text):
        await _cancel(message, state, lang); return
    work_desc = "" if message.text.strip() == "/skip" else message.text.strip()
    await state.update_data(work_desc=work_desc)
    await state.set_state(MasterCreateOrder.waiting_for_price)
    await message.answer(t("step_price", lang), parse_mode="HTML")


@router.message(MasterCreateOrder.waiting_for_price)
async def master_order_price(message: Message, state: FSMContext, db_user: dict):
    lang = lang_of(db_user)
    if _cancel_check(message.text):
        await _cancel(message, state, lang); return
    amount = _parse_amount(message.text)
    if amount is None:
        await message.answer(t("err_invalid_amount", lang))
        return
    await state.update_data(agreed_price=amount)
    await state.set_state(MasterCreateOrder.waiting_for_paid)
    await message.answer(t("step_paid", lang), parse_mode="HTML")


@router.message(MasterCreateOrder.waiting_for_paid)
async def master_order_paid(message: Message, state: FSMContext, db_user: dict):
    lang = lang_of(db_user)
    if _cancel_check(message.text):
        await _cancel(message, state, lang); return
    paid = _parse_amount(message.text)
    if paid is None:
        await message.answer(t("err_invalid_amount", lang))
        return
    data = await state.get_data()
    price = data.get("agreed_price", 0)
    if paid > price:
        await message.answer(t("err_paid_too_much", lang, paid=paid, price=price))
        return
    await state.update_data(paid_amount=paid)
    await state.set_state(MasterCreateOrder.waiting_for_photos)
    await message.answer(t("step_photos", lang), parse_mode="HTML")


@router.message(MasterCreateOrder.waiting_for_photos)
async def master_order_photos(message: Message, state: FSMContext, db_user: dict):
    lang = lang_of(db_user)
    if _cancel_check(message.text):
        await _cancel(message, state, lang); return

    data = await state.get_data()
    photos: list = data.get("photos", [])

    if message.text and message.text.strip() in ("/skip", "/done"):
        await _show_order_summary(message, state, lang)
        return

    if not message.photo:
        await message.answer(t("photo_prompt", lang))
        return

    file_id = message.photo[-1].file_id
    photos.append(file_id)
    await state.update_data(photos=photos)

    if len(photos) >= 2:
        await message.answer(t("photos_done", lang))
        await _show_order_summary(message, state, lang)
    else:
        await message.answer(t("photo_received", lang, count=len(photos)))


async def _show_order_summary(message: Message, state: FSMContext, lang: str = "uz"):
    data = await state.get_data()
    await state.set_state(MasterCreateOrder.waiting_for_confirm)
    price = data.get("agreed_price", 0)
    paid = data.get("paid_amount", 0)
    photos = data.get("photos", [])
    summary = (
        t("order_summary_title", lang)
        + "\n\n"
        + f"🚗 {t('order_lbl_car', lang)}:  <b>{data['brand']} {data['model']}</b>\n"
        + f"🔢 {t('order_lbl_status', lang) if False else 'Raqam/Номер'}:  <b>{data['plate']}</b>\n"
        + f"🎨 Rang/Цвет:  {data.get('color') or '—'}\n"
        + f"📅 Yil/Год:    {data.get('year') or '—'}\n"
        + f"👤 {t('order_lbl_client', lang)}:  <b>{data['client_name']}</b>\n"
        + f"📞 Tel:        {data['client_phone']}\n"
        + f"🔧 {t('order_lbl_problem', lang)}: {data['problem']}\n"
        + f"🛠 {t('order_lbl_work', lang)}:   {data.get('work_desc') or '—'}\n"
        + f"💰 {t('order_lbl_price', lang)}:   <b>{price:,}</b>\n"
        + f"💵 {t('order_lbl_advance', lang)}:  <b>{paid:,}</b>\n"
        + f"📷 Rasm/Фото:  {len(photos)}\n\n"
        + t("order_confirm_prompt", lang)
    )
    await message.answer(summary, parse_mode="HTML")


@router.message(MasterCreateOrder.waiting_for_confirm)
async def master_order_confirm(message: Message, state: FSMContext, db_user: dict):
    lang = lang_of(db_user)
    if _cancel_check(message.text) or _confirm_no(message.text):
        await _cancel(message, state, lang); return
    if not _confirm_yes(message.text):
        await message.answer(t("order_confirm_prompt", lang), parse_mode="HTML")
        return
    data = await state.get_data()
    await state.clear()
    try:
        order_number = await get_next_order_number()
        car_id = await create_car(
            order_number=order_number,
            brand=data["brand"],
            model=data["model"],
            plate=data["plate"],
            color=data.get("color") or "",
            year=data.get("year") or 0,
        )
        price = data.get("agreed_price", 0)
        paid = data.get("paid_amount", 0)
        order_id = await create_order(
            order_number=order_number,
            car_id=car_id,
            master_id=db_user["id"],
            client_name=data["client_name"],
            client_phone=data.get("client_phone") or "",
            problem=data["problem"],
            work_desc=data.get("work_desc") or "",
            agreed_price=price,
            paid_amount=paid,
        )
        for fid in data.get("photos", []):
            try:
                await add_photo(order_id, fid)
            except Exception:
                logger.warning("Failed to save photo for order %s", order_number)
        from bot.config import BOT_USERNAME
        await message.answer(
            t("order_created", lang,
              order_number=order_number,
              car=f"{data['brand']} {data['model']} | {data['plate']}",
              client_name=data["client_name"],
              client_phone=data.get("client_phone", ""),
              problem=data["problem"],
              price=price,
              paid=paid),
            parse_mode="HTML",
            reply_markup=get_main_keyboard("master", lang),
        )
        if BOT_USERNAME:
            deep_link = f"https://t.me/{BOT_USERNAME}?start={order_number}"
            await message.answer(
                t("share_link_msg", lang, link=deep_link),
                parse_mode="HTML",
                reply_markup=get_share_order_keyboard(order_number, lang=lang),
            )
    except Exception:
        logger.exception("Failed to create order")
        await message.answer(
            t("order_create_error", lang),
            reply_markup=get_main_keyboard("master", lang),
        )


# ---------------------------------------------------------------------------
# My Orders — paginated inline list
# ---------------------------------------------------------------------------

async def _build_order_list(master_id: int, page: int = 1):
    all_orders = await get_orders_by_master(master_id)
    active = [dict(o) for o in all_orders if o["status"] in _ACTIVE]
    total = len(active)
    total_pages = max(1, math.ceil(total / _PAGE))
    page = max(1, min(page, total_pages))
    page_items = active[(page - 1) * _PAGE: page * _PAGE]
    return active, page_items, total, total_pages, page


@router.message(F.text.in_(all_variants("btn_my_orders")))
async def master_my_orders_handler(message: Message, db_user: dict):
    if not isinstance(db_user, dict) or db_user.get("role") not in ("master", "admin"):
        return
    lang = lang_of(db_user)
    active, page_items, total, total_pages, page = await _build_order_list(db_user["id"])
    if not active:
        await message.answer(t("no_active_orders_master", lang), parse_mode="HTML")
        return
    await message.answer(
        t("my_orders_header", lang, total=total, page=page, total_pages=total_pages),
        parse_mode="HTML",
        reply_markup=get_master_order_list_keyboard(page_items, page, total_pages),
    )


@router.callback_query(F.data.startswith("mst_order_page:"))
async def master_orders_page_callback(callback: CallbackQuery, db_user: dict):
    if not isinstance(db_user, dict) or db_user.get("role") not in ("master", "admin"):
        await callback.answer(t("no_access", lang_of(db_user))); return
    lang = lang_of(db_user)
    page = int(callback.data.split(":")[1])
    active, page_items, total, total_pages, page = await _build_order_list(db_user["id"], page)
    await callback.message.edit_text(
        t("my_orders_header", lang, total=total, page=page, total_pages=total_pages),
        parse_mode="HTML",
        reply_markup=get_master_order_list_keyboard(page_items, page, total_pages),
    )
    await callback.answer()


@router.callback_query(F.data == "mst_orders_back")
async def master_orders_back_callback(callback: CallbackQuery, db_user: dict):
    if not isinstance(db_user, dict) or db_user.get("role") not in ("master", "admin"):
        await callback.answer(t("no_access", lang_of(db_user))); return
    lang = lang_of(db_user)
    active, page_items, total, total_pages, _ = await _build_order_list(db_user["id"])
    await callback.message.edit_text(
        t("my_orders_header", lang, total=total, page=1, total_pages=total_pages),
        parse_mode="HTML",
        reply_markup=get_master_order_list_keyboard(page_items, 1, total_pages),
    )
    await callback.answer()


# ---------------------------------------------------------------------------
# Closed Orders History
# ---------------------------------------------------------------------------

@router.message(F.text.in_(all_variants("btn_closed_orders")))
async def master_closed_orders_handler(message: Message, db_user: dict):
    if not isinstance(db_user, dict) or db_user.get("role") not in ("master", "admin"):
        return
    lang = lang_of(db_user)
    all_orders = await get_orders_by_master(db_user["id"])
    closed = [o for o in (all_orders or []) if o["status"] == "closed"]
    if not closed:
        await message.answer(t("no_closed_orders_master", lang), parse_mode="HTML")
        return
    lines = []
    for o in closed[:20]:
        car = f"{o.get('brand','') or ''} {o.get('model','') or ''}".strip() or "—"
        lines.append(
            f"<b>{o['order_number']}</b> | {car} | {o.get('plate','—')} | "
            f"{format_money(o.get('agreed_price',0))} | {format_datetime(o.get('created_at'))}"
        )
    header = t("closed_orders_header", lang, total=len(closed))
    await message.answer(header + "\n".join(lines), parse_mode="HTML")


# ---------------------------------------------------------------------------
# Order detail view
# ---------------------------------------------------------------------------

def _order_text(order: dict, lang: str = "uz") -> str:
    car = f"{order.get('brand', '') or ''} {order.get('model', '') or ''}".strip() or "—"
    client = order.get("client_full_name") or order.get("client_name") or "—"
    paid_flag = "✅" if order.get("client_confirmed") else "⏳"
    lines = [
        f"📋 <b>{order['order_number']}</b>",
        f"{t('order_lbl_status', lang)}: {format_order_status(order['status'], lang)}",
        f"{t('order_lbl_car', lang)}: {car} | {order.get('plate', '—')}",
        f"{t('order_lbl_client', lang)}: {client}  |  📞 {order.get('client_phone') or order.get('client_phone_num') or '—'}",
        f"{t('order_lbl_problem', lang)}: {order.get('problem') or '—'}",
        f"{t('order_lbl_work', lang)}: {order.get('work_desc') or '—'}",
        f"{t('order_lbl_price', lang)}: {format_money(order.get('agreed_price', 0))}  |  {t('order_lbl_advance', lang)}: {format_money(order.get('paid_amount', 0))}",
        f"{t('order_lbl_confirmed', lang)}: {paid_flag}",
        f"{t('order_lbl_date', lang)}: {format_datetime(order.get('created_at'))}",
    ]
    return "\n".join(lines)


@router.callback_query(F.data.startswith("mst_order_view:"))
async def master_order_view_callback(callback: CallbackQuery, db_user: dict):
    if not isinstance(db_user, dict) or db_user.get("role") not in ("master", "admin"):
        await callback.answer(t("no_access", lang_of(db_user))); return
    lang = lang_of(db_user)
    order_number = callback.data.split(":", 1)[1]
    order = await get_order_detail(order_number)
    if not order:
        await callback.answer(t("order_not_found_short", lang)); return
    order = dict(order)
    confirmed = bool(order.get("client_confirmed"))
    has_client = bool(order.get("client_id"))
    await callback.message.edit_text(
        _order_text(order, lang), parse_mode="HTML",
        reply_markup=get_master_order_detail_keyboard(
            order["order_number"], order["status"], confirmed, has_client, lang=lang
        ),
    )
    await callback.answer()


# ---------------------------------------------------------------------------
# Status change + client notification on "ready"
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("mst_status:"))
async def master_status_change_callback(callback: CallbackQuery, db_user: dict):
    if not isinstance(db_user, dict) or db_user.get("role") not in ("master", "admin"):
        await callback.answer(t("no_access", lang_of(db_user))); return
    lang = lang_of(db_user)

    parts = callback.data.split(":")
    order_number, new_status = parts[1], parts[2]

    valid = {"new": "preparation", "preparation": "in_process", "in_process": "ready"}
    order_now = await get_order_detail(order_number)
    if not order_now:
        await callback.answer(t("order_not_found_short", lang)); return
    if valid.get(order_now["status"]) != new_status:
        await callback.answer(t("cant_change_status", lang)); return

    try:
        await update_order_status(
            order_number, new_status,
            note=f"Master changed status to {new_status}",
            changed_by=db_user["id"],
        )
    except Exception:
        logger.exception("Failed to update order status")
        await callback.answer(t("error_generic", lang)); return

    if new_status == "ready":
        try:
            client_id = order_now.get("client_id")
            if client_id:
                client = await get_user_by_id(client_id)
                if client and client.get("telegram_id"):
                    client_lang = client.get("language") or "uz"
                    notify_client_receipt_request(client["telegram_id"], order_number, lang=client_lang)
        except Exception:
            logger.warning("Failed to notify client for order %s", order_number)

    order = dict(await get_order_detail(order_number))
    confirmed = bool(order.get("client_confirmed"))
    has_client = bool(order.get("client_id"))
    await callback.message.edit_text(
        t("status_updated", lang) + "\n\n" + _order_text(order, lang),
        parse_mode="HTML",
        reply_markup=get_master_order_detail_keyboard(
            order["order_number"], order["status"], confirmed, has_client, lang=lang
        ),
    )
    await callback.answer(t("status_updated", lang))


# ---------------------------------------------------------------------------
# Financial close — master enters parts cost after client confirms
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("mst_close:"))
async def master_close_order_start(callback: CallbackQuery, db_user: dict, state: FSMContext):
    if not isinstance(db_user, dict) or db_user.get("role") not in ("master", "admin"):
        await callback.answer(t("no_access", lang_of(db_user))); return
    lang = lang_of(db_user)
    order_number = callback.data.split(":", 1)[1]
    order = await get_order_detail(order_number)
    if not order or not order.get("client_confirmed"):
        await callback.answer(t("client_not_confirmed", lang)); return
    await state.update_data(close_order_number=order_number, close_agreed_price=order["agreed_price"])
    await state.set_state(MasterCloseOrder.waiting_for_parts_cost)
    await callback.message.answer(
        t("parts_cost_prompt", lang,
          order_number=order_number,
          agreed=format_money(order["agreed_price"])),
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard(lang),
    )
    await callback.answer()


@router.message(MasterCloseOrder.waiting_for_parts_cost)
async def master_close_parts_cost(message: Message, state: FSMContext, db_user: dict):
    lang = lang_of(db_user)
    if _cancel_check(message.text):
        await _cancel(message, state, lang); return
    parts_cost = _parse_amount(message.text)
    if parts_cost is None:
        await message.answer(t("err_invalid_parts", lang))
        return
    data = await state.get_data()
    agreed = data.get("close_agreed_price", 0) or 0
    profit = max(0, agreed - parts_cost)
    ratio = await _master_share_ratio(db_user["id"])
    master_share = int(profit * ratio)
    service_share = profit - master_share
    master_pct = int(ratio * 100)
    service_pct = 100 - master_pct

    await state.update_data(
        close_parts_cost=parts_cost,
        close_profit=profit,
        close_master_share=master_share,
        close_service_share=service_share,
    )
    await state.set_state(MasterCloseOrder.waiting_for_confirm)
    await message.answer(
        t("financial_report", lang,
          order_number=data["close_order_number"],
          agreed=agreed,
          parts=parts_cost,
          profit=profit,
          master_share=master_share,
          master_pct=master_pct,
          service_share=service_share,
          service_pct=service_pct),
        parse_mode="HTML",
    )


@router.message(MasterCloseOrder.waiting_for_confirm)
async def master_close_confirm(message: Message, state: FSMContext, db_user: dict):
    lang = lang_of(db_user)
    if _cancel_check(message.text) or _confirm_no(message.text):
        await state.set_state(MasterCloseOrder.waiting_for_parts_cost)
        await message.answer(t("parts_retry", lang))
        return
    if not _confirm_yes(message.text):
        await message.answer(t("order_confirm_prompt", lang), parse_mode="HTML")
        return
    data = await state.get_data()
    await state.clear()
    order_number = data["close_order_number"]
    try:
        await close_order(
            order_number=order_number,
            parts_cost=data["close_parts_cost"],
            profit=data["close_profit"],
            master_share=data["close_master_share"],
            service_share=data["close_service_share"],
            changed_by=db_user["id"],
        )
        admins = await get_users_by_role("admin")
        from bot.utils.notification_queue import notification_queue
        admin_msg = t("admin_order_closed_msg", "uz",
                      order_number=order_number,
                      master_name=db_user.get("full_name", "—"),
                      parts=data["close_parts_cost"],
                      profit=data["close_profit"],
                      master_share=data["close_master_share"],
                      service_share=data["close_service_share"])
        for admin in admins:
            if admin.get("telegram_id"):
                notification_queue.enqueue(telegram_id=admin["telegram_id"], message=admin_msg)

        await message.answer(
            t("order_closed_success", lang,
              order_number=order_number,
              share=data["close_master_share"]),
            parse_mode="HTML",
            reply_markup=get_main_keyboard("master", lang),
        )
    except Exception:
        logger.exception("Failed to close order %s", order_number)
        await message.answer(t("order_closed_error", lang), reply_markup=get_main_keyboard("master", lang))


# ---------------------------------------------------------------------------
# Add parts cost to active order (item_name + amount + receipt photo)
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("mst_add_parts:"))
async def master_add_parts_start(callback: CallbackQuery, db_user: dict, state: FSMContext):
    if not isinstance(db_user, dict) or db_user.get("role") not in ("master", "admin"):
        await callback.answer(t("no_access", lang_of(db_user))); return
    lang = lang_of(db_user)
    order_number = callback.data.split(":", 1)[1]
    order = await get_order_detail(order_number)
    if not order:
        await callback.answer(t("order_not_found_short", lang)); return
    if order["status"] == "closed":
        await callback.answer(t("parts_closed_error", lang)); return
    current_parts = int(order.get("parts_cost") or 0)
    await state.update_data(parts_order_number=order_number, parts_order_id=order["id"])
    await state.set_state(MasterUpdateParts.waiting_for_item_name)
    await callback.message.answer(
        t("parts_add_title", lang, order_number=order_number, current=current_parts),
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard(lang),
    )
    await callback.answer()


@router.message(MasterUpdateParts.waiting_for_item_name)
async def master_add_parts_name(message: Message, state: FSMContext, db_user: dict):
    lang = lang_of(db_user)
    if _cancel_check(message.text):
        await _cancel(message, state, lang); return
    await state.update_data(parts_item_name=message.text.strip())
    await state.set_state(MasterUpdateParts.waiting_for_amount)
    await message.answer(t("parts_step_amount", lang), parse_mode="HTML")


@router.message(MasterUpdateParts.waiting_for_amount)
async def master_add_parts_amount(message: Message, state: FSMContext, db_user: dict):
    lang = lang_of(db_user)
    if _cancel_check(message.text):
        await _cancel(message, state, lang); return
    amount = _parse_amount(message.text)
    if amount is None or amount <= 0:
        await message.answer(t("err_positive_amount", lang))
        return
    await state.update_data(parts_amount=amount)
    await state.set_state(MasterUpdateParts.waiting_for_receipt)
    await message.answer(t("parts_step_receipt", lang), parse_mode="HTML")


@router.message(MasterUpdateParts.waiting_for_receipt)
async def master_add_parts_receipt(message: Message, state: FSMContext, db_user: dict):
    lang = lang_of(db_user)
    if _cancel_check(message.text):
        await _cancel(message, state, lang); return

    receipt_file_id = None
    if message.text and message.text.strip() == "/skip":
        pass
    elif message.photo:
        receipt_file_id = message.photo[-1].file_id
    elif not message.text:
        await message.answer(t("parts_photo_prompt", lang)); return
    else:
        await message.answer(t("parts_photo_prompt", lang)); return

    data = await state.get_data()
    order_number = data["parts_order_number"]
    order_id = data["parts_order_id"]
    item_name = data["parts_item_name"]
    amount = data["parts_amount"]
    await state.clear()
    try:
        await create_order_expense(
            order_id=order_id,
            item_name=item_name,
            amount=amount,
            receipt_file_id=receipt_file_id,
            added_by=db_user["id"],
        )
        await update_parts_cost(order_number, amount, changed_by=db_user["id"])
        order = dict(await get_order_detail(order_number))
        new_total = int(order.get("parts_cost") or 0)
        receipt_note = t("receipt_saved", lang) if receipt_file_id else ""
        await message.answer(
            t("parts_added", lang,
              order_number=order_number,
              item_name=item_name,
              amount=amount,
              receipt_note=receipt_note,
              total=new_total),
            parse_mode="HTML",
            reply_markup=get_main_keyboard("master", lang),
        )
    except Exception:
        logger.exception("Failed to add expense for %s", order_number)
        await message.answer(t("parts_add_error", lang), reply_markup=get_main_keyboard("master", lang))


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

@router.message(F.text.in_(all_variants("btn_statistics")))
async def master_statistics_handler(message: Message, db_user: dict):
    if not isinstance(db_user, dict) or db_user.get("role") not in ("master", "admin"):
        return
    from datetime import datetime
    lang = lang_of(db_user)
    now = datetime.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    summary = await get_financial_summary_by_master(db_user["id"], month_start, now)
    if not summary or summary["order_count"] == 0:
        await message.answer(t("no_statistics", lang))
        return

    await message.answer(
        t("statistics_report", lang,
          orders=summary["order_count"],
          revenue=format_money(summary["total_price"]),
          parts=format_money(summary["total_parts"]),
          profit=format_money(summary["total_profit"]),
          share=format_money(summary["total_master_share"])),
        parse_mode="HTML",
    )

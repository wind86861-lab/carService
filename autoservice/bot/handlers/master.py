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

def _cancel_check(text: str) -> bool:
    return text == "❌ Bekor qilish"


async def _cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=get_main_keyboard("master"))


def _parse_amount(text: str):
    """Return int from a money string, or None if invalid."""
    clean = text.strip().replace(" ", "").replace(",", "").replace("_", "")
    return int(clean) if clean.isdigit() else None


# ---------------------------------------------------------------------------
# New Order — full FSM flow in Telegram
# ---------------------------------------------------------------------------

@router.message(F.text == "🆕 Yangi buyurtma")
async def master_new_order_handler(message: Message, db_user: dict, state: FSMContext):
    if not isinstance(db_user, dict) or db_user.get("role") not in ("master", "admin"):
        return
    await state.set_state(MasterCreateOrder.waiting_for_brand)
    await message.answer(
        "🆕 <b>Yangi buyurtma</b>\n\n"
        "1️⃣ Mashina <b>markasini</b> kiriting:\n(masalan: Chevrolet, Nexia, Matiz)",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard(),
    )


@router.message(MasterCreateOrder.waiting_for_brand)
async def master_order_brand(message: Message, state: FSMContext):
    if _cancel_check(message.text):
        await _cancel(message, state); return
    await state.update_data(brand=message.text.strip())
    await state.set_state(MasterCreateOrder.waiting_for_model)
    await message.answer("2️⃣ Mashina <b>modelini</b> kiriting:", parse_mode="HTML")


@router.message(MasterCreateOrder.waiting_for_model)
async def master_order_model(message: Message, state: FSMContext):
    if _cancel_check(message.text):
        await _cancel(message, state); return
    await state.update_data(model=message.text.strip())
    await state.set_state(MasterCreateOrder.waiting_for_plate)
    await message.answer(
        "3️⃣ Davlat <b>raqamini</b> kiriting:\n(masalan: 01A123BB)",
        parse_mode="HTML",
    )


@router.message(MasterCreateOrder.waiting_for_plate)
async def master_order_plate(message: Message, state: FSMContext):
    if _cancel_check(message.text):
        await _cancel(message, state); return
    await state.update_data(plate=message.text.strip().upper())
    await state.set_state(MasterCreateOrder.waiting_for_color)
    await message.answer("4️⃣ Mashina <b>rangini</b> kiriting yoki /skip:", parse_mode="HTML")


@router.message(MasterCreateOrder.waiting_for_color)
async def master_order_color(message: Message, state: FSMContext):
    if _cancel_check(message.text):
        await _cancel(message, state); return
    color = None if message.text.strip() == "/skip" else message.text.strip()
    await state.update_data(color=color)
    await state.set_state(MasterCreateOrder.waiting_for_year)
    await message.answer(
        "5️⃣ Ishlab chiqarilgan <b>yilini</b> kiriting yoki /skip:",
        parse_mode="HTML",
    )


@router.message(MasterCreateOrder.waiting_for_year)
async def master_order_year(message: Message, state: FSMContext):
    if _cancel_check(message.text):
        await _cancel(message, state); return
    txt = message.text.strip()
    year = None
    if txt != "/skip":
        if txt.isdigit() and 1900 < int(txt) < 2100:
            year = int(txt)
        else:
            await message.answer("❗ To'g'ri yil kiriting (masalan: 2018) yoki /skip")
            return
    await state.update_data(year=year)
    await state.set_state(MasterCreateOrder.waiting_for_client_name)
    await message.answer("6️⃣ Mijozning <b>ismi</b>:", parse_mode="HTML")


@router.message(MasterCreateOrder.waiting_for_client_name)
async def master_order_client_name(message: Message, state: FSMContext):
    if _cancel_check(message.text):
        await _cancel(message, state); return
    await state.update_data(client_name=message.text.strip())
    await state.set_state(MasterCreateOrder.waiting_for_client_phone)
    await message.answer(
        "7️⃣ Mijozning <b>telefon raqami</b>:\n(masalan: +998901234567)",
        parse_mode="HTML",
    )


@router.message(MasterCreateOrder.waiting_for_client_phone)
async def master_order_client_phone(message: Message, state: FSMContext):
    if _cancel_check(message.text):
        await _cancel(message, state); return
    phone = message.text.strip()
    if len(phone) < 7 or not any(c.isdigit() for c in phone):
        await message.answer("❗ To'g'ri telefon raqam kiriting (masalan: +998901234567):")
        return
    await state.update_data(client_phone=phone)
    await state.set_state(MasterCreateOrder.waiting_for_problem)
    await message.answer("8️⃣ <b>Muammo / nosozlik</b> tavsifini kiriting:", parse_mode="HTML")


@router.message(MasterCreateOrder.waiting_for_problem)
async def master_order_problem(message: Message, state: FSMContext):
    if _cancel_check(message.text):
        await _cancel(message, state); return
    await state.update_data(problem=message.text.strip())
    await state.set_state(MasterCreateOrder.waiting_for_work_desc)
    await message.answer(
        "9️⃣ <b>Bajariladigan ishlar</b> ro'yxatini kiriting yoki /skip:\n"
        "(masalan: motor yog'i almashtirish, filtr almashtirish)",
        parse_mode="HTML",
    )


@router.message(MasterCreateOrder.waiting_for_work_desc)
async def master_order_work_desc(message: Message, state: FSMContext):
    if _cancel_check(message.text):
        await _cancel(message, state); return
    work_desc = "" if message.text.strip() == "/skip" else message.text.strip()
    await state.update_data(work_desc=work_desc)
    await state.set_state(MasterCreateOrder.waiting_for_price)
    await message.answer(
        "🔟 Xizmat <b>narxini</b> kiriting (so'm):\n(masalan: 150000)",
        parse_mode="HTML",
    )


@router.message(MasterCreateOrder.waiting_for_price)
async def master_order_price(message: Message, state: FSMContext):
    if _cancel_check(message.text):
        await _cancel(message, state); return
    amount = _parse_amount(message.text)
    if amount is None:
        await message.answer("❗ Faqat raqam kiriting (masalan: 150000):")
        return
    await state.update_data(agreed_price=amount)
    await state.set_state(MasterCreateOrder.waiting_for_paid)
    await message.answer(
        "1️⃣1️⃣ Oldindan to'lov (<b>avans</b>) miqdori (so'm):\n(masalan: 50000, yoki 0)",
        parse_mode="HTML",
    )


@router.message(MasterCreateOrder.waiting_for_paid)
async def master_order_paid(message: Message, state: FSMContext):
    if _cancel_check(message.text):
        await _cancel(message, state); return
    paid = _parse_amount(message.text)
    if paid is None:
        await message.answer("❗ Faqat raqam kiriting (masalan: 50000 yoki 0):")
        return
    data = await state.get_data()
    price = data.get("agreed_price", 0)
    if paid > price:
        await message.answer(
            f"❗ Avans ({paid:,}) xizmat narxidan ({price:,}) ko'p bo'lishi mumkin emas.\n"
            "Qaytadan kiriting:"
        )
        return
    await state.update_data(paid_amount=paid)
    await state.set_state(MasterCreateOrder.waiting_for_photos)
    await message.answer(
        "1️⃣2️⃣ <b>Mashina rasmlarini</b> yuboring (1–2 ta).\n"
        "Tugatish uchun /done, o'tkazib yuborish uchun /skip:",
        parse_mode="HTML",
    )


@router.message(MasterCreateOrder.waiting_for_photos)
async def master_order_photos(message: Message, state: FSMContext):
    if _cancel_check(message.text):
        await _cancel(message, state); return

    data = await state.get_data()
    photos: list = data.get("photos", [])

    if message.text and message.text.strip() in ("/skip", "/done"):
        await _show_order_summary(message, state)
        return

    if not message.photo:
        await message.answer("Rasm yuboring yoki /done (tayyor) / /skip (o'tkazish):")
        return

    file_id = message.photo[-1].file_id
    photos.append(file_id)
    await state.update_data(photos=photos)

    if len(photos) >= 2:
        await message.answer("✅ 2 ta rasm qabul qilindi.")
        await _show_order_summary(message, state)
    else:
        await message.answer(
            f"✅ {len(photos)} ta rasm qabul qilindi. "
            "Yana 1 ta rasm yuboring yoki /done:"
        )


async def _show_order_summary(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.set_state(MasterCreateOrder.waiting_for_confirm)
    price = data.get("agreed_price", 0)
    paid = data.get("paid_amount", 0)
    photos = data.get("photos", [])
    summary = (
        "✅ <b>Buyurtmani tasdiqlang:</b>\n\n"
        f"🚗 Mashina:   <b>{data['brand']} {data['model']}</b>\n"
        f"🔢 Raqam:    <b>{data['plate']}</b>\n"
        f"🎨 Rang:     {data.get('color') or '—'}\n"
        f"📅 Yil:      {data.get('year') or '—'}\n"
        f"👤 Mijoz:    <b>{data['client_name']}</b>\n"
        f"📞 Tel:      {data['client_phone']}\n"
        f"🔧 Muammo:  {data['problem']}\n"
        f"🛠 Ishlar:   {data.get('work_desc') or '—'}\n"
        f"💰 Narx:     <b>{price:,} so'm</b>\n"
        f"💵 Avans:    <b>{paid:,} so'm</b>\n"
        f"📷 Rasmlar:  {len(photos)} ta\n\n"
        "Tasdiqlash uchun <b>Ha</b>, bekor qilish uchun <b>Yo'q</b> yuboring."
    )
    await message.answer(summary, parse_mode="HTML")


@router.message(MasterCreateOrder.waiting_for_confirm)
async def master_order_confirm(message: Message, state: FSMContext, db_user: dict):
    if _cancel_check(message.text) or message.text.lower() in ("yo'q", "yoq", "no", "n"):
        await _cancel(message, state); return
    if message.text.lower() not in ("ha", "yes", "y", "ok", "+"):
        await message.answer(
            "Tasdiqlash uchun <b>Ha</b>, bekor qilish uchun <b>Yo'q</b> yuboring.",
            parse_mode="HTML",
        )
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
            f"✅ <b>Buyurtma yaratildi!</b>\n\n"
            f"Buyurtma raqami: <b>{order_number}</b>\n"
            f"Mashina: {data['brand']} {data['model']} | {data['plate']}\n"
            f"Mijoz: {data['client_name']} | {data.get('client_phone', '')}\n"
            f"Muammo: {data['problem']}\n"
            f"Narx: {price:,} so'm | Avans: {paid:,} so'm",
            parse_mode="HTML",
            reply_markup=get_main_keyboard("master"),
        )
        if BOT_USERNAME:
            deep_link = f"https://t.me/{BOT_USERNAME}?start={order_number}"
            await message.answer(
                f"📤 <b>Mijozga havola:</b>\n"
                f"Quyidagi tugmani bosib havolani mijozga yuboring. "
                f"Mijoz havolaga bosib mashinasini kuzatadi.\n\n"
                f"<code>{deep_link}</code>",
                parse_mode="HTML",
                reply_markup=get_share_order_keyboard(order_number),
            )
    except Exception:
        logger.exception("Failed to create order")
        await message.answer(
            "❌ Buyurtma yaratishda xato yuz berdi.",
            reply_markup=get_main_keyboard("master"),
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


@router.message(F.text == "📋 Mening buyurtmalarim")
async def master_my_orders_handler(message: Message, db_user: dict):
    if not isinstance(db_user, dict) or db_user.get("role") not in ("master", "admin"):
        return
    active, page_items, total, total_pages, page = await _build_order_list(db_user["id"])
    if not active:
        await message.answer("📋 <b>Faol buyurtmalar yo'q.</b>", parse_mode="HTML")
        return
    await message.answer(
        f"📋 <b>Mening buyurtmalarim</b> ({total} ta faol)\nSahifa {page}/{total_pages}",
        parse_mode="HTML",
        reply_markup=get_master_order_list_keyboard(page_items, page, total_pages),
    )


@router.callback_query(F.data.startswith("mst_order_page:"))
async def master_orders_page_callback(callback: CallbackQuery, db_user: dict):
    if not isinstance(db_user, dict) or db_user.get("role") not in ("master", "admin"):
        await callback.answer("Ruxsat yo'q."); return
    page = int(callback.data.split(":")[1])
    active, page_items, total, total_pages, page = await _build_order_list(db_user["id"], page)
    await callback.message.edit_text(
        f"📋 <b>Mening buyurtmalarim</b> ({total} ta faol)\nSahifa {page}/{total_pages}",
        parse_mode="HTML",
        reply_markup=get_master_order_list_keyboard(page_items, page, total_pages),
    )
    await callback.answer()


@router.callback_query(F.data == "mst_orders_back")
async def master_orders_back_callback(callback: CallbackQuery, db_user: dict):
    if not isinstance(db_user, dict) or db_user.get("role") not in ("master", "admin"):
        await callback.answer("Ruxsat yo'q."); return
    active, page_items, total, total_pages, _ = await _build_order_list(db_user["id"])
    await callback.message.edit_text(
        f"📋 <b>Mening buyurtmalarim</b> ({total} ta faol)\nSahifa 1/{total_pages}",
        parse_mode="HTML",
        reply_markup=get_master_order_list_keyboard(page_items, 1, total_pages),
    )
    await callback.answer()


# ---------------------------------------------------------------------------
# Closed Orders History
# ---------------------------------------------------------------------------

@router.message(F.text == "📁 Yopilgan buyurtmalar")
async def master_closed_orders_handler(message: Message, db_user: dict):
    if not isinstance(db_user, dict) or db_user.get("role") not in ("master", "admin"):
        return
    all_orders = await get_orders_by_master(db_user["id"])
    closed = [o for o in (all_orders or []) if o["status"] == "closed"]
    if not closed:
        await message.answer("📁 <b>Yopilgan buyurtmalar yo'q.</b>", parse_mode="HTML")
        return
    lines = []
    for o in closed[:20]:
        car = f"{o.get('brand','') or ''} {o.get('model','') or ''}".strip() or "—"
        lines.append(
            f"<b>{o['order_number']}</b> | {car} | {o.get('plate','—')} | "
            f"{format_money(o.get('agreed_price',0))} | {format_datetime(o.get('created_at'))}"
        )
    header = f"📁 <b>Yopilgan buyurtmalar</b> ({len(closed)} ta)\n\n"
    await message.answer(header + "\n".join(lines), parse_mode="HTML")


# ---------------------------------------------------------------------------
# Order detail view
# ---------------------------------------------------------------------------

def _order_text(order: dict) -> str:
    car = f"{order.get('brand', '') or ''} {order.get('model', '') or ''}".strip() or "—"
    client = order.get("client_full_name") or order.get("client_name") or "—"
    paid_flag = "✅" if order.get("client_confirmed") else "⏳"
    lines = [
        f"📋 <b>{order['order_number']}</b>",
        f"Holat: {format_order_status(order['status'])}",
        f"Mashina: {car} | {order.get('plate', '—')}",
        f"Mijoz: {client}  |  📞 {order.get('client_phone') or order.get('client_phone_num') or '—'}",
        f"Muammo: {order.get('problem') or '—'}",
        f"Ish: {order.get('work_desc') or '—'}",
        f"Narx: {format_money(order.get('agreed_price', 0))}  |  Avans: {format_money(order.get('paid_amount', 0))}",
        f"Mijoz tasdiqladi: {paid_flag}",
        f"Sana: {format_datetime(order.get('created_at'))}",
    ]
    return "\n".join(lines)


@router.callback_query(F.data.startswith("mst_order_view:"))
async def master_order_view_callback(callback: CallbackQuery, db_user: dict):
    if not isinstance(db_user, dict) or db_user.get("role") not in ("master", "admin"):
        await callback.answer("Ruxsat yo'q."); return
    order_number = callback.data.split(":", 1)[1]
    order = await get_order_detail(order_number)
    if not order:
        await callback.answer("Buyurtma topilmadi."); return
    order = dict(order)
    confirmed = bool(order.get("client_confirmed"))
    has_client = bool(order.get("client_id"))
    await callback.message.edit_text(
        _order_text(order), parse_mode="HTML",
        reply_markup=get_master_order_detail_keyboard(
            order["order_number"], order["status"], confirmed, has_client
        ),
    )
    await callback.answer()


# ---------------------------------------------------------------------------
# Status change + client notification on "ready"
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("mst_status:"))
async def master_status_change_callback(callback: CallbackQuery, db_user: dict):
    if not isinstance(db_user, dict) or db_user.get("role") not in ("master", "admin"):
        await callback.answer("Ruxsat yo'q."); return

    parts = callback.data.split(":")
    order_number, new_status = parts[1], parts[2]

    valid = {"new": "preparation", "preparation": "in_process", "in_process": "ready"}
    order_now = await get_order_detail(order_number)
    if not order_now:
        await callback.answer("Buyurtma topilmadi."); return
    if valid.get(order_now["status"]) != new_status:
        await callback.answer("Bu holat o'zgartirib bo'lmaydi."); return

    try:
        await update_order_status(
            order_number, new_status,
            note=f"Master changed status to {new_status}",
            changed_by=db_user["id"],
        )
    except Exception:
        logger.exception("Failed to update order status")
        await callback.answer("❌ Xato yuz berdi."); return

    # Notify client when order is ready
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
        "✅ Holat yangilandi!\n\n" + _order_text(order),
        parse_mode="HTML",
        reply_markup=get_master_order_detail_keyboard(
            order["order_number"], order["status"], confirmed, has_client
        ),
    )
    await callback.answer("✅ Holat yangilandi!")


# ---------------------------------------------------------------------------
# Financial close — master enters parts cost after client confirms
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("mst_close:"))
async def master_close_order_start(callback: CallbackQuery, db_user: dict, state: FSMContext):
    if not isinstance(db_user, dict) or db_user.get("role") not in ("master", "admin"):
        await callback.answer("Ruxsat yo'q."); return
    order_number = callback.data.split(":", 1)[1]
    order = await get_order_detail(order_number)
    if not order or not order.get("client_confirmed"):
        await callback.answer("Mijoz hali tasdiqlamagan."); return
    await state.update_data(close_order_number=order_number, close_agreed_price=order["agreed_price"])
    await state.set_state(MasterCloseOrder.waiting_for_parts_cost)
    await callback.message.answer(
        f"💰 <b>{order_number}</b> — Moliyaviy hisobot\n\n"
        f"Kelishilgan narx: <b>{format_money(order['agreed_price'])}</b>\n\n"
        "Ehtiyot qismlar narxini (so'm) kiriting yoki 0:",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard(),
    )
    await callback.answer()


@router.message(MasterCloseOrder.waiting_for_parts_cost)
async def master_close_parts_cost(message: Message, state: FSMContext, db_user: dict):
    if _cancel_check(message.text):
        await _cancel(message, state); return
    parts_cost = _parse_amount(message.text)
    if parts_cost is None:
        await message.answer("❗ Faqat raqam kiriting (masalan: 30000 yoki 0):")
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
    report = (
        f"📊 <b>Moliyaviy hisobot — {data['close_order_number']}</b>\n\n"
        f"Kelishilgan narx:   <b>{agreed:,} so'm</b>\n"
        f"Ehtiyot qismlar:    <b>{parts_cost:,} so'm</b>\n"
        f"Foyda:              <b>{profit:,} so'm</b>\n"
        f"Sizning ulushingiz: <b>{master_share:,} so'm</b> ({master_pct}%)\n"
        f"Xizmat ulushi:      <b>{service_share:,} so'm</b> ({service_pct}%)\n\n"
        "Tasdiqlash uchun <b>Ha</b>, qayta kiritish uchun <b>Yo'q</b>."
    )
    await message.answer(report, parse_mode="HTML")


@router.message(MasterCloseOrder.waiting_for_confirm)
async def master_close_confirm(message: Message, state: FSMContext, db_user: dict):
    if _cancel_check(message.text) or message.text.lower() in ("yo'q", "yoq", "no", "n"):
        await state.set_state(MasterCloseOrder.waiting_for_parts_cost)
        await message.answer("Ehtiyot qismlar narxini qaytadan kiriting:")
        return
    if message.text.lower() not in ("ha", "yes", "y", "ok", "+"):
        await message.answer(
            "Tasdiqlash uchun <b>Ha</b>, qayta kiritish uchun <b>Yo'q</b>.",
            parse_mode="HTML",
        )
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
        # Notify admin
        admins = await get_users_by_role("admin")
        from bot.utils.notification_queue import notification_queue
        admin_msg = (
            f"💰 <b>Buyurtma yopildi — {order_number}</b>\n\n"
            f"Usta: {db_user.get('full_name', '—')}\n"
            f"Ehtiyot qismlar:    {data['close_parts_cost']:,} so'm\n"
            f"Foyda:              {data['close_profit']:,} so'm\n"
            f"Master ulushi:      {data['close_master_share']:,} so'm\n"
            f"Xizmat ulushi:      {data['close_service_share']:,} so'm"
        )
        for admin in admins:
            if admin.get("telegram_id"):
                notification_queue.enqueue(telegram_id=admin["telegram_id"], message=admin_msg)

        await message.answer(
            f"✅ <b>{order_number}</b> muvaffaqiyatli yopildi!\n\n"
            f"Sizning ulushingiz: <b>{data['close_master_share']:,} so'm</b>",
            parse_mode="HTML",
            reply_markup=get_main_keyboard("master"),
        )
    except Exception:
        logger.exception("Failed to close order %s", order_number)
        await message.answer("❌ Buyurtmani yopishda xato yuz berdi.", reply_markup=get_main_keyboard("master"))


# ---------------------------------------------------------------------------
# Add parts cost to active order (item_name + amount + receipt photo)
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("mst_add_parts:"))
async def master_add_parts_start(callback: CallbackQuery, db_user: dict, state: FSMContext):
    if not isinstance(db_user, dict) or db_user.get("role") not in ("master", "admin"):
        await callback.answer("Ruxsat yo'q."); return
    order_number = callback.data.split(":", 1)[1]
    order = await get_order_detail(order_number)
    if not order:
        await callback.answer("Buyurtma topilmadi."); return
    if order["status"] == "closed":
        await callback.answer("Yopilgan buyurtmaga qo'shib bo'lmaydi."); return
    current_parts = int(order.get("parts_cost") or 0)
    await state.update_data(parts_order_number=order_number, parts_order_id=order["id"])
    await state.set_state(MasterUpdateParts.waiting_for_item_name)
    await callback.message.answer(
        f"🔩 <b>{order_number}</b> — Xarajat qo'shish\n\n"
        f"Hozirgi jami xarajat: <b>{current_parts:,} so'm</b>\n\n"
        "1️⃣ Xarajat <b>nomini</b> kiriting:\n(masalan: Balon salidor, Moy filtri)",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard(),
    )
    await callback.answer()


@router.message(MasterUpdateParts.waiting_for_item_name)
async def master_add_parts_name(message: Message, state: FSMContext):
    if _cancel_check(message.text):
        await _cancel(message, state); return
    await state.update_data(parts_item_name=message.text.strip())
    await state.set_state(MasterUpdateParts.waiting_for_amount)
    await message.answer(
        "2️⃣ Narxini kiriting (so'm):\n(masalan: 3000)",
        parse_mode="HTML",
    )


@router.message(MasterUpdateParts.waiting_for_amount)
async def master_add_parts_amount(message: Message, state: FSMContext):
    if _cancel_check(message.text):
        await _cancel(message, state); return
    amount = _parse_amount(message.text)
    if amount is None or amount <= 0:
        await message.answer("❗ 0 dan katta raqam kiriting (masalan: 3000):")
        return
    await state.update_data(parts_amount=amount)
    await state.set_state(MasterUpdateParts.waiting_for_receipt)
    await message.answer(
        "3️⃣ <b>Chek rasmini</b> yuboring yoki /skip:\n"
        "(chek/kvitansiya rasmini yuklang)",
        parse_mode="HTML",
    )


@router.message(MasterUpdateParts.waiting_for_receipt)
async def master_add_parts_receipt(message: Message, state: FSMContext, db_user: dict):
    if _cancel_check(message.text):
        await _cancel(message, state); return

    receipt_file_id = None
    if message.text and message.text.strip() == "/skip":
        pass
    elif message.photo:
        receipt_file_id = message.photo[-1].file_id
    elif not message.text:
        await message.answer("Rasm yuboring yoki /skip:"); return
    else:
        await message.answer("Rasm yuboring yoki /skip:"); return

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
        await message.answer(
            f"✅ <b>{order_number}</b> — xarajat qo'shildi!\n\n"
            f"📦 {item_name}: <b>{amount:,} so'm</b>\n"
            f"{'📷 Chek saqlandi' if receipt_file_id else ''}\n"
            f"Jami xarajat: <b>{new_total:,} so'm</b>",
            parse_mode="HTML",
            reply_markup=get_main_keyboard("master"),
        )
    except Exception:
        logger.exception("Failed to add expense for %s", order_number)
        await message.answer("❌ Xato yuz berdi.", reply_markup=get_main_keyboard("master"))


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

@router.message(F.text == "📊 Statistika")
async def master_statistics_handler(message: Message, db_user: dict):
    from datetime import datetime
    now = datetime.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    summary = await get_financial_summary_by_master(db_user["id"], month_start, now)
    if not summary or summary["order_count"] == 0:
        await message.answer("Bu oy hali yopilgan buyurtmalar yo'q.")
        return

    txt = (
        "📊 <b>Shu oygi statistikangiz:</b>\n\n"
        f"Yopilgan buyurtmalar: <b>{summary['order_count']}</b>\n"
        f"Jami daromad:         <b>{format_money(summary['total_price'])}</b>\n"
        f"Ehtiyot qismlar:      <b>{format_money(summary['total_parts'])}</b>\n"
        f"Foyda:                <b>{format_money(summary['total_profit'])}</b>\n"
        f"Sizning ulushingiz:   <b>{format_money(summary['total_master_share'])}</b>"
    )
    await message.answer(txt, parse_mode="HTML")

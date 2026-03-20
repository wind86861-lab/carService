import logging
import math

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.database.models import (
    create_car,
    create_order,
    get_financial_summary_by_master,
    get_next_order_number,
    get_order_detail,
    get_orders_by_master,
    update_order_status,
)
from bot.keyboards.inline import (
    get_master_order_detail_keyboard,
    get_master_order_list_keyboard,
)
from bot.keyboards.reply import get_cancel_keyboard, get_main_keyboard
from bot.states import MasterCreateOrder
from bot.utils.formatters import format_datetime, format_money, format_order_status

logger = logging.getLogger(__name__)

router = Router()

_PAGE = 8
_ACTIVE = ["new", "preparation", "in_process", "ready"]


# ---------------------------------------------------------------------------
# New Order — full FSM flow in Telegram
# ---------------------------------------------------------------------------

@router.message(F.text == "🆕 Yangi buyurtma")
async def master_new_order_handler(message: Message, db_user: dict, state: FSMContext):
    if not isinstance(db_user, dict) or db_user.get("role") not in ("master", "admin"):
        return
    await state.set_state(MasterCreateOrder.waiting_for_brand)
    await message.answer(
        "🆕 <b>Yangi buyurtma</b>\n\n1️⃣ Mashina <b>markasini</b> kiriting:\n(masalan: Chevrolet, Nexia, Matiz)",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard(),
    )


@router.message(MasterCreateOrder.waiting_for_brand)
async def master_order_brand(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_main_keyboard("master"))
        return
    await state.update_data(brand=message.text.strip())
    await state.set_state(MasterCreateOrder.waiting_for_model)
    await message.answer("2️⃣ Mashina <b>modelini</b> kiriting:\n(masalan: Lacetti, 5-3, 3)", parse_mode="HTML")


@router.message(MasterCreateOrder.waiting_for_model)
async def master_order_model(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_main_keyboard("master"))
        return
    await state.update_data(model=message.text.strip())
    await state.set_state(MasterCreateOrder.waiting_for_plate)
    await message.answer("3️⃣ Davlat <b>raqamini</b> kiriting:\n(masalan: 01A123BB)", parse_mode="HTML")


@router.message(MasterCreateOrder.waiting_for_plate)
async def master_order_plate(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_main_keyboard("master"))
        return
    await state.update_data(plate=message.text.strip().upper())
    await state.set_state(MasterCreateOrder.waiting_for_color)
    await message.answer("4️⃣ Mashina <b>rangini</b> kiriting yoki /skip:", parse_mode="HTML")


@router.message(MasterCreateOrder.waiting_for_color)
async def master_order_color(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_main_keyboard("master"))
        return
    color = None if message.text.strip() == "/skip" else message.text.strip()
    await state.update_data(color=color)
    await state.set_state(MasterCreateOrder.waiting_for_year)
    await message.answer("5️⃣ Ishlab chiqarilgan <b>yilini</b> kiriting yoki /skip:", parse_mode="HTML")


@router.message(MasterCreateOrder.waiting_for_year)
async def master_order_year(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_main_keyboard("master"))
        return
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
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_main_keyboard("master"))
        return
    await state.update_data(client_name=message.text.strip())
    await state.set_state(MasterCreateOrder.waiting_for_client_phone)
    await message.answer("7️⃣ Mijozning <b>telefon raqami</b> yoki /skip:", parse_mode="HTML")


@router.message(MasterCreateOrder.waiting_for_client_phone)
async def master_order_client_phone(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_main_keyboard("master"))
        return
    phone = None if message.text.strip() == "/skip" else message.text.strip()
    await state.update_data(client_phone=phone)
    await state.set_state(MasterCreateOrder.waiting_for_problem)
    await message.answer("8️⃣ <b>Muammo/vazifa</b> tavsifini kiriting:", parse_mode="HTML")


@router.message(MasterCreateOrder.waiting_for_problem)
async def master_order_problem(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_main_keyboard("master"))
        return
    await state.update_data(problem=message.text.strip())
    data = await state.get_data()
    await state.set_state(MasterCreateOrder.waiting_for_confirm)
    summary = (
        "✅ <b>Buyurtmani tasdiqlang:</b>\n\n"
        f"🚗 Mashina:  <b>{data['brand']} {data['model']}</b>\n"
        f"🔢 Raqam:   <b>{data['plate']}</b>\n"
        f"🎨 Rang:    {data.get('color') or '—'}\n"
        f"📅 Yil:     {data.get('year') or '—'}\n"
        f"👤 Mijoz:   <b>{data['client_name']}</b>\n"
        f"📞 Tel:     {data.get('client_phone') or '—'}\n"
        f"🔧 Muammo: {data['problem']}\n\n"
        "Tasdiqlash uchun <b>Ha</b>, bekor qilish uchun <b>Yo'q</b> yuboring."
    )
    await message.answer(summary, parse_mode="HTML")


@router.message(MasterCreateOrder.waiting_for_confirm)
async def master_order_confirm(message: Message, state: FSMContext, db_user: dict):
    if message.text == "❌ Bekor qilish" or message.text.lower() in ("yo'q", "yoq", "no", "n"):
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_main_keyboard("master"))
        return
    if message.text.lower() not in ("ha", "yes", "y", "ok", "+"):
        await message.answer("Tasdiqlash uchun <b>Ha</b>, bekor qilish uchun <b>Yo'q</b> yuboring.", parse_mode="HTML")
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
        await create_order(
            order_number=order_number,
            car_id=car_id,
            master_id=db_user["id"],
            client_name=data["client_name"],
            client_phone=data.get("client_phone") or "",
            problem=data["problem"],
            work_desc="",
            agreed_price=0,
            paid_amount=0,
        )
        await message.answer(
            f"✅ <b>Buyurtma yaratildi!</b>\n\n"
            f"Buyurtma raqami: <b>{order_number}</b>\n"
            f"Mashina: {data['brand']} {data['model']} | {data['plate']}\n"
            f"Mijoz: {data['client_name']}\n"
            f"Muammo: {data['problem']}",
            parse_mode="HTML",
            reply_markup=get_main_keyboard("master"),
        )
    except Exception:
        logger.exception("Failed to create order")
        await message.answer("❌ Buyurtma yaratishda xato yuz berdi.", reply_markup=get_main_keyboard("master"))


# ---------------------------------------------------------------------------
# My Orders — paginated inline list
# ---------------------------------------------------------------------------

async def _build_order_list_message(master_id: int, page: int = 1):
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
    active, page_items, total, total_pages, page = await _build_order_list_message(db_user["id"])
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
        await callback.answer("Ruxsat yo'q.")
        return
    page = int(callback.data.split(":")[1])
    active, page_items, total, total_pages, page = await _build_order_list_message(db_user["id"], page)
    await callback.message.edit_text(
        f"📋 <b>Mening buyurtmalarim</b> ({total} ta faol)\nSahifa {page}/{total_pages}",
        parse_mode="HTML",
        reply_markup=get_master_order_list_keyboard(page_items, page, total_pages),
    )
    await callback.answer()


@router.callback_query(F.data == "mst_orders_back")
async def master_orders_back_callback(callback: CallbackQuery, db_user: dict):
    if not isinstance(db_user, dict) or db_user.get("role") not in ("master", "admin"):
        await callback.answer("Ruxsat yo'q.")
        return
    active, page_items, total, total_pages, _ = await _build_order_list_message(db_user["id"])
    await callback.message.edit_text(
        f"📋 <b>Mening buyurtmalarim</b> ({total} ta faol)\nSahifa 1/{total_pages}",
        parse_mode="HTML",
        reply_markup=get_master_order_list_keyboard(page_items, 1, total_pages),
    )
    await callback.answer()


# ---------------------------------------------------------------------------
# Order detail
# ---------------------------------------------------------------------------

def _format_order_detail(order: dict) -> str:
    car = f"{order.get('brand', '') or ''} {order.get('model', '') or ''}".strip() or "—"
    client = order.get("client_full_name") or order.get("client_name") or "—"
    txt = (
        f"📋 <b>{order['order_number']}</b>\n"
        f"Holat: {format_order_status(order['status'])}\n"
        f"Mashina: {car} | {order.get('plate', '—')}\n"
        f"Mijoz: {client}\n"
        f"Muammo: {order.get('problem') or '—'}\n"
        f"Ish tavsifi: {order.get('work_desc') or '—'}\n"
        f"Narx: {format_money(order.get('agreed_price', 0))}\n"
        f"Sana: {format_datetime(order.get('created_at'))}"
    )
    return txt


@router.callback_query(F.data.startswith("mst_order_view:"))
async def master_order_view_callback(callback: CallbackQuery, db_user: dict):
    if not isinstance(db_user, dict) or db_user.get("role") not in ("master", "admin"):
        await callback.answer("Ruxsat yo'q.")
        return
    order_number = callback.data.split(":", 1)[1]
    order = await get_order_detail(order_number)
    if not order:
        await callback.answer("Buyurtma topilmadi.")
        return
    order = dict(order)
    await callback.message.edit_text(
        _format_order_detail(order),
        parse_mode="HTML",
        reply_markup=get_master_order_detail_keyboard(order["order_number"], order["status"]),
    )
    await callback.answer()


# ---------------------------------------------------------------------------
# Status change
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("mst_status:"))
async def master_status_change_callback(callback: CallbackQuery, db_user: dict):
    if not isinstance(db_user, dict) or db_user.get("role") not in ("master", "admin"):
        await callback.answer("Ruxsat yo'q.")
        return
    parts = callback.data.split(":")
    order_number = parts[1]
    new_status = parts[2]

    valid = {"new": "preparation", "preparation": "in_process", "in_process": "ready"}
    order_now = await get_order_detail(order_number)
    if not order_now:
        await callback.answer("Buyurtma topilmadi.")
        return
    current = order_now["status"]
    if valid.get(current) != new_status:
        await callback.answer("Bu holat o'zgartirib bo'lmaydi.")
        return

    try:
        await update_order_status(
            order_number, new_status,
            note=f"Master changed status to {new_status}",
            changed_by=db_user["id"],
        )
    except Exception:
        logger.exception("Failed to update order status")
        await callback.answer("❌ Xato yuz berdi.")
        return

    order = await get_order_detail(order_number)
    order = dict(order)
    await callback.message.edit_text(
        f"✅ Holat yangilandi!\n\n" + _format_order_detail(order),
        parse_mode="HTML",
        reply_markup=get_master_order_detail_keyboard(order["order_number"], order["status"]),
    )
    await callback.answer("✅ Holat yangilandi!")


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

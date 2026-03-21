import logging
import math
import secrets
import string

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config import WEB_URL
from bot.database.models import (
    block_user,
    get_all_masters,
    get_all_orders,
    get_dashboard_stats,
    get_financial_summary_by_master,
    get_order_detail,
    unblock_user,
)
from bot.i18n import all_variants, lang_of, t
from bot.keyboards.inline import (
    get_admin_confirm_keyboard,
    get_admin_order_detail_keyboard,
    get_admin_order_keyboard,
    get_admin_orders_keyboard,
    get_admin_page_keyboard,
    get_admin_period_keyboard,
    get_admin_user_keyboard,
    get_broadcast_confirm_keyboard,
    get_broadcast_target_keyboard,
    get_clients_for_master_keyboard,
)
from bot.keyboards.reply import get_cancel_keyboard, get_main_keyboard
from bot.states import AdminBroadcast, AdminCreateMaster, AdminNewMaster, AdminSearch
from bot.utils.formatters import format_datetime, format_money, format_order_status

logger = logging.getLogger(__name__)

router = Router()

PAGE_SIZE = 8

_CANCEL_TEXTS = all_variants("btn_cancel")


def _require_admin(db_user: dict) -> bool:
    return db_user.get("role") == "admin"


def _cancel_check(text: str) -> bool:
    return text in _CANCEL_TEXTS


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

async def _get_all_clients(search: str | None = None, page: int = 1):
    from sqlalchemy import text
    from bot.database.connection import async_session
    offset = (page - 1) * PAGE_SIZE
    async with async_session() as session:
        if search:
            q = f"%{search}%"
            result = await session.execute(
                text("SELECT id, full_name, phone, telegram_id, is_active, role FROM users "
                     "WHERE role='client' AND (full_name ILIKE :q OR phone ILIKE :q) "
                     "ORDER BY id DESC LIMIT :limit OFFSET :offset"),
                {"q": q, "limit": PAGE_SIZE, "offset": offset},
            )
            count_r = await session.execute(
                text("SELECT COUNT(*) FROM users WHERE role='client' AND (full_name ILIKE :q OR phone ILIKE :q)"),
                {"q": q},
            )
        else:
            result = await session.execute(
                text("SELECT id, full_name, phone, telegram_id, is_active, role FROM users "
                     "WHERE role='client' ORDER BY id DESC LIMIT :limit OFFSET :offset"),
                {"limit": PAGE_SIZE, "offset": offset},
            )
            count_r = await session.execute(
                text("SELECT COUNT(*) FROM users WHERE role='client'")
            )
        total = count_r.scalar()
        return list(result.mappings().all()), total


async def _get_user_by_id(user_id: int) -> dict | None:
    from sqlalchemy import text
    from bot.database.connection import async_session
    async with async_session() as session:
        r = await session.execute(
            text("SELECT id, full_name, phone, telegram_id, is_active, role, username FROM users WHERE id = :id"),
            {"id": user_id},
        )
        row = r.mappings().first()
        return dict(row) if row else None


async def _get_user_orders_summary(user_id: int) -> dict:
    from sqlalchemy import text
    from bot.database.connection import async_session
    async with async_session() as session:
        r = await session.execute(
            text("SELECT COUNT(*) AS total, "
                 "SUM(CASE WHEN status='closed' THEN 1 ELSE 0 END) AS closed, "
                 "COALESCE(SUM(CASE WHEN status='closed' THEN agreed_price ELSE 0 END), 0) AS revenue "
                 "FROM orders WHERE master_id = :id OR client_id = :id"),
            {"id": user_id},
        )
        row = r.mappings().first()
        return dict(row) if row else {"total": 0, "closed": 0, "revenue": 0}


async def _get_financials(period: str = "month") -> dict:
    from datetime import datetime, timedelta
    from sqlalchemy import text
    from bot.database.connection import async_session
    now = datetime.now()
    if period == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "year":
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    async with async_session() as session:
        r = await session.execute(
            text("SELECT COUNT(*) AS orders, "
                 "COALESCE(SUM(agreed_price),0) AS revenue, "
                 "COALESCE(SUM(profit),0) AS profit, "
                 "COALESCE(SUM(master_share),0) AS master_share, "
                 "COALESCE(SUM(parts_cost),0) AS parts_cost "
                 "FROM orders WHERE status='closed' "
                 "AND closed_at >= CAST(:start AS timestamp) AND closed_at <= CAST(:end AS timestamp)"),
            {"start": start, "end": now},
        )
        row = r.mappings().first()
        return dict(row) if row else {}


async def _search_orders(query: str):
    from sqlalchemy import text
    from bot.database.connection import async_session
    q = f"%{query}%"
    async with async_session() as session:
        r = await session.execute(
            text("SELECT o.order_number, o.status, o.client_name, o.agreed_price, o.created_at, "
                 "c.brand, c.model, c.plate, m.full_name AS master_name "
                 "FROM orders o LEFT JOIN cars c ON c.id=o.car_id "
                 "LEFT JOIN users m ON m.id=o.master_id "
                 "WHERE o.order_number ILIKE :q OR c.plate ILIKE :q OR o.client_name ILIKE :q "
                 "ORDER BY o.created_at DESC LIMIT 10"),
            {"q": q},
        )
        return list(r.mappings().all())


async def _get_car_history(plate: str):
    from sqlalchemy import text
    from bot.database.connection import async_session
    async with async_session() as session:
        r = await session.execute(
            text("SELECT o.order_number, o.status, o.problem, o.work_desc, o.agreed_price, "
                 "o.created_at, o.closed_at, m.full_name AS master_name, "
                 "c.brand, c.model, c.plate "
                 "FROM orders o LEFT JOIN cars c ON c.id=o.car_id "
                 "LEFT JOIN users m ON m.id=o.master_id "
                 "WHERE c.plate ILIKE :plate ORDER BY o.created_at DESC LIMIT 10"),
            {"plate": plate.strip().upper()},
        )
        return list(r.mappings().all())


async def _promote_user(user_id: int) -> dict:
    from sqlalchemy import text
    from bot.database.connection import async_session
    from web.auth import hash_password
    async with async_session() as session:
        r = await session.execute(
            text("SELECT id, full_name, telegram_id, username FROM users WHERE id = :id"),
            {"id": user_id},
        )
        user = r.mappings().first()
        if not user:
            return {}
        username = user["username"]
        password = None
        if not username:
            base = (user["full_name"] or "master").lower().replace(" ", "")[:10]
            username = base + str(user_id)
            password = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(10))
            pwd_hash = hash_password(password)
            await session.execute(
                text("UPDATE users SET role='master', username=:u, password_hash=:p WHERE id=:id"),
                {"u": username, "p": pwd_hash, "id": user_id},
            )
        else:
            await session.execute(
                text("UPDATE users SET role='master' WHERE id=:id"),
                {"id": user_id},
            )
        await session.commit()
        return {"username": username, "password": password, "telegram_id": user["telegram_id"]}


async def _demote_user(user_id: int):
    from sqlalchemy import text
    from bot.database.connection import async_session
    async with async_session() as session:
        await session.execute(text("UPDATE users SET role='client' WHERE id=:id"), {"id": user_id})
        await session.commit()


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@router.message(F.text.in_(all_variants("btn_dashboard")))
async def admin_dashboard_handler(message: Message, db_user: dict):
    if not _require_admin(db_user):
        return
    lang = lang_of(db_user)
    try:
        stats = await get_dashboard_stats()
        text = t("dashboard", lang,
                 active=stats["active_orders"],
                 ready=stats["ready_orders"],
                 revenue=format_money(stats["month_revenue"]),
                 profit=format_money(stats["month_profit"]),
                 clients=stats["total_clients"],
                 masters=stats["total_masters"])
    except Exception:
        logger.exception("Failed to load dashboard stats")
        text = t("dashboard_error", lang)
    await message.answer(text, parse_mode="HTML")


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------

@router.message(F.text.in_(all_variants("btn_all_orders")))
async def admin_all_orders_handler(message: Message, db_user: dict):
    if not _require_admin(db_user):
        return
    lang = lang_of(db_user)
    try:
        result = await get_all_orders(page=1, page_size=PAGE_SIZE)
        items = [dict(o) for o in result.get("items", [])]
        total = result.get("total", 0)
        total_pages = max(1, math.ceil(total / PAGE_SIZE))
        await message.answer(
            t("all_orders_header", lang, total=total, page=1, total_pages=total_pages),
            parse_mode="HTML",
            reply_markup=get_admin_orders_keyboard(items, 1, total_pages),
        )
    except Exception:
        logger.exception("Failed to load orders list")
        await message.answer(t("orders_load_error", lang))


@router.callback_query(F.data.startswith("adm_orders_page:"))
async def admin_orders_page_callback(callback: CallbackQuery, db_user: dict):
    if not _require_admin(db_user):
        await callback.answer(t("no_access", lang_of(db_user)))
        return
    lang = lang_of(db_user)
    page = int(callback.data.split(":")[1])
    result = await get_all_orders(page=page, page_size=PAGE_SIZE)
    items = [dict(o) for o in result.get("items", [])]
    total = result.get("total", 0)
    total_pages = max(1, math.ceil(total / PAGE_SIZE))
    await callback.message.edit_text(
        t("all_orders_header", lang, total=total, page=page, total_pages=total_pages),
        parse_mode="HTML",
        reply_markup=get_admin_orders_keyboard(items, page, total_pages),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adm_order_view:"))
async def admin_order_view_callback(callback: CallbackQuery, db_user: dict):
    if not _require_admin(db_user):
        await callback.answer(t("no_access", lang_of(db_user)))
        return
    lang = lang_of(db_user)
    order_number = callback.data.split(":", 1)[1]
    order = await get_order_detail(order_number)
    if not order:
        await callback.answer(t("order_search_none", lang))
        return
    order = dict(order)
    car = f"{order.get('brand','') or ''} {order.get('model','') or ''}".strip() or "—"
    master = order.get("master_full_name") or order.get("master_name") or "—"
    client = order.get("client_full_name") or order.get("client_name") or "—"
    txt = (
        f"📋 <b>{order['order_number']}</b>\n"
        f"{t('order_lbl_status', lang)}: {format_order_status(order['status'], lang)}\n"
        f"{t('order_lbl_car', lang)}: {car} | {order.get('plate','—')}\n"
        f"{t('order_lbl_client', lang)}: {client}\n"
        f"{t('order_lbl_master', lang)}: {master}\n"
        f"{t('order_lbl_problem', lang)}: {order.get('problem') or '—'}\n"
        f"{t('order_lbl_work', lang)}: {order.get('work_desc') or '—'}\n"
        f"{t('order_lbl_price', lang)}: {format_money(order.get('agreed_price', 0))}\n"
        f"{t('order_lbl_date', lang)}: {format_datetime(order.get('created_at'))}"
    )
    if order.get("status") == "closed":
        txt += (
            f"\n💰 {t('order_lbl_parts', lang)}: {format_money(order.get('parts_cost', 0))}\n"
            f"{t('order_lbl_profit', lang)}: {format_money(order.get('profit', 0))}\n"
            f"{t('order_lbl_closed_at', lang)}: {format_datetime(order.get('closed_at'))}"
        )
    await callback.message.edit_text(
        txt, parse_mode="HTML",
        reply_markup=get_admin_order_detail_keyboard(order["order_number"], order["status"]),
    )
    await callback.answer()


@router.callback_query(F.data == "adm_order_search")
async def admin_order_search_start(callback: CallbackQuery, db_user: dict, state: FSMContext):
    if not _require_admin(db_user):
        await callback.answer(t("no_access", lang_of(db_user)))
        return
    lang = lang_of(db_user)
    await state.set_state(AdminSearch.waiting_for_order)
    await callback.message.answer(
        t("order_search_prompt", lang),
        reply_markup=get_cancel_keyboard(lang),
    )
    await callback.answer()


@router.callback_query(F.data == "adm_orders_back")
async def admin_orders_back_callback(callback: CallbackQuery, db_user: dict):
    if not _require_admin(db_user):
        await callback.answer(t("no_access", lang_of(db_user)))
        return
    lang = lang_of(db_user)
    result = await get_all_orders(page=1, page_size=PAGE_SIZE)
    items = [dict(o) for o in result.get("items", [])]
    total = result.get("total", 0)
    total_pages = max(1, math.ceil(total / PAGE_SIZE))
    await callback.message.edit_text(
        t("all_orders_header", lang, total=total, page=1, total_pages=total_pages),
        parse_mode="HTML",
        reply_markup=get_admin_orders_keyboard(items, 1, total_pages),
    )
    await callback.answer()


@router.message(AdminSearch.waiting_for_order)
async def admin_order_search_handler(message: Message, state: FSMContext, db_user: dict):
    lang = lang_of(db_user)
    if _cancel_check(message.text):
        await state.clear()
        await message.answer(t("cancelled", lang), reply_markup=get_main_keyboard("admin", lang))
        return
    await state.clear()
    orders = await _search_orders(message.text.strip())
    if not orders:
        await message.answer(t("order_search_none", lang), reply_markup=get_main_keyboard("admin", lang))
        return
    for o in orders:
        car = f"{o.get('brand','') or ''} {o.get('model','') or ''}".strip() or "—"
        txt = (
            f"<b>{o['order_number']}</b> | {car} | {o.get('plate','—')}\n"
            f"{t('order_lbl_status', lang)}: {format_order_status(o['status'], lang)} | {format_money(o.get('agreed_price',0))}\n"
            f"{t('order_lbl_client', lang)}: {o.get('client_name','—')} | {t('order_lbl_master', lang)}: {o.get('master_name','—')}\n"
            f"{t('order_lbl_date', lang)}: {format_datetime(o['created_at'])}"
        )
        await message.answer(txt, parse_mode="HTML",
                             reply_markup=get_admin_order_keyboard(o["order_number"], o["status"]))
    await message.answer(t("order_search_done", lang), reply_markup=get_main_keyboard("admin", lang))


@router.callback_query(F.data.startswith("adm_force_close:"))
async def admin_force_close_callback(callback: CallbackQuery, db_user: dict):
    if not _require_admin(db_user):
        await callback.answer(t("no_access", lang_of(db_user)))
        return
    lang = lang_of(db_user)
    order_number = callback.data.split(":", 1)[1]
    await callback.message.edit_text(
        t("force_close_confirm", lang, order_number=order_number, web_url=WEB_URL),
        parse_mode="HTML",
        reply_markup=get_admin_confirm_keyboard("force_close", order_number),
    )
    await callback.answer()


# ---------------------------------------------------------------------------
# Clients
# ---------------------------------------------------------------------------

@router.message(F.text.in_(all_variants("btn_clients")))
async def admin_clients_handler(message: Message, db_user: dict, state: FSMContext):
    if not _require_admin(db_user):
        return
    lang = lang_of(db_user)
    await state.set_state(AdminSearch.waiting_for_client)
    await message.answer(
        t("clients_search_prompt", lang),
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard(lang),
    )


@router.message(AdminSearch.waiting_for_client)
async def admin_client_search_handler(message: Message, state: FSMContext, db_user: dict):
    lang = lang_of(db_user)
    if _cancel_check(message.text):
        await state.clear()
        await message.answer(t("cancelled", lang), reply_markup=get_main_keyboard("admin", lang))
        return
    await state.clear()
    query = message.text.strip()
    search = None if query == "." else query
    clients, total = await _get_all_clients(search=search, page=1)
    if not clients:
        await message.answer(t("no_clients", lang), reply_markup=get_main_keyboard("admin", lang))
        return
    total_pages = max(1, math.ceil(total / PAGE_SIZE))
    lines = [t("clients_header", lang, total=total) + "\n"]
    for c in clients:
        status = "✅" if c["is_active"] else "🚫"
        lines.append(f"{status} <b>{c['full_name']}</b> | {c.get('phone','—')} | /client_{c['id']}")
    if total_pages > 1:
        lines.append(f"\n{t('order_lbl_date', lang)} 1/{total_pages}")
    await message.answer(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=get_admin_page_keyboard(1, total_pages, f"clients:{search or ''}") if total_pages > 1 else get_main_keyboard("admin", lang),
    )


@router.message(F.text.regexp(r"^/client_(\d+)$"))
async def admin_client_detail_handler(message: Message, db_user: dict):
    if not _require_admin(db_user):
        return
    lang = lang_of(db_user)
    user_id = int(message.text.split("_")[1])
    user = await _get_user_by_id(user_id)
    if not user:
        await message.answer(t("client_not_found_adm", lang))
        return
    summary = await _get_user_orders_summary(user_id)
    status = t("status_active", lang) if user["is_active"] else t("status_blocked", lang)
    text = t("client_detail", lang,
             name=user["full_name"],
             status=status,
             phone=user.get("phone") or "—",
             tg_id=user["telegram_id"],
             username=user.get("username") or "—",
             total=summary.get("total", 0),
             closed=summary.get("closed", 0),
             revenue=format_money(summary.get("revenue", 0)))
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_admin_user_keyboard(user_id, user["role"], user["is_active"]),
    )


# ---------------------------------------------------------------------------
# Masters
# ---------------------------------------------------------------------------

@router.message(F.text.in_(all_variants("btn_masters")))
async def admin_masters_handler(message: Message, db_user: dict):
    if not _require_admin(db_user):
        return
    lang = lang_of(db_user)
    result = await get_all_masters(page=1, page_size=PAGE_SIZE)
    masters = result.get("items", [])
    total = result.get("total", 0)
    total_pages = max(1, math.ceil(total / PAGE_SIZE))
    if not masters:
        await message.answer(t("no_masters_adm", lang))
        return
    lines = [t("masters_header", lang, total=total) + "\n"]
    for m in masters:
        status = "✅" if m.get("is_active") else "🚫"
        lines.append(f"{status} <b>{m['full_name']}</b> | {m.get('phone','—')} | /master_{m['id']}")
    await message.answer(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=get_admin_page_keyboard(1, total_pages, "masters") if total_pages > 1 else get_main_keyboard("admin", lang),
    )


@router.message(F.text.regexp(r"^/master_(\d+)$"))
async def admin_master_detail_handler(message: Message, db_user: dict):
    if not _require_admin(db_user):
        return
    lang = lang_of(db_user)
    user_id = int(message.text.split("_")[1])
    user = await _get_user_by_id(user_id)
    if not user:
        await message.answer(t("master_not_found_adm", lang))
        return
    summary = await _get_user_orders_summary(user_id)
    status = t("status_active", lang) if user["is_active"] else t("status_blocked", lang)
    text = t("master_detail", lang,
             name=user["full_name"],
             status=status,
             phone=user.get("phone") or "—",
             username=user.get("username") or "—",
             tg_id=user["telegram_id"],
             total=summary.get("total", 0),
             closed=summary.get("closed", 0),
             revenue=format_money(summary.get("revenue", 0)))
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_admin_user_keyboard(user_id, user["role"], user["is_active"]),
    )


# ---------------------------------------------------------------------------
# Pagination callback
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("adm_page:"))
async def admin_page_callback(callback: CallbackQuery, db_user: dict):
    if not _require_admin(db_user):
        await callback.answer(t("no_access", lang_of(db_user)))
        return
    lang = lang_of(db_user)
    _, entity_raw, page_str = callback.data.split(":", 2)
    page = int(page_str)
    entity_parts = entity_raw.split(":", 1)
    entity = entity_parts[0]
    search = entity_parts[1] if len(entity_parts) > 1 else None

    if entity == "masters":
        result = await get_all_masters(page=page, page_size=PAGE_SIZE)
        items = result.get("items", [])
        total = result.get("total", 0)
        total_pages = max(1, math.ceil(total / PAGE_SIZE))
        lines = [t("masters_header", lang, total=total) + f" — {page}/{total_pages}:\n"]
        for m in items:
            s = "✅" if m.get("is_active") else "🚫"
            lines.append(f"{s} <b>{m['full_name']}</b> | {m.get('phone','—')} | /master_{m['id']}")
        await callback.message.edit_text(
            "\n".join(lines),
            parse_mode="HTML",
            reply_markup=get_admin_page_keyboard(page, total_pages, "masters"),
        )
    elif entity == "clients":
        clients, total = await _get_all_clients(search=search or None, page=page)
        total_pages = max(1, math.ceil(total / PAGE_SIZE))
        lines = [t("clients_header", lang, total=total) + f" — {page}/{total_pages}:\n"]
        for c in clients:
            s = "✅" if c["is_active"] else "🚫"
            lines.append(f"{s} <b>{c['full_name']}</b> | {c.get('phone','—')} | /client_{c['id']}")
        await callback.message.edit_text(
            "\n".join(lines),
            parse_mode="HTML",
            reply_markup=get_admin_page_keyboard(page, total_pages, f"clients:{search or ''}"),
        )
    await callback.answer()


@router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery):
    await callback.answer()


# ---------------------------------------------------------------------------
# User actions (block/unblock/promote/demote)
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("adm_block:"))
async def admin_block_callback(callback: CallbackQuery, db_user: dict):
    if not _require_admin(db_user):
        await callback.answer(t("no_access", lang_of(db_user)))
        return
    lang = lang_of(db_user)
    user_id = int(callback.data.split(":")[1])
    await callback.message.edit_reply_markup(
        reply_markup=get_admin_confirm_keyboard("block", str(user_id))
    )
    await callback.answer(t("confirm_action", lang))


@router.callback_query(F.data.startswith("adm_unblock:"))
async def admin_unblock_callback(callback: CallbackQuery, db_user: dict):
    if not _require_admin(db_user):
        await callback.answer(t("no_access", lang_of(db_user)))
        return
    lang = lang_of(db_user)
    user_id = int(callback.data.split(":")[1])
    await callback.message.edit_reply_markup(
        reply_markup=get_admin_confirm_keyboard("unblock", str(user_id))
    )
    await callback.answer(t("confirm_action", lang))


@router.callback_query(F.data.startswith("adm_promote:"))
async def admin_promote_callback(callback: CallbackQuery, db_user: dict):
    if not _require_admin(db_user):
        await callback.answer(t("no_access", lang_of(db_user)))
        return
    lang = lang_of(db_user)
    user_id = int(callback.data.split(":")[1])
    await callback.message.edit_reply_markup(
        reply_markup=get_admin_confirm_keyboard("promote", str(user_id))
    )
    await callback.answer(t("confirm_action", lang))


@router.callback_query(F.data.startswith("adm_demote:"))
async def admin_demote_callback(callback: CallbackQuery, db_user: dict):
    if not _require_admin(db_user):
        await callback.answer(t("no_access", lang_of(db_user)))
        return
    lang = lang_of(db_user)
    user_id = int(callback.data.split(":")[1])
    await callback.message.edit_reply_markup(
        reply_markup=get_admin_confirm_keyboard("demote", str(user_id))
    )
    await callback.answer(t("confirm_action", lang))


@router.callback_query(F.data.startswith("adm_confirm:"))
async def admin_confirm_action_callback(callback: CallbackQuery, db_user: dict):
    if not _require_admin(db_user):
        await callback.answer(t("no_access", lang_of(db_user)))
        return
    lang = lang_of(db_user)
    parts = callback.data.split(":")
    action = parts[1]
    target = parts[2]

    try:
        if action == "block":
            await block_user(int(target))
            await callback.message.edit_text(t("user_blocked_msg", lang, target=target))
        elif action == "unblock":
            await unblock_user(int(target))
            await callback.message.edit_text(t("user_unblocked_msg", lang, target=target))
        elif action == "promote":
            result = await _promote_user(int(target))
            msg = t("user_promoted_msg", lang, target=target)
            if result.get("password") and result.get("telegram_id"):
                from bot.config import BOT_TOKEN
                import httpx
                creds_msg = t("master_credentials_msg", lang,
                              web_url=WEB_URL,
                              username=result["username"],
                              password=result["password"])
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                        json={"chat_id": result["telegram_id"], "text": creds_msg},
                        timeout=5.0,
                    )
                msg += t("credentials_sent", lang)
            await callback.message.edit_text(msg)
        elif action == "demote":
            await _demote_user(int(target))
            await callback.message.edit_text(t("user_demoted_msg", lang, target=target))
        elif action == "force_close":
            await callback.message.edit_text(
                t("force_close_redirect", lang, web_url=WEB_URL)
            )
    except Exception:
        logger.exception("Admin confirm action failed: %s %s", action, target)
        await callback.message.edit_text(t("action_error", lang))
    await callback.answer()


@router.callback_query(F.data == "adm_cancel")
async def admin_cancel_callback(callback: CallbackQuery, db_user: dict):
    lang = lang_of(db_user)
    await callback.message.edit_text(t("action_cancelled", lang))
    await callback.answer()


# ---------------------------------------------------------------------------
# Financials
# ---------------------------------------------------------------------------

@router.message(F.text.in_(all_variants("btn_finance")))
async def admin_financials_handler(message: Message, db_user: dict):
    if not _require_admin(db_user):
        return
    lang = lang_of(db_user)
    await message.answer(
        t("financials_title", lang),
        parse_mode="HTML",
        reply_markup=get_admin_period_keyboard(),
    )


@router.callback_query(F.data.startswith("adm_period:"))
async def admin_period_callback(callback: CallbackQuery, db_user: dict):
    if not _require_admin(db_user):
        await callback.answer(t("no_access", lang_of(db_user)))
        return
    lang = lang_of(db_user)
    period = callback.data.split(":")[1]
    period_labels = {
        "today": t("period_today", lang),
        "week": t("period_week", lang),
        "month": t("period_month", lang),
        "year": t("period_year", lang),
    }
    try:
        data = await _get_financials(period)
        text = t("financials_report", lang,
                 period=period_labels.get(period, period),
                 orders=data.get("orders", 0),
                 revenue=format_money(data.get("revenue", 0)),
                 parts=format_money(data.get("parts_cost", 0)),
                 profit=format_money(data.get("profit", 0)),
                 master_share=format_money(data.get("master_share", 0)))
    except Exception:
        logger.exception("Failed to load financials")
        text = t("financials_error", lang)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_admin_period_keyboard())
    await callback.answer()


# ---------------------------------------------------------------------------
# Car History
# ---------------------------------------------------------------------------

@router.message(F.text.in_(all_variants("btn_car_history")))
async def admin_car_history_handler(message: Message, db_user: dict, state: FSMContext):
    if not _require_admin(db_user):
        return
    lang = lang_of(db_user)
    await state.set_state(AdminSearch.waiting_for_plate)
    await message.answer(
        t("car_history_prompt", lang),
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard(lang),
    )


@router.message(AdminSearch.waiting_for_plate)
async def admin_plate_search_handler(message: Message, state: FSMContext, db_user: dict):
    lang = lang_of(db_user)
    if _cancel_check(message.text):
        await state.clear()
        await message.answer(t("cancelled", lang), reply_markup=get_main_keyboard("admin", lang))
        return
    await state.clear()
    orders = await _get_car_history(message.text.strip())
    if not orders:
        await message.answer(
            t("car_not_found", lang, plate=message.text.upper()),
            parse_mode="HTML",
            reply_markup=get_main_keyboard("admin", lang),
        )
        return
    plate = orders[0].get("plate", message.text.upper())
    brand = f"{orders[0].get('brand','') or ''} {orders[0].get('model','') or ''}".strip()
    lines = [t("car_history_header", lang, plate=plate, brand=brand, count=len(orders))]
    for o in orders:
        lines.append(
            f"<b>{o['order_number']}</b> | {format_order_status(o['status'], lang)}\n"
            f"{t('order_lbl_problem', lang)}: {o.get('problem','—')}\n"
            f"{t('order_lbl_work', lang)}: {o.get('work_desc','—')}\n"
            f"{t('order_lbl_master', lang)}: {o.get('master_name','—')} | {format_money(o.get('agreed_price',0))}\n"
            f"{t('order_lbl_date', lang)}: {format_datetime(o.get('created_at'))}\n"
        )
    await message.answer("\n".join(lines), parse_mode="HTML", reply_markup=get_main_keyboard("admin", lang))


# ---------------------------------------------------------------------------
# Create Master
# ---------------------------------------------------------------------------

@router.message(F.text.in_(all_variants("btn_new_master")))
async def admin_create_master_handler(message: Message, db_user: dict):
    if not _require_admin(db_user):
        return
    lang = lang_of(db_user)
    clients, total = await _get_all_clients(page=1)
    total_pages = max(1, math.ceil(total / PAGE_SIZE))
    await message.answer(
        t("new_master_title", lang, total=total, page=1, total_pages=total_pages),
        parse_mode="HTML",
        reply_markup=get_clients_for_master_keyboard(clients, 1, total_pages),
    )


@router.callback_query(F.data.startswith("adm_nm_page:"))
async def admin_new_master_clients_page(callback: CallbackQuery, db_user: dict):
    if not _require_admin(db_user):
        await callback.answer(t("no_access", lang_of(db_user)))
        return
    lang = lang_of(db_user)
    page = int(callback.data.split(":")[1])
    clients, total = await _get_all_clients(page=page)
    total_pages = max(1, math.ceil(total / PAGE_SIZE))
    await callback.message.edit_text(
        t("new_master_title", lang, total=total, page=page, total_pages=total_pages),
        parse_mode="HTML",
        reply_markup=get_clients_for_master_keyboard(clients, page, total_pages),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adm_pick_client:"))
async def admin_pick_client_for_master(callback: CallbackQuery, db_user: dict, state: FSMContext):
    if not _require_admin(db_user):
        await callback.answer(t("no_access", lang_of(db_user)))
        return
    lang = lang_of(db_user)
    user_id = int(callback.data.split(":")[1])
    user = await _get_user_by_id(user_id)
    if not user:
        await callback.answer(t("client_not_found_adm", lang))
        return
    await state.update_data(promote_user_id=user_id, promote_full_name=user["full_name"])
    await state.set_state(AdminNewMaster.waiting_for_username)
    await callback.message.edit_text(
        t("new_master_selected", lang,
          name=user["full_name"],
          phone=user.get("phone") or "—"),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminNewMaster.waiting_for_username)
async def admin_new_master_username_handler(message: Message, state: FSMContext, db_user: dict):
    lang = lang_of(db_user)
    if _cancel_check(message.text):
        await state.clear()
        await message.answer(t("cancelled", lang), reply_markup=get_main_keyboard("admin", lang))
        return
    await state.update_data(new_username=message.text.strip())
    await state.set_state(AdminNewMaster.waiting_for_password)
    await message.answer(t("new_master_pwd_prompt", lang))


@router.message(AdminNewMaster.waiting_for_password)
async def admin_new_master_password_handler(message: Message, state: FSMContext, db_user: dict):
    lang = lang_of(db_user)
    if _cancel_check(message.text):
        await state.clear()
        await message.answer(t("cancelled", lang), reply_markup=get_main_keyboard("admin", lang))
        return
    data = await state.get_data()
    await state.clear()
    user_id = data["promote_user_id"]
    full_name = data["promote_full_name"]
    username_input = data.get("new_username", "/skip")
    password_input = message.text.strip()
    if username_input == "/skip":
        base = (full_name or "master").lower().replace(" ", "")[:10]
        username = base + str(user_id)
    else:
        username = username_input
    if password_input == "/skip":
        password = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(10))
    else:
        password = password_input
    try:
        from sqlalchemy import text as sqlt
        from bot.database.connection import async_session
        from web.auth import hash_password
        async with async_session() as session:
            existing = await session.execute(sqlt("SELECT id FROM users WHERE username=:u"), {"u": username})
            if existing.first():
                await message.answer(
                    t("username_taken", lang, username=username),
                    reply_markup=get_main_keyboard("admin", lang),
                )
                return
            pwd_hash = hash_password(password)
            await session.execute(
                sqlt("UPDATE users SET role='master', username=:u, password_hash=:p WHERE id=:id"),
                {"u": username, "p": pwd_hash, "id": user_id},
            )
            await session.commit()
        user = await _get_user_by_id(user_id)
        if user and user.get("telegram_id"):
            from bot.config import BOT_TOKEN
            import httpx
            creds = t("master_credentials_msg", lang,
                      web_url=WEB_URL,
                      username=username,
                      password=password)
            async with httpx.AsyncClient() as hc:
                await hc.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    json={"chat_id": user["telegram_id"], "text": creds},
                    timeout=5.0,
                )
        await message.answer(
            t("master_promoted_success", lang,
              name=full_name,
              username=username,
              password=password,
              web_url=WEB_URL),
            parse_mode="HTML",
            reply_markup=get_main_keyboard("admin", lang),
        )
    except Exception:
        logger.exception("Failed to promote client to master")
        await message.answer(t("master_promote_error", lang), reply_markup=get_main_keyboard("admin", lang))


# ---------------------------------------------------------------------------
# Broadcast
# ---------------------------------------------------------------------------

@router.message(F.text.in_(all_variants("btn_broadcast")))
async def admin_broadcast_handler(message: Message, state: FSMContext, db_user: dict):
    if not _require_admin(db_user):
        return
    lang = lang_of(db_user)
    await state.set_state(AdminBroadcast.waiting_for_target)
    await message.answer(
        t("broadcast_title", lang),
        parse_mode="HTML",
        reply_markup=get_broadcast_target_keyboard(),
    )


@router.callback_query(F.data.startswith("broadcast_target:"), AdminBroadcast.waiting_for_target)
async def admin_broadcast_target_callback(callback: CallbackQuery, state: FSMContext, db_user: dict):
    lang = lang_of(db_user)
    target = callback.data.split(":", 1)[1]
    audience_keys = {"all": "audience_all", "clients": "audience_clients", "masters": "audience_masters"}
    audience_label = t(audience_keys.get(target, "audience_all"), lang)
    await state.update_data(target=target)
    await state.set_state(AdminBroadcast.waiting_for_message)
    await callback.message.edit_text(
        t("broadcast_audience_set", lang, audience=audience_label),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminBroadcast.waiting_for_message)
async def admin_broadcast_message_handler(message: Message, state: FSMContext, db_user: dict):
    lang = lang_of(db_user)
    await state.update_data(message_text=message.text)
    await state.set_state(AdminBroadcast.waiting_for_confirm)
    data = await state.get_data()
    audience_keys = {"all": "audience_all", "clients": "audience_clients", "masters": "audience_masters"}
    audience_label = t(audience_keys.get(data["target"], "audience_all"), lang)
    preview = t("broadcast_preview", lang,
                audience=audience_label,
                text=message.text[:500])
    await message.answer(preview, parse_mode="HTML", reply_markup=get_broadcast_confirm_keyboard())


@router.callback_query(F.data == "broadcast_confirm", AdminBroadcast.waiting_for_confirm)
async def admin_broadcast_confirm_callback(callback: CallbackQuery, state: FSMContext, db_user: dict):
    lang = lang_of(db_user)
    data = await state.get_data()
    await state.clear()
    await callback.message.edit_text(t("broadcast_sending", lang))
    try:
        from web.utils.broadcast import send_broadcast
        result = await send_broadcast(data["target"], data["message_text"], db_user["id"])
        await callback.message.edit_text(
            t("broadcast_done", lang,
              sent=result["sent_count"],
              failed=result["failed_count"]),
            parse_mode="HTML",
        )
    except Exception:
        logger.exception("Broadcast failed")
        await callback.message.edit_text(t("broadcast_error", lang))
    await callback.answer()


@router.callback_query(F.data == "broadcast_cancel", AdminBroadcast.waiting_for_confirm)
async def admin_broadcast_cancel_callback(callback: CallbackQuery, state: FSMContext, db_user: dict):
    lang = lang_of(db_user)
    await state.clear()
    await callback.message.edit_text(t("action_cancelled", lang))
    await callback.answer()

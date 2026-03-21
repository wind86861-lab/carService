import asyncio

from sqlalchemy import text

from bot.database.connection import async_session

# ---------------------------------------------------------------------------
# Migration SQL statements
# ---------------------------------------------------------------------------

RUN_MIGRATIONS_SQL = [
    text("""
        CREATE TABLE IF NOT EXISTS users (
            id          SERIAL PRIMARY KEY,
            telegram_id BIGINT UNIQUE NOT NULL,
            full_name   TEXT NOT NULL,
            phone       TEXT,
            role        TEXT NOT NULL DEFAULT 'client',
            is_active   BOOLEAN NOT NULL DEFAULT TRUE,
            registered_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
    """),
    text("""
        CREATE TABLE IF NOT EXISTS cars (
            id           SERIAL PRIMARY KEY,
            order_number TEXT UNIQUE NOT NULL,
            brand        TEXT,
            model        TEXT,
            plate        TEXT,
            color        TEXT,
            year         INTEGER,
            client_id    INTEGER REFERENCES users(id),
            visit_count  INTEGER NOT NULL DEFAULT 1,
            created_at   TIMESTAMP NOT NULL DEFAULT NOW()
        );
    """),
    text("""
        CREATE TABLE IF NOT EXISTS orders (
            id               SERIAL PRIMARY KEY,
            order_number     TEXT UNIQUE NOT NULL,
            car_id           INTEGER REFERENCES cars(id),
            master_id        INTEGER REFERENCES users(id),
            client_id        INTEGER REFERENCES users(id),
            client_name      TEXT,
            client_phone     TEXT,
            problem          TEXT,
            work_desc        TEXT,
            agreed_price     NUMERIC NOT NULL DEFAULT 0,
            paid_amount      NUMERIC NOT NULL DEFAULT 0,
            parts_cost       NUMERIC NOT NULL DEFAULT 0,
            profit           NUMERIC NOT NULL DEFAULT 0,
            master_share     NUMERIC NOT NULL DEFAULT 0,
            service_share    NUMERIC NOT NULL DEFAULT 0,
            status           TEXT NOT NULL DEFAULT 'new',
            client_confirmed BOOLEAN NOT NULL DEFAULT FALSE,
            created_at       TIMESTAMP NOT NULL DEFAULT NOW(),
            ready_at         TIMESTAMP,
            closed_at        TIMESTAMP
        );
    """),
    text("""
        CREATE TABLE IF NOT EXISTS order_photos (
            id          SERIAL PRIMARY KEY,
            order_id    INTEGER REFERENCES orders(id),
            file_id     TEXT NOT NULL,
            uploaded_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
    """),
    text("""
        CREATE TABLE IF NOT EXISTS order_logs (
            id         SERIAL PRIMARY KEY,
            order_id   INTEGER REFERENCES orders(id),
            status     TEXT,
            note       TEXT,
            changed_by INTEGER REFERENCES users(id),
            changed_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
    """),
    text("""
        CREATE TABLE IF NOT EXISTS feedbacks (
            id         SERIAL PRIMARY KEY,
            order_id   INTEGER REFERENCES orders(id),
            client_id  INTEGER REFERENCES users(id),
            rating     INTEGER CHECK (rating >= 1 AND rating <= 10),
            category   TEXT,
            comment    TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
    """),
    text("""
        CREATE TABLE IF NOT EXISTS broadcasts (
            id         SERIAL PRIMARY KEY,
            sender_id  INTEGER REFERENCES users(id),
            target     TEXT,
            message    TEXT,
            sent_count INTEGER NOT NULL DEFAULT 0,
            sent_at    TIMESTAMP NOT NULL DEFAULT NOW()
        );
    """),
    text("""
        CREATE TABLE IF NOT EXISTS counters (
            name  TEXT PRIMARY KEY,
            value INTEGER NOT NULL DEFAULT 0
        );
    """),
    text("""
        INSERT INTO counters (name, value) VALUES ('order_seq', 0)
        ON CONFLICT DO NOTHING;
    """),
    # Indexes
    text("CREATE INDEX IF NOT EXISTS idx_users_telegram_id  ON users(telegram_id);"),
    text("CREATE INDEX IF NOT EXISTS idx_orders_number      ON orders(order_number);"),
    text("CREATE INDEX IF NOT EXISTS idx_orders_master_id   ON orders(master_id);"),
    text("CREATE INDEX IF NOT EXISTS idx_orders_client_id   ON orders(client_id);"),
    text("CREATE INDEX IF NOT EXISTS idx_orders_status      ON orders(status);"),
    text("CREATE INDEX IF NOT EXISTS idx_cars_plate         ON cars(plate);"),
    text("""
        CREATE TABLE IF NOT EXISTS order_expenses (
            id          SERIAL PRIMARY KEY,
            order_id    INTEGER REFERENCES orders(id) ON DELETE CASCADE,
            item_name   TEXT NOT NULL,
            amount      NUMERIC NOT NULL DEFAULT 0,
            receipt_file_id TEXT,
            added_by    INTEGER REFERENCES users(id),
            created_at  TIMESTAMP NOT NULL DEFAULT NOW()
        );
    """),
    text("CREATE INDEX IF NOT EXISTS idx_expenses_order_id ON order_expenses(order_id);"),
    text("ALTER TABLE users ADD COLUMN IF NOT EXISTS language TEXT NOT NULL DEFAULT 'uz';"),
]

# ---------------------------------------------------------------------------
# User CRUD
# ---------------------------------------------------------------------------


async def get_user_by_telegram_id(telegram_id: int):
    """Find a user by telegram_id. Returns the row or None."""
    async with async_session() as session:
        result = await session.execute(
            text("SELECT * FROM users WHERE telegram_id = :tid"),
            {"tid": telegram_id},
        )
        return result.mappings().first()


async def create_user(
    telegram_id: int, full_name: str, phone: str | None, role: str = "client"
):
    """Insert a new user. Uses ON CONFLICT DO NOTHING for safety. Returns the user row."""
    async with async_session() as session:
        await session.execute(
            text(
                "INSERT INTO users (telegram_id, full_name, phone, role) "
                "VALUES (:tid, :name, :phone, :role) "
                "ON CONFLICT (telegram_id) DO NOTHING"
            ),
            {"tid": telegram_id, "name": full_name, "phone": phone, "role": role},
        )
        await session.commit()
    return await get_user_by_telegram_id(telegram_id)


async def update_user_role(telegram_id: int, role: str):
    """Update the role field for the given telegram_id."""
    async with async_session() as session:
        await session.execute(
            text("UPDATE users SET role = :role WHERE telegram_id = :tid"),
            {"role": role, "tid": telegram_id},
        )
        await session.commit()


async def set_user_language(telegram_id: int, language: str):
    """Persist the UI language preference for a user ('uz' or 'ru')."""
    async with async_session() as session:
        await session.execute(
            text("UPDATE users SET language = :lang WHERE telegram_id = :tid"),
            {"lang": language, "tid": telegram_id},
        )
        await session.commit()


async def update_user_phone(telegram_id: int, phone: str):
    """Save the phone number for the given telegram_id."""
    async with async_session() as session:
        await session.execute(
            text("UPDATE users SET phone = :phone WHERE telegram_id = :tid"),
            {"phone": phone, "tid": telegram_id},
        )
        await session.commit()


async def get_master_total_earnings(master_id: int) -> int:
    """Return total agreed_price sum from all closed orders for a master (for bonus calc)."""
    async with async_session() as session:
        result = await session.execute(
            text(
                "SELECT COALESCE(SUM(agreed_price), 0) FROM orders "
                "WHERE master_id = :mid AND status = 'closed'"
            ),
            {"mid": master_id},
        )
        return int(result.scalar_one())


async def get_all_users():
    """Return all active users."""
    async with async_session() as session:
        result = await session.execute(
            text("SELECT * FROM users WHERE is_active = TRUE")
        )
        return result.mappings().all()


async def get_users_by_role(role: str):
    """Return all active users with the given role."""
    async with async_session() as session:
        result = await session.execute(
            text("SELECT * FROM users WHERE is_active = TRUE AND role = :role"),
            {"role": role},
        )
        return result.mappings().all()


# ---------------------------------------------------------------------------
# Counter
# ---------------------------------------------------------------------------


async def get_next_order_number() -> str:
    """Atomically increment order_seq and return formatted order number like A-0042."""
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                text(
                    "UPDATE counters SET value = value + 1 "
                    "WHERE name = 'order_seq' RETURNING value"
                )
            )
            value = result.scalar_one()
    return f"A-{value:04d}"


# ---------------------------------------------------------------------------
# User by internal ID
# ---------------------------------------------------------------------------


async def get_user_by_id(user_id: int):
    """Return the users row for the given internal id."""
    async with async_session() as session:
        result = await session.execute(
            text("SELECT * FROM users WHERE id = :uid"),
            {"uid": user_id},
        )
        return result.mappings().first()


# ---------------------------------------------------------------------------
# Order CRUD
# ---------------------------------------------------------------------------


async def get_order_by_number(order_number: str):
    """Find a single order row by its order_number. Returns the row or None."""
    async with async_session() as session:
        result = await session.execute(
            text("SELECT * FROM orders WHERE order_number = :num"),
            {"num": order_number},
        )
        return result.mappings().first()


async def get_orders_by_client(client_id: int):
    """Return all orders for a client, newest first."""
    async with async_session() as session:
        result = await session.execute(
            text(
                "SELECT * FROM orders WHERE client_id = :cid "
                "ORDER BY created_at DESC"
            ),
            {"cid": client_id},
        )
        return result.mappings().all()


async def link_client_to_order(order_number: str, client_id: int):
    """Set client_id on both the order and the matching car in a single transaction."""
    async with async_session() as session:
        async with session.begin():
            await session.execute(
                text(
                    "UPDATE orders SET client_id = :cid WHERE order_number = :num"
                ),
                {"cid": client_id, "num": order_number},
            )
            await session.execute(
                text(
                    "UPDATE cars SET client_id = :cid WHERE order_number = :num"
                ),
                {"cid": client_id, "num": order_number},
            )


async def confirm_client_receipt(
    order_number: str,
    profit: int = 0,
    master_share: int = 0,
    service_share: int = 0,
):
    """Set client_confirmed, calculate financials, and close the order."""
    async with async_session() as session:
        await session.execute(
            text(
                "UPDATE orders SET client_confirmed = TRUE, "
                "profit = :profit, master_share = :ms, service_share = :ss, "
                "status = 'closed', closed_at = NOW() "
                "WHERE order_number = :num"
            ),
            {
                "profit": profit, "ms": master_share,
                "ss": service_share, "num": order_number,
            },
        )
        await session.commit()


async def update_order_status(
    order_number: str,
    status: str,
    note: str | None = None,
    changed_by: int | None = None,
):
    """Update the status field on the order. Sets timestamps and writes an order_logs entry."""
    async with async_session() as session:
        async with session.begin():
            if status == "ready":
                result = await session.execute(
                    text(
                        "UPDATE orders SET status = :st, ready_at = NOW() "
                        "WHERE order_number = :num RETURNING id"
                    ),
                    {"st": status, "num": order_number},
                )
            elif status == "closed":
                result = await session.execute(
                    text(
                        "UPDATE orders SET status = :st, closed_at = NOW() "
                        "WHERE order_number = :num RETURNING id"
                    ),
                    {"st": status, "num": order_number},
                )
            else:
                result = await session.execute(
                    text(
                        "UPDATE orders SET status = :st WHERE order_number = :num RETURNING id"
                    ),
                    {"st": status, "num": order_number},
                )
            row = result.first()
            if row:
                await session.execute(
                    text(
                        "INSERT INTO order_logs (order_id, status, note, changed_by) "
                        "VALUES (:oid, :st, :note, :by)"
                    ),
                    {"oid": row[0], "st": status, "note": note, "by": changed_by},
                )


# ---------------------------------------------------------------------------
# Car CRUD
# ---------------------------------------------------------------------------


async def get_car_by_order_number(order_number: str):
    """Return the cars row whose order_number matches."""
    async with async_session() as session:
        result = await session.execute(
            text("SELECT * FROM cars WHERE order_number = :num"),
            {"num": order_number},
        )
        return result.mappings().first()


# ---------------------------------------------------------------------------
# Photos
# ---------------------------------------------------------------------------


async def get_photos_by_order(order_id: int):
    """Return all photos for an order, ordered by upload time."""
    async with async_session() as session:
        result = await session.execute(
            text(
                "SELECT * FROM order_photos WHERE order_id = :oid "
                "ORDER BY uploaded_at ASC"
            ),
            {"oid": order_id},
        )
        return result.mappings().all()


# ---------------------------------------------------------------------------
# Feedback
# ---------------------------------------------------------------------------


async def create_feedback(
    order_id: int,
    client_id: int,
    rating: int,
    category: str | None = None,
    comment: str | None = None,
):
    """Insert a new feedback row."""
    async with async_session() as session:
        await session.execute(
            text(
                "INSERT INTO feedbacks (order_id, client_id, rating, category, comment) "
                "VALUES (:oid, :cid, :rating, :cat, :cmt)"
            ),
            {
                "oid": order_id,
                "cid": client_id,
                "rating": rating,
                "cat": category,
                "cmt": comment,
            },
        )
        await session.commit()


async def get_feedback_by_order(order_id: int):
    """Return the feedback row for a given order, or None."""
    async with async_session() as session:
        result = await session.execute(
            text("SELECT * FROM feedbacks WHERE order_id = :oid"),
            {"oid": order_id},
        )
        return result.mappings().first()


# ---------------------------------------------------------------------------
# Car creation
# ---------------------------------------------------------------------------


async def create_car(
    order_number: str,
    brand: str,
    model: str,
    plate: str,
    color: str,
    year: int,
    client_id: int | None = None,
) -> int:
    """Insert a car row. Increments visit_count based on existing rows with the same plate."""
    async with async_session() as session:
        async with session.begin():
            max_result = await session.execute(
                text("SELECT COALESCE(MAX(visit_count), 0) FROM cars WHERE plate = :plate"),
                {"plate": plate},
            )
            visit_count = max_result.scalar_one() + 1
            result = await session.execute(
                text(
                    "INSERT INTO cars (order_number, brand, model, plate, color, year, client_id, visit_count) "
                    "VALUES (:num, :brand, :model, :plate, :color, :year, :cid, :vc) RETURNING id"
                ),
                {
                    "num": order_number, "brand": brand, "model": model,
                    "plate": plate, "color": color, "year": year,
                    "cid": client_id, "vc": visit_count,
                },
            )
            return result.scalar_one()


# ---------------------------------------------------------------------------
# Order creation
# ---------------------------------------------------------------------------


async def create_order(
    order_number: str,
    car_id: int,
    master_id: int,
    client_name: str,
    client_phone: str,
    problem: str,
    work_desc: str,
    agreed_price,
    paid_amount,
) -> int:
    """Insert order and initial log entry in a single transaction. Returns order id."""
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                text(
                    "INSERT INTO orders "
                    "(order_number, car_id, master_id, client_name, client_phone, problem, work_desc, agreed_price, paid_amount) "
                    "VALUES (:num, :cid, :mid, :cname, :cphone, :prob, :work, :price, :paid) RETURNING id"
                ),
                {
                    "num": order_number, "cid": car_id, "mid": master_id,
                    "cname": client_name, "cphone": client_phone,
                    "prob": problem, "work": work_desc,
                    "price": agreed_price, "paid": paid_amount,
                },
            )
            order_id = result.scalar_one()
            await session.execute(
                text(
                    "INSERT INTO order_logs (order_id, status, note, changed_by) "
                    "VALUES (:oid, 'new', 'Order created', :mid)"
                ),
                {"oid": order_id, "mid": master_id},
            )
            return order_id


# ---------------------------------------------------------------------------
# Photos
# ---------------------------------------------------------------------------


async def add_photo(order_id: int, file_id: str) -> int:
    """Insert a row into order_photos. Returns the new photo id."""
    async with async_session() as session:
        result = await session.execute(
            text(
                "INSERT INTO order_photos (order_id, file_id) "
                "VALUES (:oid, :fid) RETURNING id"
            ),
            {"oid": order_id, "fid": file_id},
        )
        await session.commit()
        return result.scalar_one()


async def count_photos(order_id: int) -> int:
    """Return how many photos exist for an order."""
    async with async_session() as session:
        result = await session.execute(
            text("SELECT COUNT(*) FROM order_photos WHERE order_id = :oid"),
            {"oid": order_id},
        )
        return result.scalar_one()


# ---------------------------------------------------------------------------
# Close order with financials
# ---------------------------------------------------------------------------


async def close_order(
    order_number: str,
    parts_cost,
    profit,
    master_share,
    service_share,
    changed_by: int | None = None,
):
    """Update all financial fields, set status to closed, write log entry."""
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                text(
                    "UPDATE orders SET "
                    "parts_cost = :pc, profit = :profit, master_share = :ms, service_share = :ss, "
                    "status = 'closed', closed_at = NOW() "
                    "WHERE order_number = :num RETURNING id"
                ),
                {
                    "pc": parts_cost, "profit": profit, "ms": master_share,
                    "ss": service_share, "num": order_number,
                },
            )
            row = result.first()
            if row:
                await session.execute(
                    text(
                        "INSERT INTO order_logs (order_id, status, note, changed_by) "
                        "VALUES (:oid, 'closed', 'Order closed by master', :by)"
                    ),
                    {"oid": row[0], "by": changed_by},
                )


# ---------------------------------------------------------------------------
# Orders by master
# ---------------------------------------------------------------------------


async def get_orders_by_master(master_id: int, status: str | None = None):
    """Return all orders for a master, newest first. Optional status filter."""
    async with async_session() as session:
        if status:
            result = await session.execute(
                text(
                    "SELECT o.*, c.brand, c.model, c.plate, c.color, c.year, c.visit_count "
                    "FROM orders o LEFT JOIN cars c ON c.id = o.car_id "
                    "WHERE o.master_id = :mid AND o.status = :st "
                    "ORDER BY o.created_at DESC"
                ),
                {"mid": master_id, "st": status},
            )
        else:
            result = await session.execute(
                text(
                    "SELECT o.*, c.brand, c.model, c.plate, c.color, c.year, c.visit_count "
                    "FROM orders o LEFT JOIN cars c ON c.id = o.car_id "
                    "WHERE o.master_id = :mid "
                    "ORDER BY o.created_at DESC"
                ),
                {"mid": master_id},
            )
        return result.mappings().all()


# ---------------------------------------------------------------------------
# Order detail (joined)
# ---------------------------------------------------------------------------


async def get_order_detail(order_number: str):
    """Return order joined with car and users in a single query."""
    async with async_session() as session:
        result = await session.execute(
            text(
                "SELECT "
                "o.id, o.order_number, o.car_id, o.master_id, o.client_id, "
                "o.client_name, o.client_phone, o.problem, o.work_desc, "
                "o.agreed_price, o.paid_amount, o.parts_cost, o.profit, "
                "o.master_share, o.service_share, o.status, o.client_confirmed, "
                "o.created_at, o.ready_at, o.closed_at, "
                "c.brand, c.model, c.plate, c.color, c.year, c.visit_count, "
                "c.order_number AS car_order_number, "
                "u.full_name AS client_full_name, u.phone AS client_phone_num, "
                "m.full_name AS master_full_name, m.telegram_id AS master_telegram_id "
                "FROM orders o "
                "LEFT JOIN cars c ON c.id = o.car_id "
                "LEFT JOIN users u ON u.id = o.client_id "
                "LEFT JOIN users m ON m.id = o.master_id "
                "WHERE o.order_number = :num"
            ),
            {"num": order_number},
        )
        return result.mappings().first()


# ---------------------------------------------------------------------------
# Order logs
# ---------------------------------------------------------------------------


async def get_order_logs(order_id: int):
    """Return all log entries for an order ordered by changed_at ascending."""
    async with async_session() as session:
        result = await session.execute(
            text(
                "SELECT ol.*, u.full_name AS changed_by_name "
                "FROM order_logs ol "
                "LEFT JOIN users u ON u.id = ol.changed_by "
                "WHERE ol.order_id = :oid "
                "ORDER BY ol.changed_at ASC"
            ),
            {"oid": order_id},
        )
        return result.mappings().all()


# ---------------------------------------------------------------------------
# Additional payment
# ---------------------------------------------------------------------------


async def add_payment(order_number: str, amount, changed_by: int | None = None):
    """Add to paid_amount and write a log entry."""
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                text(
                    "UPDATE orders SET paid_amount = paid_amount + :amount "
                    "WHERE order_number = :num RETURNING id, paid_amount"
                ),
                {"amount": amount, "num": order_number},
            )
            row = result.first()
            if row:
                await session.execute(
                    text(
                        "INSERT INTO order_logs (order_id, status, note, changed_by) "
                        "VALUES (:oid, NULL, :note, :by)"
                    ),
                    {
                        "oid": row[0],
                        "note": f"Payment recorded: {amount}. Total paid: {row[1]}",
                        "by": changed_by,
                    },
                )


async def create_order_expense(
    order_id: int,
    item_name: str,
    amount: int,
    receipt_file_id: str | None = None,
    added_by: int | None = None,
) -> int:
    """Insert an expense row for an order. Returns new expense id."""
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                text(
                    "INSERT INTO order_expenses (order_id, item_name, amount, receipt_file_id, added_by) "
                    "VALUES (:oid, :name, :amt, :rfid, :by) RETURNING id"
                ),
                {"oid": order_id, "name": item_name, "amt": amount, "rfid": receipt_file_id, "by": added_by},
            )
            return result.scalar_one()


async def get_expenses_by_order(order_id: int):
    """Return all expense rows for an order, oldest first."""
    async with async_session() as session:
        result = await session.execute(
            text(
                "SELECT e.*, u.full_name AS added_by_name "
                "FROM order_expenses e LEFT JOIN users u ON u.id = e.added_by "
                "WHERE e.order_id = :oid ORDER BY e.created_at ASC"
            ),
            {"oid": order_id},
        )
        return result.mappings().all()


async def update_parts_cost(order_number: str, add_amount: int, changed_by: int | None = None):
    """Add add_amount to parts_cost for the order and write a log entry."""
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                text(
                    "UPDATE orders SET parts_cost = COALESCE(parts_cost, 0) + :amt "
                    "WHERE order_number = :num RETURNING id, parts_cost"
                ),
                {"amt": add_amount, "num": order_number},
            )
            row = result.first()
            if row:
                await session.execute(
                    text(
                        "INSERT INTO order_logs (order_id, status, note, changed_by) "
                        "VALUES (:oid, 'parts_updated', :note, :by)"
                    ),
                    {
                        "oid": row[0],
                        "note": f"Parts cost updated: +{add_amount}, total={row[1]}",
                        "by": changed_by,
                    },
                )


# ---------------------------------------------------------------------------
# Car history by plate
# ---------------------------------------------------------------------------


async def get_orders_by_plate(plate: str):
    """Return all orders for a given plate, newest first."""
    async with async_session() as session:
        result = await session.execute(
            text(
                "SELECT o.*, c.brand, c.model, c.plate, c.color, c.year, c.visit_count "
                "FROM orders o JOIN cars c ON c.id = o.car_id "
                "WHERE c.plate = :plate "
                "ORDER BY o.created_at DESC"
            ),
            {"plate": plate.upper()},
        )
        return result.mappings().all()


# ---------------------------------------------------------------------------
# Financial aggregation
# ---------------------------------------------------------------------------


async def get_financial_summary_by_master(master_id: int, from_date, to_date):
    """Return aggregated financial sums for a master in a date range."""
    async with async_session() as session:
        result = await session.execute(
            text(
                "SELECT "
                "COUNT(id) AS order_count, "
                "COALESCE(SUM(agreed_price), 0) AS total_price, "
                "COALESCE(SUM(parts_cost), 0) AS total_parts, "
                "COALESCE(SUM(profit), 0) AS total_profit, "
                "COALESCE(SUM(master_share), 0) AS total_master_share "
                "FROM orders "
                "WHERE master_id = :mid AND status = 'closed' "
                "AND closed_at >= CAST(:from_date AS timestamp) AND closed_at <= CAST(:to_date AS timestamp)"
            ),
            {"mid": master_id, "from_date": from_date, "to_date": to_date},
        )
        return result.mappings().first()


async def get_order_financials(order_number: str):
    """Return financial fields for a single order."""
    async with async_session() as session:
        result = await session.execute(
            text(
                "SELECT agreed_price, paid_amount, parts_cost, profit, master_share, service_share "
                "FROM orders WHERE order_number = :num"
            ),
            {"num": order_number},
        )
        return result.mappings().first()


# ---------------------------------------------------------------------------
# Scheduler helpers
# ---------------------------------------------------------------------------


async def get_orders_closed_without_feedback():
    """Return orders closed over 1 hour ago that have no feedback yet."""
    async with async_session() as session:
        result = await session.execute(
            text(
                "SELECT o.id, o.order_number, o.client_id, u.telegram_id AS client_telegram_id "
                "FROM orders o "
                "JOIN users u ON u.id = o.client_id "
                "WHERE o.status = 'closed' "
                "AND o.closed_at < NOW() - INTERVAL '1 hour' "
                "AND o.client_id IS NOT NULL "
                "AND NOT EXISTS (SELECT 1 FROM feedbacks f WHERE f.order_id = o.id)"
            )
        )
        return result.mappings().all()


async def get_orders_pending_auto_confirm():
    """Return orders where client_confirmed is false and closed_at is over 72 hours ago."""
    async with async_session() as session:
        result = await session.execute(
            text(
                "SELECT o.id, o.order_number, o.client_id, u.telegram_id AS client_telegram_id "
                "FROM orders o "
                "JOIN users u ON u.id = o.client_id "
                "WHERE o.status = 'closed' "
                "AND o.client_confirmed = FALSE "
                "AND o.closed_at < NOW() - INTERVAL '72 hours' "
                "AND o.client_id IS NOT NULL"
            )
        )
        return result.mappings().all()


async def auto_confirm_order(order_number: str):
    """Set client_confirmed to true and write an auto-confirm log entry."""
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                text(
                    "UPDATE orders SET client_confirmed = TRUE "
                    "WHERE order_number = :num RETURNING id"
                ),
                {"num": order_number},
            )
            row = result.first()
            if row:
                await session.execute(
                    text(
                        "INSERT INTO order_logs (order_id, status, note, changed_by) "
                        "VALUES (:oid, NULL, 'Auto-confirmed after 72 hours', NULL)"
                    ),
                    {"oid": row[0]},
                )


# ---------------------------------------------------------------------------
# Step 5 — Admin functions
# ---------------------------------------------------------------------------


async def get_dashboard_stats() -> dict:
    """Return dashboard KPIs in a single call using parallel queries."""
    async with async_session() as session:
        active_q, ready_q, revenue_q, users_q = await asyncio.gather(
            session.execute(
                text("SELECT COUNT(*) FROM orders WHERE status IN ('new','preparation','in_process')")
            ),
            session.execute(text("SELECT COUNT(*) FROM orders WHERE status = 'ready'")),
            session.execute(
                text(
                    "SELECT COALESCE(SUM(agreed_price),0), COALESCE(SUM(profit),0) "
                    "FROM orders WHERE status='closed' "
                    "AND DATE_TRUNC('month', closed_at) = DATE_TRUNC('month', NOW())"
                )
            ),
            session.execute(
                text(
                    "SELECT "
                    "  (SELECT COUNT(*) FROM users WHERE role='client' AND is_active=TRUE), "
                    "  (SELECT COUNT(*) FROM users WHERE role='master' AND is_active=TRUE)"
                )
            ),
        )
        rev_row = revenue_q.first()
        usr_row = users_q.first()
        return {
            "active_orders": active_q.scalar(),
            "ready_orders": ready_q.scalar(),
            "month_revenue": float(rev_row[0]) if rev_row else 0.0,
            "month_profit": float(rev_row[1]) if rev_row else 0.0,
            "total_clients": usr_row[0] if usr_row else 0,
            "total_masters": usr_row[1] if usr_row else 0,
        }


async def get_all_orders(
    filters: dict | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """Return paginated orders with optional filters."""
    filters = filters or {}
    where = ["1=1"]
    params: dict = {}

    if filters.get("status"):
        where.append("o.status = :status")
        params["status"] = filters["status"]
    if filters.get("master_id"):
        where.append("o.master_id = :master_id")
        params["master_id"] = filters["master_id"]
    if filters.get("date_from"):
        where.append("o.created_at >= :date_from")
        params["date_from"] = filters["date_from"]
    if filters.get("date_to"):
        where.append("o.created_at <= :date_to")
        params["date_to"] = filters["date_to"]
    if filters.get("search"):
        where.append("(o.order_number ILIKE :search OR c.plate ILIKE :search OR o.client_name ILIKE :search)")
        params["search"] = f"%{filters['search']}%"

    where_sql = " AND ".join(where)
    offset = (page - 1) * page_size
    params["limit"] = page_size
    params["offset"] = offset

    base = (
        "FROM orders o "
        "LEFT JOIN cars c ON c.id = o.car_id "
        "LEFT JOIN users m ON m.id = o.master_id "
        f"WHERE {where_sql}"
    )
    async with async_session() as session:
        count_result = await session.execute(text(f"SELECT COUNT(*) {base}"), params)
        total = count_result.scalar()
        rows = await session.execute(
            text(
                f"SELECT o.*, c.brand, c.model, c.plate, c.color, c.year, "
                f"m.full_name AS master_name {base} "
                "ORDER BY o.created_at DESC LIMIT :limit OFFSET :offset"
            ),
            params,
        )
        return {"items": rows.mappings().all(), "total": total, "page": page, "page_size": page_size}


async def force_close_order(order_number: str, parts_cost: float, admin_id: int) -> dict | None:
    """Admin force-close: bypasses master check, records financials and log entry."""
    async with async_session() as session:
        async with session.begin():
            row = await session.execute(
                text("SELECT id, agreed_price, paid_amount FROM orders WHERE order_number = :num"),
                {"num": order_number},
            )
            order = row.first()
            if not order:
                return None
            order_id, agreed_price, paid_amount = order
            profit = float(agreed_price) - parts_cost
            master_share = round(profit * 0.4, 2)
            service_share = round(profit * 0.6, 2)
            result = await session.execute(
                text(
                    "UPDATE orders SET status='closed', parts_cost=:pc, profit=:pr, "
                    "master_share=:ms, service_share=:ss, closed_at=NOW() "
                    "WHERE order_number=:num RETURNING id, order_number, agreed_price, "
                    "parts_cost, profit, master_share, service_share"
                ),
                {
                    "pc": parts_cost, "pr": profit, "ms": master_share,
                    "ss": service_share, "num": order_number,
                },
            )
            updated = result.first()
            await session.execute(
                text(
                    "INSERT INTO order_logs (order_id, status, note, changed_by) "
                    "VALUES (:oid, 'closed', 'Force closed by admin', :adm)"
                ),
                {"oid": order_id, "adm": admin_id},
            )
            return dict(updated._mapping) if updated else None


async def get_all_clients(
    search: str | None = None,
    is_active: bool | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """Return paginated client list with order count and avg_rating."""
    where = ["u.role = 'client'"]
    params: dict = {}
    if search:
        where.append("(u.full_name ILIKE :search OR u.phone ILIKE :search)")
        params["search"] = f"%{search}%"
    if is_active is not None:
        where.append("u.is_active = :is_active")
        params["is_active"] = is_active
    where_sql = " AND ".join(where)
    offset = (page - 1) * page_size
    params["limit"] = page_size
    params["offset"] = offset

    async with async_session() as session:
        count_result = await session.execute(
            text(f"SELECT COUNT(*) FROM users u WHERE {where_sql}"), params
        )
        total = count_result.scalar()
        rows = await session.execute(
            text(
                f"SELECT u.id, u.full_name, u.phone, u.telegram_id, u.is_active, u.registered_at, "
                "COALESCE(stats.order_count, 0) AS order_count, "
                "COALESCE(stats.avg_rating, 0) AS avg_rating, "
                "stats.last_order_date "
                "FROM users u "
                "LEFT JOIN ("
                "  SELECT o.client_id, COUNT(o.id) AS order_count, "
                "  AVG(f.rating) AS avg_rating, MAX(o.created_at) AS last_order_date "
                "  FROM orders o LEFT JOIN feedbacks f ON f.order_id = o.id "
                "  GROUP BY o.client_id"
                ") stats ON stats.client_id = u.id "
                f"WHERE {where_sql} "
                "ORDER BY u.registered_at DESC LIMIT :limit OFFSET :offset"
            ),
            params,
        )
        return {"items": rows.mappings().all(), "total": total, "page": page, "page_size": page_size}


async def get_client_profile(client_id: int) -> dict | None:
    """Return full client profile including orders and feedbacks."""
    async with async_session() as session:
        user_row = await session.execute(
            text("SELECT * FROM users WHERE id = :id"), {"id": client_id}
        )
        user = user_row.mappings().first()
        if not user:
            return None
        orders_row = await session.execute(
            text(
                "SELECT o.*, c.brand, c.model, c.plate FROM orders o "
                "LEFT JOIN cars c ON c.id = o.car_id "
                "WHERE o.client_id = :cid ORDER BY o.created_at DESC"
            ),
            {"cid": client_id},
        )
        feedbacks_row = await session.execute(
            text(
                "SELECT f.*, o.order_number FROM feedbacks f "
                "JOIN orders o ON o.id = f.order_id "
                "WHERE f.client_id = :cid ORDER BY f.created_at DESC"
            ),
            {"cid": client_id},
        )
        return {
            "user": dict(user),
            "orders": list(orders_row.mappings().all()),
            "feedbacks": list(feedbacks_row.mappings().all()),
        }


async def get_all_masters(page: int = 1, page_size: int = 20) -> dict:
    """Return paginated master list with aggregated performance stats."""
    offset = (page - 1) * page_size
    async with async_session() as session:
        count_result = await session.execute(
            text("SELECT COUNT(*) FROM users WHERE role = 'master'")
        )
        total = count_result.scalar()
        rows = await session.execute(
            text(
                "SELECT u.id, u.full_name, u.phone, u.telegram_id, u.role, u.is_active, u.username, "
                "COALESCE(s.active_orders, 0) AS active_orders, "
                "COALESCE(s.closed_orders, 0) AS closed_orders, "
                "COALESCE(s.total_earned, 0) AS total_earned, "
                "COALESCE(r.avg_rating, 0) AS avg_rating "
                "FROM users u "
                "LEFT JOIN ("
                "  SELECT master_id, "
                "    SUM(CASE WHEN status IN ('new','preparation','in_process','ready') THEN 1 ELSE 0 END) AS active_orders, "
                "    SUM(CASE WHEN status='closed' THEN 1 ELSE 0 END) AS closed_orders, "
                "    SUM(CASE WHEN status='closed' THEN master_share ELSE 0 END) AS total_earned "
                "  FROM orders GROUP BY master_id"
                ") s ON s.master_id = u.id "
                "LEFT JOIN ("
                "  SELECT o.master_id, AVG(f.rating) AS avg_rating "
                "  FROM feedbacks f JOIN orders o ON o.id = f.order_id "
                "  GROUP BY o.master_id"
                ") r ON r.master_id = u.id "
                "WHERE u.role = 'master' "
                "ORDER BY u.full_name "
                "LIMIT :limit OFFSET :offset"
            ),
            {"limit": page_size, "offset": offset},
        )
        return {"items": rows.mappings().all(), "total": total, "page": page, "page_size": page_size}


async def get_master_profile(master_id: int, date_from=None, date_to=None) -> dict | None:
    """Return master with period stats and orders."""
    async with async_session() as session:
        user_row = await session.execute(
            text("SELECT * FROM users WHERE id = :id"), {"id": master_id}
        )
        user = user_row.mappings().first()
        if not user:
            return None
        where = ["o.master_id = :mid"]
        params: dict = {"mid": master_id}
        if date_from:
            where.append("o.closed_at >= :df")
            params["df"] = date_from
        if date_to:
            where.append("o.closed_at <= :dt")
            params["dt"] = date_to
        where_sql = " AND ".join(where)
        stats_row = await session.execute(
            text(
                f"SELECT COUNT(*) AS order_count, "
                "COALESCE(SUM(agreed_price),0) AS revenue, "
                "COALESCE(SUM(profit),0) AS profit, "
                "COALESCE(SUM(master_share),0) AS master_earned "
                f"FROM orders o WHERE status='closed' AND {where_sql}"
            ),
            params,
        )
        orders_row = await session.execute(
            text(
                "SELECT o.*, c.brand, c.model, c.plate FROM orders o "
                "LEFT JOIN cars c ON c.id = o.car_id "
                f"WHERE {where_sql} ORDER BY o.created_at DESC"
            ),
            params,
        )
        feedbacks_row = await session.execute(
            text(
                "SELECT f.*, o.order_number, u.full_name AS client_name "
                "FROM feedbacks f JOIN orders o ON o.id = f.order_id "
                "JOIN users u ON u.id = f.client_id "
                "WHERE o.master_id = :mid ORDER BY f.created_at DESC"
            ),
            {"mid": master_id},
        )
        stats = stats_row.mappings().first()
        return {
            "user": dict(user),
            "stats": dict(stats) if stats else {},
            "orders": list(orders_row.mappings().all()),
            "feedbacks": list(feedbacks_row.mappings().all()),
        }


async def get_financial_report(
    master_id: int | None = None,
    date_from=None,
    date_to=None,
) -> dict:
    """Return financial summary totals and per-order breakdown for closed orders."""
    where = ["o.status = 'closed'"]
    params: dict = {}
    if master_id:
        where.append("o.master_id = :master_id")
        params["master_id"] = master_id
    if date_from:
        where.append("o.closed_at >= :date_from")
        params["date_from"] = date_from
    if date_to:
        where.append("o.closed_at <= :date_to")
        params["date_to"] = date_to
    where_sql = " AND ".join(where)
    async with async_session() as session:
        summary_row = await session.execute(
            text(
                "SELECT COALESCE(SUM(agreed_price),0) AS total_revenue, "
                "COALESCE(SUM(parts_cost),0) AS total_parts_cost, "
                "COALESCE(SUM(profit),0) AS total_profit, "
                "COALESCE(SUM(service_share),0) AS total_service_share, "
                "COALESCE(SUM(master_share),0) AS total_master_share "
                f"FROM orders o WHERE {where_sql}"
            ),
            params,
        )
        orders_row = await session.execute(
            text(
                "SELECT o.order_number, m.full_name AS master_name, "
                "c.brand, c.model, c.plate, "
                "o.agreed_price, o.parts_cost, o.profit, o.master_share, o.service_share, "
                "o.closed_at "
                "FROM orders o "
                "LEFT JOIN users m ON m.id = o.master_id "
                "LEFT JOIN cars c ON c.id = o.car_id "
                f"WHERE {where_sql} ORDER BY o.closed_at DESC"
            ),
            params,
        )
        summary = dict(summary_row.mappings().first() or {})
        return {"summary": summary, "orders": list(orders_row.mappings().all())}


async def get_all_feedbacks(
    filters: dict | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """Return paginated feedbacks with client and master names."""
    filters = filters or {}
    where = ["1=1"]
    params: dict = {}
    if filters.get("master_id"):
        where.append("o.master_id = :master_id")
        params["master_id"] = filters["master_id"]
    if filters.get("rating_max"):
        where.append("f.rating <= :rating_max")
        params["rating_max"] = filters["rating_max"]
    if filters.get("date_from"):
        where.append("f.created_at >= :date_from")
        params["date_from"] = filters["date_from"]
    if filters.get("date_to"):
        where.append("f.created_at <= :date_to")
        params["date_to"] = filters["date_to"]
    where_sql = " AND ".join(where)
    offset = (page - 1) * page_size
    params["limit"] = page_size
    params["offset"] = offset

    base = (
        "FROM feedbacks f "
        "JOIN orders o ON o.id = f.order_id "
        "LEFT JOIN users cl ON cl.id = f.client_id "
        "LEFT JOIN users m ON m.id = o.master_id "
        f"WHERE {where_sql}"
    )
    async with async_session() as session:
        count_result = await session.execute(text(f"SELECT COUNT(*) {base}"), params)
        total = count_result.scalar()
        rows = await session.execute(
            text(
                f"SELECT f.id, f.rating, f.category, f.comment, f.created_at, "
                "o.order_number, cl.full_name AS client_name, m.full_name AS master_name "
                f"{base} ORDER BY f.created_at DESC LIMIT :limit OFFSET :offset"
            ),
            params,
        )
        return {"items": rows.mappings().all(), "total": total, "page": page, "page_size": page_size}


async def get_feedback_stats() -> dict:
    """Return overall avg_rating, distribution, category counts, per-master avg_rating."""
    async with async_session() as session:
        avg_row = await session.execute(
            text("SELECT COALESCE(AVG(rating),0) AS avg_rating, COUNT(*) AS total FROM feedbacks")
        )
        dist_rows = await session.execute(
            text(
                "SELECT gs.n AS score, COALESCE(cnt.c, 0) AS count "
                "FROM generate_series(1,10) gs(n) "
                "LEFT JOIN (SELECT rating, COUNT(*) AS c FROM feedbacks GROUP BY rating) cnt "
                "ON cnt.rating = gs.n ORDER BY gs.n"
            )
        )
        cat_rows = await session.execute(
            text(
                "SELECT COALESCE(category,'Uncategorized') AS category, COUNT(*) AS count "
                "FROM feedbacks GROUP BY category ORDER BY count DESC"
            )
        )
        master_rows = await session.execute(
            text(
                "SELECT m.full_name AS master_name, m.id AS master_id, "
                "AVG(f.rating) AS avg_rating, COUNT(f.id) AS total_feedback "
                "FROM feedbacks f "
                "JOIN orders o ON o.id = f.order_id "
                "JOIN users m ON m.id = o.master_id "
                "GROUP BY m.id, m.full_name ORDER BY avg_rating DESC"
            )
        )
        avg = avg_row.mappings().first()
        return {
            "avg_rating": float(avg["avg_rating"]) if avg else 0.0,
            "total": int(avg["total"]) if avg else 0,
            "distribution": list(dist_rows.mappings().all()),
            "categories": list(cat_rows.mappings().all()),
            "masters": list(master_rows.mappings().all()),
        }


async def get_visits_by_plate(plate: str) -> list:
    """Return all service visits for a given license plate ordered by date desc."""
    async with async_session() as session:
        rows = await session.execute(
            text(
                "SELECT o.order_number, o.problem, o.work_desc, o.agreed_price, "
                "o.status, o.created_at, o.closed_at, "
                "m.full_name AS master_name, "
                "c.brand, c.model, c.plate, c.color, c.year "
                "FROM orders o "
                "JOIN cars c ON c.id = o.car_id "
                "LEFT JOIN users m ON m.id = o.master_id "
                "WHERE UPPER(c.plate) = UPPER(:plate) "
                "ORDER BY o.created_at DESC"
            ),
            {"plate": plate},
        )
        return rows.mappings().all()


async def block_user(user_id: int) -> dict | None:
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                text("UPDATE users SET is_active=FALSE WHERE id=:id RETURNING *"),
                {"id": user_id},
            )
            row = result.mappings().first()
            return dict(row) if row else None


async def unblock_user(user_id: int) -> dict | None:
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                text("UPDATE users SET is_active=TRUE WHERE id=:id RETURNING *"),
                {"id": user_id},
            )
            row = result.mappings().first()
            return dict(row) if row else None


async def set_user_role(user_id: int, role: str) -> dict | None:
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                text("UPDATE users SET role=:role WHERE id=:id RETURNING *"),
                {"id": user_id, "role": role},
            )
            row = result.mappings().first()
            return dict(row) if row else None


async def save_broadcast(sender_id: int, target: str, message: str, sent_count: int):
    async with async_session() as session:
        async with session.begin():
            await session.execute(
                text(
                    "INSERT INTO broadcasts (sender_id, target, message, sent_count) "
                    "VALUES (:sid, :tgt, :msg, :cnt)"
                ),
                {"sid": sender_id, "tgt": target, "msg": message, "cnt": sent_count},
            )


async def get_broadcasts() -> list:
    async with async_session() as session:
        rows = await session.execute(
            text(
                "SELECT b.*, u.full_name AS sender_name FROM broadcasts b "
                "LEFT JOIN users u ON u.id = b.sender_id "
                "ORDER BY b.sent_at DESC LIMIT 100"
            )
        )
        return rows.mappings().all()


# ---------------------------------------------------------------------------
# Step 6 — Scheduler helpers
# ---------------------------------------------------------------------------


async def get_masters_with_unlinked_ready_orders() -> list:
    """Return masters who have ready orders older than 24 h with no linked client."""
    async with async_session() as session:
        rows = await session.execute(
            text(
                "SELECT o.order_number, m.telegram_id AS master_telegram_id "
                "FROM orders o "
                "JOIN users m ON m.id = o.master_id "
                "WHERE o.status = 'ready' "
                "AND o.client_id IS NULL "
                "AND o.ready_at < NOW() - INTERVAL '24 hours'"
            )
        )
        return rows.mappings().all()

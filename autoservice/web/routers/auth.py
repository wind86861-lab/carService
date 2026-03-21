from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from bot.database.models import create_user, get_user_by_telegram_id
from web.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
    verify_telegram_login,
)
from web.schemas import TelegramAuthSchema

router = APIRouter(tags=["auth"])


class LoginSchema(BaseModel):
    username: str
    password: str


@router.post("/auth/login")
async def login(data: LoginSchema):
    """Login with username/password for admin or master."""
    from sqlalchemy import text
    from bot.database.connection import async_session

    async with async_session() as session:
        result = await session.execute(
            text("SELECT * FROM users WHERE username = :u"),
            {"u": data.username},
        )
        user = result.mappings().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    if not verify_password(data.password, user.get("password_hash")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    if user["role"] not in ("admin", "master"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    token = create_access_token(user_id=user["id"], role=user["role"])
    return {"access_token": token, "token_type": "bearer", "role": user["role"]}


@router.get("/profile")
async def get_profile(user=Depends(get_current_user)):
    """Return the current user's profile info + summary stats."""
    from sqlalchemy import text
    from bot.database.connection import async_session

    uid = user["id"]
    async with async_session() as session:
        result = await session.execute(
            text(
                "SELECT COUNT(id) AS total_orders, "
                "COUNT(CASE WHEN status='closed' THEN 1 END) AS closed_orders, "
                "COALESCE(SUM(CASE WHEN status='closed' THEN agreed_price ELSE 0 END),0) AS total_revenue, "
                "COALESCE(SUM(CASE WHEN status='closed' THEN master_share ELSE 0 END),0) AS total_earnings "
                "FROM orders WHERE master_id = :mid"
            ),
            {"mid": uid},
        )
        stats = result.mappings().first()

    return {
        "id": user["id"],
        "full_name": user["full_name"],
        "phone": user.get("phone"),
        "username": user.get("username"),
        "role": user["role"],
        "telegram_id": user.get("telegram_id"),
        "total_orders": stats["total_orders"] if stats else 0,
        "closed_orders": stats["closed_orders"] if stats else 0,
        "total_revenue": int(stats["total_revenue"]) if stats else 0,
        "total_earnings": int(stats["total_earnings"]) if stats else 0,
    }


class ChangePasswordSchema(BaseModel):
    current_password: str
    new_password: str


@router.patch("/profile/password")
async def change_password(body: ChangePasswordSchema, user=Depends(get_current_user)):
    """Change the current user's password."""
    from sqlalchemy import text
    from bot.database.connection import async_session

    async with async_session() as session:
        result = await session.execute(
            text("SELECT password_hash FROM users WHERE id = :uid"),
            {"uid": user["id"]},
        )
        row = result.mappings().first()

    if not row or not verify_password(body.current_password, row.get("password_hash")):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    new_hash = hash_password(body.new_password)
    async with async_session() as session:
        await session.execute(
            text("UPDATE users SET password_hash = :h WHERE id = :uid"),
            {"h": new_hash, "uid": user["id"]},
        )
        await session.commit()

    return {"message": "Password changed successfully"}


@router.post("/auth/telegram")
async def telegram_auth(data: TelegramAuthSchema):
    """Verify Telegram Login Widget data and return a JWT access token."""
    payload = data.model_dump()
    if not verify_telegram_login(payload):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram signature")

    tg_id = data.id
    full_name = data.first_name
    if data.last_name:
        full_name += f" {data.last_name}"

    user = await get_user_by_telegram_id(tg_id)
    if not user:
        user = await create_user(telegram_id=tg_id, full_name=full_name, phone=None, role="client")

    token = create_access_token(user_id=user["id"], role=user["role"])
    return {"access_token": token, "token_type": "bearer", "role": user["role"]}

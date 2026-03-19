from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from bot.database.models import create_user, get_user_by_telegram_id
from web.auth import create_access_token, verify_telegram_login, verify_password
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

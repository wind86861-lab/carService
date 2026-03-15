from fastapi import APIRouter, HTTPException, status

from bot.database.models import create_user, get_user_by_telegram_id
from web.auth import create_access_token, verify_telegram_login
from web.schemas import TelegramAuthSchema

router = APIRouter(tags=["auth"])


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

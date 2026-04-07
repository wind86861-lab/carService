import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/autoservice")
SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-secret-key-in-production")
ACCESS_TOKEN_EXPIRE_HOURS: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "24"))
MAX_PHOTO_SIZE_MB: int = int(os.getenv("MAX_PHOTO_SIZE_MB", "10"))
UPLOAD_DIR: Path = Path(os.getenv("UPLOAD_DIR", "uploads"))
WEB_URL: str = os.getenv("WEB_URL", "http://localhost:8000")
BOT_USERNAME: str = os.getenv("BOT_USERNAME", "")
ADMIN_GROUP_CHAT_ID: str = os.getenv("ADMIN_GROUP_CHAT_ID", "")

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

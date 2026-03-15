import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/autoservice")
ADMIN_IDS: list[int] = [
    int(id_str.strip())
    for id_str in os.getenv("ADMIN_IDS", "").split(",")
    if id_str.strip().isdigit()
]
BOT_USERNAME: str = os.getenv("BOT_USERNAME", "")
WEB_URL: str = os.getenv("WEB_URL", "http://localhost:8000")

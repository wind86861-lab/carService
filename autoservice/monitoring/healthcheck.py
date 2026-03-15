#!/usr/bin/env python3
"""
Health-check script — run every 5 minutes via cron:
    */5 * * * * /usr/bin/python3 /srv/autoservice/monitoring/healthcheck.py
"""
import os
import sys

import httpx

WEB_URL = os.getenv("WEB_URL", "http://localhost:8000")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
MONITORING_CHAT_ID = os.getenv("MONITORING_CHAT_ID", "")
TG_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


def alert(msg: str) -> None:
    if not MONITORING_CHAT_ID or not BOT_TOKEN:
        print(f"[ALERT] {msg}", file=sys.stderr)
        return
    try:
        httpx.post(
            f"{TG_API}/sendMessage",
            json={"chat_id": MONITORING_CHAT_ID, "text": f"🚨 AutoService Alert\n\n{msg}"},
            timeout=10,
        )
    except Exception as e:
        print(f"Failed to send alert: {e}", file=sys.stderr)


def check_api() -> bool:
    try:
        resp = httpx.get(f"{WEB_URL}/api/health", timeout=10)
        if resp.status_code == 200:
            return True
        alert(f"API health check returned HTTP {resp.status_code}.")
        return False
    except Exception as e:
        alert(f"API health check failed: {e}")
        return False


def check_bot() -> bool:
    if not BOT_TOKEN:
        return True
    try:
        resp = httpx.get(f"{TG_API}/getMe", timeout=10)
        if resp.status_code == 200 and resp.json().get("ok"):
            return True
        alert(f"Bot getMe check failed: {resp.text}")
        return False
    except Exception as e:
        alert(f"Bot health check failed: {e}")
        return False


if __name__ == "__main__":
    api_ok = check_api()
    bot_ok = check_bot()
    if api_ok and bot_ok:
        print("All services healthy.")
        sys.exit(0)
    else:
        sys.exit(1)

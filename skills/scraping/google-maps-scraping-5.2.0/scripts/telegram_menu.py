#!/usr/bin/env python3
"""
Telegram /start and /menu handler — sends Reply Keyboard buttons.

Reads config from config.json in the skill root (via scripts/lib.py).
Bot token auto-detects from hermes .env if not set in config.
"""

import json
import os
import re
import urllib.request
from pathlib import Path

# ── Config via shared lib ────────────────────────────────────────────────────

from lib import get_hermes_home, load_config

config = load_config()
BOT_TOKEN = config.get("telegram", {}).get("bot_token", "")


def _read_bot_token():
    """Resolve bot token: config > hermes .env file."""
    if BOT_TOKEN:
        return BOT_TOKEN

    env_path = str(get_hermes_home() / ".env")
    if not os.path.exists(env_path):
        return None

    with open(env_path, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(r'^TELEGRAM_BOT_TOKEN=(.+)$', content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return None


def send_menu(chat_id, text="Welcome back! Here is your menu."):
    """Send the Reply Keyboard to a Telegram chat."""
    token = _read_bot_token()
    if not token:
        return {"ok": False, "error": "No bot token found"}

    payload = {
        "chat_id": chat_id,
        "text": text,
        "reply_markup": {
            "keyboard": [
                [{"text": "🗺️ Scrape Maps"}, {"text": "📊 View Last CSV"}],
                [{"text": "🗂️ List All Scrapes"}, {"text": "❓ Help"}],
            ],
            "resize_keyboard": True,
            "is_persistent": True,
        },
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
        return {"ok": resp.get("ok", False)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


if __name__ == "__main__":
    import sys

    chat_id = sys.argv[1] if len(sys.argv) > 1 else None
    if not chat_id:
        print("Usage: python telegram_menu.py <chat_id>")
        sys.exit(1)
    result = send_menu(chat_id)
    print(json.dumps(result))
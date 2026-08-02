# Telegram Reply Keyboard Setup

Reply Keyboard buttons are a native Telegram UI feature — persistent buttons at the bottom of the chat. When tapped, they send their text as a regular message.

## How It Works

1. Send a `sendMessage` call with `reply_markup.keyboard` in the payload
2. The buttons appear at the bottom of the chat permanently
3. When user taps a button, its `text` is sent as a regular chat message
4. The agent receives the button text and acts on it (matched via memory/skill rules)

## Sending the Keyboard to a User

```python
import re, urllib.request, json
from pathlib import Path

# Read bot token from hermes .env
hermes_home = Path.home() / "AppData" / "Local" / "hermes"
env_path = hermes_home / ".env"

with open(env_path, "r") as f:
    content = f.read()
match = re.search(r'^TELEGRAM_BOT_TOKEN=(.+)$', content, re.MULTILINE)
token = match.group(1).strip()

base = f"https://api.telegram.org/bot{token}"

payload = {
    "chat_id": "<USER_CHAT_ID>",
    "text": "Welcome! Choose an option below:",
    "reply_markup": {
        "keyboard": [
            [{"text": "🗺️ Scrape Maps"}, {"text": "📊 View Last CSV"}],
            [{"text": "🗂️ List All Scrapes"}, {"text": "❓ Help"}]
        ],
        "resize_keyboard": True,    # Fits buttons to screen size
        "is_persistent": True       # Stays visible after first use
    }
}
data = json.dumps(payload).encode()
req = urllib.request.Request(f"{base}/sendMessage", data=data, headers={"Content-Type": "application/json"})
resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
```

## Key Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `keyboard` | array of arrays | Each inner array = one row of buttons. Each button has a `text` field. |
| `resize_keyboard` | bool | `true` = auto-size buttons to fit screen. Always set this. |
| `is_persistent` | bool | `true` = keep buttons visible after user sends a message. |
| `one_time_keyboard` | bool | `true` = hide keyboard after first use (not recommended for persistent menus). |

## Updating the Keyboard

Send a new `sendMessage` with `reply_markup` to replace the keyboard. The old buttons are replaced entirely.

## Best Practices

- **Always use `execute_code`** to send the Telegram API call (avoids secret redaction of the bot token in terminal output)
- **Button text must match exactly** what the agent's memory/skill rules check for (case-sensitive, emoji included)
- **Use emoji prefixes** for readability: 🗺️ 📊 🗂️ ❓
- **Update all allowed users** by iterating `TELEGRAM_ALLOWED_USERS` from `.env`
- **Users who never started the bot** will get a 400 error — skip them gracefully
- **Keyboard buttons are per-chat** — each user needs their own `sendMessage`
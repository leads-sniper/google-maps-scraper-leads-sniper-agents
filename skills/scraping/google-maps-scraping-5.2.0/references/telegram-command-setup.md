# Telegram Command Setup

Register `/scrap` as a Telegram bot command so it shows in the command menu and isn't rejected as "unknown command".

## How to Register

Use the Telegram Bot API `setMyCommands` endpoint. You need the bot token.

### From execute_code (recommended — avoids secret redaction)

```python
import re, urllib.request, json
from pathlib import Path

# Auto-detect bot token from hermes .env
hermes_home = Path.home() / "AppData" / "Local" / "hermes"
env_path = hermes_home / ".env"

with open(env_path, "r") as f:
    content = f.read()

match = re.search(r'^TELEGRAM_BOT_TOKEN=(.+)$', content, re.MULTILINE)
if match:
    token = match.group(1).strip()
    url = f"https://api.telegram.org/bot{token}/setMyCommands"
    data = json.dumps({
        "commands": [
            {"command": "scrap", "description": "Scrape Google Maps data (restaurants, dentists, spas, etc.)"},
            {"command": "new", "description": "Start a fresh session"},
            {"command": "help", "description": "Show commands"},
            {"command": "commands", "description": "List all commands"}
        ]
    }).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
    print(f"Success: {resp.get('ok')}")
```

### From terminal (requires copying the token)

```bash
TOKEN="<your_bot_token>"
curl -s -X POST "https://api.telegram.org/bot${TOKEN}/setMyCommands" \
  -H "Content-Type: application/json" \
  -d '{
    "commands": [
      {"command": "scrap", "description": "Scrape Google Maps data"},
      {"command": "new", "description": "Start a fresh session"},
      {"command": "help", "description": "Show commands"},
      {"command": "commands", "description": "List all commands"}
    ]
  }'
```

## Verify Registration

```bash
TOKEN="<your_bot_token>"
curl -s "https://api.telegram.org/bot${TOKEN}/getMyCommands" | python -m json.tool
```

## Why /scrap instead of /start?

Telegram reserves `/start` as a platform-level command — it's intercepted before the agent sees it and silently dropped in Hermes. Custom commands like `/scrap` are unrestricted and fully reach the agent.
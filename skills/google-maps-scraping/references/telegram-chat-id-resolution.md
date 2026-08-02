# Telegram Chat ID Resolution

When the agent needs to send a Telegram Reply Keyboard or message via the Telegram Bot API directly (`telegram_menu.py`, custom messages), it needs the user's numeric chat_id.

## Primary Source: TELEGRAM_ALLOWED_USERS

The cleanest source is the Hermes `.env` file:

```bash
grep TELEGRAM_ALLOWED_USERS ~/AppData/Local/hermes/.env
```

This returns a comma-separated list of numeric user IDs. The first one is typically the bot owner.

## Fallback: TELEGRAM_HOME_CHANNEL

If the user is in a channel/group context:

```bash
grep TELEGRAM_HOME_CHANNEL ~/AppData/Local/hermes/.env
```

## Fallback: getUpdates API

If the above don't match the active user, use the Telegram Bot API to list recent chat interactions:

```bash
TOKEN=$(grep TELEGRAM_BOT_TOKEN ~/AppData/Local/hermes/.env | cut -d= -f2)
curl -s "https://api.telegram.org/bot${TOKEN}/getUpdates" | python -c "
import sys, json
data = json.load(sys.stdin)
for update in data.get('result', []):
    msg = update.get('message') or update.get('callback_query', {}).get('message')
    if msg:
        chat = msg['chat']
        print(f\"chat_id={chat['id']} type={chat.get('type','?')} title={chat.get('title','?')} username={chat.get('username','?')}\")
"
```

This shows the last 100 updates. The most recent message's chat_id is the active conversation.

## Via telegram_menu.py

The `telegram_menu.py` script takes the chat_id as its first argument:

```bash
python scripts/telegram_menu.py <CHAT_ID>
```

It reads the bot token from config.json or auto-detects from the Hermes `.env` file.

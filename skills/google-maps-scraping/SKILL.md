---
name: google-maps-scraping
description: "Scrape Google Maps B2B leads via bundled Leads Sniper server. Zero-touch setup — auto-starts server, interactive Google Workspace auth, portable across machines."
version: 5.3.0
author: Hermes Agent
metadata:
  hermes:
    tags: [Google Maps, Scraping, Leads, CSV, Sheets, API, B2B, Server, Portable, Windows, Zero-Touch]
    related_skills: [google-workspace]
---

# Google Maps Scraping (Leads Sniper)

> 🚫 **NO terminal commands, curl, or shell output on the chat. EVER.** All scraping runs inside `delegate_task` subagents. The user sees only clean progress messages and results. No raw API calls, no "sleep 45", no background task details in the conversation.

## 📦 Portability — This Skill is Self-Contained

This skill folder can be **copied to any Hermes installation** (Windows, Linux, macOS, VPS). Everything is configured via:

| What | How | File |
|------|-----|------|
| API endpoint + token | `setup.py` or env vars | `config.json` |
| Storage directory | `setup.py` or `GMAPS_STORAGE_DIR` env var | `config.json` |
| Google Sheets auth | Google Workspace skill (separate) | `google_token.json` in HERMES_HOME |

No hardcoded paths, no machine-specific references. Run `setup.py` on each new machine and you're ready.

---

## ⚡ Quick Start — First Time Setup

On a **new Hermes installation**, run this once after copying the skill folder:

```bash
# From the skill directory:
python scripts/setup.py
```

The setup script will:
1. Detect any existing config (migration mode)
2. Prompt for:
   - **API Base URL** (default: `http://127.0.0.1:8787`)
   - **API Token** (or skip to use the `LEADS_SNIPER_TOKEN` env var)
3. **Auto-detect bundled server** — finds `server/local-api.exe`, offers to start it
4. **Test API connection** — now that the server is running, this actually works
5. Prompt for:
   - **Storage directory** (default: `~/Hermes_Scrapes`)
   - **Telegram bot token** (optional — auto-detects from Hermes `.env`)
6. **Check Google Workspace auth**:
   - If **already authenticated** — asks "Re-run setup anyway? (overwrites existing token)" (default: n)
   - If **not set up** — asks "Would you like to set up Google Workspace now?" (default: n)
     - Say **y** → interactive wizard: prompts for client_secret path, runs `--auth-url`, asks you to paste the redirect URL, exchanges code, verifies
     - Say **n** → skips cleanly with a note that CSVs save locally
7. Write `config.json`

### Non-interactive mode (CI / VPS setup)

```bash
LEADS_SNIPER_TOKEN="<token>" python scripts/setup.py --noninteractive
```

### Migrate from an old config

```bash
python scripts/setup.py --migrate-from /path/to/old_config.json
```

### Manual config edit

After setup, you can edit `config.json` directly — the scripts read it on every run.

---

## 🔐 Google Workspace Setup (Required for Sheets Uploads)

This skill uploads scrape results to Google Sheets. You need Google Workspace OAuth
set up **once** per machine. The setup is a 5-step process that takes ~10 minutes.

### Step 1: Create OAuth credentials in Google Cloud Console

1. Go to **[Google Cloud Console → APIs & Services → Credentials](https://console.cloud.google.com/apis/credentials)**
2. Click **Create Credentials → OAuth 2.0 Client ID**
3. Application type: **Desktop app** → give it a name → **Create**
4. **Download the JSON file** — it contains your `client_id` and `client_secret`

> ⚠️ If the app is in "Testing" mode, you must add your Google account as a test user:
> Go to **[OAuth Consent Screen](https://console.cloud.google.com/auth/audience)** → **Audience** → **Test users** → **Add users**

### Step 2: Enable the required APIs

In the same Google Cloud project, enable these two APIs:

- **[Google Sheets API](https://console.developers.google.com/apis/api/sheets.googleapis.com/overview)** → click **Enable**
- **[Google Drive API](https://console.developers.google.com/apis/api/drive.googleapis.com/overview)** → click **Enable**

> Without these APIs enabled, the OAuth token will be valid but API calls will fail with 403.

### Step 3: Register the client secret

```bash
GSETUP="python $HERMES_HOME/skills/productivity/google-workspace/scripts/setup.py"
$GSETUP --client-secret /path/to/client_secret.json
```

### Step 4: Get the authorization URL

```bash
$GSETUP --auth-url
```

This prints a URL. **Open it in a browser**, sign in with your Google account,
and authorize Hermes. The browser will redirect to a broken-looking
`http://localhost:1/?code=...` page — **that's expected.** Copy the entire URL.

### Step 5: Exchange the code

```bash
$GSETUP --auth-code "http://localhost:1/?code=4/0A...&scope=..."
```

### Step 6: Verify

```bash
$GSETUP --check
# Should print: AUTHENTICATED
```

### Quick start (if you already have the client secret file)

> ⚠️ Before running these commands, make sure **Google Sheets API** and **Google Drive API**
> are enabled in your Google Cloud project:
> - [Enable Sheets API](https://console.developers.google.com/apis/api/sheets.googleapis.com/overview)
> - [Enable Drive API](https://console.developers.google.com/apis/api/drive.googleapis.com/overview)

```bash
GSETUP="python $HERMES_HOME/skills/productivity/google-workspace/scripts/setup.py"
$GSETUP --client-secret /path/to/client_secret.json
$GSETUP --auth-url
# Open the URL, authorize, paste the redirect URL:
$GSETUP --auth-code "http://localhost:1/?code=4/0A..."
$GSETUP --check
```

> 💡 **Token lifetime:** The OAuth token auto-refreshes. You should only need to
> do this once unless you revoke access or the token expires.
>
> **Need email only?** Skip all this — use the `himalaya` skill instead (Gmail
> App Password, 2-minute setup). Sheets uploads still need the full OAuth flow.

---

## 📁 Skill Folder (portable)

```
google-maps-scraping/
├── SKILL.md                          ← This file
├── config.json                       ← Per-installation config (created by setup.py)
├── server/
│   └── local-api.exe                 ← Bundled Leads Sniper server (auto-started)
├── scripts/
│   ├── lib.py                        ← Shared config loader (all scripts use this)
│   ├── setup.py                      ← First-time setup wizard
│   ├── server.py                     ← Server lifecycle: start/stop/status/ensure
│   ├── upload_csv_to_sheets.py       ← CSV → Google Sheets uploader
│   ├── run_scrape.py                 ← Background scraper (auto-starts server)
│   └── telegram_menu.py              ← Telegram Reply Keyboard sender
└── references/
    ├── api-spec.json                 ← API spec (Leads Sniper OpenAPI)
    ├── browser-fallback-workflow.md  ← Manual scraping via browser
    ├── setup-cheatsheet.md           ← Quick reference for agent-guided setup
    ├── telegram-chat-id-resolution.md← Resolve Telegram user/group chat_id
    ├── telegram-command-setup.md     ← Register /scrap bot command
    ├── telegram-reply-keyboard.md    ← Setup Reply Keyboard buttons
    └── token-recovery.md             ← Find/rotate the API token
```

> ✅ **No manual server management.** The bundled `local-api.exe` in `server/` is auto-started by `run_scrape.py` and by the scrape workflow. Just run `setup.py` once and the server handles itself.

---

## 🖥️ Server Management (Zero-Touch)

The `local-api.exe` is bundled inside `server/` and is **fully automatic**:

| Action | Command |
|--------|---------|
| **Auto-start (before scrape)** | `python scripts/server.py ensure` |
| **Start manually** | `python scripts/server.py start` |
| **Check status** | `python scripts/server.py status` |
| **Stop** | `python scripts/server.py stop` |
| **View log** | `python scripts/server.py log 20` |

The server starts on its own when you scrape. You don't need to think about it.

---

## 🚀 Onboarding

### On Telegram — Reply Keyboard Buttons

When user sends any of these button texts, respond accordingly:

| Button text | Response |
|-------------|----------|
| `🗺️ Scrape Maps` | "What niche and city would you like me to scrape? (e.g., Plumbers in Dallas)" — then trigger scraping |
| `📊 View Last CSV` | Read the most recent sheet's data and show a preview table (first 10 rows with Name, Phone, Rating, Reviews, Email), plus the link. Do NOT just share the link — the user wants to SEE the data. |
| `🗂️ List All Scrapes` | Read `history.json` from the configured storage dir, show 10 per page newest-first. Format: numbered list with niche, location, count, date, and sheet link. Append pagination hint at bottom. |
| `❓ Help` | Show available commands and how to use the bot |

The keyboard was set up via Telegram API `sendMessage` with `reply_markup.keyboard`.

### On Telegram `/start` or `/menu` or "interactive menu"
When user sends `/start`, `/menu`, or says any variant of "interactive menu", "show me the buttons", "show me the menu buttons", SILENTLY send the Reply Keyboard back via Telegram API. No shell commands shown to user. Say "Welcome back! Here is your menu." then send keyboard:
```
🗺️ Scrape Maps   |   📊 View Last CSV
🗂️ List All Scrapes   |   ❓ Help
```

### On Telegram `/scrap` or first message
When user sends `/scrap` (or first greeting like "hi", "hello"), respond with welcome message + Reply Keyboard, then load skill.

> 💡 **First-time on a new Telegram bot?** `/scrap` must be registered as a bot command — see `references/telegram-command-setup.md`.

### When the user says "load google maps scraping" or asks to scrape

**🚫 NEVER use the terminal tool for any check or command on the chat.** Terminal output always leaks into the conversation. Instead, use `execute_code` (Python) for all preliminary checks — it runs silently and only shows what you print.

1. **Check if the server is running** — use `execute_code` to import from `scripts.lib` and check silently:
   ```python
   # This is an example of what to execute, NOT a terminal command
   from pathlib import Path
   import sys
   SKILL = Path.home() / "AppData/Local/hermes/skills/scraping/google-maps-scraping"
   sys.path.insert(0, str(SKILL / "scripts"))
   from lib import load_config
   cfg = load_config()
   import urllib.request
   try:
       req = urllib.request.Request(f"{cfg['api']['base_url']}/v1/status",
           headers={"Authorization": f"Bearer {cfg['api']['token']}"})
       resp = urllib.request.urlopen(req, timeout=5)
       print("SERVER_OK")
   except Exception:
       print("SERVER_DOWN")
   ```
   Then show the user a single line: `✅ Server running` or `⚠️ Server not running`

2. **Check Google Workspace auth** — use `execute_code` to import `check_google_auth` from `scripts.lib`:
   ```python
   from scripts.lib import check_google_auth
   authed, path = check_google_auth()
   print("AUTHED" if authed else "NO_AUTH")
   ```
   Show the user: `✅ Google Sheets ready` or `⚠️ Google Sheets not set up`

3. **Only ask for a new API key** if the server test fails with 401 Unauthorized.

4. **Tell the user the status in a single clean message** — then ask what they want to scrape:
   ```
   Everything's good to go:
   - ✅ Server running
   - ✅ Google Sheets ready
   
   What would you like me to scrape? Just tell me the niche and location.
   ```

---

## 🛑 `/stop` Command Handler

When the user sends `/stop` or taps the stop button, **immediately stop everything and do NOT do any follow-up checks or actions:**

1. **Stop the current scrape job** via API: `POST /v1/jobs/{job_id}/stop`
2. **Save partial results** — if the job had found leads, upload what we have. If zero leads, skip.
3. **Stop the server** — call this ONCE and do NOT start it again:
   ```
   python scripts/server.py stop
   ```
4. **STOP** — do NOT check server status, do NOT verify Google auth, do NOT read config, do NOT run any other commands. Just reply with a single clean message and be done.
5. **If partial results were saved:**
   ```
   🛑 Stopped. [N] results saved before stopping.
   📊 [link]
   ```
   **If nothing was found:**
   ```
   🛑 Stopped. No results yet — try a different search?
   ```

---

## 🔌 API Details

| Field | Value |
|-------|-------|
| Base URL | Configured via `config.json` (default: `http://127.0.0.1:8787`) |
| Auth header | `Authorization: Bearer <token>` |
| Token source | `LEADS_SNIPER_TOKEN` env var > `config.json` `api.token` field |
| API docs | `{base_url}/docs` |
| Swagger spec | `{base_url}/swagger.json` |

> **No hardcoded tokens.** The old fallback token `752281cb05e6aab65a87cf2e26ca4c1b` has been removed. Run `setup.py` or set `LEADS_SNIPER_TOKEN` to configure.

---

## 📡 Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/v1/status` | Health check & extension status |
| POST | `/v1/google-maps/search` | Submit scrape job |
| GET | `/v1/jobs/{job_id}` | Poll job status |
| GET | `/v1/jobs/{job_id}/results` | Results as JSON |
| GET | `/v1/jobs/{job_id}/export.csv` | Download CSV |
| POST | `/v1/jobs/{job_id}/stop` | Stop a job |
| POST | `/v1/auth/rotate-key` | Rotate API key |
| GET | `/v1/logs` | Download logs |

---

## 📤 POST `/v1/google-maps/search`

```json
{
  "keyword": "dentists, lawyers",
  "location": "Miami",
  "limit": 100,
  "extract_emails": true
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `keyword` | string | ✅ | — | Search term(s), comma-separated |
| `location` | string | ❌ | — | Target area |
| `limit` | int | ❌ | 100 | Max results |
| `extract_emails` | bool | ❌ | false | Extract emails & social profiles |
| `webhook_url` | string | ❌ | — | Webhook on completion |

**Response:** `{"job_id": "job_...", "status": "queued"}`

---

## 📊 Job Status — `GET /v1/jobs/{job_id}`

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `queued` → `running` → `completed` / `stopped` / `failed` |
| `progress` | int | Progress % |
| `total_found` | int | Leads found |
| `error` | string | Diagnostic if scroll stuck |
| `message` | string | E.g. "Waiting for extension..." |

**Status handling:**
- ✅ `completed` → Download full results
- ⚠️ `stopped` + `total_found > 0` → Download partial results
- ❌ `stopped` + `total_found == 0` → Tell user "No listings found for this query"
- ❌ `failed` → Abort, report error
- ⚠️ `queued` + `message` contains "Waiting for Chrome Extension to connect" → The job is stuck, not actually progressing (0% forever). This means the Leads Sniper Chrome extension is not open/active in a browser on the machine running the server. Tell the user: "The job is queued but waiting on the Chrome extension — please open Google Chrome and make sure the Leads Sniper extension is active/enabled, then it should start automatically." Do NOT treat this as a failure or abort — it resumes once the extension connects. Just report the message and move on; re-check on the next status request.

**Checking status of an in-progress scrape (user asks "what's the status" / "check now" / repeats the question):**
Read the last line of `gmaps_progress.log` in the configured storage dir (`get_storage_dir()`) — the running delegate_task subagent writes progress there, so it reflects live state without another API call or without needing to poll the subagent (which is otherwise invisible until it finishes — see opacity pitfall below). Only fall back to a direct `GET /v1/jobs/{job_id}` call if the log is missing/stale, and note that a direct call from a *different* execute_code context can 401 if it's not using the same resolved token as the subagent — that 401 does not mean the job died, just that this ad-hoc check used a bad/missing token.

---

## 🔁 Scrape Workflow

**🚫 ABSOLUTELY NO terminal commands, curl, or raw API calls on the chat. EVER.**

All scraping must happen **inside a `delegate_task` subagent** — the subagent can use terminal/curl internally, but the main chat sees **only** clean progress messages and the final result. No shell commands, no "sleep 45", no "curl -s ...", no background task mentions.

### ⚡ Speed-Optimized Pattern (Pre-Check Then Delegate)

The subagent has **no conversation context** — it re-loads skills, re-reads config, re-checks auth from scratch. That adds ~50s of overhead before the job is even submitted.

**Permanent fix:** main agent pre-checks everything first, then passes confirmed state to the subagent so it skips setup entirely.

**Step 1 — Main agent pre-checks** (in `execute_code`, not terminal):

```python
import sys, json, urllib.request
from pathlib import Path

SKILL = Path.home() / "AppData/Local/hermes/skills/google-maps-scraping"
sys.path.insert(0, str(SKILL / "scripts"))
from lib import load_config, check_google_auth

cfg = load_config()
token = cfg['api']['token']
base_url = cfg['api']['base_url']
authed, _ = check_google_auth()

# Check server
try:
    req = urllib.request.Request(f"{base_url}/v1/status",
        headers={"Authorization": f"Bearer {token}"})
    urllib.request.urlopen(req, timeout=5)
    server_ok = True
except Exception:
    server_ok = False
    # start server
    import subprocess
    subprocess.run(["python", str(SKILL/"scripts/server.py"), "ensure"],
        cwd=str(SKILL), capture_output=True, timeout=30)

print(f"TOKEN={token}")
print(f"BASE_URL={base_url}")
print(f"AUTHED={authed}")
print(f"SERVER={server_ok}")
```

**Step 2 — Delegate with confirmed state passed as context** (instant, no re-checks):

Delegate a subagent with this structured goal:

> **Goal:** Scrape `[keyword]` in `[location]` using the Leads Sniper local API.
>
> 1. **Submit a search job** via `POST /v1/google-maps/search` with keyword="...", location="...", limit=100, extract_emails=true
> 2. **Poll every 45s** (`GET /v1/jobs/{job_id}`) — log progress to a file, don't print to stdout
> 3. **Download CSV** from `GET /v1/jobs/{job_id}/export.csv`
> 4. **Upload to Google Sheets** using the skill's upload script:
>    ```
>    python "<skill_dir>/scripts/upload_csv_to_sheets.py" "<JOB_ID>" "Title"
>    ```
> 5. **Verify** `history.json` was updated with the correct count and sheet URL
> 6. Return: sheet URL and total count

**Context (MUST include pre-checked values):**

Pass the output of the pre-check above. The subagent must use these values directly — **do NOT re-read config, do NOT re-check auth, do NOT re-check server.** Go straight to submitting the job.

```
token=TOKEN_VALUE
base_url=BASE_URL_VALUE
authed=AUTHED_VALUE
server_running=SERVER_VALUE
skill_dir=<skill_dir>
```

Also append: "The sheet must be publicly editable (anyone with link can write)." and "Use ASCII-safe output only in scripts (no emoji in print). Use +/!/x markers."

If pre-check showed server was down, start it from the main agent before delegating (so the context always says server_running=true).

---

## 🔑 Token Recovery (401 Unauthorized)

If the API returns 401, the token has been rotated. See `references/token-recovery.md` for the full discovery process.

**Quick checklist:**
1. Check `LEADS_SNIPER_TOKEN` env var
2. Check `config.json` `api.token` field
3. Search Chrome extension LevelDB for 32-char hex strings
4. Rotate via `POST /v1/auth/rotate-key`

After finding the new token, update config:
```bash
# Update config.json directly or re-run setup
python scripts/setup.py
```

---

## 🧠 Core Instructions for This Skill

1. **🚫 NEVER use the terminal tool on the chat.** The terminal tool's output always shows on Telegram (`💻 terminal`). Use `execute_code` (Python) for ALL checks — reads, config loading, API pings. `execute_code` runs silently and only shows what you explicitly print.
2. **Always use the pre-check then delegate pattern** — first check server/auth/config in `execute_code`, then pass those values as `context` to the subagent. The subagent skips re-checking everything and goes straight to submitting the job (see Scrape Workflow section).
3. **Progress format** (only this, no raw output):
   ```
   ⏳ 45% — 45 found — still running
   ⏳ 80% — 80 found — almost there
   ✅ Completed! N restaurants found
   ```
4. **Final result format (table + link):**
   ```
   ✅ Done! [N] [business type] found
   📊 [Google Sheet link]
   ```
4. **After every scrape, immediately ask for a new task:**
   > "Want me to scrape something else? Just give me a keyword and location!"
5. **On Telegram `/scrap`** → Greet and ask what they want to scrape (no onboarding questions).
6. **On scrape request** → First test if current API key works. Only ask for a new one if it fails with 401.

---

## 📊 Post-Scrape: Extracting Data From the Sheet

After a scrape is uploaded to Sheets, the user may ask you to list specific fields (emails, phones, websites). To read data back:

```bash
python "$HERMES_HOME/skills/productivity/google-workspace/scripts/google_api.py" sheets get "<SHEET_ID>" "Sheet1"
```

The email field is column 17 (`Email_From_WEBSITE`), names are column 1. Multiple emails in one cell are separated by `;` or `,`. Pipe the output to a temp file and parse with Python for clean extraction.

---

## 🗂️ Listing All Scrapes (Button Handler)

When the user taps "🗂️ List All Scrapes" or sends `/pageN`:

1. Read `history.json` from the **configured storage directory** (set via `setup.py` / `GMAPS_STORAGE_DIR` env var)
2. Parse as JSON, reverse for newest-first: `records = list(reversed(history))`
3. Calculate pages: `PAGE_SIZE = 10`, `total_pages = (len(records) + PAGE_SIZE - 1) // PAGE_SIZE`
4. Slice: `page_records = records[(page-1)*10 : page*10]`
5. Display format (Telegram Markdown):
   ```
   *🗂️ Scrape History — Page 1/N*
   4. *Spas* in Dallas — 113 leads
      🗓️ 2026-07-14 14:31  📊 [Sheet](url)
   3. *Spas* in New York — 60 leads
      🗓️ 2026-07-14 14:23  📊 [Sheet](url)
   ...
   Page 1. Type /page2 to see older records.
   ```
6. For `/page2`, `/page3` etc: extract the number, offset, and show that page
7. If history.json is empty, show "No scrapes recorded yet."

---

## 🧠 📊 View Last CSV Handler

When the user taps "📊 View Last CSV":

1. Read the last record from `history.json` in the configured storage directory
2. If no records exist, say "No scrapes yet!"
3. Otherwise, read the sheet data via the google-workspace script:
   ```bash
   python "$HERMES_HOME/skills/productivity/google-workspace/scripts/google_api.py" sheets get "<SHEET_ID>" "Sheet1"
   ```
4. Show a preview of the first 10-15 rows: Name, Phone, Rating, Reviews, and Email columns
5. Include the sheet link at the bottom so they can see the full data
6. Do NOT just share the link — the user pressed the button because they want to SEE the data

---

## 🗄️ Local Database System

Every scrape result is stored locally for instant access.

### Storage Structure

```
<storage_dir>/          ← configured in config.json (default: ~/Hermes_Scrapes)
├── history.json        ← Master tracking file (auto-created by upload script)
├── gmaps_<job_id>.csv  ← Raw CSV files from each scrape
└── gmaps_progress.log  ← Progress file (run_scrape.py)
```

### history.json Format

```json
[
  {
    "id": 1,
    "date": "2026-07-14 21:00:00",
    "query": "Spas in New York",
    "niche": "Spas",
    "location": "New York",
    "count": 100,
    "csv_path": "<storage_dir>/gmaps_job_xxx.csv",
    "sheet_url": "https://docs.google.com/spreadsheets/d/..."
  }
]
```

### Rules

1. **Every scrape** saves CSV to `<storage_dir>/gmaps_<job_id>.csv`
2. **Every scrape** appends a record to `<storage_dir>/history.json`
3. **"🗂️ List All Scrapes"** → read history.json, show 10 per page (newest first by `id` descending), paginate with `/page2`, `/page3` etc.
4. **"📊 View Last CSV"** → read the last record's sheet data via Sheets API and show a data preview (Name, Phone, Rating, Reviews, Email) for the first 10-15 rows. Include the sheet link. Do NOT just share the link.
5. **Filter/sort/clean** → read local CSV with Python instantly — no Google Sheets download needed

### Pagination Implementation

```python
import json
PAGE_SIZE = 10

# storage_dir comes from config.json / lib.get_storage_dir()
from lib import get_storage_dir
storage_dir = get_storage_dir()
history_path = storage_dir / "history.json"

with open(history_path) as f:
    history = json.load(f)

# Determine page number
page = 1  # or extract from /pageN

records = list(reversed(history))
total_pages = (len(records) + PAGE_SIZE - 1) // PAGE_SIZE
start = (page - 1) * PAGE_SIZE
page_records = records[start:start + PAGE_SIZE]

# Build response
lines = [f"*🗂️ Scrape History — Page {page}/{total_pages}*"]
for r in page_records:
    lines.append(f"  {r['id']}. *{r['niche']}* in {r['location']} — {r['count']} leads")
    lines.append(f"     🗓️ {r['date']}  📊 [Sheet]({r['sheet_url']})")
# ...
```

---

## ⚠️ Pitfalls

- Auth header must include `Bearer ` prefix
- Parameter name is `keyword` not `query`
- `stopped` with results = partial data, still usable
- Poll no faster than every 30s
- Windows CLI arg limit: use the upload script, not `--values` for large datasets
- Column letters beyond Z (e.g., AQ for 43 cols): handled by upload script
- If queue is stuck, use browser fallback instead
- **Subagent isolation**: delegate_task subagents run in isolated environments with separate filesystem access. After the upload script runs, the subagent MUST explicitly verify `history.json` was updated by reading the file and checking the last record. If empty, manually append the record using Python.
- **delegate_task opacity**: Subagents are invisible until they finish — the user sees no progress updates. If the user asks "what's the status?" or "is it running?", switch to direct execution (Mode A) instead. The user wants live feedback, not a black box.
- **🔁 Button handler priority**: The SKILL.md's button table takes priority over memory. When the user taps "📊 View Last CSV", show data (not just a link). When they tap "🗂️ List All Scrapes", read history.json and paginate.
- **Token resolution**: `LEADS_SNIPER_TOKEN` env var > `config.json` `api.token` field. If neither is set, the API calls will fail with 401.
- **Token can auto-rotate mid-job, not just between sessions**: the Chrome extension periodically re-syncs its API key with the server, visible in `server.py log` as `API Key automatically synchronized with Chrome Extension: <32-hex>`. This can fire more than once during a single scrape — the active key can flip to a new value and then flip *back* to the original a few minutes later — so a token that worked for the initial `POST /v1/google-maps/search` can 401 on a later poll or on `export.csv` with no config changes on your side. **A 401 mid-workflow is not fatal and does not mean the job died.** Recovery: run `python scripts/server.py log 20`, find the most recent `API Key automatically synchronized with Chrome Extension: <token>` line, test that candidate against `/v1/status`; if it also 401s, retry the token you started with (it likely flipped back). Write the working token into `config.json`'s `api.token` field and immediately retry the failed call. Full walkthrough in `references/token-recovery.md`.
- **First-time setup**: Always run `python scripts/setup.py` after copying the skill to a new machine.
- **Google Workspace `setup.py` flags**: The google-workspace `setup.py` does NOT accept `--services` or `--format` flags. Only use: `--check`, `--client-secret PATH`, `--auth-url`, `--auth-code CODE`, `--revoke`, `--install-deps`.
- **Chat ID resolution for `telegram_menu.py`**: The script requires a chat_id argument. The current user's chat_id is the numeric value from `TELEGRAM_ALLOWED_USERS` in the Hermes `.env` file. If multiple users are allowed, the first one is typically the bot owner. Use `grep TELEGRAM_ALLOWED_USERS ~/AppData/Local/hermes/.env` to find it. For a multi-user setup, see `references/telegram-chat-id-resolution.md`.
- **`/v1/status` requires auth**: The health endpoint returns 401 if called without `Authorization: Bearer <token>`. The bundled `server.py` handles this correctly — it sends the token and treats 401 as "server is up". When testing manually, include the header.
- **Server start before API test**: In `setup.py`, the server section comes before the API connection test. This order matters — the server must be running before the test will pass.
- **Windows process management**: `os.kill(pid, 0)` does NOT work on Windows for checking if a process is alive. The `server.py` uses `tasklist /FI "PID eq {pid}"` for Windows and `os.kill(pid, 0)` for Linux/Mac. Similarly, `os.kill(pid, signal.SIGTERM)` doesn't work on Windows — `server.py` uses `taskkill /F /PID {pid}` instead. Never use raw `os.kill` for process management in cross-platform scripts.
- **Server process**: Find the Leads Sniper API server with `netstat -ano | grep 8787` then `wmic process where "processid=<PID>" get commandline` (Windows) or `ps aux | grep local-api` (Linux/Mac).
- **`server.py` token resolution**: `server.py`'s `_get_token()` reads from `config.json` first, then falls back to `LEADS_SNIPER_TOKEN` env var. If neither has a valid token, the health check will get 401 (which it treats as "server is up"). For actual scraping, the token must be correct.
- **`setup.py` server start fallback**: `setup.py` first tries `server.py ensure` (which checks if already running). If `ensure` returns non-zero, it falls back to `server.py start` (direct launch + health check). This ensures the server starts even if the PID file is stale or the status check fails.
- **Config not written until end**: `setup.py` collects all inputs (token, server path, etc.) during the wizard but only writes `config.json` at the very end (after Google Workspace section). Scripts called during setup (like `server.py ensure`) read the OLD config, not the values the user just entered. This is by design — the old config is sufficient for health checks, and the new config is written after the server is confirmed running.
- **Unicode emoji crash on Windows cp1252 terminals**: Emoji characters like `✓` (U+2713), `⚠` (U+26A0), `✗` (U+2717), `✅` (U+2705) crash with `UnicodeEncodeError: 'charmap' codec can't encode character` when Python's stdout is piped (e.g., via `subprocess.run(capture_output=True)`) on Windows terminals using cp1252 encoding. All scripts in this skill use ASCII-safe alternatives: `+` for success, `!` for warning, `x` for failure, `i` for info. **Never use non-ASCII emoji in `print()` calls in scripts that may run as subprocess children.** Only the SKILL.md (documentation) and agent-facing output can use emoji — the agent's output goes through Hermes, not cp1252.
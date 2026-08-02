# Setup Cheat Sheet — Quick Reference

For the agent to walk a user through setup without loading the full SKILL.md.

## Prerequisites

- Leads Sniper Chrome extension installed + `local-api.exe` (bundled in `server/`)
- Google Cloud project with OAuth Desktop client + Sheets API + Drive API enabled

## 1. Run the Maps Skill Setup

```bash
cd <skill_dir>
python scripts/setup.py
```

Prompts for:
- **API token** → paste from Leads Sniper extension side panel
- **Server** → auto-detects bundled `server/local-api.exe`, offers to start it
- **Storage dir** → where CSVs + history.json go (default: `~/Hermes_Scrapes`)
- **Telegram** → optional, auto-detects from Hermes `.env`
- **Google Workspace** → if not set up, offers interactive wizard

## 2. Google Workspace (if not set up)

**If user says "y" to interactive setup:**

```
Step 1: Enter path to client_secret.json
Step 2: Press Enter after enabling Sheets API + Drive API
Step 3: Open the printed URL, authorize, paste redirect URL back
Step 4: Token exchange happens automatically
Step 5: Verification runs automatically
```

**If user says "n" (manual):**

```bash
GSETUP="python $HERMES_HOME/skills/productivity/google-workspace/scripts/setup.py"
$GSETUP --client-secret /path/to/client_secret.json
$GSETUP --auth-url                     # → open URL, authorize, copy redirect
$GSETUP --auth-code "http://localhost:1/?code=..."
$GSETUP --check                        # → should print AUTHENTICATED
```

> ⚠️ `--services` and `--format` flags do NOT exist on google-workspace setup.py.

## 3. Server Management

The server is **auto-started** by `run_scrape.py` and the scrape workflow.

| Manual command | What it does |
|----------------|-------------|
| `python scripts/server.py start` | Launch server, wait for ready |
| `python scripts/server.py status` | Check if running |
| `python scripts/server.py stop` | Stop gracefully |
| `python scripts/server.py log 20` | Last 20 lines of server log |

## 4. Scraping

**Agent workflow:** Always use `delegate_task`. The subagent should:
1. Call `python scripts/server.py ensure` (or `run_scrape.py` does it automatically)
2. Test API with `GET /v1/status`
3. Submit search: `POST /v1/google-maps/search`
4. Poll every 45s until `completed` or `stopped`
5. Download CSV: `GET /v1/jobs/{id}/export.csv`
6. Upload to Sheets: `python scripts/upload_csv_to_sheets.py <JOB_ID> "Title"`
7. Verify `history.json` was updated

## 5. Common Pitfalls

- **401 Unauthorized** → Token rotated. Check `LEADS_SNIPER_TOKEN` env var, then `config.json`, then Chrome extension LevelDB.
- **`/v1/status` returns 401** → The health endpoint requires `Authorization: Bearer <token>`. `server.py` handles this automatically — sends the token and treats 401 as "server is up". When testing manually, include the `-H "Authorization: Bearer <token>"` header.
- **403 Sheets API** → API not enabled in Google Cloud Console. Enable at: `https://console.developers.google.com/apis/api/sheets.googleapis.com/overview`
- **Server won't start** → Check `server/server.log` for errors. The exe may need admin or the port 8787 may be in use.
- **Server setup order**: In `setup.py`, the server section comes BEFORE the API test. The server must be running before the test will pass.
- **Windows process management**: `os.kill` does NOT work on Windows. `server.py` uses `tasklist`/`taskkill` for Windows, `os.kill` for Linux/Mac.
- **Token exchange fails** → Code expired. Run `--auth-url` again for a fresh URL.
- **`--services` / `--format` flags fail** → Those don't exist on google-workspace setup.py. Use bare `--auth-url` and `--auth-code "<url>"`.
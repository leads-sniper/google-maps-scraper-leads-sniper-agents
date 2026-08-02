# Token Recovery — Leads Sniper API

## Why the token goes stale

The Leads Sniper Chrome extension generates the API key. It can be rotated via the extension UI or the API. The token can drift when someone rotates it.

## Infrastructure layout

| Component | Location (typical) |
|-----------|-------------------|
| API server | `local-api.exe` — check process list / netstat for port 8787 |
| Electron app config | `~/AppData/Roaming/leads-sniper-domain-scraper/` (database.db, Preferences, Local State) |
| Chrome extension LevelDB | `~/AppData/Local/Google/Chrome/User Data/Default/Local Extension Settings/` |
| Extension IDs observed | `efanbdapblmioigjkkgjkmhoclopfcco`, `gomaljcnlkdihcfibegjhlkoeiphamoe`, `ifibfemgeogfhoebkmokieepdoobkbpo`, `jnpopddenbjmnbffejfkonfeclaklcje`, `majdfhpaihoncoakbjgbdhglocklcgno`, `mdjblmhlefooihlgfadiplnnlanedpjp` |

## Config & token sources (resolution order)

When a script needs the API token, it resolves in this order:

1. **`LEADS_SNIPER_TOKEN` env var** — always checked first
2. **`config.json`** — the skill's portable config (set via `setup.py`)
3. **`GMAPS_BASE_URL` env var** — API endpoint override

When you need to find or recover a token:

### Priority checklist

1. **Test current token** — `curl -s http://127.0.0.1:8787/v1/status -H "Authorization: Bearer <TOKEN>"`
2. **Check env vars** — `echo $LEADS_SNIPER_TOKEN`
3. **Check config.json** — read the `api.token` field
4. **Search Chrome extension LevelDB** — `strings .../Local Extension Settings/<ext_id>/000003.log | grep -oE '[a-f0-9]{32}' | sort -u`
5. **Extract from `local-api.exe` binary** — use `strings` or Python to find embedded 32-char hex strings, then test each against `/v1/status`
6. **Rotate via API** — `POST /v1/auth/rotate-key` with `{"old_key":"<CURRENT>","new_key":"<NEW_32_HEX>"}` (requires knowing the current key)

### Browser fallback (last resort)

Open the Chrome extension's side panel UI and look for the "Local API" / "API Key" section where the key is displayed.

## Live mid-job token flips (fastest recovery path)

Observed in practice: the extension can auto re-sync its key **during an active scrape**, not just between sessions. A token that worked for the initial `POST /v1/google-maps/search` 401'd on a later poll and on `export.csv`, with no config edits made in between. The fastest fix does not require LevelDB spelunking:

1. `python scripts/server.py log 20` — look for the most recent line:
   `[INFO] API Key automatically synchronized with Chrome Extension: <32-hex>`
   That is the currently-active token as of that timestamp.
2. Test it: `GET /v1/status` with `Authorization: Bearer <that token>`. If 200, use it.
3. If it still 401s, the key may have flipped back — test the token you started the job with. In one observed case the sequence was: `token_A` (worked for search) → `token_B` (synced, worked for polling) → `token_A` again (synced back, needed for `export.csv`). Only two candidates were ever in play; you don't need to guess arbitrary hex strings, just check `server.py log` and try both directions.
4. Update `config.json`'s `api.token` with whichever candidate returns 200, then immediately retry the failed call (search/poll/export) — don't restart the whole job, the job itself keeps running server-side across these key flips.
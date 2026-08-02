#!/usr/bin/env python3
"""
Reusable uploader: fetch Leads Sniper CSV from API and upload to a public
editable Google Sheet. Handles large datasets that overflow the CLI arg limit.

Usage:
  python upload_csv_to_sheets.py JOB_ID ["Sheet Title"]

Reads config from:
  - config.json in the skill root (via scripts/lib.py)
  - LEADS_SNIPER_TOKEN env var (takes precedence)
  - google_token.json in HERMES_HOME (from google-workspace skill setup)
"""

import csv
import datetime
import io
import json
import os
import sys
import urllib.request
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# ── Config via shared lib ────────────────────────────────────────────────────

from lib import (
    get_api_base_url,
    get_api_token,
    get_storage_dir,
    get_google_token_path,
    load_config,
)

config = load_config()
AUTH_TOKEN = get_api_token(config)
BASE_URL = get_api_base_url(config)
STORAGE_DIR = get_storage_dir(config)
TOKEN_PATH = get_google_token_path()

# ── Ensure storage dir exists ────────────────────────────────────────────────

STORAGE_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_PATH = STORAGE_DIR / "history.json"

# ── Args ─────────────────────────────────────────────────────────────────────

if len(sys.argv) < 2:
    print("Usage: python upload_csv_to_sheets.py JOB_ID [\"Sheet Title\"]")
    sys.exit(1)

JOB_ID = sys.argv[1]
TITLE = sys.argv[2] if len(sys.argv) > 2 else f"Leads Sniper - {JOB_ID}"

# ── Fetch CSV from API ───────────────────────────────────────────────────────

auth_header = f"Bearer {AUTH_TOKEN}" if AUTH_TOKEN else ""
if not auth_header:
    print("ERROR: No API token found. Run setup.py or set LEADS_SNIPER_TOKEN env var.", file=sys.stderr)
    sys.exit(1)

req = urllib.request.Request(
    f"{BASE_URL.rstrip('/')}/v1/jobs/{JOB_ID}/export.csv",
    headers={"Authorization": auth_header},
)
csv_text = urllib.request.urlopen(req, timeout=60).read().decode("utf-8")
reader = csv.reader(io.StringIO(csv_text))
data = [row for row in reader]
print(f"  → {len(data)} rows × {len(data[0])} columns", file=sys.stderr)

# ── Save CSV locally ─────────────────────────────────────────────────────────

csv_path = STORAGE_DIR / f"gmaps_{JOB_ID}.csv"
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(data)
print(f"  → CSV saved: {csv_path}", file=sys.stderr)

# ── Create Google Sheet ──────────────────────────────────────────────────────

if not TOKEN_PATH.exists():
    print(f"ERROR: Google token not found at {TOKEN_PATH}. Run google-workspace setup first.", file=sys.stderr)
    sys.exit(1)

creds = Credentials.from_authorized_user_file(str(TOKEN_PATH))
sheets = build("sheets", "v4", credentials=creds)
sheet = sheets.spreadsheets().create(
    body={"properties": {"title": TITLE}},
    fields="spreadsheetId,spreadsheetUrl",
).execute()
SID, SUR = sheet["spreadsheetId"], sheet["spreadsheetUrl"]
print(f"Sheet created: {SUR}", file=sys.stderr)

# ── Upload data ──────────────────────────────────────────────────────────────


def col_letter(n):
    result = ""
    while n > 0:
        n -= 1
        result = chr(65 + n % 26) + result
        n //= 26
    return result or "A"


cols = len(data[0]) if data else 1
range_str = f"Sheet1!A1:{col_letter(cols)}{len(data)}"
r = (
    sheets.spreadsheets()
    .values()
    .update(
        spreadsheetId=SID,
        range=range_str,
        valueInputOption="USER_ENTERED",
        body={"range": range_str, "values": data, "majorDimension": "ROWS"},
    )
    .execute()
)
print(f"  → {r.get('updatedCells')} cells written", file=sys.stderr)

# ── Make public + editable ───────────────────────────────────────────────────

drive = build("drive", "v3", credentials=creds)
drive.permissions().create(
    fileId=SID, body={"type": "anyone", "role": "writer"}, fields="id"
).execute()
print("  → Public & editable", file=sys.stderr)

# ── Append to history.json ───────────────────────────────────────────────────

history = []
if HISTORY_PATH.exists():
    with open(HISTORY_PATH, "r") as f:
        try:
            history = json.load(f)
        except Exception:
            history = []

# Parse title to extract niche + location
# Priority 1: "Niches - Location" split on " - "
# Priority 2: "X in Y" format (e.g. "Restaurants in New York")
cleaned = TITLE.replace("Google Maps - ", "")
if " - " in cleaned:
    title_parts = cleaned.split(" - ", 1)
    niche, location = title_parts[0], title_parts[1]
elif " in " in cleaned:
    title_parts = cleaned.rsplit(" in ", 1)
    niche, location = title_parts[0], title_parts[1]
else:
    niche, location = cleaned, ""
query = f"{niche} in {location}" if location else niche

record = {
    "id": len(history) + 1,
    "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "query": query,
    "niche": niche,
    "location": location,
    "count": len(data) - 1,
    "csv_path": str(csv_path),
    "sheet_url": SUR,
}
history.append(record)
with open(HISTORY_PATH, "w") as f:
    json.dump(history, f, indent=2)
print(f"  → history.json updated ({len(history)} total records)", file=sys.stderr)

# ── Output: sheet URL + count for the agent ──────────────────────────────────

print(f"{SUR}|{len(data)-1}")
#!/usr/bin/env python3
"""
Silent Google Maps scraper — runs in background, logs progress to file.
Usage: python run_scrape.py <keyword> <location> [limit] [extract_emails]

Reads config from config.json in the skill root (via scripts/lib.py).
Falls back to LEADS_SNIPER_TOKEN env var.

Auto-starts the bundled Leads Sniper server if it's not already running.

The agent polls the progress log and shows clean updates to the user.
"""

import csv
import io
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

# ── Config via shared lib ────────────────────────────────────────────────────

from lib import get_api_base_url, get_api_token, get_storage_dir, load_config

config = load_config()
TOKEN = get_api_token(config)
BASE = get_api_base_url(config)
STORAGE_DIR = get_storage_dir(config)

# ── Auto-start server if bundled ──

SKILL_DIR = Path(__file__).resolve().parent.parent
server_script = SKILL_DIR / "scripts" / "server.py"
if server_script.exists():
    r = subprocess.run(
        [sys.executable, str(server_script), "ensure"],
        capture_output=True, text=True, timeout=35
    )
    if r.returncode != 0:
        print(f"Warning: Server may not be ready: {r.stdout.strip()}", file=sys.stderr)

# Progress files (per-run, in storage dir)
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
PROGRESS_LOG = str(STORAGE_DIR / "gmaps_progress.log")
DATA_FILE = str(STORAGE_DIR / "gmaps_data.json")

# ── Args ─────────────────────────────────────────────────────────────────────

KEYWORD = sys.argv[1] if len(sys.argv) > 1 else "restaurants"
LOCATION = sys.argv[2] if len(sys.argv) > 2 else ""
LIMIT = int(sys.argv[3]) if len(sys.argv) > 3 else 100
EXTRACT = sys.argv[4].lower() in ("true", "1", "yes") if len(sys.argv) > 4 else True

AUTH = f"Bearer {TOKEN}" if TOKEN else ""
if not AUTH:
    print("ERROR: No API token. Run setup.py or set LEADS_SNIPER_TOKEN.", file=sys.stderr)
    sys.exit(1)

# ── Helpers ──────────────────────────────────────────────────────────────────


def log(status, found=0, limit=0):
    with open(PROGRESS_LOG, "w") as f:
        f.write(f"{status}|{found}|{limit}\n")


def api(method, path, data=None):
    url = f"{BASE.rstrip('/')}{path}"
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": AUTH,
            "Content-Type": "application/json",
        },
    )
    resp = urllib.request.urlopen(req, timeout=300)
    return json.loads(resp.read().decode())


# ── Main ─────────────────────────────────────────────────────────────────────

# Build payload
payload = {"keyword": KEYWORD, "limit": LIMIT, "extract_emails": EXTRACT}
if LOCATION:
    payload["location"] = LOCATION

try:
    # Step 1: Submit
    resp = api("POST", "/v1/google-maps/search", json.dumps(payload).encode())
    job_id = resp["job_id"]
    log("queued", 0, LIMIT)

    # Step 2: Poll
    while True:
        time.sleep(45)
        d = api("GET", f"/v1/jobs/{job_id}")
        st, tf = d["status"], d.get("total_found", 0)
        limit = d.get("limit", LIMIT)
        error = d.get("error", "")
        log(st, tf, limit)

        if st == "completed":
            break
        elif st == "stopped":
            if tf > 0:
                log("partial", tf, limit)
                break
            else:
                log("no_results", 0, 0)
                sys.exit(1)
        elif st == "failed":
            log("failed", 0, 0)
            sys.exit(1)

    # Step 3: Download CSV
    req = urllib.request.Request(
        f"{BASE.rstrip('/')}/v1/jobs/{job_id}/export.csv",
        headers={"Authorization": AUTH},
    )
    csv_text = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
    reader = csv.reader(io.StringIO(csv_text))
    data = [row for row in reader]

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)

    log("done", len(data) - 1, limit)

except Exception as e:
    log(f"error|{str(e)}", 0, 0)
    sys.exit(1)
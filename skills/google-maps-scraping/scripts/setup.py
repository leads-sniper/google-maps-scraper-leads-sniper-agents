#!/usr/bin/env python3
"""
google-maps-scraping — Setup Wizard
====================================
Run ONCE after copying the skill to a new Hermes installation.

What it does:
  1. Detects existing config (migration mode if found)
  2. Prompts for API base URL, token, and storage directory
  3. Optionally tests the API connection
  4. Optionally creates the storage directory
  5. Writes config.json

Usage:
  python scripts/setup.py            # interactive (default)
  python scripts/setup.py --noninteractive  # use defaults / env vars
  python scripts/setup.py --migrate-from <old_config.json>  # import old config
"""

import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

# ---- Add scripts dir to path for lib import ----
SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))
from lib import CONFIG_PATH, DEFAULTS, load_config, save_config, get_hermes_home, check_google_auth
from server import _get_default_exe_name

# ---- Helpers ----

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


def prompt(label, default=None, secret=False):
    """Prompt user for input with optional default."""
    if default:
        display = " [{}]".format(default)
    else:
        display = ""
    p = f"{label}{display}: "
    val = input(p)
    if not val and default is not None:
        return default
    return val.strip()


def banner(msg):
    print(f"\n{BOLD}{CYAN}{'='*60}{RESET}")
    print(f"{BOLD}{CYAN}  {msg}{RESET}")
    print(f"{BOLD}{CYAN}{'='*60}{RESET}\n")


def ok(msg):
    print(f"  {GREEN}+{RESET} {msg}")


def warn(msg):
    print(f"  {YELLOW}!{RESET} {msg}")


def fail(msg):
    print(f"  {RED}x{RESET} {msg}")


def _info(msg):
    print(f"  {CYAN}i{RESET} {msg}")


def test_api(base_url, token):
    """Ping the Leads Sniper API health endpoint."""
    if not token:
        return False, "No token provided"
    try:
        req = urllib.request.Request(
            f"{base_url.rstrip('/')}/v1/status",
            headers={"Authorization": f"Bearer {token}"},
        )
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read().decode())
        ok(f"API online — {data.get('status', 'unknown')} ({data.get('extension_connected', False)})")
        return True, data
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}: {e.reason}"
    except Exception as e:
        return False, str(e)


def download_server_binary(dest_path, binary_name):
    """Download the correct native Leads Sniper API server binary from GitHub Releases."""
    BASE_URL = "https://github.com/leads-sniper/google-maps-scraper-leads-sniper-agents/releases/latest/download/"
    url = f"{BASE_URL}{binary_name}"
    
    print(f"  Downloading native Leads Sniper API server for your platform...")
    print(f"  Source: {url}")
    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        # Download block-by-block to show progress
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        with urllib.request.urlopen(req) as response, open(dest_path, 'wb') as out_file:
            meta = response.info()
            file_size = int(meta.get("Content-Length", 0))
            downloaded = 0
            block_size = 16384
            
            while True:
                buffer = response.read(block_size)
                if not buffer:
                    break
                downloaded += len(buffer)
                out_file.write(buffer)
                if file_size > 0:
                    percent = downloaded * 100 / file_size
                    sys.stdout.write(f"\r  Progress: {percent:.1f}% ({downloaded / (1024*1024):.1f}MB / {file_size / (1024*1024):.1f}MB)")
                    sys.stdout.flush()
            print()
        
        # Set executable permissions on Unix systems
        if sys.platform != "win32":
            try:
                os.chmod(str(dest_path), 0o755)
            except Exception:
                pass
            
        ok(f"Successfully downloaded and configured native server: {dest_path.name}")
        return True
    except Exception as e:
        fail(f"Failed to download server binary: {e}")
        return False


def _run_gws(args, gws_setup, capture=False):
    """Run a google-workspace setup command and return output."""
    cmd = [sys.executable, str(gws_setup)] + args
    r = subprocess.run(cmd, capture_output=capture, text=True, timeout=30)
    return r


def google_workspace_section(existing, has_existing):
    """Check Google Workspace auth and guide the user through setup interactively."""
    print(f"\n{BOLD}{CYAN}── Google Workspace Integration (Optional) ──{RESET}")

    authed, token_path = check_google_auth()
    redoing = False
    if authed:
        ok(f"Google Workspace authenticated — token at: {token_path}")
        print()
        redo = prompt("  Re-run Google Workspace setup anyway? (overwrites existing token)", default="n").lower()
        if redo not in ("y", "yes"):
            print()
            return
        redoing = True
        warn("Existing token will be overwritten.")
        print()

    hermes_home = get_hermes_home()
    gws_skill = hermes_home / "skills" / "productivity" / "google-workspace"
    gws_setup = gws_skill / "scripts" / "setup.py"

    if not redoing:
        warn("Google Workspace is NOT set up yet.")
        print()

    if not gws_setup.exists():
        warn(f"google-workspace skill not found at {gws_skill}")
        print()
        print("  You need to install the google-workspace skill first.")
        print("  The skill is available in the Hermes skills repository.")
        print("  After installing, re-run this setup to verify.")
        print()
        return

    ok(f"Found google-workspace skill at: {gws_skill}")
    print()

    # Ask if they want to run it interactively
    run_now = prompt("  Would you like to set up Google Workspace now?", default="n").lower()

    if run_now not in ("y", "yes"):
        warn("Skipping Google Workspace setup. Scrapes will save CSVs locally but won't upload to Sheets.")
        print()
        return

    # ── Interactive setup ──
    print()
    print(f"  {BOLD}Interactive Google Workspace Setup{RESET}")
    print()

    # Step 1: Ask for client secret path
    print(f"  {BOLD}Step 1: OAuth credentials{RESET}")
    print("  If you haven't created them yet, go to:")
    print("    https://console.cloud.google.com/apis/credentials")
    print("    → Create Credentials → OAuth 2.0 Client ID → Desktop app")
    print("    Download the JSON file.")
    print()
    secret_path = prompt("  Path to client_secret.json", default="").strip()
    while secret_path and not Path(secret_path).exists():
        fail(f"File not found: {secret_path}")
        secret_path = prompt("  Path to client_secret.json (or press Enter to skip)", default="").strip()
    print()

    if secret_path:
        r = _run_gws(["--client-secret", secret_path], gws_setup)
        if r.returncode == 0:
            ok("Client secret registered")
        else:
            fail(f"Failed: {r.stderr or r.stdout}")
            print()
            return
    else:
        warn("Skipping client secret registration.")
        print()
        return

    # Step 2: Enable APIs reminder
    print(f"  {BOLD}Step 2: Enable APIs{RESET}")
    print("  Make sure these APIs are enabled in your Google Cloud project:")
    print("    https://console.developers.google.com/apis/api/sheets.googleapis.com/overview")
    print("    https://console.developers.google.com/apis/api/drive.googleapis.com/overview")
    print()
    input("  Press Enter once you've enabled them (or skip if already done)...")
    print()

    # Step 3: Get auth URL
    print(f"  {BOLD}Step 3: Authorize in browser{RESET}")
    r = _run_gws(["--auth-url"], gws_setup, capture=True)
    if r.returncode != 0:
        fail(f"Failed to get auth URL: {r.stderr or r.stdout}")
        print()
        return
    auth_url = r.stdout.strip()
    print(f"  Open this URL in your browser:")
    print(f"  {BOLD}{auth_url}{RESET}")
    print()
    print("  Sign in with your Google account and authorize Hermes.")
    print("  The browser will redirect to http://localhost:1/?code=...")
    print("  Copy the ENTIRE redirect URL from the address bar.")
    print()
    redirect_url = prompt("  Paste the redirect URL here").strip()
    print()

    # Step 4: Exchange the code
    print(f"  {BOLD}Step 4: Exchanging code...{RESET}")
    r = _run_gws(["--auth-code", redirect_url], gws_setup, capture=True)
    print(f"  {r.stdout.strip()}")
    if r.returncode != 0:
        fail(f"Exchange failed")
        print()
        return
    print()

    # Step 5: Verify
    print(f"  {BOLD}Step 5: Verifying...{RESET}")
    r = _run_gws(["--check"], gws_setup, capture=True)
    print(f"  {r.stdout.strip()}")
    if r.returncode == 0:
        ok("Google Workspace is ready!")
    else:
        warn("Verification failed — check the output above.")
    print()


# ---- Main ----

def main():
    banner("Google Maps Scraping — Setup")

    # Detect existing config
    existing = load_config()
    has_existing = CONFIG_PATH.exists() and CONFIG_PATH.stat().st_size > 30
    if has_existing:
        warn(f"Existing config found at: {CONFIG_PATH}")
        print("  Press Enter to keep current values, or type new ones.\n")

    print(f"\n{BOLD}{CYAN}── API Configuration ──{RESET}")

    # API Base URL
    default_url = existing.get("api", {}).get("base_url") or DEFAULTS["api"]["base_url"]
    url = prompt("  API Base URL", default=default_url)
    print()

    # API Token
    default_token = existing.get("api", {}).get("token") or ""
    # Show masked hint if one exists
    if default_token:
        hint = default_token[:6] + "****" + default_token[-4:]
        print(f"  Current token: {hint}")
    token_source = prompt(
        "  API Token (or press Enter to keep using LEADS_SNIPER_TOKEN env var)",
        default="(env var)" if not default_token else "(keep current)",
    )
    if token_source in ("(env var)", "(keep current)", ""):
        if has_existing and default_token:
            resolved_token = default_token
        else:
            resolved_token = os.environ.get("LEADS_SNIPER_TOKEN", "")
    else:
        resolved_token = token_source
    print()

    print(f"\n{BOLD}{CYAN}── Leads Sniper Server ──{RESET}")

    # Auto-detect bundled exe
    exe_name = _get_default_exe_name()
    bundled_exe = SKILL_DIR / "server" / exe_name
    default_server = existing.get("api", {}).get("server_path") or str(bundled_exe)

    if bundled_exe.exists():
        ok(f"Bundled server found: {bundled_exe}")
        server_path = str(bundled_exe)
    else:
        platform_fallback = "local-api.exe" if sys.platform == "win32" else "local-api"
        generic_exe = SKILL_DIR / "server" / platform_fallback
        if generic_exe.exists():
            ok(f"Bundled server found: {generic_exe}")
            server_path = str(generic_exe)
        else:
            warn("No server binary found in skill folder.")
            download_now = prompt("  Would you like to download the native server binary now?", default="y").lower()
            if download_now in ("y", "yes"):
                success = download_server_binary(bundled_exe, exe_name)
                if success:
                    server_path = str(bundled_exe)
                else:
                    server_path = prompt(f"  Path to server binary ({platform_fallback})", default=default_server)
            else:
                server_path = prompt(f"  Path to server binary ({platform_fallback})", default=default_server)
                
            if server_path and not Path(server_path).exists():
                warn(f"File not found: {server_path}")
                warn("You can set it later in config.json")
            print()

    # Option to start the server now
    if server_path and Path(server_path).exists():
        # Check if server is already running
        import subprocess as _sp
        status_r = _sp.run(
            [sys.executable, str(SKILL_DIR / "scripts" / "server.py"), "status"],
            capture_output=True, text=True, timeout=10
        )
        server_already_running = (status_r.returncode == 0)

        if server_already_running:
            ok("Server is already running")
            restart = prompt("  Restart server? (to pick up new token)", default="n").lower()
            if restart in ("y", "yes"):
                _info("Restarting server...")
                r = _sp.run(
                    [sys.executable, str(SKILL_DIR / "scripts" / "server.py"), "restart"],
                    capture_output=True, text=True, timeout=40
                )
                print(f"  {r.stdout.strip()}")
                if r.returncode != 0:
                    warn("Server restart may have failed.")
        else:
            start_now = prompt("  Start the server now?", default="y").lower()
            if start_now in ("y", "yes"):
                _info("Starting server...")
                r = _sp.run(
                    [sys.executable, str(SKILL_DIR / "scripts" / "server.py"), "ensure"],
                    capture_output=True, text=True, timeout=35
                )
                if r.stdout.strip():
                    print(f"  {r.stdout.strip()}")
                if r.stderr.strip():
                    print(f"  STDERR: {r.stderr.strip()}")
                if r.returncode != 0:
                    # Fallback: try direct launch + port check
                    _info("Direct launch fallback...")
                    r2 = _sp.run(
                        [sys.executable, str(SKILL_DIR / "scripts" / "server.py"), "start"],
                        capture_output=True, text=True, timeout=40
                    )
                    if r2.stdout.strip():
                        print(f"  {r2.stdout.strip()}")
                    if r2.returncode == 0:
                        ok("Server started via fallback")
                    else:
                        warn(f"Server start failed (code {r2.returncode})")
                        if r2.stderr.strip():
                            print(f"  STDERR: {r2.stderr.strip()}")
        print()

    # Test connection (now that server has a chance to be running)
    test_choice = prompt("  Test API connection now?", default="y").lower()
    if test_choice in ("y", "yes"):
        print()
        ok_conn, msg = test_api(url, resolved_token)
        if not ok_conn:
            warn(f"Connection failed: {msg}")
            warn("Check that the server is running and the token is correct.")
        print()

    print(f"\n{BOLD}{CYAN}── Storage Settings ──{RESET}")

    default_storage = existing.get("storage", {}).get("dir") or DEFAULTS["storage"]["dir"]
    storage_dir = prompt("  Storage directory", default=default_storage)

    # Create storage dir?
    expanded = os.path.expanduser(storage_dir)
    if not Path(expanded).exists():
        create = prompt(f"  Create '{expanded}' now?", default="y").lower()
        if create in ("y", "yes"):
            Path(expanded).mkdir(parents=True, exist_ok=True)
            ok(f"Created: {expanded}")
    else:
        ok(f"Directory exists: {expanded}")
    print()

    print(f"\n{BOLD}{CYAN}── Telegram Notifications (Optional) ──{RESET}")

    default_tg = existing.get("telegram", {}).get("bot_token", "")
    if default_tg:
        tg_hint = default_tg[:6] + "****"
    else:
        tg_hint = ""
    tg_token = prompt(
        "  Telegram Bot Token (leave blank to auto-detect from hermes .env)",
        default=tg_hint if tg_hint else "(auto-detect)",
    )
    if tg_token in ("(auto-detect)", ""):
        tg_token = ""
    print()

    # ── Google Workspace check ──
    google_workspace_section(existing, has_existing)

    # ---- Build config ----
    config = {
        "api": {
            "base_url": url,
            "token_env_var": "LEADS_SNIPER_TOKEN",
            "token": resolved_token,
            "server_path": server_path,
        },
        "storage": {
            "dir": storage_dir,
        },
        "telegram": {
            "bot_token": tg_token,
        },
    }

    # ---- Write ----
    save_config(config)
    print(f"\n{BOLD}{GREEN}+ Setup complete!{RESET}")
    print(f"  Config written to: {CONFIG_PATH}")

    # Summary
    print(f"\n{BOLD}Config summary:{RESET}")
    print(f"  API endpoint : {url}")
    masked = resolved_token[:6] + "****" + resolved_token[-4:] if resolved_token else "(env var only)"
    print(f"  API token    : {masked}")
    print(f"  Storage dir  : {storage_dir}")
    print(f"  Server       : {'bundled' if server_path and 'server' in server_path else server_path or 'not configured'}")
    print(f"  Telegram     : {'configured' if tg_token else 'auto-detect'}")
    print()
    print("  ── Next steps ──")
    gws_ok, _ = check_google_auth()
    if gws_ok:
        print("  [+] Google Workspace ready -- you're all set!")
    else:
        print("  1. Google Workspace: check if it's already set up, then follow the steps:")
        print(f"     python \"{SKILL_DIR.parent.parent / 'productivity' / 'google-workspace' / 'scripts' / 'setup.py'}\" --check")
        print("     If that says NOT_AUTHENTICATED, create OAuth credentials at:")
        print("       https://console.cloud.google.com/apis/credentials")
        print("     Then enable these APIs in your Google Cloud project:")
        print("       https://console.developers.google.com/apis/api/sheets.googleapis.com/overview")
        print("       https://console.developers.google.com/apis/api/drive.googleapis.com/overview")
        print("     Then register the secret and authorize:")
        print(f"       python \"{SKILL_DIR.parent.parent / 'productivity' / 'google-workspace' / 'scripts' / 'setup.py'}\" --client-secret /path/to/client_secret.json")
        print(f"       python \"{SKILL_DIR.parent.parent / 'productivity' / 'google-workspace' / 'scripts' / 'setup.py'}\" --auth-url")
        print("     (Open the URL, authorize, paste the redirect URL back)")
        print(f"       python \"{SKILL_DIR.parent.parent / 'productivity' / 'google-workspace' / 'scripts' / 'setup.py'}\" --auth-code \"<redirect_url>\"")
    print("  2. Start scraping! Load the skill and run a search.")
    print()


if __name__ == "__main__":
    # Handle --migrate-from
    if "--migrate-from" in sys.argv:
        idx = sys.argv.index("--migrate-from")
        old_path = sys.argv[idx + 1]
        with open(old_path) as f:
            old_config = json.load(f)
        save_config(old_config)
        print(f"Migrated config from {old_path} → {CONFIG_PATH}")
        sys.exit(0)

    # Non-interactive: write defaults + env vars, test if token present
    if "--noninteractive" in sys.argv:
        config = json.loads(json.dumps(DEFAULTS))
        env_token = os.environ.get("LEADS_SNIPER_TOKEN")
        if env_token:
            config["api"]["token"] = env_token
        env_url = os.environ.get("GMAPS_BASE_URL")
        if env_url:
            config["api"]["base_url"] = env_url
        env_storage = os.environ.get("GMAPS_STORAGE_DIR")
        if env_storage:
            config["storage"]["dir"] = env_storage
        # Auto-detect bundled server
        exe_name = _get_default_exe_name()
        bundled = SKILL_DIR / "server" / exe_name
        if not bundled.exists():
            platform_fallback = "local-api.exe" if sys.platform == "win32" else "local-api"
            generic_exe = SKILL_DIR / "server" / platform_fallback
            if generic_exe.exists():
                bundled = generic_exe
            else:
                download_success = download_server_binary(bundled, exe_name)
                if not download_success:
                    bundled = None
                    
        if bundled and bundled.exists():
            config["api"]["server_path"] = str(bundled)
        save_config(config)
        ok(f"Config written to {CONFIG_PATH}")

        if config["api"]["token"]:
            ok_conn, msg = test_api(config["api"]["base_url"], config["api"]["token"])
            if ok_conn:
                ok("API connection verified")
            else:
                warn(f"API test: {msg}")

        # Check Google auth
        authed, _ = check_google_auth()
        if authed:
            ok("Google Workspace authenticated")
        else:
            warn("Google Workspace not set up — run 'python scripts/setup.py' for instructions")
        sys.exit(0)

    main()
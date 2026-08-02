#!/usr/bin/env python3
"""
Shared config loader for the google-maps-scraping skill.
All scripts import from here instead of hardcoding paths.

Config resolution order (first wins):
  1. Environment variables (LEADS_SNIPER_TOKEN, GMAPS_BASE_URL, GMAPS_STORAGE_DIR)
  2. config.json in the skill root directory
  3. Built-in defaults
"""

import json
import os
from pathlib import Path

# ── Path resolution ──────────────────────────────────────────────────────────

SKILL_DIR = Path(__file__).resolve().parent.parent  # scripts/../ = skill root
CONFIG_PATH = SKILL_DIR / "config.json"

# ── Defaults ─────────────────────────────────────────────────────────────────

DEFAULTS = {
    "api": {
        "base_url": "http://127.0.0.1:8787",
        "token_env_var": "LEADS_SNIPER_TOKEN",
        "token": None,  # only set if not using env var
    },
    "storage": {
        "dir": "~/Hermes_Scrapes",
    },
    "telegram": {
        # If empty, auto-detect from hermes .env
        "bot_token": "",
    },
}

# ── Config loading ───────────────────────────────────────────────────────────

def load_config():
    """Deep-merge user config from config.json over DEFAULTS."""
    config = json.loads(json.dumps(DEFAULTS))  # deep copy
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            user_config = json.load(f)
        for section, values in user_config.items():
            if section in config and isinstance(config[section], dict):
                config[section].update(values)
            else:
                config[section] = values
    return config


def get_api_base_url(config=None):
    """API base URL: env var > config > default."""
    if config is None:
        config = load_config()
    return os.environ.get("GMAPS_BASE_URL") or config.get("api", {}).get("base_url", "http://127.0.0.1:8787")


def get_api_token(config=None):
    """API token: env var > config value > None."""
    if config is None:
        config = load_config()
    env_var = config.get("api", {}).get("token_env_var", "LEADS_SNIPER_TOKEN")
    token = os.environ.get(env_var)
    if not token:
        token = config.get("api", {}).get("token")
    return token


def get_storage_dir(config=None):
    """Storage directory: env var > config > default, with ~ expansion."""
    if config is None:
        config = load_config()
    raw = os.environ.get("GMAPS_STORAGE_DIR") or config.get("storage", {}).get("dir", "~/Hermes_Scrapes")
    return Path(os.path.expanduser(raw)).resolve()


def get_hermes_home():
    """Resolve HERMES_HOME (AppData/Local/hermes)."""
    env = os.environ.get("HERMES_HOME")
    if env:
        return Path(env)
    # Fallback: ~/AppData/Local/hermes (cross-platform home detection)
    return Path.home() / "AppData" / "Local" / "hermes"


def get_google_token_path():
    """Path to google_token.json for Sheets uploads."""
    return get_hermes_home() / "google_token.json"


def save_config(config):
    """Write config to config.json (creates parent dirs)."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


def check_google_auth():
    """Check if Google Workspace OAuth token exists and is valid.
    
    Attempts to load and refresh the token (like google-workspace --check does).
    
    Returns (is_authenticated: bool, token_path: Path | None).
    Token path is None if file doesn't exist.
    """
    token_path = get_google_token_path()
    if not token_path.exists():
        return False, None

    # Try actual Google auth validation (handles refresh)
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request

        creds = Credentials.from_authorized_user_file(str(token_path))

        if creds.valid:
            return True, token_path

        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Save refreshed token
            import json
            token_path.write_text(
                json.dumps(
                    {"type": "authorized_user", **json.loads(creds.to_json())},
                    indent=2
                )
            )
            return True, token_path

        return False, token_path
    except ImportError:
        # Fallback: just check file exists and expiry
        try:
            import json
            from datetime import datetime
            token_data = json.loads(token_path.read_text())
            expiry = token_data.get("expiry")
            if expiry:
                exp = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
                if exp < datetime.now().astimezone():
                    return False, token_path
            return True, token_path
        except Exception:
            return False, token_path
    except Exception:
        return False, token_path
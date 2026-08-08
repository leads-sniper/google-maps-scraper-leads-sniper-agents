#!/usr/bin/env python3
"""
Server lifecycle manager for Leads Sniper local API.
Auto-starts, stops, and monitors the local-api.exe process.

Commands:
  python scripts/server.py ensure    -- Start if not running (used before scrape)
  python scripts/server.py start     -- Start server, wait for ready
  python scripts/server.py stop      -- Stop server gracefully
  python scripts/server.py status    -- Check if running
  python scripts/server.py restart   -- Restart server

The server path is read from config.json (set by setup.py).
If no server is configured, commands are no-ops with a warning.
"""

import json
import os
import signal
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

# -- Paths --
SKILL_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = SKILL_DIR / "config.json"
SERVER_DIR = SKILL_DIR / "server"
PID_FILE = SERVER_DIR / "server.pid"
LOG_FILE = SERVER_DIR / "server.log"

def _get_default_exe_name():
    import sys
    import platform
    system = sys.platform
    arch = platform.machine().lower()
    if system == "win32":
        return "local-api-windows-amd64.exe"
    elif system == "darwin":
        if "arm" in arch or "m1" in arch or "m2" in arch or "m3" in arch:
            return "local-api-darwin-arm64"
        return "local-api-darwin-amd64"
    elif system == "linux":
        if "arm" in arch or "aarch64" in arch:
            return "local-api-linux-arm64"
        return "local-api-linux-amd64"
    return "local-api.exe"

DEFAULT_EXE_NAME = _get_default_exe_name()
DEFAULT_EXE = SERVER_DIR / DEFAULT_EXE_NAME
POLL_INTERVAL = 2
START_TIMEOUT = 30

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

OK_SYM = "+"
WARN_SYM = "!"
FAIL_SYM = "x"
INFO_SYM = "i"


def _ok(msg):
    print(f"  {GREEN}{OK_SYM}{RESET} {msg}")


def _warn(msg):
    print(f"  {YELLOW}{WARN_SYM}{RESET} {msg}")


def _fail(msg):
    print(f"  {RED}{FAIL_SYM}{RESET} {msg}")


def _info(msg):
    print(f"  {CYAN}{INFO_SYM}{RESET} {msg}")


def _load_config():
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text())
        except Exception:
            return {}
    return {}


def _get_server_path():
    cfg = _load_config()
    path_str = cfg.get("api", {}).get("server_path", "")
    if path_str:
        p = Path(path_str)
        if p.exists():
            if sys.platform != "win32":
                try:
                    os.chmod(str(p), 0o755)
                except Exception:
                    pass
            return p

    platform_exe = SERVER_DIR / _get_default_exe_name()
    if platform_exe.exists():
        if sys.platform != "win32":
            try:
                os.chmod(str(platform_exe), 0o755)
            except Exception:
                pass
        return platform_exe

    fallback_name = "local-api.exe" if sys.platform == "win32" else "local-api"
    fallback_exe = SERVER_DIR / fallback_name
    if fallback_exe.exists():
        if sys.platform != "win32":
            try:
                os.chmod(str(fallback_exe), 0o755)
            except Exception:
                pass
        return fallback_exe

    return None


def _get_base_url():
    cfg = _load_config()
    return cfg.get("api", {}).get("base_url", "http://127.0.0.1:8787")


def _get_token():
    cfg = _load_config()
    token = cfg.get("api", {}).get("token", "")
    if not token:
        token = os.environ.get("LEADS_SNIPER_TOKEN", "")
    return token


def _read_pid():
    if PID_FILE.exists():
        try:
            return int(PID_FILE.read_text().strip())
        except (ValueError, OSError):
            return None
    return None


def _write_pid(pid):
    PID_FILE.write_text(str(pid))


def _clear_pid():
    PID_FILE.unlink(missing_ok=True)


def _is_process_alive(pid):
    if not pid:
        return False
    if sys.platform == "win32":
        try:
            r = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                capture_output=True, text=True, timeout=5
            )
            return str(pid) in r.stdout
        except Exception:
            return False
    try:
        os.kill(pid, 0)
        return True
    except (OSError, PermissionError, SystemError):
        return False


def _is_port_open(host, port, timeout=3):
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        s.close()
        return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False
    finally:
        try:
            s.close()
        except Exception:
            pass


def _health_check(base_url):
    try:
        token = _get_token()
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        req = urllib.request.Request(
            f"{base_url.rstrip('/')}/v1/status",
            headers=headers
        )
        urllib.request.urlopen(req, timeout=5)
        return True
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return True
        return False
    except Exception:
        return False


def _parse_host_port(base_url):
    from urllib.parse import urlparse
    parsed = urlparse(base_url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 8787
    return host, port


def cmd_status():
    exe = _get_server_path()
    if not exe:
        _warn("No server executable configured. Run setup.py first.")
        return False

    pid = _read_pid()
    base_url = _get_base_url()

    if pid and _is_process_alive(pid):
        if _health_check(base_url):
            _ok(f"Server running (PID {pid}) -- {base_url}")
            return True
        else:
            _warn(f"Process {pid} exists but API not responding on {base_url}")
            return False
    else:
        host, port = _parse_host_port(base_url)
        if _is_port_open(host, port):
            _ok(f"Server is running on {base_url} (no PID tracked)")
            return True
        else:
            _warn("Server is NOT running")
            return False


def cmd_start():
    exe = _get_server_path()
    if not exe:
        _warn("No server executable found. Run setup.py to configure.")
        return False

    if cmd_status():
        _info("Already running.")
        return True

    _info(f"Starting server: {exe}")

    SERVER_DIR.mkdir(parents=True, exist_ok=True)

    try:
        with open(LOG_FILE, "w") as log:
            proc = subprocess.Popen(
                [str(exe)],
                stdout=log,
                stderr=subprocess.STDOUT,
                cwd=str(SERVER_DIR),
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
        _write_pid(proc.pid)
        _info(f"Process launched (PID {proc.pid}). Waiting for it to be ready...")
    except Exception as e:
        _fail(f"Failed to launch: {e}")
        return False

    base_url = _get_base_url()
    deadline = time.time() + START_TIMEOUT

    while time.time() < deadline:
        if _health_check(base_url):
            _ok(f"Server ready on {base_url}")
            return True
        time.sleep(POLL_INTERVAL)

    _fail(f"Server did not respond within {START_TIMEOUT}s")
    _fail(f"Check log: {LOG_FILE}")
    return False


def cmd_stop():
    pid = _read_pid()
    if pid and _is_process_alive(pid):
        _info(f"Stopping server (PID {pid})...")
        try:
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/F", "/PID", str(pid)],
                               capture_output=True, timeout=5)
            else:
                os.kill(pid, signal.SIGTERM)
                for _ in range(10):
                    if not _is_process_alive(pid):
                        break
                    time.sleep(0.5)
                else:
                    os.kill(pid, signal.SIGKILL)
        except Exception as e:
            _fail(f"Error stopping: {e}")
    else:
        _info("No running server found.")

    _clear_pid()
    _ok("Server stopped")


def cmd_restart():
    cmd_stop()
    time.sleep(1)
    return cmd_start()


def cmd_ensure():
    if not _get_server_path():
        _warn("No server configured -- assuming external server is running.")
        _warn("If scraping fails, check that Leads Sniper API is on.")
        return False
    return cmd_start()


def cmd_log():
    if not LOG_FILE.exists():
        _warn("No server log found.")
        return
    lines = LOG_FILE.read_text().splitlines()
    n = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 20
    for line in lines[-n:]:
        print(line)


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/server.py <start|stop|status|restart|ensure|log>")
        sys.exit(1)

    command = sys.argv[1]
    commands = {
        "start": cmd_start,
        "stop": cmd_stop,
        "status": cmd_status,
        "restart": cmd_restart,
        "ensure": cmd_ensure,
        "log": cmd_log,
    }

    fn = commands.get(command)
    if not fn:
        print(f"Unknown command: {command}")
        print("Available: start, stop, status, restart, ensure, log")
        sys.exit(1)

    success = fn()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
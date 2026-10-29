#!/usr/bin/env python3
# ════════════════════════════════════════════════════════════════════════
#  TASJIL BOT — Telegram | جازي + أوريدو | Python 3.10+ | Webhook Mode
#  نسخة احترافية محسّنة — متعدد الأرقام، بروكسيات منفصلة، قوائم ديناميكية
# ════════════════════════════════════════════════════════════════════════

import os, json, time, re, logging, sqlite3, random, hashlib, asyncio
import aiohttp, aiofiles, base64, secrets, struct, uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any
from functools import wraps

from aiohttp import web
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    BotCommand, MenuButtonCommands
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
from telegram.constants import ParseMode
from telegram.error import TelegramError, BadRequest as TgBadRequest

# ════════════════════════════════════════════════════════════════════════
#  CONFIG
# ════════════════════════════════════════════════════════════════════════
BOT_TOKEN    = "8177922042:AAENSzEnv83UanX9J8egYLeT09ioy9YbTkA"
ADMIN_IDS    = {8499896271}
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_PORT = int(os.getenv("PORT", 8443))
WEBHOOK_URL  = os.getenv("WEBHOOK_URL", "")

ACTIVATION_CHANNEL = "@tasjil_bot_activation"
TG_CHANNEL         = "https://t.me/tasjilbott"

BASE_DIR       = Path("/tmp/tasjil_bot")
SESSIONS_DIR   = BASE_DIR / "sessions"
USERS_DIR      = BASE_DIR / "users"
PENDING_DIR    = BASE_DIR / "pending"
RATE_DIR       = BASE_DIR / "rate_limit"
OO_SESS_DIR    = BASE_DIR / "ooredoo_sessions"
ADMINS_FILE    = BASE_DIR / "admins.json"
USERS_FILE     = BASE_DIR / "users_map.json"
BROADCAST_LOG  = BASE_DIR / "broadcast_log.json"
MATCH_GIFT_F   = BASE_DIR / "match_gift.json"
BAN_FILE       = BASE_DIR / "banned.json"
DB_FILE        = BASE_DIR / "dedup.db"
DJEZZY_LOG     = BASE_DIR / "djezzy.log"
OO_LOG         = BASE_DIR / "ooredoo.log"

# ─── Proxy files (منفصلة لكل شبكة) ───
DJ_PROXIES_FILE    = BASE_DIR / "djezzy_proxies.json"
OO_PROXIES_FILE    = BASE_DIR / "ooredoo_proxies.json"
DJ_PROXY_EN_FILE   = BASE_DIR / "djezzy_proxy_enabled.json"
OO_PROXY_EN_FILE   = BASE_DIR / "ooredoo_proxy_enabled.json"

# ─── Operator disable flags ───
DJ_DISABLED_FILE   = BASE_DIR / "djezzy_disabled.json"
OO_DISABLED_FILE   = BASE_DIR / "ooredoo_disabled.json"

for d in [BASE_DIR, SESSIONS_DIR, USERS_DIR, PENDING_DIR, RATE_DIR, OO_SESS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

RATE_LIMIT_SECONDS = 600

# ════════════════════════════════════════════════════════════════════════
#  DJEZZY CREDENTIALS
# ════════════════════════════════════════════════════════════════════════
DJ_CLIENT_ID_OLD     = "87pIExRhxBb3_wGsA5eSEfyATloa"
DJ_CLIENT_SECRET_OLD = "uf82p68Bgisp8Yg1Uz8Pf6_v1XYa"
DJ_CLIENT_ID_NEW     = "6E6CwTkp8H1CyQxraPmcEJPQ7xka"
DJ_CLIENT_SECRET_NEW = "MVpXHW_ImuMsxKIwrJpoVVMHjRsa"

DJ_PROXY_API_URL = "https://dev-bendjarayacine.pantheonsite.io/wp-admin/maint/proxy.json"

DJ_DEFAULT_PROXIES = [
    "http://gate.kookeey.info:1000:7464034-bc00eb59f5:fc54fe8a0a-DZ-32737453-1m",
    "http://gate.kookeey.info:1000:7464034-bc00eb59f5:fc54fe8a0a-DZ-56432587-1m",
    "http://mobile.kookeey.info:1086:7464034-bc00eb59f5:fc54fe8a0a-DZ-83875156-1m",
    "http://mobile.kookeey.info:1086:7464034-bc00eb59f5:fc54fe8a0a-DZ-55676526-1m",
    "http://gate.kookeey.info:1000:6569414-55154c240e:199dff35c9-DZ-43435299-1m",
    "http://mobile.kookeey.info:1086:6569414-55154c240e:199dff35c9-DZ-79987015-1m",
]

# ════════════════════════════════════════════════════════════════════════
#  OOREDOO CREDENTIALS
# ════════════════════════════════════════════════════════════════════════
OO_BASE            = "https://apis.ooredoo.dz"
OO_BFF             = "https://apis.ooredoo.dz/api/ooredoo-bff"
OO_AUTH            = "https://apis.ooredoo.dz/api/auth/realms/myooredoo/protocol/openid-connect/token"
OO_CLIENT_ID       = "myooredoo-app"
OO_X_VERSION       = "1.5.15"
OO_X_SIG           = "f320f896f3da2a5a0284f9af316efb4ab0432b26406413568db116fa9dc60feb"
OO_PLATFORM        = "android"
OO_PLATFORM_ORIGIN = "mobile-android"

OO_INTEGRITY_1 = "JWBTpxXcH7KY9EXYeIRp8NjQMx2dt3vF8ejjoARazyoFzOw6Cu8+wkeV+zSVHSTeI6a12SG/FU+Q/9uBrcN71RlYO4CulD2x375NKwJRAInar8DVUilHBKUfjEsoHd6EwfLCfdYzLNXJu9POfEf6tqKn3PUe0pY6qZxWLhyVAFHw8Qwb52ZqdI2soCH4S3mrz+OZL+YovdGSUKlXKIkxVroAMTAg3jljLF7gvXaEsB/O3uW+tbkBMwSX2uTOwf+rh3sgOF/zPhKCFgRvZmU1o87Fa96Y/+wOcK+UpfXTCBYVrvQ1wG6ryC7vHMSqgUhYJK4tbSoti0zv4av9pwxh9Iv2MgsMENjyKBK/TuFZxEG3xQCKj1LTMgn2xBEeKcbsKrEW3xDRwsccGI3D7GHnbUlhdI4ujDIRQVKHaZSwhTp+32Cr4EB/Qt8p/xRbdgCde9MUlM4AYIGlfyVoHSkOvTu5c0DIIy1EhowtAkbKIJl49wsYKWvpT/nXFWzeXP3R2qzaclCnIb9qihhrarmwz8l8XH2T+f7AK2uSNiuWLG5Fy2mM/YLmuJPZT9Ciag/mpy7JGImKNQAcFbSAInBdKQjUKT+COzZfrXj5rwil9/HDMtuzIovq8hrQGY+roTfVPheTLWmcjkVCOL8VXAHjPb22vOuqrkMioWT9CQ5O8RgW7RKHrObeKQMp8F7tSjOqkxYDFkPVN1G4nkEBrTlPKK9YtPl+j7IuH9fGcDTwhCTTqP8peuBryW0L11tApvAEi7VkJyBxpVxW"
OO_INTEGRITY_2 = "JWBTpxXcH7KR/kzaHeUUydDWODuU4i3H4fL9gCgKzyYfyN4qLJJE8keV+zSVHSTeI6aEyC2tbSza/NGmkflQ/UgaNZSN9SKxz7tcdQckHY25n6mOaDZ9PPMQmF4sKZqDwebce/c1SNGNn6qvTULW/L348aJvy7Vii6dyPTu3OSPV9AwKwGwQKNHN61HyK3jx/fa8Os5ux9u3Q654YLZrAJ99QGEm/C9nEBPmlHC98RjovLGBnuJOGx6k7fnyrt/Ogy5fNg+tBgi5HEsoXDAwutX7TOWfx4YKHpKW//TvPRQgp69e2Xqa+CvGJJ+a/WlPMPhRCSsfo0OG04mVvlkc8eXiLzV/GPuJCEmcRf9Z6V+xoDyMtU7OZ3XT5BMhI/D/N68LsRn/9dIBH6X7n0WAW3tzeKZK1zENWFKrd7aLlzEdwFzO/1JTQsEDom5TRie0Kd5yic4BGvS1C1BsA2wJhzyiZ2j7RUE9m8tOAkPEIs929FYIfmH8XcCQKHT0TqT0+N+wCiyfNawPlDhZWcObscFZeEmKgvqiUFCoCj6xI1hvyHK0nu7fnZ/sGc6oNT/SrFjubYWjOyoYFL7gMnlYAhyjZhjuAwN1m1/wjwrOx8DbFr2NW8qb3hv+CIzK1zL3LDryKjqNkTxcOp4aJnmSTa73guCEmWc7pnLkLw5O8RgW7RKHrObeeQ0l9lu4HWXwlhdWRxvVMQDimhtTrGASL6sIuaxyhOkrH4HFImP70SaCoK9+euMxnzkPjg9HqPIFj+I0KSMloVxW"

OO_DEFAULT_PROXIES = [
    "38.154.185.97:6370:nhtbnigs:3tdfei3ngchg",
    "84.247.60.125:6095:nhtbnigs:3tdfei3ngchg",
    "31.59.20.176:6754:nhtbnigs:3tdfei3ngchg",
]

# ════════════════════════════════════════════════════════════════════════
#  DJEZZY OFFERS
# ════════════════════════════════════════════════════════════════════════
DJ_OFFERS = {
    "BTL500MBDAY":             {"name": "5GB — 90دج — 24س",    "display": "5GB | 90 دج | 24 ساعة",    "gb": "5",   "price": "90",   "dur": "24 ساعة"},
    "DOVINTSPEEDDAY100MoPRE":  {"name": "300Mo — 30دج — 24س",  "display": "300Mo | 30 دج | 24 ساعة",  "gb": "300Mo","price": "30",  "dur": "24 ساعة"},
    "DOVINTSPEEDDAY250MoPRE":  {"name": "600Mo — 50دج — 24س",  "display": "600Mo | 50 دج | 24 ساعة",  "gb": "600Mo","price": "50",  "dur": "24 ساعة"},
    "DOVINTSPEEDDAY1GoPRE":    {"name": "2Go — 100دج — 24س",   "display": "2Go | 100 دج | 24 ساعة",   "gb": "2",   "price": "100",  "dur": "24 ساعة"},
    "OFFREJEUNE50":            {"name": "1Go — 50دج — 24س",    "display": "1Go | 50 دج | 24 ساعة",    "gb": "1",   "price": "50",   "dur": "24 ساعة"},
    "BTLINTSPEEDDAY2Go":       {"name": "4GB — 70دج — 24س 🏷️","display": "4GB | 70 دج | 24 ساعة",    "gb": "4",   "price": "70",   "dur": "24 ساعة"},
    "BTL4GBDAY":               {"name": "5GB — 190دج — 24س",   "display": "5GB | 190 دج | 24 ساعة",   "gb": "5",   "price": "190",  "dur": "24 ساعة"},
    "BTL1GBDAY":               {"name": "4GB — 140دج — 24س",   "display": "4GB | 140 دج | 24 ساعة",   "gb": "4",   "price": "140",  "dur": "24 ساعة"},
    "DOVINTSPEEDWEEK2GoPRE":   {"name": "4Go — 150دج — 7أيام", "display": "4Go | 150 دج | 7 أيام",   "gb": "4",   "price": "150",  "dur": "7 أيام"},
    "DOVINTSPEEDWEEK3GoPRE":   {"name": "10Go — 300دج — 7أيام","display": "10Go | 300 دج | 7 أيام",  "gb": "10",  "price": "300",  "dur": "7 أيام"},
    "BTLDATA2WEEKS":           {"name": "4GB — 400دج — 15يوم", "display": "4GB | 400 دج | 15 يوم",    "gb": "4",   "price": "400",  "dur": "15 يوم"},
    "1GBFB3DAYInternet":       {"name": "1GB FB — 70دج — 3أيام","display": "1GB Facebook | 70 دج | 3 أيام","gb":"1","price": "70", "dur": "3 أيام"},
    "DOVINTSPEEDMONTH6GoPRE":  {"name": "12Go — 500دج — 30يوم","display": "12Go | 500 دج | 30 يوم",  "gb": "12",  "price": "500",  "dur": "30 يوم"},
    "DOVINTSPEEDMONTH15GoPRE": {"name": "30Go — 1000دج — 30يوم","display": "30Go | 1000 دج | 30 يوم","gb": "30",  "price": "1000", "dur": "30 يوم"},
    "DOVINTSPEEDMONTH30GoPRE": {"name": "60Go — 1500دج — 30يوم","display": "60Go | 1500 دج | 30 يوم","gb": "60",  "price": "1500", "dur": "30 يوم"},
    "2GBMONTH":                {"name": "3GB — 250دج — 30يوم", "display": "3GB | 250 دج | 30 يوم",    "gb": "3",   "price": "250",  "dur": "30 يوم"},
    "BTL500MBHOUR":            {"name": "1GB — 40دج — 1ساعة ⚡","display": "1GB | 40 دج | 1 ساعة",   "gb": "1",   "price": "40",   "dur": "1 ساعة"},
    "ImtiyazSurpriseData2hfbPRE": {"name": "FB غير محدود — 50دج — 4س 📘","display": "FB غير محدود | 50 دج | 4 ساعات","gb": "∞","price": "50","dur": "4 ساعات"},
}

DJ_OFFER_SHORTCUTS = {
    "5": "BTL500MBDAY", "6": "DOVINTSPEEDDAY100MoPRE", "7": "DOVINTSPEEDDAY250MoPRE",
    "8": "DOVINTSPEEDDAY1GoPRE", "9": "OFFREJEUNE50", "10": "BTLINTSPEEDDAY2Go",
    "11": "BTL4GBDAY", "12": "BTL1GBDAY", "13": "DOVINTSPEEDWEEK2GoPRE",
    "14": "DOVINTSPEEDWEEK3GoPRE", "15": "BTLDATA2WEEKS", "16": "1GBFB3DAYInternet",
    "17": "DOVINTSPEEDMONTH6GoPRE", "18": "DOVINTSPEEDMONTH15GoPRE",
    "19": "DOVINTSPEEDMONTH30GoPRE", "20": "2GBMONTH", "21": "BTL500MBHOUR",
    "22": "ImtiyazSurpriseData2hfbPRE",
}

# ════════════════════════════════════════════════════════════════════════
#  OOREDOO OFFERS
# ════════════════════════════════════════════════════════════════════════
OO_OFFERS = {
    1:  {"label": "الهدية اليومية 🎲",     "type": "daily_gift", "price": "0",   "duration": "24 ساعة"},
    2:  {"label": "سناب شات مجاني 👻",     "type": "snapchat",   "price": "0",   "duration": "24 ساعة"},
    5:  {"label": "1Go — 150دج — 30يوم",   "type": "byop", "price": "150",  "duration": "30 يوم",
         "payload": {"bundleCode": "BYOB_1GBMONTHLYBUNDLE", "msisdn": None}},
    6:  {"label": "2Go — 200دج — 30يوم",   "type": "byop", "price": "200",  "duration": "30 يوم",
         "payload": {"bundleCode": "BYOB_2GBMONTHLYBUNDLE", "msisdn": None}},
    7:  {"label": "5Go — 400دج — 30يوم",   "type": "byop", "price": "400",  "duration": "30 يوم",
         "payload": {"bundleCode": "BYOB_5GBMONTHLYBUNDLE", "msisdn": None}},
    8:  {"label": "10Go — 700دج — 30يوم",  "type": "byop", "price": "700",  "duration": "30 يوم",
         "payload": {"bundleCode": "BYOB_10GBMONTHLYBUNDLE", "msisdn": None}},
    9:  {"label": "20Go — 1200دج — 30يوم", "type": "byop", "price": "1200", "duration": "30 يوم",
         "payload": {"bundleCode": "BYOB_20GBMONTHLYBUNDLE", "msisdn": None}},
    10: {"label": "500Mo — 80دج — 7أيام",  "type": "bundle", "price": "80",  "duration": "7 أيام",
         "endpoint": "/bundle/purchase/weekly", "payload": {"bundleCode": "WEEKLY_500MB"}},
    11: {"label": "1Go — 120دج — 7أيام",   "type": "bundle", "price": "120", "duration": "7 أيام",
         "endpoint": "/bundle/purchase/weekly", "payload": {"bundleCode": "WEEKLY_1GB"}},
    12: {"label": "2Go — 200دج — 7أيام",   "type": "bundle", "price": "200", "duration": "7 أيام",
         "endpoint": "/bundle/purchase/weekly", "payload": {"bundleCode": "WEEKLY_2GB"}},
    13: {"label": "200Mo — 50دج — يومي",   "type": "bundle", "price": "50",  "duration": "24 ساعة",
         "endpoint": "/bundle/purchase/daily", "payload": {"bundleCode": "DAILY_200MB"}},
    14: {"label": "500Mo — 80دج — يومي",   "type": "bundle", "price": "80",  "duration": "24 ساعة",
         "endpoint": "/bundle/purchase/daily", "payload": {"bundleCode": "DAILY_500MB"}},
    15: {"label": "1Go — 120دج — يومي",    "type": "bundle", "price": "120", "duration": "24 ساعة",
         "endpoint": "/bundle/purchase/daily", "payload": {"bundleCode": "DAILY_1GB"}},
    16: {"label": "معلوماتي 📊",           "type": "my_info"},
    17: {"label": "رصيدي وباقاتي 💳",      "type": "my_info"},
    19: {"label": "تجديد التوكن 🔄",       "type": "refresh"},
}

# ════════════════════════════════════════════════════════════════════════
#  LOGGING
# ════════════════════════════════════════════════════════════════════════
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("tasjil")

def dlog(msg: str):
    try:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(DJEZZY_LOG, "a") as f:
            f.write(f"{ts} {msg}\n")
    except Exception:
        pass

def oolog(msg: str):
    try:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(OO_LOG, "a") as f:
            f.write(f"{ts} {msg}\n")
    except Exception:
        pass

# ════════════════════════════════════════════════════════════════════════
#  SQLITE — Dedup + Locks
# ════════════════════════════════════════════════════════════════════════
_db_conn: Optional[sqlite3.Connection] = None

def get_db() -> sqlite3.Connection:
    global _db_conn
    if _db_conn:
        return _db_conn
    _db_conn = sqlite3.connect(str(DB_FILE), check_same_thread=False)
    _db_conn.execute("PRAGMA journal_mode=WAL")
    _db_conn.execute("PRAGMA synchronous=NORMAL")
    _db_conn.execute("PRAGMA cache_size=-8000")
    _db_conn.execute("CREATE TABLE IF NOT EXISTS processed_events (event_id TEXT PRIMARY KEY, created_at INTEGER NOT NULL)")
    _db_conn.execute("CREATE TABLE IF NOT EXISTS user_locks (uid TEXT PRIMARY KEY, locked_at INTEGER NOT NULL)")
    _db_conn.execute("CREATE INDEX IF NOT EXISTS idx_ev_ts ON processed_events(created_at)")
    _db_conn.commit()
    if random.randint(1, 50) == 1:
        now = int(time.time())
        _db_conn.execute("DELETE FROM processed_events WHERE created_at < ?", (now - 3600,))
        _db_conn.execute("DELETE FROM user_locks WHERE locked_at < ?", (now - 600,))
        _db_conn.commit()
    return _db_conn

def try_mark_event(event_id: str) -> bool:
    try:
        db = get_db()
        db.execute("INSERT OR IGNORE INTO processed_events VALUES (?,?)", (event_id, int(time.time())))
        db.commit()
        return db.total_changes > 0
    except Exception:
        return True

def try_lock_user(uid: str) -> bool:
    try:
        db = get_db()
        db.execute("INSERT OR IGNORE INTO user_locks VALUES (?,?)", (str(uid), int(time.time())))
        db.commit()
        return db.total_changes > 0
    except Exception:
        return True

def unlock_user(uid: str):
    try:
        db = get_db()
        db.execute("DELETE FROM user_locks WHERE uid=?", (str(uid),))
        db.commit()
    except Exception:
        pass

# ════════════════════════════════════════════════════════════════════════
#  JSON HELPERS
# ════════════════════════════════════════════════════════════════════════
def _read_json(path: Path, default=None):
    try:
        if path.exists():
            return json.loads(path.read_text("utf-8"))
    except Exception:
        pass
    return default if default is not None else {}

def _write_json(path: Path, data):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
    tmp.replace(path)

# ════════════════════════════════════════════════════════════════════════
#  SESSION / USER — multi-number support
# ════════════════════════════════════════════════════════════════════════
def get_session(uid: str) -> dict:
    return _read_json(SESSIONS_DIR / f"{uid}.json", {})

def set_session(uid: str, data: dict):
    _write_json(SESSIONS_DIR / f"{uid}.json", data)

def clear_session(uid: str):
    p = SESSIONS_DIR / f"{uid}.json"
    if p.exists():
        p.unlink()

def get_user(uid: str) -> Optional[dict]:
    d = _read_json(USERS_DIR / f"{uid}.json", None)
    return d

def save_user(uid: str, data: dict):
    _write_json(USERS_DIR / f"{uid}.json", data)

def get_phone_map() -> dict:
    return _read_json(BASE_DIR / "phone_map.json", {})

def save_phone_owner(msisdn: str, uid: str):
    m = get_phone_map()
    m[msisdn] = uid
    _write_json(BASE_DIR / "phone_map.json", m)

def get_phone_owner(msisdn: str) -> Optional[str]:
    return get_phone_map().get(msisdn)

# ─── Multi-number: الأرقام المحفوظة لمستخدم ───
def get_user_numbers(uid: str) -> list:
    """يُعيد قائمة الأرقام المحفوظة للمستخدم مع بياناتها"""
    user = get_user(uid)
    if not user:
        return []
    return user.get("numbers", [])

def add_user_number(uid: str, msisdn: str, operator: str, tokens: dict):
    """يضيف أو يحدّث رقم في قائمة المستخدم"""
    user = get_user(uid) or {}
    numbers = user.get("numbers", [])
    # تحديث إذا موجود
    for n in numbers:
        if n["msisdn"] == msisdn:
            n.update(tokens)
            n["operator"] = operator
            n["updated_at"] = int(time.time())
            save_user(uid, user)
            return
    # إضافة جديد
    entry = {"msisdn": msisdn, "operator": operator, "added_at": int(time.time()), **tokens}
    numbers.append(entry)
    user["numbers"] = numbers
    # الرقم النشط
    user["active_msisdn"] = msisdn
    user["active_operator"] = operator
    save_user(uid, user)
    save_phone_owner(msisdn, uid)

def get_active_number(uid: str) -> Optional[dict]:
    """يُعيد بيانات الرقم النشط حالياً"""
    user = get_user(uid)
    if not user:
        return None
    active_msisdn = user.get("active_msisdn")
    if not active_msisdn:
        return None
    for n in user.get("numbers", []):
        if n["msisdn"] == active_msisdn:
            return n
    return None

def switch_active_number(uid: str, msisdn: str) -> bool:
    user = get_user(uid)
    if not user:
        return False
    for n in user.get("numbers", []):
        if n["msisdn"] == msisdn:
            user["active_msisdn"] = msisdn
            user["active_operator"] = n.get("operator", "djezzy")
            save_user(uid, user)
            return True
    return False

def update_number_tokens(uid: str, msisdn: str, tokens: dict):
    user = get_user(uid)
    if not user:
        return
    for n in user.get("numbers", []):
        if n["msisdn"] == msisdn:
            n.update(tokens)
            n["updated_at"] = int(time.time())
            save_user(uid, user)
            return

# ════════════════════════════════════════════════════════════════════════
#  RATE LIMIT
# ════════════════════════════════════════════════════════════════════════
def get_rate_timestamps(uid: str) -> list:
    d = _read_json(RATE_DIR / f"{uid}.json", [])
    return d if isinstance(d, list) else []

def record_rate_event(uid: str):
    lst = get_rate_timestamps(uid)
    lst.append(int(time.time()))
    if len(lst) > 2:
        lst = lst[-2:]
    _write_json(RATE_DIR / f"{uid}.json", lst)

def check_rate_limit(uid: str) -> Optional[int]:
    lst = get_rate_timestamps(uid)
    if len(lst) < 2:
        return None
    elapsed = int(time.time()) - lst[0]
    if elapsed < RATE_LIMIT_SECONDS:
        return RATE_LIMIT_SECONDS - elapsed
    return None

def fmt_remaining(secs: int) -> str:
    m = (secs + 59) // 60
    if m <= 1:
        return "أقل من دقيقة"
    return f"{m} دقيقة"

# ════════════════════════════════════════════════════════════════════════
#  USERS MAP / BROADCAST
# ════════════════════════════════════════════════════════════════════════
def mark_user_seen(uid: str):
    m = _read_json(USERS_FILE, {})
    if uid not in m:
        m[uid] = {"first_seen": int(time.time()), "last_active": int(time.time())}
    else:
        m[uid]["last_active"] = int(time.time())
    _write_json(USERS_FILE, m)

def get_all_users() -> list:
    return list(_read_json(USERS_FILE, {}).keys())

def get_active_users(days=7) -> list:
    m = _read_json(USERS_FILE, {})
    since = int(time.time()) - days * 86400
    return [uid for uid, d in m.items() if (d.get("last_active", 0) if isinstance(d, dict) else 0) >= since]

def get_user_stats() -> dict:
    m = _read_json(USERS_FILE, {})
    total = len(m)
    now = int(time.time())
    a7 = sum(1 for d in m.values() if now - (d.get("last_active", 0) if isinstance(d, dict) else 0) <= 7*86400)
    a30 = sum(1 for d in m.values() if now - (d.get("last_active", 0) if isinstance(d, dict) else 0) <= 30*86400)
    return {"total": total, "active_7d": a7, "active_30d": a30}

def was_broadcast_sent(bc_id: str, uid: str) -> bool:
    log = _read_json(BROADCAST_LOG, {})
    return uid in log.get(bc_id, [])

def mark_broadcast_sent(bc_id: str, uid: str):
    log = _read_json(BROADCAST_LOG, {})
    if bc_id not in log:
        log[bc_id] = []
    if uid not in log[bc_id]:
        log[bc_id].append(uid)
    _write_json(BROADCAST_LOG, log)

# ════════════════════════════════════════════════════════════════════════
#  ADMIN MANAGEMENT
# ════════════════════════════════════════════════════════════════════════
def get_admins() -> dict:
    return _read_json(ADMINS_FILE, {})

def add_admin(aid: str, info: dict):
    a = get_admins()
    a[str(aid)] = info
    _write_json(ADMINS_FILE, a)

def remove_admin(aid: str):
    a = get_admins()
    a.pop(str(aid), None)
    _write_json(ADMINS_FILE, a)

def is_admin(uid: int) -> bool:
    return uid in ADMIN_IDS or str(uid) in get_admins()

# ════════════════════════════════════════════════════════════════════════
#  OPERATOR DISABLE TOGGLE
# ════════════════════════════════════════════════════════════════════════
def is_djezzy_disabled() -> bool:
    d = _read_json(DJ_DISABLED_FILE, {"disabled": False})
    return d.get("disabled", False)

def set_djezzy_disabled(v: bool):
    _write_json(DJ_DISABLED_FILE, {"disabled": v, "msg": d.get("msg", "") if (d := _read_json(DJ_DISABLED_FILE, {})) else ""})

def get_djezzy_disabled_msg() -> str:
    return _read_json(DJ_DISABLED_FILE, {}).get("msg", "🔧 خدمة جازي في صيانة، يُرجى المحاولة لاحقاً.")

def is_ooredoo_disabled() -> bool:
    d = _read_json(OO_DISABLED_FILE, {"disabled": False})
    return d.get("disabled", False)

def set_ooredoo_disabled(v: bool):
    _write_json(OO_DISABLED_FILE, {"disabled": v, "msg": d.get("msg", "") if (d := _read_json(OO_DISABLED_FILE, {})) else ""})

def get_ooredoo_disabled_msg() -> str:
    return _read_json(OO_DISABLED_FILE, {}).get("msg", "🔧 خدمة أوريدو في صيانة، يُرجى المحاولة لاحقاً.")

# ════════════════════════════════════════════════════════════════════════
#  PROXY MANAGEMENT — منفصل لكل شبكة
# ════════════════════════════════════════════════════════════════════════
def dj_proxy_enabled() -> bool:
    return _read_json(DJ_PROXY_EN_FILE, {"enabled": True}).get("enabled", True)

def set_dj_proxy_enabled(v: bool):
    _write_json(DJ_PROXY_EN_FILE, {"enabled": v})

def oo_proxy_enabled() -> bool:
    return _read_json(OO_PROXY_EN_FILE, {"enabled": True}).get("enabled", True)

def set_oo_proxy_enabled(v: bool):
    _write_json(OO_PROXY_EN_FILE, {"enabled": v})

def load_dj_proxies() -> list:
    d = _read_json(DJ_PROXIES_FILE, [])
    return d if d else DJ_DEFAULT_PROXIES[:]

def save_dj_proxies(proxies: list):
    _write_json(DJ_PROXIES_FILE, proxies)

def load_oo_proxies() -> list:
    d = _read_json(OO_PROXIES_FILE, [])
    return d if d else OO_DEFAULT_PROXIES[:]

def save_oo_proxies(proxies: list):
    _write_json(OO_PROXIES_FILE, proxies)

def parse_proxy(proxy_str: str) -> dict:
    """يحلل صيغ متعددة: http://host:port:user:pass أو host:port:user:pass"""
    raw = re.sub(r'^https?://', '', proxy_str)
    p = raw.split(":", 3)
    if len(p) == 4:
        return {"host": f"{p[0]}:{p[1]}", "user": p[2], "password": p[3]}
    return {"host": raw, "user": "", "password": ""}

def proxy_to_aiohttp(p_str: str) -> tuple:
    """(proxy_url, proxy_auth)"""
    pp = parse_proxy(p_str)
    url = f"http://{pp['host']}"
    auth = aiohttp.BasicAuth(pp["user"], pp["password"]) if pp["user"] else None
    return url, auth

async def refresh_dj_proxies() -> list:
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8)) as s:
            async with s.get(DJ_PROXY_API_URL, ssl=False) as r:
                lst = await r.json(content_type=None)
                if isinstance(lst, list) and lst:
                    save_dj_proxies(lst)
                    return lst
    except Exception:
        pass
    return load_dj_proxies()

# ════════════════════════════════════════════════════════════════════════
#  MATCH GIFT CONFIG
# ════════════════════════════════════════════════════════════════════════
def get_match_gift_cfg() -> dict:
    defaults = {"enabled": False, "qr_code": "https://www.djezzy.dz/scanwin-wd26?1",
                "gift_label": "12Go", "start_hour": 1, "end_hour": 5}
    d = _read_json(MATCH_GIFT_F, {})
    return {**defaults, **d}

def save_match_gift_cfg(cfg: dict):
    _write_json(MATCH_GIFT_F, cfg)

# ════════════════════════════════════════════════════════════════════════
#  BAN
# ════════════════════════════════════════════════════════════════════════
def is_banned(uid: str) -> bool:
    return str(uid) in _read_json(BAN_FILE, {})

# ════════════════════════════════════════════════════════════════════════
#  OOREDOO DEVICE IDENTITY
# ════════════════════════════════════════════════════════════════════════
def oo_now_ms() -> str:
    return str(int(time.time() * 1000))

def oo_new_instance_id() -> str:
    u = str(uuid.uuid1())
    return u + oo_now_ms()

def oo_new_plat_sig(instance_id: str) -> str:
    payload = json.dumps({"platform": "android", "is-physical-device": True, "device-id": instance_id},
                         separators=(',', ':'))
    return base64.b64encode(payload.encode()).decode()

def oo_new_corr_id() -> str:
    return secrets.token_hex(8) + oo_now_ms()

def oo_new_fingerprint() -> str:
    return secrets.token_hex(32)

def oo_extract_jwt_device_id(access_token: str) -> Optional[str]:
    try:
        parts = access_token.split(".")
        if len(parts) < 2:
            return None
        pad = 4 - len(parts[1]) % 4
        payload = base64.urlsafe_b64decode(parts[1] + "=" * (pad % 4))
        data = json.loads(payload)
        return data.get("device-id")
    except Exception:
        return None

def oo_make_plat_sig_from_jwt(access_token: str) -> str:
    did = oo_extract_jwt_device_id(access_token)
    if not did:
        return oo_new_plat_sig(oo_new_instance_id())
    payload = json.dumps({"platform": "android", "is-physical-device": True, "device-id": did},
                         separators=(',', ':'))
    return base64.b64encode(payload.encode()).decode()

def oo_base_headers(msisdn: str, fp: str, corr_id: str, ts: str, device: dict) -> dict:
    return {
        "User-Agent": "Dart/3.11 (dart:io)",
        "Accept-Encoding": "gzip",
        "x-msisdn": msisdn,
        "x-device-fingerprint": fp,
        "x-platform-origin": OO_PLATFORM_ORIGIN,
        "x-correlation-id": corr_id,
        "platform": OO_PLATFORM,
        "x-version": OO_X_VERSION,
        "x-signature": OO_X_SIG,
        "x-platform-data-signature": device.get("plat_sig", ""),
        "x-timestamp": ts,
        "x-instance-id": device.get("instance_id", ""),
    }

def oo_authed_headers(msisdn: str, token: str, tok_hdrs: dict) -> dict:
    ts     = tok_hdrs.get("tok_timestamp", oo_now_ms())
    iid    = tok_hdrs.get("tok_instance_id", oo_new_instance_id())
    psig   = tok_hdrs.get("tok_plat_sig", oo_new_plat_sig(iid))
    return {
        "User-Agent": "Dart/3.11 (dart:io)",
        "Accept-Encoding": "gzip",
        "x-msisdn": msisdn,
        "x-device-fingerprint": oo_new_fingerprint(),
        "x-platform-origin": OO_PLATFORM_ORIGIN,
        "authorization": f"Bearer {token}",
        "x-correlation-id": oo_new_corr_id(),
        "platform": OO_PLATFORM,
        "x-version": OO_X_VERSION,
        "x-signature": OO_X_SIG,
        "x-platform-data-signature": psig,
        "x-timestamp": ts,
        "x-instance-id": iid,
    }

def oo_web_headers(msisdn: str, token: str, tok_hdrs: dict) -> dict:
    """headers لـ gamification/status و validateUser (web platform)"""
    ts     = tok_hdrs.get("tok_timestamp", oo_now_ms())
    iid    = tok_hdrs.get("tok_instance_id", oo_new_instance_id())
    psig   = tok_hdrs.get("tok_plat_sig", oo_new_plat_sig(iid))
    return {
        "User-Agent": "Dart/3.11 (dart:io)",
        "Accept-Encoding": "gzip",
        "x-msisdn": msisdn,
        "x-device-fingerprint": oo_new_fingerprint(),
        "x-platform-origin": "web",
        "authorization": f"Bearer {token}",
        "x-correlation-id": oo_new_corr_id(),
        "platform": "web",
        "x-version": OO_X_VERSION,
        "x-signature": OO_X_SIG,
        "x-platform-data-signature": psig,
        "x-timestamp": ts,
        "x-instance-id": iid,
        "origin": "https://my.ooredoo.dz",
        "referer": "https://my.ooredoo.dz/",
    }

def oo_get_token_headers(num: dict) -> dict:
    return {
        "tok_fingerprint": num.get("tok_fingerprint", ""),
        "tok_timestamp":   num.get("tok_timestamp", oo_now_ms()),
        "tok_instance_id": num.get("tok_instance_id", oo_new_instance_id()),
        "tok_plat_sig":    num.get("tok_plat_sig", ""),
    }

# ════════════════════════════════════════════════════════════════════════
#  HTTP CORE — retry logic منفصل للشبكتين
# ════════════════════════════════════════════════════════════════════════
async def _do_request(session: aiohttp.ClientSession, method: str, url: str,
                      headers: dict, body: Optional[str], proxy_url: Optional[str],
                      proxy_auth, timeout: float = 12.0) -> Optional[dict]:
    try:
        kwargs = dict(headers=headers, proxy=proxy_url, proxy_auth=proxy_auth,
                      timeout=aiohttp.ClientTimeout(total=timeout), ssl=False)
        if method == "POST":
            kwargs["data"] = body or ""
        async with session.request(method, url, **kwargs) as r:
            raw = await r.read()
            try:
                text = raw.decode("utf-8", errors="replace")
            except Exception:
                text = ""
            if text.strip().startswith(("<html", "<!DOCTYPE")):
                return None
            try:
                j = json.loads(text)
            except Exception:
                j = None
            return {"http_code": r.status, "body": text, "json": j,
                    "resp_headers": dict(r.headers)}
    except Exception:
        return None

async def dj_request(method: str, url: str, headers: dict, body: Optional[str] = None,
                     timeout: float = 10.0, max_retries: int = 4) -> Optional[dict]:
    """طلب جازي مع retry على البروكسيات"""
    proxies = load_dj_proxies() if dj_proxy_enabled() else []
    random.shuffle(proxies)
    candidates = proxies[:8] if proxies else [None]
    if not proxies:
        candidates = [None]

    async with aiohttp.ClientSession() as session:
        # جرّب أول 8 بالتوازي
        tasks = []
        for p in candidates:
            if p:
                pu, pa = proxy_to_aiohttp(p)
            else:
                pu, pa = None, None
            tasks.append(_do_request(session, method, url, headers, body, pu, pa, timeout))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, dict) and r:
                return r

        # الباقي تسلسلياً
        for p in proxies[8:]:
            pu, pa = proxy_to_aiohttp(p)
            r = await _do_request(session, method, url, headers, body, pu, pa, timeout)
            if r:
                return r

        # مباشر إذا فشل الكل
        if proxies:
            r = await _do_request(session, method, url, headers, body, None, None, timeout)
            if r:
                return r
    return None

async def oo_request(method: str, url: str, headers: dict, body: Optional[str] = None,
                     timeout: float = 12.0, preferred_proxy: Optional[str] = None) -> Optional[dict]:
    """طلب أوريدو — يُبدأ بـ preferred_proxy ثم يُجرّب الباقي"""
    proxies = load_oo_proxies() if oo_proxy_enabled() else []
    random.shuffle(proxies)

    # preferred_proxy أولاً
    if preferred_proxy and preferred_proxy in proxies:
        proxies = [preferred_proxy] + [p for p in proxies if p != preferred_proxy]
    elif not proxies:
        proxies = [None]

    async with aiohttp.ClientSession() as session:
        for p in proxies:
            if p:
                pu, pa = proxy_to_aiohttp(p)
            else:
                pu, pa = None, None
            r = await _do_request(session, method, url, headers, body, pu, pa, timeout)
            if r:
                # فحص IP blocked
                if r.get("http_code") in (403, 407):
                    continue
                return r
        return None

# ════════════════════════════════════════════════════════════════════════
#  TELEGRAM HELPERS
# ════════════════════════════════════════════════════════════════════════
application: Application = None  # global ref

async def safe_edit(query, text: str, markup=None, parse_mode=ParseMode.HTML):
    """تعديل رسالة مع حذف آمن إذا فشل"""
    try:
        await query.edit_message_text(text, reply_markup=markup, parse_mode=parse_mode)
    except TgBadRequest:
        pass
    except Exception:
        pass

async def safe_delete(bot, chat_id, msg_id):
    try:
        await bot.delete_message(chat_id, msg_id)
    except Exception:
        pass

async def notify_admins(text: str):
    all_ids = set(ADMIN_IDS) | {int(k) for k in get_admins()}
    for aid in all_ids:
        try:
            await application.bot.send_message(aid, f"🔔 <b>إشعار إداري</b>\n\n{text}", parse_mode=ParseMode.HTML)
        except Exception:
            pass

def mask_msisdn(msisdn: str) -> str:
    if len(msisdn) >= 6:
        return msisdn[:4] + "xxxx" + msisdn[-2:]
    return msisdn

def fmt_time_remaining(secs: int) -> str:
    if secs <= 0:
        return "0 ثانية"
    d_ = secs // 86400
    h_ = (secs % 86400) // 3600
    m_ = (secs % 3600) // 60
    s_ = secs % 60
    parts = []
    if d_ > 0: parts.append(f"{d_} يوم")
    if h_ > 0: parts.append(f"{h_} ساعة")
    if m_ > 0: parts.append(f"{m_} دقيقة")
    if s_ > 0 and d_ == 0 and h_ == 0: parts.append(f"{s_} ثانية")
    return " و".join(parts) if parts else "0 ثانية"

# ════════════════════════════════════════════════════════════════════════
#  KEYBOARDS — احترافية
# ════════════════════════════════════════════════════════════════════════
def main_menu_kb(uid: str, operator: str = None, msisdn: str = None) -> InlineKeyboardMarkup:
    """القائمة الرئيسية — تعرض الرقم النشط وخيارات الشبكة"""
    num = get_active_number(uid)
    op = (num or {}).get("operator", operator or "djezzy")
    ms = (num or {}).get("msisdn", msisdn or "")
    masked = mask_msisdn(ms) if ms else "—"

    if op == "djezzy":
        rows = [
            [InlineKeyboardButton("📶 تفعيل 2G — الهدية الأسبوعية", callback_data="dj_2g")],
            [InlineKeyboardButton("🏷️ عرض 4GB بـ 70دج", callback_data="dj_70dz")],
            [InlineKeyboardButton("📨 إرسال دعوة — جيقا مجاناً", callback_data="dj_invite")],
            [InlineKeyboardButton("📦 عروض جازي", callback_data="dj_more")],
        ]
        cfg = get_match_gift_cfg()
        if cfg["enabled"]:
            rows.append([InlineKeyboardButton("🇩🇿 هدية المباراة", callback_data="dj_match")])
        rows.append([InlineKeyboardButton("📱 تبديل الرقم / إضافة رقم", callback_data="switch_number")])
        header = (f"📱 <b>الرقم النشط:</b> <code>{masked}</code> — 🟢 <b>جازي</b>\n"
                  "━━━━━━━━━━━━━━━━━━━━\n"
                  "اختر الخدمة المطلوبة:")
    else:
        rows = [
            [InlineKeyboardButton("🎲 الهدية اليومية — ألعاب أوريدو", callback_data="oo_daily")],
            [InlineKeyboardButton("👻 سناب شات مجاني — يومي", callback_data="oo_snap")],
            [InlineKeyboardButton("📦 عروض أوريدو", callback_data="oo_offers")],
            [InlineKeyboardButton("📊 معلوماتي — رصيد وباقات", callback_data="oo_info")],
            [InlineKeyboardButton("📱 تبديل الرقم / إضافة رقم", callback_data="switch_number")],
        ]
        header = (f"📱 <b>الرقم النشط:</b> <code>{masked}</code> — 🟡 <b>أوريدو</b>\n"
                  "━━━━━━━━━━━━━━━━━━━━\n"
                  "اختر الخدمة المطلوبة:")

    return header, InlineKeyboardMarkup(rows)

def numbers_switch_kb(uid: str) -> InlineKeyboardMarkup:
    """لوحة تبديل الأرقام"""
    nums = get_user_numbers(uid)
    active = (get_active_number(uid) or {}).get("msisdn", "")
    rows = []
    for n in nums:
        ms = n["msisdn"]
        op = n.get("operator", "djezzy")
        icon = "✅" if ms == active else ("🟢" if op == "djezzy" else "🟡")
        op_label = "جازي" if op == "djezzy" else "أوريدو"
        rows.append([InlineKeyboardButton(f"{icon} {mask_msisdn(ms)} — {op_label}",
                                          callback_data=f"use_number:{ms}")])
    rows.append([InlineKeyboardButton("➕ إضافة رقم جديد", callback_data="add_number")])
    rows.append([InlineKeyboardButton("🔙 رجوع", callback_data="back_main")])
    return InlineKeyboardMarkup(rows)

def dj_offers_kb(remaining_info: str = "") -> InlineKeyboardMarkup:
    """عروض جازي المنظّمة"""
    rows = []
    # يومية
    rows.append([InlineKeyboardButton("━━ 📅 يومية ━━", callback_data="noop")])
    rows.append([
        InlineKeyboardButton("300Mo — 30دج", callback_data="dj_offer:DOVINTSPEEDDAY100MoPRE"),
        InlineKeyboardButton("600Mo — 50دج", callback_data="dj_offer:DOVINTSPEEDDAY250MoPRE"),
    ])
    rows.append([
        InlineKeyboardButton("1Go — 50دج", callback_data="dj_offer:OFFREJEUNE50"),
        InlineKeyboardButton("2Go — 100دج", callback_data="dj_offer:DOVINTSPEEDDAY1GoPRE"),
    ])
    rows.append([
        InlineKeyboardButton("🏷️ 4GB — 70دج", callback_data="dj_offer:BTLINTSPEEDDAY2Go"),
        InlineKeyboardButton("4GB — 140دج", callback_data="dj_offer:BTL1GBDAY"),
    ])
    rows.append([
        InlineKeyboardButton("5GB — 90دج 🔥", callback_data="dj_offer:BTL500MBDAY"),
        InlineKeyboardButton("5GB — 190دج", callback_data="dj_offer:BTL4GBDAY"),
    ])
    rows.append([InlineKeyboardButton("⚡ 1GB — 40دج — ساعة", callback_data="dj_offer:BTL500MBHOUR")])
    # أسبوعية
    rows.append([InlineKeyboardButton("━━ 📆 أسبوعية ━━", callback_data="noop")])
    rows.append([
        InlineKeyboardButton("4Go — 150دج — 7أيام", callback_data="dj_offer:DOVINTSPEEDWEEK2GoPRE"),
        InlineKeyboardButton("10Go — 300دج — 7أيام", callback_data="dj_offer:DOVINTSPEEDWEEK3GoPRE"),
    ])
    rows.append([InlineKeyboardButton("4GB — 400دج — 15يوم", callback_data="dj_offer:BTLDATA2WEEKS")])
    # شهرية
    rows.append([InlineKeyboardButton("━━ 🗓️ شهرية ━━", callback_data="noop")])
    rows.append([
        InlineKeyboardButton("3GB — 250دج", callback_data="dj_offer:2GBMONTH"),
        InlineKeyboardButton("12Go — 500دج", callback_data="dj_offer:DOVINTSPEEDMONTH6GoPRE"),
    ])
    rows.append([
        InlineKeyboardButton("30Go — 1000دج", callback_data="dj_offer:DOVINTSPEEDMONTH15GoPRE"),
        InlineKeyboardButton("60Go — 1500دج", callback_data="dj_offer:DOVINTSPEEDMONTH30GoPRE"),
    ])
    # خاصة
    rows.append([
        InlineKeyboardButton("1GB FB — 70دج — 3أيام", callback_data="dj_offer:1GBFB3DAYInternet"),
        InlineKeyboardButton("📘 FB غير محدود — 50دج", callback_data="dj_offer:ImtiyazSurpriseData2hfbPRE"),
    ])
    rows.append([InlineKeyboardButton("🔙 رجوع", callback_data="back_main")])
    return InlineKeyboardMarkup(rows)

def oo_offers_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("━━ 📅 يومية ━━", callback_data="noop")],
        [
            InlineKeyboardButton("200Mo — 50دج", callback_data="oo_offer:13"),
            InlineKeyboardButton("500Mo — 80دج", callback_data="oo_offer:14"),
        ],
        [InlineKeyboardButton("1Go — 120دج", callback_data="oo_offer:15")],
        [InlineKeyboardButton("━━ 📆 أسبوعية ━━", callback_data="noop")],
        [
            InlineKeyboardButton("500Mo — 80دج", callback_data="oo_offer:10"),
            InlineKeyboardButton("1Go — 120دج", callback_data="oo_offer:11"),
        ],
        [InlineKeyboardButton("2Go — 200دج", callback_data="oo_offer:12")],
        [InlineKeyboardButton("━━ 🗓️ شهرية (BYOP) ━━", callback_data="noop")],
        [
            InlineKeyboardButton("1Go — 150دج", callback_data="oo_offer:5"),
            InlineKeyboardButton("2Go — 200دج", callback_data="oo_offer:6"),
        ],
        [
            InlineKeyboardButton("5Go — 400دج", callback_data="oo_offer:7"),
            InlineKeyboardButton("10Go — 700دج", callback_data="oo_offer:8"),
        ],
        [InlineKeyboardButton("20Go — 1200دج", callback_data="oo_offer:9")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(rows)

def admin_main_kb() -> InlineKeyboardMarkup:
    dj_disabled = is_djezzy_disabled()
    oo_disabled = is_ooredoo_disabled()
    dj_proxy_en = dj_proxy_enabled()
    oo_proxy_en = oo_proxy_enabled()
    rows = [
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="adm_stats")],
        [InlineKeyboardButton("📢 إرسال إعلان", callback_data="adm_broadcast")],
        [InlineKeyboardButton("━━ جازي ━━", callback_data="noop")],
        [
            InlineKeyboardButton(f"{'🔴 تعطيل جازي' if not dj_disabled else '🟢 تفعيل جازي'}", callback_data="adm_toggle_dj"),
            InlineKeyboardButton(f"{'🟢 بروكسي جازي' if dj_proxy_en else '🔴 بروكسي جازي'}", callback_data="adm_toggle_dj_proxy"),
        ],
        [
            InlineKeyboardButton("✏️ بروكسيات جازي", callback_data="adm_edit_dj_proxies"),
            InlineKeyboardButton("🔄 تحديث بروكسيات", callback_data="adm_refresh_dj_proxies"),
        ],
        [InlineKeyboardButton("━━ أوريدو ━━", callback_data="noop")],
        [
            InlineKeyboardButton(f"{'🔴 تعطيل أوريدو' if not oo_disabled else '🟢 تفعيل أوريدو'}", callback_data="adm_toggle_oo"),
            InlineKeyboardButton(f"{'🟢 بروكسي أوريدو' if oo_proxy_en else '🔴 بروكسي أوريدو'}", callback_data="adm_toggle_oo_proxy"),
        ],
        [InlineKeyboardButton("✏️ بروكسيات أوريدو", callback_data="adm_edit_oo_proxies")],
        [InlineKeyboardButton("━━ هدية المباراة ━━", callback_data="noop")],
        [
            InlineKeyboardButton("🎁 إعدادات الهدية", callback_data="adm_match_gift"),
        ],
        [InlineKeyboardButton("👤 إدارة الإداريين", callback_data="adm_admins")],
    ]
    return InlineKeyboardMarkup(rows)

# ════════════════════════════════════════════════════════════════════════
#  DJEZZY API
# ════════════════════════════════════════════════════════════════════════
async def dj_send_otp(msisdn: str, client_id: str = None) -> bool:
    cid = client_id or DJ_CLIENT_ID_OLD
    url = "https://apim.djezzy.dz/oauth2/token"
    for proxy in load_dj_proxies():
        pu, pa = proxy_to_aiohttp(proxy)
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "MobileApp/3.0.0",
            "Accept": "application/json",
        }
        body = f"client_id={cid}&grant_type=otp&mobileNumber={msisdn}&scope=djezzyAppV2"
        try:
            async with aiohttp.ClientSession() as s:
                async with s.post(url, data=body, headers=headers,
                                  proxy=pu, proxy_auth=pa,
                                  timeout=aiohttp.ClientTimeout(total=8), ssl=False) as r:
                    if r.status in (200, 201):
                        return True
                    if r.status in (400, 401):
                        return False
        except Exception:
            continue
    return False

async def dj_verify_otp(msisdn: str, otp: str, client_id: str = None,
                        client_secret: str = None) -> Optional[Any]:
    cid = client_id or DJ_CLIENT_ID_OLD
    cs  = client_secret or DJ_CLIENT_SECRET_OLD
    url = "https://apim.djezzy.dz/oauth2/token"
    body = (f"scope=djezzyAppV2&client_secret={cs}&client_id={cid}"
            f"&otp={otp}&mobileNumber={msisdn}&grant_type=mobile")
    headers = {"Content-Type": "application/x-www-form-urlencoded",
               "User-Agent": "MobileApp/3.0.0", "Accept": "application/json"}
    for proxy in load_dj_proxies():
        pu, pa = proxy_to_aiohttp(proxy)
        try:
            async with aiohttp.ClientSession() as s:
                async with s.post(url, data=body, headers=headers,
                                  proxy=pu, proxy_auth=pa,
                                  timeout=aiohttp.ClientTimeout(total=8), ssl=False) as r:
                    j = await r.json(content_type=None)
                    if r.status == 400 and j.get("error") == "invalid_grant":
                        return "wrong_otp"
                    if r.status == 200 and "access_token" in j:
                        return {"access_token": j["access_token"],
                                "refresh_token": j.get("refresh_token", "")}
        except Exception:
            continue
    return False

async def dj_refresh_token(refresh_token: str, client_id: str = None,
                           client_secret: str = None) -> Optional[Any]:
    cid = client_id or DJ_CLIENT_ID_OLD
    cs  = client_secret or DJ_CLIENT_SECRET_OLD
    url = "https://apim.djezzy.dz/oauth2/token"
    body = (f"scope=djezzyAppV2&client_secret={cs}&client_id={cid}"
            f"&grant_type=refresh_token&refresh_token={refresh_token}")
    headers = {"Content-Type": "application/x-www-form-urlencoded",
               "User-Agent": "MobileApp/3.0.0", "Accept": "application/json"}
    for proxy in load_dj_proxies():
        pu, pa = proxy_to_aiohttp(proxy)
        try:
            async with aiohttp.ClientSession() as s:
                async with s.post(url, data=body, headers=headers,
                                  proxy=pu, proxy_auth=pa,
                                  timeout=aiohttp.ClientTimeout(total=8), ssl=False) as r:
                    j = await r.json(content_type=None)
                    if r.status == 400 and j.get("error") == "invalid_grant":
                        return "expired"
                    if r.status == 200 and "access_token" in j:
                        return {"access_token": j["access_token"],
                                "refresh_token": j.get("refresh_token", refresh_token)}
        except Exception:
            continue
    return False

async def dj_fetch_sub_history(msisdn: str, access_token: str) -> Optional[list]:
    url = f"https://apim.djezzy.dz/mobile-api/api/v1/subscribers/subscription-history/{msisdn}"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {access_token}",
        "User-Agent": "MobileApp/3.0.0",
        "Connection": "Keep-Alive",
        "Accept-Language": "fr",
    }
    r = await dj_request("GET", url, headers, timeout=12)
    if not r:
        return None
    j = r.get("json", {})
    if isinstance(j, dict) and j.get("status") == 200:
        return j.get("data", [])
    return None

def dj_remaining_from_history(history: list, package_codes: list) -> Optional[int]:
    """الوقت المتبقي لأحدث اشتراك من قائمة codes"""
    if not history:
        return None
    latest_ts = None
    duration_secs = 86400  # افتراضي يوم
    for item in history:
        if item.get("packageCode", "") in package_codes:
            dt_str = item.get("subscriptionDateTime")
            if dt_str:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                    ts = int(dt.timestamp())
                    if latest_ts is None or ts > latest_ts:
                        latest_ts = ts
                except Exception:
                    pass
    if latest_ts is None:
        return None
    remaining = (latest_ts + duration_secs) - int(time.time())
    return max(0, remaining)

async def dj_activate_offer(msisdn: str, access_token: str, package_code: str) -> dict:
    """
    يُحاول تفعيل العرض — يُعيد dict:
      {"status": "ok"|"insufficient_balance"|"proxy_error"|"server_error", ...}
    فشل بروكسي → يُعيد proxy_error (لا يُعاد بمحاولات — فشل واحد يكفي للعروض)
    """
    url     = f"https://apim.djezzy.dz/mobile-api/api/v1/subscribers/activate-product/{msisdn}"
    payload = json.dumps({"packageCode": package_code})
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "accept-language": "fr",
        "authorization": f"Bearer {access_token}",
        "User-Agent": "MobileApp/3.0.0",
    }
    r = await dj_request("POST", url, headers, payload, timeout=10)
    if r is None:
        return {"status": "proxy_error"}
    code = r.get("http_code", 0)
    j    = r.get("json", {}) or {}
    dlog(f"[DJ_OFFER:{package_code}] http={code} body={r.get('body','')[:200]}")

    if code == 402 or j.get("status") == 402:
        balance = (j.get("data") or {}).get("mainBalance")
        return {"status": "insufficient_balance", "balance": balance}

    inner_msg = j.get("message", "")
    msg_str = (inner_msg.get("en", "") if isinstance(inner_msg, dict) else str(inner_msg))

    if code in (200, 201) or j.get("status") == 200:
        if "successfully" in msg_str.lower() or code == 201 or j.get("status") == 200:
            return {"status": "ok"}

    if code >= 500:
        return {"status": "server_error", "code": code}
    return {"status": "error", "code": code, "msg": msg_str}

async def dj_activate_offer_new(msisdn: str, access_token: str, package_code: str) -> dict:
    """طريقة التفعيل الجديدة (OTP-based) — تُستخدم كـ fallback"""
    url     = f"https://apim.djezzy.dz/mobile-api/api/v1/subscribers/activate-product-new/{msisdn}"
    payload = json.dumps({"packageCode": package_code})
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "accept-language": "fr",
        "authorization": f"Bearer {access_token}",
        "User-Agent": "MobileApp/3.0.0",
    }
    r = await dj_request("POST", url, headers, payload, timeout=10)
    if r is None:
        return {"status": "proxy_error"}
    code = r.get("http_code", 0)
    j    = r.get("json", {}) or {}
    if code in (200, 201) or j.get("status") == 200:
        return {"status": "ok"}
    return {"status": "error", "code": code}

async def dj_activate_2g(msisdn: str, access_token: str) -> dict:
    url     = f"https://apim.djezzy.dz/mobile-api/api/v1/services/walkwin/activate/{msisdn}"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {access_token}",
        "User-Agent": "MobileApp/3.0.0",
    }
    # هذا طلب لا يحتاج رصيد — يُعاد حتى 4 مرات
    for attempt in range(4):
        r = await dj_request("POST", url, headers, None, timeout=10)
        if r is None:
            await asyncio.sleep(1)
            continue
        code = r.get("http_code", 0)
        j    = r.get("json", {}) or {}
        dlog(f"[DJ_2G] attempt={attempt+1} code={code}")
        if code in (200, 201):
            return {"status": "ok"}
        if code == 400:
            msg = j.get("message", "")
            if isinstance(msg, dict):
                msg = msg.get("ar", msg.get("en", ""))
            return {"status": "already_activated", "msg": str(msg)}
        if code >= 500:
            await asyncio.sleep(1)
            continue
        return {"status": "error", "code": code}
    return {"status": "proxy_error"}

async def dj_fetch_mgm_invitations(msisdn: str, access_token: str) -> Optional[list]:
    url     = f"https://apim.djezzy.dz/mobile-api/api/v1/services/mgm/invitations/{msisdn}"
    headers = {"Accept": "application/json", "Authorization": f"Bearer {access_token}",
               "User-Agent": "MobileApp/3.0.0", "accept-language": "ar"}
    # لا يحتاج رصيد — يُعاد 4 مرات
    for _ in range(4):
        r = await dj_request("GET", url, headers, timeout=12)
        if r is None:
            await asyncio.sleep(1)
            continue
        j = r.get("json", {})
        if isinstance(j, dict) and j.get("status") == 200:
            return j.get("data", [])
        return None
    return None

async def dj_send_mgm_invite(sender_msisdn: str, receiver_msisdn: str,
                             access_token: str, refresh_token: str) -> dict:
    url     = f"https://apim.djezzy.dz/mobile-api/api/v1/services/mgm/send-invitation/{sender_msisdn}"
    payload = json.dumps({"msisdnReciever": receiver_msisdn})
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "accept-language": "ar",
        "Authorization": f"Bearer {access_token}",
        "User-Agent": "MobileApp/3.0.0",
    }
    for attempt in range(10):
        r = await dj_request("POST", url, headers, payload, timeout=10)
        if r is None:
            await asyncio.sleep(1)
            continue
        code = r.get("http_code", 0)
        j    = r.get("json", {}) or {}
        fault = j.get("fault")
        if fault and int((fault.get("code") or 0)) == 900901:
            return {"status": "TOKEN_EXPIRED"}
        msg_f = j.get("message", "")
        ar = msg_f.get("ar", "") if isinstance(msg_f, dict) else str(msg_f)
        if code == 201 and "تمت العملية بنجاح" in ar:
            return {"status": "SUCCESS"}
        if code == 400 and "الحد الأقصى" in ar:
            return {"status": "MAX_INVITATIONS"}
        if "تمت دعوة هذا" in ar or "غير متوفرة" in ar:
            return {"status": "ALREADY_INVITED"}
        if "غير موجود" in ar:
            return {"status": "CUSTOMER_NOT_EXIST"}
        if "غير نشط" in ar:
            return {"status": "INVALID_NUMBER"}
        await asyncio.sleep(1)
    return {"status": "ERROR"}

async def dj_activate_mgm_reward(msisdn: str, access_token: str, pkg: str) -> str:
    url     = f"https://apim.djezzy.dz/mobile-api/api/v1/services/mgm/activate-reward/{msisdn}"
    payload = json.dumps({"packageCode": pkg})
    headers = {
        "Content-Type": "application/json", "Accept": "application/json",
        "accept-language": "ar", "Authorization": f"Bearer {access_token}",
        "User-Agent": "MobileApp/3.0.0",
    }
    for attempt in range(5):
        r = await dj_request("POST", url, headers, payload, timeout=15)
        if r is None:
            await asyncio.sleep(0.5)
            continue
        code = r.get("http_code", 0)
        j    = r.get("json", {}) or {}
        if code in (200, 201):
            return "SUCCESS"
        if code == 404:
            msg_en = (j.get("message", {}).get("en", "") if isinstance(j.get("message"), dict)
                      else str(j.get("message", "")))
            if "eligibility" in msg_en.lower():
                return "ALREADY_CLAIMED"
            return "REWARD_NOT_EXIST"
        if code == 400:
            msg_ar = (j.get("message", {}).get("ar", "") if isinstance(j.get("message"), dict)
                      else str(j.get("message", "")))
            if "تعذر" in msg_ar or "لم تمر" in msg_ar:
                return "ALREADY_CLAIMED"
        await asyncio.sleep(0.5)
    return "ERROR"

async def dj_activate_match_gift(msisdn: str, access_token: str, qr_code: str) -> dict:
    url     = f"https://apim.djezzy.dz/mobile-api/api/v1/services/scan/activate-reward/{msisdn}"
    payload = json.dumps({"qrCode": qr_code})
    headers = {
        "Content-Type": "application/json", "Accept": "application/json",
        "Accept-Encoding": "gzip", "Authorization": f"Bearer {access_token}",
        "User-Agent": "MobileApp/3.0.0",
    }
    r = await dj_request("POST", url, headers, payload, timeout=12)
    if r is None:
        return {"status": "proxy_error"}
    code = r.get("http_code", 0)
    if code in (200, 201):
        return {"status": "ok"}
    if code == 400:
        return {"status": "not_eligible"}
    return {"status": "error", "code": code}

# ════════════════════════════════════════════════════════════════════════
#  OOREDOO API
# ════════════════════════════════════════════════════════════════════════
async def oo_send_otp(msisdn: str) -> Optional[dict]:
    """
    خطوات 1-5: checkpoint1 → OTP
    يُعيد {"proxy": p_str} عند النجاح، أو None
    """
    proxies = load_oo_proxies()
    random.shuffle(proxies)
    candidates = proxies if proxies else [None]

    async with aiohttp.ClientSession() as session:
        for p_str in candidates:
            if p_str:
                pu, pa = proxy_to_aiohttp(p_str)
            else:
                pu, pa = None, None

            iid  = oo_new_instance_id()
            psig = oo_new_plat_sig(iid)
            device = {"instance_id": iid, "plat_sig": psig}
            ts = oo_now_ms()
            corr = oo_new_corr_id()

            # ─ Step 4: checkpoint/token ─
            hdrs4 = oo_base_headers(msisdn, oo_new_fingerprint(), corr, ts, device)
            hdrs4.update({
                "content-type": "application/json; charset=utf-8",
                "x-native-integrity-token": OO_INTEGRITY_1,
                "x-path": "/api/auth/realms/myooredoo/protocol/openid-connect/token",
                "x-method": "POST",
            })
            try:
                async with session.post(f"{OO_BFF}/checkpoint/token",
                                        data="{}", headers=hdrs4,
                                        proxy=pu, proxy_auth=pa,
                                        timeout=aiohttp.ClientTimeout(total=12), ssl=False) as r4:
                    nonce1   = r4.headers.get("x-nonce-id", "")
                    chronos1 = r4.headers.get("x-chronos-id", "")
                    if not nonce1 or not chronos1:
                        continue
                    # ─ Step 5: POST OTP ─
                    fp5 = oo_new_fingerprint()
                    hdrs5 = {
                        "User-Agent": "Dart/3.11 (dart:io)",
                        "Accept-Encoding": "gzip",
                        "Content-Type": "application/x-www-form-urlencoded",
                        "x-msisdn": msisdn,
                        "x-device-fingerprint": fp5,
                        "x-nonce-id": nonce1,
                        "x-platform-origin": OO_PLATFORM_ORIGIN,
                        "platform": OO_PLATFORM,
                        "x-version": OO_X_VERSION,
                        "x-signature": OO_X_SIG,
                        "x-chronos-id": chronos1,
                        "x-timestamp": ts,
                        "x-platform-info": psig,
                        "x-force-update": "true",
                        "x-instance-id": iid,
                    }
                    otp_body = (f"client_id={OO_CLIENT_ID}&grant_type=otp"
                                f"&username={msisdn}&otp=")
                    async with session.post(OO_AUTH, data=otp_body, headers=hdrs5,
                                            proxy=pu, proxy_auth=pa,
                                            timeout=aiohttp.ClientTimeout(total=12), ssl=False) as r5:
                        oolog(f"[OTP_SEND] code={r5.status} proxy={p_str or 'direct'}")
                        if r5.status in (200, 201, 204):
                            return {"proxy": p_str, "nonce1": nonce1, "chronos1": chronos1, "device": device}
            except Exception as e:
                oolog(f"[OTP_SEND] exception proxy={p_str}: {e}")
                continue
    return None

async def oo_verify_otp(msisdn: str, otp: str, sticky_proxy: Optional[str] = None) -> Optional[Any]:
    """
    خطوات 6-7: checkpoint2 → token
    يُعيد dict بالتوكن, "wrong_otp", أو None
    """
    proxies = load_oo_proxies()
    random.shuffle(proxies)
    if sticky_proxy:
        proxies = [sticky_proxy] + [p for p in proxies if p != sticky_proxy]
    if not proxies:
        proxies = [None]

    async with aiohttp.ClientSession() as session:
        for p_str in proxies:
            if p_str:
                pu, pa = proxy_to_aiohttp(p_str)
            else:
                pu, pa = None, None

            iid  = oo_new_instance_id()
            psig = oo_new_plat_sig(iid)
            device = {"instance_id": iid, "plat_sig": psig}
            ts = oo_now_ms()
            corr = oo_new_corr_id()

            # ─ Step 6: checkpoint ─
            hdrs6 = oo_base_headers(msisdn, oo_new_fingerprint(), corr, ts, device)
            hdrs6.update({
                "content-type": "application/json; charset=utf-8",
                "x-native-integrity-token": OO_INTEGRITY_2,
                "x-path": "/api/auth/realms/myooredoo/protocol/openid-connect/token",
                "x-method": "POST",
            })
            try:
                async with session.post(f"{OO_BFF}/checkpoint/token",
                                        data="{}", headers=hdrs6,
                                        proxy=pu, proxy_auth=pa,
                                        timeout=aiohttp.ClientTimeout(total=12), ssl=False) as r6:
                    nonce2   = r6.headers.get("x-nonce-id", "")
                    chronos2 = r6.headers.get("x-chronos-id", "")
                    if not nonce2 or not chronos2:
                        continue
                    fp7 = oo_new_fingerprint()
                    hdrs7 = {
                        "User-Agent": "Dart/3.11 (dart:io)",
                        "Accept-Encoding": "gzip",
                        "x-msisdn": msisdn,
                        "x-device-fingerprint": fp7,
                        "x-nonce-id": nonce2,
                        "x-platform-origin": OO_PLATFORM_ORIGIN,
                        "platform": OO_PLATFORM,
                        "x-version": OO_X_VERSION,
                        "x-signature": OO_X_SIG,
                        "x-chronos-id": chronos2,
                        "x-timestamp": ts,
                        "x-platform-info": psig,
                        "x-force-update": "true",
                        "x-instance-id": iid,
                    }
                    body7 = (f"client_id={OO_CLIENT_ID}&grant_type=password"
                             f"&username={msisdn}&otp={otp}")
                    async with session.post(OO_AUTH, data=body7, headers=hdrs7,
                                            proxy=pu, proxy_auth=pa,
                                            timeout=aiohttp.ClientTimeout(total=12), ssl=False) as r7:
                        code7 = r7.status
                        oolog(f"[OTP_VERIFY] code={code7} proxy={p_str or 'direct'}")
                        if code7 in (401, 403):
                            return "wrong_otp"
                        if code7 == 200:
                            j7 = await r7.json(content_type=None)
                            if "access_token" in j7:
                                did = oo_extract_jwt_device_id(j7["access_token"])
                                return {
                                    "access_token":    j7["access_token"],
                                    "refresh_token":   j7.get("refresh_token", ""),
                                    "tok_fingerprint": fp7,
                                    "tok_timestamp":   ts,
                                    "tok_instance_id": did or iid,
                                    "tok_plat_sig":    oo_make_plat_sig_from_jwt(j7["access_token"]),
                                    "tok_correlation": corr,
                                    "tok_proxy":       p_str,
                                }
            except Exception as e:
                oolog(f"[OTP_VERIFY] exception proxy={p_str}: {e}")
                continue
    return None

async def oo_refresh_token(refresh_token: str, msisdn: str,
                           preferred_proxy: Optional[str] = None) -> Optional[dict]:
    ts   = oo_now_ms()
    iid  = oo_new_instance_id()
    psig = oo_new_plat_sig(iid)
    hdrs = {
        "User-Agent": "Dart/3.11 (dart:io)",
        "Accept-Encoding": "gzip",
        "Content-Type": "application/x-www-form-urlencoded",
        "x-msisdn": msisdn,
        "x-platform-origin": "mobile-android",
        "platform": "android",
        "x-version": OO_X_VERSION,
        "x-signature": OO_X_SIG,
        "x-platform-data-signature": psig,
        "x-timestamp": ts,
        "x-instance-id": iid,
    }
    body = (f"client_id={OO_CLIENT_ID}&grant_type=refresh_token"
            f"&refresh_token={refresh_token}")
    proxies = load_oo_proxies()
    random.shuffle(proxies)
    if preferred_proxy:
        proxies = [preferred_proxy] + [p for p in proxies if p != preferred_proxy]
    proxies.append(None)  # direct كآخر محاولة

    async with aiohttp.ClientSession() as session:
        for p_str in proxies:
            if p_str:
                pu, pa = proxy_to_aiohttp(p_str)
            else:
                pu, pa = None, None
            try:
                async with session.post(OO_AUTH, data=body, headers=hdrs,
                                        proxy=pu, proxy_auth=pa,
                                        timeout=aiohttp.ClientTimeout(total=12), ssl=False) as r:
                    code = r.status
                    j    = await r.json(content_type=None)
                    oolog(f"[OO_REFRESH] code={code} proxy={p_str or 'direct'}")
                    if code == 400 and j.get("error") == "invalid_session":
                        return "expired"
                    if code == 200 and "access_token" in j:
                        did = oo_extract_jwt_device_id(j["access_token"])
                        return {
                            "access_token":    j["access_token"],
                            "refresh_token":   j.get("refresh_token", refresh_token),
                            "tok_timestamp":   ts,
                            "tok_instance_id": did or iid,
                            "tok_plat_sig":    oo_make_plat_sig_from_jwt(j["access_token"]),
                            "tok_proxy":       p_str,
                        }
            except Exception:
                continue
    return None

async def oo_gamification_status(msisdn: str, token: str, tok_hdrs: dict) -> Optional[dict]:
    hdrs = oo_web_headers(msisdn, token, tok_hdrs)
    pref = tok_hdrs.get("tok_proxy")
    r = await oo_request("GET", f"{OO_BFF}/gamification/status", hdrs, preferred_proxy=pref)
    if not r:
        return None
    return r.get("json")

async def oo_gamification_play(msisdn: str, token: str, tok_hdrs: dict) -> Optional[dict]:
    ts   = oo_now_ms()
    corr = oo_new_corr_id()
    iid  = tok_hdrs.get("tok_instance_id", oo_new_instance_id())
    psig = tok_hdrs.get("tok_plat_sig", oo_new_plat_sig(iid))
    device = {"instance_id": iid, "plat_sig": psig}
    pref = tok_hdrs.get("tok_proxy")

    # checkpoint
    hdrs_chk = oo_base_headers(msisdn, oo_new_fingerprint(), corr, ts, device)
    hdrs_chk.update({
        "content-type": "application/json; charset=utf-8",
        "x-native-integrity-token": OO_INTEGRITY_1,
        "x-path": "/api/ooredoo-bff/gamification/play",
        "x-method": "GET",
    })
    r_chk = await oo_request("POST", f"{OO_BFF}/checkpoint/token", hdrs_chk, "{}",
                              preferred_proxy=pref)
    if not r_chk:
        return None
    nonce   = r_chk.get("resp_headers", {}).get("x-nonce-id", "")
    chronos = r_chk.get("resp_headers", {}).get("x-chronos-id", "")
    if not nonce or not chronos:
        return None

    play_ts   = tok_hdrs.get("tok_timestamp", ts)
    hdrs_play = {
        "User-Agent": "Dart/3.11 (dart:io)",
        "Accept-Encoding": "gzip",
        "x-msisdn": msisdn,
        "x-nonce-id": nonce,
        "x-device-fingerprint": oo_new_fingerprint(),
        "x-platform-origin": "web",
        "authorization": f"Bearer {token}",
        "x-correlation-id": oo_new_corr_id(),
        "platform": "web",
        "x-version": OO_X_VERSION,
        "x-signature": OO_X_SIG,
        "x-chronos-id": chronos,
        "x-platform-data-signature": psig,
        "x-timestamp": play_ts,
        "x-instance-id": iid,
        "origin": "https://my.ooredoo.dz",
        "referer": "https://my.ooredoo.dz/",
    }
    r_play = await oo_request("GET", f"{OO_BFF}/gamification/play", hdrs_play,
                               preferred_proxy=pref)
    if not r_play:
        return None
    code = r_play.get("http_code", 0)
    oolog(f"[OO_PLAY] code={code}")
    if code == 500:
        return {"already_played": True}
    if code == 401:
        return {"auth_error": True}
    if code == 200:
        return {**r_play.get("json", {}), "already_played": False}
    return None

async def oo_activate_snapchat(msisdn: str, token: str, tok_hdrs: dict) -> dict:
    hdrs = oo_authed_headers(msisdn, token, tok_hdrs)
    pref = tok_hdrs.get("tok_proxy")
    r = await oo_request("POST", f"{OO_BFF}/snap-chat/apply", hdrs, "",
                          preferred_proxy=pref)
    if not r:
        return {"status": "proxy_error"}
    code = r.get("http_code", 0)
    if code == 200:
        return {"status": "ok"}
    if code == 500:
        return {"status": "already_activated"}
    return {"status": "error", "code": code}

async def oo_activate_bundle(msisdn: str, token: str, tok_hdrs: dict,
                             endpoint: str, payload: dict) -> dict:
    hdrs = {**oo_authed_headers(msisdn, token, tok_hdrs),
            "content-type": "application/json; charset=utf-8"}
    pref = tok_hdrs.get("tok_proxy")
    payload["msisdn"] = msisdn
    r = await oo_request("POST", f"{OO_BFF}{endpoint}", hdrs,
                          json.dumps(payload), preferred_proxy=pref)
    if not r:
        return {"status": "proxy_error"}
    code = r.get("http_code", 0)
    j    = r.get("json", {}) or {}
    if code == 200:
        return {"status": "ok"}
    if code == 409:
        err = j.get("code", "")
        if "CREDIT_LIMIT" in str(err):
            return {"status": "insufficient_balance"}
        return {"status": "already_activated"}
    return {"status": "error", "code": code}

async def oo_get_my_info(msisdn: str, token: str, tok_hdrs: dict) -> dict:
    pref = tok_hdrs.get("tok_proxy")
    hdrs_web = oo_web_headers(msisdn, token, tok_hdrs)
    hdrs_aut = oo_authed_headers(msisdn, token, tok_hdrs)

    # validateUser
    r_v = await oo_request("GET", f"{OO_BFF}/users/validateUser?msisdn={msisdn}",
                            hdrs_web, preferred_proxy=pref)
    plan = contract = "—"
    if r_v and r_v.get("http_code") == 200:
        jv = r_v.get("json", {}) or {}
        plan     = jv.get("planType", "—")
        contract = jv.get("contractType", "—")

    # getActivePackages
    r_p = await oo_request("GET", f"{OO_BFF}/bundle/getActivePackages?msisdn={msisdn}",
                            hdrs_aut, preferred_proxy=pref)
    balance = "—"
    subs = []
    if r_p and r_p.get("http_code") == 200:
        jp = r_p.get("json", {}) or {}
        balance = jp.get("accountBalance", "—")
        for b in jp.get("bundleInstances", []):
            nm = b.get("bundleName", b.get("bundleCode", ""))
            ex = b.get("expirationDate", "")
            if nm: subs.append(f"📦 {nm}" + (f" (ينتهي: {ex})" if ex else ""))
        rem = jp.get("remainigDataAllocation")
        if rem: subs.append(f"📶 الإنترنت المتبقي: {rem}")

    return {"plan": plan, "contract": contract, "balance": balance, "subs": subs}

# ════════════════════════════════════════════════════════════════════════
#  TELEGRAM COMMAND HANDLERS
# ════════════════════════════════════════════════════════════════════════
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = str(update.effective_user.id)
    chat = update.effective_chat.id
    mark_user_seen(uid)

    if is_banned(uid):
        return

    # امسح أي state قديم
    context.user_data.clear()

    num = get_active_number(uid)
    if num:
        header, kb = main_menu_kb(uid)
        await update.message.reply_text(header, reply_markup=kb, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(
            "👋 <b>مرحباً بك في Tasjil BOT!</b>\n\n"
            "🤖 البوت الأكثر احترافاً لتفعيل عروض الإنترنت الجزائرية.\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "📱 <b>للبدء، أرسل رقم هاتفك:</b>\n"
            "🟢 جازي: <code>07XXXXXXXX</code>\n"
            "🟡 أوريدو: <code>05XXXXXXXX</code>\n\n"
            "⚡ <a href='https://t.me/tasjilbott'>قناة تلغرام</a>",
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )

async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    context.user_data.clear()
    num = get_active_number(uid)
    if not num:
        await update.message.reply_text(
            "⚠️ لم تسجّل رقماً بعد.\n📱 أرسل رقم هاتفك لتبدأ.")
        return
    header, kb = main_menu_kb(uid)
    await update.message.reply_text(header, reply_markup=kb, parse_mode=ParseMode.HTML)

async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ تم إلغاء العملية الحالية.")
    uid = str(update.effective_user.id)
    num = get_active_number(uid)
    if num:
        header, kb = main_menu_kb(uid)
        await update.message.reply_text(header, reply_markup=kb, parse_mode=ParseMode.HTML)

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 <b>المساعدة</b>\n\n"
        "• أرسل رقم هاتفك (جازي أو أوريدو) للتسجيل\n"
        "• يمكنك إضافة أكثر من رقم والتبديل بينها\n"
        "• /menu — لعرض القائمة الرئيسية\n"
        "• /cancel — لإلغاء أي عملية جارية\n\n"
        f"⚡ <a href='{TG_CHANNEL}'>قناة التلغرام</a>",
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )

async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid):
        return
    await update.message.reply_text(
        "⚙️ <b>لوحة التحكم الإدارية</b>",
        reply_markup=admin_main_kb(),
        parse_mode=ParseMode.HTML,
    )

# ════════════════════════════════════════════════════════════════════════
#  MESSAGE HANDLER — الرقم + OTP
# ════════════════════════════════════════════════════════════════════════
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = str(update.effective_user.id)
    text = update.message.text.strip()
    chat = update.effective_chat.id

    mark_user_seen(uid)
    if is_banned(uid):
        return

    state = context.user_data.get("state", "")

    # ─── حالة انتظار OTP جازي ───
    if state == "awaiting_dj_otp":
        await handle_dj_otp(update, context, text)
        return

    # ─── حالة انتظار OTP جازي لعرض (fallback) ───
    if state == "awaiting_dj_offer_otp":
        await handle_dj_offer_otp(update, context, text)
        return

    # ─── حالة انتظار OTP أوريدو ───
    if state == "awaiting_oo_otp":
        await handle_oo_otp(update, context, text)
        return

    # ─── حالة انتظار MGM (رقم المدعو) ───
    if state == "awaiting_mgm_phone":
        await handle_mgm_phone(update, context, text)
        return

    # ─── حالة انتظار رقم للتبديل ───
    if state == "awaiting_switch_input":
        phone = text.strip()
        await handle_new_phone(update, context, phone)
        return

    # ─── هل هو رقم هاتف؟ ───
    phone_match = re.match(r'^(05|06|07)\d{8}$', text)
    if phone_match:
        await handle_new_phone(update, context, text)
        return

    # ─── اختصارات رقمية (عروض جازي) ───
    if text in DJ_OFFER_SHORTCUTS and get_active_number(uid):
        num = get_active_number(uid)
        if num and num.get("operator") == "djezzy":
            pkg = DJ_OFFER_SHORTCUTS[text]
            await trigger_dj_offer(update, context, pkg)
            return

    # ─── رسالة إدارية في حالة broadcast ───
    if is_admin(uid) and state == "awaiting_broadcast":
        await handle_admin_broadcast_text(update, context, text)
        return

    if is_admin(uid) and state == "awaiting_dj_proxies":
        await handle_admin_dj_proxies(update, context, text)
        return

    if is_admin(uid) and state == "awaiting_oo_proxies":
        await handle_admin_oo_proxies(update, context, text)
        return

    if is_admin(uid) and state == "awaiting_qr":
        await handle_admin_qr(update, context, text)
        return

    if is_admin(uid) and state == "awaiting_disable_msg":
        await handle_admin_disable_msg(update, context, text)
        return

    # ─── قائمة إذا لم يُفهم ───
    num = get_active_number(uid)
    if num:
        header, kb = main_menu_kb(uid)
        await update.message.reply_text(header, reply_markup=kb, parse_mode=ParseMode.HTML)

# ════════════════════════════════════════════════════════════════════════
#  PHONE ROUTING
# ════════════════════════════════════════════════════════════════════════
async def handle_new_phone(update: Update, context: ContextTypes.DEFAULT_TYPE, phone: str):
    uid = str(update.effective_user.id)

    if phone.startswith("07") or phone.startswith("06"):
        # جازي
        if is_djezzy_disabled():
            await update.message.reply_text(get_djezzy_disabled_msg())
            return
        await start_dj_login(update, context, phone)
    elif phone.startswith("05"):
        # أوريدو
        if is_ooredoo_disabled():
            await update.message.reply_text(get_ooredoo_disabled_msg())
            return
        await start_oo_login(update, context, phone)
    else:
        await update.message.reply_text("⚠️ الرقم غير مدعوم. استخدم 05/06/07.")

# ════════════════════════════════════════════════════════════════════════
#  DJEZZY LOGIN
# ════════════════════════════════════════════════════════════════════════
async def start_dj_login(update: Update, context: ContextTypes.DEFAULT_TYPE, phone: str):
    uid    = str(update.effective_user.id)
    msisdn = "213" + phone[1:]

    # فحص إذا عنده حساب مسجّل
    owner = get_phone_owner(msisdn)
    if owner == uid:
        user = get_user(uid)
        num  = next((n for n in (user or {}).get("numbers", []) if n["msisdn"] == msisdn), None)
        if num and num.get("refresh_token"):
            msg = await update.message.reply_text("🔄 جاري التحقق من حسابك...")
            result = await dj_refresh_token(num["refresh_token"])
            if isinstance(result, dict):
                update_number_tokens(uid, msisdn, result)
                switch_active_number(uid, msisdn)
                await msg.delete()
                await update.message.reply_text(f"✅ تم التعرف على رقمك <code>{phone}</code>!",
                                                parse_mode=ParseMode.HTML)
                header, kb = main_menu_kb(uid)
                await update.message.reply_text(header, reply_markup=kb, parse_mode=ParseMode.HTML)
                return
            elif result == "expired":
                pass  # سنرسل OTP جديد
            else:
                pass

    msg = await update.message.reply_text(f"📲 جاري إرسال رمز التحقق إلى <code>{phone}</code>...",
                                           parse_mode=ParseMode.HTML)
    ok = await dj_send_otp(msisdn)
    await msg.delete()
    if not ok:
        await update.message.reply_text(
            "⚠️ <b>سيرفر جازي غير متاح حالياً.</b>\n\n"
            f"يمكنك المحاولة لاحقاً أو التواصل عبر {TG_CHANNEL}",
            parse_mode=ParseMode.HTML)
        return

    context.user_data["state"]          = "awaiting_dj_otp"
    context.user_data["dj_msisdn"]      = msisdn
    context.user_data["dj_phone"]       = phone
    context.user_data["dj_client"]      = "old"

    await update.message.reply_text(
        f"✅ تم إرسال رمز التحقق إلى <code>{phone}</code>\n\n"
        "🔢 أدخل الرمز المكوّن من 6 أرقام:\n\n"
        "📱 أرسل رقمك مجدداً لاستقبال رمز جديد\n"
        "❌ أو أرسل <code>0</code> للإلغاء",
        parse_mode=ParseMode.HTML
    )

async def handle_dj_otp(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    uid    = str(update.effective_user.id)
    msisdn = context.user_data.get("dj_msisdn", "")
    phone  = context.user_data.get("dj_phone", "")

    if text == "0":
        context.user_data.clear()
        await update.message.reply_text("❌ تم الإلغاء.")
        return

    if re.match(r'^(05|06|07)\d{8}$', text):
        # رقم جديد → إعادة إرسال OTP
        await start_dj_login(update, context, text)
        return

    if not re.match(r'^\d{6}$', text):
        await update.message.reply_text("⚠️ الرمز يجب أن يكون 6 أرقام فقط.")
        return

    msg = await update.message.reply_text("⏳ جاري التحقق من الرمز...")
    result = await dj_verify_otp(msisdn, text)
    await msg.delete()

    if result == "wrong_otp":
        await update.message.reply_text(
            "❌ رمز خاطئ، تأكد من الرمز وأعد المحاولة.\n\n"
            "📱 أو أرسل رقمك مجدداً لاستقبال رمز جديد")
        return
    if not result:
        await update.message.reply_text("❌ حدث خطأ في التحقق، حاول مجدداً.")
        return

    context.user_data.clear()
    add_user_number(uid, msisdn, "djezzy", result)
    save_phone_owner(msisdn, uid)

    await update.message.reply_text(f"✅ <b>تم تسجيل الدخول بنجاح!</b>\n📱 الرقم: <code>{phone}</code>",
                                    parse_mode=ParseMode.HTML)
    # عرض الوقت المتبقي للـ 2G
    history_msg = await update.message.reply_text("🔄 جاري فحص السجل...")
    hist = await dj_fetch_sub_history(msisdn, result["access_token"])
    await history_msg.delete()

    remaining_2g = None
    if hist:
        remaining_2g = dj_remaining_from_history(hist, ["GIFTWALKWIN2GO", "GIFTWALKWIN1GO"])

    header, kb = main_menu_kb(uid)
    info = ""
    if remaining_2g and remaining_2g > 0:
        info = f"\n\n⏳ الوقت المتبقي لتفعيل 2G: <b>{fmt_time_remaining(remaining_2g)}</b>"
    elif remaining_2g == 0:
        info = "\n\n✅ 2G جاهز للتفعيل الآن!"

    await update.message.reply_text(header + info, reply_markup=kb, parse_mode=ParseMode.HTML)

async def handle_dj_offer_otp(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """OTP للعرض الجديد (fallback)"""
    uid        = str(update.effective_user.id)
    msisdn     = context.user_data.get("dj_msisdn", "")
    phone      = context.user_data.get("dj_phone", "")
    pkg        = context.user_data.get("pending_pkg", "")

    if text == "0":
        context.user_data.clear()
        await update.message.reply_text("❌ تم الإلغاء.")
        return

    if not re.match(r'^\d{6}$', text):
        await update.message.reply_text("⚠️ الرمز 6 أرقام.")
        return

    msg = await update.message.reply_text("⏳ جاري التحقق...")
    result = await dj_verify_otp(msisdn, text, DJ_CLIENT_ID_NEW, DJ_CLIENT_SECRET_NEW)
    if result == "wrong_otp":
        await msg.edit_text("❌ رمز خاطئ.")
        return
    if not result:
        await msg.edit_text("❌ خطأ في التحقق.")
        return

    update_number_tokens(uid, msisdn, result)
    await msg.edit_text(f"✅ جاري تفعيل العرض...")
    res = await dj_activate_offer(msisdn, result["access_token"], pkg)
    context.user_data.clear()

    offer_info = DJ_OFFERS.get(pkg, {})
    offer_name = offer_info.get("name", pkg)
    masked     = mask_msisdn(msisdn)

    if res["status"] == "ok":
        record_rate_event(uid)
        await update.message.reply_text(
            f"⭐ <b>تم تفعيل العرض بنجاح!</b>\n\n"
            f"📦 العرض: <b>{offer_name}</b>\n"
            f"📱 الرقم: <code>{masked}</code>\n\n"
            f"⚡ <a href='{TG_CHANNEL}'>قناة التلغرام</a>",
            parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    else:
        await update.message.reply_text("❌ فشل تفعيل العرض بالطريقة الثانية أيضاً.")

    header, kb = main_menu_kb(uid)
    await update.message.reply_text(header, reply_markup=kb, parse_mode=ParseMode.HTML)

# ════════════════════════════════════════════════════════════════════════
#  OOREDOO LOGIN
# ════════════════════════════════════════════════════════════════════════
async def start_oo_login(update: Update, context: ContextTypes.DEFAULT_TYPE, phone: str):
    uid    = str(update.effective_user.id)
    msisdn = "213" + phone[1:]

    owner = get_phone_owner(msisdn)
    if owner == uid:
        user = get_user(uid)
        num  = next((n for n in (user or {}).get("numbers", []) if n["msisdn"] == msisdn), None)
        if num and num.get("refresh_token"):
            msg = await update.message.reply_text("🔄 جاري التحقق من حسابك أوريدو...")
            pref = num.get("tok_proxy")
            result = await oo_refresh_token(num["refresh_token"], msisdn, pref)
            await msg.delete()
            if isinstance(result, dict):
                update_number_tokens(uid, msisdn, result)
                switch_active_number(uid, msisdn)
                await update.message.reply_text(f"✅ تم التعرف على رقمك أوريدو <code>{phone}</code>!",
                                                parse_mode=ParseMode.HTML)
                header, kb = main_menu_kb(uid)
                await update.message.reply_text(header, reply_markup=kb, parse_mode=ParseMode.HTML)
                return

    msg = await update.message.reply_text(f"📲 جاري إرسال رمز التحقق إلى <code>{phone}</code>...",
                                           parse_mode=ParseMode.HTML)
    otp_res = await oo_send_otp(msisdn)
    await msg.delete()
    if not otp_res:
        await update.message.reply_text(
            "⚠️ <b>سيرفر أوريدو غير متاح حالياً.</b>\n\n"
            f"يمكنك المحاولة لاحقاً.",
            parse_mode=ParseMode.HTML)
        return

    context.user_data["state"]      = "awaiting_oo_otp"
    context.user_data["oo_msisdn"]  = msisdn
    context.user_data["oo_phone"]   = phone
    context.user_data["oo_proxy"]   = otp_res.get("proxy")

    await update.message.reply_text(
        f"✅ تم إرسال رمز التحقق إلى <code>{phone}</code>\n\n"
        "🔢 أدخل الرمز المكوّن من 6 أرقام:\n\n"
        "📱 أرسل رقمك مجدداً لاستقبال رمز جديد\n"
        "❌ أو أرسل <code>0</code> للإلغاء",
        parse_mode=ParseMode.HTML
    )

async def handle_oo_otp(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    uid    = str(update.effective_user.id)
    msisdn = context.user_data.get("oo_msisdn", "")
    phone  = context.user_data.get("oo_phone", "")
    sticky = context.user_data.get("oo_proxy")

    if text == "0":
        context.user_data.clear()
        await update.message.reply_text("❌ تم الإلغاء.")
        return

    if re.match(r'^05\d{8}$', text):
        await start_oo_login(update, context, text)
        return

    if not re.match(r'^\d{6}$', text):
        await update.message.reply_text("⚠️ الرمز يجب أن يكون 6 أرقام.")
        return

    msg = await update.message.reply_text("⏳ جاري التحقق...")
    result = await oo_verify_otp(msisdn, text, sticky)
    await msg.delete()

    if result == "wrong_otp":
        await update.message.reply_text("❌ رمز خاطئ، أعد المحاولة.")
        return
    if not result:
        await update.message.reply_text("❌ خطأ في التحقق، حاول مجدداً.")
        return

    context.user_data.clear()
    add_user_number(uid, msisdn, "ooredoo", result)
    save_phone_owner(msisdn, uid)

    await update.message.reply_text(f"✅ <b>تم تسجيل الدخول أوريدو بنجاح!</b>\n📱 الرقم: <code>{phone}</code>",
                                    parse_mode=ParseMode.HTML)

    # فحص الهدية اليومية
    tok_hdrs = oo_get_token_headers(result)
    status_msg = await update.message.reply_text("🔄 جاري فحص الهدية اليومية...")
    gstat = await oo_gamification_status(msisdn, result["access_token"], tok_hdrs)
    await status_msg.delete()

    header, kb = main_menu_kb(uid)
    daily_info = ""
    if gstat:
        played      = gstat.get("played", False)
        last_played = gstat.get("lastPlayedTime")
        if played and last_played:
            try:
                from datetime import datetime
                lp_ts  = int(datetime.fromisoformat(last_played.replace("Z","+00:00")).timestamp())
                rem    = (lp_ts + 86400) - int(time.time())
                if rem > 0:
                    daily_info = f"\n\n⏳ الهدية اليومية: <b>{fmt_time_remaining(rem)}</b> متبقية"
            except Exception:
                pass
        elif not played:
            daily_info = "\n\n🎲 <b>الهدية اليومية جاهزة للتفعيل!</b>"

    await update.message.reply_text(header + daily_info, reply_markup=kb, parse_mode=ParseMode.HTML)

# ════════════════════════════════════════════════════════════════════════
#  DJEZZY ACTIONS
# ════════════════════════════════════════════════════════════════════════
async def trigger_dj_2g(query, context, uid: str):
    num = get_active_number(uid)
    if not num:
        await query.answer("⚠️ لا يوجد رقم مسجّل")
        return
    if is_djezzy_disabled():
        await safe_edit(query, get_djezzy_disabled_msg())
        return

    msisdn = num["msisdn"]
    masked = mask_msisdn(msisdn)

    await safe_edit(query, f"⏳ جاري تفعيل 2G للرقم <code>{masked}</code>...", parse_mode=ParseMode.HTML)

    # فحص السجل أولاً
    hist = await dj_fetch_sub_history(msisdn, num.get("access_token", ""))
    if hist:
        rem = dj_remaining_from_history(hist, ["GIFTWALKWIN2GO", "GIFTWALKWIN1GO"])
        if rem and rem > 0:
            header, kb = main_menu_kb(uid)
            await safe_edit(query,
                f"⏳ <b>الهدية الأسبوعية مفعّلة مسبقاً.</b>\n\n"
                f"🕐 الوقت المتبقي: <b>{fmt_time_remaining(rem)}</b>\n\n"
                + header,
                markup=kb, parse_mode=ParseMode.HTML)
            return

    # تفعيل
    rl = check_rate_limit(uid)
    if rl:
        header, kb = main_menu_kb(uid)
        await safe_edit(query,
            f"⏳ انتظر قبل الطلب التالي.\n🕐 المتبقي: {fmt_remaining(rl)}\n\n" + header,
            markup=kb, parse_mode=ParseMode.HTML)
        return

    result = await dj_activate_2g(msisdn, num.get("access_token", ""))
    header, kb = main_menu_kb(uid)

    if result["status"] == "ok":
        record_rate_event(uid)
        await safe_edit(query,
            f"✅ <b>تم تفعيل 2G بنجاح!</b>\n\n"
            f"📱 الرقم: <code>{masked}</code>\n"
            f"📶 الهدية الأسبوعية المجانية نشطة\n\n"
            f"⚡ <a href='{TG_CHANNEL}'>قناة التلغرام</a>\n\n" + header,
            markup=kb, parse_mode=ParseMode.HTML)
    elif result["status"] == "already_activated":
        await safe_edit(query,
            f"ℹ️ 2G مفعّل مسبقاً هذا الأسبوع.\n\n" + header,
            markup=kb, parse_mode=ParseMode.HTML)
    else:
        await safe_edit(query,
            f"❌ فشل تفعيل 2G (خطأ: {result.get('status')}).\n\n" + header,
            markup=kb, parse_mode=ParseMode.HTML)

async def trigger_dj_offer(update_or_query, context, pkg: str, from_callback=False):
    if from_callback:
        query = update_or_query
        uid   = str(query.from_user.id)
        send  = lambda t, kb=None: safe_edit(query, t, markup=kb, parse_mode=ParseMode.HTML)
    else:
        update = update_or_query
        uid    = str(update.effective_user.id)
        async def send(t, kb=None):
            await update.message.reply_text(t, reply_markup=kb, parse_mode=ParseMode.HTML)

    num = get_active_number(uid)
    if not num:
        await send("⚠️ لا يوجد رقم مسجّل.")
        return
    if is_djezzy_disabled():
        await send(get_djezzy_disabled_msg())
        return

    rl = check_rate_limit(uid)
    if rl:
        header, kb = main_menu_kb(uid)
        await send(f"⏳ انتظر {fmt_remaining(rl)} قبل الطلب التالي.\n\n" + header, kb)
        return

    msisdn     = num["msisdn"]
    masked     = mask_msisdn(msisdn)
    offer_info = DJ_OFFERS.get(pkg, {})
    offer_name = offer_info.get("name", pkg)

    await send(f"⏳ جاري تفعيل <b>{offer_name}</b> للرقم <code>{masked}</code>...")

    # فحص السجل مسبقاً
    hist = await dj_fetch_sub_history(msisdn, num.get("access_token", ""))
    if hist:
        rem = dj_remaining_from_history(hist, [pkg])
        if rem and rem > 0:
            header, kb = main_menu_kb(uid)
            await send(
                f"ℹ️ <b>{offer_name}</b> مفعّل مسبقاً.\n"
                f"⏳ المتبقي: <b>{fmt_time_remaining(rem)}</b>\n\n" + header, kb)
            return

    # طريقة 1
    result = await dj_activate_offer(msisdn, num.get("access_token", ""), pkg)
    header, kb = main_menu_kb(uid)

    if result["status"] == "ok":
        record_rate_event(uid)
        await send(
            f"⭐ <b>تم تفعيل العرض بنجاح!</b>\n\n"
            f"📦 العرض: <b>{offer_name}</b>\n"
            f"📶 {offer_info.get('display', '')}\n"
            f"📱 الرقم: <code>{masked}</code>\n\n"
            f"⚡ <a href='{TG_CHANNEL}'>قناة التلغرام</a>\n\n" + header, kb)
        return

    if result["status"] == "insufficient_balance":
        bal = result.get("balance")
        bal_txt = f"\n💳 رصيدك: {bal} دج" if bal else ""
        await send(f"⚠️ رصيدك غير كافٍ لتفعيل {offer_name}.{bal_txt}\n\n" + header, kb)
        return

    if result["status"] == "proxy_error":
        # بروكسي — لا إعادة لعروض التفعيل
        await send(f"❌ تعذر الاتصال بالسيرفر، حاول مجدداً.\n\n" + header, kb)
        return

    # طريقة 2 (server_error أو error) — عرض زر
    fallback_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 تجربة طريقة أخرى", callback_data=f"dj_offer_fallback:{pkg}")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_main")],
    ])
    await send(
        f"⚠️ تعذر تفعيل <b>{offer_name}</b> بالطريقة الأولى.\n\n"
        "هل تريد تجربة طريقة أخرى؟", fallback_kb)

async def trigger_dj_70dz(query, context, uid: str):
    await trigger_dj_offer(query, context, "BTLINTSPEEDDAY2Go", from_callback=True)

async def handle_mgm_start(query, context, uid: str):
    num = get_active_number(uid)
    if not num:
        await query.answer("⚠️ لا يوجد رقم")
        return
    if is_djezzy_disabled():
        await safe_edit(query, get_djezzy_disabled_msg())
        return

    msisdn = num["msisdn"]
    msg = await safe_edit(query,
        "⏳ جاري فحص الدعوات المعلّقة...")

    # جلب الدعوات
    invites = await dj_fetch_mgm_invitations(msisdn, num.get("access_token", ""))
    pending_count = 0
    if isinstance(invites, list):
        pending_count = sum(1 for i in invites if i.get("status") == "PENDING")

    context.user_data["state"]      = "awaiting_mgm_phone"
    context.user_data["dj_msisdn"]  = msisdn

    await safe_edit(query,
        f"📨 <b>إرسال دعوة جازي</b>\n\n"
        f"📱 الرقم المُرسِل: <code>{mask_msisdn(msisdn)}</code>\n"
        f"📋 الدعوات المعلّقة: <b>{pending_count}</b>\n\n"
        "أرسل رقم الشخص الذي تريد دعوته:\n"
        "<code>07XXXXXXXX</code> أو <code>06XXXXXXXX</code>\n\n"
        "❌ أو أرسل <code>0</code> للإلغاء",
        parse_mode=ParseMode.HTML)

async def handle_mgm_phone(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    uid         = str(update.effective_user.id)
    sender_ms   = context.user_data.get("dj_msisdn", "")
    num         = get_active_number(uid)

    if text == "0":
        context.user_data.clear()
        await update.message.reply_text("❌ تم الإلغاء.")
        header, kb = main_menu_kb(uid)
        await update.message.reply_text(header, reply_markup=kb, parse_mode=ParseMode.HTML)
        return

    if not re.match(r'^(06|07)\d{8}$', text):
        await update.message.reply_text("⚠️ أرسل رقم جازي صحيح (06/07).")
        return

    receiver_ms = "213" + text[1:]
    msg = await update.message.reply_text("⏳ جاري إرسال الدعوة...")

    result = await dj_send_mgm_invite(sender_ms, receiver_ms, num.get("access_token", ""), num.get("refresh_token", ""))
    context.user_data.clear()

    status_map = {
        "SUCCESS":          f"✅ <b>تم إرسال الدعوة بنجاح!</b>\n\n📨 الرقم المدعو: <code>{text}</code>\n⏳ انتظر قبول الدعوة للحصول على جيقا مجانية.",
        "MAX_INVITATIONS":  "⚠️ وصلت للحد الأقصى من الدعوات.",
        "ALREADY_INVITED":  "ℹ️ هذا الرقم تمت دعوته مسبقاً.",
        "CUSTOMER_NOT_EXIST": "❌ الرقم غير موجود في شبكة جازي.",
        "INVALID_NUMBER":   "❌ الرقم غير نشط.",
        "TOKEN_EXPIRED":    "🔄 انتهت الجلسة، أرسل رقمك مجدداً.",
        "ERROR":            "❌ حدث خطأ في إرسال الدعوة.",
    }
    resp = status_map.get(result.get("status", "ERROR"), "❌ خطأ غير متوقع.")
    await msg.edit_text(resp, parse_mode=ParseMode.HTML)

    header, kb = main_menu_kb(uid)
    await update.message.reply_text(header, reply_markup=kb, parse_mode=ParseMode.HTML)

# ════════════════════════════════════════════════════════════════════════
#  OOREDOO ACTIONS
# ════════════════════════════════════════════════════════════════════════
async def trigger_oo_daily_gift(query, context, uid: str):
    num = get_active_number(uid)
    if not num or num.get("operator") != "ooredoo":
        await query.answer("⚠️ يجب اختيار رقم أوريدو")
        return
    if is_ooredoo_disabled():
        await safe_edit(query, get_ooredoo_disabled_msg())
        return

    msisdn   = num["msisdn"]
    masked   = mask_msisdn(msisdn)
    tok_hdrs = oo_get_token_headers(num)
    token    = num.get("access_token", "")

    await safe_edit(query, f"⏳ جاري فحص الهدية اليومية للرقم <code>{masked}</code>...",
                    parse_mode=ParseMode.HTML)

    # فحص الحالة أولاً
    gstat = await oo_gamification_status(msisdn, token, tok_hdrs)
    if gstat:
        played = gstat.get("played", False)
        lp     = gstat.get("lastPlayedTime")
        if played and lp:
            try:
                from datetime import datetime
                lp_ts = int(datetime.fromisoformat(lp.replace("Z", "+00:00")).timestamp())
                rem   = (lp_ts + 86400) - int(time.time())
                if rem > 0:
                    header, kb = main_menu_kb(uid)
                    await safe_edit(query,
                        f"⏳ لقد لعبت الهدية اليومية مسبقاً.\n\n"
                        f"🕐 المتبقي: <b>{fmt_time_remaining(rem)}</b>\n\n" + header,
                        markup=kb, parse_mode=ParseMode.HTML)
                    return
            except Exception:
                pass

    await safe_edit(query, "🎲 جاري تفعيل الهدية اليومية...")
    result = await oo_gamification_play(msisdn, token, tok_hdrs)
    header, kb = main_menu_kb(uid)

    if result is None:
        await safe_edit(query, f"❌ خطأ في الاتصال، حاول مجدداً.\n\n" + header, markup=kb, parse_mode=ParseMode.HTML)
        return

    if result.get("auth_error"):
        # تجديد التوكن
        pref = num.get("tok_proxy")
        refreshed = await oo_refresh_token(num.get("refresh_token", ""), msisdn, pref)
        if isinstance(refreshed, dict):
            update_number_tokens(uid, msisdn, refreshed)
            await safe_edit(query, "🔄 تم تجديد الجلسة. أعد تفعيل الهدية.", parse_mode=ParseMode.HTML)
        else:
            await safe_edit(query, "❌ انتهت الجلسة، أرسل رقمك مجدداً.", parse_mode=ParseMode.HTML)
        return

    if result.get("already_played"):
        gstat2 = await oo_gamification_status(msisdn, token, tok_hdrs)
        lp2    = (gstat2 or {}).get("lastPlayedTime")
        rem_txt = ""
        if lp2:
            try:
                from datetime import datetime
                lp2_ts = int(datetime.fromisoformat(lp2.replace("Z", "+00:00")).timestamp())
                rem2   = (lp2_ts + 86400) - int(time.time())
                rem_txt = f"\n⏰ المتبقي: {fmt_time_remaining(max(0, rem2))}"
            except Exception:
                pass
        await safe_edit(query,
            f"⚠️ لقد لعبت الهدية اليومية مسبقاً.{rem_txt}\n\n" + header,
            markup=kb, parse_mode=ParseMode.HTML)
        return

    gift_name = result.get("giftName", "هدية")
    validity  = result.get("validityHour", "")
    record_rate_event(uid)
    await safe_edit(query,
        f"🎉 <b>تهانيك! ربحت هديتك اليومية!</b>\n\n"
        f"🎁 الهدية: <b>{gift_name}</b>\n"
        + (f"⏳ الصلاحية: {validity} ساعة\n" if validity else "")
        + f"📱 الرقم: <code>{masked}</code>\n\n"
        + f"⚡ <a href='{TG_CHANNEL}'>قناة التلغرام</a>\n\n" + header,
        markup=kb, parse_mode=ParseMode.HTML)

async def trigger_oo_snapchat(query, context, uid: str):
    num = get_active_number(uid)
    if not num or num.get("operator") != "ooredoo":
        await query.answer("⚠️ يجب اختيار رقم أوريدو")
        return
    if is_ooredoo_disabled():
        await safe_edit(query, get_ooredoo_disabled_msg())
        return

    msisdn   = num["msisdn"]
    masked   = mask_msisdn(msisdn)
    tok_hdrs = oo_get_token_headers(num)

    await safe_edit(query, f"⏳ جاري تفعيل سناب شات للرقم <code>{masked}</code>...",
                    parse_mode=ParseMode.HTML)
    result = await oo_activate_snapchat(msisdn, num.get("access_token", ""), tok_hdrs)
    header, kb = main_menu_kb(uid)

    if result["status"] == "ok":
        await safe_edit(query,
            f"✅ <b>تم تفعيل سناب شات!</b>\n\n"
            f"👻 استمتع بسناب شات مجاناً\n"
            f"📱 الرقم: <code>{masked}</code>\n\n" + header,
            markup=kb, parse_mode=ParseMode.HTML)
    elif result["status"] == "already_activated":
        await safe_edit(query,
            f"⚠️ سناب شات مفعّل مسبقاً، لم تمر 24 ساعة.\n\n" + header,
            markup=kb, parse_mode=ParseMode.HTML)
    else:
        await safe_edit(query,
            f"❌ خطأ في تفعيل سناب شات.\n\n" + header,
            markup=kb, parse_mode=ParseMode.HTML)

async def trigger_oo_offer(query, context, uid: str, offer_num: int):
    num = get_active_number(uid)
    if not num or num.get("operator") != "ooredoo":
        await query.answer("⚠️ يجب اختيار رقم أوريدو")
        return
    if is_ooredoo_disabled():
        await safe_edit(query, get_ooredoo_disabled_msg())
        return

    offer = OO_OFFERS.get(offer_num)
    if not offer:
        await query.answer("⚠️ عرض غير موجود")
        return

    if offer["type"] == "daily_gift":
        await trigger_oo_daily_gift(query, context, uid)
        return
    if offer["type"] == "snapchat":
        await trigger_oo_snapchat(query, context, uid)
        return
    if offer["type"] == "my_info":
        await trigger_oo_info(query, context, uid)
        return

    rl = check_rate_limit(uid)
    if rl:
        header, kb = main_menu_kb(uid)
        await safe_edit(query,
            f"⏳ انتظر {fmt_remaining(rl)} قبل الطلب التالي.\n\n" + header,
            markup=kb, parse_mode=ParseMode.HTML)
        return

    msisdn   = num["msisdn"]
    masked   = mask_msisdn(msisdn)
    tok_hdrs = oo_get_token_headers(num)

    await safe_edit(query,
        f"⏳ جاري تفعيل <b>{offer['label']}</b> للرقم <code>{masked}</code>...",
        parse_mode=ParseMode.HTML)

    payload = dict(offer.get("payload", {}))
    payload["msisdn"] = msisdn
    endpoint = offer.get("endpoint", "/bundle/purchase/byop")
    result   = await oo_activate_bundle(msisdn, num.get("access_token", ""), tok_hdrs, endpoint, payload)
    header, kb = main_menu_kb(uid)

    if result["status"] == "ok":
        record_rate_event(uid)
        await safe_edit(query,
            f"✅ <b>تم تفعيل العرض بنجاح!</b>\n\n"
            f"📦 العرض: <b>{offer['label']}</b>\n"
            f"💰 السعر: {offer['price']} دج\n"
            f"⏳ المدة: {offer['duration']}\n"
            f"📱 الرقم: <code>{masked}</code>\n\n" + header,
            markup=kb, parse_mode=ParseMode.HTML)
    elif result["status"] == "insufficient_balance":
        await safe_edit(query,
            f"⚠️ رصيدك غير كافٍ.\n💰 السعر: {offer['price']} دج\n\n" + header,
            markup=kb, parse_mode=ParseMode.HTML)
    elif result["status"] == "already_activated":
        await safe_edit(query, f"⚠️ العرض مفعّل مسبقاً.\n\n" + header, markup=kb, parse_mode=ParseMode.HTML)
    else:
        await safe_edit(query, f"❌ خطأ في تفعيل العرض.\n\n" + header, markup=kb, parse_mode=ParseMode.HTML)

async def trigger_oo_info(query, context, uid: str):
    num = get_active_number(uid)
    if not num or num.get("operator") != "ooredoo":
        await query.answer("⚠️ يجب اختيار رقم أوريدو")
        return

    msisdn   = num["msisdn"]
    masked   = mask_msisdn(msisdn)
    tok_hdrs = oo_get_token_headers(num)

    await safe_edit(query, "⏳ جاري تحميل معلوماتك...")
    info = await oo_get_my_info(msisdn, num.get("access_token", ""), tok_hdrs)
    header, kb = main_menu_kb(uid)

    subs_text = "\n".join(f"• {s}" for s in info["subs"]) if info["subs"] else "📭 لا توجد اشتراكات نشطة"
    await safe_edit(query,
        f"📊 <b>معلوماتي — أوريدو</b>\n\n"
        f"📱 الرقم: <code>{masked}</code>\n"
        f"📦 نوع الشريحة: {info['plan']}\n"
        f"📋 نوع العقد: {info['contract']}\n"
        f"💳 الرصيد: {info['balance']} دج\n\n"
        f"━━━━━━━━━━━━━━\n\n"
        f"{subs_text}\n\n"
        f"━━━━━━━━━━━━━━\n" + header,
        markup=kb, parse_mode=ParseMode.HTML)

# ════════════════════════════════════════════════════════════════════════
#  CALLBACK HANDLER
# ════════════════════════════════════════════════════════════════════════
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid   = str(query.from_user.id)
    data  = query.data

    mark_user_seen(uid)
    if is_banned(uid):
        await query.answer("⛔ محظور")
        return

    await query.answer()

    # ─── noop ───
    if data == "noop":
        return

    # ─── القائمة الرئيسية ───
    if data == "back_main":
        context.user_data.clear()
        header, kb = main_menu_kb(uid)
        await safe_edit(query, header, markup=kb, parse_mode=ParseMode.HTML)
        return

    # ─── تبديل الرقم ───
    if data == "switch_number":
        kb = numbers_switch_kb(uid)
        await safe_edit(query, "📱 <b>أرقامك المحفوظة</b>\n\nاختر رقماً أو أضف رقماً جديداً:",
                        markup=kb, parse_mode=ParseMode.HTML)
        return

    if data == "add_number":
        context.user_data["state"] = "awaiting_switch_input"
        await safe_edit(query,
            "📱 أرسل الرقم الجديد:\n"
            "🟢 جازي: <code>07XXXXXXXX</code>\n"
            "🟡 أوريدو: <code>05XXXXXXXX</code>",
            parse_mode=ParseMode.HTML)
        return

    if data.startswith("use_number:"):
        ms = data.split(":", 1)[1]
        if switch_active_number(uid, ms):
            header, kb = main_menu_kb(uid)
            await safe_edit(query, f"✅ تم التبديل إلى <code>{mask_msisdn(ms)}</code>\n\n" + header,
                            markup=kb, parse_mode=ParseMode.HTML)
        else:
            await safe_edit(query, "⚠️ الرقم غير موجود.")
        return

    # ─── جازي ───
    if data == "dj_2g":
        await trigger_dj_2g(query, context, uid)
        return

    if data == "dj_70dz":
        await trigger_dj_offer(query, context, "BTLINTSPEEDDAY2Go", from_callback=True)
        return

    if data == "dj_invite":
        await handle_mgm_start(query, context, uid)
        return

    if data == "dj_more":
        num = get_active_number(uid)
        ms  = mask_msisdn((num or {}).get("msisdn", ""))
        await safe_edit(query,
            f"📦 <b>عروض جازي</b> — الرقم: <code>{ms}</code>\n\nاختر العرض:",
            markup=dj_offers_kb(), parse_mode=ParseMode.HTML)
        return

    if data == "dj_match":
        cfg = get_match_gift_cfg()
        if not cfg["enabled"]:
            await safe_edit(query, "⏰ هدية المباراة غير متاحة حالياً.")
            return
        num = get_active_number(uid)
        if not num:
            await safe_edit(query, "⚠️ لا يوجد رقم.")
            return
        msisdn = num["msisdn"]
        rl = check_rate_limit(uid)
        if rl:
            await safe_edit(query, f"⏳ انتظر {fmt_remaining(rl)} دقيقة.")
            return
        await safe_edit(query, "⏳ جاري تفعيل هدية المباراة 🇩🇿...")
        result = await dj_activate_match_gift(msisdn, num.get("access_token", ""), cfg["qr_code"])
        header, kb = main_menu_kb(uid)
        if result["status"] == "ok":
            record_rate_event(uid)
            await safe_edit(query,
                f"🎉 <b>تم تفعيل هدية المباراة!</b>\n\n"
                f"🎁 الهدية: {cfg['gift_label']}\n"
                f"📱 الرقم: <code>{mask_msisdn(msisdn)}</code>\n\n" + header,
                markup=kb, parse_mode=ParseMode.HTML)
        elif result["status"] == "not_eligible":
            await safe_edit(query,
                "⚠️ اليوم ليس يوم مباراة أو استفدت مسبقاً.\n\n" + header,
                markup=kb, parse_mode=ParseMode.HTML)
        else:
            await safe_edit(query, f"❌ خطأ في التفعيل.\n\n" + header, markup=kb, parse_mode=ParseMode.HTML)
        return

    if data.startswith("dj_offer:"):
        pkg = data.split(":", 1)[1]
        await trigger_dj_offer(query, context, pkg, from_callback=True)
        return

    if data.startswith("dj_offer_fallback:"):
        pkg = data.split(":", 1)[1]
        num = get_active_number(uid)
        if not num:
            return
        msisdn = num["msisdn"]
        offer_info = DJ_OFFERS.get(pkg, {})
        offer_name = offer_info.get("name", pkg)

        await safe_edit(query, f"⏳ جاري إرسال رمز للطريقة الثانية...")
        ok = await dj_send_otp(msisdn, DJ_CLIENT_ID_NEW)
        if not ok:
            header, kb = main_menu_kb(uid)
            await safe_edit(query, "❌ فشل إرسال رمز التحقق.\n\n" + header, markup=kb, parse_mode=ParseMode.HTML)
            return
        context.user_data["state"]       = "awaiting_dj_offer_otp"
        context.user_data["dj_msisdn"]   = msisdn
        context.user_data["dj_phone"]    = "0" + msisdn[3:]
        context.user_data["pending_pkg"] = pkg
        await safe_edit(query,
            f"✅ تم إرسال رمز التحقق.\n\n"
            f"🔢 أدخل الرمز لتفعيل <b>{offer_name}</b>:\n"
            "❌ أو أرسل <code>0</code> للإلغاء",
            parse_mode=ParseMode.HTML)
        return

    # ─── أوريدو ───
    if data == "oo_daily":
        await trigger_oo_daily_gift(query, context, uid)
        return

    if data == "oo_snap":
        await trigger_oo_snapchat(query, context, uid)
        return

    if data == "oo_info":
        await trigger_oo_info(query, context, uid)
        return

    if data == "oo_offers":
        num = get_active_number(uid)
        ms  = mask_msisdn((num or {}).get("msisdn", ""))
        await safe_edit(query,
            f"📦 <b>عروض أوريدو</b> — الرقم: <code>{ms}</code>\n\nاختر العرض:",
            markup=oo_offers_kb(), parse_mode=ParseMode.HTML)
        return

    if data.startswith("oo_offer:"):
        n = int(data.split(":", 1)[1])
        await trigger_oo_offer(query, context, uid, n)
        return

    # ─── إدارة ───
    if is_admin(query.from_user.id):
        await handle_admin_callback(query, context, uid, data)
        return

# ════════════════════════════════════════════════════════════════════════
#  ADMIN CALLBACKS
# ════════════════════════════════════════════════════════════════════════
async def handle_admin_callback(query, context, uid: str, data: str):
    if data == "adm_stats":
        stats   = get_user_stats()
        dj_cnt  = len(load_dj_proxies())
        oo_cnt  = len(load_oo_proxies())
        cfg     = get_match_gift_cfg()
        text = (
            f"📊 <b>إحصائيات Tasjil BOT</b>\n\n"
            f"👥 إجمالي المستخدمين: <b>{stats['total']}</b>\n"
            f"🟢 نشط (7 أيام): <b>{stats['active_7d']}</b>\n"
            f"🟡 نشط (30 يوم): <b>{stats['active_30d']}</b>\n\n"
            f"🔗 بروكسيات جازي: <b>{dj_cnt}</b> {'✅' if dj_proxy_enabled() else '🔴'}\n"
            f"🔗 بروكسيات أوريدو: <b>{oo_cnt}</b> {'✅' if oo_proxy_enabled() else '🔴'}\n\n"
            f"🟢 جازي: {'✅ نشط' if not is_djezzy_disabled() else '🔴 صيانة'}\n"
            f"🟡 أوريدو: {'✅ نشط' if not is_ooredoo_disabled() else '🔴 صيانة'}\n\n"
            f"🎁 هدية المباراة: {'✅' if cfg['enabled'] else '❌'}\n"
            f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        await safe_edit(query, text, markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="adm_back")]]),
                        parse_mode=ParseMode.HTML)
        return

    if data == "adm_back":
        await safe_edit(query, "⚙️ <b>لوحة التحكم</b>", markup=admin_main_kb(), parse_mode=ParseMode.HTML)
        return

    if data == "adm_toggle_dj":
        cur = is_djezzy_disabled()
        _write_json(DJ_DISABLED_FILE, {"disabled": not cur, "msg": get_djezzy_disabled_msg()})
        await safe_edit(query,
            f"🟢 جازي الآن: {'🔴 في صيانة' if not cur else '✅ نشط'}",
            markup=admin_main_kb(), parse_mode=ParseMode.HTML)
        return

    if data == "adm_toggle_oo":
        cur = is_ooredoo_disabled()
        _write_json(OO_DISABLED_FILE, {"disabled": not cur, "msg": get_ooredoo_disabled_msg()})
        await safe_edit(query,
            f"🟡 أوريدو الآن: {'🔴 في صيانة' if not cur else '✅ نشط'}",
            markup=admin_main_kb(), parse_mode=ParseMode.HTML)
        return

    if data == "adm_toggle_dj_proxy":
        v = not dj_proxy_enabled()
        set_dj_proxy_enabled(v)
        await safe_edit(query, f"🔗 بروكسي جازي: {'✅ مفعّل' if v else '🔴 معطّل'}",
                        markup=admin_main_kb(), parse_mode=ParseMode.HTML)
        return

    if data == "adm_toggle_oo_proxy":
        v = not oo_proxy_enabled()
        set_oo_proxy_enabled(v)
        await safe_edit(query, f"🔗 بروكسي أوريدو: {'✅ مفعّل' if v else '🔴 معطّل'}",
                        markup=admin_main_kb(), parse_mode=ParseMode.HTML)
        return

    if data == "adm_edit_dj_proxies":
        current = "\n".join(load_dj_proxies())
        context.user_data["state"] = "awaiting_dj_proxies"
        await safe_edit(query,
            f"✏️ <b>بروكسيات جازي الحالية:</b>\n<code>{current}</code>\n\n"
            "أرسل القائمة الجديدة، كل بروكسي في سطر:\n"
            "<code>http://host:port:user:pass</code>\n\n"
            "/cancel للإلغاء",
            parse_mode=ParseMode.HTML)
        return

    if data == "adm_edit_oo_proxies":
        current = "\n".join(load_oo_proxies())
        context.user_data["state"] = "awaiting_oo_proxies"
        await safe_edit(query,
            f"✏️ <b>بروكسيات أوريدو الحالية:</b>\n<code>{current}</code>\n\n"
            "أرسل القائمة الجديدة، صيغة:\n"
            "<code>ip:port:user:pass</code>\n\n"
            "/cancel للإلغاء",
            parse_mode=ParseMode.HTML)
        return

    if data == "adm_refresh_dj_proxies":
        await safe_edit(query, "🔄 جاري تحديث بروكسيات جازي من API...")
        proxies = await refresh_dj_proxies()
        await safe_edit(query, f"✅ تم تحديث بروكسيات جازي: <b>{len(proxies)}</b>",
                        markup=admin_main_kb(), parse_mode=ParseMode.HTML)
        return

    if data == "adm_match_gift":
        cfg = get_match_gift_cfg()
        st  = "✅ مفعّلة" if cfg["enabled"] else "❌ معطلة"
        kb  = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔴 إيقاف" if cfg["enabled"] else "🟢 تفعيل",
                                  callback_data="adm_toggle_match")],
            [InlineKeyboardButton("✏️ تغيير QR Code", callback_data="adm_set_qr")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="adm_back")],
        ])
        await safe_edit(query,
            f"🎁 <b>هدية المباراة</b>\n\n"
            f"الحالة: {st}\n"
            f"الهدية: {cfg['gift_label']}\n"
            f"QR: <code>{cfg['qr_code']}</code>",
            markup=kb, parse_mode=ParseMode.HTML)
        return

    if data == "adm_toggle_match":
        cfg = get_match_gift_cfg()
        cfg["enabled"] = not cfg["enabled"]
        save_match_gift_cfg(cfg)
        await safe_edit(query,
            f"🎁 هدية المباراة: {'✅ مفعّلة' if cfg['enabled'] else '❌ معطلة'}",
            markup=admin_main_kb(), parse_mode=ParseMode.HTML)
        return

    if data == "adm_set_qr":
        context.user_data["state"] = "awaiting_qr"
        cfg = get_match_gift_cfg()
        await safe_edit(query,
            f"✏️ QR الحالي:\n<code>{cfg['qr_code']}</code>\n\nأرسل QR الجديد:\n/cancel للإلغاء",
            parse_mode=ParseMode.HTML)
        return

    if data == "adm_broadcast":
        stats = get_user_stats()
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"📢 الكل ({stats['total']})", callback_data="adm_bc_all"),
             InlineKeyboardButton(f"✅ النشطين ({stats['active_7d']})", callback_data="adm_bc_active")],
            [InlineKeyboardButton("❌ إلغاء", callback_data="adm_back")],
        ])
        await safe_edit(query, "📢 <b>إرسال إعلان</b>\n\nاختر الجمهور:",
                        markup=kb, parse_mode=ParseMode.HTML)
        return

    if data in ("adm_bc_all", "adm_bc_active"):
        target = "all" if data == "adm_bc_all" else "active_7d"
        context.user_data["state"]          = "awaiting_broadcast"
        context.user_data["bc_target"]      = target
        await safe_edit(query,
            f"📝 أرسل نص الإعلان:\n\n/cancel للإلغاء",
            parse_mode=ParseMode.HTML)
        return

    if data.startswith("adm_bc_confirm:"):
        bc_id = data.split(":", 1)[1]
        pending = context.user_data.get("pending_bc", {})
        if pending.get("id") != bc_id:
            await safe_edit(query, "❌ معرف البث غير متطابق.")
            return
        users = pending["users"]
        msg_text = pending["msg"]
        context.user_data.pop("pending_bc", None)
        await safe_edit(query, f"🚀 جاري الإرسال لـ <b>{len(users)}</b> مستخدم...",
                        parse_mode=ParseMode.HTML)
        sent = failed = skipped = 0
        for u in users:
            if was_broadcast_sent(bc_id, u):
                skipped += 1
                continue
            try:
                await application.bot.send_message(int(u),
                    f"📢 <b>إعلان:</b>\n\n{msg_text}", parse_mode=ParseMode.HTML)
                mark_broadcast_sent(bc_id, u)
                sent += 1
            except Exception:
                failed += 1
            await asyncio.sleep(0.08)
        await application.bot.send_message(
            query.message.chat.id,
            f"✅ اكتمل الإعلان\n📤 مُرسَل: {sent}\n❌ فشل: {failed}\n⏭️ تخطي: {skipped}",
            parse_mode=ParseMode.HTML)
        return

    if data == "adm_admins":
        admins = get_admins()
        lines = [f"• <code>{k}</code> — {v.get('name','')}" for k, v in admins.items()]
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ إضافة إداري", callback_data="adm_add_admin")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="adm_back")],
        ])
        await safe_edit(query,
            "👤 <b>الإداريون</b>\n\n" + ("\n".join(lines) or "لا يوجد إداريون إضافيون") + "\n\n"
            f"🔑 المشرف الرئيسي: " + ", ".join(str(i) for i in ADMIN_IDS),
            markup=kb, parse_mode=ParseMode.HTML)
        return

# ════════════════════════════════════════════════════════════════════════
#  ADMIN TEXT STATE HANDLERS
# ════════════════════════════════════════════════════════════════════════
async def handle_admin_broadcast_text(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    uid    = str(update.effective_user.id)
    target = context.user_data.get("bc_target", "all")
    users  = get_all_users() if target == "all" else get_active_users(7)
    bc_id  = f"bc_{int(time.time())}_{hashlib.md5(text.encode()).hexdigest()[:6]}"

    context.user_data["pending_bc"] = {"id": bc_id, "users": users, "msg": text}
    context.user_data["state"] = ""

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"✅ إرسال للـ {len(users)}", callback_data=f"adm_bc_confirm:{bc_id}"),
         InlineKeyboardButton("❌ إلغاء", callback_data="adm_back")],
    ])
    await update.message.reply_text(
        f"📢 <b>معاينة الإعلان</b>\n\n"
        f"🎯 المستهدفون: {len(users)} مستخدم\n"
        f"━━━━━━━━━━━━━━\n{text}\n━━━━━━━━━━━━━━\n\n⚠️ تأكيد الإرسال؟",
        reply_markup=kb, parse_mode=ParseMode.HTML)

async def handle_admin_dj_proxies(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    uid = str(update.effective_user.id)
    context.user_data.clear()
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if not lines:
        await update.message.reply_text("❌ لا توجد بروكسيات صالحة.")
        return
    save_dj_proxies(lines)
    await update.message.reply_text(f"✅ تم حفظ <b>{len(lines)}</b> بروكسي لجازي.",
                                    parse_mode=ParseMode.HTML)
    await update.message.reply_text("⚙️ <b>لوحة التحكم</b>", reply_markup=admin_main_kb(),
                                    parse_mode=ParseMode.HTML)

async def handle_admin_oo_proxies(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    uid = str(update.effective_user.id)
    context.user_data.clear()
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    valid = []
    for l in lines:
        parts = l.split(":")
        if len(parts) == 4:
            valid.append(l)
        elif "@" in l:
            up, hp = l.split("@", 1)
            h, p   = hp.split(":", 1) if ":" in hp else (hp, "")
            valid.append(f"{h}:{p}:{up}")
    if not valid:
        await update.message.reply_text("❌ لا توجد بروكسيات صالحة (صيغة: ip:port:user:pass).")
        return
    save_oo_proxies(valid)
    await update.message.reply_text(f"✅ تم حفظ <b>{len(valid)}</b> بروكسي لأوريدو.",
                                    parse_mode=ParseMode.HTML)
    await update.message.reply_text("⚙️ <b>لوحة التحكم</b>", reply_markup=admin_main_kb(),
                                    parse_mode=ParseMode.HTML)

async def handle_admin_qr(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    context.user_data.clear()
    cfg = get_match_gift_cfg()
    cfg["qr_code"] = text.strip()
    save_match_gift_cfg(cfg)
    await update.message.reply_text(f"✅ تم تحديث QR:\n<code>{cfg['qr_code']}</code>",
                                    parse_mode=ParseMode.HTML)

async def handle_admin_disable_msg(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    target = context.user_data.get("disable_target", "dj")
    context.user_data.clear()
    if target == "dj":
        d = _read_json(DJ_DISABLED_FILE, {})
        d["msg"] = text.strip()
        _write_json(DJ_DISABLED_FILE, d)
    else:
        d = _read_json(OO_DISABLED_FILE, {})
        d["msg"] = text.strip()
        _write_json(OO_DISABLED_FILE, d)
    await update.message.reply_text("✅ تم تحديث رسالة الصيانة.")

# ════════════════════════════════════════════════════════════════════════
#  WEBHOOK SERVER
# ════════════════════════════════════════════════════════════════════════
async def webhook_handler(request: web.Request) -> web.Response:
    try:
        data   = await request.json()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
    return web.Response(text="OK")

async def health_check(request: web.Request) -> web.Response:
    return web.Response(text="Tasjil BOT ✅")

# ════════════════════════════════════════════════════════════════════════
#  APPLICATION SETUP
# ════════════════════════════════════════════════════════════════════════
async def set_bot_commands(app):
    commands = [
        BotCommand("start",  "🚀 البداية"),
        BotCommand("menu",   "📋 القائمة"),
        BotCommand("cancel", "❌ إلغاء"),
        BotCommand("help",   "📖 المساعدة"),
    ]
    await app.bot.set_my_commands(commands)
    await app.bot.set_chat_menu_button()

def build_application() -> Application:
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .concurrent_updates(True)
        .build()
    )
    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("menu",   cmd_menu))
    app.add_handler(CommandHandler("cancel", cmd_cancel))
    app.add_handler(CommandHandler("help",   cmd_help))
    app.add_handler(CommandHandler("yacin",  cmd_admin))  # سري
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    return app

async def main():
    global application
    application = build_application()

    await application.initialize()
    await set_bot_commands(application)

    if WEBHOOK_URL:
        webhook_full = WEBHOOK_URL.rstrip("/") + WEBHOOK_PATH
        await application.bot.set_webhook(
            url=webhook_full,
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True,
        )
        logger.info(f"Webhook: {webhook_full}")

        web_app = web.Application()
        web_app.router.add_post(WEBHOOK_PATH, webhook_handler)
        web_app.router.add_get("/",       health_check)
        web_app.router.add_get("/health", health_check)

        await application.start()
        runner = web.AppRunner(web_app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", WEBHOOK_PORT)
        await site.start()
        logger.info(f"Server on port {WEBHOOK_PORT}")
        while True:
            await asyncio.sleep(3600)
    else:
        logger.info("Polling mode")
        await application.bot.delete_webhook(drop_pending_updates=True)
        await application.start()
        await application.updater.start_polling(
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True,
        )
        await application.updater.idle()

if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
# ════════════════════════════════════════════════════════════════════════
#  TASJIL BOT — Telegram (Djezzy Only) | Python 3.11+ | Webhook Mode
#  Converted & Enhanced from PHP/Facebook → Telegram
# ════════════════════════════════════════════════════════════════════════

import os, json, time, re, logging, sqlite3, random, hashlib, asyncio
import aiohttp, aiofiles
from datetime import datetime, timezone
from pathlib import Path
from functools import wraps
from typing import Optional, Any

from aiohttp import web
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
    BotCommand, MenuButtonCommands
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
from telegram.constants import ParseMode
from telegram.error import TelegramError

# ════════════════════════════════════════════════════════════════════════
#  CONFIG
# ════════════════════════════════════════════════════════════════════════
BOT_TOKEN     = "8177922042:AAENSzEnv83UanX9J8egYLeT09ioy9YbTkA"
ADMIN_IDS     = {8499896271}          # set — قابل للتوسعة
WEBHOOK_PATH  = f"/webhook/{BOT_TOKEN}"
WEBHOOK_PORT  = int(os.getenv("PORT", 8443))
WEBHOOK_URL   = os.getenv("WEBHOOK_URL", "")   # مثل https://yourdomain.com

ACTIVATION_CHANNEL = "@tasjil_bot_activation"  # قناة الإثباتات

BASE_DIR      = Path("/tmp/djezzy_bot")
SESSIONS_DIR  = BASE_DIR / "sessions"
USERS_DIR     = BASE_DIR / "users"
PENDING_DIR   = BASE_DIR / "pending"
RATE_DIR      = BASE_DIR / "rate_limit"
ADMINS_FILE   = BASE_DIR / "admins.json"
PROXIES_FILE  = BASE_DIR / "proxies.json"
USERS_FILE    = BASE_DIR / "users_map.json"
BROADCAST_LOG = BASE_DIR / "broadcast_log.json"
MATCH_GIFT_F  = BASE_DIR / "match_gift.json"
BAN_FILE      = BASE_DIR / "banned.json"
SUB_CHANNELS  = BASE_DIR / "sub_channels.json"
DB_FILE       = BASE_DIR / "dedup.db"
DJEZZY_LOG    = BASE_DIR / "djezzy.log"

for d in [BASE_DIR, SESSIONS_DIR, USERS_DIR, PENDING_DIR, RATE_DIR]:
    d.mkdir(parents=True, exist_ok=True)

RATE_LIMIT_SECONDS = 600   # 10 دقائق بين كل طلبَين ناجحَين

# ════════════════════════════════════════════════════════════════════════
#  CLIENT CREDENTIALS — Djezzy API
# ════════════════════════════════════════════════════════════════════════
CLIENT_ID_OLD     = "87pIExRhxBb3_wGsA5eSEfyATloa"
CLIENT_SECRET_OLD = "uf82p68Bgisp8Yg1Uz8Pf6_v1XYa"
CLIENT_ID_NEW     = "6E6CwTkp8H1CyQxraPmcEJPQ7xka"
CLIENT_SECRET_NEW = "MVpXHW_ImuMsxKIwrJpoVVMHjRsa"

PROXY_API_URL = "https://dev-bendjarayacine.pantheonsite.io/wp-admin/maint/proxy.json"

DEFAULT_PROXIES = [
    "https://pr.oxylabs.io:7777:customer-resi_9eb6a5c5-cc-dz:9vgYBr~ShNkc",
]

# ════════════════════════════════════════════════════════════════════════
#  OFFERS MAP
# ════════════════════════════════════════════════════════════════════════
OFFERS = {
    "BTL500MBDAY":             {"name": "📦 5GB - 90دج - 24h",        "display": "الإنترنت: 5GB | السعر: 90 دج | المدة: 24 ساعة"},
    "DOVINTSPEEDDAY100MoPRE":  {"name": "📦 300Mo - 30دج - 24h",      "display": "الإنترنت: 300Mo | السعر: 30 دج | المدة: 24 ساعة"},
    "DOVINTSPEEDDAY250MoPRE":  {"name": "📦 600Mo - 50دج - 24h",      "display": "الإنترنت: 600Mo | السعر: 50 دج | المدة: 24 ساعة"},
    "DOVINTSPEEDDAY1GoPRE":    {"name": "📦 2Go - 100دج - 24h",       "display": "الإنترنت: 2Go | السعر: 100 دج | المدة: 24 ساعة"},
    "OFFREJEUNE50":            {"name": "📦 1Go - 50دج - 24h",        "display": "الإنترنت: 1Go | السعر: 50 دج | المدة: 24 ساعة"},
    "BTLINTSPEEDDAY2Go":       {"name": "🏷️ 4GB - 70دج - 24h",       "display": "الإنترنت: 4GB | السعر: 70 دج | المدة: 24 ساعة"},
    "BTL4GBDAY":               {"name": "📦 5GB - 190دج - 24h",       "display": "الإنترنت: 5GB | السعر: 190 دج | المدة: 24 ساعة"},
    "BTL1GBDAY":               {"name": "📦 4GB - 140دج - 24h",       "display": "الإنترنت: 4GB | السعر: 140 دج | المدة: 24 ساعة"},
    "DOVINTSPEEDWEEK2GoPRE":   {"name": "📦 4Go - 150دج - 7أيام",     "display": "الإنترنت: 4Go | السعر: 150 دج | المدة: 7 أيام"},
    "DOVINTSPEEDWEEK3GoPRE":   {"name": "📦 10Go - 300دج - 7أيام",    "display": "الإنترنت: 10Go | السعر: 300 دج | المدة: 7 أيام"},
    "BTLDATA2WEEKS":           {"name": "📦 4GB - 400دج - 15يوم",     "display": "الإنترنت: 4GB | السعر: 400 دج | المدة: 15 يوم"},
    "1GBFB3DAYInternet":       {"name": "📦 1GB(FB) - 70دج - 3أيام",  "display": "الإنترنت: 1GB (Facebook) | السعر: 70 دج | المدة: 3 أيام"},
    "DOVINTSPEEDMONTH6GoPRE":  {"name": "📦 12Go - 500دج - 30يوم",    "display": "الإنترنت: 12Go | السعر: 500 دج | المدة: 30 يوم"},
    "DOVINTSPEEDMONTH15GoPRE": {"name": "📦 30Go - 1000دج - 30يوم",   "display": "الإنترنت: 30Go | السعر: 1000 دج | المدة: 30 يوم"},
    "DOVINTSPEEDMONTH30GoPRE": {"name": "📦 60Go - 1500دج - 30يوم",   "display": "الإنترنت: 60Go | السعر: 1500 دج | المدة: 30 يوم"},
    "2GBMONTH":                {"name": "📦 3GB - 250دج - 30يوم",     "display": "الإنترنت: 3GB | السعر: 250 دج | المدة: 30 يوم"},
    "BTL500MBHOUR":            {"name": "⚡ 1GB - 40دج - 1ساعة",      "display": "الإنترنت: 1GB | السعر: 40 دج | المدة: 1 ساعة"},
    "ImtiyazSurpriseData2hfbPRE": {"name": "📘 FB غير محدود - 50دج - 4h", "display": "الإنترنت: Facebook غير محدود | السعر: 50 دج | المدة: 4 ساعات"},
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

# ════════════════════════════════════════════════════════════════════════
#  LOGGING
# ════════════════════════════════════════════════════════════════════════
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("tasjil_bot")

def dlog(msg: str):
    try:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(DJEZZY_LOG, "a") as f:
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
    _db_conn.execute("""CREATE TABLE IF NOT EXISTS processed_events
        (event_id TEXT PRIMARY KEY, created_at INTEGER NOT NULL)""")
    _db_conn.execute("""CREATE TABLE IF NOT EXISTS user_locks
        (uid TEXT PRIMARY KEY, locked_at INTEGER NOT NULL)""")
    _db_conn.execute("""CREATE INDEX IF NOT EXISTS idx_ev_ts
        ON processed_events(created_at)""")
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
        db.execute("INSERT OR IGNORE INTO processed_events VALUES (?,?)",
                   (event_id, int(time.time())))
        db.commit()
        return db.changes() > 0  # type: ignore
    except Exception:
        return True

def try_lock_user(uid: str) -> bool:
    try:
        db = get_db()
        db.execute("INSERT OR IGNORE INTO user_locks VALUES (?,?)",
                   (str(uid), int(time.time())))
        db.commit()
        return db.changes() > 0  # type: ignore
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

# ─── Sessions ───
def get_session(uid: str) -> dict:
    return _read_json(SESSIONS_DIR / f"{uid}.json", {})

def set_session(uid: str, data: dict):
    _write_json(SESSIONS_DIR / f"{uid}.json", data)

def clear_session(uid: str):
    p = SESSIONS_DIR / f"{uid}.json"
    if p.exists():
        p.unlink()

# ─── Users ───
def save_user(uid: str, data: dict):
    _write_json(USERS_DIR / f"{uid}.json", data)

def get_user(uid: str) -> Optional[dict]:
    return _read_json(USERS_DIR / f"{uid}.json", None)

# ─── Users Map (all known users) ───
def get_users_map() -> dict:
    return _read_json(USERS_FILE, {})

def mark_user_seen(uid: str):
    m = get_users_map()
    now = int(time.time())
    if str(uid) not in m:
        m[str(uid)] = {"first_seen": now, "last_active": now}
    else:
        m[str(uid)]["last_active"] = now
    _write_json(USERS_FILE, m)

def get_all_users() -> list:
    return list(get_users_map().keys())

def get_active_users(days=7) -> list:
    m = get_users_map()
    since = int(time.time()) - days * 86400
    return [uid for uid, d in m.items()
            if (d["last_active"] if isinstance(d, dict) else d) >= since]

def get_user_stats() -> dict:
    m = get_users_map()
    total = len(m)
    now = int(time.time())
    a7 = sum(1 for d in m.values()
             if (d["last_active"] if isinstance(d, dict) else d) >= now - 7*86400)
    a30 = sum(1 for d in m.values()
              if (d["last_active"] if isinstance(d, dict) else d) >= now - 30*86400)
    return {"total": total, "active_7d": a7, "active_30d": a30}

# ─── Phone Map ───
PHONE_MAP_FILE = BASE_DIR / "phone_map.json"

def save_phone_owner(msisdn: str, uid: str):
    m = _read_json(PHONE_MAP_FILE, {})
    m[msisdn] = str(uid)
    _write_json(PHONE_MAP_FILE, m)

def get_phone_owner(msisdn: str) -> Optional[str]:
    return _read_json(PHONE_MAP_FILE, {}).get(msisdn)

# ─── Pending ───
def set_pending(uid: str, op: str):
    _write_json(PENDING_DIR / f"{uid}.json", {"op": op, "ts": int(time.time())})

def clear_pending(uid: str):
    p = PENDING_DIR / f"{uid}.json"
    if p.exists():
        p.unlink()

# ─── Banned ───
def is_banned(uid: str) -> bool:
    return str(uid) in _read_json(BAN_FILE, {})

def ban_user(uid: str):
    m = _read_json(BAN_FILE, {})
    m[str(uid)] = int(time.time())
    _write_json(BAN_FILE, m)

def unban_user(uid: str):
    m = _read_json(BAN_FILE, {})
    m.pop(str(uid), None)
    _write_json(BAN_FILE, m)

# ─── Admins ───
def get_admins() -> dict:
    return _read_json(ADMINS_FILE, {})

def is_admin(uid: int) -> bool:
    return uid in ADMIN_IDS or str(uid) in get_admins()

def add_admin(uid: str, info: dict):
    m = get_admins()
    m[str(uid)] = info
    _write_json(ADMINS_FILE, m)

def remove_admin(uid: str):
    m = get_admins()
    m.pop(str(uid), None)
    _write_json(ADMINS_FILE, m)

# ─── Sub Channels (mandatory subscription) ───
def get_sub_channels() -> list:
    return _read_json(SUB_CHANNELS, [])

def save_sub_channels(channels: list):
    _write_json(SUB_CHANNELS, channels)

# ─── Match Gift ───
def get_match_gift_config() -> dict:
    defaults = {"enabled": False, "qr_code": "https://www.djezzy.dz/scanwin-wd26?1",
                "gift_label": "12Go", "start_hour": 1, "end_hour": 5}
    d = _read_json(MATCH_GIFT_F, {})
    return {**defaults, **d}

def save_match_gift_config(cfg: dict):
    _write_json(MATCH_GIFT_F, cfg)

# ─── Rate Limit ───
def get_rate_timestamps(uid: str) -> list:
    return _read_json(RATE_DIR / f"{uid}.json", [])

def record_final_result(uid: str):
    ts = get_rate_timestamps(uid)
    ts.append(int(time.time()))
    if len(ts) > 2:
        ts = ts[-2:]
    _write_json(RATE_DIR / f"{uid}.json", ts)

def check_rate_limit(uid: str) -> Optional[int]:
    ts = get_rate_timestamps(uid)
    if len(ts) < 2:
        return None
    elapsed = int(time.time()) - ts[0]
    if elapsed < RATE_LIMIT_SECONDS:
        return RATE_LIMIT_SECONDS - elapsed
    return None

def format_rate_remaining(secs: int) -> str:
    minutes = max(1, (secs + 59) // 60)
    return "أقل من دقيقة" if minutes <= 1 else f"{minutes} دقيقة"

# ─── Broadcast Log ───
def get_broadcast_log() -> dict:
    return _read_json(BROADCAST_LOG, {})

def save_broadcast_log(log: dict):
    _write_json(BROADCAST_LOG, log)

def was_broadcast_sent(bc_id: str, uid: str) -> bool:
    return uid in get_broadcast_log().get(bc_id, {})

def mark_broadcast_sent(bc_id: str, uid: str):
    log = get_broadcast_log()
    if bc_id not in log:
        log[bc_id] = {}
    log[bc_id][uid] = int(time.time())
    save_broadcast_log(log)

# ════════════════════════════════════════════════════════════════════════
#  PROXY SYSTEM
# ════════════════════════════════════════════════════════════════════════
def load_proxies() -> list:
    d = _read_json(PROXIES_FILE, [])
    return d if d else list(DEFAULT_PROXIES)

def save_proxies(proxies: list):
    _write_json(PROXIES_FILE, proxies)

async def refresh_proxies_from_api() -> list:
    try:
        async with aiohttp.ClientSession() as sess:
            async with sess.get(PROXY_API_URL, timeout=aiohttp.ClientTimeout(total=8)) as r:
                if r.status == 200:
                    data = await r.json(content_type=None)
                    if isinstance(data, list) and data:
                        save_proxies(data)
                        return data
    except Exception:
        pass
    return load_proxies()

def parse_proxy(raw: str) -> dict:
    """
    Formats supported:
      https://host:port:user:pass
      host:port:user:pass
      user:pass@host:port
    """
    raw = raw.strip()
    # strip scheme
    raw_clean = re.sub(r'^https?://', '', raw)
    # user:pass@host:port
    if '@' in raw_clean:
        userpass, hostport = raw_clean.rsplit('@', 1)
        hp = hostport.split(':', 1)
        return {"url": f"http://{userpass}@{hostport}",
                "host": hp[0], "port": int(hp[1]) if len(hp) > 1 else 3128,
                "userpass": userpass}
    # host:port:user:pass
    parts = raw_clean.split(':', 3)
    if len(parts) == 4:
        host, port, user, pw = parts
        return {"url": f"http://{user}:{pw}@{host}:{port}",
                "host": host, "port": int(port),
                "userpass": f"{user}:{pw}"}
    return {"url": f"http://{raw_clean}", "host": raw_clean, "port": 3128, "userpass": ""}

async def curl_with_proxies(
    url: str,
    method: str = "POST",
    data: Any = None,
    headers: dict = None,
    log_tag: str = "",
    timeout: int = 10,
    batch_size: int = 6,
) -> Optional[dict]:
    """
    Tries proxies in parallel batches. Returns {"status": int, "json": dict, "text": str} or None.
    """
    proxies = load_proxies()
    if not proxies:
        dlog(f"[{log_tag}] No proxies!")
        return None

    random.shuffle(proxies)
    hdr = headers or {}

    async def _try_one(proxy_raw: str) -> Optional[dict]:
        pp = parse_proxy(proxy_raw)
        try:
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as sess:
                kwargs = dict(
                    headers=hdr,
                    proxy=pp["url"],
                    timeout=aiohttp.ClientTimeout(total=timeout, connect=4),
                )
                if method == "POST":
                    if isinstance(data, str):
                        kwargs["data"] = data
                    elif isinstance(data, dict):
                        kwargs["json"] = data
                async with getattr(sess, method.lower())(url, **kwargs) as resp:
                    text = await resp.text()
                    if "<html" in text.lower() or "<!doctype" in text.lower():
                        return None
                    try:
                        j = json.loads(text)
                    except Exception:
                        j = None
                    return {"status": resp.status, "json": j, "text": text}
        except Exception as e:
            dlog(f"[{log_tag}] proxy={pp['host']} err={e}")
            return None

    # Batch parallel
    for batch_start in range(0, len(proxies), batch_size):
        batch = proxies[batch_start:batch_start + batch_size]
        tasks = [asyncio.create_task(_try_one(p)) for p in batch]
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED,
                                           timeout=timeout + 2)
        for t in pending:
            t.cancel()
        for t in done:
            result = t.result()
            if result is not None:
                # cancel rest
                for tt in tasks:
                    tt.cancel()
                return result
        await asyncio.sleep(0.1)

    dlog(f"[{log_tag}] ALL proxies failed!")
    return None

# ════════════════════════════════════════════════════════════════════════
#  DJEZZY API — OTP + Token + Refresh
# ════════════════════════════════════════════════════════════════════════
DJEZZY_UA = "Dalvik/2.1.0 (Linux; U; Android 6.0; PGN610 Build/MRA58K)"
DJEZZY_UA2 = "MobileApp/3.0.9"

async def send_djezzy_otp(msisdn: str, client_id: str = CLIENT_ID_OLD) -> bool:
    url    = "https://apim.djezzy.dz/mobile-api/oauth2/registration"
    params = f"msisdn={msisdn}&client_id={client_id}&scope=smsotp"
    body   = json.dumps({"consent-agreement": [{"marketing-notifications": False}],
                         "is-consent": True})
    hdrs   = {"Content-Type": "application/json", "Accept": "application/json",
              "Accept-Encoding": "gzip", "User-Agent": DJEZZY_UA2,
              "accept-language": "fr"}
    result = await curl_with_proxies(
        f"{url}?{params}", "POST", body, hdrs, "OTP", timeout=8
    )
    if result and 200 <= result["status"] < 300:
        dlog(f"[OTP] msisdn={msisdn} client={client_id} OK")
        return True
    dlog(f"[OTP] msisdn={msisdn} FAIL status={result['status'] if result else 'None'}")
    return False

async def verify_otp(msisdn: str, otp: str, client_id: str = CLIENT_ID_OLD,
                     client_secret: str = CLIENT_SECRET_OLD) -> Any:
    """Returns dict|'wrong_otp'|False"""
    body = "&".join([
        "scope=djezzyAppV2",
        f"client_secret={client_secret}",
        f"client_id={client_id}",
        f"otp={otp}",
        f"mobileNumber={msisdn}",
        "grant_type=mobile",
    ])
    hdrs = {"Content-Type": "application/x-www-form-urlencoded",
            "Accept": "*/*", "User-Agent": DJEZZY_UA,
            "Connection": "Keep-Alive", "Accept-Encoding": "gzip"}
    result = await curl_with_proxies(
        "https://apim.djezzy.dz/oauth2/token", "POST", body, hdrs, "TOKEN", timeout=8
    )
    if not result:
        return False
    j = result["json"] or {}
    if result["status"] == 400 and j.get("error") == "invalid_grant":
        return "wrong_otp"
    if result["status"] == 200 and "access_token" in j:
        return {"access_token": j["access_token"],
                "refresh_token": j.get("refresh_token", "")}
    return False

async def verify_otp_new(msisdn: str, otp: str) -> Any:
    return await verify_otp(msisdn, otp, CLIENT_ID_NEW, CLIENT_SECRET_NEW)

async def refresh_access_token(refresh_token: str, msisdn: str) -> Any:
    """Returns dict|'expired'|False"""
    body = "&".join([
        "scope=djezzyAppV2",
        f"client_secret={CLIENT_SECRET_OLD}",
        f"client_id={CLIENT_ID_OLD}",
        "grant_type=refresh_token",
        f"refresh_token={refresh_token}",
    ])
    hdrs = {"Content-Type": "application/x-www-form-urlencoded",
            "Accept": "*/*", "User-Agent": DJEZZY_UA,
            "Connection": "Keep-Alive", "Accept-Encoding": "gzip"}
    result = await curl_with_proxies(
        "https://apim.djezzy.dz/oauth2/token", "POST", body, hdrs, "REFRESH", timeout=8
    )
    if not result:
        return False
    j = result["json"] or {}
    if result["status"] == 400 and j.get("error") == "invalid_grant":
        return "expired"
    if result["status"] == 200 and "access_token" in j:
        return {"access_token": j["access_token"],
                "refresh_token": j.get("refresh_token", refresh_token)}
    return False

async def refresh_access_token_new(refresh_token: str, msisdn: str) -> Any:
    body = "&".join([
        "scope=djezzyAppV2",
        f"client_secret={CLIENT_SECRET_NEW}",
        f"client_id={CLIENT_ID_NEW}",
        "grant_type=refresh_token",
        f"refresh_token={refresh_token}",
    ])
    hdrs = {"Content-Type": "application/x-www-form-urlencoded",
            "Accept": "*/*", "User-Agent": DJEZZY_UA,
            "Connection": "Keep-Alive", "Accept-Encoding": "gzip"}
    result = await curl_with_proxies(
        "https://apim.djezzy.dz/oauth2/token", "POST", body, hdrs, "REFRESH_NEW", timeout=8
    )
    if not result:
        return False
    j = result["json"] or {}
    if result["status"] == 400 and j.get("error") == "invalid_grant":
        return "expired"
    if result["status"] == 200 and "access_token" in j:
        return {"access_token": j["access_token"],
                "refresh_token": j.get("refresh_token", refresh_token)}
    return False

async def fetch_subscription_history(msisdn: str, access_token: str) -> Optional[dict]:
    url = f"https://apim.djezzy.dz/mobile-api/api/v1/subscribers/{msisdn}/subscription-history"
    hdrs = {"Content-Type": "application/json", "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "MobileApp/3.0.0"}
    result = await curl_with_proxies(url, "GET", None, hdrs, "HISTORY", timeout=10)
    return result["json"] if result and result["status"] == 200 else None

def get_last_walkwin_date(history: dict) -> Optional[int]:
    try:
        items = history.get("data", {}).get("subscriptionHistory", [])
        for item in items:
            code = item.get("serviceCode", "")
            if "GIFTWALKWIN" in code or "WALK" in code.upper():
                date_str = item.get("activationDate", "")
                if date_str:
                    from datetime import datetime
                    dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    return int(dt.timestamp())
    except Exception:
        pass
    return None

def format_time_remaining(secs: int) -> str:
    days = secs // 86400
    hours = (secs % 86400) // 3600
    mins = (secs % 3600) // 60
    parts = []
    if days:
        parts.append(f"{days} يوم")
    if hours:
        parts.append(f"{hours} ساعة")
    if mins:
        parts.append(f"{mins} دقيقة")
    return " و ".join(parts) if parts else "أقل من دقيقة"

# ════════════════════════════════════════════════════════════════════════
#  DJEZZY API — Activate Offers
# ════════════════════════════════════════════════════════════════════════
async def activate_offer_old(uid: str, user: dict, package_code: str,
                              send_fn, menu_fn) -> bool:
    """API القديمة. تُعيد True عند النجاح، False/None عند الفشل."""
    msisdn = user["msisdn"]
    access_token = user["access_token"]
    masked = msisdn[:4] + "xxxx" + msisdn[-2:]
    offer_info = OFFERS.get(package_code, {})
    offer_label = offer_info.get("name", package_code)

    url = f"https://apim.djezzy.dz/mobile-api/api/v1/subscribers/activate-product/{msisdn}"
    payload = json.dumps({"packageCode": package_code})
    hdrs = {"Content-Type": "application/json", "Accept": "application/json",
            "Accept-Encoding": "gzip", "accept-language": "fr",
            "authorization": f"Bearer {access_token}",
            "User-Agent": "MobileApp/3.0.0"}

    result = await curl_with_proxies(url, "POST", payload, hdrs,
                                     f"OFFER_OLD:{package_code}", timeout=10)
    if not result:
        return False

    status = result["status"]
    j = result["json"] or {}

    if status == 402 or j.get("status") == 402:
        balance = j.get("data", {}).get("mainBalance")
        bal_msg = f"\n💳 رصيدك الحالي: {balance} دج" if balance is not None else ""
        await send_fn(
            f"⚠️ رصيدك غير كافي لتفعيل هذا العرض 😔{bal_msg}\n\n"
            f"⚡ قناة التلغرام: t.me/tasjilbott"
        )
        return None  # فشل API حقيقي (ليس بروكسي)

    inner_status = j.get("status", 0)
    inner_msg = j.get("message", "")
    if isinstance(inner_msg, dict):
        inner_msg = inner_msg.get("en", "")

    if status in (200, 201) or inner_status == 200:
        if "successfully" in str(inner_msg).lower() or status == 201 or inner_status == 200:
            detail = offer_info.get("display", "")
            await send_fn(
                f"⭐ تم تفعيل العرض بنجاح! 🎁\n\n"
                f"📱 الرقم: {masked}\n"
                f"📦 العرض: {offer_label}\n"
                f"✅ {detail}\n\n"
                f"⚡ قناة التلغرام: t.me/tasjilbott"
            )
            return True

    return False

async def activate_offer_new(uid: str, user: dict, package_code: str,
                              send_fn, menu_fn):
    """API الجديدة — تُكرر حتى 10 مرات مع تجديد التوكن."""
    msisdn = user["msisdn"]
    access_token = user["access_token"]
    refresh_token = user.get("refresh_token", "")
    masked = msisdn[:4] + "xxxx" + msisdn[-2:]
    offer_info = OFFERS.get(package_code, {})
    offer_label = offer_info.get("name", package_code)

    url = (f"https://apim.djezzy.dz/djezzy-api/api/v1/subscribers"
           f"/{msisdn}/subscription-product?include=")
    max_attempts = 10
    token_refresh_count = 0

    for attempt in range(1, max_attempts + 1):
        payload = json.dumps({"data": {"id": package_code, "type": "products"}})
        hdrs = {"Content-Type": "application/json", "Accept": "application/json",
                "Accept-Encoding": "gzip", "Connection": "Keep-Alive",
                "Authorization": f"Bearer {access_token}",
                "User-Agent": "Djezzy/2.7.0", "X-Csrf-Token": "YACIN_DZ"}

        result = await curl_with_proxies(url, "POST", payload, hdrs,
                                         f"OFFER_NEW:{package_code}:#{attempt}",
                                         timeout=10)
        if not result:
            await asyncio.sleep(1)
            continue

        status = result["status"]
        j = result["json"] or {}

        # Token expired
        fault = j.get("fault", {})
        if fault and fault.get("code") == 900901:
            if token_refresh_count >= 3:
                break
            token_refresh_count += 1
            refreshed = await refresh_access_token_new(refresh_token, msisdn)
            if refreshed == "expired":
                # إعادة إرسال OTP
                phone_display = "0" + msisdn[3:]
                await send_djezzy_otp_and_wait_offer(uid, msisdn, phone_display,
                                                      package_code, send_fn)
                return
            if not refreshed:
                break
            access_token  = refreshed["access_token"]
            refresh_token = refreshed["refresh_token"]
            user = {**user, "access_token": access_token, "refresh_token": refresh_token}
            save_user(uid, user)
            continue

        if status == 402 or j.get("status") == 402:
            balance = j.get("data", {}).get("mainBalance")
            bal_msg = f"\n💳 رصيدك الحالي: {balance} دج" if balance is not None else ""
            await send_fn(
                f"⚠️ رصيدك غير كافي لتفعيل هذا العرض 😔{bal_msg}\n\n"
                f"⚡ قناة التلغرام: t.me/tasjilbott"
            )
            return

        if status in (200, 201):
            detail = offer_info.get("display", "")
            await send_fn(
                f"⭐ تم تفعيل العرض بنجاح! 🎁\n\n"
                f"📱 الرقم: {masked}\n"
                f"📦 العرض: {offer_label}\n"
                f"✅ {detail}\n\n"
                f"⚡ قناة التلغرام: t.me/tasjilbott"
            )
            return

        if status == 429:
            await asyncio.sleep(2)
        else:
            await asyncio.sleep(1)

    await send_fn(
        f"⚠️ تعذر تفعيل العرض. يبدو أن شريحتك لا تدعم هذا العرض أو حدث خطأ مؤقت.\n\n"
        f"⚡ قناة التلغرام: t.me/tasjilbott"
    )

async def activate_offer(uid: str, user: dict, package_code: str, send_fn, menu_fn):
    """يجرب API القديمة أولاً ثم الجديدة عند الفشل."""
    rl = check_rate_limit(uid)
    if rl:
        await send_fn(
            f"⏳ أنت ترسل طلبات كثيرة.\n\n"
            f"🕐 الوقت المتبقي: {format_rate_remaining(rl)}\n\n"
            f"يُطبَّق هذا القيد لضمان استمرارية الخدمة."
        )
        return

    set_pending(uid, f"تفعيل {package_code}")
    await send_fn("🔄 جاري تفعيل العرض...")

    result = await activate_offer_old(uid, user, package_code, send_fn, menu_fn)

    if result is True:
        # نجاح API القديمة
        record_final_result(uid)
        clear_pending(uid)
        clear_session(uid)
        await post_activation_log(user, package_code)
        await send_fn(
            "🥰 إذا أردت دعمنا لتطوير الخدمة:\n\n"
            "🔴 https://timebucks.com/?refID=227870531\n\n"
            "✅ سجّل بحساب جوجل فقط"
        )
        await menu_fn()
        return

    if result is None:
        # فشل API حقيقي (رصيد ناقص) — لا إعادة محاولة
        clear_pending(uid)
        record_final_result(uid)
        clear_session(uid)
        await menu_fn()
        return

    # result is False → فشل بروكسي → جرب الجديدة
    clear_pending(uid)
    await send_fn("⚠️ تعذر التفعيل بالطريقة الأولى، جاري تجربة طريقة أخرى...")
    phone_display = "0" + user["msisdn"][3:]
    await send_djezzy_otp_and_wait_offer(uid, user["msisdn"], phone_display,
                                          package_code, send_fn)

async def activate_2g(uid: str, user: dict, send_fn, menu_fn):
    rl = check_rate_limit(uid)
    if rl:
        await send_fn(
            f"⏳ أنت ترسل طلبات كثيرة.\n\n"
            f"🕐 الوقت المتبقي: {format_rate_remaining(rl)}"
        )
        return

    msisdn = user["msisdn"]
    access_token = user["access_token"]
    refresh_token = user.get("refresh_token", "")
    masked = msisdn[:4] + "xxxx" + msisdn[-2:]

    await send_fn("🔍 جاري فحص تاريخ آخر تفعيل...")
    history = await fetch_subscription_history(msisdn, access_token)
    if history:
        last_ts = get_last_walkwin_date(history)
        if last_ts:
            elapsed = int(time.time()) - last_ts
            seven_days = 7 * 24 * 3600
            if elapsed < seven_days:
                remaining = seven_days - elapsed
                record_final_result(uid)
                await send_fn(
                    f"😬 لم تكمل أسبوعاً بعد!\n\n"
                    f"⏳ الوقت المتبقي: {format_time_remaining(remaining)}\n\n"
                    f"⚡ قناة التلغرام: t.me/tasjilbott"
                )
                clear_session(uid)
                await menu_fn()
                return

    set_pending(uid, "تفعيل 2G 🎁")
    await send_fn("🔄 جاري تفعيل 2G الأسبوعية 🎁...")

    url = f"https://apim.djezzy.dz/mobile-api/api/v1/services/walk/activate-reward/{msisdn}"
    payload = json.dumps({"packageCode": "GIFTWALKWIN2GO"})
    max_attempts = 30
    token_refresh_count = 0

    for attempt in range(1, max_attempts + 1):
        hdrs = {"Content-Type": "application/json", "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "Authorization": f"Bearer {access_token}",
                "User-Agent": "MobileApp/3.0.0"}

        result = await curl_with_proxies(url, "POST", payload, hdrs,
                                         f"2G:#{attempt}", timeout=10)
        if not result:
            await asyncio.sleep(1)
            continue

        status = result["status"]
        j = result["json"] or {}

        fault = j.get("fault", {})
        if fault and fault.get("code") == 900901:
            if token_refresh_count >= 3:
                break
            token_refresh_count += 1
            refreshed = await refresh_access_token(refresh_token, msisdn)
            if refreshed == "expired":
                clear_pending(uid)
                await send_fn("🔄 انتهت صلاحية الجلسة، أرسل رقمك مجدداً.")
                clear_session(uid)
                return
            if not refreshed:
                break
            access_token  = refreshed["access_token"]
            refresh_token = refreshed["refresh_token"]
            save_user(uid, {**user, "access_token": access_token,
                            "refresh_token": refresh_token})
            continue

        if status in (402, 403):
            clear_pending(uid)
            record_final_result(uid)
            await send_fn(
                "⚠️ يلزمك الاشتراك في باقة 100دج أو أكثر أولاً للاستفادة من 2G المجانية كل أسبوع.\n\n"
                "🔴 ملاحظة: هذا التحديث من جيزي ولا يمكن تجاوزه.\n\n"
                "⚡ قناة التلغرام: t.me/tasjilbott"
            )
            clear_session(uid)
            await menu_fn()
            return

        if status in (200, 201):
            msg_str = j.get("message", "")
            if isinstance(msg_str, dict):
                msg_str = msg_str.get("en", "")
            if "successfully" in str(msg_str).lower() or status == 201:
                clear_pending(uid)
                record_final_result(uid)
                await send_fn(
                    f"⭐ تم تفعيل 2G بنجاح! 🎁\n\n"
                    f"📱 الرقم: {masked}\n\n"
                    f"⚡ قناة التلغرام: t.me/tasjilbott"
                )
                await post_activation_log(user, "GIFTWALKWIN2GO")
                clear_session(uid)
                await send_fn(
                    "🥰 إذا أردت دعمنا:\n\n"
                    "🔴 https://timebucks.com/?refID=227870531\n\n"
                    "✅ سجّل بحساب جوجل فقط"
                )
                await menu_fn()
                return
            await asyncio.sleep(1)
            continue

        if status == 429:
            await asyncio.sleep(2)
        else:
            await asyncio.sleep(1)

    clear_pending(uid)
    await send_fn(
        "⚠️ هناك مشكلة في سيرفر جيزي، تعذّر التفعيل لرقمك.\n\n"
        "⚡ قناة التلغرام: t.me/tasjilbott"
    )
    clear_session(uid)
    await menu_fn()

async def activate_match_gift(uid: str, user: dict, send_fn, menu_fn):
    cfg = get_match_gift_config()
    if not cfg["enabled"]:
        await send_fn("⏰ هدية المباراة غير متاحة حالياً.\n\n⚡ t.me/tasjilbott")
        return

    rl = check_rate_limit(uid)
    if rl:
        await send_fn(f"⏳ الوقت المتبقي: {format_rate_remaining(rl)}")
        return

    msisdn = user["msisdn"]
    access_token = user["access_token"]
    masked = msisdn[:4] + "xxxx" + msisdn[-2:]

    await send_fn("🔄 جاري تفعيل هدية مباراة الجزائر 🇩🇿...")

    url = f"https://apim.djezzy.dz/mobile-api/api/v1/services/scan/activate-reward/{msisdn}"
    payload = json.dumps({"qrCode": cfg["qr_code"]})
    hdrs = {"Content-Type": "application/json", "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "MobileApp/3.0.0"}

    result = await curl_with_proxies(url, "POST", payload, hdrs, "MATCH_GIFT", timeout=12)
    if not result:
        await send_fn("❌ حدث خطأ، يرجى المحاولة مجدداً.\n\n⚡ t.me/tasjilbott")
        return

    status = result["status"]
    if status in (200, 201):
        record_final_result(uid)
        await send_fn(
            f"🎉 تم تفعيل هدية المباراة بنجاح!\n\n"
            f"🇩🇿 استمتع بمباراة الجزائر ⚽\n\n"
            f"📱 الرقم: {masked}\n"
            f"🎁 الهدية: {cfg['gift_label']}\n\n"
            f"⚡ t.me/tasjilbott"
        )
        await post_activation_log(user, "MATCH_GIFT", cfg['gift_label'])
        clear_session(uid)
        await menu_fn()
        return

    if status == 400:
        record_final_result(uid)
        await send_fn(
            "⚠️ إما أن اليوم ليس يوم مباراة الجزائر، أو استفدت من الهدية مسبقاً، "
            "أو أن رقمك غير مؤهل.\n\n⚡ t.me/tasjilbott"
        )
        clear_session(uid)
        await menu_fn()
        return

    await send_fn(f"❌ حدث خطأ (HTTP {status}). يرجى المحاولة مجدداً.\n\n⚡ t.me/tasjilbott")
    clear_session(uid)

# ════════════════════════════════════════════════════════════════════════
#  MGM — Invite System
# ════════════════════════════════════════════════════════════════════════
async def fetch_mgm_invitations(msisdn: str, access_token: str) -> Optional[dict]:
    url = f"https://apim.djezzy.dz/mobile-api/api/v1/services/mgm/invitations/{msisdn}"
    hdrs = {"Accept": "application/json", "Accept-Encoding": "gzip",
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "MobileApp/3.0.0"}
    result = await curl_with_proxies(url, "GET", None, hdrs, "MGM_LIST", timeout=10)
    return result["json"] if result and result["status"] == 200 else None

async def try_activate_mgm_bonus(uid: str, msisdn: str, access_token: str) -> str:
    url = f"https://apim.djezzy.dz/mobile-api/api/v1/services/mgm/bonus/{msisdn}"
    hdrs = {"Content-Type": "application/json", "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "MobileApp/3.0.0"}
    result = await curl_with_proxies(url, "POST", "{}", hdrs, "MGM_BONUS", timeout=10)
    if not result:
        return "ERROR"
    j = result["json"] or {}
    status = result["status"]
    if status == 200:
        data = j.get("data", {})
        pkg = data.get("packageCode", "")
        if "1GO" in pkg.upper() or "1GB" in pkg.upper():
            return "SUCCESS_1GO"
        return "SUCCESS_500MO"
    if status == 409:
        return "ALREADY_CLAIMED"
    return "ERROR"

async def send_invite(msisdn: str, receiver_msisdn: str, access_token: str) -> str:
    url = f"https://apim.djezzy.dz/mobile-api/api/v1/services/mgm/invite/{msisdn}"
    payload = json.dumps({"receiverMsisdn": receiver_msisdn})
    hdrs = {"Content-Type": "application/json", "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "MobileApp/3.0.0"}
    result = await curl_with_proxies(url, "POST", payload, hdrs, "MGM_INVITE", timeout=10)
    if not result:
        return "ERROR"
    status = result["status"]
    j = result["json"] or {}
    if status in (200, 201):
        return "SUCCESS"
    if status == 409:
        return "DUPLICATE"
    if status == 400:
        return "NOT_DJEZZY"
    return f"ERROR_{status}"

async def delete_pending_invitations(msisdn: str, access_token: str, ids: list) -> bool:
    ok = True
    for inv_id in ids:
        url = (f"https://apim.djezzy.dz/mobile-api/api/v1/services/mgm"
               f"/invitation/{msisdn}/{inv_id}")
        hdrs = {"Accept": "application/json", "Accept-Encoding": "gzip",
                "Authorization": f"Bearer {access_token}",
                "User-Agent": "MobileApp/3.0.0"}
        result = await curl_with_proxies(url, "DELETE", None, hdrs, "MGM_DEL", timeout=8)
        if not result or result["status"] not in (200, 204):
            ok = False
    return ok

# ════════════════════════════════════════════════════════════════════════
#  ACTIVATION CHANNEL — Post Log
# ════════════════════════════════════════════════════════════════════════
async def post_activation_log(user: dict, offer_code: str,
                               override_label: str = None):
    """يرسل منشور تفعيل إلى قناة الإثباتات."""
    try:
        from telegram import Bot
        bot = Bot(token=BOT_TOKEN)

        msisdn = user.get("msisdn", "")
        uid = user.get("user_id", "")
        username = user.get("username", "")
        user_display = f"@{username}" if username else f"#{uid}"

        # اخفاء أجزاء من الرقم
        if len(msisdn) >= 12:
            local = "0" + msisdn[3:]  # 0770000000
            masked_phone = local[:2] + "xxxxxx" + local[-2:]
        else:
            masked_phone = msisdn

        offer_info = OFFERS.get(offer_code, {})
        offer_name = override_label or offer_info.get("name", offer_code)
        # استخراج حجم البيانات من الاسم
        size_match = re.search(r"(\d+(?:\.\d+)?)\s*(GB|Go|Mo|MB|جيقا|G)",
                               offer_name, re.IGNORECASE)
        size_str = size_match.group(0) if size_match else offer_name

        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        text = (
            f"🎉 <b>تفعيل جديد</b>\n\n"
            f"👤 المستخدم: {user_display}\n"
            f"🆔 ID: <code>{uid}</code>\n"
            f"📱 الرقم: <code>{masked_phone}</code>\n"
            f"🎁 نوع العرض: انترنت مجاني\n"
            f"✅ {offer_name}\n"
            f"💰 المجموع: {size_str}\n"
            f"🕐 الوقت: {now_utc}"
        )
        await bot.send_message(
            chat_id=ACTIVATION_CHANNEL,
            text=text,
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        dlog(f"[CHANNEL_LOG] err={e}")

# ════════════════════════════════════════════════════════════════════════
#  MANDATORY SUBSCRIPTION CHECK
# ════════════════════════════════════════════════════════════════════════
async def check_subscriptions(uid: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """يتحقق من اشتراك المستخدم في القنوات الإلزامية."""
    channels = get_sub_channels()
    if not channels:
        return True
    for ch in channels:
        try:
            member = await context.bot.get_chat_member(ch, uid)
            if member.status in ("left", "kicked", "banned"):
                return False
        except Exception:
            pass
    return True

def build_subscription_keyboard(channels: list) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(f"✅ اشترك في القناة {i+1}", url=f"https://t.me/{ch.lstrip('@')}")]
            for i, ch in enumerate(channels)]
    rows.append([InlineKeyboardButton("✔️ تحققت من الاشتراك", callback_data="check_sub")])
    return InlineKeyboardMarkup(rows)

# ════════════════════════════════════════════════════════════════════════
#  OTP WAIT HELPERS
# ════════════════════════════════════════════════════════════════════════
async def send_otp_and_wait(uid: str, msisdn: str, phone_display: str, send_fn):
    ok = await send_djezzy_otp(msisdn, CLIENT_ID_OLD)
    if ok:
        set_session(uid, {"state": "awaiting_otp", "msisdn": msisdn})
        await send_fn(
            f"✅ تم إرسال رمز التحقق إلى: <b>{phone_display}</b>\n\n"
            f"🔢 أدخل الرمز المكوّن من 6 أرقام:\n\n"
            f"📱 أو أرسل رقمك مجدداً لاستقبال رمز جديد\n\n"
            f"❌ لإلغاء أرسل: /cancel"
        )
    else:
        await send_fn(
            "⚠️ سيرفر جيزي غير متاح حالياً 🧑‍🔧\n\n"
            "يمكنك التسجيل عبر التطبيق:\n"
            "🔗 https://tasjil-app.lovestoblog.com\n\n"
            "أو من: https://t.me/tasjilbott/130"
        )

async def send_djezzy_otp_and_wait_offer(uid: str, msisdn: str, phone_display: str,
                                          package_code: str, send_fn):
    ok = await send_djezzy_otp(msisdn, CLIENT_ID_NEW)
    offer_info = OFFERS.get(package_code, {})
    offer_label = offer_info.get("name", package_code)
    if ok:
        set_session(uid, {"state": "awaiting_offer_otp",
                          "msisdn": msisdn,
                          "pending_package": package_code})
        await send_fn(
            f"✅ تم إرسال رمز التحقق إلى: <b>{phone_display}</b>\n\n"
            f"📌 نجرب طريقة تفعيل بديلة للعرض:\n"
            f"📦 <b>{offer_label}</b>\n\n"
            f"🔢 أدخل الرمز المكوّن من 6 أرقام:\n\n"
            f"📱 أو أرسل رقمك مجدداً لاستقبال رمز جديد\n\n"
            f"❌ لإلغاء أرسل: /cancel"
        )
    else:
        await send_fn(
            "⚠️ سيرفر جيزي غير متاح حالياً 🧑‍🔧\n\n"
            "يمكنك التسجيل عبر التطبيق:\n"
            "🔗 https://tasjil-app.lovestoblog.com"
        )

# ════════════════════════════════════════════════════════════════════════
#  TELEGRAM UI BUILDERS
# ════════════════════════════════════════════════════════════════════════
def main_menu_keyboard(cfg: dict = None) -> InlineKeyboardMarkup:
    if cfg is None:
        cfg = get_match_gift_config()
    rows = [
        [
            InlineKeyboardButton("📶 تفعيل 2G الأسبوعية 🎁", callback_data="menu_2g"),
            InlineKeyboardButton("🏷️ عرض 4GB بـ 70دج",       callback_data="menu_70dz"),
        ],
        [
            InlineKeyboardButton("📨 إرسال دعوة",             callback_data="menu_invite"),
            InlineKeyboardButton("📦 المزيد من العروض",        callback_data="menu_more"),
        ],
    ]
    if cfg.get("enabled"):
        rows.append([InlineKeyboardButton("🇩🇿 هدية المباراة 🔥", callback_data="menu_match")])
    return InlineKeyboardMarkup(rows)

def more_offers_keyboard() -> InlineKeyboardMarkup:
    offers_btn = [
        ("📦 5GB - 90دج (24h)",    "BTL500MBDAY"),
        ("📦 300Mo - 30دج (24h)",  "DOVINTSPEEDDAY100MoPRE"),
        ("📦 600Mo - 50دج (24h)",  "DOVINTSPEEDDAY250MoPRE"),
        ("📦 2Go - 100دج (24h)",   "DOVINTSPEEDDAY1GoPRE"),
        ("📦 1Go - 50دج (24h)",    "OFFREJEUNE50"),
        ("📦 5GB - 190دج (24h)",   "BTL4GBDAY"),
        ("📦 4GB - 140دج (24h)",   "BTL1GBDAY"),
        ("📦 4Go - 150دج (7أيام)", "DOVINTSPEEDWEEK2GoPRE"),
        ("📦 10Go - 300دج (7أيام)","DOVINTSPEEDWEEK3GoPRE"),
        ("📦 4GB - 400دج (15يوم)", "BTLDATA2WEEKS"),
        ("📦 12Go - 500دج (30يوم)","DOVINTSPEEDMONTH6GoPRE"),
        ("📦 30Go - 1000دج (30يوم)","DOVINTSPEEDMONTH15GoPRE"),
        ("📦 60Go - 1500دج (30يوم)","DOVINTSPEEDMONTH30GoPRE"),
        ("📦 3GB - 250دج (30يوم)", "2GBMONTH"),
        ("⚡ 1GB - 40دج (1ساعة)",  "BTL500MBHOUR"),
        ("📘 FB غير محدود 50دج",   "ImtiyazSurpriseData2hfbPRE"),
    ]
    rows = []
    for i in range(0, len(offers_btn), 2):
        row = [InlineKeyboardButton(offers_btn[i][0], callback_data=f"offer_{offers_btn[i][1]}")]
        if i + 1 < len(offers_btn):
            row.append(InlineKeyboardButton(offers_btn[i+1][0],
                                            callback_data=f"offer_{offers_btn[i+1][1]}"))
        rows.append(row)
    rows.append([InlineKeyboardButton("🔙 رجوع", callback_data="back_main")])
    return InlineKeyboardMarkup(rows)

def main_menu_text(cfg: dict = None) -> str:
    if cfg is None:
        cfg = get_match_gift_config()
    match_line = "\n🇩🇿 هدية المباراة متاحة الآن! 🔥" if cfg.get("enabled") else ""
    return (
        "📱 <b>اختر الخدمة المطلوبة</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "📶 <b>تفعيل 2G</b> — الهدية الأسبوعية المجانية\n"
        "🏷️ <b>عرض 4GB بـ 70دج</b> — لمدة 24 ساعة\n"
        "📨 <b>إرسال دعوة</b> — واكسب جيقا مجاناً\n"
        "📦 <b>المزيد من العروض</b> — كل عروض الإنترنت"
        f"{match_line}\n\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )

# ════════════════════════════════════════════════════════════════════════
#  ADMIN PANEL UI
# ════════════════════════════════════════════════════════════════════════
def admin_main_keyboard() -> InlineKeyboardMarkup:
    cfg = get_match_gift_config()
    match_status = "🟢 إيقاف هدية المباراة" if cfg["enabled"] else "🔴 تفعيل هدية المباراة"
    rows = [
        [
            InlineKeyboardButton("📊 إحصائيات",        callback_data="adm_stats"),
            InlineKeyboardButton("📢 بث رسالة",         callback_data="adm_broadcast"),
        ],
        [
            InlineKeyboardButton("🔗 البروكسيات",       callback_data="adm_proxies"),
            InlineKeyboardButton("➕ إضافة بروكسيات",    callback_data="adm_addproxy"),
        ],
        [
            InlineKeyboardButton(match_status,           callback_data="adm_toggle_match"),
            InlineKeyboardButton("✏️ تغيير QR",          callback_data="adm_set_qr"),
        ],
        [
            InlineKeyboardButton("🔄 تحديث بروكسيات API", callback_data="adm_refresh_proxy"),
        ],
        [
            InlineKeyboardButton("🚫 حظر مستخدم",        callback_data="adm_ban"),
            InlineKeyboardButton("✅ فك الحظر",           callback_data="adm_unban"),
        ],
        [
            InlineKeyboardButton("📡 القنوات الإلزامية", callback_data="adm_channels"),
            InlineKeyboardButton("👥 إدارة الإداريين",   callback_data="adm_admins"),
        ],
    ]
    return InlineKeyboardMarkup(rows)

def admin_menu_text() -> str:
    cfg = get_match_gift_config()
    stats = get_user_stats()
    proxies = load_proxies()
    match_status = "✅ مفعّلة" if cfg["enabled"] else "❌ معطلة"
    return (
        "🤖 <b>لوحة تحكم Tasjil BOT</b>\n\n"
        f"👥 المستخدمون: <b>{stats['total']}</b> | نشط 7أيام: <b>{stats['active_7d']}</b>\n"
        f"🔗 البروكسيات: <b>{len(proxies)}</b>\n"
        f"🎁 هدية المباراة: <b>{match_status}</b>\n"
        f"📦 الهدية: <b>{cfg['gift_label']}</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )

# ════════════════════════════════════════════════════════════════════════
#  HANDLERS — COMMANDS
# ════════════════════════════════════════════════════════════════════════
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    username = update.effective_user.username or ""
    chat_id = update.effective_chat.id

    if is_banned(uid):
        await update.message.reply_text("🚫 تم حظرك من استخدام هذا البوت.")
        return

    mark_user_seen(uid)
    # حفظ username
    user_data = get_user(uid) or {}
    user_data["user_id"] = uid
    user_data["username"] = username
    save_user(uid, user_data)

    # تحقق من الاشتراكات
    channels = get_sub_channels()
    if channels and not await check_subscriptions(int(uid), context):
        kb = build_subscription_keyboard(channels)
        await update.message.reply_text(
            "⚠️ <b>يجب الاشتراك في القنوات التالية أولاً:</b>",
            reply_markup=kb,
            parse_mode=ParseMode.HTML
        )
        return

    sess = get_session(uid)
    user = get_user(uid)

    if user and user.get("access_token") and user.get("msisdn"):
        cfg = get_match_gift_config()
        await update.message.reply_text(
            main_menu_text(cfg),
            reply_markup=main_menu_keyboard(cfg),
            parse_mode=ParseMode.HTML
        )
    else:
        await update.message.reply_text(
            "👋 <b>أهلاً وسهلاً في Tasjil BOT! 🎉</b>\n\n"
            "🌟 نرحب بك في بوت تفعيل عروض جيزي!\n\n"
            "📌 <b>مزايا البوت:</b>\n"
            "✅ تفعيل 2G الأسبوعية المجانية 🎁\n"
            "✅ إرسال الدعوات 📨\n"
            "✅ تفعيل عرض 4GB بـ 70دج 🏷️\n"
            "✅ جميع عروض الإنترنت ⭐\n\n"
            "━━━━━━━━━━━━━━\n\n"
            "📱 للبدء، <b>أرسل رقم هاتفك (جيزي)</b>\n"
            "🔹 مثال: <code>0770000000</code>\n\n"
            "⚡ قناة التلغرام: https://t.me/tasjilbott",
            parse_mode=ParseMode.HTML
        )

async def cmd_yacin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """فتح واجهة الإدارة."""
    uid = update.effective_user.id
    if not is_admin(uid):
        await update.message.reply_text("⛔ ليس لديك صلاحية الوصول.")
        return
    await update.message.reply_text(
        admin_menu_text(),
        reply_markup=admin_main_keyboard(),
        parse_mode=ParseMode.HTML
    )

async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if is_banned(uid):
        return
    mark_user_seen(uid)
    user = get_user(uid)
    if user and user.get("access_token"):
        cfg = get_match_gift_config()
        await update.message.reply_text(
            main_menu_text(cfg),
            reply_markup=main_menu_keyboard(cfg),
            parse_mode=ParseMode.HTML
        )
    else:
        await update.message.reply_text(
            "📱 أرسل رقم هاتفك (جيزي) للبدء:\n"
            "🔹 مثال: <code>0770000000</code>",
            parse_mode=ParseMode.HTML
        )

async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    clear_session(uid)
    clear_pending(uid)
    await update.message.reply_text("✅ تم إلغاء العملية الحالية.")
    user = get_user(uid)
    if user and user.get("access_token"):
        cfg = get_match_gift_config()
        await update.message.reply_text(
            main_menu_text(cfg),
            reply_markup=main_menu_keyboard(cfg),
            parse_mode=ParseMode.HTML
        )

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 <b>أوامر البوت:</b>\n\n"
        "/start — بداية أو إعادة تشغيل البوت\n"
        "/menu — عرض القائمة الرئيسية\n"
        "/cancel — إلغاء العملية الحالية\n"
        "/help — عرض هذه الرسالة\n\n"
        "💡 <b>للتسجيل:</b> أرسل رقم جيزي مباشرة\n\n"
        "⚡ قناة التلغرام: https://t.me/tasjilbott",
        parse_mode=ParseMode.HTML
    )

# ════════════════════════════════════════════════════════════════════════
#  HANDLERS — TEXT MESSAGES (State Machine)
# ════════════════════════════════════════════════════════════════════════
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    username = update.effective_user.username or ""
    text = (update.message.text or "").strip()
    chat_id = update.effective_chat.id

    if is_banned(uid):
        await update.message.reply_text("🚫 تم حظرك من استخدام هذا البوت.")
        return

    mark_user_seen(uid)
    # تحديث username
    user_data = get_user(uid) or {}
    user_data["user_id"] = uid
    user_data["username"] = username
    save_user(uid, user_data)

    async def send(msg: str, **kwargs):
        await update.message.reply_text(
            msg, parse_mode=ParseMode.HTML, **kwargs
        )

    async def show_menu():
        cfg = get_match_gift_config()
        await update.message.reply_text(
            main_menu_text(cfg),
            reply_markup=main_menu_keyboard(cfg),
            parse_mode=ParseMode.HTML
        )

    sess = get_session(uid)
    state = sess.get("state", "")

    # ══ حالة انتظار admin ══
    admin_state = context.user_data.get("admin_state", "")

    if is_admin(int(uid)) and admin_state:
        await handle_admin_text(update, context, uid, text, admin_state)
        return

    # ══ تحقق من الاشتراكات ══
    channels = get_sub_channels()
    if channels and not await check_subscriptions(int(uid), context):
        kb = build_subscription_keyboard(channels)
        await send("⚠️ يجب الاشتراك في القنوات أولاً:", reply_markup=kb)
        return

    # ══ State Machine ══
    if state == "awaiting_otp":
        await handle_awaiting_otp(uid, text, sess, send, show_menu)
        return

    if state == "awaiting_offer_otp":
        await handle_offer_otp(uid, text, sess, send, show_menu)
        return

    if state == "awaiting_invite_phone":
        await handle_invite_phone(uid, text, sess, send, show_menu)
        return

    # ══ رقم هاتف ══
    digits = re.sub(r'\D', '', text)
    if re.match(r'^07\d{8}$', digits):
        await handle_new_phone(uid, digits, send, show_menu)
        return

    # ══ اختصارات رقمية ══
    if text in OFFER_SHORTCUTS:
        pkg = OFFER_SHORTCUTS[text]
        user = get_user(uid)
        if not user or not user.get("access_token"):
            await send("⚠️ يجب تسجيل الدخول أولاً.\n\n📱 أرسل رقم هاتفك (جيزي)")
            return
        if sess.get("msisdn"):
            user["msisdn"] = sess["msisdn"]
        await activate_offer(uid, user, pkg, send, show_menu)
        return

    if text == "1":
        user = get_user(uid)
        if user and user.get("access_token"):
            if sess.get("msisdn"):
                user["msisdn"] = sess["msisdn"]
            set_session(uid, {**sess, "state": "menu"})
            await activate_2g(uid, user, send, show_menu)
        else:
            await send("⚠️ يجب تسجيل الدخول أولاً.\n\n📱 أرسل رقم هاتفك (جيزي)")
        return

    if text == "2":
        user = get_user(uid)
        if user and user.get("access_token"):
            if sess.get("msisdn"):
                user["msisdn"] = sess["msisdn"]
            await activate_offer(uid, user, "BTLINTSPEEDDAY2Go", send, show_menu)
        else:
            await send("⚠️ يجب تسجيل الدخول أولاً.\n\n📱 أرسل رقم هاتفك (جيزي)")
        return

    if text == "3":
        user = get_user(uid)
        if user and user.get("access_token"):
            if sess.get("msisdn"):
                user["msisdn"] = sess["msisdn"]
            await handle_invite_start(uid, user, send, show_menu)
        else:
            await send("⚠️ يجب تسجيل الدخول أولاً.\n\n📱 أرسل رقم هاتفك (جيزي)")
        return

    if text == "4":
        await show_more_offers(update)
        return

    if text == "30":
        cfg = get_match_gift_config()
        if cfg["enabled"]:
            user = get_user(uid)
            if user and user.get("access_token"):
                if sess.get("msisdn"):
                    user["msisdn"] = sess["msisdn"]
                await activate_match_gift(uid, user, send, show_menu)
            else:
                await send("⚠️ يجب تسجيل الدخول أولاً.\n\n📱 أرسل رقم هاتفك (جيزي)")
        else:
            await send("⏰ هدية المباراة غير متاحة حالياً.\n\n⚡ t.me/tasjilbott")
        return

    # ══ default ══
    user = get_user(uid)
    if user and user.get("access_token"):
        await show_menu()
    else:
        await send(
            "👋 أرسل رقم هاتفك (جيزي) للبدء:\n"
            "🔹 مثال: <code>0770000000</code>",
        )

async def handle_new_phone(uid: str, phone: str, send_fn, menu_fn):
    msisdn = "213" + phone[1:]
    owner = get_phone_owner(msisdn)
    user = get_user(uid)

    if owner == uid and user and user.get("access_token"):
        user["msisdn"] = msisdn
        save_user(uid, user)
        refreshed = await refresh_access_token(user["refresh_token"], msisdn)
        if refreshed == "expired":
            await send_djezzy_otp_and_wait_offer(uid, msisdn, phone,
                                                  None, send_fn)
            return
        if isinstance(refreshed, dict):
            save_user(uid, {**user, "msisdn": msisdn,
                            "access_token": refreshed["access_token"],
                            "refresh_token": refreshed["refresh_token"]})
            set_session(uid, {"state": "menu", "msisdn": msisdn})
            await send_fn("✅ تم التعرف على رقمك بنجاح!")
            await menu_fn()
            return

    elif owner and owner != uid:
        await send_fn(
            "🚫 أنت لست صاحب هذا الرقم، يجب إثبات الهوية.\n"
            "📲 سيتم إرسال رمز تحقق..."
        )

    await send_otp_and_wait(uid, msisdn, phone, send_fn)

async def handle_awaiting_otp(uid: str, text: str, sess: dict, send_fn, menu_fn):
    msisdn = sess.get("msisdn", "")
    phone_display = "0" + msisdn[3:] if len(msisdn) >= 4 else msisdn

    if text.lower() == "/cancel":
        clear_session(uid)
        await send_fn("✅ تم إلغاء عملية التسجيل.")
        return

    digits = re.sub(r'\D', '', text)
    if re.match(r'^07\d{8}$', digits):
        new_msisdn = "213" + digits[1:]
        clear_session(uid)
        await send_fn(f"📲 جاري إرسال رمز تحقق جديد إلى {digits}...")
        await send_otp_and_wait(uid, new_msisdn, digits, send_fn)
        return

    m = re.search(r'\b(\d{6})\b', text)
    if not m:
        await send_fn(
            f"⚠️ أدخل الرمز المكوّن من 6 أرقام.\n\n"
            f"📱 أو أرسل رقمك مجدداً\n"
            f"🔢 الرمز أُرسل إلى: <b>{phone_display}</b>\n\n"
            f"❌ لإلغاء: /cancel"
        )
        return

    otp = m.group(1)
    if not msisdn:
        clear_session(uid)
        await send_fn("❌ خطأ في الجلسة، أرسل رقمك مجدداً.")
        return

    result = await verify_otp(msisdn, otp)
    if result == "wrong_otp":
        await send_fn(
            "❌ الرمز خاطئ!\n\n"
            "🔄 أعد إدخال الرمز الصحيح\n"
            "📱 أو أرسل رقمك مجدداً\n\n"
            "❌ لإلغاء: /cancel"
        )
    elif result is False:
        await send_fn(
            "❌ حدث خطأ، حاول مجدداً.\n\n"
            "📱 يمكنك إرسال رقمك مجدداً\n\n"
            "❌ لإلغاء: /cancel"
        )
    else:
        user = get_user(uid) or {}
        user.update({"user_id": uid, "msisdn": msisdn,
                     "access_token": result["access_token"],
                     "refresh_token": result["refresh_token"]})
        save_user(uid, user)
        save_phone_owner(msisdn, uid)
        set_session(uid, {"state": "menu", "msisdn": msisdn})
        await send_fn("✅ تم تسجيل الدخول بنجاح! 🎉")
        await menu_fn()

async def handle_offer_otp(uid: str, text: str, sess: dict, send_fn, menu_fn):
    msisdn = sess.get("msisdn", "")
    package_code = sess.get("pending_package", "")
    phone_display = "0" + msisdn[3:] if len(msisdn) >= 4 else msisdn

    if text.lower() == "/cancel":
        clear_session(uid)
        set_session(uid, {"state": "menu", "msisdn": msisdn})
        await send_fn("✅ تم إلغاء عملية تفعيل العرض.")
        await menu_fn()
        return

    digits = re.sub(r'\D', '', text)
    if re.match(r'^07\d{8}$', digits):
        new_msisdn = "213" + digits[1:]
        clear_session(uid)
        await send_fn(f"📲 جاري إرسال رمز تحقق جديد إلى {digits}...")
        await send_djezzy_otp_and_wait_offer(uid, new_msisdn, digits, package_code, send_fn)
        return

    m = re.search(r'\b(\d{6})\b', text)
    if not m:
        await send_fn(
            f"⚠️ أدخل الرمز المكوّن من 6 أرقام.\n\n"
            f"📱 أو أرسل رقمك مجدداً\n"
            f"🔢 الرمز أُرسل إلى: <b>{phone_display}</b>\n\n"
            f"❌ لإلغاء: /cancel"
        )
        return

    if not msisdn or not package_code:
        clear_session(uid)
        await send_fn("❌ خطأ في الجلسة، أرسل رقمك مجدداً.")
        return

    otp = m.group(1)
    result = await verify_otp_new(msisdn, otp)
    if result == "wrong_otp":
        await send_fn(
            "❌ الرمز خاطئ!\n\n"
            "🔄 أعد إدخال الرمز الصحيح\n\n"
            "❌ لإلغاء: /cancel"
        )
        return
    if result is False:
        await send_fn(
            "❌ خطأ في التحقق، حاول مجدداً.\n\n"
            "❌ لإلغاء: /cancel"
        )
        return

    user_for_offer = {
        **(get_user(uid) or {}),
        "msisdn": msisdn,
        "access_token": result["access_token"],
        "refresh_token": result["refresh_token"],
    }
    save_user(uid, user_for_offer)
    save_phone_owner(msisdn, uid)
    set_session(uid, {"state": "menu", "msisdn": msisdn})
    await send_fn("✅ تم التحقق بنجاح! جاري تفعيل العرض...")
    await activate_offer_new(uid, user_for_offer, package_code, send_fn, menu_fn)
    record_final_result(uid)
    await post_activation_log(user_for_offer, package_code)
    await send_fn(
        "🥰 إذا أردت دعمنا:\n\n"
        "🔴 https://timebucks.com/?refID=227870531\n\n"
        "✅ سجّل بحساب جوجل فقط"
    )
    await menu_fn()

async def handle_invite_start(uid: str, user: dict, send_fn, menu_fn):
    rl = check_rate_limit(uid)
    if rl:
        await send_fn(f"⏳ الوقت المتبقي: {format_rate_remaining(rl)}")
        return

    msisdn = user["msisdn"]
    access_token = user["access_token"]

    await send_fn("🔍 جاري فحص المكافآت المعلقة...")
    bonus_result = await try_activate_mgm_bonus(uid, msisdn, access_token)

    if bonus_result == "SUCCESS_1GO":
        record_final_result(uid)
        await send_fn(
            "🎁 تم تفعيل مكافأة معلقة — حصلت على 1 جيقا! 🎉\n\n"
            "⏳ عد بعد 24 ساعة للحصول على مكافأة جديدة.\n\n"
            "⚡ t.me/tasjilbott"
        )
        await post_activation_log(user, "MGM_BONUS_1GO", "مكافأة دعوة 1Go")
        clear_session(uid)
        await menu_fn()
        return
    if bonus_result == "SUCCESS_500MO":
        record_final_result(uid)
        await send_fn(
            "🎁 تم تفعيل مكافأة معلقة — حصلت على 500Mo! 🎉\n\n"
            "⏳ عد بعد 24 ساعة للحصول على مكافأة جديدة.\n\n"
            "⚡ t.me/tasjilbott"
        )
        await post_activation_log(user, "MGM_BONUS_500MO", "مكافأة دعوة 500Mo")
        clear_session(uid)
        await menu_fn()
        return
    if bonus_result == "ALREADY_CLAIMED":
        record_final_result(uid)
        await send_fn(
            "⚠️ استفدت من الدعوة اليوم.\n"
            "⏳ تأكد من مرور 24 ساعة وأعد المحاولة.\n\n"
            "⚡ t.me/tasjilbott"
        )
        clear_session(uid)
        await menu_fn()
        return

    await send_fn("🔍 جاري فحص الدعوات المتاحة...")
    invitations = await fetch_mgm_invitations(msisdn, access_token)
    if invitations is None:
        await send_fn("❌ خطأ أثناء جلب بيانات الدعوات، حاول مجدداً.")
        clear_session(uid)
        await menu_fn()
        return

    max_inv = invitations.get("campaign", {}).get("maxInvitation", 5)
    inv_list = invitations.get("invitations", [])
    done_count = sum(1 for i in inv_list if i.get("status") == "DONE")
    pending_ids = [i["id"] for i in inv_list if i.get("status") == "PENDING"]
    total_count = len(inv_list)

    if done_count >= max_inv:
        record_final_result(uid)
        await send_fn(f"🚫 وصلت للحد الأقصى للدعوات ({max_inv}) ✅\n\n⚡ t.me/tasjilbott")
        clear_session(uid)
        await menu_fn()
        return

    if total_count >= max_inv and pending_ids:
        await send_fn("🔄 جاري حذف الدعوات المعلقة...")
        deleted = await delete_pending_invitations(msisdn, access_token, pending_ids)
        if not deleted:
            await send_fn("❌ تعذر حذف الدعوات المعلقة، حاول لاحقاً.")
            clear_session(uid)
            await menu_fn()
            return
        await send_fn("✅ تم حذف الدعوات المعلقة.")

    set_session(uid, {
        "state": "awaiting_invite_phone",
        "msisdn": msisdn,
        "access_token": access_token,
        "refresh_token": user.get("refresh_token", ""),
    })
    cancel_kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("❌ إلغاء", callback_data="back_main")
    ]])
    await send_fn(
        "📲 <b>أرسل رقم الشخص الذي تريد دعوته (جيزي فقط)</b>\n\n"
        "🔹 مثال: <code>0770000000</code>\n\n"
        "❌ لإلغاء اضغط الزر أدناه:",
        reply_markup=cancel_kb
    )

async def handle_invite_phone(uid: str, text: str, sess: dict, send_fn, menu_fn):
    rl = check_rate_limit(uid)
    if rl:
        await send_fn(f"⏳ الوقت المتبقي: {format_rate_remaining(rl)}")
        return

    digits = re.sub(r'\D', '', text)
    if not re.match(r'^07\d{8}$', digits):
        await send_fn(
            "❌ الرقم غير صحيح.\n\n"
            "🔹 أرسل رقم جيزي بصيغة: <code>07xxxxxxxx</code>\n\n"
            "❌ للإلغاء: /cancel"
        )
        return

    receiver_msisdn = "213" + digits[1:]
    sender_msisdn = sess["msisdn"]
    if receiver_msisdn == sender_msisdn:
        await send_fn("❌ لا يمكنك دعوة رقمك الخاص!\n\n❌ للإلغاء: /cancel")
        return

    access_token = sess["access_token"]
    await send_fn("🔄 جاري إرسال الدعوة...")

    result = await send_invite(sender_msisdn, receiver_msisdn, access_token)
    if result == "SUCCESS":
        record_final_result(uid)
        masked = digits[:4] + "xxxx" + digits[-2:]
        await send_fn(
            f"✅ تم إرسال الدعوة بنجاح! 🎉\n\n"
            f"📲 الرقم: {masked}\n\n"
            f"⏳ انتظر قبول الدعوة للحصول على مكافأتك.\n\n"
            f"⚡ t.me/tasjilbott"
        )
        await post_activation_log({**get_user(uid) or {}, "msisdn": sender_msisdn},
                                   "MGM_INVITE", "دعوة صديق")
    elif result == "DUPLICATE":
        await send_fn("⚠️ هذا الرقم تمت دعوته مسبقاً.\n\n❌ للإلغاء: /cancel")
        return
    elif result == "NOT_DJEZZY":
        await send_fn("❌ هذا الرقم ليس جيزي.\n\n❌ للإلغاء: /cancel")
        return
    else:
        await send_fn(f"❌ فشل إرسال الدعوة ({result}). حاول مجدداً.\n\n❌ للإلغاء: /cancel")
        return

    clear_session(uid)
    await send_fn(
        "🥰 إذا أردت دعمنا:\n\n"
        "🔴 https://timebucks.com/?refID=227870531\n\n"
        "✅ سجّل بحساب جوجل فقط"
    )
    await menu_fn()

async def show_more_offers(update: Update):
    text = (
        "📦 <b>قائمة عروض الإنترنت</b>\n\n"
        "━━━━━ 📅 عروض يومية ━━━━━\n\n"
        "• 5GB — 90دج — 24ساعة\n"
        "• 300Mo — 30دج — 24ساعة\n"
        "• 600Mo — 50دج — 24ساعة\n"
        "• 2Go — 100دج — 24ساعة\n"
        "• 1Go — 50دج — 24ساعة\n"
        "• 4GB — 70دج — 24ساعة 🏷️\n"
        "• 5GB — 190دج — 24ساعة\n"
        "• 4GB — 140دج — 24ساعة\n"
        "• 1GB سريع — 40دج — 1ساعة ⚡\n\n"
        "━━━━━ 📆 عروض أسبوعية ━━━━━\n\n"
        "• 4Go — 150دج — 7أيام\n"
        "• 10Go — 300دج — 7أيام\n"
        "• 4GB — 400دج — 15يوم\n\n"
        "━━━━━ 🗓️ عروض شهرية ━━━━━\n\n"
        "• 12Go — 500دج — 30يوم\n"
        "• 30Go — 1000دج — 30يوم\n"
        "• 60Go — 1500دج — 30يوم\n"
        "• 3GB — 250دج — 30يوم\n\n"
        "━━━━━ ⭐ خاصة ━━━━━\n\n"
        "• FB غير محدود — 50دج — 4ساعات 📘\n"
        "• 1GB(FB) — 70دج — 3أيام 📘"
    )
    await update.message.reply_text(
        text,
        reply_markup=more_offers_keyboard(),
        parse_mode=ParseMode.HTML
    )

# ════════════════════════════════════════════════════════════════════════
#  CALLBACK QUERY HANDLER
# ════════════════════════════════════════════════════════════════════════
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = str(query.from_user.id)
    data = query.data or ""
    chat_id = query.message.chat_id

    if is_banned(uid) and not is_admin(int(uid)):
        await query.answer("🚫 تم حظرك.", show_alert=True)
        return

    async def send(msg: str, **kwargs):
        await context.bot.send_message(
            chat_id=chat_id, text=msg,
            parse_mode=ParseMode.HTML, **kwargs
        )

    async def edit(msg: str, kb=None):
        try:
            await query.edit_message_text(
                msg, parse_mode=ParseMode.HTML,
                reply_markup=kb
            )
        except Exception:
            await send(msg, reply_markup=kb)

    async def show_menu():
        cfg = get_match_gift_config()
        await edit(main_menu_text(cfg), main_menu_keyboard(cfg))

    # ── Subscription check ──
    if data == "check_sub":
        channels = get_sub_channels()
        if not channels or await check_subscriptions(int(uid), context):
            await query.answer("✅ تم التحقق بنجاح!")
            user = get_user(uid)
            if user and user.get("access_token"):
                cfg = get_match_gift_config()
                await edit(main_menu_text(cfg), main_menu_keyboard(cfg))
            else:
                await edit(
                    "👋 مرحباً! أرسل رقم هاتفك (جيزي) للبدء:\n"
                    "🔹 مثال: <code>0770000000</code>"
                )
        else:
            kb = build_subscription_keyboard(channels)
            await query.answer("❌ لم تشترك بعد!", show_alert=True)
        return

    # ── Main Menu items ──
    user = get_user(uid)
    sess = get_session(uid)

    if data in ("back_main", "menu"):
        if user and user.get("access_token"):
            await show_menu()
        else:
            await edit("📱 أرسل رقم هاتفك (جيزي) للبدء:\n🔹 مثال: <code>0770000000</code>")
        return

    def ensure_logged_in() -> bool:
        return bool(user and user.get("access_token"))

    if data == "menu_2g":
        if not ensure_logged_in():
            await send("⚠️ يجب تسجيل الدخول أولاً.\n\n📱 أرسل رقم هاتفك (جيزي)")
            return
        if sess.get("msisdn"):
            user["msisdn"] = sess["msisdn"]
        await activate_2g(uid, user, send, show_menu)
        return

    if data == "menu_70dz":
        if not ensure_logged_in():
            await send("⚠️ يجب تسجيل الدخول أولاً.\n\n📱 أرسل رقم هاتفك (جيزي)")
            return
        if sess.get("msisdn"):
            user["msisdn"] = sess["msisdn"]
        await activate_offer(uid, user, "BTLINTSPEEDDAY2Go", send, show_menu)
        return

    if data == "menu_invite":
        if not ensure_logged_in():
            await send("⚠️ يجب تسجيل الدخول أولاً.\n\n📱 أرسل رقم هاتفك (جيزي)")
            return
        if sess.get("msisdn"):
            user["msisdn"] = sess["msisdn"]
        await handle_invite_start(uid, user, send, show_menu)
        return

    if data == "menu_more":
        await edit(
            "📦 <b>اختر العرض المطلوب:</b>",
            more_offers_keyboard()
        )
        return

    if data == "menu_match":
        cfg = get_match_gift_config()
        if not cfg["enabled"]:
            await query.answer("⏰ هدية المباراة غير متاحة حالياً.", show_alert=True)
            return
        if not ensure_logged_in():
            await send("⚠️ يجب تسجيل الدخول أولاً.\n\n📱 أرسل رقم هاتفك (جيزي)")
            return
        if sess.get("msisdn"):
            user["msisdn"] = sess["msisdn"]
        await activate_match_gift(uid, user, send, show_menu)
        return

    if data.startswith("offer_"):
        pkg = data[6:]
        if not ensure_logged_in():
            await send("⚠️ يجب تسجيل الدخول أولاً.\n\n📱 أرسل رقم هاتفك (جيزي)")
            return
        if sess.get("msisdn"):
            user["msisdn"] = sess["msisdn"]
        offer_info = OFFERS.get(pkg, {})
        await send(
            f"📦 <b>تفعيل العرض</b>\n\n"
            f"🏷️ {offer_info.get('name', pkg)}\n"
            f"ℹ️ {offer_info.get('display', '')}\n\n"
            f"هل تريد تفعيل هذا العرض؟",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ تفعيل الآن", callback_data=f"confirm_offer_{pkg}")],
                [InlineKeyboardButton("🔙 رجوع",       callback_data="menu_more")],
            ])
        )
        return

    if data.startswith("confirm_offer_"):
        pkg = data[14:]
        if not ensure_logged_in():
            await send("⚠️ يجب تسجيل الدخول أولاً.")
            return
        if sess.get("msisdn"):
            user["msisdn"] = sess["msisdn"]
        await activate_offer(uid, user, pkg, send, show_menu)
        return

    # ══ ADMIN CALLBACKS ══
    if not is_admin(int(uid)):
        await query.answer("⛔ غير مصرح", show_alert=True)
        return

    if data == "adm_stats":
        stats = get_user_stats()
        proxies = load_proxies()
        cfg = get_match_gift_config()
        text = (
            "📊 <b>إحصائيات Tasjil BOT</b>\n\n"
            f"👥 إجمالي المستخدمين: <b>{stats['total']}</b>\n"
            f"🟢 نشط (7 أيام): <b>{stats['active_7d']}</b>\n"
            f"🟡 نشط (30 يوم): <b>{stats['active_30d']}</b>\n\n"
            f"🔗 عدد البروكسيات: <b>{len(proxies)}</b>\n"
            f"🎁 هدية المباراة: <b>{'✅ مفعّلة' if cfg['enabled'] else '❌ معطلة'}</b>\n\n"
            f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        await edit(text, InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 رجوع", callback_data="adm_back")
        ]]))
        return

    if data == "adm_back":
        await edit(admin_menu_text(), admin_main_keyboard())
        return

    if data == "adm_broadcast":
        stats = get_user_stats()
        await edit(
            f"📢 <b>إرسال إعلان</b>\n\n"
            f"👥 إجمالي: {stats['total']}\n"
            f"🟢 نشطين (7أيام): {stats['active_7d']}\n\n"
            f"اختر الجمهور:",
            InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(f"📢 الكل ({stats['total']})",
                                         callback_data="adm_bc_all"),
                    InlineKeyboardButton(f"✅ النشطين ({stats['active_7d']})",
                                         callback_data="adm_bc_active"),
                ],
                [InlineKeyboardButton("❌ إلغاء", callback_data="adm_back")],
            ])
        )
        return

    if data in ("adm_bc_all", "adm_bc_active"):
        target = "all" if data == "adm_bc_all" else "active_7d"
        context.user_data["admin_state"] = "awaiting_broadcast"
        context.user_data["broadcast_target"] = target
        await send(
            f"📝 أرسل نص الإعلان للـ "
            f"{'<b>جميع المستخدمين</b>' if target == 'all' else '<b>النشطين (7أيام)</b>'}:\n\n"
            f"/cancel للإلغاء"
        )
        return

    if data == "adm_proxies":
        proxies = load_proxies()
        lines = [f"🔗 <b>البروكسيات ({len(proxies)})</b>\n"]
        for i, p in enumerate(proxies[:20]):
            pp = parse_proxy(p)
            lines.append(f"{i+1}. <code>{pp['host']}</code>")
        if len(proxies) > 20:
            lines.append(f"... و {len(proxies)-20} أخرى")
        await edit(
            "\n".join(lines),
            InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 تحديث API",     callback_data="adm_refresh_proxy"),
                    InlineKeyboardButton("➕ إضافة",          callback_data="adm_addproxy"),
                ],
                [InlineKeyboardButton("🔙 رجوع", callback_data="adm_back")],
            ])
        )
        return

    if data == "adm_addproxy":
        context.user_data["admin_state"] = "awaiting_proxies"
        await send(
            "📝 <b>إضافة بروكسيات جديدة</b>\n\n"
            "أرسل قائمة البروكسيات، كل بروكسي في سطر:\n"
            "<code>https://host:port:user:pass</code>\n\n"
            "⚠️ ستُستبدل القائمة الحالية.\n/cancel للإلغاء"
        )
        return

    if data == "adm_refresh_proxy":
        await send("🔄 جاري تحديث البروكسيات من API...")
        proxies = await refresh_proxies_from_api()
        await send(f"✅ تم تحديث البروكسيات: <b>{len(proxies)}</b> بروكسي.")
        await context.bot.send_message(
            chat_id=chat_id, text=admin_menu_text(),
            reply_markup=admin_main_keyboard(),
            parse_mode=ParseMode.HTML
        )
        return

    if data == "adm_toggle_match":
        cfg = get_match_gift_config()
        cfg["enabled"] = not cfg["enabled"]
        save_match_gift_config(cfg)
        status = "✅ مفعّلة" if cfg["enabled"] else "❌ معطلة"
        await send(f"🎁 هدية المباراة الآن: <b>{status}</b>")
        await edit(admin_menu_text(), admin_main_keyboard())
        return

    if data == "adm_set_qr":
        cfg = get_match_gift_config()
        context.user_data["admin_state"] = "awaiting_qr"
        await send(
            f"✏️ QR الحالي:\n<code>{cfg['qr_code']}</code>\n\n"
            f"أرسل الـ QR Code الجديد:\n/cancel للإلغاء"
        )
        return

    if data == "adm_ban":
        context.user_data["admin_state"] = "awaiting_ban_id"
        await send("🚫 أرسل ID المستخدم للحظر:\n/cancel للإلغاء")
        return

    if data == "adm_unban":
        context.user_data["admin_state"] = "awaiting_unban_id"
        await send("✅ أرسل ID المستخدم لفك الحظر:\n/cancel للإلغاء")
        return

    if data == "adm_channels":
        channels = get_sub_channels()
        ch_text = "\n".join([f"• {c}" for c in channels]) if channels else "لا توجد قنوات"
        await edit(
            f"📡 <b>القنوات الإلزامية</b>\n\n{ch_text}\n\n"
            f"اختر:",
            InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ إضافة قناة",  callback_data="adm_add_channel")],
                [InlineKeyboardButton("🗑️ حذف قناة",   callback_data="adm_del_channel")],
                [InlineKeyboardButton("🔙 رجوع",        callback_data="adm_back")],
            ])
        )
        return

    if data == "adm_add_channel":
        context.user_data["admin_state"] = "awaiting_channel"
        await send("📡 أرسل username القناة:\nمثال: <code>@mychannel</code>\n/cancel للإلغاء")
        return

    if data == "adm_del_channel":
        channels = get_sub_channels()
        if not channels:
            await query.answer("لا توجد قنوات لحذفها", show_alert=True)
            return
        rows = [[InlineKeyboardButton(f"🗑️ {c}", callback_data=f"del_ch_{c}")] for c in channels]
        rows.append([InlineKeyboardButton("🔙 رجوع", callback_data="adm_channels")])
        await edit("اختر القناة للحذف:", InlineKeyboardMarkup(rows))
        return

    if data.startswith("del_ch_"):
        ch = data[7:]
        channels = get_sub_channels()
        channels = [c for c in channels if c != ch]
        save_sub_channels(channels)
        await query.answer(f"✅ تم حذف {ch}", show_alert=True)
        await edit(admin_menu_text(), admin_main_keyboard())
        return

    if data == "adm_admins":
        admins = get_admins()
        admin_list = "\n".join([f"• <code>{uid}</code> — {info.get('name', 'بدون اسم')}"
                                for uid, info in admins.items()]) or "لا يوجد إداريون إضافيون"
        await edit(
            f"👥 <b>الإداريون</b>\n\n{admin_list}\n\n"
            f"👑 الإداري الرئيسي: 8499896271",
            InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ إضافة إداري",  callback_data="adm_add_admin")],
                [InlineKeyboardButton("🗑️ حذف إداري",   callback_data="adm_remove_admin")],
                [InlineKeyboardButton("🔙 رجوع",         callback_data="adm_back")],
            ])
        )
        return

    if data == "adm_add_admin":
        context.user_data["admin_state"] = "awaiting_admin_id"
        await send("👤 أرسل ID الإداري الجديد:\n/cancel للإلغاء")
        return

    if data == "adm_remove_admin":
        context.user_data["admin_state"] = "awaiting_remove_admin_id"
        await send("👤 أرسل ID الإداري للحذف:\n/cancel للإلغاء")
        return

    if data.startswith("adm_confirm_bc_"):
        bc_id = data[15:]
        await execute_broadcast(uid, bc_id, context, send)
        return

# ════════════════════════════════════════════════════════════════════════
#  ADMIN TEXT HANDLER
# ════════════════════════════════════════════════════════════════════════
async def handle_admin_text(update: Update, context: ContextTypes.DEFAULT_TYPE,
                             uid: str, text: str, admin_state: str):
    chat_id = update.effective_chat.id

    async def send(msg: str, **kwargs):
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML, **kwargs)

    if text.lower() == "/cancel":
        context.user_data.pop("admin_state", None)
        context.user_data.pop("broadcast_target", None)
        await send("❌ تم الإلغاء.")
        await context.bot.send_message(
            chat_id=chat_id, text=admin_menu_text(),
            reply_markup=admin_main_keyboard(),
            parse_mode=ParseMode.HTML
        )
        return

    if admin_state == "awaiting_broadcast":
        target = context.user_data.get("broadcast_target", "all")
        bc_id = f"bc_{int(time.time())}_{hashlib.md5(text.encode()).hexdigest()[:6]}"
        users = get_all_users() if target == "all" else get_active_users(7)
        user_count = len(users)

        context.user_data["pending_broadcast"] = {
            "id": bc_id, "target": target, "message": text, "users": users
        }
        context.user_data.pop("admin_state", None)

        preview = (
            f"📢 <b>معاينة الإعلان</b>\n\n"
            f"🎯 المستهدفون: <b>{user_count} مستخدم</b>\n"
            f"🆔 معرف: <code>{bc_id}</code>\n\n"
            f"━━━━━━━━━━━━━━\n"
            f"{text}\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"⚠️ هل تريد إرسال هذا الإعلان؟"
        )
        await send(preview, reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(f"✅ إرسال ({user_count})",
                                     callback_data=f"adm_confirm_bc_{bc_id}"),
                InlineKeyboardButton("❌ إلغاء", callback_data="adm_back"),
            ]
        ]))
        return

    if admin_state == "awaiting_proxies":
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        # محاولة JSON
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                lines = parsed
        except Exception:
            pass
        valid = [l for l in lines if re.match(r'^https?://', l) or ':' in l]
        if not valid:
            await send("❌ لا توجد بروكسيات صالحة. الصيغة: https://host:port:user:pass")
            return
        save_proxies(valid)
        context.user_data.pop("admin_state", None)
        await send(f"✅ تم حفظ <b>{len(valid)}</b> بروكسي بنجاح!")
        await context.bot.send_message(
            chat_id=chat_id, text=admin_menu_text(),
            reply_markup=admin_main_keyboard(), parse_mode=ParseMode.HTML
        )
        return

    if admin_state == "awaiting_qr":
        cfg = get_match_gift_config()
        cfg["qr_code"] = text.strip()
        save_match_gift_config(cfg)
        context.user_data.pop("admin_state", None)
        await send(f"✅ تم تحديث QR Code:\n<code>{cfg['qr_code']}</code>")
        await context.bot.send_message(
            chat_id=chat_id, text=admin_menu_text(),
            reply_markup=admin_main_keyboard(), parse_mode=ParseMode.HTML
        )
        return

    if admin_state == "awaiting_ban_id":
        target_id = text.strip()
        ban_user(target_id)
        context.user_data.pop("admin_state", None)
        await send(f"🚫 تم حظر المستخدم: <code>{target_id}</code>")
        # إشعار الإداريين
        await notify_admins(context,
                            f"🚫 تم حظر مستخدم\n🆔 ID: {target_id}\n👤 بواسطة: {uid}")
        await context.bot.send_message(
            chat_id=chat_id, text=admin_menu_text(),
            reply_markup=admin_main_keyboard(), parse_mode=ParseMode.HTML
        )
        return

    if admin_state == "awaiting_unban_id":
        target_id = text.strip()
        unban_user(target_id)
        context.user_data.pop("admin_state", None)
        await send(f"✅ تم فك الحظر عن: <code>{target_id}</code>")
        await notify_admins(context,
                            f"✅ فك حظر مستخدم\n🆔 ID: {target_id}\n👤 بواسطة: {uid}")
        await context.bot.send_message(
            chat_id=chat_id, text=admin_menu_text(),
            reply_markup=admin_main_keyboard(), parse_mode=ParseMode.HTML
        )
        return

    if admin_state == "awaiting_channel":
        ch = text.strip()
        if not ch.startswith("@"):
            ch = "@" + ch
        channels = get_sub_channels()
        if ch not in channels:
            channels.append(ch)
            save_sub_channels(channels)
        context.user_data.pop("admin_state", None)
        await send(f"✅ تمت إضافة القناة: <code>{ch}</code>")
        await context.bot.send_message(
            chat_id=chat_id, text=admin_menu_text(),
            reply_markup=admin_main_keyboard(), parse_mode=ParseMode.HTML
        )
        return

    if admin_state == "awaiting_admin_id":
        new_admin_id = text.strip()
        add_admin(new_admin_id, {"name": "إداري جديد", "added_by": uid,
                                  "added_at": int(time.time())})
        context.user_data.pop("admin_state", None)
        await send(f"✅ تمت إضافة الإداري: <code>{new_admin_id}</code>")
        await notify_admins(context,
                            f"👤 إداري جديد تمت إضافته\n🆔 ID: {new_admin_id}\n👤 بواسطة: {uid}")
        await context.bot.send_message(
            chat_id=chat_id, text=admin_menu_text(),
            reply_markup=admin_main_keyboard(), parse_mode=ParseMode.HTML
        )
        return

    if admin_state == "awaiting_remove_admin_id":
        target_id = text.strip()
        remove_admin(target_id)
        context.user_data.pop("admin_state", None)
        await send(f"✅ تم حذف الإداري: <code>{target_id}</code>")
        await context.bot.send_message(
            chat_id=chat_id, text=admin_menu_text(),
            reply_markup=admin_main_keyboard(), parse_mode=ParseMode.HTML
        )
        return

async def execute_broadcast(uid: str, bc_id: str,
                             context: ContextTypes.DEFAULT_TYPE, send_fn):
    pending = context.user_data.pop("pending_broadcast", None)
    if not pending or pending["id"] != bc_id:
        await send_fn("❌ معرف البث غير متطابق.")
        return

    users    = pending["users"]
    msg_text = pending["message"]
    chat_id  = None

    for admin_id in ADMIN_IDS:
        chat_id = admin_id
        break
    for a in get_admins():
        chat_id = int(a)
        break

    await send_fn(f"🚀 جاري الإرسال لـ <b>{len(users)}</b> مستخدم...")

    sent = 0; failed = 0; skipped = 0
    for u_id in users:
        if was_broadcast_sent(bc_id, u_id):
            skipped += 1
            continue
        try:
            await context.bot.send_message(
                chat_id=int(u_id),
                text=f"📢 <b>إعلان:</b>\n\n{msg_text}",
                parse_mode=ParseMode.HTML
            )
            mark_broadcast_sent(bc_id, u_id)
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.08)

    summary = (
        f"✅ <b>اكتمل الإعلان</b>\n\n"
        f"📤 مُرسَل: <b>{sent}</b>\n"
        f"❌ فشل: <b>{failed}</b>\n"
        f"⏭️ تخطي (سبق): <b>{skipped}</b>\n"
        f"🆔 معرف: <code>{bc_id}</code>"
    )
    await send_fn(summary)
    await notify_admins(context,
                        f"📢 بث منجز\n📤 أُرسل: {sent}\n❌ فشل: {failed}\n👤 بواسطة: {uid}")

async def notify_admins(context: ContextTypes.DEFAULT_TYPE, msg: str):
    """إشعار جميع الإداريين بعملية مُنجزة."""
    all_admin_ids = set(ADMIN_IDS)
    for aid in get_admins().keys():
        all_admin_ids.add(int(aid))
    for admin_id in all_admin_ids:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"🔔 <b>إشعار إداري</b>\n\n{msg}",
                parse_mode=ParseMode.HTML
            )
        except Exception:
            pass

# ════════════════════════════════════════════════════════════════════════
#  BOT MENU COMMANDS
# ════════════════════════════════════════════════════════════════════════
async def set_bot_commands(app):
    commands = [
        BotCommand("start",  "🚀 بداية البوت"),
        BotCommand("menu",   "📋 القائمة الرئيسية"),
        BotCommand("cancel", "❌ إلغاء العملية الحالية"),
        BotCommand("help",   "📖 المساعدة"),
        BotCommand("yacin",  "⚙️ لوحة الإدارة"),
    ]
    await app.bot.set_my_commands(commands)
    await app.bot.set_chat_menu_button()

# ════════════════════════════════════════════════════════════════════════
#  WEBHOOK SERVER
# ════════════════════════════════════════════════════════════════════════
async def webhook_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
    return web.Response(text="OK")

async def health_check(request: web.Request) -> web.Response:
    return web.Response(text="Tasjil BOT running ✅")

# ════════════════════════════════════════════════════════════════════════
#  APPLICATION SETUP
# ════════════════════════════════════════════════════════════════════════
application: Application = None  # global ref

def build_application() -> Application:
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .concurrent_updates(True)
        .build()
    )

    # Commands
    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("menu",   cmd_menu))
    app.add_handler(CommandHandler("cancel", cmd_cancel))
    app.add_handler(CommandHandler("help",   cmd_help))
    app.add_handler(CommandHandler("yacin",  cmd_yacin))

    # Callbacks
    app.add_handler(CallbackQueryHandler(handle_callback))

    # Text
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    return app

async def main():
    global application
    application = build_application()

    await application.initialize()
    await set_bot_commands(application)

    if WEBHOOK_URL:
        # ── Webhook mode ──
        webhook_full = WEBHOOK_URL.rstrip("/") + WEBHOOK_PATH
        await application.bot.set_webhook(
            url=webhook_full,
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True,
        )
        logger.info(f"Webhook set: {webhook_full}")

        web_app = web.Application()
        web_app.router.add_post(WEBHOOK_PATH, webhook_handler)
        web_app.router.add_get("/",            health_check)
        web_app.router.add_get("/health",      health_check)

        await application.start()
        runner = web.AppRunner(web_app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", WEBHOOK_PORT)
        await site.start()
        logger.info(f"Server running on port {WEBHOOK_PORT}")
        # keep alive
        while True:
            await asyncio.sleep(3600)
    else:
        # ── Polling mode (للاختبار المحلي) ──
        logger.info("Starting in polling mode (no WEBHOOK_URL set)")
        await application.bot.delete_webhook(drop_pending_updates=True)
        await application.start()
        await application.updater.start_polling(
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True,
        )
        logger.info("Bot polling started. Press Ctrl+C to stop.")
        await application.updater.idle()

if __name__ == "__main__":
    asyncio.run(main())

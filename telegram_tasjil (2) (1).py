#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║  ⚡ OOREDOO + DJEZZY BOT — EDITION NOIRE v7.0               ║
║  ✅ دعم أوريدو (05) + جيزي (07)                              ║
║  ✅ بروكسيات منفصلة لكل مشغل مع تبديل تلقائي                ║
║  ✅ صيانة مستقلة لكل مشغل                                    ║
║  ✅ إعادة محاولة x3 للعمليات الحساسة                         ║
║  ✅ Thread Pool + Queue لتحمل الضغط العالي                   ║
║  ✅ إصلاح None في اسم الباقة وتاريخ الانتهاء                 ║
╚══════════════════════════════════════════════════════════════╝
"""

import requests, time, re, json, threading, logging, sys
import uuid, base64, os, urllib3, queue
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlencode
from datetime import datetime, timezone
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s",
                    datefmt="%H:%M:%S")
logger = logging.getLogger("multi_bot")

# ═══════════════════════════ CONFIG ═══════════════════════════
TELEGRAM_BOT_TOKEN = "8177922042:AAGGL8lwr4o_2zxpCFVss7wbO40kb80AHM4"
TELEGRAM_API  = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
ADMIN_ID      = 8499896271
ADMIN_IDS     = [8499896271]
LOG_CHANNEL_ID = "@tasjil_bot_activation"

# ─── أوريدو ───
OOREDOO_BFF              = "https://apis.ooredoo.dz/api/ooredoo-bff"
OOREDOO_AUTH             = "https://apis.ooredoo.dz/api/auth/realms/myooredoo/protocol/openid-connect/token"
OOREDOO_CLIENT_ID        = "myooredoo-app"
OOREDOO_X_VERSION        = "1.5.17"
OOREDOO_X_SIG            = "5c7641dbb82cf11066df68afc91541c967640106a95192740b43d51a5ce6777a"
OOREDOO_PLATFORM         = "android"
OOREDOO_PLATFORM_ORIGIN  = "mobile-android"

OOREDOO_INTEGRITY_1 = "JWBTpxXcH7KY9EXYeIRp8NjQMx2dt3vF8ejjoARazyoFzOw6Cu8+wkeV+zSVHSTeI6a12SG/FU+Q/9uBrcN71RlYO4CulD2x375NKwJRAInar8DVUilHBKUfjEsoHd6EwfLCfdYzLNXJu9POfEf6tqKn3PUe0pY6qZxWLhyVAFHw8Qwb52ZqdI2soCH4S3mrz+OZL+YovdGSUKlXKIkxVroAMTAg3jljLF7gvXaEsB/O3uW+tbkBMwSX2uTOwf+rh3sgOF/zPhKCFgRvZmU1o87Fa96Y/+wOcK+UpfXTCBYVrvQ1wG6ryC7vHMSqgUhYJK4tbSoti0zv4av9pwxh9Iv2MgsMENjyKBK/TuFZxEG3xQCKj1LTMgn2xBEeKcbsKrEW3xDRwsccGI3D7GHnbUlhdI4ujDIRQVKHaZSwhTp+32Cr4EB/Qt8p/xRbdgCde9MUlM4AYIGlfyVoHSkOvTu5c0DIIy1EhowtAkbKIJl49wsYKWvpT/nXFWzeXP3R2qzaclCnIb9qihhrarmwz8l8XH2T+f7AK2uSNiuWLG5Fy2mM/YLmuJPZT9Ciag/mpy7JGImKNQAcFbSAInBdKQjUKT+COzZfrXj5rwil9/HDMtuzIovq8hrQGY+roTfVPheTLWmcjkVCOL8VXAHjPb22vOuqrkMioWT9CQ5O8RgW7RKHrObeKQMp8F7tSjOqkxYDFkPVN1G4nkEBrTlPKK9YtPl+j7IuH9fGcDTwhCTTqP8peuBryW0L11tApvAEi7VkJyBxpVxW"
OOREDOO_INTEGRITY_2 = "JWBTpxXcH7KR/kzaHeUUydDWODuU4i3H4fL9gCgKzyYfyN4qLJJE8keV+zSVHSTeI6aEyC2tbSza/NGmkflQ/UgaNZSN9SKxz7tcdQckHY25n6mOaDZ9PPMQmF4sKZqDwebce/c1SNGNn6qvTULW/L348aJvy7Vii6dyPTu3OSPV9AwKwGwQKNHN61HyK3jx/fa8Os5ux9u3Q654YLZrAJ99QGEm/C9nEBPmlHC98RjovLGBnuJOGx6k7fnyrt/Ogy5fNg+tBgi5HEsoXDAwutX7TOWfx4YKHpKW//TvPRQgp69e2Xqa+CvGJJ+a/WlPMPhRCSsfo0OG04mVvlkc8eXiLzV/GPuJCEmcRf9Z6V+xoDyMtU7OZ3XT5BMhI/D/N68LsRn/9dIBH6X7n0WAW3tzeKZK1zENWFKrd7aLlzEdwFzO/1JTQsEDom5TRie0Kd5yic4BGvS1C1BsA2wJhzyiZ2j7RUE9m8tOAkPEIs929FYIfmH8XcCQKHT0TqT0+N+wCiyfNawPlDhZWcObscFZeEmKgvqiUFCoCj6xI1hvyHK0nu7fnZ/sGc6oNT/SrFjubYWjOyoYFL7gMnlYAhyjZhjuAwN1m1/wjwrOx8DbFr2NW8qb3hv+CIzK1zL3LDryKjqNkTxcOp4aJnmSTa73guCEmWc7pnLkLw5O8RgW7RKHrObeeQ0l9lu4HWXwlhdWRxvVMQDimhtTrGASL6sIuaxyhOkrH4HFImP70SaCoK9+euMxnzkPjg9HqPIFj+I0KSMloVxW"

# ─── جيزي ───
DJZ_CLIENT_ID     = "87pIExRhxBb3_wGsA5eSEfyATloa"
DJZ_CLIENT_SECRET = "uf82p68Bgisp8Yg1Uz8Pf6_v1XYa"
DJZ_URL_REG       = "https://apim.djezzy.dz/mobile-api/oauth2/registration"
DJZ_URL_TOKEN     = "https://apim.djezzy.dz/oauth2/token"
DJZ_URL_HIST      = "https://apim.djezzy.dz/mobile-api/api/v1/subscribers/subscription-history/{msisdn}"
DJZ_URL_ACT       = "https://apim.djezzy.dz/mobile-api/api/v1/services/walk/activate-reward/{msisdn}"
DJZ_URL_BALANCE   = "https://apim.djezzy.dz/mobile-api/api/v1/subscribers/main-balance/{msisdn}"
DJZ_URL_SUBS      = "https://apim.djezzy.dz/mobile-api/api/v1/subscribers/connected-products-balances/{msisdn}"
DJZ_PKG_CODE      = "GIFTWALKWIN2GO"
DJZ_COOLDOWN      = 7 * 24 * 3600

# ═══════════════════════════════════════════════════════
#  هدية 72 جيغا — إعدادات قابلة للتعديل من الأدمن
# ═══════════════════════════════════════════════════════
_djz_72gb_config = {
    "qr_code": "https://www.djezzy.dz/scanwin-wd26?1",
    "launch_ts": 1762041600.0,   # 2026-11-01 00:00 توقيت الجزائر (UTC+1)
}
_djz_72gb_lock = threading.Lock()

def djz_72gb_get_qr():
    with _djz_72gb_lock:
        return _djz_72gb_config["qr_code"]

def djz_72gb_set_qr(new_qr: str):
    with _djz_72gb_lock:
        _djz_72gb_config["qr_code"] = new_qr

def djz_72gb_seconds_remaining() -> float:
    """يعيد الثواني المتبقية حتى الإطلاق، 0 إذا حان الوقت"""
    import time
    return max(0.0, _djz_72gb_config["launch_ts"] - time.time())


# ═══════════════════════════════════════════════════════
#  نظام تذكير هدية جيزي الأسبوعية
# ═══════════════════════════════════════════════════════
DJZ_REMINDER_PERIOD = 7 * 24 * 3600
_djz_reminders = {}
_djz_reminders_lock = threading.Lock()

def djz_reminder_register(cid, msisdn):
    with _djz_reminders_lock:
        _djz_reminders[(cid, msisdn)] = time.time()
    logger.info(f"djz_reminder: مسجّل لـ {mask_phone(msisdn)} | cid={cid}")

def djz_reminder_cancel(cid, msisdn):
    with _djz_reminders_lock:
        _djz_reminders.pop((cid, msisdn), None)

def _djz_reminder_worker():
    logger.info("djz_reminder_worker: شغّال")
    while True:
        try:
            time.sleep(600)
            now = time.time()
            to_notify = []
            with _djz_reminders_lock:
                for key, ts in list(_djz_reminders.items()):
                    if now - ts >= DJZ_REMINDER_PERIOD:
                        to_notify.append(key)
                        del _djz_reminders[key]
            for (cid, msisdn) in to_notify:
                try:
                    msg = (
                        f"{emo('gift','🎁')} <b>تذكير — هدية جيزي جاهزة!</b>\n"
                        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
                        f"⏰ مرّت <b>7 أيام</b> منذ آخر تفعيل\n"
                        f"{emo('phone','📱')} الرقم: <code>{mask_phone(msisdn)}</code>\n\n"
                        f"{emo('check','✨')} هديتك Walk & Win <b>جاهزة الآن</b>"
                    )
                    tg_send(cid, msg,
                            inline_kb=[[ibtn("🎁 تفعيل الهدية", callback="djz_offer_2go",
                                             emoji_key="gift", color="success")],
                                       [ibtn("🏠 القائمة", callback="menu_home",
                                             emoji_key="home", color="primary")]])
                    logger.info(f"djz_reminder: أُرسل → cid={cid} | {mask_phone(msisdn)}")
                except Exception as e:
                    logger.warning(f"djz_reminder send: {e}")
        except Exception as e:
            logger.warning(f"djz_reminder_worker: {e}")

threading.Thread(target=_djz_reminder_worker, daemon=True, name="djz_reminder").start()


# ─── صور التصميم ───
WELCOME_IMAGE = "https://i.ibb.co/23r4ZGy8/file-00000000ccd481f4a938a6e2f1d8a895.png"
MENU_IMAGE    = "https://i.ibb.co/7xv5QrzG/file-00000000275881f4b46e76308e04a7d8.png"
SNAKE_IMAGE   = "https://i.ibb.co/tMdpTjmj/file-000000000ee481f48bcd0023f2162e6f.png"
OFFER_IMAGE   = "https://i.ibb.co/wrrYSB6S/file-00000000de9c81f4bc5c002bedefc6cc.png"
DJEZZY_IMAGE  = "https://i.ibb.co/yFcRPWs9/file-000000004af0820c91493c0c2737272c.png"
OO_OFFERS_IMAGE  = "https://i.ibb.co/zWKsJVdH/file-00000000d81c82438ff6b947f4ee3cd6.png"
DJZ_OFFERS_IMAGE = "https://i.ibb.co/G4CkLHBh/file-00000000ec8c81f48095a431a1abccd2.png"


# ─── إيموجيات Premium ───
EMOJI_IDS = {
    "snake":     "6221996895535896347",
    "gift":      "6312028412311508214",
    "wallet":    "5427168083074628963",
    "user":      "6165919345798026257",
    "logout":    "5938098930205069821",
    "home":      "5938093595855688024",
    "check":     "6224506517941391909",
    "cross":     "6224185666704511761",
    "time":      "5938398023137628324",
    "info":      "6222095018358740369",
    "lock":      "5938098930205069821",
    "key":       "6312028412311508214",
    "phone":     "5938027397524754858",
    "stats":     "5938398023137628324",
    "refresh":   "5967448232739999992",
    "rocket":    "6221996895535896347",
    "box":       "5967448232739999992",
    "star":      "5427168083074628963",
    "warning":   "6224185666704511761",
    "sms":       "6312028412311508214",
    "admin":     "6221996895535896347",
    "ban":       "6224185666704511761",
    "unban":     "6224506517941391909",
    "broadcast": "6312028412311508214",
    "trash":     "6222089370476746321",
    "plus":      "5861680977994060034",
    "switch":    "5938093595855688024",
    "sim":       "5938027397524754858",
    "data":      "6222095018358740369",
    "signal":    "5938398023137628324",
    "proxy":     "6222095018358740369",
    "wrench":    "5938398023137628324",
}

def emo(key, char):
    eid = EMOJI_IDS.get(key)
    return f'<tg-emoji emoji-id="{eid}">{char}</tg-emoji>' if eid else char

# ═══════════════════════════════════════════════════════════
#  PROXY MANAGER — منفصل لكل مشغل
# ═══════════════════════════════════════════════════════════
# تنسيق البروكسي: "http://user:pass@host:port" أو "http://host:port"
# اتركها فارغة [] للاتصال المباشر

_proxy_config = {
    "ooredoo": {
        "enabled": False,           # True = مفعّل | False = مباشر
        "proxies": [
            # "http://user:pass@1.2.3.4:8080",
            # "http://user:pass@5.6.7.8:8080",
        ],
        "_index": 0,
        "_lock":  threading.Lock(),
    },
    "djezzy": {
        "enabled": False,
        "proxies": [
            # "http://user:pass@9.10.11.12:8080",
        ],
        "_index": 0,
        "_lock":  threading.Lock(),
    },
}

def proxy_get_next(operator: str) -> dict | None:
    """يعيد dict جاهز لـ requests أو None للاتصال المباشر"""
    cfg = _proxy_config.get(operator, {})
    if not cfg.get("enabled") or not cfg.get("proxies"):
        return None
    with cfg["_lock"]:
        proxies = cfg["proxies"]
        if not proxies:
            return None
        idx = cfg["_index"] % len(proxies)
        cfg["_index"] += 1
        url = proxies[idx]
    # تحقق من صحة الـ URL — يجب أن يبدأ بـ http:// أو socks5://
    if not url or not (url.startswith("http://") or url.startswith("https://") or url.startswith("socks5://")):
        logger.warning(f"proxy_get_next [{operator}]: invalid proxy URL skipped: {url!r}")
        return None
    # تحقق أن الـ host ليس مجرد أرقام (خطأ تنسيق)
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if not parsed.hostname or not parsed.port:
            logger.warning(f"proxy_get_next [{operator}]: proxy missing host/port: {url!r}")
            return None
    except Exception:
        return None
    return {"http": url, "https": url}

def proxy_set_list(operator: str, proxy_list: list):
    """يحدّث قائمة البروكسيات — يستخدمها الأدمن"""
    cfg = _proxy_config.get(operator)
    if not cfg: return
    with cfg["_lock"]:
        cfg["proxies"] = [p.strip() for p in proxy_list if p.strip()]
        cfg["_index"] = 0

def proxy_toggle(operator: str, enabled: bool):
    cfg = _proxy_config.get(operator)
    if cfg: cfg["enabled"] = enabled

def proxy_status_text() -> str:
    lines = [f"{emo('proxy','🌐')} <b>حالة البروكسيات</b>\n<b>━━━━━━━━━━━━━━━━━━━━━</b>"]
    for op, cfg in _proxy_config.items():
        state  = "✅ مفعّل" if cfg["enabled"] else "⛔ معطّل (مباشر)"
        count  = len(cfg.get("proxies", []))
        label  = "🔴 أوريدو" if op == "ooredoo" else "🟡 جيزي"
        lines.append(f"\n{label}\n  الحالة: <b>{state}</b>\n  عدد البروكسيات: <b>{count}</b>")
    return "\n".join(lines)

# ═══════════════════════════════════════════════════════════
#  HTTP SESSIONS — pool ضخم للضغط العالي
# ═══════════════════════════════════════════════════════════
def _make_session(pool_conn=100, pool_max=300):
    s = requests.Session()
    adapter = HTTPAdapter(
        pool_connections=pool_conn,
        pool_maxsize=pool_max,
        max_retries=Retry(total=1, connect=1, read=1, backoff_factor=0.1,
                          status_forcelist=(502, 503, 504)),
        pool_block=False,
    )
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    s.headers.update({"Accept-Encoding": "gzip, deflate", "Connection": "keep-alive"})
    return s

_oo_session = _make_session(pool_conn=80, pool_max=200)
_dz_session = _make_session(pool_conn=80, pool_max=200)
_tg_session = _make_session(pool_conn=50, pool_max=150)

# Thread pool للمهام الثقيلة — يمنع تشبع threads الـ daemon
_worker_pool = ThreadPoolExecutor(max_workers=200, thread_name_prefix="bot_worker")

def submit_task(fn, *args, **kwargs):
    """يرسل مهمة إلى pool بدلاً من daemon thread مباشر"""
    _worker_pool.submit(fn, *args, **kwargs)

# ═══════════════════════════ DATA STORE ═══════════════════════════
DATA_FILE = "bot_data.json"
_lock, _save_lock = threading.Lock(), threading.Lock()
_save_pending = {"flag": False}

_users, _sessions = {}, {}
_forced_channels = [
    {"id": "@tasjilbott",             "url": "https://t.me/tasjilbott"},
    {"id": "@tasjilapp",              "url": "https://t.me/tasjilapp"},
    {"id": "@tasjil_bot_activation",  "url": "https://t.me/tasjil_bot_activation"},
]
_bot_stats = {"users": 0, "activations": 0}

# _maintenance per-operator + global
# {
#   "global": False,       ← يوقف كل شيء
#   "ooredoo": False,      ← يوقف أوريدو فقط
#   "djezzy": False,       ← يوقف جيزي فقط
# }
_maintenance = {"global": False, "ooredoo": False, "djezzy": False}

_otp_cooldown, _otp_cooldown_lock = {}, threading.Lock()
_user_locks, _user_locks_guard = {}, threading.Lock()

def _get_user_lock(cid):
    with _user_locks_guard:
        if cid not in _user_locks:
            _user_locks[cid] = threading.Lock()
        return _user_locks[cid]

def _check_otp_cooldown(cid):
    now = time.time()
    with _otp_cooldown_lock:
        last = _otp_cooldown.get(cid, 0)
        if now - last < 60:
            return int(60 - (now - last))
        _otp_cooldown[cid] = now
    return 0

def is_in_maintenance(operator: str | None = None) -> bool:
    """True إذا كان البوت أو المشغل المحدد في صيانة"""
    if _maintenance.get("global"): return True
    if operator and _maintenance.get(operator): return True
    return False

def maintenance_status_text() -> str:
    g  = "🔴 مفعّل" if _maintenance.get("global")  else "🟢 إيقاف"
    oo = "🔴 مفعّل" if _maintenance.get("ooredoo") else "🟢 إيقاف"
    dj = "🔴 مفعّل" if _maintenance.get("djezzy")  else "🟢 إيقاف"
    return (
        f"{emo('wrench','🔧')} <b>حالة الصيانة</b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
        f"🌐 الكل: <b>{g}</b>\n"
        f"🔴 أوريدو: <b>{oo}</b>\n"
        f"🟡 جيزي:  <b>{dj}</b>"
    )

def _do_save():
    with _save_lock:
        try:
            data = {
                "users":       {str(k): v for k, v in _users.items()},
                "channels":    _forced_channels,
                "stats":       _bot_stats,
                "maintenance": _maintenance,
                "proxy_config": {
                    op: {"enabled": cfg["enabled"], "proxies": cfg["proxies"]}
                    for op, cfg in _proxy_config.items()
                },
            }
            tmp = DATA_FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
            os.replace(tmp, DATA_FILE)
            _save_pending["flag"] = False
        except Exception as e:
            logger.warning(f"save: {e}")

def _save_async():
    if _save_pending["flag"]: return
    _save_pending["flag"] = True
    def _d(): time.sleep(2); _do_save()
    threading.Thread(target=_d, daemon=True).start()

def _load_from_disk():
    global _users, _forced_channels, _bot_stats, _maintenance
    if not os.path.exists(DATA_FILE): return
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        raw = data.get("users", {})
        for k, v in raw.items():
            cid = int(k)
            if "phones" not in v and v.get("msisdn"):
                msisdn = v["msisdn"]
                op = v.get("operator", "ooredoo")
                v["phones"] = {
                    msisdn: {
                        "operator": op,
                        "access_token":  v.get("access_token", ""),
                        "refresh_token": v.get("refresh_token", ""),
                        "tok_timestamp":   v.get("tok_timestamp"),
                        "tok_instance_id": v.get("tok_instance_id"),
                        "tok_plat_sig":    v.get("tok_plat_sig"),
                        "tok_correlation": v.get("tok_correlation"),
                    }
                }
                v["active_phone"] = msisdn
            _users[cid] = v
        _forced_channels = data.get("channels", [])
        _bot_stats = data.get("stats", {"users": 0, "activations": 0})

        # تحميل الصيانة — دعم الصيغة القديمة (bool) والجديدة (dict)
        saved_maint = data.get("maintenance", False)
        if isinstance(saved_maint, bool):
            _maintenance = {"global": saved_maint, "ooredoo": False, "djezzy": False}
        elif isinstance(saved_maint, dict):
            _maintenance = {**{"global": False, "ooredoo": False, "djezzy": False}, **saved_maint}

        # تحميل إعدادات البروكسي
        saved_proxy = data.get("proxy_config", {})
        for op, pcfg in saved_proxy.items():
            if op in _proxy_config:
                _proxy_config[op]["enabled"] = pcfg.get("enabled", False)
                _proxy_config[op]["proxies"] = pcfg.get("proxies", [])

        logger.info(f"✅ Loaded {len(_users)} users")
    except Exception as e:
        logger.warning(f"load: {e}")

# ═══════════════════════════ USER HELPERS ═══════════════════════════
def oo_get_user(cid):
    with _lock:
        return dict(_users.get(cid)) if _users.get(cid) else None

def _get_active_phone_data(cid):
    u = oo_get_user(cid)
    if not u: return None, None
    ap = u.get("active_phone")
    phones = u.get("phones", {})
    if ap and ap in phones:
        return ap, dict(phones[ap])
    if phones:
        k = next(iter(phones))
        return k, dict(phones[k])
    return None, None

def oo_save_base(cid, base_data):
    with _lock:
        if cid not in _users:
            _users[cid] = {"phones": {}}; _bot_stats["users"] += 1
        changed = False
        for k, v in base_data.items():
            if v is not None and _users[cid].get(k) != v:
                _users[cid][k] = v; changed = True
    if changed: _save_async()

def oo_save_phone(cid, msisdn, phone_data):
    with _lock:
        if cid not in _users:
            _users[cid] = {"phones": {}}; _bot_stats["users"] += 1
        if "phones" not in _users[cid]:
            _users[cid]["phones"] = {}
        existing = _users[cid]["phones"].get(msisdn, {})
        existing.update({k: v for k, v in phone_data.items() if v is not None})
        _users[cid]["phones"][msisdn] = existing
        _users[cid]["active_phone"] = msisdn
    _save_async()

def oo_delete_phone(cid, msisdn):
    with _lock:
        if cid not in _users: return
        _users[cid].get("phones", {}).pop(msisdn, None)
        phones = _users[cid].get("phones", {})
        if _users[cid].get("active_phone") == msisdn:
            _users[cid]["active_phone"] = next(iter(phones), None)
    _save_async()
    try: djz_reminder_cancel(cid, msisdn)
    except: pass

def oo_set_active_phone(cid, msisdn):
    with _lock:
        if cid not in _users: return
        _users[cid]["active_phone"] = msisdn
    _save_async()

def oo_delete_user(cid):
    with _lock: _users.pop(cid, None)
    _save_async()

def oo_get_session(cid):
    with _lock: return dict(_sessions.get(cid)) if _sessions.get(cid) else {}

def oo_set_session(cid, data):
    with _lock:
        if cid not in _sessions: _sessions[cid] = {}
        _sessions[cid].update({k: v for k, v in data.items() if v is not None})

def oo_clear_session(cid):
    with _lock: _sessions.pop(cid, None)

def oo_now_ms():  return str(int(time.time() * 1000))
def oo_new_iid():
    u = uuid.uuid4().hex
    return f"{u[:8]}-{u[8:12]}-11{u[12:16]}-{u[16:20]}-{u[20:32]}{oo_now_ms()}"
def oo_new_psig(iid):
    p = json.dumps({"platform": "android", "is-physical-device": True, "device-id": iid},
                   separators=(",", ":"))
    return base64.b64encode(p.encode()).decode()
def oo_new_corr(): return uuid.uuid4().hex + oo_now_ms()
def oo_new_fp():   return uuid.uuid4().hex + uuid.uuid4().hex[:32]
def oo_get_device(_cid=None):
    iid = oo_new_iid()
    return {"instance_id": iid, "plat_sig": oo_new_psig(iid)}
def oo_decode_jwt(token):
    if not token: return {}
    try:
        p = token.split(".")[1]; p += "=" * (-len(p) % 4)
        return json.loads(base64.urlsafe_b64decode(p))
    except: return {}
def oo_extract_did(token): return oo_decode_jwt(token).get("device-id")

def oo_format_size(val, unit):
    try:
        v = float(val); u = str(unit).upper()
        if u in ("GB", "GO"): return f"{int(v) if v.is_integer() else v} Go"
        if u in ("MB", "MO"):
            return f"{round(v/1024, 2)} Go" if v >= 1024 else f"{int(v)} Mo"
        return f"{val} {unit}"
    except: return f"{val} {unit}"

def mask_phone(m):
    if not m: return "—"
    s = str(m).strip()
    if s.startswith("213") and len(s) == 12: s = "0" + s[3:]
    return s[:2] + "x" * (len(s) - 4) + s[-2:] if len(s) >= 8 else s

def get_user_display(cid):
    u = oo_get_user(cid) or {}
    return f"@{u['username']}" if u.get("username") else u.get("first_name") or "غير معروف"

def is_admin(cid): return cid in ADMIN_IDS
def op_label(op): return "🔴 أوريدو" if op == "ooredoo" else "🟡 جيزي"

# ═══════════════════════════ HTTP WITH PROXY ═══════════════════════════
def _get_session_for(operator: str):
    return _oo_session if operator == "ooredoo" else _dz_session

def oo_http(method, url, headers, body="", timeout=6, operator="ooredoo"):
    sess   = _get_session_for(operator)
    proxy  = proxy_get_next(operator)
    kwargs = dict(headers=headers, timeout=timeout, verify=False)
    if proxy:
        kwargs["proxies"] = proxy
        logger.debug(f"oo_http [{operator}] using proxy: {proxy}")
    else:
        logger.debug(f"oo_http [{operator}] direct connection (no proxy)")
    logger.debug(f"oo_http → {method} {url} | body={str(body)[:200]}")
    try:
        if method == "GET":
            r = sess.get(url, **kwargs)
        else:
            ct = headers.get("content-type", headers.get("Content-Type", ""))
            if "application/json" in ct and isinstance(body, str):
                r = sess.post(url, data=body.encode("utf-8"), **kwargs)
            else:
                r = sess.post(url, data=body, **kwargs)
        txt = r.text
        logger.debug(f"oo_http ← {r.status_code} | body={txt[:300]}")
        if "Request Rejected" in txt or "support id" in txt.lower():
            logger.warning(f"oo_http: IP blocked detected [{operator}]")
            return {"ip_blocked": True, "code": r.status_code}
        try: j = r.json()
        except: j = None
        return {"code": r.status_code, "body": txt,
                "headers": {k.lower(): v for k, v in r.headers.items()}, "json": j}
    except Exception as e:
        logger.warning(f"http err [{operator}]: {e}"); return None

def djz_http_get(url, headers, params=None, timeout=15):
    proxy  = proxy_get_next("djezzy")
    kwargs = dict(headers=headers, timeout=timeout, verify=False)
    if params: kwargs["params"] = params
    if proxy:  kwargs["proxies"] = proxy
    logger.debug(f"djz_http_get → GET {url} | params={params}")
    try:
        r = _dz_session.get(url, **kwargs)
        logger.debug(f"djz_http_get ← {r.status_code} | body={r.text[:300]}")
        return r
    except Exception as e:
        logger.warning(f"djz_http_get exception: {e}"); return None

def djz_http_post(url, headers, data=None, json_data=None, params=None, timeout=20):
    proxy  = proxy_get_next("djezzy")
    kwargs = dict(headers=headers, timeout=timeout, verify=False)
    if data:      kwargs["data"]   = data
    if json_data: kwargs["json"]   = json_data
    if params:    kwargs["params"] = params
    if proxy:     kwargs["proxies"] = proxy
    _log_body = str(data or json_data or "")[:200]
    logger.debug(f"djz_http_post → POST {url} | body={_log_body}")
    try:
        r = _dz_session.post(url, **kwargs)
        logger.debug(f"djz_http_post ← {r.status_code} | body={r.text[:300]}")
        return r
    except Exception as e:
        logger.warning(f"djz_http_post exception: {e}"); return None

# ═══════════════════════════ RETRY WRAPPER ═══════════════════════════
def retry_call(fn, max_attempts=3, retry_codes=(400, 401, 500), delay=1.0):
    """
    يكرر الدالة حتى max_attempts مرة.
    fn يجب أن يعيد: True/False أو dict يحتوي success/error.
    يتوقف عند النجاح أو استنفاد المحاولات.
    """
    last_result = None
    for attempt in range(1, max_attempts + 1):
        try:
            result = fn()
            last_result = result
            # نجاح صريح
            if result is True:
                return result
            if isinstance(result, dict):
                if result.get("success") or result.get("access_token"): return result
                # فشل نهائي لا فائدة من إعادته
                if result.get("wrong_otp") or result.get("rate_limit"): return result
            # نجاح bool عادي
            if result and not isinstance(result, dict):
                return result
        except Exception as e:
            last_result = {"error": str(e)}
            logger.debug(f"retry_call attempt {attempt}/{max_attempts}: {e}")
        if attempt < max_attempts:
            time.sleep(delay * attempt)
    return last_result

# ═══════════════════════════ HEADERS ═══════════════════════════
def oo_base_h(msisdn, fp, corr, ts, iid, psig):
    return {
        "User-Agent": "Dart/3.11 (dart:io)", "Accept-Encoding": "gzip",
        "x-msisdn": msisdn, "x-device-fingerprint": fp,
        "x-platform-origin": OOREDOO_PLATFORM_ORIGIN, "x-correlation-id": corr,
        "platform": OOREDOO_PLATFORM, "x-version": OOREDOO_X_VERSION,
        "x-signature": OOREDOO_X_SIG, "x-platform-data-signature": psig,
        "x-timestamp": ts, "x-instance-id": iid,
    }

def oo_authed_h(msisdn, token, tokh):
    ts   = tokh.get("tok_timestamp")   or oo_now_ms()
    iid  = tokh.get("tok_instance_id") or oo_new_iid()
    psig = tokh.get("tok_plat_sig")    or oo_new_psig(iid)
    return {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
        "Accept-Encoding": "gzip, deflate, br",
        "x-msisdn": msisdn, "x-device-fingerprint": oo_new_fp(),
        "x-platform-origin": "web", "authorization": f"Bearer {token}",
        "x-correlation-id": oo_new_corr(), "platform": "web",
        "x-version": OOREDOO_X_VERSION, "x-signature": OOREDOO_X_SIG,
        "x-platform-data-signature": psig, "x-timestamp": ts, "x-instance-id": iid,
        "origin": "https://my.ooredoo.dz", "referer": "https://my.ooredoo.dz/",
    }

# ═══════════════════════════ OOREDOO API ═══════════════════════════
def oo_send_otp(msisdn):
    last_error = "unknown"
    for _attempt in range(2):
        try:
            iid = oo_new_iid(); psig = oo_new_psig(iid); ts = oo_now_ms()
            h3 = oo_base_h(msisdn, oo_new_fp(), oo_new_corr(), ts, iid, psig)
            h3["content-type"] = "application/json; charset=utf-8"
            h3["x-native-integrity-token"] = OOREDOO_INTEGRITY_1
            h3["x-path"]   = "/api/auth/realms/myooredoo/protocol/openid-connect/token"
            h3["x-method"] = "POST"
            r3 = oo_http("POST", f"{OOREDOO_BFF}/checkpoint/token", h3, "{}", timeout=8, operator="ooredoo")
            if not r3 or r3.get("ip_blocked"):
                last_error = "ip_blocked"; time.sleep(3); continue
            nonce   = r3["headers"].get("x-nonce-id")
            chronos = r3["headers"].get("x-chronos-id")
            if not nonce or not chronos:
                last_error = "checkpoint_failed"; time.sleep(2); continue
            h4 = {
                "User-Agent": "Dart/3.11 (dart:io)", "Accept-Encoding": "gzip",
                "x-msisdn": msisdn, "x-device-fingerprint": oo_new_fp(),
                "x-nonce-id": nonce, "x-platform-origin": OOREDOO_PLATFORM_ORIGIN,
                "platform": OOREDOO_PLATFORM, "x-version": OOREDOO_X_VERSION,
                "x-signature": OOREDOO_X_SIG, "x-chronos-id": chronos,
                "x-timestamp": ts, "x-platform-info": psig, "x-force-update": "true",
                "x-instance-id": iid, "Content-Type": "application/x-www-form-urlencoded",
            }
            b4 = urlencode({"client_id": OOREDOO_CLIENT_ID, "grant_type": "password", "username": msisdn})
            r4 = oo_http("POST", OOREDOO_AUTH, h4, b4, timeout=10, operator="ooredoo")
            if not r4: last_error = "network"; time.sleep(3); continue
            c4 = r4.get("code")
            if c4 in (401, 403, 200): return {"ok": True}
            if c4 == 429: last_error = "rate_limit"; time.sleep(5); continue
            last_error = f"http_{c4}"; time.sleep(2)
        except Exception as e:
            last_error = str(e); time.sleep(2)
    return {"error": last_error}

def oo_verify_otp(msisdn, otp, device):
    iid, psig, ts = device["instance_id"], device["plat_sig"], oo_now_ms()
    h6 = oo_base_h(msisdn, oo_new_fp(), oo_new_corr(), ts, iid, psig)
    h6["content-type"] = "application/json; charset=utf-8"
    h6["x-native-integrity-token"] = OOREDOO_INTEGRITY_2
    h6["x-path"]   = "/api/auth/realms/myooredoo/protocol/openid-connect/token"
    h6["x-method"] = "POST"
    r6 = oo_http("POST", f"{OOREDOO_BFF}/checkpoint/token", h6, "{}", timeout=6, operator="ooredoo")
    if not r6 or r6.get("ip_blocked"):
        logger.warning(f"oo_verify_otp: checkpoint فشل أو IP محجوب | r6={r6}")
        return False
    n2 = r6["headers"].get("x-nonce-id"); c2 = r6["headers"].get("x-chronos-id")
    logger.debug(f"oo_verify_otp: checkpoint OK | nonce={n2} chronos={c2}")
    if not n2 or not c2:
        logger.warning(f"oo_verify_otp: checkpoint لم يُرجع nonce/chronos | headers={r6['headers']}")
        return False
    fp7 = oo_new_fp()
    h7 = {
        "User-Agent": "Dart/3.11 (dart:io)", "Accept-Encoding": "gzip",
        "x-msisdn": msisdn, "x-device-fingerprint": fp7, "x-nonce-id": n2,
        "x-platform-origin": OOREDOO_PLATFORM_ORIGIN, "platform": OOREDOO_PLATFORM,
        "x-version": OOREDOO_X_VERSION, "x-signature": OOREDOO_X_SIG,
        "x-chronos-id": c2, "x-timestamp": ts, "x-platform-info": psig,
        "x-force-update": "true", "x-instance-id": iid,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    b7 = urlencode({"client_id": OOREDOO_CLIENT_ID, "grant_type": "password",
                    "username": msisdn, "otp": otp})
    r7 = oo_http("POST", OOREDOO_AUTH, h7, b7, timeout=8, operator="ooredoo")
    c7 = r7.get("code") if r7 else None
    logger.debug(f"oo_verify_otp: auth response code={c7} | body={r7.get('body','')[:300] if r7 else 'None'}")
    if c7 in (401, 403):
        logger.warning(f"oo_verify_otp: wrong_otp | HTTP {c7} | {r7.get('body','')[:200]}")
        return "wrong_otp"
    if c7 == 200 and r7.get("json") and "access_token" in r7["json"]:
        j = r7["json"]
        return {
            "access_token": j["access_token"], "refresh_token": j.get("refresh_token", ""),
            "tok_fingerprint": fp7, "tok_timestamp": ts,
            "tok_instance_id": oo_extract_did(j["access_token"]) or iid,
            "tok_plat_sig": psig, "tok_correlation": oo_new_corr(),
        }
    return False

def oo_login_password(msisdn, password):
    iid = oo_new_iid(); psig = oo_new_psig(iid); ts = oo_now_ms()
    h_cp = oo_base_h(msisdn, oo_new_fp(), oo_new_corr(), ts, iid, psig)
    h_cp["content-type"] = "application/json; charset=utf-8"
    h_cp["x-native-integrity-token"] = OOREDOO_INTEGRITY_2
    h_cp["x-path"]   = "/api/auth/realms/myooredoo/protocol/openid-connect/token"
    h_cp["x-method"] = "POST"
    r_cp = oo_http("POST", f"{OOREDOO_BFF}/checkpoint/token", h_cp, "{}", timeout=8, operator="ooredoo")
    if not r_cp or r_cp.get("ip_blocked"): return None
    nonce   = r_cp["headers"].get("x-nonce-id")
    chronos = r_cp["headers"].get("x-chronos-id")
    if not nonce or not chronos: return None
    h = {
        "User-Agent": "Dart/3.11 (dart:io)", "Accept-Encoding": "gzip",
        "x-msisdn": msisdn, "x-device-fingerprint": oo_new_fp(),
        "x-nonce-id": nonce, "x-platform-origin": OOREDOO_PLATFORM_ORIGIN,
        "platform": OOREDOO_PLATFORM, "x-version": OOREDOO_X_VERSION,
        "x-signature": OOREDOO_X_SIG, "x-chronos-id": chronos,
        "x-timestamp": ts, "x-platform-info": psig, "x-force-update": "true",
        "x-instance-id": iid, "Content-Type": "application/x-www-form-urlencoded",
    }
    body = urlencode({"client_id": OOREDOO_CLIENT_ID, "grant_type": "password",
                      "username": msisdn, "password": password})
    r = oo_http("POST", OOREDOO_AUTH, h, body, timeout=10, operator="ooredoo")
    if not r: return None
    if r["code"] in (401, 403): return "wrong_password"
    if r["code"] == 200 and r.get("json", {}).get("access_token"):
        j = r["json"]
        return {
            "access_token": j["access_token"], "refresh_token": j.get("refresh_token", ""),
            "tok_fingerprint": oo_new_fp(), "tok_timestamp": ts,
            "tok_instance_id": oo_extract_did(j["access_token"]) or iid,
            "tok_plat_sig": psig,
        }
    return None

def oo_refresh_token(phone_data, device):
    rt = phone_data.get("refresh_token", "")
    if not rt: return "expired"
    iid  = phone_data.get("tok_instance_id") or device["instance_id"]
    psig = phone_data.get("tok_plat_sig")    or device["plat_sig"]
    ts   = oo_now_ms()
    payload = {"grant_type": "refresh_token", "client_id": OOREDOO_CLIENT_ID, "refresh_token": rt}
    headers = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/x-www-form-urlencoded",
               "Origin": "https://my.ooredoo.dz", "Referer": "https://my.ooredoo.dz/"}
    proxy = proxy_get_next("ooredoo")
    kwargs = dict(data=payload, headers=headers, timeout=8, verify=False)
    if proxy: kwargs["proxies"] = proxy
    try:
        r = _oo_session.post(OOREDOO_AUTH, **kwargs)
        if r.status_code == 200:
            res = r.json()
            if res.get("access_token"):
                return {
                    "access_token": res["access_token"], "refresh_token": res.get("refresh_token", rt),
                    "tok_fingerprint": oo_new_fp(), "tok_timestamp": ts,
                    "tok_instance_id": oo_extract_did(res["access_token"]) or iid,
                    "tok_plat_sig": psig, "tok_correlation": oo_new_corr(),
                }
        return "expired"
    except: return False

def oo_check_session(cid, msisdn, phone_data):
    if not phone_data or not phone_data.get("access_token"): return False
    dev = oo_get_device()
    h = oo_authed_h(msisdn, phone_data["access_token"], phone_data)
    r = oo_http("GET", f"{OOREDOO_BFF}/users/validateUser?msisdn={msisdn}", h, timeout=5, operator="ooredoo")
    if r and r["code"] == 200: return True
    if r and r["code"] == 401:
        nt = oo_refresh_token(phone_data, dev)
        if isinstance(nt, dict):
            oo_save_phone(cid, msisdn, nt); return True
    return False

def _oo_auth_get(cid, msisdn, phone_data, path, timeout=5, allow_204=False):
    logger.info(f"_oo_auth_get: GET {path} | msisdn={msisdn}")
    try:
        h = oo_authed_h(msisdn, phone_data.get("access_token"), phone_data)
        r = oo_http("GET", f"{OOREDOO_BFF}{path}", h, timeout=timeout, operator="ooredoo")
        if r and r["code"] == 200:
            logger.debug(f"_oo_auth_get: ✅ 200 | json_keys={list((r.get('json') or {}).keys())}")
            return r["json"] if r.get("json") is not None else {"_empty": True}
        if r and r["code"] == 204 and allow_204: return {"_empty": True}
        if r and r["code"] == 401:
            logger.warning(f"_oo_auth_get: 401 على {path} — محاولة تجديد التوكن")
            dev = oo_get_device()
            nt  = oo_refresh_token(phone_data, dev)
            if isinstance(nt, dict):
                oo_save_phone(cid, msisdn, nt)
                phone_data.update(nt)
                h2 = oo_authed_h(msisdn, phone_data.get("access_token"), phone_data)
                r2 = oo_http("GET", f"{OOREDOO_BFF}{path}", h2, timeout=timeout, operator="ooredoo")
                if r2 and r2["code"] == 200:
                    logger.debug(f"_oo_auth_get: ✅ 200 بعد تجديد التوكن")
                    return r2["json"] if r2.get("json") is not None else {"_empty": True}
                logger.error(f"_oo_auth_get: فشل بعد تجديد التوكن | code={r2['code'] if r2 else 'None'}")
            else:
                logger.error(f"_oo_auth_get: فشل تجديد التوكن | nt={nt}")
            return {"_need_refresh": True}
        logger.warning(f"_oo_auth_get: HTTP {r['code'] if r else 'None'} على {path} | body={r.get('body','')[:200] if r else ''}")
        return None
    except Exception as e:
        logger.warning(f"auth_get exception: {e}"); return None

def oo_get_balance(cid, msisdn, pd):
    return _oo_auth_get(cid, msisdn, pd, f"/subscriptions/getAccountInfo?msisdn={msisdn}")

def oo_power_snake_status(cid, msisdn, pd):
    return _oo_auth_get(cid, msisdn, pd, "/gamification/power-snake?status=AVAILABLE", timeout=6, allow_204=True)

def oo_power_snake_redeem(msisdn, phone_data, gift_id):
    h = oo_authed_h(msisdn, phone_data.get("access_token"), phone_data)
    h["content-type"] = "application/json"
    r = oo_http("POST", f"{OOREDOO_BFF}/gamification/power-snake/{gift_id}/redeem", h, "", timeout=8, operator="ooredoo")
    if r and r["code"] == 200: return r["json"] if r.get("json") else {"success": True}
    if r and r["code"] == 401: return {"auth_error": True}
    return {"error": f"HTTP {r['code'] if r else 'net'}"}

def oo_buy_cvm(msisdn, phone_data, bundle_code):
    h = oo_authed_h(msisdn, phone_data.get("access_token"), phone_data)
    h["content-type"] = "application/json; charset=utf-8"
    payload = {"bundleCode": bundle_code}
    r = oo_http("POST", f"{OOREDOO_BFF}/cvm/dynamic-bundle-purchase", h, json.dumps(payload), timeout=10, operator="ooredoo")
    if not r: return {"error": "net"}
    code = r["code"]
    body_lower = (r.get("body") or "").lower()
    if code in (200, 201, 204): return {"success": True}
    if code == 401: return {"auth_error": True}
    if code in (400, 409, 500):
        if any(k in body_lower for k in ["already", "deja", "مسبق", "استفدت", "used", "24h"]):
            return {"error": "already_used"}
    if code == 409: return {"error": "💰 رصيد غير كافي"}
    if code == 400: return {"error": "⚠ العرض غير متاح لشريحتك"}
    if code == 500: return {"error": "already_used"}
    return {"error": f"HTTP {code}"}


def oo_buy_byop(msisdn, phone_data, payload):
    h = oo_authed_h(msisdn, phone_data.get("access_token"), phone_data)
    h["content-type"] = "application/json; charset=utf-8"
    r = oo_http("POST", f"{OOREDOO_BFF}/bundle/purchase/byop", h, json.dumps(payload), timeout=10, operator="ooredoo")
    if not r: return {"error": "net"}
    code = r["code"]
    body_lower = (r.get("body") or "").lower()
    if code in (200, 201, 204): return {"success": True}
    if code == 401: return {"auth_error": True}
    if code == 409:
        if any(k in body_lower for k in ["already", "deja", "مسبق", "used"]):
            return {"error": "already_used"}
        return {"error": "💰 رصيد غير كافي"}
    if code == 400: return {"error": "⚠ العرض غير متاح لشريحتك"}
    return {"error": f"HTTP {code}"}

def oo_buy_snapchat(msisdn, phone_data):
    h = oo_authed_h(msisdn, phone_data.get("access_token"), phone_data)
    h["content-type"] = "application/json; charset=utf-8"
    r = oo_http("POST", f"{OOREDOO_BFF}/snap-chat/apply", h, "{}", timeout=10, operator="ooredoo")
    if not r: return {"error": "net"}
    code = r["code"]
    if code in (200, 201, 204): return {"success": True}
    if code == 401: return {"auth_error": True}
    if code == 500: return {"error": "already_used"}
    return {"error": f"HTTP {code}"}

# ═══════════════════════════ DJEZZY API — مع proxy + retry ═══════════════════════
def djz_format_msisdn(phone: str) -> str:
    phone = phone.strip().replace(" ", "").replace("+", "")
    if phone.startswith("07") and len(phone) == 10:  return "213" + phone[1:]
    if phone.startswith("7")  and len(phone) == 9:   return "213" + phone
    if phone.startswith("2137") and len(phone) == 12: return phone
    return phone

def djz_send_otp(msisdn: str) -> bool:
    params  = {"msisdn": msisdn, "client_id": DJZ_CLIENT_ID, "scope": "smsotp"}
    headers = {"User-Agent": "MobileApp/3.0.9", "Accept": "application/json",
               "Content-Type": "application/json", "accept-language": "fr"}
    payload = {"consent-agreement": [{"marketing-notifications": False}], "is-consent": True}
    def _attempt():
        res = djz_http_post(DJZ_URL_REG, headers=headers, json_data=payload, params=params, timeout=20)
        if res is None: return False
        return 200 <= res.status_code < 300
    result = retry_call(_attempt, max_attempts=3, delay=2.0)
    return bool(result)

def djz_verify_otp(msisdn: str, otp_code: str) -> dict:
    headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "*/*",
               "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 6.0; PGN610 Build/MRA58K)",
               "Connection": "Keep-Alive"}
    data = {"scope": "openid", "client_id": DJZ_CLIENT_ID, "client_secret": DJZ_CLIENT_SECRET,
            "otp": otp_code, "mobileNumber": msisdn, "grant_type": "mobile"}
    def _attempt():
        res = djz_http_post(DJZ_URL_TOKEN, headers=headers, data=data, timeout=20)
        if res is None:
            logger.warning("djz_verify_otp: لا رد من السيرفر (None)")
            return {}
        logger.debug(f"djz_verify_otp: HTTP {res.status_code} | body={res.text[:300]}")
        if res.status_code == 200:
            t = res.json()
            if t.get("access_token"): return t
            logger.warning(f"djz_verify_otp: 200 بدون access_token | keys={list(t.keys())}")
        # ── FIX: جيزي يرجع 400 أو 401 أو 403 للرمز الخاطئ ──
        elif res.status_code in (400, 401, 403):
            try:
                err = res.json()
                logger.warning(f"djz_verify_otp: wrong_otp | {res.status_code} | {err}")
            except Exception:
                logger.warning(f"djz_verify_otp: wrong_otp | {res.status_code} | {res.text[:200]}")
            return {"wrong_otp": True}
        elif res.status_code == 429:
            logger.warning("djz_verify_otp: rate_limit (429)")
            return {"rate_limit": True}
        else:
            logger.error(f"djz_verify_otp: كود غير متوقع {res.status_code} | {res.text[:200]}")
        return {}
    return retry_call(_attempt, max_attempts=3, delay=1.5) or {}


def _djz_fmt_remaining(secs: float) -> str:
    """يعرض الوقت المتبقي بشكل ذكي — يحذف القيم الصفرية"""
    total = int(secs)
    d = total // 86400
    h = (total % 86400) // 3600
    m = (total % 3600) // 60
    s = total % 60
    parts = []
    if d: parts.append(f"{d} يوم" if d == 1 else f"{d} أيام")
    if h: parts.append(f"{h} ساعة")
    if m: parts.append(f"{m} دقيقة")
    if s or not parts: parts.append(f"{s} ثانية")
    return " و ".join(parts)

def djz_check_cooldown(msisdn: str, access_token: str):
    url = DJZ_URL_HIST.format(msisdn=msisdn)
    headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json",
               "User-Agent": "MobileApp/3.0.0", "Accept-Language": "fr"}
    try:
        res = djz_http_get(url, headers)
        if res is None or res.status_code != 200:
            return False, -1, "غير معروف", False
        data = res.json().get("data", [])
        latest_time = None
        for item in data:
            if item.get("packageCode") == DJZ_PKG_CODE:
                dt_str = item.get("subscriptionDateTime")
                if dt_str:
                    try:
                        parsed_dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                        if latest_time is None or parsed_dt > latest_time:
                            latest_time = parsed_dt
                    except: pass
        if latest_time is None:
            return True, 0, "جاهز للتفعيل ✨", True
        now = datetime.now(timezone.utc)
        remaining = DJZ_COOLDOWN - (now - latest_time).total_seconds()
        if remaining <= 0:
            return True, 0, "جاهز للتفعيل ✨", True
        return False, remaining, _djz_fmt_remaining(remaining), True
    except Exception as e:
        logger.debug(f"djz_cooldown: {e}")
        return False, -1, "غير معروف", False


def djz_activate_72gb(msisdn: str, access_token: str) -> dict:
    """تفعيل هدية 72 جيغا عبر scan/activate-reward"""
    url = f"https://apim.djezzy.dz/mobile-api/api/v1/services/scan/activate-reward/{msisdn}"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "Authorization": f"Bearer {access_token}",
        "User-Agent": "MobileApp/3.0.0",
        "Accept-Language": "fr",
    }
    payload = {"qrCode": djz_72gb_get_qr()}
    def _attempt():
        res = djz_http_post(url, headers=headers, json_data=payload, timeout=25)
        if res is None:
            return {"error": "network_error"}
        # نجاح
        if res.status_code in (200, 201):
            try: body = res.json()
            except: body = {}
            # تأكد أنه ليس HTML
            ct = res.headers.get("Content-Type", "")
            if "html" in ct.lower():
                return {"error": f"HTTP {res.status_code} — استجابة HTML غير متوقعة"}
            return {"success": True, "body": body}
        # توكن منتهي
        if res.status_code == 401:
            return {"token_expired": True}
        # خطأ آخر — أرسله كما هو
        try: err_body = res.json()
        except: err_body = res.text[:300]
        return {"error": f"HTTP {res.status_code}", "raw": err_body}
    return retry_call(_attempt, max_attempts=3, delay=2.0) or {"error": "فشل الاتصال"}



# ═══════════════════════════════════════════════════════
#  عروض إنترنت جيزي
# ═══════════════════════════════════════════════════════
DJZ_OFFERS = [
    # ── الأكثر شعبية 🔥 ──
    {"cat": "يومية",  "name": "5 جيغا",          "price": 90,   "dur": "24 ساعة",  "id": "BTL500MBDAY",              "type": "shake",  "hot": True},
    {"cat": "يومية",  "name": "4 جيغا",           "price": 70,   "dur": "24 ساعة",  "id": "BTLINTSPEEDDAY2Go",        "type": "shake",  "hot": True},
    {"cat": "يومية",  "name": "2 جيغا",           "price": 100,  "dur": "24 ساعة",  "id": "DOVINTSPEEDDAY1GoPRE",     "type": "normal", "hot": True},
    # ── يومية ──
    {"cat": "يومية",  "name": "300 ميغا",         "price": 30,   "dur": "24 ساعة",  "id": "DOVINTSPEEDDAY100MoPRE",   "type": "normal"},
    {"cat": "يومية",  "name": "600 ميغا",         "price": 50,   "dur": "24 ساعة",  "id": "DOVINTSPEEDDAY250MoPRE",   "type": "normal"},
    {"cat": "يومية",  "name": "1 جيغا",           "price": 50,   "dur": "24 ساعة",  "id": "OFFREJEUNE50",             "type": "shake"},
    {"cat": "يومية",  "name": "5 جيغا",           "price": 190,  "dur": "24 ساعة",  "id": "BTL4GBDAY",                "type": "shake"},
    {"cat": "يومية",  "name": "4 جيغا",           "price": 140,  "dur": "24 ساعة",  "id": "BTL1GBDAY",                "type": "shake"},
    # ── أسبوعية ──
    {"cat": "أسبوعية","name": "4 جيغا",           "price": 150,  "dur": "7 أيام",   "id": "DOVINTSPEEDWEEK2GoPRE",    "type": "normal"},
    {"cat": "أسبوعية","name": "10 جيغا",          "price": 300,  "dur": "7 أيام",   "id": "DOVINTSPEEDWEEK3GoPRE",    "type": "normal"},
    # ── 15 يوم ──
    {"cat": "15 يوم", "name": "4 جيغا",           "price": 400,  "dur": "15 يوم",   "id": "BTLDATA2WEEKS",            "type": "shake"},
    {"cat": "15 يوم", "name": "فيسبوك 1 جيغا",   "price": 70,   "dur": "3 أيام",   "id": "1GBFB3DAYInternet",        "type": "shake"},
    # ── شهرية ──
    {"cat": "شهرية",  "name": "12 جيغا",          "price": 500,  "dur": "30 يوم",   "id": "DOVINTSPEEDMONTH6GoPRE",   "type": "normal"},
    {"cat": "شهرية",  "name": "30 جيغا",          "price": 1000, "dur": "30 يوم",   "id": "DOVINTSPEEDMONTH15GoPRE",  "type": "normal"},
    {"cat": "شهرية",  "name": "60 جيغا",          "price": 1500, "dur": "30 يوم",   "id": "DOVINTSPEEDMONTH30GoPRE",  "type": "normal"},
    {"cat": "شهرية",  "name": "3 جيغا",           "price": 250,  "dur": "30 يوم",   "id": "2GBMONTH",                 "type": "shake"},
    # ── خاصة ──
    {"cat": "خاصة",   "name": "1 جيغا",           "price": 40,   "dur": "ساعة",     "id": "BTL500MBHOUR",             "type": "shake"},
    {"cat": "خاصة",   "name": "فيسبوك غير محدود", "price": 50,   "dur": "4 ساعات",  "id": "ImtiyazSurpriseData2hfbPRE","type": "shake"},
]

def _djz_offer_by_idx(idx: int) -> dict:
    try: return DJZ_OFFERS[idx]
    except: return {}

def _djz_shake_query(msisdn: str, token: str, pkg: str) -> bool:
    """يتحقق من وجود العرض في shake — يعيد True إذا وُجد"""
    url = f"https://apim.djezzy.dz/mobile-api/api/v1/services/shake/{msisdn}"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json",
               "Accept-Language": "fr", "Accept-Encoding": "gzip",
               "User-Agent": "MobileApp/3.0.9", "Content-Type": "application/json"}
    try:
        res = djz_http_get(url, headers, timeout=15)
        if res is None or res.status_code != 200: return False
        data = res.json().get("data", {})
        code = data.get("code", "")
        return code == pkg
    except: return False

def djz_activate_shake(msisdn: str, token: str, pkg: str) -> dict:
    url = f"https://apim.djezzy.dz/mobile-api/api/v1/services/shake/{msisdn}"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json",
               "Accept-Language": "fr", "Accept-Encoding": "gzip",
               "Content-Type": "application/json", "User-Agent": "MobileApp/3.0.9"}
    def _post():
        res = djz_http_post(url, headers=headers, json_data={"packageCode": pkg}, timeout=20)
        if res is None: return {"error": "network_error"}
        if res.status_code == 401: return {"token_expired": True}
        try: body = res.json()
        except: body = {}
        if res.status_code in (200, 201):
            ct = res.headers.get("Content-Type","")
            if "html" in ct.lower(): return {"error": f"HTTP {res.status_code} — HTML"}
            return {"success": True}
        if res.status_code == 404:
            # العرض غير موجود حالياً — يبدأ polling
            return {"not_found": True}
        msg_ar = ""
        if isinstance(body.get("message"), dict):
            msg_ar = body["message"].get("ar","")
        return {"error": msg_ar or f"HTTP {res.status_code}", "raw": body}
    # محاولة أولى
    result = _post()
    if not result.get("not_found"):
        return result
    # ── polling: ينتظر ظهور العرض ثم يُفعّل ──
    logger.info(f"djz_shake: 404 على {pkg} — بدء polling")
    for attempt in range(1, 21):
        time.sleep(3)
        found = _djz_shake_query(msisdn, token, pkg)
        logger.info(f"djz_shake poll {attempt}/20: found={found}")
        if found:
            # ظهر العرض — أرسل التفعيل
            result2 = _post()
            if result2.get("not_found"):
                continue   # نادر — العرض اختفى مجدداً
            return result2
    return {"error": "لم يظهر العرض بعد 20 محاولة — حاول لاحقاً"}

def djz_activate_normal(msisdn: str, token: str, pkg: str) -> dict:
    url = f"https://apim.djezzy.dz/mobile-api/api/v1/subscribers/activate-product/{msisdn}"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json",
               "Accept-Language": "fr", "Accept-Encoding": "gzip",
               "Content-Type": "application/json", "User-Agent": "MobileApp/3.0.9"}
    def _attempt():
        res = djz_http_post(url, headers=headers, json_data={"packageCode": pkg}, timeout=20)
        if res is None: return {"error": "network_error"}
        if res.status_code == 401: return {"token_expired": True}
        try: body = res.json()
        except: body = {}
        if res.status_code in (200, 201):
            ct = res.headers.get("Content-Type","")
            if "html" in ct.lower(): return {"error": f"HTTP {res.status_code} — HTML"}
            return {"success": True}
        msg_ar = ""
        balance = ""
        if isinstance(body.get("message"), dict):
            msg_ar = body["message"].get("ar","")
        if isinstance(body.get("data"), dict):
            bal = body["data"].get("mainBalance","")
            if bal != "": balance = f"\n💰 رصيدك: <b>{bal} دج</b>"
        return {"error": (msg_ar or f"HTTP {res.status_code}") + balance, "raw": body}
    return retry_call(_attempt, max_attempts=2, delay=1.5) or {"error": "فشل الاتصال"}

def djz_offers_menu(cid):
    cat_emoji = {"يومية":"☀️","أسبوعية":"📅","15 يوم":"🗓","شهرية":"📆","خاصة":"⭐"}
    lines = [f"{emo('gift','🌐')} <b>عروض الإنترنت — جيزي</b>\n<b>━━━━━━━━━━━━━━━━━━━━━</b>\n"]
    kb = []
    # ── الأكثر شعبية أولاً ──
    hot = [o for o in DJZ_OFFERS if o.get("hot")]
    if hot:
        lines.append("\n🔥 <b>الأكثر شعبية</b>")
        for o in hot:
            lines.append(f"  🔥 {o['name']} — <b>{o['price']} دج</b> | {o['dur']}")
        for o in hot:
            idx = DJZ_OFFERS.index(o)
            kb.append([ibtn(f"🔥 {o['name']} — {o['price']} دج",
                            callback=f"djz_buy:{idx}", emoji_key="gift", color="success")])
    # ── باقي الفئات ──
    cats = ["يومية","أسبوعية","15 يوم","شهرية","خاصة"]
    for cat in cats:
        offers = [o for o in DJZ_OFFERS if o["cat"] == cat and not o.get("hot")]
        if not offers: continue
        lines.append(f"\n{cat_emoji.get(cat,'📦')} <b>{cat}</b>")
        for o in offers:
            lines.append(f"  • {o['name']} — <b>{o['price']} دج</b> | {o['dur']}")
        for o in offers:
            idx = DJZ_OFFERS.index(o)
            kb.append([ibtn(f"{cat_emoji.get(cat,'')} {o['name']} — {o['price']} دج",
                            callback=f"djz_buy:{idx}", emoji_key="gift", color="primary")])
    kb.append([ibtn("🏠 رجوع", callback="menu_home", emoji_key="home", color="danger")])
    tg_send(cid, "\n".join(lines), inline_kb=kb)

def djz_buy_confirm(cid, idx: int):
    o = _djz_offer_by_idx(idx)
    if not o: return tg_send(cid, f"{emo('cross','❌')} عرض غير موجود")
    msisdn, pd = _get_active_phone_data(cid)
    if not msisdn: return
    # ── إرسال شاشة التأكيد فوراً بدون انتظار الرصيد ──
    caption = (
        f"{emo('info','💠')} <b>تأكيد الاشتراك</b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
        f"{emo('gift','📦')} العرض: <b>{o['name']}</b>\n"
        f"{emo('time','⏳')} المدة: <b>{o['dur']}</b>\n"
        f"{emo('star','💰')} السعر: <b>{o['price']} دج</b>\n\n"
        f"{emo('info','💠')} هل تريد الاشتراك؟"
    )
    msg = tg_send(cid, caption, inline_kb=[
        [ibtn("✅ تأكيد الاشتراك", callback=f"djz_confirm_buy:{idx}",
              emoji_key="check", color="success")],
        [ibtn("❌ إلغاء", callback="djz_offers_menu",
              emoji_key="cross", color="danger")],
    ])
    # ── جلب الرصيد في الخلفية وتحديث الرسالة ──
    msg_id = None
    try:
        r = msg or {}
        res_obj = r.get("result", {})
        if isinstance(res_obj, dict):
            msg_id = res_obj.get("message_id")
    except: pass
    def _fetch_bal():
        try:
            token, _ = _djz_ensure_token(cid, msisdn, pd)
            bal_res = djz_get_balance(msisdn, token)
            bal_txt = f"{bal_res['main_balance']} دج" if bal_res.get("success") else "غير متاح"
            new_cap = (
                f"{emo('info','💠')} <b>تأكيد الاشتراك</b>\n"
                f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
                f"{emo('gift','📦')} العرض: <b>{o['name']}</b>\n"
                f"{emo('time','⏳')} المدة: <b>{o['dur']}</b>\n"
                f"{emo('star','💰')} السعر: <b>{o['price']} دج</b>\n"
                f"{emo('wallet','💳')} رصيدك: <b>{bal_txt}</b>\n\n"
                f"{emo('info','💠')} هل تريد الاشتراك؟"
            )
            if msg_id:
                tg_edit(cid, msg_id, new_cap, inline_kb=[
                    [ibtn("✅ تأكيد الاشتراك", callback=f"djz_confirm_buy:{idx}",
                          emoji_key="check", color="success")],
                    [ibtn("❌ إلغاء", callback="djz_offers_menu",
                          emoji_key="cross", color="danger")],
                ])
        except: pass
    submit_task(_fetch_bal)

def djz_do_buy(cid, idx: int):
    lock = _get_user_lock(cid)
    if not lock.acquire(blocking=False): return tg_send(cid, "⏳ انتظر قليلاً...")
    try:
        o = _djz_offer_by_idx(idx)
        if not o: return tg_send(cid, f"{emo('cross','❌')} عرض غير موجود")
        msisdn, pd = _get_active_phone_data(cid)
        if not msisdn: return
        tg_send(cid, f"{emo('time','⏳')} <i>جاري الاشتراك في {o['name']}...</i>")
        token, _ = _djz_ensure_token(cid, msisdn, pd)
        if o["type"] == "shake":
            result = djz_activate_shake(msisdn, token, o["id"])
        else:
            result = djz_activate_normal(msisdn, token, o["id"])
        # توكن منتهي → تجديد
        if result.get("token_expired"):
            new_tok = djz_refresh_token(pd)
            if new_tok:
                oo_save_phone(cid, msisdn, new_tok); pd.update(new_tok)
                token = new_tok["access_token"]
                result = (djz_activate_shake(msisdn, token, o["id"])
                          if o["type"] == "shake"
                          else djz_activate_normal(msisdn, token, o["id"]))
            if result.get("token_expired") or not new_tok:
                return _djz_reauth_via_otp(cid, msisdn, pd)
        if result.get("success"):
            tg_send(cid,
                f"{emo('check','🎉')} <b>تم الاشتراك بنجاح!</b>\n"
                f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
                f"{emo('gift','📦')} <b>{o['name']}</b>\n"
                f"{emo('time','⏳')} صالح لمدة <b>{o['dur']}</b>\n"
                f"{emo('phone','📱')} الرقم: <code>{mask_phone(msisdn)}</code>",
                inline_kb=[[ibtn("🏠 رجوع", callback="menu_home",
                                 emoji_key="home", color="danger")]])
            send_activation_log(cid, msisdn, o['name'], f"{o['price']} دج", o['dur'], 'اشتراك')
        else:
            err = result.get("error","خطأ غير معروف")
            tg_send(cid,
                f"{emo('cross','❌')} <b>فشل الاشتراك</b>\n"
                f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
                f"{emo('info','💠')} {err}",
                inline_kb=[[ibtn("🔄 إعادة المحاولة", callback=f"djz_buy:{idx}",
                                 emoji_key="refresh", color="primary")],
                           [ibtn("🏠 رجوع", callback="menu_home",
                                 emoji_key="home", color="danger")]])
    finally: lock.release()


def djz_activate_2gb(msisdn: str, access_token: str) -> bool:
    url = DJZ_URL_ACT.format(msisdn=msisdn)
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json",
               "Accept": "application/json", "User-Agent": "MobileApp/3.0.0", "Accept-Language": "fr"}
    def _attempt():
        res = djz_http_post(url, headers=headers, json_data={"packageCode": DJZ_PKG_CODE}, timeout=20)
        if res is None: return False
        try: resp_json = res.json()
        except: resp_json = {}
        status = resp_json.get("status", res.status_code)
        return status == 200 or res.status_code in (200, 201)
    result = retry_call(_attempt, max_attempts=3, delay=2.0)
    return bool(result)

def djz_get_balance(msisdn: str, access_token: str) -> dict:
    """إصلاح: استخراج صحيح لاسم الباقة من subscriptionType"""
    url = DJZ_URL_BALANCE.format(msisdn=msisdn)
    params = {
        "include": ("surprise-products,subscription-type-illegibility,connected-products,"
                    "subscription-history,flash-products,supplementary-informations,available-services")
    }
    headers = {"Authorization": f"Bearer {access_token}", "Accept": "*/*",
               "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 6.0; PGN610 Build/MRA58K)"}
    logger.info(f"djz_get_balance: جلب الرصيد | msisdn={msisdn}")
    try:
        res = djz_http_get(url, headers, params=params, timeout=15)
        if res is None:
            logger.warning("djz_get_balance: لا رد من السيرفر")
            return {"success": False, "error": "network_error"}
        if res.status_code == 401:
            logger.warning(f"djz_get_balance: 401 Unauthorized | body={res.text[:200]}")
            return {"success": False, "error": "التوكن منتهي الصلاحية أو غير صالح"}
        res.raise_for_status()
        raw  = res.json()
        data = raw.get("data", {})
        logger.debug(f"djz_get_balance: data keys={list(data.keys())}")

        main_balance = data.get("mainBalance", 0.0)
        due          = data.get("due", 0.0)
        cust_info    = data.get("customerInformations", {})
        conn_type    = cust_info.get("connectionType", "4G LTE")

        # ─── إصلاح: subscriptionType قد يكون dict أو str ───
        sim_name = "جيزي"
        sub_type = cust_info.get("subscriptionType")
        if isinstance(sub_type, dict):
            name_field = sub_type.get("name") or sub_type.get("label") or {}
            if isinstance(name_field, dict):
                sim_name = name_field.get("ar") or name_field.get("fr") or name_field.get("en") or "جيزي"
            elif isinstance(name_field, str) and name_field:
                sim_name = name_field
            else:
                sim_name = sub_type.get("code") or sub_type.get("id") or "جيزي"
        elif isinstance(sub_type, str) and sub_type:
            sim_name = sub_type

        # ─── استخراج باقات الإنترنت من connectedProducts ───
        connected = data.get("connectedProducts") or []
        internet_packs = []
        for prod in connected:
            if not isinstance(prod, dict): continue
            pname = _extract_name(prod) or prod.get("code", "")
            exp   = prod.get("expirationDate") or prod.get("expiration") or "—"
            balances = prod.get("balances") or []
            for b in balances[:2]:
                rem  = b.get("remainingValue", 0)
                init = b.get("initialValue", 0)
                bname = _extract_name(b) or b.get("type", "")
                internet_packs.append({"name": pname, "balance_name": bname,
                                       "remaining": rem, "initial": init, "expiry": exp})

        return {
            "success": True,
            "main_balance":   main_balance,
            "due":            due,
            "sim_type":       sim_name,
            "connection_type": conn_type,
            "internet_packs": internet_packs,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def _extract_name(obj: dict) -> str:
    """يستخرج اسم مقروء من كائن يحتوي name بصيغ مختلفة"""
    if not isinstance(obj, dict): return ""
    name = obj.get("name") or obj.get("label") or obj.get("displayName") or ""
    if isinstance(name, dict):
        return name.get("ar") or name.get("fr") or name.get("en") or ""
    if isinstance(name, str):
        return name.strip()
    return ""

def djz_get_subscriptions(msisdn: str, access_token: str) -> dict:
    """إصلاح: معالجة صحيحة لـ name و expirationDate من الـ API"""
    url = DJZ_URL_SUBS.format(msisdn=msisdn)
    headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json",
               "User-Agent": "MobileApp/3.0.0"}
    logger.info(f"djz_get_subscriptions: جلب الاشتراكات | msisdn={msisdn}")
    try:
        res = djz_http_get(url, headers, timeout=15)
        if res is None:
            logger.warning("djz_get_subscriptions: لا رد من السيرفر")
            return {"success": False, "error": "network_error"}
        if res.status_code == 401:
            logger.warning(f"djz_get_subscriptions: 401 | body={res.text[:200]}")
            return {"success": False, "error": "التوكن منتهي الصلاحية أو غير صالح"}
        res.raise_for_status()
        data     = res.json().get("data", {})
        products = data.get("products") or data.get("items") or []
        logger.debug(f"djz_get_subscriptions: {len(products)} منتج وُجد")

        result = []
        for p in products:
            if not isinstance(p, dict): continue

            # ─── اسم الباقة: يجرب name ثم description ثم code ───
            pname = _extract_name(p)
            if not pname:
                desc = p.get("description") or {}
                if isinstance(desc, dict):
                    pname = desc.get("ar") or desc.get("fr") or desc.get("en") or ""
                elif isinstance(desc, str):
                    pname = desc
            if not pname:
                pname = p.get("code") or p.get("id") or "باقة غير معروفة"

            # ─── تاريخ الانتهاء ───
            exp = (p.get("expirationDate") or p.get("expiration") or
                   p.get("endDate") or p.get("validUntil") or "—")

            # ─── الأرصدة ───
            balances = p.get("balances") or p.get("quota") or []
            clean_bals = []
            for b in balances:
                if not isinstance(b, dict): continue
                bname = _extract_name(b) or b.get("type") or b.get("unit") or "رصيد"
                clean_bals.append({
                    "name":           bname,
                    "remainingValue": b.get("remainingValue") or b.get("remaining") or 0,
                    "initialValue":   b.get("initialValue")  or b.get("total")    or 0,
                    "unit":           b.get("unit") or "",
                })

            result.append({
                "name":            pname,
                "code":            p.get("code") or "",
                "expiration_date": exp,
                "balances":        clean_bals,
            })

        return {"success": True, "subscriptions": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

def djz_refresh_token(phone_data: dict) -> dict | None:
    """تجديد توكن جيزي تلقائياً"""
    rt = phone_data.get("refresh_token", "")
    if not rt: return None
    headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "*/*",
               "User-Agent": "MobileApp/3.0.0"}
    data = {"scope": "openid", "client_id": DJZ_CLIENT_ID, "client_secret": DJZ_CLIENT_SECRET,
            "grant_type": "refresh_token", "refresh_token": rt}
    try:
        res = djz_http_post(DJZ_URL_TOKEN, headers=headers, data=data, timeout=15)
        if res and res.status_code == 200:
            t = res.json()
            if t.get("access_token"):
                return {"access_token": t["access_token"],
                        "refresh_token": t.get("refresh_token", rt)}
    except Exception as e:
        logger.debug(f"djz_refresh: {e}")
    return None


def _djz_reauth_via_otp(cid, msisdn, pd):
    """يرسل OTP جديد ويطلب من المستخدم إدخاله لتجديد التوكن"""
    oo_set_session(cid, {"state": "awaiting_otp", "msisdn": msisdn, "op": "djezzy"})
    ok = djz_send_otp(msisdn)
    if ok:
        tg_send(cid,
            f"{emo('warning','⚠')} <b>انتهت صلاحية التوكن</b>\n\n"
            f"{emo('sms','📩')} تم إرسال رمز جديد إلى <code>{mask_phone(msisdn)}</code>\n"
            f"{emo('info','💠')} أدخل الرمز للمتابعة",
            inline_kb=[[ibtn("🔄 إعادة الإرسال", callback="resend_otp",
                             emoji_key="refresh", color="success")],
                       [ibtn("📱 تغيير الرقم",  callback="change_phone",
                             emoji_key="phone",   color="primary")]])
    else:
        tg_send(cid,
            f"{emo('cross','❌')} <b>فشل تجديد التوكن</b>\n"
            f"{emo('info','💠')} فشل إرسال رمز التحقق — حاول مجدداً",
            inline_kb=[[ibtn("🔄 إعادة المحاولة", callback="resend_otp",
                             emoji_key="refresh", color="primary")]])


def _djz_ensure_token(cid, msisdn, pd) -> tuple[str, bool]:
    """يعيد (access_token, refreshed). يجدد التوكن تلقائياً عند الحاجة."""
    token = pd.get("access_token", "")
    # اختبار سريع: إذا كان التوكن قصيراً جداً فهو منتهٍ على الأرجح
    if not token or len(token) < 30:
        new_tok = djz_refresh_token(pd)
        if new_tok:
            oo_save_phone(cid, msisdn, new_tok)
            pd.update(new_tok)
            return pd["access_token"], True
    return token, False

# ══════════════ Telegram API ══════════════
def tg_request(method, **kwargs):
    try:
        r = _tg_session.post(f"{TELEGRAM_API}/{method}", json=kwargs, timeout=10)
        return r.json()
    except: return None

def tg_send(cid, text, inline_kb=None):
    payload = {"chat_id": cid, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    if inline_kb: payload["reply_markup"] = {"inline_keyboard": inline_kb}
    return tg_request("sendMessage", **payload)

def tg_photo(cid, photo, caption, inline_kb=None):
    payload = {"chat_id": cid, "photo": photo, "caption": caption, "parse_mode": "HTML"}
    if inline_kb: payload["reply_markup"] = {"inline_keyboard": inline_kb}
    return tg_request("sendPhoto", **payload)

def tg_edit(cid, msg_id, text, inline_kb=None):
    payload = {"chat_id": cid, "message_id": msg_id, "text": text,
               "parse_mode": "HTML", "disable_web_page_preview": True}
    if inline_kb: payload["reply_markup"] = {"inline_keyboard": inline_kb}
    return tg_request("editMessageText", **payload)

def tg_answer_cb(cb_id, text=None, alert=False):
    payload = {"callback_query_id": cb_id}
    if text: payload["text"] = text
    if alert: payload["show_alert"] = True
    return tg_request("answerCallbackQuery", **payload)

def tg_delete(cid, msg_id):
    return tg_request("deleteMessage", chat_id=cid, message_id=msg_id)


# ═══════════════════════════════════════════════════════
#  نظام الاشتراك الإجباري
# ═══════════════════════════════════════════════════════
def _check_member(cid, channel_id: str) -> bool:
    """يتحقق إذا كان المستخدم مشتركاً في القناة"""
    try:
        r = _tg_session.post(f"{TELEGRAM_API}/getChatMember",
                             json={"chat_id": channel_id, "user_id": cid},
                             timeout=8)
        data = r.json()
        # إذا فشل الطلب (البوت ليس أدمن أو خطأ آخر) → نعتبره مشتركاً
        if not data.get("ok"):
            logger.warning(f"_check_member: فشل فحص {channel_id} | {data.get('description','')} — تجاوز")
            return True
        status = data.get("result", {}).get("status", "")
        # left أو kicked = غير مشترك، باقي الحالات = مشترك
        return status not in ("left", "kicked", "")
    except Exception as e:
        logger.warning(f"_check_member exception {channel_id}: {e} — تجاوز")
        return True

def _get_unjoined(cid) -> list:
    """يعيد القنوات التي لم يشترك فيها المستخدم بعد — يدعم string وdict"""
    unjoined = []
    for ch in _forced_channels:
        if isinstance(ch, str):
            ch = {"id": ch, "url": f"https://t.me/{ch.lstrip('@')}"}
        if not _check_member(cid, ch["id"]):
            unjoined.append(ch)
    return unjoined

def _send_join_required(cid, unjoined: list):
    """يرسل رسالة الاشتراك الإجباري مع أزرار القنوات"""
    caption = (
        f"{emo('warning','⚠')} <b>الاشتراك الإجباري</b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
        f"{emo('info','💠')} يجب الاشتراك في القنوات التالية للمتابعة:\n"
    )
    kb = []
    for ch in unjoined:
        name = ch["id"].replace("@","")
        kb.append([ibtn(f"📢 {name}", url=ch["url"], emoji_key="broadcast")])
    kb.append([ibtn("✅ تحققت من اشتراكي", callback="check_sub",
                    emoji_key="check", color="success")])
    tg_send(cid, caption, inline_kb=kb)

def require_sub(cid) -> bool:
    """يعيد True إذا كان المستخدم مشتركاً في كل القنوات أو إدمن"""
    if not _forced_channels: return True
    if is_admin(cid): return True
    unjoined = _get_unjoined(cid)
    if unjoined:
        _send_join_required(cid, unjoined)
        return False
    return True

def send_log(text):
    if LOG_CHANNEL_ID:
        try: tg_send(LOG_CHANNEL_ID, text)
        except: pass

def send_activation_log(cid, msisdn: str, offer_name: str, price: str,
                        duration: str, mode: str = "عادي"):
    """ينشر تفعيلاً ناجحاً في قناة السجل بالشكل المطلوب"""
    if not LOG_CHANNEL_ID: return
    try:
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
        u = oo_get_user(cid) or {}
        username = u.get("username","")
        fname    = u.get("first_name","") or ""
        if username:
            user_display = f"@{username}"
        elif fname:
            user_display = fname
        else:
            user_display = f"ID:{cid}"
        text = (
            f"🎉 <b>تفعيل جديد</b>\n\n"
            f"👤 المستخدم: {user_display}\n"
            f"🆔 ID: <code>{cid}</code>\n"
            f"📱 الرقم: <code>{mask_phone(msisdn)}</code>\n"
            f"🎁 نوع العرض: {offer_name} — {price} — {duration}\n"
            f"🔓 الوضع: {mode}\n"
            f"💰 المجموع: {offer_name} | {price} | {duration}\n"
            f"📆 التاريخ: {date_str}\n"
            f"🕐 الوقت: {time_str}"
        )
        bot_username = "tasjilbott"
        kb = [[ibtn("🤖 فتح البوت", url=f"https://t.me/{bot_username}",
                    emoji_key="rocket")]]
        r = _tg_session.post(f"{TELEGRAM_API}/sendMessage",
                             json={"chat_id": LOG_CHANNEL_ID, "text": text,
                                   "parse_mode": "HTML",
                                   "reply_markup": {"inline_keyboard": kb}},
                             timeout=10)
    except Exception as e:
        logger.warning(f"send_activation_log: {e}")

# ══════════════ زر Inline ══════════════
def ibtn(text, callback=None, url=None, emoji_key=None, color="primary"):
    b = {"text": text}
    if callback: b["callback_data"] = callback
    if url:      b["url"] = url
    if emoji_key and emoji_key in EMOJI_IDS:
        b["icon_custom_emoji_id"] = EMOJI_IDS[emoji_key]
    if color: b["style"] = color
    return b

# ══════════════════════════════════════════════════
#  القائمة الرئيسية
# ══════════════════════════════════════════════════
def main_menu(cid, msisdn=None, phone_data=None):
    if msisdn is None:
        msisdn, phone_data = _get_active_phone_data(cid)
    if msisdn is None:
        oo_set_session(cid, {"state": "awaiting_phone"})
        return tg_send(cid,
            f"{emo('phone','📱')} أرسل رقمك:\n"
            f"🔴 أوريدو: <code>05XXXXXXXX</code>\n"
            f"🟡 جيزي:  <code>07XXXXXXXX</code>")

    op = phone_data.get("operator", "ooredoo")
    u  = oo_get_user(cid) or {}
    phones = u.get("phones", {})
    count  = len(phones)

    caption = (
        f"{emo('check','✨')} <b>القائمة الرئيسية</b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"{emo('phone','📱')} الرقم: <code>{mask_phone(msisdn)}</code>\n"
        f"{emo('info','💠')} المشغل: <b>{op_label(op)}</b>\n"
        f"{emo('sim','📋')} الأرقام المحفوظة: <b>{count}</b>\n\n"
        f"{emo('info','💠')} <i>اختر خدمة:</i>"
    )
    kb = []
    if op == "djezzy":
        kb.append([ibtn("🎁 تفعيل 2 جيغا — Walk & Win", callback="djz_offer_2go",
                        emoji_key="gift", color="success")])
        kb.append([ibtn("🇩🇿 هدية 72 جيغا — الذكرى 72", callback="djz_72gb",
                        emoji_key="gift", color="success")])

    else:
        kb.append([ibtn("🎁 هدية 2 جيغا (24 ساعة)", callback="offer_2go",
                        emoji_key="gift", color="success")])
        kb.append([ibtn("📦 هدية يومية أوريدو", callback="oo_buy:0",
                        emoji_key="gift", color="success")])
        kb.append([ibtn("🎁 هدية 72 جيغا — أوريدو", callback="oo_72gb",
                        emoji_key="gift", color="success")])
    if op == "ooredoo":
        kb.append([ibtn("🐍 ألعاب الصناديق", callback="menu_snake",
                        emoji_key="snake", color="success")])
    if op == "djezzy":
        kb.append([ibtn("🌐 عروض الإنترنت", callback="djz_offers_menu",
                        emoji_key="gift", color="success")])
    kb.append([ibtn("💳 رصيدي", callback="menu_balance",
                    emoji_key="wallet", color="primary")])
    if op == "djezzy":
        kb.append([
            ibtn("📦 اشتراكاتي", callback="djz_menu_subs", emoji_key="data", color="primary"),
            ibtn("ℹ معلوماتي",  callback="djz_menu_info", emoji_key="info", color="primary"),
        ])
    else:
        kb.append([ibtn("🌐 عروض الإنترنت", callback="menu_offers",
                        emoji_key="gift", color="primary")])
    kb.append([ibtn(f"📋 أرقامي ({count})", callback="menu_phones",
                    emoji_key="sim", color="primary")])

    kb.append([ibtn("🚪 تسجيل الخروج", callback="menu_logout",
                    emoji_key="logout", color="danger")])
    try:
        img = DJEZZY_IMAGE if op == "djezzy" else MENU_IMAGE
        tg_photo(cid, img, caption, inline_kb=kb)
    except:
        tg_send(cid, caption, inline_kb=kb)

def snake_menu(cid):
    caption = (
        f"{emo('snake','🐍')} <b>Power of Snake</b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
        f"{emo('info','💠')} العب وافتح صناديق الهدايا:\n"
        f"{emo('gift','🎁')} كل صندوق يحتوي على ميجا/جيجا مجانية"
    )
    kb = [
        [ibtn("📦 صناديقي",  callback="snake_check", emoji_key="box",  color="primary")],
        [ibtn("🎁 فتح صندوق", callback="snake_open",  emoji_key="gift", color="success")],
        [ibtn("🏠 رجوع",     callback="menu_home",   emoji_key="home", color="danger")],
    ]
    try: tg_photo(cid, SNAKE_IMAGE, caption, inline_kb=kb)
    except: tg_send(cid, caption, inline_kb=kb)



# ══════════════════════════════════════════════════
#  هدية 72 جيغا أوريدو — قفل زمني
#  تبدأ: 2026-11-01 00:00 | تنتهي: 2026-11-02 00:00
# ══════════════════════════════════════════════════
OO_72GB_START = 1762214400  # 2026-11-01 00:00 UTC+1 الجزائر
OO_72GB_END   = 1762300800  # 2026-11-02 00:00 UTC+1 الجزائر

def oo_do_72gb(cid):
    import time as _time
    now = _time.time() + 3600  # UTC+1
    u      = oo_get_user(cid) or {}
    msisdn = u.get("active_phone")
    if not msisdn:
        return tg_send(cid, f"{emo('cross','❌')} لا يوجد رقم نشط.")
    pd = u.get("phones", {}).get(msisdn, {})

    if now < OO_72GB_START:
        remaining = int(OO_72GB_START - now)
        h, m = divmod(remaining // 60, 60)
        return tg_send(cid,
            f"{emo('time','⏳')} <b>الهدية لم تُطلق بعد!</b>\n"
            f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
            f"🎁 <b>هدية 72 جيغا — أوريدو</b>\n\n"
            f"⏱ تبدأ في: <b>01 نوفمبر 2026 الساعة 00:00</b>\n"
            f"🕐 الوقت المتبقي: <b>{h}س {m}د</b>",
            inline_kb=[[ibtn("🏠 رجوع", callback="menu_home", emoji_key="home", color="danger")]])

    if now > OO_72GB_END:
        return tg_send(cid,
            f"{emo('cross','❌')} <b>انتهت فترة الهدية</b>\n"
            f"كانت متاحة في 01 نوفمبر 2026 فقط.",
            inline_kb=[[ibtn("🏠 رجوع", callback="menu_home", emoji_key="home", color="danger")]])

    pd = oo_check_session(cid, msisdn, pd) or pd
    tg_send(cid, f"{emo('rocket','🚀')} <i>جاري تفعيل هدية 72 جيغا...</i>")

    # طلب التفعيل — bundle code يُضاف لاحقاً
    res = oo_buy_cvm(msisdn, pd, "OO_72GB_GIFT_BUNDLE")

    if res.get("success"):
        caption = (
            f"{emo('gift','🎁')} <b>تم التفعيل بنجاح!</b>\n"
            f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
            f"✅ <b>هدية 72 جيغا — أوريدو</b>\n"
            f"📊 72 GB | ⏱ 24 ساعة\n"
            f"💰 مجاني"
        )
        kb = [[ibtn("🏠 القائمة الرئيسية", callback="menu_home", emoji_key="home", color="primary")]]
        tg_send(cid, caption, inline_kb=kb)
        send_activation_log(cid, msisdn, "72 جيغا", "مجاني", "24 ساعة", "هدية أوريدو 72")
    elif res.get("error") == "already_used":
        tg_send(cid,
            f"{emo('info','💠')} <b>الهدية مستخدمة مسبقاً</b>\n"
            f"تم تفعيلها مسبقاً على هذا الرقم.",
            inline_kb=[[ibtn("🏠 رجوع", callback="menu_home", emoji_key="home", color="danger")]])
    elif res.get("auth_error"):
        tg_send(cid, f"{emo('key','🔑')} انتهت الجلسة، أعد تسجيل الدخول.",
                inline_kb=[[ibtn("🔄 تسجيل الدخول", callback="menu_logout", emoji_key="logout", color="danger")]])
    else:
        tg_send(cid,
            f"{emo('cross','❌')} <b>فشل التفعيل</b>\n{res.get('error','')}",
            inline_kb=[[ibtn("🔄 إعادة المحاولة", callback="oo_72gb", emoji_key="refresh", color="primary")]])

# ══════════════════════════════════════════════════
#  كتالوج عروض أوريدو
# ══════════════════════════════════════════════════
OO_OFFERS = [
    # ── CVM (ديناميكية) ──
    {"idx": 0, "name": "🎁 هدية يومية",             "vol": "2 GB",   "dur": "24 ساعة", "price": "مجاني",    "type": "cvm",      "code": "BTL_24H_DATA_Free_2Go",       "payload": None},
    {"idx": 1, "name": "⚡ 5 جيغا يومي",             "vol": "5 GB",   "dur": "24 ساعة", "price": "90 دج",    "type": "cvm",      "code": "ATL_24H_DATA_90DZD_5Go",      "payload": None},
    {"idx": 2, "name": "🔥 10 جيغا (3 أيام)",        "vol": "10 GB",  "dur": "3 أيام",  "price": "190 دج",   "type": "cvm",      "code": "ATL_72H_DATA_190DZD_10Go",    "payload": None},
    {"idx": 3, "name": "💎 30 جيغا أسبوعي",          "vol": "30 GB",  "dur": "7 أيام",  "price": "490 دج",   "type": "cvm",      "code": "ATL_7D_DATA_490DZD_30Go",     "payload": None},
    # ── BYOP (شهرية) ──
    {"idx": 4, "name": "🌐 30 جيغا شهري",            "vol": "30 GB",  "dur": "30 يوم",  "price": "950 دج",   "type": "byop",     "code": None,
     "payload": {"validity":"Monthly","limitedBundleDetails":[{"account":"data","allocation":30}],"unlimitedBundleDetails":[]}},
    {"idx": 5, "name": "🌐 50 جيغا شهري",            "vol": "50 GB",  "dur": "30 يوم",  "price": "1250 دج",  "type": "byop",     "code": None,
     "payload": {"validity":"Monthly","limitedBundleDetails":[{"account":"data","allocation":50}],"unlimitedBundleDetails":[]}},
    {"idx": 6, "name": "🌐 60 جيغا شهري",            "vol": "60 GB",  "dur": "30 يوم",  "price": "1350 دج",  "type": "byop",     "code": None,
     "payload": {"validity":"Monthly","limitedBundleDetails":[{"account":"data","allocation":60}],"unlimitedBundleDetails":[]}},
    {"idx": 7, "name": "🌐 70 جيغا شهري",            "vol": "70 GB",  "dur": "30 يوم",  "price": "1475 دج",  "type": "byop",     "code": None,
     "payload": {"validity":"Monthly","limitedBundleDetails":[{"account":"data","allocation":70}],"unlimitedBundleDetails":[]}},
    # ── BYOP (غير محدود) ──
    {"idx": 8,  "name": "💬 واتساب غير محدود (15 يوم)", "vol": "∞ WA",  "dur": "15 يوم", "price": "50 دج",   "type": "byop", "code": None,
     "payload": {"validity":"Biweekly","limitedBundleDetails":[],"unlimitedBundleDetails":["WA"]}},
    {"idx": 9,  "name": "📘 فيسبوك غير محدود (أسبوع)",  "vol": "∞ FB",  "dur": "7 أيام", "price": "80 دج",   "type": "byop", "code": None,
     "payload": {"validity":"Weekly","limitedBundleDetails":[],"unlimitedBundleDetails":["FB"]}},
    {"idx": 10, "name": "📘 فيسبوك غير محدود (15 يوم)", "vol": "∞ FB",  "dur": "15 يوم", "price": "100 دج",  "type": "byop", "code": None,
     "payload": {"validity":"Biweekly","limitedBundleDetails":[],"unlimitedBundleDetails":["FB"]}},
    {"idx": 11, "name": "📸 إنستاغرام غير محدود (15 يوم)","vol": "∞ IG", "dur": "15 يوم", "price": "100 دج",  "type": "byop", "code": None,
     "payload": {"validity":"Biweekly","limitedBundleDetails":[],"unlimitedBundleDetails":["IG"]}},
    {"idx": 12, "name": "▶️ يوتيوب غير محدود (15 يوم)",  "vol": "∞ YT",  "dur": "15 يوم", "price": "100 دج",  "type": "byop", "code": None,
     "payload": {"validity":"Biweekly","limitedBundleDetails":[],"unlimitedBundleDetails":["YT"]}},
    {"idx": 13, "name": "📘 فيسبوك غير محدود (شهر)",     "vol": "∞ FB",  "dur": "30 يوم", "price": "200 دج",  "type": "byop", "code": None,
     "payload": {"validity":"Monthly","limitedBundleDetails":[],"unlimitedBundleDetails":["FB"]}},
    {"idx": 14, "name": "📸 إنستاغرام غير محدود (شهر)",  "vol": "∞ IG",  "dur": "30 يوم", "price": "200 دج",  "type": "byop", "code": None,
     "payload": {"validity":"Monthly","limitedBundleDetails":[],"unlimitedBundleDetails":["IG"]}},
    {"idx": 15, "name": "▶️ يوتيوب غير محدود (شهر)",     "vol": "∞ YT",  "dur": "30 يوم", "price": "200 دج",  "type": "byop", "code": None,
     "payload": {"validity":"Monthly","limitedBundleDetails":[],"unlimitedBundleDetails":["YT"]}},
    # ── سناب شات مجاني ──
    {"idx": 16, "name": "👻 سناب شات مجاني (شهر)",       "vol": "∞ SC",  "dur": "30 يوم", "price": "مجاني",   "type": "snap",     "code": None, "payload": None},
]

def offers_menu(cid):
    maint = is_in_maintenance("ooredoo")
    caption = (
        f"{emo('gift','🎁')} <b>عروض الإنترنت — أوريدو</b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
        f"{emo('info','💠')} اختر العرض المناسب:"
    )
    kb = []
    for o in OO_OFFERS:
        label = f"{o['name']} | {o['vol']} | {o['dur']} | {o['price']}"
        cb    = f"oo_buy:{o['idx']}"
        kb.append([ibtn(label, callback=cb, emoji_key="gift", color="success")])
    kb.append([ibtn("🏠 رجوع", callback="menu_home", emoji_key="home", color="danger")])
    try: tg_photo(cid, OFFER_IMAGE, caption, inline_kb=kb)
    except: tg_send(cid, caption, inline_kb=kb)

def oo_buy_confirm(cid, idx, edit_id=None):
    """شاشة تأكيد شراء عرض أوريدو"""
    if idx >= len(OO_OFFERS): return
    o = OO_OFFERS[idx]
    maint = is_in_maintenance("ooredoo")
    if maint:
        caption = (
            f"{emo('warning','⚠')} <b>الخدمة في صيانة مؤقتة</b>\n"
            f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
            f"{emo('info','💠')} يمكنك تفعيل <b>{o['name']}</b>\n"
            f"من تطبيق <b>My Ooredoo</b> الرسمي مؤقتاً."
        )
        kb = [[ibtn("🏠 رجوع", callback="menu_offers", emoji_key="home", color="danger")]]
        return tg_send(cid, caption, inline_kb=kb)
    caption = (
        f"{emo('gift','🎁')} <b>تأكيد الطلب</b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
        f"📦 <b>العرض:</b> {o['name']}\n"
        f"📊 <b>الحجم:</b> {o['vol']}\n"
        f"⏱ <b>المدة:</b> {o['dur']}\n"
        f"💰 <b>السعر:</b> {o['price']}\n\n"
        f"{emo('info','💠')} هل تريد تفعيل هذا العرض؟"
    )
    kb = [
        [ibtn("✅ تأكيد التفعيل", callback=f"oo_confirm_buy:{idx}", emoji_key="check", color="success")],
        [ibtn("❌ إلغاء",         callback="menu_offers",            emoji_key="cross", color="danger")],
    ]
    tg_send(cid, caption, inline_kb=kb)

def oo_do_buy(cid, idx):
    """تنفيذ شراء عرض أوريدو"""
    if idx >= len(OO_OFFERS): return
    o      = OO_OFFERS[idx]
    u      = oo_get_user(cid) or {}
    msisdn = u.get("active_phone")
    if not msisdn:
        return tg_send(cid, f"{emo('cross','❌')} لا يوجد رقم نشط.")
    pd = u.get("phones", {}).get(msisdn, {})

    # تجديد التوكن إن لزم
    dev = oo_get_device(cid)
    pd  = oo_check_session(cid, msisdn, pd) or pd

    tg_send(cid, f"{emo('rocket','🚀')} <i>جاري تفعيل {o['name']}...</i>")

    if o["type"] == "cvm":
        res = oo_buy_cvm(msisdn, pd, o["code"])
    elif o["type"] == "byop":
        res = oo_buy_byop(msisdn, pd, o["payload"])
    elif o["type"] == "snap":
        res = oo_buy_snapchat(msisdn, pd)
    else:
        return tg_send(cid, f"{emo('cross','❌')} نوع عرض غير معروف.")

    if res.get("success"):
        caption = (
            f"{emo('gift','🎁')} <b>تم التفعيل بنجاح!</b>\n"
            f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
            f"✅ <b>{o['name']}</b>\n"
            f"📊 {o['vol']} | ⏱ {o['dur']}\n"
            f"💰 {o['price']} — مُقتطع من رصيدك"
        )
        kb = [[ibtn("🏠 القائمة الرئيسية", callback="menu_home", emoji_key="home", color="primary")]]
        tg_send(cid, caption, inline_kb=kb)
        send_activation_log(cid, msisdn, o["vol"], o["price"], o["dur"], f"أوريدو — {o['name']}")
    elif res.get("auth_error"):
        tg_send(cid, f"{emo('key','🔑')} انتهت الجلسة، أعد تسجيل الدخول.",
                inline_kb=[[ibtn("🔄 تسجيل الدخول", callback="menu_logout", emoji_key="logout", color="danger")]])
    elif res.get("error") == "already_used":
        tg_send(cid,
            f"{emo('info','💠')} <b>العرض مستخدم مسبقاً</b>\n"
            f"انتظر انتهاء الفترة الحالية قبل التجديد.",
            inline_kb=[[ibtn("🏠 رجوع", callback="menu_home", emoji_key="home", color="danger")]])
    else:
        tg_send(cid,
            f"{emo('cross','❌')} <b>فشل التفعيل</b>\n{res.get('error','')}",
            inline_kb=[[ibtn("🔄 إعادة المحاولة", callback=f"oo_buy:{idx}", emoji_key="refresh", color="primary")]])

# ══════════════════════════════════════════════════
#  شاشة أرقامي
# ══════════════════════════════════════════════════
def phones_menu(cid, edit_id=None):
    u = oo_get_user(cid) or {}
    phones       = u.get("phones", {})
    active_phone = u.get("active_phone")
    if not phones:
        caption = (
            f"{emo('sim','📋')} <b>أرقامي</b>\n"
            f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
            f"{emo('info','💠')} لا توجد أرقام محفوظة بعد"
        )
        kb = [
            [ibtn("➕ إضافة رقم جديد", callback="add_phone", emoji_key="plus", color="success")],
            [ibtn("🏠 رجوع",           callback="menu_home", emoji_key="home", color="danger")],
        ]
        if edit_id: return tg_edit(cid, edit_id, caption, inline_kb=kb)
        return tg_send(cid, caption, inline_kb=kb)

    lines = [f"{emo('sim','📋')} <b>أرقامي ({len(phones)})</b>\n",
             "<b>━━━━━━━━━━━━━━━━━━━━━</b>\n"]
    for m, pd in phones.items():
        active_mark = " ✅ <i>(نشط)</i>" if m == active_phone else ""
        lines.append(f"{op_label(pd.get('operator','ooredoo'))} <code>{mask_phone(m)}</code>{active_mark}")

    caption = "\n".join(lines)
    kb = []
    for m, pd in list(phones.items()):
        row = []
        if m != active_phone:
            row.append(ibtn(f"🔄 تفعيل {mask_phone(m)}",
                            callback=f"switch_phone:{m}", emoji_key="switch", color="success"))
        row.append(ibtn(f"🗑 حذف {mask_phone(m)}",
                        callback=f"del_phone:{m}", emoji_key="trash", color="danger"))
        kb.append(row)
    kb.append([ibtn("➕ إضافة رقم جديد", callback="add_phone",  emoji_key="plus", color="primary")])
    kb.append([ibtn("🏠 رجوع",           callback="menu_home",  emoji_key="home", color="danger")])
    if edit_id: return tg_edit(cid, edit_id, caption, inline_kb=kb)
    tg_send(cid, caption, inline_kb=kb)

# ══════════════════════════════════════════════════
#  الرصيد والاشتراكات — إصلاح كامل
# ══════════════════════════════════════════════════
def show_balance(cid, edit_id=None):
    msisdn, pd = _get_active_phone_data(cid)
    if not msisdn or not pd:
        return tg_send(cid, f"{emo('cross','❌')} لا يوجد حساب مسجّل")
    op = pd.get("operator", "ooredoo")

    if op == "djezzy":
        pending_msg = tg_send(cid, f"{emo('time','⏳')} <i>جاري جلب الرصيد...</i>")
        pending_mid = (pending_msg or {}).get("result", {}).get("message_id") if isinstance((pending_msg or {}).get("result"), dict) else None
        token, _ = _djz_ensure_token(cid, msisdn, pd)
        result = djz_get_balance(msisdn, token)
        if result["success"]:
            lines = [
                f"{emo('wallet','💳')} <b>رصيدي — جيزي</b>\n",
                f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n",
                f"{emo('star','💰')} الرصيد: <b>{result['main_balance']} دج</b>",
                f"{emo('info','📋')} نوع الشريحة: <b>{result['sim_type']}</b>",
                f"{emo('signal','📶')} الشبكة: <b>{result['connection_type']}</b>",
                f"{emo('warning','💳')} الديون: <b>{result['due']} دج</b>",
                f"{emo('phone','📱')} الرقم: <code>{mask_phone(msisdn)}</code>",
            ]
            # باقات الإنترنت النشطة
            packs = result.get("internet_packs", [])
            if packs:
                lines.append(f"\n{emo('data','📦')} <b>الباقات النشطة:</b>")
                for pk in packs[:4]:
                    lines.append(f"  {emo('star','✦')} {pk['name']}: <b>{pk['remaining']}</b>/{pk['initial']} | ينتهي: {pk['expiry']}")
            caption = "\n".join(lines)
        else:
            caption = f"{emo('cross','❌')} تعذر جلب الرصيد\n{result.get('error','')}"
        kb = [[ibtn("🔄 تحديث", callback="menu_balance",  emoji_key="refresh", color="primary")],
              [ibtn("🏠 رجوع",  callback="menu_home",    emoji_key="home",    color="danger")]]
        if pending_mid: tg_delete(cid, pending_mid)
        if edit_id: return tg_edit(cid, edit_id, caption, inline_kb=kb)
        return tg_send(cid, caption, inline_kb=kb)

    # أوريدو
    oo_pending = tg_send(cid, f"{emo('time','⏳')} <i>جاري جلب الرصيد...</i>")
    oo_pending_mid = (oo_pending or {}).get("result", {}).get("message_id") if isinstance((oo_pending or {}).get("result"), dict) else None
    bal = oo_get_balance(cid, msisdn, pd)
    if oo_pending_mid: tg_delete(cid, oo_pending_mid)
    if bal and bal.get("error") == "expired":
        oo_delete_phone(cid, msisdn)
        return tg_send(cid, f"{emo('cross','🔄')} انتهت الجلسة، أعد /start")
    if not bal or bal.get("error"):
        caption = f"{emo('cross','❌')} <b>تعذر جلب الرصيد</b>\n{emo('info','💠')} حاول مرة أخرى"
        kb = [[ibtn("🔄 تحديث", callback="menu_balance", emoji_key="refresh", color="primary")],
              [ibtn("🏠 رجوع",  callback="menu_home",   emoji_key="home",    color="danger")]]
        if edit_id: return tg_edit(cid, edit_id, caption, inline_kb=kb)
        return tg_send(cid, caption, inline_kb=kb)

    lines = [f"{emo('wallet','💳')} <b>رصيدي — أوريدو</b>\n", "<b>━━━━━━━━━━━━━━━━━━━━━</b>\n"]
    possible_keys = ["accounts", "balances", "accountList", "data", "result"]
    accounts = []
    for k in possible_keys:
        if isinstance(bal.get(k), list) and bal[k]:
            accounts = bal[k]; break
        if isinstance(bal.get(k), dict):
            accounts = [bal[k]]; break
    if not accounts:
        for k, v in bal.items():
            if k in ("msisdn", "id", "status"): continue
            if isinstance(v, (int, float, str)) and v not in ("", None):
                lines.append(f"{emo('star','✦')} <b>{k}:</b> {v}")
    else:
        for acc in accounts[:8]:
            if not isinstance(acc, dict): continue
            n = acc.get("accountType") or acc.get("type") or acc.get("name") or "—"
            v = acc.get("value") or acc.get("balance") or acc.get("amount") or acc.get("usage-value") or "—"
            u_unit = acc.get("unit") or acc.get("usageUnit") or acc.get("usage-unit") or ""
            lines.append(f"{emo('star','✦')} <b>{n}:</b> {oo_format_size(v, u_unit)}")
    if len(lines) <= 2:
        lines.append(f"{emo('info','ℹ')} <i>لا توجد بيانات رصيد متاحة</i>")
    caption = "\n".join(lines)
    kb = [[ibtn("🔄 تحديث", callback="menu_balance", emoji_key="refresh", color="primary")],
          [ibtn("🏠 رجوع",  callback="menu_home",   emoji_key="home",    color="danger")]]
    if edit_id: return tg_edit(cid, edit_id, caption, inline_kb=kb)
    tg_send(cid, caption, inline_kb=kb)

def show_djz_subscriptions(cid, edit_id=None):
    """اشتراكاتي — جيزي — إصلاح None"""
    msisdn, pd = _get_active_phone_data(cid)
    if not msisdn or pd.get("operator") != "djezzy":
        return tg_send(cid, f"{emo('cross','❌')} هذه الخاصية لجيزي فقط")
    pending_msg = tg_send(cid, f"{emo('time','⏳')} <i>جاري جلب الاشتراكات...</i>")
    pending_mid = (pending_msg or {}).get("result", {}).get("message_id") if isinstance((pending_msg or {}).get("result"), dict) else None
    token, _ = _djz_ensure_token(cid, msisdn, pd)
    result = djz_get_subscriptions(msisdn, token)
    if not result["success"]:
        caption = f"{emo('cross','❌')} تعذر جلب الاشتراكات\n{result.get('error','')}"
    else:
        subs = result["subscriptions"]
        if not subs:
            caption = (f"{emo('info','📦')} <b>اشتراكاتي — جيزي</b>\n"
                       f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
                       f"{emo('info','💠')} لا توجد اشتراكات نشطة حالياً")
        else:
            lines = [f"{emo('data','📦')} <b>اشتراكاتي ({len(subs)}) — جيزي</b>\n",
                     "<b>━━━━━━━━━━━━━━━━━━━━━</b>\n"]
            for idx, s in enumerate(subs[:6], 1):
                pname = s["name"] or s.get("code") or f"باقة {idx}"
                exp   = s["expiration_date"] or "غير محدد"
                lines.append(f"\n{emo('star','✦')} <b>{idx}. {pname}</b>")
                lines.append(f"   {emo('time','⏳')} تنتهي: <b>{exp}</b>")
                for b in s.get("balances", [])[:3]:
                    rem   = b.get("remainingValue", 0)
                    init  = b.get("initialValue", 0)
                    bname = b.get("name") or b.get("type") or "رصيد"
                    unit  = b.get("unit") or ""
                    lines.append(f"   {emo('info','💠')} {bname}: <b>{rem}{unit}</b> / {init}{unit}")
            caption = "\n".join(lines)
    kb = [[ibtn("🔄 تحديث", callback="djz_menu_subs", emoji_key="refresh", color="primary")],
          [ibtn("🏠 رجوع",  callback="menu_home",     emoji_key="home",    color="danger")]]
    if pending_mid: tg_delete(cid, pending_mid)
    if edit_id: return tg_edit(cid, edit_id, caption, inline_kb=kb)
    tg_send(cid, caption, inline_kb=kb)

def show_djz_info(cid, edit_id=None):
    """معلوماتي — جيزي"""
    msisdn, pd = _get_active_phone_data(cid)
    if not msisdn or pd.get("operator") != "djezzy":
        return tg_send(cid, f"{emo('cross','❌')} هذه الخاصية لجيزي فقط")
    pending_msg = tg_send(cid, f"{emo('time','⏳')} <i>جاري جلب المعلومات...</i>")
    pending_mid = (pending_msg or {}).get("result", {}).get("message_id") if isinstance((pending_msg or {}).get("result"), dict) else None
    token, _ = _djz_ensure_token(cid, msisdn, pd)
    result = djz_get_balance(msisdn, token)
    if not result["success"]:
        caption = f"{emo('cross','❌')} تعذر جلب المعلومات\n{result.get('error','')}"
    else:
        caption = (
            f"{emo('user','ℹ')} <b>معلوماتي — جيزي</b>\n"
            f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
            f"{emo('phone','📱')} الرقم: <code>{mask_phone(msisdn)}</code>\n"
            f"{emo('info','📋')} نوع الشريحة: <b>{result['sim_type']}</b>\n"
            f"{emo('signal','📶')} نوع الشبكة: <b>{result['connection_type']}</b>\n"
            f"{emo('star','💰')} الرصيد الرئيسي: <b>{result['main_balance']} دج</b>\n"
            f"{emo('warning','💳')} الديون: <b>{result['due']} دج</b>"
        )
    kb = [[ibtn("🔄 تحديث", callback="djz_menu_info", emoji_key="refresh", color="primary")],
          [ibtn("🏠 رجوع",  callback="menu_home",     emoji_key="home",    color="danger")]]
    if pending_mid: tg_delete(cid, pending_mid)
    if edit_id: return tg_edit(cid, edit_id, caption, inline_kb=kb)
    tg_send(cid, caption, inline_kb=kb)

# ══════════════════════════════════════════════════
#  تفعيل 2 جيغا — مع retry x3
# ══════════════════════════════════════════════════
def oo_do_free_2go(cid, edit_id=None):
    lock = _get_user_lock(cid)
    if not lock.acquire(blocking=False): return tg_send(cid, "⏳ انتظر قليلاً...")
    try:
        msisdn, pd = _get_active_phone_data(cid)
        if not msisdn or not pd: return
        tg_send(cid, f"{emo('time','⏳')} <i>جاري تفعيل 2 جيغا...</i>")
        def _try_buy():
            return oo_buy_cvm(msisdn, pd, "BTL_24H_DATA_Free_2Go")
        res = retry_call(_try_buy, max_attempts=3, delay=1.5)
        if res and res.get("success"):
            caption = (
                f"{emo('check','🎉')} <b>تم التفعيل بنجاح!</b>\n"
                f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
                f"{emo('gift','🎁')} حصلت على <b>2 Go</b>\n"
                f"{emo('time','⏳')} صالح لمدة <b>24 ساعة</b>\n"
                f"{emo('phone','📱')} الرقم: <code>{mask_phone(msisdn)}</code>"
            )
            tg_send(cid, caption, inline_kb=[[ibtn("🏠 رجوع", callback="menu_home",
                                                    emoji_key="home", color="danger")]])
            send_activation_log(cid, msisdn, "2 جيغا", "مجاني", "24 ساعة", "أوريدو هدية")
        elif res and res.get("error") == "already_used":
            tg_send(cid,
                    f"{emo('warning','⚠')} <b>استفدت مسبقاً</b>\n\n"
                    f"{emo('time','⏳')} جرّب مجدداً بعد <b>24 ساعة</b>",
                    inline_kb=[[ibtn("🏠 رجوع", callback="menu_home", emoji_key="home", color="danger")]])
        else:
            err = res.get("error","") if isinstance(res, dict) else ""
            tg_send(cid, f"{emo('cross','❌')} <b>فشل التفعيل</b>\n\n{err}",
                    inline_kb=[[ibtn("🏠 رجوع", callback="menu_home", emoji_key="home", color="danger")]])
    finally: lock.release()


def djz_do_72gb(cid, edit_id=None):
    """تفعيل هدية 72 جيغا — مع قفل زمني وتجديد توكن تلقائي"""
    lock = _get_user_lock(cid)
    if not lock.acquire(blocking=False):
        return tg_send(cid, "⏳ انتظر قليلاً...")
    try:
        msisdn, pd = _get_active_phone_data(cid)
        if not msisdn or not pd:
            return
        # ── قفل زمني: 1 نوفمبر 2026 ──
        secs_left = djz_72gb_seconds_remaining()
        if secs_left > 0:
            caption = (
                f"{emo('time','⏳')} <b>الهدية لم تُطلق بعد!</b>\n"
                f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
                f"🇩🇿 <b>هدية الذكرى 72 — 72 جيغا</b>\n\n"
                f"{emo('time','⏳')} تُفتح في: <b>1 نوفمبر 2026 — 00:00</b>\n"
                f"⏰ متبقي: <b>{_djz_fmt_remaining(secs_left)}</b>"
            )
            return tg_send(cid, caption,
                           inline_kb=[[ibtn("🏠 رجوع", callback="menu_home",
                                            emoji_key="home", color="danger")]])
        tg_send(cid, f"{emo('rocket','🚀')} <i>جاري تفعيل هدية 72 جيغا...</i>")
        token, _ = _djz_ensure_token(cid, msisdn, pd)
        result = djz_activate_72gb(msisdn, token)
        # توكن منتهي → تجديد تلقائي
        if result.get("token_expired"):
            new_tok = djz_refresh_token(pd)
            if new_tok:
                oo_save_phone(cid, msisdn, new_tok)
                pd.update(new_tok)
                token = new_tok["access_token"]
                result = djz_activate_72gb(msisdn, token)
            if result.get("token_expired") or not new_tok:
                return _djz_reauth_via_otp(cid, msisdn, pd)
        if result.get("success"):
            caption = (
                f"{emo('check','🎉')} <b>تم التفعيل بنجاح!</b>\n"
                f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
                f"🇩🇿 <b>هدية الذكرى 72 — 72 جيغا</b>\n"
                f"{emo('time','⏳')} صالحة لمدة <b>24 ساعة</b>\n"
                f"{emo('phone','📱')} الرقم: <code>{mask_phone(msisdn)}</code>"
            )
            tg_send(cid, caption,
                    inline_kb=[[ibtn("🏠 رجوع", callback="menu_home",
                                     emoji_key="home", color="danger")]])
            send_activation_log(cid, msisdn, "72 جيغا 🇩🇿", "مجاني", "24 ساعة", "هدية الذكرى")
        else:
            err = result.get("error", "خطأ غير معروف")
            raw = result.get("raw", "")
            raw_txt = f"\n<code>{str(raw)[:200]}</code>" if raw else ""
            tg_send(cid,
                    f"{emo('cross','❌')} <b>فشل التفعيل</b>\n"
                    f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
                    f"{emo('info','💠')} <b>السبب:</b> {err}{raw_txt}",
                    inline_kb=[[ibtn("🏠 رجوع", callback="menu_home",
                                     emoji_key="home", color="danger")]])
    finally:
        lock.release()


def djz_do_offer_2go(cid, edit_id=None):
    lock = _get_user_lock(cid)
    if not lock.acquire(blocking=False): return tg_send(cid, "⏳ انتظر قليلاً...")
    try:
        msisdn, pd = _get_active_phone_data(cid)
        if not msisdn or not pd: return
        tg_send(cid, f"{emo('time','⏳')} <i>جاري الفحص...</i>")
        token, _ = _djz_ensure_token(cid, msisdn, pd)
        is_ready, _sec, status_text, record_ok = djz_check_cooldown(msisdn, token)
        if not record_ok:
            caption = (
                f"{emo('warning','⚠')} <b>الوضعية: غير معروف</b>\n"
                f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
                f"{emo('cross','❌')} تعذر فحص سجل الهدية\n\n"
                f"{emo('info','💠')} <b>أسباب محتملة لعدم التفعيل:</b>\n"
                f"  • عدم اكتمال أسبوع من آخر تفعيل\n"
                f"  • تحتاج اشتراك في عرض 100 دج\n"
                f"  • رقمك لا يدعم هذا العرض"
            )
            return tg_send(cid, caption,
                           inline_kb=[[ibtn("🔄 إعادة المحاولة", callback="djz_offer_2go",
                                            emoji_key="refresh", color="primary")],
                                      [ibtn("🏠 رجوع", callback="menu_home",
                                            emoji_key="home", color="danger")]])
        if not is_ready:
            caption = (
                f"{emo('warning','⚠')} <b>الهدية غير متاحة بعد</b>\n"
                f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
                f"{emo('time','⏳')} متبقي: <b>{status_text}</b>\n\n"
                f"{emo('info','💠')} الهدية متاحة مرة كل <b>أسبوع (7 أيام)</b>"
            )
            return tg_send(cid, caption,
                           inline_kb=[[ibtn("🏠 رجوع", callback="menu_home",
                                            emoji_key="home", color="danger")]])
        caption = (
            f"{emo('gift','🎁')} <b>الهدية جاهزة للتفعيل!</b>\n"
            f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
            f"{emo('check','✨')} هدية <b>Walk & Win — 2 جيغا</b>\n"
            f"{emo('time','⏳')} صالحة لمدة <b>24 ساعة</b>\n"
            f"{emo('phone','📱')} الرقم: <code>{mask_phone(msisdn)}</code>"
        )
        tg_send(cid, caption,
                inline_kb=[
                    [ibtn("🚀 تفعيل 2 جيغا الآن", callback="djz_confirm_2go",
                          emoji_key="rocket", color="success")],
                    [ibtn("🏠 رجوع", callback="menu_home", emoji_key="home", color="danger")],
                ])
    finally: lock.release()

def djz_confirm_activate_2go(cid):
    lock = _get_user_lock(cid)
    if not lock.acquire(blocking=False): return tg_send(cid, "⏳ انتظر قليلاً...")
    try:
        msisdn, pd = _get_active_phone_data(cid)
        if not msisdn or not pd: return
        tg_send(cid, f"{emo('rocket','🚀')} <i>جاري تفعيل الهدية...</i>")
        token, _ = _djz_ensure_token(cid, msisdn, pd)
        _, _sec, _stxt, record_ok = djz_check_cooldown(msisdn, token)
        success = djz_activate_2gb(msisdn, token)
        if success:
            caption = (
                f"{emo('check','🎉')} <b>تم التفعيل بنجاح!</b>\n"
                f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
                f"{emo('gift','🎁')} حصلت على <b>2 Go</b> — Walk & Win\n"
                f"{emo('time','⏳')} صالح لمدة <b>24 ساعة</b>\n"
                f"{emo('phone','📱')} الرقم: <code>{mask_phone(msisdn)}</code>"
            )
            tg_send(cid, caption,
                    inline_kb=[[ibtn("🏠 رجوع", callback="menu_home", emoji_key="home", color="danger")]])
            send_activation_log(cid, msisdn, "2 جيغا Walk&Win", "مجاني", "24 ساعة", "جيزي هدية")
            djz_reminder_register(cid, msisdn)
        else:
            if not record_ok:
                fail_msg = (
                    f"{emo('cross','❌')} <b>فشل التفعيل</b>\n"
                    f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
                    f"{emo('info','💠')} <b>الأسباب المحتملة:</b>\n"
                    f"  • عدم اكتمال أسبوع من آخر تفعيل\n"
                    f"  • تحتاج اشتراك في عرض 100 دج\n"
                    f"  • رقمك لا يدعم هذا العرض"
                )
            else:
                fail_msg = (
                    f"{emo('cross','❌')} <b>فشل التفعيل</b>\n"
                    f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
                    f"{emo('info','💠')} <b>الأسباب المحتملة:</b>\n"
                    f"  • تحتاج اشتراك في عرض 100 دج\n"
                    f"  • رقمك لا يدعم هذا العرض"
                )
            tg_send(cid, fail_msg,
                    inline_kb=[[ibtn("🏠 رجوع", callback="menu_home",
                                     emoji_key="home", color="danger")]])
    finally: lock.release()

# ══════════════════════════════════════════════════
#  Snake (أوريدو)
# ══════════════════════════════════════════════════
def oo_snake_check(cid, edit_id=None):
    msisdn, pd = _get_active_phone_data(cid)
    if not msisdn or not pd: return
    try:
        st = oo_power_snake_status(cid, msisdn, pd)
        if isinstance(st, dict) and st.get("error") == "expired":
            oo_delete_phone(cid, msisdn)
            return tg_send(cid, f"{emo('cross','🔄')} انتهت الجلسة، أعد /start")
        gifts = []
        if isinstance(st, list): gifts = st
        elif isinstance(st, dict): gifts = st.get("gifts") or st.get("content") or []
        if gifts:
            lines = [f"{emo('gift','🎁')} <b>صناديقك المتوفرة: {len(gifts)}</b>\n",
                     "<b>━━━━━━━━━━━━━━━━━━━━━</b>\n"]
            for idx, g in enumerate(gifts[:10], 1):
                name = g.get("giftName") or g.get("name") or "صندوق"
                val  = g.get("value") or g.get("size") or ""
                lines.append(f"{emo('star','✦')} {idx}. <b>{name}</b> {val}")
            caption = "\n".join(lines)
            kb = [[ibtn("🎁 فتح صندوق", callback="snake_open",  emoji_key="gift",    color="success")],
                  [ibtn("🏠 رجوع",      callback="menu_home",   emoji_key="home",    color="danger")]]
        else:
            caption = (f"{emo('cross','❌')} <b>لا توجد صناديق</b>\n\n{emo('info','💠')} جرّب لاحقاً")
            kb = [[ibtn("🔄 تحديث", callback="snake_check", emoji_key="refresh", color="primary")],
                  [ibtn("🏠 رجوع",  callback="menu_home",   emoji_key="home",    color="danger")]]
        if edit_id: tg_edit(cid, edit_id, caption, inline_kb=kb)
        else: tg_send(cid, caption, inline_kb=kb)
    except Exception as e:
        logger.exception(f"snake_check: {e}")
        tg_send(cid, f"{emo('cross','❌')} خطأ",
                inline_kb=[[ibtn("🏠 رجوع", callback="menu_home", emoji_key="home", color="danger")]])

def oo_snake_open(cid, edit_id=None):
    lock = _get_user_lock(cid)
    if not lock.acquire(blocking=False): return tg_send(cid, "⏳ انتظر قليلاً...")
    try:
        msisdn, pd = _get_active_phone_data(cid)
        if not msisdn or not pd: return
        st = oo_power_snake_status(cid, msisdn, pd)
        gifts = []
        if isinstance(st, list): gifts = st
        elif isinstance(st, dict): gifts = st.get("gifts") or st.get("content") or []
        if not gifts:
            return tg_send(cid, f"{emo('cross','❌')} <b>لا توجد صناديق</b>",
                           inline_kb=[[ibtn("🏠 رجوع", callback="menu_home", emoji_key="home", color="danger")]])
        gid = gifts[0].get("id") or gifts[0].get("giftId")
        def _try_redeem():
            return oo_power_snake_redeem(msisdn, pd, gid)
        res = retry_call(_try_redeem, max_attempts=3, delay=1.5)
        if isinstance(res, dict) and not res.get("error"):
            a    = res.get("assignedReward", {})
            r    = a.get("reward", {}) if isinstance(a, dict) else {}
            size = oo_format_size(r.get("usage-value", 0), r.get("usage-unit", ""))
            caption = (
                f"{emo('check','🎉')} <b>مبروك!</b>\n"
                f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
                f"{emo('gift','📦')} تم فتح الصندوق بنجاح\n"
                f"{emo('stats','📊')} الحجم: <b>{size}</b>"
            )
            tg_send(cid, caption, inline_kb=[[ibtn("🏠 رجوع", callback="menu_home", emoji_key="home", color="danger")]])
            send_activation_log(cid, msisdn, f"صندوق {size}", "مجاني", "—", "Snake")
        else:
            tg_send(cid, f"{emo('cross','❌')} <b>فشل فتح الصندوق</b>",
                    inline_kb=[[ibtn("🏠 رجوع", callback="menu_home", emoji_key="home", color="danger")]])
    except Exception as e:
        logger.exception(f"snake_open: {e}")
        tg_send(cid, f"{emo('cross','❌')} خطأ",
                inline_kb=[[ibtn("🏠 رجوع", callback="menu_home", emoji_key="home", color="danger")]])
    finally: lock.release()

# ══════════════════════════════════════════════════
#  لوحة الأدمن — موسّعة
# ══════════════════════════════════════════════════
_admin_states = {}

def admin_panel(cid, edit_id=None):
    caption = (
        f"{emo('admin','👑')} <b>لوحة الأدمن</b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
        f"{emo('info','💠')} اختر العملية:"
    )
    kb = [
        [ibtn("📊 إحصائيات",   callback="adm_stats",    emoji_key="stats",     color="primary"),
         ibtn("👥 المستخدمون", callback="adm_users",    emoji_key="user",      color="primary")],
        [ibtn("📢 بث رسالة",   callback="adm_broadcast", emoji_key="broadcast", color="success")],
        [ibtn("🚫 حظر",        callback="adm_ban",       emoji_key="ban",       color="danger"),
         ibtn("✅ فك الحظر",   callback="adm_unban",     emoji_key="unban",     color="success")],
        [ibtn("🔧 الصيانة",    callback="adm_maintenance", emoji_key="wrench",  color="primary")],
        [ibtn("🌐 البروكسيات", callback="adm_proxy",     emoji_key="proxy",     color="primary")],
        [ibtn("🇩🇿 تعديل QR 72 جيغا", callback="adm_qr72",  emoji_key="key",       color="primary")],
        [ibtn("🏠 رجوع",       callback="menu_home",     emoji_key="home",      color="danger")],
    ]
    if edit_id: tg_edit(cid, edit_id, caption, inline_kb=kb)
    else: tg_send(cid, caption, inline_kb=kb)

def admin_maintenance_panel(cid, edit_id=None):
    caption = maintenance_status_text() + f"\n\n{emo('info','💠')} اختر الإجراء:"
    g   = _maintenance.get("global")
    oo_ = _maintenance.get("ooredoo")
    dj_ = _maintenance.get("djezzy")
    kb = [
        [ibtn(f"🌐 الكل: {'إيقاف' if g else 'تفعيل'}",
              callback="adm_maint_toggle_global",  color="danger" if not g else "success")],
        [ibtn(f"🔴 أوريدو: {'إيقاف' if oo_ else 'تفعيل'}",
              callback="adm_maint_toggle_oo",      color="danger" if not oo_ else "success")],
        [ibtn(f"🟡 جيزي: {'إيقاف' if dj_ else 'تفعيل'}",
              callback="adm_maint_toggle_dj",      color="danger" if not dj_ else "success")],
        [ibtn("🏠 رجوع", callback="admin_panel", emoji_key="home", color="danger")],
    ]
    if edit_id: tg_edit(cid, edit_id, caption, inline_kb=kb)
    else: tg_send(cid, caption, inline_kb=kb)

def admin_proxy_panel(cid, edit_id=None):
    caption = proxy_status_text() + f"\n\n{emo('info','💠')} إدارة البروكسيات:"
    oo_en = _proxy_config["ooredoo"]["enabled"]
    dj_en = _proxy_config["djezzy"]["enabled"]
    kb = [
        [ibtn(f"🔴 أوريدو: {'تعطيل' if oo_en else 'تفعيل'}",
              callback="adm_proxy_toggle_oo", color="danger" if oo_en else "success")],
        [ibtn("🔴 تعديل بروكسيات أوريدو", callback="adm_proxy_edit_oo", color="primary")],
        [ibtn(f"🟡 جيزي: {'تعطيل' if dj_en else 'تفعيل'}",
              callback="adm_proxy_toggle_dj", color="danger" if dj_en else "success")],
        [ibtn("🟡 تعديل بروكسيات جيزي", callback="adm_proxy_edit_dj", color="primary")],
        [ibtn("🏠 رجوع", callback="admin_panel", emoji_key="home", color="danger")],
    ]
    if edit_id: tg_edit(cid, edit_id, caption, inline_kb=kb)
    else: tg_send(cid, caption, inline_kb=kb)

def admin_stats(cid, edit_id=None):
    try:
        total  = len(_users)
        active = sum(1 for u in _users.values() if any(pd.get("access_token") for pd in u.get("phones",{}).values()))
        banned = sum(1 for u in _users.values() if u.get("banned"))
        oo_cnt = sum(1 for u in _users.values() for pd in u.get("phones",{}).values() if pd.get("operator","ooredoo")=="ooredoo")
        dj_cnt = sum(1 for u in _users.values() for pd in u.get("phones",{}).values() if pd.get("operator")=="djezzy")
        g   = "🔴 مفعّل" if _maintenance.get("global")  else "🟢 إيقاف"
        oo_ = "🔴 مفعّل" if _maintenance.get("ooredoo") else "🟢 إيقاف"
        dj_ = "🔴 مفعّل" if _maintenance.get("djezzy")  else "🟢 إيقاف"
        caption = (
            f"{emo('stats','📊')} <b>إحصائيات البوت</b>\n"
            f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
            f"{emo('user','👥')} إجمالي المستخدمين: <b>{total}</b>\n"
            f"{emo('check','✅')} جلسات نشطة: <b>{active}</b>\n"
            f"🔴 أوريدو: <b>{oo_cnt}</b> رقم | 🟡 جيزي: <b>{dj_cnt}</b> رقم\n"
            f"{emo('ban','🚫')} محظورون: <b>{banned}</b>\n\n"
            f"🔧 صيانة الكل: <b>{g}</b>\n"
            f"🔴 صيانة أوريدو: <b>{oo_}</b>\n"
            f"🟡 صيانة جيزي:  <b>{dj_}</b>"
        )
    except Exception as e:
        caption = f"{emo('cross','❌')} خطأ: {e}"
    kb = [[ibtn("🏠 رجوع", callback="admin_panel", emoji_key="home", color="danger")]]
    if edit_id: tg_edit(cid, edit_id, caption, inline_kb=kb)
    else: tg_send(cid, caption, inline_kb=kb)

def admin_users(cid, edit_id=None):
    try:
        lines = [f"{emo('user','👥')} <b>المستخدمون ({len(_users)})</b>\n",
                 "<b>━━━━━━━━━━━━━━━━━━━━━</b>\n"]
        for i, (uid, u) in enumerate(list(_users.items())[:20], 1):
            banned = " 🚫" if u.get("banned") else ""
            phones = u.get("phones", {})
            nums   = " | ".join(mask_phone(m) for m in list(phones.keys())[:3])
            ops    = "".join("🔴" if pd.get("operator","ooredoo")=="ooredoo" else "🟡"
                             for pd in phones.values())
            lines.append(f"{i}. {ops} <code>{uid}</code> | {nums}{banned}")
        caption = "\n".join(lines)
    except Exception as e:
        caption = f"{emo('cross','❌')} خطأ: {e}"
    kb = [[ibtn("🏠 رجوع", callback="admin_panel", emoji_key="home", color="danger")]]
    if edit_id: tg_edit(cid, edit_id, caption, inline_kb=kb)
    else: tg_send(cid, caption, inline_kb=kb)

def admin_login_menu(cid):
    caption = (
        f"{emo('lock','👋')} <b>مرحباً أدمن</b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
        f"{emo('info','💠')} اختر طريقة تسجيل الدخول:"
    )
    kb = [
        [ibtn("📩 الدخول برمز SMS",   callback="admin_sms", emoji_key="sms", color="success")],
        [ibtn("🔑 الدخول بكلمة السر", callback="admin_pwd", emoji_key="key", color="primary")],
    ]
    tg_send(cid, caption, inline_kb=kb)

# ══════════════════════════════════════════════════
#  معالج النصوص
# ══════════════════════════════════════════════════
def handle(cid, text):
    try:
        text = text.strip()

        # ─── صيانة ───
        if is_in_maintenance() and not is_admin(cid):
            return tg_send(cid, "🔧 <b>البوت في صيانة مؤقتة</b>\nسيعود قريباً ⚙️")

        if text == "/admin":
            if is_admin(cid): return admin_panel(cid)
            return

        # أوامر الأدمن
        st = _admin_states.get(cid)
        if st and is_admin(cid):
            if st == "broadcast":
                _admin_states.pop(cid, None)
                count = 0
                for uid in list(_users.keys()):
                    try:
                        if tg_send(uid, f"{emo('broadcast','📢')} <b>{text}</b>"): count += 1
                    except: pass
                return tg_send(cid, f"{emo('check','✅')} تم البث إلى <b>{count}</b> مستخدم")
            if st == "ban":
                _admin_states.pop(cid, None)
                try:
                    target = int(text)
                    oo_save_base(target, {"banned": True})
                    return tg_send(cid, f"{emo('ban','🚫')} تم حظر <code>{target}</code>")
                except: return tg_send(cid, f"{emo('cross','❌')} ID غير صحيح")
            if st == "unban":
                _admin_states.pop(cid, None)
                try:
                    target = int(text)
                    oo_save_base(target, {"banned": False})
                    return tg_send(cid, f"{emo('check','✅')} تم فك الحظر عن <code>{target}</code>")
                except: return tg_send(cid, f"{emo('cross','❌')} ID غير صحيح")
            if st == "proxy_edit_oo":
                _admin_states.pop(cid, None)
                lines = [l.strip() for l in text.splitlines() if l.strip()]
                proxy_set_list("ooredoo", lines)
                _save_async()
                return tg_send(cid, f"{emo('check','✅')} تم حفظ <b>{len(lines)}</b> بروكسي لأوريدو")
            if st == "proxy_edit_dj":
                _admin_states.pop(cid, None)
                lines = [l.strip() for l in text.splitlines() if l.strip()]
                proxy_set_list("djezzy", lines)
                _save_async()
                return tg_send(cid, f"{emo('check','✅')} تم حفظ <b>{len(lines)}</b> بروكسي لجيزي")
            if st == "qr72_edit":
                _admin_states.pop(cid, None)
                new_qr = text.strip()
                djz_72gb_set_qr(new_qr)
                return tg_send(cid,
                    f"{emo('check','✅')} <b>تم تحديث QR Code</b>\n\n"
                    f"{emo('info','💠')} الجديد:\n<code>{new_qr}</code>")

        user_check = oo_get_user(cid) or {}
        if user_check.get("banned"):
            return tg_send(cid, f"{emo('ban','🚫')} <b>أنت محظور</b>")

        if not is_admin(cid) and not require_sub(cid):
            return

        sess  = oo_get_session(cid)
        state = sess.get("state", "")

        # ─── /start ───
        if text == "/start":
            msisdn, pd = _get_active_phone_data(cid)
            if msisdn and pd:
                op = pd.get("operator", "ooredoo")
                # فحص صيانة المشغل
                if is_in_maintenance(op) and not is_admin(cid):
                    op_name = "أوريدو 🔴" if op == "ooredoo" else "جيزي 🟡"
                    return tg_send(cid, f"🔧 <b>خدمة {op_name} في صيانة مؤقتة</b>\nسيعود قريباً ⚙️")
                if op == "djezzy" or oo_check_session(cid, msisdn, pd):
                    return main_menu(cid, msisdn, pd)
            if is_admin(cid):
                oo_set_session(cid, {"state": "admin_choose_login"})
                return admin_login_menu(cid)
            oo_set_session(cid, {"state": "awaiting_phone"})
            caption = (
                f"{emo('check','👋')} <b>مرحباً!</b>\n"
                f"<b>━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
                f"{emo('phone','📱')} أرسل رقمك للبدء:\n"
                f"🔴 أوريدو: <code>05XXXXXXXX</code>\n"
                f"🟡 جيزي:  <code>07XXXXXXXX</code>"
            )
            try: tg_photo(cid, WELCOME_IMAGE, caption)
            except: tg_send(cid, caption)
            return

        if state == "admin_choose_login": return admin_login_menu(cid)

        if state == "admin_await_phone_pwd":
            dg = "".join(c for c in text if c.isdigit())
            if not re.match(r"^05\d{8}$", dg):
                return tg_send(cid, f"{emo('cross','❌')} رقم أوريدو غير صحيح (05XXXXXXXX)")
            oo_set_session(cid, {"state": "admin_await_password", "msisdn": "213" + dg[1:]})
            return tg_send(cid, f"{emo('key','🔑')} أرسل كلمة السر:")

        if state == "admin_await_password":
            msisdn = sess.get("msisdn")
            tg_send(cid, f"{emo('time','⏳')} جاري التحقق...")
            res = oo_login_password(msisdn, text)
            if res == "wrong_password": return tg_send(cid, f"{emo('cross','❌')} كلمة السر خاطئة")
            if not res: return tg_send(cid, f"{emo('cross','❌')} سيرفر غير متاح")
            oo_save_phone(cid, msisdn, {"operator": "ooredoo", **res})
            oo_clear_session(cid)
            tg_send(cid, f"{emo('check','🎉')} <b>تم تسجيل الدخول بنجاح!</b>")
            return main_menu(cid)

        # ══════ إدخال رقم الهاتف ══════
        if state == "awaiting_phone":
            dg = "".join(c for c in text if c.isdigit())

            # أوريدو 05
            if re.match(r"^05\d{8}$", dg):
                if is_in_maintenance("ooredoo") and not is_admin(cid):
                    return tg_send(cid, "🔧 <b>خدمة أوريدو في صيانة مؤقتة</b> 🔴")
                msisdn = "213" + dg[1:]
                u = oo_get_user(cid) or {}
                if msisdn in u.get("phones", {}):
                    oo_set_active_phone(cid, msisdn)
                    oo_clear_session(cid)
                    pd = u["phones"][msisdn]
                    tg_send(cid, f"{emo('check','✅')} تم التبديل إلى <code>{mask_phone(msisdn)}</code>")
                    return main_menu(cid, msisdn, pd)
                wait = _check_otp_cooldown(cid)
                if wait > 0: return tg_send(cid, f"{emo('warning','⚠')} <b>انتظر {wait} ثانية</b>")
                oo_set_session(cid, {"state": "awaiting_otp", "msisdn": msisdn, "op": "ooredoo"})
                tg_send(cid,
                    f"{emo('check','✅')} تم استلام رقمك\n{emo('time','⏳')} جاري إرسال الرمز...",
                    inline_kb=[[ibtn("📱 تغيير الرقم", callback="change_phone",
                                     emoji_key="phone", color="primary")]])
                def _bg_oo():
                    res = oo_send_otp(msisdn)
                    if res.get("ok"):
                        tg_send(cid,
                            f"{emo('check','✅')} <b>تم إرسال OTP</b>\n\n"
                            f"{emo('info','📩')} إذا لم يصلك، اضغط إعادة الإرسال",
                            inline_kb=[[ibtn("🔄 إعادة الإرسال", callback="resend_otp",
                                             emoji_key="refresh", color="success")],
                                       [ibtn("📱 تغيير الرقم",  callback="change_phone",
                                             emoji_key="phone",   color="primary")]])
                    else:
                        err = str(res.get("error",""))
                        msg = (f"{emo('warning','⚠')} <b>حظر مؤقت</b>\nانتظر 60 ثانية"
                               if ("rate_limit" in err or "ip_blocked" in err)
                               else f"{emo('cross','❌')} فشل الإرسال")
                        tg_send(cid, msg,
                                inline_kb=[[ibtn("🔄 إعادة",    callback="resend_otp",   emoji_key="refresh", color="success")],
                                            [ibtn("📱 تغيير",   callback="change_phone", emoji_key="phone",   color="primary")]])
                submit_task(_bg_oo)
                return

            # جيزي 07
            elif re.match(r"^07\d{8}$", dg):
                if is_in_maintenance("djezzy") and not is_admin(cid):
                    return tg_send(cid, "🔧 <b>خدمة جيزي في صيانة مؤقتة</b> 🟡")
                msisdn = djz_format_msisdn(dg)
                u = oo_get_user(cid) or {}
                if msisdn in u.get("phones", {}):
                    oo_set_active_phone(cid, msisdn)
                    oo_clear_session(cid)
                    pd = u["phones"][msisdn]
                    tg_send(cid, f"{emo('check','✅')} تم التبديل إلى <code>{mask_phone(msisdn)}</code>")
                    return main_menu(cid, msisdn, pd)
                wait = _check_otp_cooldown(cid)
                if wait > 0: return tg_send(cid, f"{emo('warning','⚠')} <b>انتظر {wait} ثانية</b>")
                oo_set_session(cid, {"state": "awaiting_otp", "msisdn": msisdn, "op": "djezzy"})
                tg_send(cid,
                    f"{emo('check','✅')} تم استلام رقمك\n{emo('time','⏳')} جاري إرسال الرمز...",
                    inline_kb=[[ibtn("📱 تغيير الرقم", callback="change_phone",
                                     emoji_key="phone", color="primary")]])
                def _bg_djz():
                    ok = djz_send_otp(msisdn)   # retry x3 مدمج
                    if ok:
                        tg_send(cid,
                            f"{emo('check','✅')} <b>تم إرسال OTP</b>\n\n"
                            f"{emo('info','📩')} إذا لم يصلك، اضغط إعادة الإرسال",
                            inline_kb=[[ibtn("🔄 إعادة الإرسال", callback="resend_otp",
                                             emoji_key="refresh", color="success")],
                                       [ibtn("📱 تغيير الرقم",  callback="change_phone",
                                             emoji_key="phone",   color="primary")]])
                    else:
                        tg_send(cid, f"{emo('cross','❌')} فشل إرسال OTP",
                                inline_kb=[[ibtn("🔄 إعادة",  callback="resend_otp",   emoji_key="refresh", color="success")],
                                            [ibtn("📱 تغيير", callback="change_phone", emoji_key="phone",   color="primary")]])
                submit_task(_bg_djz)
                return

            else:
                return tg_send(cid,
                    f"{emo('cross','❌')} رقم غير صحيح\n"
                    f"🔴 أوريدو: <code>05XXXXXXXX</code>\n"
                    f"🟡 جيزي:  <code>07XXXXXXXX</code>")

        # ══════ fallback: المستخدم يرسل رقم هاتف في أي حالة ══════
        # إذا أرسل المستخدم رقم هاتف وهو ليس في state awaiting_phone أو awaiting_otp
        # نحوله مباشرة لمعالجة الرقم (مثلاً كان في قائمة أو عملية أخرى)
        if state not in ("awaiting_phone", "awaiting_otp", "admin_await_phone_pwd",
                         "admin_await_password", "admin_choose_login"):
            dg_check = "".join(c for c in text if c.isdigit())
            if re.match(r"^(05|07)\d{8}$", dg_check):
                oo_clear_session(cid)
                oo_set_session(cid, {"state": "awaiting_phone"})
                return handle(cid, text)

        # ══════ OTP ══════
        if state == "awaiting_otp":
            otp_raw = "".join(c for c in text if c.isdigit())
            # ── إذا أرسل المستخدم رقم هاتف بدلاً من الرمز → أعد التوجيه ──
            if re.match(r"^(05|07)\d{8}$", otp_raw) or re.match(r"^213[57]\d{8}$", otp_raw):
                oo_clear_session(cid)
                oo_set_session(cid, {"state": "awaiting_phone"})
                return handle(cid, text)   # أعد المعالجة كرقم هاتف جديد
            if len(otp_raw) < 4:
                return tg_send(cid, f"{emo('cross','❌')} رمز غير صحيح")
            msisdn = sess.get("msisdn")
            op     = sess.get("op", "ooredoo")
            if not msisdn: return

            if op == "djezzy":
                tg_send(cid, f"{emo('time','⏳')} <i>جاري التحقق من الرمز...</i>")
                # djz_verify_otp لديه retry x3 مدمج
                result = djz_verify_otp(msisdn, otp_raw)
                if result.get("wrong_otp"):
                    return tg_send(cid,
                        f"{emo('cross','❌')} <b>رمز خاطئ</b>\n"
                        f"{emo('info','💠')} تأكد من الرمز أو اطلب رمزاً جديداً",
                        inline_kb=[[ibtn("🔄 إعادة الإرسال", callback="resend_otp",
                                         emoji_key="refresh", color="success")],
                                   [ibtn("📱 تغيير الرقم",  callback="change_phone",
                                         emoji_key="phone", color="primary")]])
                if result.get("rate_limit"):
                    return tg_send(cid, f"{emo('warning','⚠')} <b>تجاوزت الحد</b> — انتظر دقيقة")
                if result.get("access_token"):
                    oo_save_phone(cid, msisdn, {
                        "operator": "djezzy",
                        "access_token":  result["access_token"],
                        "refresh_token": result.get("refresh_token", ""),
                    })
                    oo_clear_session(cid)
                    tg_send(cid, f"{emo('check','🎉')} <b>تم تسجيل الدخول بنجاح!</b>")
                    return main_menu(cid)
                return tg_send(cid, f"{emo('cross','❌')} فشل التحقق، حاول مجدداً")

            else:  # ooredoo
                tg_send(cid, f"{emo('time','⏳')} <i>جاري التحقق...</i>")
                dev = oo_get_device()
                def _try_verify():
                    return oo_verify_otp(msisdn, otp_raw, dev)
                res = retry_call(_try_verify, max_attempts=3, delay=1.5)
                if res == "wrong_otp":
                    return tg_send(cid,
                        f"{emo('cross','❌')} <b>رمز خاطئ</b>",
                        inline_kb=[[ibtn("🔄 إعادة الإرسال", callback="resend_otp",
                                         emoji_key="refresh", color="success")],
                                   [ibtn("📱 تغيير الرقم",  callback="change_phone",
                                         emoji_key="phone", color="primary")]])
                if isinstance(res, dict) and res.get("access_token"):
                    oo_save_phone(cid, msisdn, {"operator": "ooredoo", **res})
                    oo_clear_session(cid)
                    tg_send(cid, f"{emo('check','🎉')} <b>تم تسجيل الدخول بنجاح!</b>")
                    return main_menu(cid)
                return tg_send(cid, f"{emo('cross','❌')} فشل التحقق، حاول مجدداً")

    except Exception as e:
        logger.exception(f"handle error: {e}")

# ══════════════════════════════════════════════════
#  معالج الـ Callbacks
# ══════════════════════════════════════════════════
def handle_callback(cb):
    try:
        cid    = cb.get("message", {}).get("chat", {}).get("id")
        mid    = cb.get("message", {}).get("message_id")
        data   = cb.get("data", "")
        cb_id  = cb.get("id")

        if not cid: return
        tg_answer_cb(cb_id)

        user_check = oo_get_user(cid) or {}
        if user_check.get("banned") and not is_admin(cid):
            return tg_send(cid, f"{emo('ban','🚫')} <b>أنت محظور</b>")

        # ── فحص الاشتراك الإجباري (ما عدا زر التحقق نفسه) ──
        if data != "check_sub" and not is_admin(cid) and not require_sub(cid):
            return

        # ─── صيانة per-operator ───
        msisdn_cb, pd_cb = _get_active_phone_data(cid)
        if pd_cb:
            op_cb = pd_cb.get("operator", "ooredoo")
            if is_in_maintenance(op_cb) and not is_admin(cid):
                op_name = "أوريدو 🔴" if op_cb == "ooredoo" else "جيزي 🟡"
                return tg_send(cid, f"🔧 <b>خدمة {op_name} في صيانة مؤقتة</b>")

        # ─── admin panel ───
        if data == "admin_panel" and is_admin(cid):
            return admin_panel(cid, edit_id=mid)

        if is_admin(cid):
            if data == "adm_stats":    return admin_stats(cid, edit_id=mid)
            if data == "adm_users":    return admin_users(cid, edit_id=mid)
            if data == "adm_broadcast":
                _admin_states[cid] = "broadcast"
                return tg_send(cid, f"{emo('broadcast','📢')} أرسل نص الرسالة:")
            if data == "adm_ban":
                _admin_states[cid] = "ban"
                return tg_send(cid, f"{emo('ban','🚫')} أرسل ID المستخدم:")
            if data == "adm_unban":
                _admin_states[cid] = "unban"
                return tg_send(cid, f"{emo('unban','✅')} أرسل ID المستخدم:")

            # ─── الصيانة ───
            if data == "adm_maintenance":
                return admin_maintenance_panel(cid, edit_id=mid)
            if data == "adm_maint_toggle_global":
                _maintenance["global"] = not _maintenance.get("global")
                _save_async()
                return admin_maintenance_panel(cid, edit_id=mid)
            if data == "adm_maint_toggle_oo":
                _maintenance["ooredoo"] = not _maintenance.get("ooredoo")
                _save_async()
                return admin_maintenance_panel(cid, edit_id=mid)
            if data == "adm_maint_toggle_dj":
                _maintenance["djezzy"] = not _maintenance.get("djezzy")
                _save_async()
                return admin_maintenance_panel(cid, edit_id=mid)

            # ─── البروكسيات ───
            if data == "adm_proxy":
                return admin_proxy_panel(cid, edit_id=mid)
            if data == "adm_proxy_toggle_oo":
                _proxy_config["ooredoo"]["enabled"] = not _proxy_config["ooredoo"]["enabled"]
                _save_async()
                return admin_proxy_panel(cid, edit_id=mid)
            if data == "adm_proxy_toggle_dj":
                _proxy_config["djezzy"]["enabled"] = not _proxy_config["djezzy"]["enabled"]
                _save_async()
                return admin_proxy_panel(cid, edit_id=mid)
            if data == "adm_proxy_edit_oo":
                _admin_states[cid] = "proxy_edit_oo"
                cur = "\n".join(_proxy_config["ooredoo"]["proxies"]) or "فارغة"
                return tg_send(cid,
                    f"{emo('proxy','🌐')} أرسل قائمة بروكسيات أوريدو (سطر لكل بروكسي):\n"
                    f"تنسيق: <code>http://user:pass@host:port</code>\n\n"
                    f"الحالية:\n<code>{cur}</code>")
            if data == "adm_proxy_edit_dj":
                _admin_states[cid] = "proxy_edit_dj"
                cur = "\n".join(_proxy_config["djezzy"]["proxies"]) or "فارغة"
                return tg_send(cid,
                    f"{emo('proxy','🌐')} أرسل قائمة بروكسيات جيزي (سطر لكل بروكسي):\n"
                    f"تنسيق: <code>http://user:pass@host:port</code>\n\n"
                    f"الحالية:\n<code>{cur}</code>")

            if data == "adm_qr72":
                _admin_states[cid] = "qr72_edit"
                cur_qr = djz_72gb_get_qr()
                return tg_send(cid,
                    f"{emo('key','🔑')} <b>تعديل QR Code — هدية 72 جيغا</b>\n\n"
                    f"{emo('info','💠')} الحالي:\n<code>{cur_qr}</code>\n\n"
                    f"أرسل الـ QR Code الجديد:")

        # ─── Navigation ───
        if data == "check_sub":
            unjoined = _get_unjoined(cid)
            if unjoined:
                _send_join_required(cid, unjoined)
                return tg_send(cid,
                    f"{emo('cross','❌')} لم تشترك في كل القنوات بعد\n"
                    f"{emo('info','💠')} اشترك ثم اضغط تحققت مجدداً")
            tg_delete(cid, mid)
            return tg_send(cid,
                f"{emo('check','✅')} <b>شكراً على اشتراكك!</b>\n"
                f"{emo('info','💠')} أرسل /start للمتابعة")

        if data == "menu_home":
            msisdn, pd = _get_active_phone_data(cid)
            tg_delete(cid, mid)
            return main_menu(cid, msisdn, pd)

        if data == "menu_snake":
            tg_delete(cid, mid)
            return snake_menu(cid)

        if data == "menu_balance":
            return submit_task(show_balance, cid, mid)

        if data == "menu_offers":
            tg_delete(cid, mid)
            return offers_menu(cid)

        if data == "menu_phones":
            tg_delete(cid, mid)
            return phones_menu(cid)

        if data == "menu_logout":
            oo_delete_user(cid); oo_clear_session(cid)
            tg_delete(cid, mid)
            return tg_send(cid, f"{emo('check','✅')} <b>تم تسجيل الخروج</b>\nأرسل /start للبدء")

        # ── أرقامي ──
        if data == "add_phone":
            oo_set_session(cid, {"state": "awaiting_phone"})
            return tg_send(cid,
                f"{emo('phone','📱')} أرسل الرقم الجديد:\n"
                f"🔴 أوريدو: <code>05XXXXXXXX</code>\n"
                f"🟡 جيزي:  <code>07XXXXXXXX</code>")

        if data.startswith("switch_phone:"):
            msisdn = data.split(":", 1)[1]
            u = oo_get_user(cid) or {}
            if msisdn in u.get("phones", {}):
                oo_set_active_phone(cid, msisdn)
                pd = u["phones"][msisdn]
                tg_send(cid, f"{emo('check','✅')} تم التبديل إلى <code>{mask_phone(msisdn)}</code>")
                tg_delete(cid, mid)
                return main_menu(cid, msisdn, pd)
            return

        if data.startswith("del_phone:"):
            msisdn = data.split(":", 1)[1]
            oo_delete_phone(cid, msisdn)
            tg_send(cid, f"{emo('trash','🗑')} تم حذف الرقم <code>{mask_phone(msisdn)}</code>")
            new_msisdn, new_pd = _get_active_phone_data(cid)
            if new_msisdn:
                return phones_menu(cid, edit_id=mid)
            else:
                tg_delete(cid, mid)
                oo_set_session(cid, {"state": "awaiting_phone"})
                return tg_send(cid,
                    f"{emo('phone','📱')} أرسل رقمك:\n"
                    f"🔴 أوريدو: <code>05XXXXXXXX</code>\n"
                    f"🟡 جيزي:  <code>07XXXXXXXX</code>")

        # ── Snake ──
        if data == "snake_check":
            return submit_task(oo_snake_check, cid, mid)
        if data == "snake_open":
            return submit_task(oo_snake_open, cid, mid)

        # ── تفعيل 2 جيغا ──
        if data == "offer_2go":
            return submit_task(oo_do_free_2go, cid, mid)
        if data == "djz_offer_2go":
            return submit_task(djz_do_offer_2go, cid, mid)
        if data == "djz_confirm_2go":
            return submit_task(djz_confirm_activate_2go, cid)

        if data == "djz_72gb":
            return submit_task(djz_do_72gb, cid, mid)

        # ── اشتراكات ومعلومات جيزي ──
        if data == "djz_offers_menu":
            return submit_task(djz_offers_menu, cid)

        # ── عروض أوريدو ──
        if data.startswith("oo_buy:"):
            idx = int(data.split(":",1)[1])
            return submit_task(oo_buy_confirm, cid, idx)

        if data.startswith("oo_confirm_buy:"):
            idx = int(data.split(":",1)[1])
            return submit_task(oo_do_buy, cid, idx)

        if data == "oo_72gb":
            return submit_task(oo_do_72gb, cid)

        if data.startswith("djz_buy:"):
            idx = int(data.split(":",1)[1])
            return submit_task(djz_buy_confirm, cid, idx)

        if data.startswith("djz_confirm_buy:"):
            idx = int(data.split(":",1)[1])
            return submit_task(djz_do_buy, cid, idx)

        if data == "djz_menu_subs":
            return submit_task(show_djz_subscriptions, cid, mid)
        if data == "djz_menu_info":
            return submit_task(show_djz_info, cid, mid)

        # ── تغيير رقم / إعادة OTP ──
        if data == "change_phone":
            oo_clear_session(cid)
            oo_set_session(cid, {"state": "awaiting_phone"})
            return tg_send(cid,
                f"{emo('phone','📱')} أرسل الرقم الجديد:\n"
                f"🔴 أوريدو: <code>05XXXXXXXX</code>\n"
                f"🟡 جيزي:  <code>07XXXXXXXX</code>")

        if data == "resend_otp":
            sess   = oo_get_session(cid)
            wait   = _check_otp_cooldown(cid)
            if wait > 0: return tg_answer_cb(cb_id, f"انتظر {wait} ثانية", alert=True)
            msisdn = sess.get("msisdn")
            op     = sess.get("op", "ooredoo")
            if not msisdn: return
            tg_send(cid, f"{emo('time','⏳')} جاري الإرسال...")
            def _bg_resend():
                if op == "djezzy":
                    ok = djz_send_otp(msisdn)   # retry x3 مدمج
                    if ok:
                        tg_send(cid,
                            f"{emo('check','✅')} <b>تم إرسال OTP</b>\n\n"
                            f"{emo('info','📩')} إذا لم يصلك، اضغط إعادة الإرسال",
                            inline_kb=[[ibtn("🔄 إعادة الإرسال", callback="resend_otp",  emoji_key="refresh", color="success")],
                                       [ibtn("📱 تغيير الرقم",  callback="change_phone", emoji_key="phone",   color="primary")]])
                    else:
                        tg_send(cid, f"{emo('cross','❌')} فشل، انتظر دقيقة",
                                inline_kb=[[ibtn("📱 تغيير", callback="change_phone", emoji_key="phone", color="primary")]])
                else:
                    res = oo_send_otp(msisdn)
                    if res.get("ok"):
                        tg_send(cid,
                            f"{emo('check','✅')} <b>تم إرسال OTP</b>\n\n"
                            f"{emo('info','📩')} إذا لم يصلك، اضغط إعادة الإرسال",
                            inline_kb=[[ibtn("🔄 إعادة الإرسال", callback="resend_otp",  emoji_key="refresh", color="success")],
                                       [ibtn("📱 تغيير الرقم",  callback="change_phone", emoji_key="phone",   color="primary")]])
                    else:
                        tg_send(cid, f"{emo('cross','❌')} فشل، انتظر دقيقة",
                                inline_kb=[[ibtn("📱 تغيير", callback="change_phone", emoji_key="phone", color="primary")]])
            submit_task(_bg_resend)
            return

        if data == "admin_sms":
            oo_set_session(cid, {"state": "awaiting_phone"})
            return tg_send(cid,
                f"{emo('phone','📱')} أرسل رقمك:\n"
                f"🔴 أوريدو: <code>05XXXXXXXX</code>\n"
                f"🟡 جيزي:  <code>07XXXXXXXX</code>")
        if data == "admin_pwd":
            oo_set_session(cid, {"state": "admin_await_phone_pwd"})
            return tg_send(cid, f"{emo('phone','📱')} أرسل رقم أوريدو (05XXXXXXXX):")

    except Exception as e:
        logger.exception(f"cb error: {e}")

# ══════════════════════════════════════════════════
#  Polling — محسّن للضغط العالي
# ══════════════════════════════════════════════════
def get_updates(offset=None):
    try:
        r = _tg_session.get(f"{TELEGRAM_API}/getUpdates",
                            params={"timeout": 15, "offset": offset,
                                    "allowed_updates": json.dumps(["message","callback_query"])},
                            timeout=(5, 20))
        return r.json()
    except: return None

def polling_loop():
    logger.info("🚀 Ooredoo + Djezzy Bot v7.0 Started...")
    _tg_session.get(f"{TELEGRAM_API}/deleteWebhook", params={"drop_pending_updates": "true"})
    offset = None
    while True:
        try:
            data = get_updates(offset)
            if data and data.get("ok"):
                for upd in data.get("result", []):
                    offset = upd["update_id"] + 1
                    if msg := upd.get("message"):
                        cid  = msg.get("chat", {}).get("id")
                        text = msg.get("text", "").strip()
                        if cid and text:
                            if frm := msg.get("from"):
                                oo_save_base(cid, {"first_name": frm.get("first_name"),
                                                   "username":   frm.get("username")})
                            submit_task(handle, cid, text)
                    elif cb := upd.get("callback_query"):
                        cid = cb.get("message", {}).get("chat", {}).get("id")
                        if cid and cb.get("from"):
                            oo_save_base(cid, {"first_name": cb["from"].get("first_name"),
                                               "username":   cb["from"].get("username")})
                        submit_task(handle_callback, cb)
        except: time.sleep(1)

def run():
    _load_from_disk()
    polling_loop()

if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        with _lock: _do_save()
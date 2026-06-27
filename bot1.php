<?php

if (!isset($input)) {
    $input = json_decode(file_get_contents("php://input"), true);
}
if (!isset($event)) {
    $event = $input['entry'][0]['messaging'][0] ?? [];
}
$sender_id = $event['sender']['id'] ?? null;
$message   = $event['message']['text'] ?? '';

define('FB_TOKEN',        'EAAFYLlWaXQkBRmeSVCCkTskO6L3TDqBURP0I1DGsPlZADbPdKqhpJjMtsoP4Cr1bjeMPDHzlOSs0M4dcgW9uZBu6ma96nWqQ3K1qLstmXIXZBeRZBqMFsd7ecjihBU6fODYSZBxdbcy5q32Suz0gWmO05a9qao8E1VB3XRRHUa6db5khqyuuHfVhLYbdiXYpHjG0v53jGkwZDZD');
define('VERIFY_TOKEN',    'Yacin');
define('PROXY_LIST_FILE', '/tmp/proxies.json');
define('PROXY_API_URL',   'https://dev-bendjarayacine.pantheonsite.io/wp-admin/maint/proxy.json');
define('SESSIONS_DIR',    '/tmp/fb_sessions');
define('USERS_DIR',       '/tmp/fb_users');
define('PHONE_MAP_FILE',  '/tmp/fb_phone_map.json');
define('PENDING_DIR',     '/tmp/fb_pending');
define('DB_FILE',         '/tmp/fb_dedup.sqlite');
define('NEW_USERS_FILE',  '/tmp/fb_new_users.json');
define('RATE_LIMIT_DIR',  '/tmp/fb_rate_limit');
define('RATE_LIMIT_SECONDS', 600);

// ════════ Client Credentials ════════
define('CLIENT_ID_OLD',     '87pIExRhxBb3_wGsA5eSEfyATloa');
define('CLIENT_SECRET_OLD', 'uf82p68Bgisp8Yg1Uz8Pf6_v1XYa');
define('CLIENT_ID_NEW',     '6E6CwTkp8H1CyQxraPmcEJPQ7xka');
define('CLIENT_SECRET_NEW', 'MVpXHW_ImuMsxKIwrJpoVVMHjRsa');

// ════════ Algeria Match Gift ════════
define('ALGERIA_MATCH_QR',         'https://www.djezzy.dz/scanwin-wd26?1');
define('ALGERIA_MATCH_START_HOUR', 1);  // 1 صباحاً
define('ALGERIA_MATCH_END_HOUR',   5);  // 5 صباحاً

@mkdir(SESSIONS_DIR, 0777, true);
@mkdir(USERS_DIR,    0777, true);
@mkdir(PENDING_DIR,  0777, true);
@mkdir(RATE_LIMIT_DIR, 0777, true);

// ════════════════════════════════════════════════════════════════════════════
// قائمة العروض
// ════════════════════════════════════════════════════════════════════════════
define('OFFERS', [
    'BTL500MBDAY'            => ['name' => '📦 5GB - 90دج - 24h',          'display' => "الإنترنت: 5GB | السعر: 90 دج | المدة: 24 ساعة"],
    'DOVINTSPEEDDAY100MoPRE' => ['name' => '📦 300Mo - 30دج - 24h',        'display' => "الإنترنت: 300Mo | السعر: 30 دج | المدة: 24 ساعة"],
    'DOVINTSPEEDDAY250MoPRE' => ['name' => '📦 600Mo - 50دج - 24h',        'display' => "الإنترنت: 600Mo | السعر: 50 دج | المدة: 24 ساعة"],
    'DOVINTSPEEDDAY1GoPRE'   => ['name' => '📦 2Go - 100دج - 24h',         'display' => "الإنترنت: 2Go | السعر: 100 دج | المدة: 24 ساعة"],
    'OFFREJEUNE50'           => ['name' => '📦 1Go - 50دج - 24h',          'display' => "الإنترنت: 1Go | السعر: 50 دج | المدة: 24 ساعة"],
    'BTLINTSPEEDDAY2Go'      => ['name' => '🏷️ 4GB - 70دج - 24h',         'display' => "الإنترنت: 4GB | السعر: 70 دج | المدة: 24 ساعة"],
    'BTL4GBDAY'              => ['name' => '📦 5GB - 190دج - 24h',         'display' => "الإنترنت: 5GB | السعر: 190 دج | المدة: 24 ساعة"],
    'BTL1GBDAY'              => ['name' => '📦 4GB - 140دج - 24h',         'display' => "الإنترنت: 4GB | السعر: 140 دج | المدة: 24 ساعة"],
    'DOVINTSPEEDWEEK2GoPRE'  => ['name' => '📦 4Go - 150دج - 7أيام',       'display' => "الإنترنت: 4Go | السعر: 150 دج | المدة: 7 أيام"],
    'DOVINTSPEEDWEEK3GoPRE'  => ['name' => '📦 10Go - 300دج - 7أيام',      'display' => "الإنترنت: 10Go | السعر: 300 دج | المدة: 7 أيام"],
    'BTLDATA2WEEKS'          => ['name' => '📦 4GB - 400دج - 15يوم',       'display' => "الإنترنت: 4GB | السعر: 400 دج | المدة: 15 يوم"],
    '1GBFB3DAYInternet'      => ['name' => '📦 1GB(FB) - 70دج - 3أيام',    'display' => "الإنترنت: 1GB (Facebook) | السعر: 70 دج | المدة: 3 أيام"],
    'DOVINTSPEEDMONTH6GoPRE' => ['name' => '📦 12Go - 500دج - 30يوم',      'display' => "الإنترنت: 12Go | السعر: 500 دج | المدة: 30 يوم"],
    'DOVINTSPEEDMONTH15GoPRE'=> ['name' => '📦 30Go - 1000دج - 30يوم',     'display' => "الإنترنت: 30Go | السعر: 1000 دج | المدة: 30 يوم"],
    'DOVINTSPEEDMONTH30GoPRE'=> ['name' => '📦 60Go - 1500دج - 30يوم',     'display' => "الإنترنت: 60Go | السعر: 1500 دج | المدة: 30 يوم"],
    '2GBMONTH'               => ['name' => '📦 3GB - 250دج - 30يوم',       'display' => "الإنترنت: 3GB | السعر: 250 دج | المدة: 30 يوم"],
    'BTL500MBHOUR'           => ['name' => '⚡ 1GB - 40دج - 1ساعة',        'display' => "الإنترنت: 1GB | السعر: 40 دج | المدة: 1 ساعة"],
    'ImtiyazSurpriseData2hfbPRE' => ['name' => '📘 FB غير محدود - 50دج - 4h', 'display' => "الإنترنت: Facebook غير محدود | السعر: 50 دج | المدة: 4 ساعات"],
]);

define('OFFER_SHORTCUTS', [
    '5'  => 'BTL500MBDAY',
    '6'  => 'DOVINTSPEEDDAY100MoPRE',
    '7'  => 'DOVINTSPEEDDAY250MoPRE',
    '8'  => 'DOVINTSPEEDDAY1GoPRE',
    '9'  => 'OFFREJEUNE50',
    '10' => 'BTLINTSPEEDDAY2Go',
    '11' => 'BTL4GBDAY',
    '12' => 'BTL1GBDAY',
    '13' => 'DOVINTSPEEDWEEK2GoPRE',
    '14' => 'DOVINTSPEEDWEEK3GoPRE',
    '15' => 'BTLDATA2WEEKS',
    '16' => '1GBFB3DAYInternet',
    '17' => 'DOVINTSPEEDMONTH6GoPRE',
    '18' => 'DOVINTSPEEDMONTH15GoPRE',
    '19' => 'DOVINTSPEEDMONTH30GoPRE',
    '20' => '2GBMONTH',
    '21' => 'BTL500MBHOUR',
    '22' => 'ImtiyazSurpriseData2hfbPRE',
]);

// ════════════════════════════════════════════════════════════════════════════
// SQLite — Dedup + User Lock
// ════════════════════════════════════════════════════════════════════════════
function getDB(): PDO
{
    static $db = null;
    if ($db !== null) return $db;
    $db = new PDO('sqlite:' . DB_FILE);
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $db->exec("PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;");
    $db->exec("CREATE TABLE IF NOT EXISTS processed_events (event_id TEXT PRIMARY KEY, created_at INTEGER NOT NULL)");
    $db->exec("CREATE TABLE IF NOT EXISTS user_locks (psid TEXT PRIMARY KEY, locked_at INTEGER NOT NULL)");
    $db->exec("DELETE FROM processed_events WHERE created_at < " . (time() - 3600));
    $db->exec("DELETE FROM user_locks WHERE locked_at < " . (time() - 600));
    return $db;
}
function tryMarkEvent(string $id): bool
{
    try {
        $s = getDB()->prepare("INSERT OR IGNORE INTO processed_events (event_id, created_at) VALUES (?,?)");
        $s->execute([$id, time()]);
        return $s->rowCount() > 0;
    } catch (Throwable $e) { return true; }
}
function unmarkEvent(string $id): void
{
    try { getDB()->prepare("DELETE FROM processed_events WHERE event_id=?")->execute([$id]); } catch (Throwable $e) {}
}
function tryLockUser(string $psid): bool
{
    try {
        $s = getDB()->prepare("INSERT OR IGNORE INTO user_locks (psid, locked_at) VALUES (?,?)");
        $s->execute([$psid, time()]);
        return $s->rowCount() > 0;
    } catch (Throwable $e) { return true; }
}
function unlockUser(string $psid): void
{
    try { getDB()->prepare("DELETE FROM user_locks WHERE psid=?")->execute([$psid]); } catch (Throwable $e) {}
}
function dbg(string $m): void
{
    file_put_contents('/tmp/fb_debug.log', date('Y-m-d H:i:s') . " $m\n", FILE_APPEND);
}

// ════════════════════════════════════════════════════════════════════════════
// Rate Limit
// ════════════════════════════════════════════════════════════════════════════
function rateLimitFile(string $psid): string { return RATE_LIMIT_DIR . "/{$psid}.json"; }
function getFinalResultTimestamps(string $psid): array
{
    $f = rateLimitFile($psid);
    if (!file_exists($f)) return [];
    $d = json_decode(@file_get_contents($f), true);
    return is_array($d) ? $d : [];
}
function recordFinalResult(string $psid): void
{
    $list   = getFinalResultTimestamps($psid);
    $list[] = time();
    if (count($list) > 2) $list = array_slice($list, -2);
    @file_put_contents(rateLimitFile($psid), json_encode($list));
}
function checkRateLimit(string $psid): ?int
{
    $list = getFinalResultTimestamps($psid);
    if (count($list) < 2) return null;
    $elapsed = time() - $list[0];
    if ($elapsed < RATE_LIMIT_SECONDS) return RATE_LIMIT_SECONDS - $elapsed;
    return null;
}
function formatRemainingRateLimit(int $secondsLeft): string
{
    $minutes = (int)ceil($secondsLeft / 60);
    if ($minutes <= 1) return "أقل من دقيقة";
    return "{$minutes} دقيقة";
}
function rateLimitMessage(int $secondsLeft): string
{
    return "⏳ أنت ترسل طلبات كثيرة خلال فترة قصيرة.\n\n🔁 يرجى إعادة المحاولة بعد:\n🕐 الوقت المتبقي: " . formatRemainingRateLimit($secondsLeft) . "\n\nيتم تطبيق هذا القيد لضمان استمرارية عمل خدمة البوت بشكل جيد لجميع المستخدمين.";
}

// ════════════════════════════════════════════════════════════════════════════
// New Users Tracking
// ════════════════════════════════════════════════════════════════════════════
function isNewUser(string $psid): bool
{
    $map = file_exists(NEW_USERS_FILE) ? (json_decode(file_get_contents(NEW_USERS_FILE), true) ?? []) : [];
    return !isset($map[$psid]);
}
function markUserAsSeen(string $psid): void
{
    $map = file_exists(NEW_USERS_FILE) ? (json_decode(file_get_contents(NEW_USERS_FILE), true) ?? []) : [];
    if (!isset($map[$psid])) { $map[$psid] = time(); file_put_contents(NEW_USERS_FILE, json_encode($map)); }
}
function getAllKnownUsers(): array
{
    if (!file_exists(NEW_USERS_FILE)) return [];
    return array_keys(json_decode(file_get_contents(NEW_USERS_FILE), true) ?? []);
}

// ════════════════════════════════════════════════════════════════════════════
// Pending Operations
// ════════════════════════════════════════════════════════════════════════════
function setPending(string $psid, string $op): void
{
    file_put_contents(PENDING_DIR . "/{$psid}.json", json_encode(['op' => $op, 'ts' => time()]));
}
function clearPending(string $psid): void
{
    $f = PENDING_DIR . "/{$psid}.json";
    if (file_exists($f)) @unlink($f);
}
function getPending(string $psid): ?string
{
    $f = PENDING_DIR . "/{$psid}.json";
    if (!file_exists($f)) return null;
    $d = json_decode(@file_get_contents($f), true);
    if (!$d) return null;
    if (time() - ($d['ts'] ?? 0) > 600) { @unlink($f); return null; }
    return $d['op'] ?? null;
}

// ════════════════════════════════════════════════════════════════════════════
// Webhook Verify
// ════════════════════════════════════════════════════════════════════════════
if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    if (isset($_GET['hub_mode'], $_GET['hub_verify_token'], $_GET['hub_challenge'])
        && $_GET['hub_mode'] === 'subscribe'
        && $_GET['hub_verify_token'] === VERIFY_TOKEN) {
        http_response_code(200); echo $_GET['hub_challenge'];
    } else { http_response_code(403); echo 'Forbidden'; }
    exit;
}

// ════════════════════════════════════════════════════════════════════════════
// POST Handler
// ════════════════════════════════════════════════════════════════════════════
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $input = file_get_contents('php://input');
    $data  = json_decode($input, true);
    http_response_code(200);
    header('Content-Type: text/plain');
    echo 'EVENT_RECEIVED';
    if (function_exists('fastcgi_finish_request')) fastcgi_finish_request();
    if (!$data || ($data['object'] ?? '') !== 'page') exit;
    foreach ($data['entry'] as $entry) {
        foreach ($entry['messaging'] ?? [] as $event) {
            $psid = $event['sender']['id'] ?? null;
            if (!$psid) continue;
            $eid = buildEventId($psid, $event);
            if (!tryMarkEvent($eid)) { dbg("[DUP] $psid $eid"); continue; }
            if (!tryLockUser($psid)) { dbg("[LOCK] $psid busy"); unmarkEvent($eid); continue; }
            try { processEvent($psid, $event); }
            catch (Throwable $e) { dbg("[ERR] $psid " . $e->getMessage()); }
            finally { unlockUser($psid); }
        }
    }
    exit;
}
http_response_code(200); echo 'OK'; exit;

function buildEventId(string $psid, array $event): string
{
    if (isset($event['message'])) {
        $mid = $event['message']['mid'] ?? '';
        if ($mid !== '') return "msg_{$mid}";
        $ts = (int)($event['timestamp'] ?? time());
        return "msg_{$psid}_" . md5(trim($event['message']['text'] ?? '')) . "_" . (int)($ts / 10);
    }
    if (isset($event['postback'])) {
        $ts = (int)($event['timestamp'] ?? time());
        return "pb_{$psid}_" . md5($event['postback']['payload'] ?? '') . "_" . (int)($ts / 10);
    }
    return "ev_{$psid}_" . md5(json_encode($event));
}

// ════════════════════════════════════════════════════════════════════════════
// Process Event
// ════════════════════════════════════════════════════════════════════════════
function processEvent(string $psid, array $event): void
{
    $isNew = isNewUser($psid);
    markUserAsSeen($psid);
    if (isset($event['postback'])) { handlePostback($psid, $event['postback']['payload'] ?? ''); return; }
    if (!isset($event['message'])) return;
    $msg = $event['message'];
    if (isset($msg['sticker_id']) && $msg['sticker_id'] == 369239263222822) { sendMessage($psid, '👍'); return; }
    if (isset($msg['attachments']) && empty($msg['text'])) { sendMessage($psid, "🙄"); return; }
    if (isset($msg['quick_reply']['payload'])) { handlePostback($psid, $msg['quick_reply']['payload']); return; }
    $text   = trim($msg['text'] ?? '');
    $digits = preg_replace('/\D/', '', $text);
    if ($text === '') { if ($isNew) sendWelcomeNew($psid); else sendWelcome($psid); return; }
    if (preg_match('/@#(.+?)@#/su', $text, $adMatch)) { handleAdminBroadcast($psid, trim($adMatch[1])); return; }

    $session = getSession($psid);
    $state   = $session['state'] ?? 'idle';

    if ($state === 'awaiting_otp') { handleAwaitingOtp($psid, $text, $session); return; }
    if ($state === 'awaiting_offer_otp') { handleOfferOtp($psid, $text, $session); return; }
    if ($state === 'awaiting_invite_phone') { handleInvitePhoneInput($psid, $text, $session); return; }
    if ($state === 'awaiting_invitee_otp') { handleInviteeOtp($psid, $text, $session); return; }

    $pending = getPending($psid);
    if ($pending !== null) { sendMessage($psid, "⏳ انتظر، نحن نقوم بـ {$pending}\nبعدها يمكنك الطلب."); return; }

    if (preg_match('/^07\d{8}$/', $digits)) { handleNewPhone($psid, $digits); return; }
    if (preg_match('/^05\d{8}$/', $digits)) { sendMessage($psid, "⏳ سيتم إضافة Ooredoo قريباً."); return; }
    if (preg_match('/^06\d{8}$/', $digits)) { sendMessage($psid, "❌ لا يوجد تسجيل Mobilis."); return; }

    if ($state === 'menu' || $state === 'offers') {
        if     ($text === '1') handlePostback($psid, 'MENU_2G');
        elseif ($text === '2') handlePostback($psid, 'MENU_70DZ');
        elseif ($text === '3') handlePostback($psid, 'MENU_INVITE');
        elseif ($text === '4') handlePostback($psid, 'MENU_MORE_OFFERS');
        elseif ($text === '30') {
            $sess = getSession($psid); $user = getUser($psid);
            if (!$user || empty($user['access_token'])) {
                sendMessage($psid, "⚠️ يجب تسجيل الدخول أولاً، أرسل رقم هاتفك.");
                return;
            }
            if (!empty($sess['msisdn'])) $user['msisdn'] = $sess['msisdn'];
            activateAlgeriaMatchGift($psid, $user);
        }
        elseif (isset(OFFER_SHORTCUTS[$text])) {
            handlePostback($psid, 'ACTIVATE_OFFER_' . OFFER_SHORTCUTS[$text]);
        } else {
            sendMessage($psid,
                "❌ اختيار خاطئ\n\n📌 قم باستخدام الأزرار الموجودة بالأسفل\nإذا لم تظهر لك الأزرار أرسل الرقم المناسب 👇\n\n━━━━━━━━━━━━━━\n\n" .
                "1️⃣ لتفعيل 2G الأسبوعية\n📩 أرسل: 1\n\n2️⃣ لتفعيل عرض 4GB بـ 70دج 🏷️\n📩 أرسل: 2\n\n3️⃣ لإرسال دعوة 🎁\n📩 أرسل: 3\n\n4️⃣ للمزيد من العروض 📦\n📩 أرسل: 4\n\n━━━━━━━━━━━━━━"
            );
        }
        return;
    }
    if ($isNew) sendWelcomeNew($psid); else sendWelcome($psid);
}

// ════════════════════════════════════════════════════════════════════════════
// Admin Broadcast
// ════════════════════════════════════════════════════════════════════════════
function handleAdminBroadcast(string $psid, string $adText): void
{
    $users = getAllKnownUsers(); $count = 0;
    foreach ($users as $uid) { sendMessage($uid, "📢 إعلان:\n\n" . $adText); $count++; usleep(100000); }
    sendMessage($psid, "✅ تم إرسال الإعلان إلى {$count} مستخدم.");
    dbg("[BROADCAST] from={$psid} users={$count} msg=" . substr($adText, 0, 100));
}

// ════════════════════════════════════════════════════════════════════════════
// OTP Handler — تسجيل الدخول العادي
// ════════════════════════════════════════════════════════════════════════════
function handleAwaitingOtp(string $psid, string $text, array $session): void
{
    $msisdn       = $session['msisdn'] ?? '';
    $phoneDisplay = '0' . substr($msisdn, 3);
    if (trim($text) === '0') {
        clearSession($psid);
        sendMessage($psid, "✅ تم إلغاء عملية التسجيل.\n\n📱 أرسل رقمك في أي وقت للبدء من جديد.");
        return;
    }
    $digits = preg_replace('/\D/', '', $text);
    if (preg_match('/^07\d{8}$/', $digits)) {
        $newMsisdn = '213' . substr($digits, 1);
        sendMessage($psid, "📲 جاري إعادة إرسال رمز التحقق إلى الرقم {$digits}...");
        sendOTPAndWait($psid, $newMsisdn, $digits);
        return;
    }
    if (!preg_match('/\b(\d{6})\b/', $text, $m)) {
        sendMessage($psid,
            "⚠️ الرجاء إدخال رمز التحقق المكوّن من 6 أرقام.\n\n📱 أو أرسل رقم هاتفك مجدداً لاستقبال رمز جديد\n🔢 الرمز أُرسل إلى: {$phoneDisplay}\n\n❌ لإلغاء العملية أرسل: 0"
        );
        return;
    }
    if (empty($msisdn)) { clearSession($psid); sendMessage($psid, "❌ حدث خطأ في الجلسة، أرسل رقمك مجدداً."); return; }
    $result = verifyOTP($msisdn, $m[1]);
    if ($result === 'wrong_otp') {
        sendMessage($psid, "❌ الرمز المُدخل خاطئ!\n\n🔄 أعد إرسال الرمز الصحيح\n📱 أو أرسل رقم هاتفك مجدداً لاستقبال رمز جديد\n\n❌ لإلغاء العملية أرسل: 0");
    } elseif ($result === false) {
        sendMessage($psid, "❌ حدث خطأ، حاول مجدداً.\n\n📱 يمكنك إرسال رقمك مجدداً لاستقبال رمز جديد\n\n❌ لإلغاء العملية أرسل: 0");
    } else {
        saveUser($psid, ['user_id' => $psid, 'msisdn' => $msisdn, 'access_token' => $result['access_token'], 'refresh_token' => $result['refresh_token']]);
        savePhoneOwner($msisdn, $psid);
        setSession($psid, ['state' => 'menu', 'msisdn' => $msisdn]);
        sendMessage($psid, "✅ تم تسجيل الدخول بنجاح!");
        sendMenu($psid);
        sendAlgeriaMatchGiftPromo($psid);
    }
}

// ════════════════════════════════════════════════════════════════════════════
// OTP Handler — تفعيل العرض بالطريقة الجديدة
// ════════════════════════════════════════════════════════════════════════════
function handleOfferOtp(string $psid, string $text, array $session): void
{
    $msisdn      = $session['msisdn'] ?? '';
    $packageCode = $session['pending_package'] ?? '';
    $phoneDisplay = '0' . substr($msisdn, 3);

    if (trim($text) === '0') {
        clearSession($psid);
        setSession($psid, ['state' => 'menu', 'msisdn' => $msisdn]);
        sendMessage($psid, "✅ تم إلغاء عملية تفعيل العرض.");
        sendMenu($psid);
        return;
    }
    $digits = preg_replace('/\D/', '', $text);
    if (preg_match('/^07\d{8}$/', $digits)) {
        $newMsisdn = '213' . substr($digits, 1);
        sendMessage($psid, "📲 جاري إعادة إرسال رمز التحقق إلى الرقم {$digits}...");
        sendNewOTPAndWaitForOffer($psid, $newMsisdn, $digits, $packageCode);
        return;
    }
    if (!preg_match('/\b(\d{6})\b/', $text, $m)) {
        sendMessage($psid,
            "⚠️ الرجاء إدخال رمز التحقق المكوّن من 6 أرقام.\n\n📱 أو أرسل رقم هاتفك مجدداً لاستقبال رمز جديد\n🔢 الرمز أُرسل إلى: {$phoneDisplay}\n\n❌ لإلغاء العملية أرسل: 0"
        );
        return;
    }
    if (empty($msisdn) || empty($packageCode)) {
        clearSession($psid);
        sendMessage($psid, "❌ حدث خطأ في الجلسة، أرسل رقمك مجدداً.");
        return;
    }
    $result = verifyOTPNew($msisdn, $m[1]);
    if ($result === 'wrong_otp') {
        sendMessage($psid, "❌ الرمز المُدخل خاطئ!\n\n🔄 أعد إرسال الرمز الصحيح\n📱 أو أرسل رقم هاتفك مجدداً لاستقبال رمز جديد\n\n❌ لإلغاء العملية أرسل: 0");
        return;
    }
    if ($result === false) {
        sendMessage($psid, "❌ حدث خطأ في التحقق، حاول مجدداً.\n\n📱 يمكنك إرسال رقمك مجدداً لاستقبال رمز جديد\n\n❌ لإلغاء العملية أرسل: 0");
        return;
    }
    $newAccessToken  = $result['access_token'];
    $newRefreshToken = $result['refresh_token'];
    $userForOffer = array_merge(getUser($psid) ?? [], [
        'msisdn'        => $msisdn,
        'access_token'  => $newAccessToken,
        'refresh_token' => $newRefreshToken,
    ]);
    setSession($psid, ['state' => 'menu', 'msisdn' => $msisdn]);
    sendMessage($psid, "✅ تم التحقق بنجاح! جاري تفعيل العرض...");
    activateOfferNew($psid, $userForOffer, $packageCode);
}

// ════════════════════════════════════════════════════════════════════════════
// Phone Handler
// ════════════════════════════════════════════════════════════════════════════
function handleNewPhone(string $psid, string $phone): void
{
    $msisdn = '213' . substr($phone, 1);
    $owner  = getPhoneOwner($msisdn);
    if ($owner === $psid) {
        $user = getUser($psid);
        if ($user && !empty($user['access_token'])) {
            $user['msisdn'] = $msisdn;
            saveUser($psid, $user);
            $refreshed = refreshAccessToken($user['refresh_token'], $msisdn, $psid);
            if ($refreshed) {
                saveUser($psid, array_merge($user, ['msisdn' => $msisdn, 'access_token' => $refreshed['access_token'], 'refresh_token' => $refreshed['refresh_token']]));
                setSession($psid, ['state' => 'menu', 'msisdn' => $msisdn]);
                sendMessage($psid, "✅ تم التعرف على رقمك بنجاح!");
                sendMenu($psid);
                sendAlgeriaMatchGiftPromo($psid);
                return;
            }
        }
    } elseif ($owner !== null) {
        sendMessage($psid, "🚫 أنت لست صاحب الرقم، يجب إثبات الهوية.\n\n📲 سيتم إرسال رمز تحقق إلى هذا الرقم...");
    }
    sendOTPAndWait($psid, $msisdn, $phone);
}
function sendOTPAndWait(string $psid, string $msisdn, string $phone): void
{
    if (sendDjezzyOTP($msisdn)) {
        setSession($psid, ['state' => 'awaiting_otp', 'msisdn' => $msisdn]);
        sendMessage($psid,
            "✅ تم إرسال رمز التحقق إلى الرقم {$phone}.\n\n🔢 الرجاء إدخال الرمز المكوّن من 6 أرقام:\n\n📱 أو أرسل رقمك مجدداً لاستقبال رمز جديد\n\n❌ لإلغاء العملية أرسل: 0"
        );
    } else {
        sendMessage($psid, "سيرفر جازي غير متاح حاليا نعمل على اصلاحه 🧑‍🔧 يمكنك التسجيل عبر التطبيق الخاص بنا رابط تحميله https://dev-tasjilapp.pantheonsite.io/wp-admin/Tasjil-APP-Downlod/update.php");
    }
}

function sendNewOTPAndWaitForOffer(string $psid, string $msisdn, string $phone, string $packageCode): void
{
    if (sendDjezzyOTPNew($msisdn)) {
        setSession($psid, ['state' => 'awaiting_offer_otp', 'msisdn' => $msisdn, 'pending_package' => $packageCode]);
        $offerInfo  = OFFERS[$packageCode] ?? null;
        $offerLabel = $offerInfo ? $offerInfo['name'] : $packageCode;
        sendMessage($psid,
            "✅ تم إرسال رمز التحقق إلى الرقم {$phone}.\n\n" .
            "📌 نقوم الآن بتجربة طريقة تفعيل أخرى للعرض.\n\n" .
            "🔢 الرجاء إدخال الرمز المكوّن من 6 أرقام لتفعيل العرض:\n" .
            "📦 العرض: {$offerLabel}\n\n" .
            "📱 أو أرسل رقمك مجدداً لاستقبال رمز جديد\n\n" .
            "❌ لإلغاء العملية أرسل: 0"
        );
    } else {
        sendMessage($psid, "سيرفر جازي غير متاح حاليا 🧑‍🔧");
    }
}

// ════════════════════════════════════════════════════════════════════════════
// Postback Handler
// ════════════════════════════════════════════════════════════════════════════
function handlePostback(string $psid, string $payload): void
{
    if (str_starts_with($payload, 'ACTIVATE_OFFER_')) {
        $packageCode = substr($payload, strlen('ACTIVATE_OFFER_'));
        $sess = getSession($psid); $user = getUser($psid);
        if (!$user || empty($user['access_token'])) { sendMessage($psid, "⚠️ يجب تسجيل الدخول أولاً، أرسل رقم هاتفك."); return; }
        if (!empty($sess['msisdn'])) $user['msisdn'] = $sess['msisdn'];
        setSession($psid, array_merge($sess, ['state' => 'menu']));
        activateOffer($psid, $user, $packageCode);
        return;
    }
    switch ($payload) {
        case 'GET_STARTED':
            sendWelcomeNew($psid);
            break;
        case 'ACTIVATE_ALGERIA_MATCH':
            $sess = getSession($psid); $user = getUser($psid);
            if (!$user || empty($user['access_token'])) {
                sendMessage($psid, "⚠️ يجب تسجيل الدخول أولاً، أرسل رقم هاتفك.");
                return;
            }
            if (!empty($sess['msisdn'])) $user['msisdn'] = $sess['msisdn'];
            activateAlgeriaMatchGift($psid, $user);
            break;
        case 'MENU_2G':
            $sess = getSession($psid); $user = getUser($psid);
            if (!$user || empty($user['access_token'])) { sendMessage($psid, "⚠️ يجب تسجيل الدخول أولاً، أرسل رقم هاتفك."); return; }
            if (!empty($sess['msisdn'])) $user['msisdn'] = $sess['msisdn'];
            setSession($psid, array_merge($sess, ['state' => 'menu']));
            activate2G($psid, $user); break;
        case 'MENU_70DZ':
            $sess = getSession($psid); $user = getUser($psid);
            if (!$user || empty($user['access_token'])) { sendMessage($psid, "⚠️ يجب تسجيل الدخول أولاً، أرسل رقم هاتفك."); return; }
            if (!empty($sess['msisdn'])) $user['msisdn'] = $sess['msisdn'];
            setSession($psid, array_merge($sess, ['state' => 'menu']));
            activate70DZ($psid, $user); break;
        case 'MENU_INVITE':
            $sess = getSession($psid); $user = getUser($psid);
            if (!$user || empty($user['access_token'])) { sendMessage($psid, "⚠️ يجب تسجيل الدخول أولاً، أرسل رقم هاتفك."); return; }
            if (!empty($sess['msisdn'])) $user['msisdn'] = $sess['msisdn'];
            handleInviteStart($psid, $user); break;
        case 'MENU_MORE_OFFERS': sendMoreOffers($psid); break;
        case 'BACK_MENU': sendMenu($psid); break;
        default: sendWelcome($psid);
    }
}

// ════════════════════════════════════════════════════════════════════════════
// Algeria Match Gift — هدية مباراة الجزائر
// ════════════════════════════════════════════════════════════════════════════
function getMatchGiftTimeRemaining(): ?int
{
    // التوقيت الجزائري UTC+1
    $nowAlgeria = time() + 3600;
    $hour = (int)date('G', $nowAlgeria);

    if ($hour >= ALGERIA_MATCH_START_HOUR && $hour < ALGERIA_MATCH_END_HOUR) {
        // حساب وقت الانتهاء بتوقيت UTC
        $todayDate     = date('Y-m-d', $nowAlgeria);
        $endAlgeria    = strtotime($todayDate . ' ' . ALGERIA_MATCH_END_HOUR . ':00:00') - 3600;
        return max(0, $endAlgeria - time());
    }
    return null;
}

function formatMatchTimeRemaining(int $seconds): string
{
    if ($seconds <= 0) return "0 دقيقة";
    $h = (int)($seconds / 3600);
    $m = (int)(($seconds % 3600) / 60);
    if ($h > 0 && $m > 0) return "{$h} ساعة و{$m} دقيقة";
    if ($h > 0) return "{$h} ساعة";
    return "{$m} دقيقة";
}

function sendAlgeriaMatchGiftPromo(string $psid): void
{
    $remaining = getMatchGiftTimeRemaining();
    if ($remaining === null) return; // خارج نطاق الوقت، لا ترسل

    $timeLeft = formatMatchTimeRemaining($remaining);

    fbApiCall(json_encode([
        'recipient'      => ['id' => $psid],
        'messaging_type' => 'RESPONSE',
        'message'        => [
            'text' =>
                "🇩🇿🔥 هدية خاصة بمباراة الجزائر!\n\n" .
                "━━━━━━━━━━━━━━━━━━━━━━\n\n" .
                "🎁 احصل على 12Go مجاناً 🎉\n" .
                "⏳ صالحة لمدة 5 ساعات فقط\n" .
                "🕐 من 1:00 صباحاً حتى 5:00 صباحاً\n\n" .
                "━━━━━━━━━━━━━━━━━━━━━━\n\n" .
                "⚠️ سارع! متبقي فقط: {$timeLeft}\n\n" .
                "📩 أرسل الرقم 30 للتفعيل الفوري",
            'quick_replies' => [
                [
                    'content_type' => 'text',
                    'title'        => '🇩🇿 تفعيل هدية المباراة',
                    'payload'      => 'ACTIVATE_ALGERIA_MATCH',
                ],
            ],
        ],
    ], JSON_UNESCAPED_UNICODE));
}

function activateAlgeriaMatchGift(string $psid, array $user): void
{
    $rl = checkRateLimit($psid);
    if ($rl !== null) { sendMessage($psid, rateLimitMessage($rl)); return; }

    // التحقق من نافذة الوقت
    $remaining = getMatchGiftTimeRemaining();
    if ($remaining === null) {
        sendMessage($psid,
            "⏰ انتهى وقت الهدية!\n\n" .
            "كانت الهدية متاحة من 1:00 صباحاً حتى 5:00 صباحاً فقط.\n\n" .
            "⚡ قناة التلغرام: https://t.me/tasjilbott"
        );
        return;
    }

    $msisdn        = $user['msisdn'];
    $accessToken   = $user['access_token'];
    $displayMasked = substr($msisdn, 0, 4) . 'xxxx' . substr($msisdn, -2);
    $timeLeft      = formatMatchTimeRemaining($remaining);

    sendMessage($psid,
        "🔄 جاري تفعيل هدية مباراة الجزائر 🇩🇿...\n\n" .
        "⏳ الوقت المتبقي للهدية: {$timeLeft}"
    );

    $url     = "https://apim.djezzy.dz/mobile-api/api/v1/services/scan/activate-reward/{$msisdn}";
    $payload = json_encode(['qrCode' => ALGERIA_MATCH_QR]);
    $headers = [
        'Content-Type: application/json',
        'Accept: application/json',
        'Accept-Encoding: gzip',
        "Authorization: Bearer {$accessToken}",
        'User-Agent: MobileApp/3.0.0',
    ];

    $proxies    = array_merge(loadProxies(), refreshProxies());
    $maxRetries = 3;

    for ($attempt = 1; $attempt <= $maxRetries; $attempt++) {
        $httpCode     = 0;
        $responseData = null;
        $gotResponse  = false;

        foreach ($proxies as $p) {
            $pp = parseProxy($p);
            $ch = curl_init($url);
            curl_setopt_array($ch, [
                CURLOPT_POST           => true,
                CURLOPT_POSTFIELDS     => $payload,
                CURLOPT_HTTPHEADER     => $headers,
                CURLOPT_RETURNTRANSFER => true,
                CURLOPT_ENCODING       => 'gzip',
                CURLOPT_TIMEOUT        => 12,
                CURLOPT_CONNECTTIMEOUT => 5,
                CURLOPT_SSL_VERIFYPEER => false,
                CURLOPT_PROXY          => $pp['host'],
                CURLOPT_PROXYUSERPWD   => $pp['userpass'],
                CURLOPT_PROXYTYPE      => CURLPROXY_HTTP,
                CURLOPT_FOLLOWLOCATION => true,
            ]);
            $body     = curl_exec($ch);
            $httpCode = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
            $errno    = curl_errno($ch);
            curl_close($ch);

            $bodyStr = (string)$body;
            dbg("[MATCH_GIFT] attempt={$attempt} http={$httpCode} body=" . substr($bodyStr, 0, 300));
            file_put_contents('/tmp/match_gift.log',
                date('Y-m-d H:i:s') . " attempt={$attempt} http={$httpCode} body=" . substr($bodyStr, 0, 400) . "\n",
                FILE_APPEND
            );

            if ($errno || !$body || stripos($bodyStr, '<html') !== false) continue;

            $responseData = @json_decode($bodyStr, true);
            $gotResponse  = true;
            break;
        }

        if (!$gotResponse) {
            usleep(1000000);
            continue;
        }

        // ─── نجاح ───────────────────────────────────────────────────────────
        if ($httpCode === 200 || $httpCode === 201) {
            recordFinalResult($psid);
            sendMessage($psid,
                "🎉 تم تفعيل الهدية بنجاح!\n\n" .
                "استمتع بمباراة الجزائر 🇩🇿⚽\n\n" .
                "✅ الرقم: {$displayMasked}\n" .
                "🎁 الهدية: 12Go صالحة لمدة 5 ساعات\n\n" .
                "⚡ قناة التلغرام: https://t.me/tasjilbott"
            );
            sendMessage($psid, "لاتنسى متابعة حساب المطور </> : https://www.facebook.com/profile.php?id=100052854003446");
            clearSession($psid);
            return;
        }

        // ─── مستفيد مسبقاً أو غير مؤهل ─────────────────────────────────────
        if ($httpCode === 400) {
            recordFinalResult($psid);
            sendMessage($psid,
                "⚠️ لقد استفدت من الهدية مسبقاً أو أن رقمك غير مؤهل لهذه الهدية.\n\n" .
                "⚡ قناة التلغرام: https://t.me/tasjilbott"
            );
            clearSession($psid);
            return;
        }

        // ─── أخطاء أخرى — إعادة المحاولة ────────────────────────────────────
        dbg("[MATCH_GIFT] attempt={$attempt} unexpected http={$httpCode}, retrying...");
        usleep(1000000);
    }

    // ─── فشل بعد 3 محاولات ──────────────────────────────────────────────────
    sendMessage($psid,
        "❌ حدث خطأ أثناء تفعيل الهدية بعد عدة محاولات.\n\n" .
        "يرجى المحاولة مجدداً.\n\n" .
        "⚡ قناة التلغرام: https://t.me/tasjilbott"
    );
    clearSession($psid);
}

// ════════════════════════════════════════════════════════════════════════════
// activateOffer — يجرب الطريقة القديمة أولاً، وعند فشلها يجرب الجديدة
// ════════════════════════════════════════════════════════════════════════════
function activateOffer(string $psid, array $user, string $packageCode): void
{
    $rl = checkRateLimit($psid);
    if ($rl !== null) { sendMessage($psid, rateLimitMessage($rl)); return; }

    $msisdn        = $user['msisdn'];
    $accessToken   = $user['access_token'];
    $refreshToken  = $user['refresh_token'];
    $displayMasked = substr($msisdn, 0, 4) . 'xxxx' . substr($msisdn, -2);
    $offerInfo     = OFFERS[$packageCode] ?? null;
    $offerLabel    = $offerInfo ? $offerInfo['name'] : $packageCode;

    setPending($psid, "تفعيل {$offerLabel} 🔖");
    sendMessage($psid, "جاري تفعيل العرض {$offerLabel} 🔄...");

    // ─── المرحلة 1: محاولة واحدة بالطريقة القديمة ──────────────────────────
    $raw = activateProductCurl($msisdn, $accessToken, json_encode(['packageCode' => $packageCode]), 'actOffer');

    if ($raw !== null) {
        $httpCode     = $raw['http_code'];
        $responseData = $raw['json'];
        $bodyStr      = $raw['body'];
        dbg("[OFFER_OLD:{$packageCode}] http={$httpCode} body=" . substr($bodyStr, 0, 300));

        if (is_array($responseData)) {
            $innerStatus = (int)($responseData['status'] ?? 0);
            $innerMsg    = $responseData['message'] ?? '';

            if ($httpCode === 402 || $innerStatus === 402) {
                clearPending($psid);
                recordFinalResult($psid);
                $balance    = $responseData['data']['mainBalance'] ?? null;
                $balanceMsg = ($balance !== null) ? "رصيدك الحالي: {$balance} دج 💳\n" : "";
                sendMessage($psid, "حدث خطأ ⚠️ رصيدك غير كافي 💰 لتفعيل هذا العرض 🔖 😔\n{$balanceMsg}\n⚡ قناة التلقرام : https://t.me/tasjilbott");
                clearSession($psid); sendMessage($psid, ""); return;
            }

            if ($httpCode === 200 || $httpCode === 201 || $innerStatus === 200) {
                $msgStr = is_array($innerMsg) ? ($innerMsg['en'] ?? '') : (string)$innerMsg;
                if (stripos($msgStr, 'successfully') !== false || $httpCode === 201 || $innerStatus === 200) {
                    clearPending($psid);
                    recordFinalResult($psid);
                    $detailMsg = $offerInfo ? "\n✅ تفاصيل العرض: " . $offerInfo['display'] : "";
                    sendMessage($psid,
                        "⭐ تم تفعيل العرض بنجاح 🎁 للرقم {$displayMasked}\n✅ اسم العرض: {$offerLabel}{$detailMsg}\n\n⚡ قناة التلقرام : https://t.me/tasjilbott"
                    );
                    sendMessage($psid, "");
                    clearSession($psid);
                    sendMessage($psid, "لاتنسى متابعة حساب المطور </> : https://www.facebook.com/profile.php?id=100052854003446");
                    return;
                }
            }
        }
    }

    // ─── المرحلة 2: الطريقة القديمة فشلت — جرب الجديدة ────────────────────
    clearPending($psid);
    sendMessage($psid, "⚠️ تعذر تفعيل العرض بالطريقة الأولى، جارٍ تجربة طريقة أخرى...");
    $phoneDisplay = '0' . substr($msisdn, 3);
    sendNewOTPAndWaitForOffer($psid, $msisdn, $phoneDisplay, $packageCode);
}

// ════════════════════════════════════════════════════════════════════════════
// activateOfferNew — التفعيل بالطريقة الجديدة بعد OTP
// ════════════════════════════════════════════════════════════════════════════
function activateOfferNew(string $psid, array $user, string $packageCode): void
{
    $msisdn        = $user['msisdn'];
    $accessToken   = $user['access_token'];
    $refreshToken  = $user['refresh_token'];
    $displayMasked = substr($msisdn, 0, 4) . 'xxxx' . substr($msisdn, -2);
    $offerInfo     = OFFERS[$packageCode] ?? null;
    $offerLabel    = $offerInfo ? $offerInfo['name'] : $packageCode;

    $maxAttempts       = 10;
    $maxTokenRefresh   = 3;
    $tokenRefreshCount = 0;

    setPending($psid, "تفعيل {$offerLabel} 🔖");

    for ($attempt = 1; $attempt <= $maxAttempts; $attempt++) {
        $raw = activateProductCurlNew($msisdn, $accessToken, $packageCode, 'actOfferNew');
        if ($raw === null) { usleep(1000000); continue; }

        $httpCode     = $raw['http_code'];
        $responseData = $raw['json'];
        $bodyStr      = $raw['body'];
        dbg("[OFFER_NEW:{$packageCode}] attempt={$attempt} http={$httpCode} body=" . substr($bodyStr, 0, 300));

        if (!is_array($responseData)) { if ($httpCode === 429) usleep(2000000); else usleep(1000000); continue; }

        $fault = $responseData['fault'] ?? null;
        if ($fault !== null) {
            $faultCode = (int)($fault['code'] ?? 0);
            if ($faultCode === 900901) {
                if ($tokenRefreshCount >= $maxTokenRefresh) { break; }
                $tokenRefreshCount++;
                $refreshed = refreshAccessTokenNew($refreshToken, $msisdn, $psid, $packageCode);
                if ($refreshed === false) { clearPending($psid); return; }
                $accessToken  = $refreshed['access_token'];
                $refreshToken = $refreshed['refresh_token'];
                $attempt--;
                continue;
            }
            usleep(1000000); continue;
        }

        $innerStatus = (int)($responseData['status'] ?? 0);

        if ($httpCode === 402 || $innerStatus === 402) {
            clearPending($psid);
            recordFinalResult($psid);
            $balance    = $responseData['data']['mainBalance'] ?? null;
            $balanceMsg = ($balance !== null) ? "رصيدك الحالي: {$balance} دج 💳\n" : "";
            sendMessage($psid, "حدث خطأ ⚠️ رصيدك غير كافي 💰 لتفعيل هذا العرض 🔖 😔\n{$balanceMsg}\n⚡ قناة التلقرام : https://t.me/tasjilbott");
            clearSession($psid); sendMessage($psid, ""); return;
        }

        if ($httpCode === 200 || $httpCode === 201) {
            clearPending($psid);
            recordFinalResult($psid);
            $detailMsg = $offerInfo ? "\n✅ تفاصيل العرض: " . $offerInfo['display'] : "";
            sendMessage($psid,
                "⭐ تم تفعيل العرض بنجاح 🎁 للرقم {$displayMasked}\n✅ اسم العرض: {$offerLabel}{$detailMsg}\n\n⚡ قناة التلقرام : https://t.me/tasjilbott"
            );
            sendMessage($psid, "");
            clearSession($psid);
            sendMessage($psid, "لاتنسى متابعة حساب المطور </> : https://www.facebook.com/profile.php?id=100052854003446");
            return;
        }

        if ($httpCode === 429) { usleep(2000000); continue; }
        if ($httpCode === 500) { usleep(1000000); continue; }
        usleep(1000000);
    }

    clearPending($psid);
    recordFinalResult($psid);
    sendMessage($psid, "عذرا ⚠️ تعذر تفعيل العرض، يبدو أن شريحتك لا تدعم هذا العرض أو حدث خطأ مؤقت\n\n⚡ قناة التلقرام : https://t.me/tasjilbott");
    clearSession($psid);
    sendMessage($psid, "");
}

// ════════════════════════════════════════════════════════════════════════════
// activate70DZ
// ════════════════════════════════════════════════════════════════════════════
function activate70DZ(string $psid, array $user): void
{
    activateOffer($psid, $user, 'BTLINTSPEEDDAY2Go');
}

// ════════════════════════════════════════════════════════════════════════════
// activate2G
// ════════════════════════════════════════════════════════════════════════════
function activate2G(string $psid, array $user): void
{
    $rl = checkRateLimit($psid);
    if ($rl !== null) { sendMessage($psid, rateLimitMessage($rl)); return; }

    $msisdn        = $user['msisdn'];
    $accessToken   = $user['access_token'];
    $refreshToken  = $user['refresh_token'];
    $displayMasked = substr($msisdn, 0, 4) . 'xxxx' . substr($msisdn, -2);

    sendMessage($psid, "🔍 جاري فحص تاريخ آخر تفعيل...");
    $history = fetchSubscriptionHistory($msisdn, $accessToken);
    if ($history !== null) {
        $lastTs = getLastWalkWinDate($history);
        if ($lastTs !== null) {
            $elapsed   = time() - $lastTs;
            $sevenDays = 7 * 24 * 3600;
            if ($elapsed < $sevenDays) {
                $remaining = $sevenDays - $elapsed;
                recordFinalResult($psid);
                sendMessage($psid,
                    "عذرا 😬 لم تكمل أسبوع ⚠️\n\n⏳ الوقت المتبقي: " . formatTimeRemaining($remaining) .
                    "\n\nأعد المحاولة بعد انتهاء هذه المدة 📆\n\n⚡ قناة التلقرام : https://t.me/tasjilbott"
                );
                clearSession($psid); sendMessage($psid, ""); return;
            }
        }
    }

    $maxAttempts       = 30;
    $maxTokenRefresh   = 3;
    $tokenRefreshCount = 0;
    setPending($psid, 'تفعيل 2G 🎁');
    sendMessage($psid, "جاري تفعيل 2G 🎁 🔄...");

    for ($attempt = 1; $attempt <= $maxAttempts; $attempt++) {
        $raw = activateWalkRewardCurl($msisdn, $accessToken, json_encode(['packageCode' => 'GIFTWALKWIN2GO']), 'act2g');
        if ($raw === null) { usleep(1000000); continue; }
        $httpCode     = $raw['http_code'];
        $responseData = $raw['json'];
        $bodyStr      = $raw['body'];
        dbg("[2G] attempt={$attempt} http={$httpCode} body=" . substr($bodyStr, 0, 300));
        if (!is_array($responseData)) { if ($httpCode === 429) usleep(2000000); else usleep(1000000); continue; }
        $fault = $responseData['fault'] ?? null;
        if ($fault !== null && (int)($fault['code'] ?? 0) === 900901) {
            if ($tokenRefreshCount >= $maxTokenRefresh) {
                clearPending($psid);
                sendMessage($psid, "فشل تحديث الجلسة بعد عدة محاولات، الرجاء إعادة ارسال رقمك للتسجيل من جديد");
                clearSession($psid); return;
            }
            $tokenRefreshCount++;
            $refreshed = refreshAccessToken($refreshToken, $msisdn, $psid);
            if ($refreshed === false) { clearPending($psid); clearSession($psid); return; }
            $accessToken  = $refreshed['access_token'];
            $refreshToken = $refreshed['refresh_token'];
            saveUser($psid, array_merge($user, ['access_token' => $accessToken, 'refresh_token' => $refreshToken]));
            $attempt--; continue;
        }
        $innerStatus = (int)($responseData['status'] ?? 0);
        if ($httpCode === 402 || $innerStatus === 402 || $httpCode === 403 || $innerStatus === 403) {
            clearPending($psid); recordFinalResult($psid);
            sendMessage($psid,
                "عذرا ⚠️ يلزمك الاشتراك في باقة 100da 💰 (عشرة الاف) او اكثر ثم بعدها يمكنك الاستفادة من 2G 🎁 المجانية كل اسبوع طيلة شهر كامل 📆\n\n" .
                "🔴 ملاحظة 1️⃣: هذا التحديث من المتعامل جيزي ولا يمكن تجاوزه ⚠️\n🔴 ملاحظة 2️⃣: يلزمك عرض ابتداءا من 100da او اكثر 💰\n⚡ قناة التلقرام : https://t.me/tasjilbott"
            );
            clearSession($psid); sendMessage($psid, ""); return;
        }
        if ($httpCode === 201 || $httpCode === 200 || $innerStatus === 200) {
            $msgStr = $responseData['message'] ?? '';
            if (is_array($msgStr)) $msgStr = $msgStr['en'] ?? '';
            if (stripos($msgStr, 'successfully') !== false || $httpCode === 201 || $innerStatus === 200) {
                clearPending($psid); recordFinalResult($psid);
                sendMessage($psid, "⭐ تم تفعيل 2G بنجاح 🎁 للرقم {$displayMasked}\n\n⚡ قناة التلقرام : https://t.me/tasjilbott");
                sendMessage($psid, "");
                clearSession($psid);
                sendMessage($psid, "لاتنسى متابعة حساب المطور </> : https://www.facebook.com/profile.php?id=100052854003446");
                return;
            }
            usleep(1000000); continue;
        }
        if ($httpCode === 429) { usleep(2000000); continue; }
        usleep(1000000);
    }
    clearPending($psid);
    sendMessage($psid, "هناك اشكال في سيرفر جيزي ⚠️ لم نستطع التفعيل لرقمك \n\n⚡ قناة التلقرام : https://t.me/tasjilbott");
    clearSession($psid); sendMessage($psid, "");
}

// ════════════════════════════════════════════════════════════════════════════
// MGM — بداية عملية الدعوة
// ════════════════════════════════════════════════════════════════════════════
function handleInviteStart(string $psid, array $user): void
{
    $rl = checkRateLimit($psid);
    if ($rl !== null) { sendMessage($psid, rateLimitMessage($rl)); return; }

    $msisdn      = $user['msisdn'];
    $accessToken = $user['access_token'];

    sendMessage($psid, "🔍 جاري فحص المكافآت المعلقة...");
    $bonusResult = tryActivateMgmBonus($psid, $msisdn, $accessToken, $user);

    if ($bonusResult === 'SUCCESS_1GO') {
        recordFinalResult($psid);
        sendMessage($psid, "🎁 تم تفعيل مكافأة معلقة وحصلت على 1 جيقا 🎉\n\n⏳ عد بعد 24 ساعة للحصول على مكافأة جديدة 📆\n\n⚡ قناة التلقرام : https://t.me/tasjilbott");
        clearSession($psid);
        sendMessage($psid, "لاتنسى متابعة حساب المطور </> : https://www.facebook.com/profile.php?id=100052854003446");
        return;
    }
    if ($bonusResult === 'SUCCESS_500MO') {
        recordFinalResult($psid);
        sendMessage($psid, "🎁 تم تفعيل مكافأة معلقة وحصلت على 500Mo 🎉\n\n⏳ عد بعد 24 ساعة للحصول على مكافأة جديدة 📆\n\n⚡ قناة التلقرام : https://t.me/tasjilbott");
        clearSession($psid);
        sendMessage($psid, "لاتنسى متابعة حساب المطور </> : https://www.facebook.com/profile.php?id=100052854003446");
        return;
    }
    if ($bonusResult === 'ALREADY_CLAIMED') {
        recordFinalResult($psid);
        sendMessage($psid, "⚠️ لقد استفدت من الدعوة اليوم ولديك مكافأة أخرى معلقة.\nتأكد من مرور 24 ساعة على آخر استلام للمكافأة وأعد المحاولة 📆\n\n⚡ قناة التلقرام : https://t.me/tasjilbott");
        clearSession($psid); sendMessage($psid, ""); return;
    }

    sendMessage($psid, "🔍 جاري الفحص اذا كانت لديك دعوات متاحة ...");
    $invitations = fetchMgmInvitations($msisdn, $accessToken);
    if ($invitations === null) {
        sendMessage($psid, "❌ حدث خطأ أثناء جلب بيانات الدعوات، حاول مجدداً.");
        clearSession($psid); sendMessage($psid, ""); return;
    }

    $maxInvitations = $invitations['campaign']['maxInvitation'] ?? 5;
    $invitationList = $invitations['invitations'] ?? [];
    $doneCount = 0; $pendingCount = 0; $pendingIds = [];
    foreach ($invitationList as $inv) {
        if (($inv['status'] ?? '') === 'DONE')    $doneCount++;
        if (($inv['status'] ?? '') === 'PENDING') { $pendingCount++; $pendingIds[] = $inv['id'] ?? null; }
    }
    $totalCount = count($invitationList);

    if ($doneCount >= $maxInvitations) {
        recordFinalResult($psid);
        sendMessage($psid, "🚫 لقد وصلت للحد الأقصى لعدد الدعوات {$maxInvitations} ✅\n\n⚡ قناة التلقرام : https://t.me/tasjilbott");
        clearSession($psid); sendMessage($psid, ""); return;
    }
    if ($totalCount >= $maxInvitations && $pendingCount > 0) {
        sendMessage($psid, "🔄 جاري حذف الدعوات المعلقة لتوفير مكان...");
        $deleted = deletePendingInvitations($msisdn, $accessToken, $pendingIds);
        if (!$deleted) {
            sendMessage($psid, "❌ تعذر حذف الدعوات المعلقة، حاول لاحقاً.");
            clearSession($psid); sendMessage($psid, ""); return;
        }
        sendMessage($psid, "✅ تم حذف الدعوات المعلقة بنجاح.");
    }

    setSession($psid, [
        'state'        => 'awaiting_invite_phone',
        'msisdn'       => $msisdn,
        'access_token' => $accessToken,
        'refresh_token'=> $user['refresh_token'],
    ]);
    sendMessage($psid,
        "📲 أرسل رقم هاتف الشخص الذي تريد دعوته (جيزي فقط)\nمثال: 0770000000\n\n❌ لإلغاء العملية أرسل: 1"
    );
}

// ════════════════════════════════════════════════════════════════════════════
// MGM — استقبال رقم المدعو
// ════════════════════════════════════════════════════════════════════════════
function handleInvitePhoneInput(string $psid, string $text, array $session): void
{
    if (trim($text) === '1') {
        clearSession($psid); sendMessage($psid, "✅ تم إلغاء عملية الدعوة."); sendMenu($psid); return;
    }
    $rl = checkRateLimit($psid);
    if ($rl !== null) { sendMessage($psid, rateLimitMessage($rl)); return; }

    $digits = preg_replace('/\D/', '', $text);
    if (!preg_match('/^07\d{8}$/', $digits)) {
        sendMessage($psid, "❌ الرقم غير صحيح، أرسل رقم جيزي بصيغة 07xxxxxxxx\n\n❌ لإلغاء العملية أرسل: 1");
        return;
    }

    $receiverMsisdn = '213' . substr($digits, 1);
    $senderMsisdn   = $session['msisdn'];

    if ($receiverMsisdn === $senderMsisdn) {
        sendMessage($psid, "❌ لا يمكنك دعوة رقمك الخاص!\n\nأرسل رقم شخص آخر.\n\n❌ لإلغاء العملية أرسل: 1");
        return;
    }

    $accessToken  = $session['access_token'];
    $refreshToken = $session['refresh_token'];

    sendMessage($psid, "📤 جاري إرسال الدعوة...");
    $result = sendMgmInvitation($senderMsisdn, $receiverMsisdn, $accessToken, $refreshToken, $psid);

    switch ($result['status']) {
        case 'SUCCESS':
            recordFinalResult($psid);
            sendMessage($psid,
                "✅ تم إرسال الدعوة بنجاح إلى الرقم 0" . substr($receiverMsisdn, 3) . " 🎉\n\n📲 تم إرسال رسالة نصية إلى الرقم المدعو.\nسيتم الآن تفعيل مكافأتك بعد تسجيل المدعو...\n\n🔢 الرجاء إدخال رمز التحقق الذي وصل لرقم المدعو:\n\n❌ لإلغاء العملية أرسل: 1"
            );
            if (sendDjezzyOTP($receiverMsisdn)) {
                setSession($psid, [
                    'state'          => 'awaiting_invitee_otp',
                    'msisdn'         => $senderMsisdn,
                    'access_token'   => $result['access_token'] ?? $accessToken,
                    'refresh_token'  => $result['refresh_token'] ?? $refreshToken,
                    'invitee_msisdn' => $receiverMsisdn,
                ]);
            } else {
                sendMessage($psid, "⚠️ تعذر إرسال رمز التحقق للمدعو. حاول لاحقاً.");
                clearSession($psid); sendMessage($psid, "");
            }
            break;
        case 'MAX_INVITATIONS':
            recordFinalResult($psid);
            sendMessage($psid, "🚫 لقد وصلت للحد الأقصى لعدد الدعوات 5 ✅\n\n⚡ قناة التلقرام : https://t.me/tasjilbott");
            clearSession($psid); sendMessage($psid, ""); break;
        case 'ALREADY_INVITED':
            sendMessage($psid, "⚠️ لقد تمت دعوة هذا الرقم من قبل، استخدم رقماً آخر.\n❌ لإلغاء العملية أرسل: 1"); break;
        case 'CUSTOMER_NOT_EXIST':
        case 'INVALID_NUMBER':
            sendMessage($psid, "❌ الرقم المدرج غير موجود أو غير نشط، تأكد من الرقم وأعد المحاولة.\n❌ لإلغاء العملية أرسل: 1"); break;
        case 'TOKEN_EXPIRED':
            sendMessage($psid, "🔄 انتهت صلاحية الجلسة، الرجاء إعادة إرسال رقمك للتسجيل.");
            clearSession($psid); sendMessage($psid, ""); break;
        default:
            sendMessage($psid, "❌ حدث خطأ غير متوقع، حاول لاحقاً.");
            clearSession($psid); sendMessage($psid, ""); break;
    }
}

// ════════════════════════════════════════════════════════════════════════════
// MGM — استقبال OTP المدعو وتفعيل المكافآت
// ════════════════════════════════════════════════════════════════════════════
function handleInviteeOtp(string $psid, string $text, array $session): void
{
    if (trim($text) === '1') {
        clearSession($psid); sendMessage($psid, "✅ تم إلغاء عملية الدعوة."); sendMenu($psid); return;
    }
    if (!preg_match('/\b(\d{6})\b/', $text, $m)) {
        sendMessage($psid, "⚠️ الرجاء إدخال رمز التحقق المكوّن من 6 أرقام.\n\n❌ لإلغاء العملية أرسل: 1"); return;
    }
    $rl = checkRateLimit($psid);
    if ($rl !== null) { sendMessage($psid, rateLimitMessage($rl)); return; }

    $inviteeMsisdn = $session['invitee_msisdn'];
    $senderMsisdn  = $session['msisdn'];
    $senderToken   = $session['access_token'];

    sendMessage($psid, "🔐 جاري التحقق من الرمز...");
    $inviteeResult = verifyOTP($inviteeMsisdn, $m[1]);
    if ($inviteeResult === 'wrong_otp') {
        sendMessage($psid, "❌ الرمز خاطئ، أعد إرسال الرمز الصحيح.\n\n❌ لإلغاء العملية أرسل: 1"); return;
    }
    if ($inviteeResult === false) {
        sendMessage($psid, "❌ حدث خطأ أثناء التحقق، حاول مجدداً.");
        clearSession($psid); sendMessage($psid, ""); return;
    }
    $inviteeToken = $inviteeResult['access_token'];
    sendMessage($psid, "🎁 تم التحقق بنجاح! جاري تفعيل المكافآت...");

    $senderBonus  = activateMgmReward($senderMsisdn, $senderToken, 'MGMBONUS1Go');
    $inviteeBonus = activateMgmReward($inviteeMsisdn, $inviteeToken, 'MGMBONUS500Mo');

    $senderMsg = match($senderBonus) {
        'SUCCESS'         => "✅ مكافأتك (1 جيقا) تم تفعيلها بنجاح 🎉",
        'ALREADY_CLAIMED' => "⚠️ مكافأتك محجوزة، تأكد من مرور 24 ساعة وأعد المحاولة.",
        'REWARD_NOT_EXIST'=> "❌ لا توجد مكافأة متاحة لرقمك حالياً.",
        default           => "⚠️ تعذر تفعيل مكافأتك مؤقتاً.",
    };
    $inviteeMsg = match($inviteeBonus) {
        'SUCCESS'         => "✅ مكافأة المدعو (500Mo) تم تفعيلها بنجاح 🎉",
        'ALREADY_CLAIMED' => "⚠️ مكافأة الرقم المدعو محجوزة، تأكد من مرور 24 ساعة وأعد المحاولة.",
        'REWARD_NOT_EXIST'=> "❌ لا توجد مكافأة متاحة للمدعو حالياً.",
        default           => "⚠️ تعذر تفعيل مكافأة المدعو مؤقتاً.",
    };
    recordFinalResult($psid);
    sendMessage($psid,
        "📊 نتيجة تفعيل المكافآت:\n\n👤 أنت (الداعي):\n{$senderMsg}\n\n👤 المدعو:\n{$inviteeMsg}\n\n⚡ قناة التلقرام : https://t.me/tasjilbott"
    );
    clearSession($psid);
    sendMessage($psid, "لاتنسى متابعة حساب المطور </> : https://www.facebook.com/profile.php?id=100052854003446");
}

// ════════════════════════════════════════════════════════════════════════════
// MGM API Calls
// ════════════════════════════════════════════════════════════════════════════
function fetchMgmInvitations(string $msisdn, string $accessToken): ?array
{
    $url     = "https://apim.djezzy.dz/mobile-api/api/v1/services/mgm/invitations/{$msisdn}";
    $proxies = array_merge(loadProxies(), refreshProxies());
    foreach ($proxies as $p) {
        $pp = parseProxy($p);
        $ch = curl_init($url);
        curl_setopt_array($ch, [CURLOPT_HTTPGET=>true,CURLOPT_HTTPHEADER=>['Accept: application/json',"Authorization: Bearer {$accessToken}",'User-Agent: MobileApp/3.0.0','accept-language: ar'],CURLOPT_RETURNTRANSFER=>true,CURLOPT_ENCODING=>'gzip',CURLOPT_TIMEOUT=>12,CURLOPT_CONNECTTIMEOUT=>5,CURLOPT_SSL_VERIFYPEER=>false,CURLOPT_PROXY=>$pp['host'],CURLOPT_PROXYUSERPWD=>$pp['userpass'],CURLOPT_PROXYTYPE=>CURLPROXY_HTTP,CURLOPT_FOLLOWLOCATION=>true]);
        $body = curl_exec($ch); $httpCode = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); $errno = curl_errno($ch); curl_close($ch);
        if ($errno || !$body || stripos($body, '<html') !== false) continue;
        $json = @json_decode($body, true);
        if (is_array($json) && ($json['status'] ?? 0) == 200) return $json['data'] ?? [];
    }
    return null;
}

function deletePendingInvitations(string $msisdn, string $accessToken, array $pendingIds): bool
{
    $url = "https://apim.djezzy.dz/mobile-api/api/v1/services/mgm/delete-invitation/{$msisdn}";
    $proxies = array_merge(loadProxies(), refreshProxies());
    $success = false;
    foreach ($pendingIds as $id) {
        if ($id === null) continue;
        foreach ($proxies as $p) {
            $pp = parseProxy($p);
            $ch = curl_init($url);
            curl_setopt_array($ch, [CURLOPT_POST=>true,CURLOPT_POSTFIELDS=>json_encode(['invitationId'=>$id]),CURLOPT_HTTPHEADER=>['Content-Type: application/json','Accept: application/json','Accept-Encoding: gzip',"Authorization: Bearer {$accessToken}",'User-Agent: MobileApp/3.0.0','accept-language: ar'],CURLOPT_RETURNTRANSFER=>true,CURLOPT_ENCODING=>'gzip',CURLOPT_TIMEOUT=>10,CURLOPT_CONNECTTIMEOUT=>5,CURLOPT_SSL_VERIFYPEER=>false,CURLOPT_PROXY=>$pp['host'],CURLOPT_PROXYUSERPWD=>$pp['userpass'],CURLOPT_PROXYTYPE=>CURLPROXY_HTTP,CURLOPT_FOLLOWLOCATION=>true]);
            $body = curl_exec($ch); $httpCode = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); $errno = curl_errno($ch); curl_close($ch);
            dbg("[DELETE_PENDING] id={$id} http={$httpCode}");
            if (!$errno && ($httpCode === 200 || $httpCode === 201)) { $success = true; break; }
        }
    }
    return $success;
}

function sendMgmInvitation(string $senderMsisdn, string $receiverMsisdn, string $accessToken, string $refreshToken, string $psid): array
{
    $url     = "https://apim.djezzy.dz/mobile-api/api/v1/services/mgm/send-invitation/{$senderMsisdn}";
    $payload = json_encode(['msisdnReciever' => $receiverMsisdn]);
    $proxies = array_merge(loadProxies(), refreshProxies());
    $maxTokenRefresh = 3; $tokenRefreshCount = 0; $attempts = 0;
    while ($attempts < 10) {
        $attempts++;
        foreach ($proxies as $p) {
            $pp = parseProxy($p);
            $ch = curl_init($url);
            curl_setopt_array($ch, [CURLOPT_POST=>true,CURLOPT_POSTFIELDS=>$payload,CURLOPT_HTTPHEADER=>['Content-Type: application/json','Accept: application/json','Accept-Encoding: gzip','accept-language: ar',"Authorization: Bearer {$accessToken}",'User-Agent: MobileApp/3.0.0'],CURLOPT_RETURNTRANSFER=>true,CURLOPT_ENCODING=>'gzip',CURLOPT_TIMEOUT=>10,CURLOPT_CONNECTTIMEOUT=>5,CURLOPT_SSL_VERIFYPEER=>false,CURLOPT_PROXY=>$pp['host'],CURLOPT_PROXYUSERPWD=>$pp['userpass'],CURLOPT_PROXYTYPE=>CURLPROXY_HTTP,CURLOPT_FOLLOWLOCATION=>true]);
            $body = curl_exec($ch); $httpCode = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); $errno = curl_errno($ch); curl_close($ch);
            dbg("[MGM_INVITE] http={$httpCode} body=" . substr((string)$body, 0, 300));
            if ($errno || !$body || stripos($body, '<html') !== false) continue;
            $json = @json_decode($body, true);
            if (!is_array($json)) continue;
            $fault = $json['fault'] ?? null;
            if ($fault && (int)($fault['code'] ?? 0) === 900901) {
                if ($tokenRefreshCount >= $maxTokenRefresh) return ['status' => 'TOKEN_EXPIRED'];
                $tokenRefreshCount++;
                $refreshed = refreshAccessToken($refreshToken, $senderMsisdn, $psid);
                if ($refreshed === false) return ['status' => 'TOKEN_EXPIRED'];
                $accessToken = $refreshed['access_token']; $refreshToken = $refreshed['refresh_token']; break;
            }
            $msgField = $json['message'] ?? '';
            $arMsg    = is_array($msgField) ? ($msgField['ar'] ?? '') : (string)$msgField;
            if ($httpCode === 201 && str_contains($arMsg, 'تمت العملية بنجاح')) return ['status' => 'SUCCESS', 'access_token' => $accessToken, 'refresh_token' => $refreshToken];
            if ($httpCode === 400 && str_contains($arMsg, 'وصلت إلى الحد الأقصى')) return ['status' => 'MAX_INVITATIONS'];
            if (str_contains($arMsg, 'تمت دعوة هذا المستلم') || str_contains($arMsg, 'هذه العملية غير متوفرة')) return ['status' => 'ALREADY_INVITED'];
            if (str_contains($arMsg, 'العميل غير موجود')) return ['status' => 'CUSTOMER_NOT_EXIST'];
            if (str_contains($arMsg, 'غير نشط أو غير صالح')) return ['status' => 'INVALID_NUMBER'];
            usleep(1000000);
        }
    }
    return ['status' => 'ERROR'];
}

function activateMgmReward(string $msisdn, string $accessToken, string $packageCode): string
{
    $url     = "https://apim.djezzy.dz/mobile-api/api/v1/services/mgm/activate-reward/{$msisdn}";
    $payload = json_encode(['packageCode' => $packageCode]);
    $proxies = array_merge(loadProxies(), refreshProxies());
    for ($attempt = 1; $attempt <= 5; $attempt++) {
        foreach ($proxies as $p) {
            $pp = parseProxy($p);
            $ch = curl_init($url);
            curl_setopt_array($ch, [CURLOPT_POST=>true,CURLOPT_POSTFIELDS=>$payload,CURLOPT_HTTPHEADER=>['Content-Type: application/json','Accept: application/json','Accept-Encoding: gzip','accept-language: ar',"Authorization: Bearer {$accessToken}",'User-Agent: MobileApp/3.0.0'],CURLOPT_RETURNTRANSFER=>true,CURLOPT_ENCODING=>'gzip',CURLOPT_TIMEOUT=>15,CURLOPT_CONNECTTIMEOUT=>6,CURLOPT_SSL_VERIFYPEER=>false,CURLOPT_PROXY=>$pp['host'],CURLOPT_PROXYUSERPWD=>$pp['userpass'],CURLOPT_PROXYTYPE=>CURLPROXY_HTTP,CURLOPT_FOLLOWLOCATION=>true]);
            $body = curl_exec($ch); $httpCode = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); $errno = curl_errno($ch); curl_close($ch);
            $bodyStr = (string)$body;
            dbg("[MGM_REWARD:{$packageCode}] attempt={$attempt} http={$httpCode} body=" . substr($bodyStr, 0, 400));
            if ($errno || !$body || stripos($bodyStr, '<html') !== false) continue;
            $json = @json_decode($bodyStr, true);
            if ($httpCode === 200 || $httpCode === 201) {
                if (is_array($json)) {
                    $msg = $json['message'] ?? ''; $msgStr = is_array($msg) ? ($msg['en'] ?? ($msg['ar'] ?? '')) : (string)$msg;
                    $status = (int)($json['status'] ?? 0);
                    if (stripos($msgStr,'successfully')!==false||stripos($msgStr,'تم')!==false||$httpCode===201||$status===200||$status===201||empty($msgStr)) return 'SUCCESS';
                } else { return 'SUCCESS'; }
            }
            if (!is_array($json)) { usleep(500000); continue; }
            if ($httpCode === 404) {
                $msg = $json['message'] ?? ''; $msgEn = is_array($msg) ? ($msg['en'] ?? '') : (string)$msg;
                if (stripos($msgEn,'Eligibility not found')!==false||stripos($msgEn,'eligibility')!==false) return 'ALREADY_CLAIMED';
                return 'REWARD_NOT_EXIST';
            }
            if ($httpCode === 400) {
                $msg = $json['message'] ?? ''; $msgAr = is_array($msg) ? ($msg['ar'] ?? '') : (string)$msg; $msgEn = is_array($msg) ? ($msg['en'] ?? '') : (string)$msg;
                if (str_contains($msgAr,'تعذر معالجة طلبك')||str_contains($msgAr,'لم تمر')||stripos($msgEn,'cannot be processed')!==false) return 'ALREADY_CLAIMED';
            }
            if ($httpCode === 401) return 'ERROR';
            usleep(500000);
        }
    }
    return 'ERROR';
}

function tryActivateMgmBonus(string $psid, string $msisdn, string $accessToken, array $user): string
{
    $r1 = activateMgmReward($msisdn, $accessToken, 'MGMBONUS1Go');
    if ($r1 === 'SUCCESS')         return 'SUCCESS_1GO';
    if ($r1 === 'ALREADY_CLAIMED') return 'ALREADY_CLAIMED';
    if ($r1 === 'REWARD_NOT_EXIST') {
        $r2 = activateMgmReward($msisdn, $accessToken, 'MGMBONUS500Mo');
        if ($r2 === 'SUCCESS')         return 'SUCCESS_500MO';
        if ($r2 === 'ALREADY_CLAIMED') return 'ALREADY_CLAIMED';
        return 'REWARD_NOT_EXIST';
    }
    return 'ERROR';
}

// ════════════════════════════════════════════════════════════════════════════
// fetchSubscriptionHistory
// ════════════════════════════════════════════════════════════════════════════
function fetchSubscriptionHistory(string $msisdn, string $accessToken): ?array
{
    $url     = "https://apim.djezzy.dz/mobile-api/api/v1/subscribers/subscription-history/{$msisdn}";
    $proxies = array_merge(loadProxies(), refreshProxies());
    foreach ($proxies as $p) {
        $pp = parseProxy($p);
        $ch = curl_init($url);
        curl_setopt_array($ch, [CURLOPT_HTTPGET=>true,CURLOPT_HTTPHEADER=>['Accept: application/json',"Authorization: Bearer {$accessToken}",'User-Agent: MobileApp/3.0.0','Connection: Keep-Alive','Accept-Language: fr'],CURLOPT_RETURNTRANSFER=>true,CURLOPT_ENCODING=>'gzip',CURLOPT_TIMEOUT=>12,CURLOPT_CONNECTTIMEOUT=>5,CURLOPT_SSL_VERIFYPEER=>false,CURLOPT_PROXY=>$pp['host'],CURLOPT_PROXYUSERPWD=>$pp['userpass'],CURLOPT_PROXYTYPE=>CURLPROXY_HTTP,CURLOPT_FOLLOWLOCATION=>true]);
        $body = curl_exec($ch); $httpCode = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); $errno = curl_errno($ch); curl_close($ch);
        if ($errno || !$body) continue;
        $json = @json_decode($body, true);
        if (is_array($json) && ($json['status'] ?? 0) == 200) return $json['data'] ?? [];
    }
    return null;
}
function getLastWalkWinDate(array $history): ?int
{
    foreach ($history as $item) {
        $code = $item['packageCode'] ?? '';
        if (in_array($code, ['GIFTWALKWIN2GO', 'GIFTWALKWIN1GO'])) {
            $dt = $item['subscriptionDateTime'] ?? null;
            if ($dt) return strtotime($dt);
        }
    }
    return null;
}
function formatTimeRemaining(int $secondsLeft): string
{
    if ($secondsLeft <= 0) return "0 ثانية";
    $days = (int)($secondsLeft / 86400); $hours = (int)(($secondsLeft % 86400) / 3600);
    $minutes = (int)(($secondsLeft % 3600) / 60); $secs = $secondsLeft % 60;
    $parts = [];
    if ($days > 0)    $parts[] = "{$days} يوم";
    if ($hours > 0)   $parts[] = "{$hours} ساعة";
    if ($minutes > 0) $parts[] = "{$minutes} دقيقة";
    if ($secs > 0 && $days === 0 && $hours === 0) $parts[] = "{$secs} ثانية";
    return implode(' و', $parts);
}

// ════════════════════════════════════════════════════════════════════════════
// cURL Helpers — الطريقة القديمة
// ════════════════════════════════════════════════════════════════════════════
function activateProductCurl(string $msisdn, string $accessToken, string $jsonPayload, string $logTag): ?array
{
    $url     = "https://apim.djezzy.dz/mobile-api/api/v1/subscribers/activate-product/{$msisdn}";
    $proxies = array_merge(loadProxies(), refreshProxies());
    foreach ($proxies as $p) {
        $pp = parseProxy($p);
        $r  = doActivateProductCurl($url, $jsonPayload, $accessToken, $pp['host'], $pp['userpass'], $logTag);
        if ($r !== null) return $r;
    }
    return null;
}
function activateWalkRewardCurl(string $msisdn, string $accessToken, string $jsonPayload, string $logTag): ?array
{
    $url     = "https://apim.djezzy.dz/mobile-api/api/v1/services/walk/activate-reward/{$msisdn}";
    $proxies = array_merge(loadProxies(), refreshProxies());
    foreach ($proxies as $p) {
        $pp = parseProxy($p);
        $r  = doActivateWalkRewardCurl($url, $jsonPayload, $accessToken, $pp['host'], $pp['userpass'], $logTag);
        if ($r !== null) return $r;
    }
    return null;
}
function doActivateWalkRewardCurl(string $url, string $payload, string $token, string $proxyHost, string $proxyAuth, string $tag): ?array
{
    $ch = curl_init($url);
    curl_setopt_array($ch, [CURLOPT_POST=>true,CURLOPT_POSTFIELDS=>$payload,CURLOPT_HTTPHEADER=>['Content-Type: application/json','Accept: application/json','Accept-Encoding: gzip',"Authorization: Bearer {$token}",'User-Agent: MobileApp/3.0.0'],CURLOPT_RETURNTRANSFER=>true,CURLOPT_ENCODING=>'gzip',CURLOPT_TIMEOUT=>10,CURLOPT_CONNECTTIMEOUT=>5,CURLOPT_SSL_VERIFYPEER=>false,CURLOPT_PROXY=>$proxyHost,CURLOPT_PROXYUSERPWD=>$proxyAuth,CURLOPT_PROXYTYPE=>CURLPROXY_HTTP,CURLOPT_FOLLOWLOCATION=>true]);
    $body = curl_exec($ch); $httpCode = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); $errno = curl_errno($ch); $error = curl_error($ch); curl_close($ch);
    file_put_contents('/tmp/activate2g.log', date('Y-m-d H:i:s')." [{$tag}] http={$httpCode} err={$error} body=".substr((string)$body,0,600)."\n", FILE_APPEND);
    if ($errno || $body === false || $httpCode === 0) return null;
    $bodyStr = (string)$body;
    if (stripos($bodyStr,'<!DOCTYPE')!==false||stripos($bodyStr,'<html')!==false) return null;
    $json = @json_decode($bodyStr, true);
    return ['http_code'=>$httpCode,'json'=>is_array($json)?$json:['raw'=>$bodyStr],'body'=>$bodyStr];
}
function doActivateProductCurl(string $url, string $payload, string $token, string $proxyHost, string $proxyAuth, string $tag): ?array
{
    $ch = curl_init($url);
    curl_setopt_array($ch, [CURLOPT_POST=>true,CURLOPT_POSTFIELDS=>$payload,CURLOPT_HTTPHEADER=>['Content-Type: application/json','Accept: application/json','Accept-Encoding: gzip','accept-language: fr',"authorization: Bearer {$token}",'User-Agent: MobileApp/3.0.0'],CURLOPT_RETURNTRANSFER=>true,CURLOPT_ENCODING=>'gzip',CURLOPT_TIMEOUT=>10,CURLOPT_CONNECTTIMEOUT=>5,CURLOPT_SSL_VERIFYPEER=>false,CURLOPT_PROXY=>$proxyHost,CURLOPT_PROXYUSERPWD=>$proxyAuth,CURLOPT_PROXYTYPE=>CURLPROXY_HTTP,CURLOPT_FOLLOWLOCATION=>true]);
    $body = curl_exec($ch); $httpCode = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); $errno = curl_errno($ch); $error = curl_error($ch); curl_close($ch);
    file_put_contents('/tmp/activate70.log', date('Y-m-d H:i:s')." [{$tag}] http={$httpCode} err={$error} body=".substr((string)$body,0,600)."\n", FILE_APPEND);
    if ($errno || $body === false || $httpCode === 0) return null;
    $bodyStr = (string)$body;
    if (stripos($bodyStr,'<!DOCTYPE')!==false||stripos($bodyStr,'<html')!==false) return null;
    $json = @json_decode($bodyStr, true);
    return ['http_code'=>$httpCode,'json'=>is_array($json)?$json:['raw'=>$bodyStr],'body'=>$bodyStr];
}

// ════════════════════════════════════════════════════════════════════════════
// cURL لتفعيل العرض بالطريقة الجديدة
// ════════════════════════════════════════════════════════════════════════════
function activateProductCurlNew(string $msisdn, string $accessToken, string $packageCode, string $logTag): ?array
{
    $url     = "https://apim.djezzy.dz/djezzy-api/api/v1/subscribers/{$msisdn}/subscription-product?include=";
    $payload = json_encode(['data' => ['id' => $packageCode, 'type' => 'products']]);
    $headers = ['Content-Type: application/json','Accept: application/json','Accept-Encoding: gzip','Connection: Keep-Alive',"Authorization: Bearer {$accessToken}",'User-Agent: Djezzy/2.7.0','X-Csrf-Token: YACIN_DZ'];
    $proxies = array_merge(loadProxies(), refreshProxies());
    foreach ($proxies as $p) {
        $pp = parseProxy($p);
        $ch = curl_init($url);
        curl_setopt_array($ch, [CURLOPT_POST=>true,CURLOPT_POSTFIELDS=>$payload,CURLOPT_HTTPHEADER=>$headers,CURLOPT_RETURNTRANSFER=>true,CURLOPT_ENCODING=>'gzip',CURLOPT_TIMEOUT=>10,CURLOPT_CONNECTTIMEOUT=>5,CURLOPT_SSL_VERIFYPEER=>false,CURLOPT_PROXY=>$pp['host'],CURLOPT_PROXYUSERPWD=>$pp['userpass'],CURLOPT_PROXYTYPE=>CURLPROXY_HTTP,CURLOPT_FOLLOWLOCATION=>true]);
        $body = curl_exec($ch); $httpCode = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); $errno = curl_errno($ch); $error = curl_error($ch); curl_close($ch);
        file_put_contents('/tmp/activate_offer_new.log', date('Y-m-d H:i:s')." [{$logTag}] http={$httpCode} err={$error} body=".substr((string)$body,0,600)."\n", FILE_APPEND);
        if ($errno || $body === false || $httpCode === 0) continue;
        $bodyStr = (string)$body;
        if (stripos($bodyStr,'<!DOCTYPE')!==false||stripos($bodyStr,'<html')!==false) continue;
        $json = @json_decode($bodyStr, true);
        return ['http_code'=>$httpCode,'json'=>is_array($json)?$json:['raw'=>$bodyStr],'body'=>$bodyStr];
    }
    return null;
}

// ════════════════════════════════════════════════════════════════════════════
// Token Refresh — credentials قديمة
// ════════════════════════════════════════════════════════════════════════════
function refreshAccessToken(string $refreshToken, string $msisdn, string $psid): mixed
{
    $allProxies = loadProxies();
    for ($i = 0; $i < 20; $i++) {
        $pp     = parseProxy($allProxies[$i % count($allProxies)]);
        $result = refreshTokenRequest($refreshToken, $pp['host'], $pp['userpass']);
        if ($result === 'expired') {
            sendMessage($psid, "🔄 انتهت صلاحية الجلسة، سيتم إرسال رمز تحقق جديد...");
            sendOTPAndWait($psid, $msisdn, '0' . substr($msisdn, 3));
            return false;
        }
        if ($result === 'html' || $result === false) {
            if ($i === count($allProxies) - 1) $allProxies = array_merge($allProxies, refreshProxies());
            usleep(300000); continue;
        }
        saveUser($psid, array_merge(getUser($psid) ?? [], ['access_token' => $result['access_token'], 'refresh_token' => $result['refresh_token']]));
        return $result;
    }
    return false;
}
function refreshTokenRequest(string $refreshToken, string $proxyHost, string $proxyAuth): mixed
{
    $r = djezzyCurl('https://apim.djezzy.dz/oauth2/token',
        http_build_query(['scope'=>'djezzyAppV2','client_secret'=>CLIENT_SECRET_OLD,'client_id'=>CLIENT_ID_OLD,'grant_type'=>'refresh_token','refresh_token'=>$refreshToken]),
        $proxyHost, $proxyAuth, 'refresh');
    if ($r==='html'||$r===false) return $r;
    $json = @json_decode($r['body'], true);
    if ($r['code']===400 && ($json['error']??'')==='invalid_grant') return 'expired';
    if ($r['code']===200 && isset($json['access_token'])) return ['access_token'=>$json['access_token'],'refresh_token'=>$json['refresh_token']??$refreshToken];
    return false;
}

// ════════════════════════════════════════════════════════════════════════════
// Token Refresh — credentials جديدة
// ════════════════════════════════════════════════════════════════════════════
function refreshAccessTokenNew(string $refreshToken, string $msisdn, string $psid, string $packageCode): mixed
{
    $allProxies = loadProxies();
    for ($i = 0; $i < 20; $i++) {
        $pp     = parseProxy($allProxies[$i % count($allProxies)]);
        $result = refreshTokenRequestNew($refreshToken, $pp['host'], $pp['userpass']);
        if ($result === 'expired') {
            sendMessage($psid, "🔄 انتهت صلاحية الجلسة، سيتم إرسال رمز تحقق جديد...");
            sendNewOTPAndWaitForOffer($psid, $msisdn, '0' . substr($msisdn, 3), $packageCode);
            return false;
        }
        if ($result === 'html' || $result === false) {
            if ($i === count($allProxies) - 1) $allProxies = array_merge($allProxies, refreshProxies());
            usleep(300000); continue;
        }
        return $result;
    }
    return false;
}
function refreshTokenRequestNew(string $refreshToken, string $proxyHost, string $proxyAuth): mixed
{
    $r = djezzyCurl('https://apim.djezzy.dz/oauth2/token',
        http_build_query(['scope'=>'djezzyAppV2','client_secret'=>CLIENT_SECRET_NEW,'client_id'=>CLIENT_ID_NEW,'grant_type'=>'refresh_token','refresh_token'=>$refreshToken]),
        $proxyHost, $proxyAuth, 'refresh_new');
    if ($r==='html'||$r===false) return $r;
    $json = @json_decode($r['body'], true);
    if ($r['code']===400 && ($json['error']??'')==='invalid_grant') return 'expired';
    if ($r['code']===200 && isset($json['access_token'])) return ['access_token'=>$json['access_token'],'refresh_token'=>$json['refresh_token']??$refreshToken];
    return false;
}

// ════════════════════════════════════════════════════════════════════════════
// Djezzy API — OTP وتحقق (credentials قديمة)
// ════════════════════════════════════════════════════════════════════════════
function sendDjezzyOTP(string $msisdn): bool
{
    $q = http_build_query(['scope'=>'smsotp','client_id'=>CLIENT_ID_OLD,'msisdn'=>$msisdn]);
    foreach (array_merge(loadProxies(), refreshProxies()) as $p) {
        $pp = parseProxy($p);
        if (djezzyCurl('https://apim.djezzy.dz/oauth2/registration',$q,$pp['host'],$pp['userpass'],'otp')===true) return true;
    }
    return false;
}
function verifyOTP(string $msisdn, string $otp): mixed
{
    foreach (array_merge(loadProxies(), refreshProxies()) as $p) {
        $pp = parseProxy($p); $res = djezzyTokenReq($msisdn, $otp, $pp['host'], $pp['userpass']);
        if ($res==='wrong_otp') return 'wrong_otp';
        if (is_array($res)) return $res;
    }
    return false;
}
function djezzyTokenReq(string $msisdn, string $otp, string $ph, string $pa): mixed
{
    $r = djezzyCurl('https://apim.djezzy.dz/oauth2/token',
        http_build_query(['scope'=>'djezzyAppV2','client_secret'=>CLIENT_SECRET_OLD,'client_id'=>CLIENT_ID_OLD,'otp'=>$otp,'mobileNumber'=>$msisdn,'grant_type'=>'mobile']),
        $ph, $pa, 'token');
    if ($r==='html'||$r===false) return false;
    $json = @json_decode($r['body'], true);
    if ($r['code']===400&&($json['error']??'')==='invalid_grant') return 'wrong_otp';
    if ($r['code']===200&&isset($json['access_token'])) return ['access_token'=>$json['access_token'],'refresh_token'=>$json['refresh_token']??''];
    return false;
}

// ════════════════════════════════════════════════════════════════════════════
// Djezzy API — OTP وتحقق (credentials جديدة)
// ════════════════════════════════════════════════════════════════════════════
function sendDjezzyOTPNew(string $msisdn): bool
{
    $q = http_build_query(['scope'=>'smsotp','client_id'=>CLIENT_ID_NEW,'msisdn'=>$msisdn]);
    foreach (array_merge(loadProxies(), refreshProxies()) as $p) {
        $pp = parseProxy($p);
        if (djezzyCurl('https://apim.djezzy.dz/oauth2/registration',$q,$pp['host'],$pp['userpass'],'otp_new')===true) return true;
    }
    return false;
}
function verifyOTPNew(string $msisdn, string $otp): mixed
{
    foreach (array_merge(loadProxies(), refreshProxies()) as $p) {
        $pp = parseProxy($p); $res = djezzyTokenReqNew($msisdn, $otp, $pp['host'], $pp['userpass']);
        if ($res==='wrong_otp') return 'wrong_otp';
        if (is_array($res)) return $res;
    }
    return false;
}
function djezzyTokenReqNew(string $msisdn, string $otp, string $ph, string $pa): mixed
{
    $r = djezzyCurl('https://apim.djezzy.dz/oauth2/token',
        http_build_query(['scope'=>'djezzyAppV2','client_secret'=>CLIENT_SECRET_NEW,'client_id'=>CLIENT_ID_NEW,'otp'=>$otp,'mobileNumber'=>$msisdn,'grant_type'=>'mobile']),
        $ph, $pa, 'token_new');
    if ($r==='html'||$r===false) return false;
    $json = @json_decode($r['body'], true);
    if ($r['code']===400&&($json['error']??'')==='invalid_grant') return 'wrong_otp';
    if ($r['code']===200&&isset($json['access_token'])) return ['access_token'=>$json['access_token'],'refresh_token'=>$json['refresh_token']??''];
    return false;
}

// ════════════════════════════════════════════════════════════════════════════
// djezzyCurl — مشترك
// ════════════════════════════════════════════════════════════════════════════
function djezzyCurl(string $url, string $data, string $ph, string $pa, string $tag): mixed
{
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_POST=>true, CURLOPT_POSTFIELDS=>$data,
        CURLOPT_HTTPHEADER=>['Content-Type: application/x-www-form-urlencoded','Accept: */*','User-Agent: Dalvik/2.1.0 (Linux; U; Android 6.0; PGN610 Build/MRA58K)','Connection: Keep-Alive','Accept-Encoding: gzip'],
        CURLOPT_RETURNTRANSFER=>true, CURLOPT_ENCODING=>'gzip', CURLOPT_TIMEOUT=>8, CURLOPT_CONNECTTIMEOUT=>4, CURLOPT_SSL_VERIFYPEER=>false,
        CURLOPT_PROXY=>$ph, CURLOPT_PROXYUSERPWD=>$pa, CURLOPT_PROXYTYPE=>CURLPROXY_HTTP, CURLOPT_FOLLOWLOCATION=>true, CURLOPT_MAXREDIRS=>3,
    ]);
    $body = curl_exec($ch); $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); $err = curl_error($ch); curl_close($ch);
    file_put_contents('/tmp/djezzy.log', date('Y-m-d H:i:s')." [$tag] CODE:$code ERR:$err BODY:".substr((string)$body,0,400)."\n", FILE_APPEND);
    if ($err || $body === false) return false;
    if (stripos((string)$body,'<!DOCTYPE')!==false||stripos((string)$body,'<html')!==false) return 'html';
    if (str_starts_with($tag, 'otp')) return ($code >= 200 && $code < 300) ? true : false;
    return ['code'=>$code,'body'=>(string)$body];
}

// ════════════════════════════════════════════════════════════════════════════
// Proxy
// ════════════════════════════════════════════════════════════════════════════
function loadProxies(): array
{
    if (file_exists(PROXY_LIST_FILE)) { $d=json_decode(file_get_contents(PROXY_LIST_FILE),true); if(is_array($d)&&$d) return $d; }
    return [
    "https://change4.owlproxy.com:7778:gip2m6CrMf80_custom_zone_DZ_st__city_sid_00576820_time_5:4986481",
    "https://change4.owlproxy.com:7778:W875sxqC3170_custom_zone_DZ_st__city_sid_31881450_time_5:4986501",
    "https://change4.owlproxy.com:7778:cvDBsWfHoZ50_custom_zone_DZ_st__city_sid_86435615_time_5:4986521",
    "https://change4.owlproxy.com:7778:DJXLLlVHro50_custom_zone_DZ_st__city_sid_64770433_time_5:4986531",
    "https://change4.owlproxy.com:7778:tLeQJdLqHd50_custom_zone_DZ_st__city_sid_68342837_time_5:4986554",
    "https://change4.owlproxy.com:7778:hqrujtOuDOA0_custom_zone_DZ_st__city_sid_27438037_time_5:4986566",
    "https://change4.owlproxy.com:7778:FV5HIpXnVl10_custom_zone_DZ_st__city_sid_38690058_time_5:4986592",
    "https://change4.owlproxy.com:7778:FJtGGAdEzO40_custom_zone_DZ_st__city_sid_79105828_time_5:4986616",
    "https://change4.owlproxy.com:7778:clcP9uW2x520_custom_zone_DZ_st__city_sid_14445049_time_5:4986639",
    "https://change4.owlproxy.com:7778:ygqi3nigqr50_custom_zone_DZ_st__city_sid_88109066_time_5:4986667",
    "https://change4.owlproxy.com:7778:2eR0qwBw0xA0_custom_zone_DZ_st__city_sid_44559704_time_5:4986683",
    "https://change4.owlproxy.com:7778:PMHs71GfGe90_custom_zone_DZ_st__city_sid_25891446_time_5:4986712",
    "https://change4.owlproxy.com:7778:dO2VIDr8nL90_custom_zone_DZ_st__city_sid_40720078_time_5:4986725",
    "https://change4.owlproxy.com:7778:QZFWrBwTdn80_custom_zone_DZ_st__city_sid_90140351_time_5:4986745",
    "https://change4.owlproxy.com:7778:LNPiVrk40F80_custom_zone_DZ_st__city_sid_20157104_time_5:4986761",
    "https://change4.owlproxy.com:7778:IKZ8Z3Y0Jy90_custom_zone_DZ_st__city_sid_11848234_time_5:4986781",
    "https://change4.owlproxy.com:7778:CUqfsRFo2o10_custom_zone_DZ_st__city_sid_79838167_time_5:4986796",
    "https://change4.owlproxy.com:7778:wCjiTL2WXUA0_custom_zone_DZ_st__city_sid_70400514_time_5:4986811",
    "https://change4.owlproxy.com:7778:Qxtw9Y0lSG30_custom_zone_DZ_st__city_sid_86368933_time_5:4986825",
    "https://change4.owlproxy.com:7778:dcWbFAOHwi70_custom_zone_DZ_st__city_sid_08920820_time_5:4986842",
    "https://change4.owlproxy.com:7778:uAX5uXQqs890_custom_zone_DZ_st__city_sid_55907938_time_5:4986851",
    "https://change4.owlproxy.com:7778:EzsX1DE6HR70_custom_zone_DZ_st__city_sid_25346730_time_5:4986862",
    "https://change4.owlproxy.com:7778:U3zd3sszGa50_custom_zone_DZ_st__city_sid_07643370_time_5:4986877",
    "https://change4.owlproxy.com:7778:CRAGlH9uqC50_custom_zone_DZ_st__city_sid_26477824_time_5:4986891",
    "https://change4.owlproxy.com:7778:T758IDr8p180_custom_zone_DZ_st__city_sid_54783317_time_5:4986902",
    "https://change4.owlproxy.com:7778:zvOrnK2rYj30_custom_zone_DZ_st__city_sid_00017921_time_5:4986918",
    "https://change4.owlproxy.com:7778:5Ou8LZuGXO60_custom_zone_DZ_st__city_sid_34565498_time_5:4986933",
    "https://change4.owlproxy.com:7778:foUDtXWxFN70_custom_zone_DZ_st__city_sid_99841159_time_5:4986944",
    "https://change4.owlproxy.com:7778:5o4XJszRkx90_custom_zone_DZ_st__city_sid_36303130_time_5:4986968",
    "https://change4.owlproxy.com:7778:itpNXR2tZd70_custom_zone_DZ_st__city_sid_93395952_time_5:4986980",
    "https://change4.owlproxy.com:7778:1KAIKjCTua60_custom_zone_DZ_st__city_sid_21326655_time_5:4986992",
    "https://change4.owlproxy.com:7778:KQ5T6dHDkQ70_custom_zone_DZ_st__city_sid_54247478_time_5:4987010",
    "https://change4.owlproxy.com:7778:2zDtAx1xEc10_custom_zone_DZ_st__city_sid_27509092_time_5:4987025",
    "https://change4.owlproxy.com:7778:iUI5giWoFh90_custom_zone_DZ_st__city_sid_96051000_time_5:4987041",
    "https://change4.owlproxy.com:7778:2VEmIjMPFD90_custom_zone_DZ_st__city_sid_52838476_time_5:4987062",
    "https://change4.owlproxy.com:7778:jK7dBuBZwn90_custom_zone_DZ_st__city_sid_68587397_time_5:4987081",
    "https://change4.owlproxy.com:7778:mxsta2yxBs30_custom_zone_DZ_st__city_sid_02121477_time_5:4987098",
    "https://change4.owlproxy.com:7778:1lLNE5uC5880_custom_zone_DZ_st__city_sid_59447515_time_5:4987114",
    "https://change4.owlproxy.com:7778:ow54kQSQiQ00_custom_zone_DZ_st__city_sid_47195322_time_5:4987129",
    "https://change4.owlproxy.com:7778:nDBCZznJ9G90_custom_zone_DZ_st__city_sid_35191153_time_5:4987148"
];
}
function refreshProxies(): array
{
    $ch = curl_init(PROXY_API_URL);
    curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER=>true,CURLOPT_TIMEOUT=>8,CURLOPT_CONNECTTIMEOUT=>4,CURLOPT_SSL_VERIFYPEER=>false]);
    $body = curl_exec($ch); curl_close($ch);
    $list = json_decode($body, true);
    if (is_array($list) && $list) { file_put_contents(PROXY_LIST_FILE, json_encode($list)); return $list; }
    return loadProxies();
}
function parseProxy(string $proxy): array
{
    $raw = preg_replace('#^https?://#', '', $proxy); $p = explode(':', $raw, 4);
    return ['host'=>($p[0]??'').':'.($p[1]??''),'userpass'=>($p[2]??'').':'.($p[3]??'')];
}

// ════════════════════════════════════════════════════════════════════════════
// Session / User / PhoneMap
// ════════════════════════════════════════════════════════════════════════════
function getSession(string $p): array  { $f=SESSIONS_DIR."/$p.json"; return file_exists($f)?(json_decode(file_get_contents($f),true)??[]):[];  }
function setSession(string $p, array $d): void { file_put_contents(SESSIONS_DIR."/$p.json", json_encode($d)); }
function clearSession(string $p): void { $f=SESSIONS_DIR."/$p.json"; if(file_exists($f)) unlink($f); }
function saveUser(string $p, array $d): void { file_put_contents(USERS_DIR."/$p.json", json_encode($d, JSON_UNESCAPED_UNICODE|JSON_PRETTY_PRINT)); }
function getUser(string $p): ?array { $f=USERS_DIR."/$p.json"; return file_exists($f)?json_decode(file_get_contents($f),true):null; }
function savePhoneOwner(string $m, string $p): void { $map=file_exists(PHONE_MAP_FILE)?(json_decode(file_get_contents(PHONE_MAP_FILE),true)??[]):[];$map[$m]=$p;file_put_contents(PHONE_MAP_FILE,json_encode($map)); }
function getPhoneOwner(string $m): ?string { if(!file_exists(PHONE_MAP_FILE))return null;return(json_decode(file_get_contents(PHONE_MAP_FILE),true)??[])[$m]??null; }

// ════════════════════════════════════════════════════════════════════════════
// Messenger UI
// ════════════════════════════════════════════════════════════════════════════
function sendWelcomeNew(string $psid): void
{
    sendMessage($psid,
        "👋 أهلاً وسهلاً بك في Tasjil BOT! 🎉\n\n🌟 نرحب بك كمستخدم جديد!\n\n📌 مزايا البوت:\n\n✅ تفعيل 2G الأسبوعية 🎁\n✅ إرسال الدعوات 📨\n✅ تفعيل عرض 4GB بـ 70دج 🏷️\n✅ جميع عروض الإنترنت متوفرة ⭐\n\n━━━━━━━━━━━━━━\n\n📱 للبدء، أرسل رقم هاتفك (جيزي)\n🔹 مثال: 0770000000\n\n⚡ قناة التلغرام:\nhttps://t.me/tasjilbott"
    );
}
function sendWelcome(string $psid): void { sendMessage($psid, "يرجى ارسال أرقام هواتف فقط 📱\n"); }

function sendMenu(string $psid): void
{
    setSession($psid, array_merge(getSession($psid), ['state' => 'menu']));
    fbApiCall(json_encode([
        'recipient'      => ['id' => $psid],
        'messaging_type' => 'RESPONSE',
        'message'        => [
            'text' =>
                "📱 اختر العرض المناسب\n\n📌 إذا لم تظهر لك الأزرار أرسل الرقم المناسب 👇\n\n━━━━━━━━━━━━━━\n\n" .
                "1️⃣ لتفعيل 2G الأسبوعية\n📩 أرسل: 1\n\n" .
                "2️⃣ لتفعيل عرض 4GB بـ 70دج 🏷️\n📩 أرسل: 2\n\n" .
                "3️⃣ لإرسال دعوة 🎁\n📩 أرسل: 3\n\n" .
                "4️⃣ للمزيد من العروض 📦\n📩 أرسل: 4\n\n━━━━━━━━━━━━━━\n\n",
            'quick_replies' => [
                ['content_type'=>'text','title'=>'📶 تفعيل 2G',          'payload'=>'MENU_2G'],
                ['content_type'=>'text','title'=>'💰 عرض 70دج - 4جيقا',  'payload'=>'MENU_70DZ'],
                ['content_type'=>'text','title'=>'📨 إرسال دعوة',         'payload'=>'MENU_INVITE'],
                ['content_type'=>'text','title'=>'📦 المزيد من العروض',   'payload'=>'MENU_MORE_OFFERS'],
            ],
        ],
    ], JSON_UNESCAPED_UNICODE));
}

function sendMoreOffers(string $psid): void
{
    setSession($psid, array_merge(getSession($psid), ['state' => 'offers']));
    $text  = "📦 قائمة عروض الإنترنت المتوفرة 📦\n\n";
    $text .= "━━━━━━━━━━━ 📅 العروض اليومية ━━━━━━━━━━━\n\n";
    $text .= "5️⃣ 5GB 🔥\n🌐 الانترنت : 5GB\n💰 السعر: 90 دج\n⏳ المدة: 24 ساعة\n📩 للتفعيل أرسل: 5\n\n\n\n";
    $text .= "6️⃣ 300MB\n🌐 الانترنت : 300Mo\n💰 السعر: 30 دج\n⏳ المدة: 24 ساعة\n📩 للتفعيل أرسل: 6\n\n\n\n";
    $text .= "7️⃣ 600MB\n🌐 الانترنت : 600Mo\n💰 السعر: 50 دج\n⏳ المدة: 24 ساعة\n📩 للتفعيل أرسل: 7\n\n\n\n";
    $text .= "8️⃣ 2GB\n🌐 الانترنت : 2G\n💰 السعر: 100 دج\n⏳ المدة: 24 ساعة\n📩 للتفعيل أرسل: 8\n\n\n\n";
    $text .= "9️⃣ 1GB\n🌐 الانترنت : 1G\n💰 السعر: 50 دج\n⏳ المدة: 24 ساعة\n📩 للتفعيل أرسل: 9\n\n\n\n";
    $text .= "🔟 4GB 🏷️\n🌐 الانترنت : 4G\n💰 السعر: 70 دج\n⏳ المدة: 24 ساعة\n📩 للتفعيل أرسل: 10\n\n\n\n";
    $text .= "1️⃣1️⃣ 5GB\n🌐 الانترنت : 5G\n💰 السعر: 190 دج\n⏳ المدة: 24 ساعة\n📩 للتفعيل أرسل: 11\n\n\n\n";
    $text .= "1️⃣2️⃣ 4GB\n🌐 الانترنت : 4G\n💰 السعر: 140 دج\n⏳ المدة: 24 ساعة\n📩 للتفعيل أرسل: 12\n\n\n\n";
    $text .= "━━━━━━━━━━━ 📆 العروض الأسبوعية ━━━━━━━━━━━\n\n";
    $text .= "1️⃣3️⃣ 4GB\n🌐 الانترنت : 4G\n💰 السعر: 150 دج\n⏳ المدة: 7 أيام\n📩 للتفعيل أرسل: 13\n\n\n\n";
    $text .= "1️⃣4️⃣ 10GB\n🌐 الانترنت : 10G\n💰 السعر: 300 دج\n⏳ المدة: 7 أيام\n📩 للتفعيل أرسل: 14\n\n\n\n";
    $text .= "1️⃣5️⃣ 4GB\n🌐 الانترنت : 4G\n💰 السعر: 400 دج\n⏳ المدة: 15 يوم\n📩 للتفعيل أرسل: 15\n\n\n\n";
    $text .= "1️⃣6️⃣ 1GB Facebook 📘\n🌐 الانترنت : 1G فيسبوك فقط\n💰 السعر: 70 دج\n⏳ المدة: 3 أيام\n📩 للتفعيل أرسل: 16\n\n\n\n";
    $text .= "━━━━━━━━━━━ 🗓️ العروض الشهرية ━━━━━━━━━━━\n\n";
    $text .= "1️⃣7️⃣ 12GB\n🌐 الانترنت : 12G\n💰 السعر: 500 دج\n⏳ المدة: 30 يوم\n📩 للتفعيل أرسل: 17\n\n\n\n";
    $text .= "1️⃣8️⃣ 30GB\n🌐 الانترنت : 30G\n💰 السعر: 1000 دج\n⏳ المدة: 30 يوم\n📩 للتفعيل أرسل: 18\n\n\n\n";
    $text .= "1️⃣9️⃣ 60GB\n🌐 الانترنت : 60G\n💰 السعر: 1500 دج\n⏳ المدة: 30 يوم\n📩 للتفعيل أرسل: 19\n\n\n\n";
    $text .= "2️⃣0️⃣ 3GB\n🌐 الانترنت : 3G\n💰 السعر: 250 دج\n⏳ المدة: 30 يوم\n📩 للتفعيل أرسل: 20\n\n\n\n";
    $text .= "━━━━━━━━━━━ ⚡ العروض الخاصة ━━━━━━━━━━━\n\n";
    $text .= "2️⃣1️⃣ 1GB سريع ⚡\n🌐 الانترنت : 1G\n💰 السعر: 40 دج\n⏳ المدة: 1 ساعة\n📩 للتفعيل أرسل: 21\n\n\n\n";
    $text .= "2️⃣2️⃣ Facebook غير محدود 📘\n🌐 الانترنت : فيسبوك فقط غير محدود\n💰 السعر: 50 دج\n⏳ المدة: 4 ساعات\n📩 للتفعيل أرسل: 22\n\n";
    $text .= "━━━━━━━━━━━━━━━━━━━━━━\n\n📨 أرسل رقم العرض فقط لتفعيله مباشرة";

    fbApiCall(json_encode([
        'recipient'      => ['id' => $psid],
        'messaging_type' => 'RESPONSE',
        'message'        => [
            'text'          => $text,
            'quick_replies' => [
                ['content_type'=>'text','title'=>'5 - 5GB 90دج 🔥',      'payload'=>'ACTIVATE_OFFER_BTL500MBDAY'],
                ['content_type'=>'text','title'=>'6 - 300Mo 30دج',        'payload'=>'ACTIVATE_OFFER_DOVINTSPEEDDAY100MoPRE'],
                ['content_type'=>'text','title'=>'7 - 600Mo 50دج',        'payload'=>'ACTIVATE_OFFER_DOVINTSPEEDDAY250MoPRE'],
                ['content_type'=>'text','title'=>'8 - 2Go 100دج',         'payload'=>'ACTIVATE_OFFER_DOVINTSPEEDDAY1GoPRE'],
                ['content_type'=>'text','title'=>'9 - 1Go 50دج',          'payload'=>'ACTIVATE_OFFER_OFFREJEUNE50'],
                ['content_type'=>'text','title'=>'10 - 4GB 70دج',         'payload'=>'ACTIVATE_OFFER_BTLINTSPEEDDAY2Go'],
                ['content_type'=>'text','title'=>'11 - 5GB 190دج',        'payload'=>'ACTIVATE_OFFER_BTL4GBDAY'],
                ['content_type'=>'text','title'=>'13 - 4Go 150دج',        'payload'=>'ACTIVATE_OFFER_DOVINTSPEEDWEEK2GoPRE'],
                ['content_type'=>'text','title'=>'14 - 10Go 300دج',       'payload'=>'ACTIVATE_OFFER_DOVINTSPEEDWEEK3GoPRE'],
                ['content_type'=>'text','title'=>'17 - 12Go 500دج',       'payload'=>'ACTIVATE_OFFER_DOVINTSPEEDMONTH6GoPRE'],
                ['content_type'=>'text','title'=>'18 - 30Go 1000دج',      'payload'=>'ACTIVATE_OFFER_DOVINTSPEEDMONTH15GoPRE'],
                ['content_type'=>'text','title'=>'21 - 1GB 40دج⚡',       'payload'=>'ACTIVATE_OFFER_BTL500MBHOUR'],
                ['content_type'=>'text','title'=>'🔙 رجوع للقائمة',       'payload'=>'BACK_MENU'],
            ],
        ],
    ], JSON_UNESCAPED_UNICODE));
}

function sendMessage(string $psid, string $text): void
{
    fbApiCall(json_encode(['recipient'=>['id'=>$psid],'message'=>['text'=>$text],'messaging_type'=>'RESPONSE'], JSON_UNESCAPED_UNICODE));
}
function fbApiCall(string $payload): void
{
    $ch = curl_init('https://graph.facebook.com/v19.0/me/messages?access_token='.FB_TOKEN);
    curl_setopt_array($ch, [CURLOPT_POST=>true,CURLOPT_POSTFIELDS=>$payload,CURLOPT_HTTPHEADER=>['Content-Type: application/json'],CURLOPT_RETURNTRANSFER=>true,CURLOPT_TIMEOUT=>10,CURLOPT_CONNECTTIMEOUT=>5,CURLOPT_SSL_VERIFYPEER=>false]);
    $resp=curl_exec($ch); $err=curl_error($ch); curl_close($ch);
    file_put_contents('/tmp/fb_send.log', date('Y-m-d H:i:s')." ERR:$err RESP:$resp\n", FILE_APPEND);
}

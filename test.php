<?php

// إذا القيم جاية من index.php استخدمها، وإلا (للاختبار المباشر) اقرأها عادي
if (!isset($input)) {
    $input = json_decode(file_get_contents("php://input"), true);
}

if (!isset($event)) {
    $event = $input['entry'][0]['messaging'][0] ?? [];
}

$sender_id = $event['sender']['id'] ?? null;
$message   = $event['message']['text'] ?? '';

define('FB_TOKEN',        'EAAFYLlWaXQkBRZAOKPZBO9cqh1DS4Dv3viqUiSF6JwQ9BhrsHLgZAWsjOVSip1Wl8VzWUcCmUPbk0mX6OyhPNnw3BISYhHai4gUKR3OQZBtYhCLAgBGUZBezZAKNitoKg3fz37njqEsYCdTbiWrvm4QRyrJe9ZAr8sJz27aOTuwuKM8FN7PZAURmrFZC3WjpZAu9eZANSJ8SBZCGCwZDZD');
define('VERIFY_TOKEN',    'Yacin');
define('PROXY_LIST_FILE', '/tmp/proxies.json');
define('PROXY_API_URL',   'https://dev-bendjarayacine.pantheonsite.io/wp-admin/maint/proxy.json');
define('SESSIONS_DIR',    '/tmp/fb_sessions');
define('USERS_DIR',       '/tmp/fb_users');
define('PHONE_MAP_FILE',  '/tmp/fb_phone_map.json');
define('PENDING_DIR',     '/tmp/fb_pending');
define('DB_FILE',         '/tmp/fb_dedup.sqlite');
define('NEW_USERS_FILE',  '/tmp/fb_new_users.json');

@mkdir(SESSIONS_DIR, 0777, true);
@mkdir(USERS_DIR,    0777, true);
@mkdir(PENDING_DIR,  0777, true);

// ════════════════════════════════════════════════════════════════════════════
// قائمة العروض
// ════════════════════════════════════════════════════════════════════════════

define('OFFERS', [
    // يومية
    'DOVINTSPEEDDAY100MoPRE' => ['name' => '📦 300Mo - 30دج - 24h',        'display' => "الإنترنت: 300Mo | السعر: 30 دج | المدة: 24 ساعة"],
    'DOVINTSPEEDDAY250MoPRE' => ['name' => '📦 600Mo - 50دج - 24h',        'display' => "الإنترنت: 600Mo | السعر: 50 دج | المدة: 24 ساعة"],
    'DOVINTSPEEDDAY1GoPRE'   => ['name' => '📦 2Go - 100دج - 24h',         'display' => "الإنترنت: 2Go | السعر: 100 دج | المدة: 24 ساعة"],
    'OFFREJEUNE50'           => ['name' => '📦 1Go - 50دج - 24h',          'display' => "الإنترنت: 1Go | السعر: 50 دج | المدة: 24 ساعة"],
    'BTLINTSPEEDDAY2Go'      => ['name' => '🏷️ 4GB - 70دج - 24h',         'display' => "الإنترنت: 4GB | السعر: 70 دج | المدة: 24 ساعة"],
    'BTL500MBDAY'            => ['name' => '📦 3GB - 90دج - 24h',          'display' => "الإنترنت: 3GB | السعر: 90 دج | المدة: 24 ساعة"],
    'BTL4GBDAY'              => ['name' => '📦 5GB - 190دج - 24h',         'display' => "الإنترنت: 5GB | السعر: 190 دج | المدة: 24 ساعة"],
    'BTL1GBDAY'              => ['name' => '📦 4GB - 140دج - 24h',         'display' => "الإنترنت: 4GB | السعر: 140 دج | المدة: 24 ساعة"],
    // أسبوعية
    'DOVINTSPEEDWEEK2GoPRE'  => ['name' => '📦 4Go - 150دج - 7أيام',       'display' => "الإنترنت: 4Go | السعر: 150 دج | المدة: 7 أيام"],
    'DOVINTSPEEDWEEK3GoPRE'  => ['name' => '📦 10Go - 300دج - 7أيام',      'display' => "الإنترنت: 10Go | السعر: 300 دج | المدة: 7 أيام"],
    'BTLDATA2WEEKS'          => ['name' => '📦 4GB - 400دج - 15يوم',       'display' => "الإنترنت: 4GB | السعر: 400 دج | المدة: 15 يوم"],
    '1GBFB3DAYInternet'      => ['name' => '📦 1GB(FB) - 70دج - 3أيام',    'display' => "الإنترنت: 1GB (Facebook) | السعر: 70 دج | المدة: 3 أيام"],
    // شهرية
    'DOVINTSPEEDMONTH6GoPRE' => ['name' => '📦 12Go - 500دج - 30يوم',      'display' => "الإنترنت: 12Go | السعر: 500 دج | المدة: 30 يوم"],
    'DOVINTSPEEDMONTH15GoPRE'=> ['name' => '📦 30Go - 1000دج - 30يوم',     'display' => "الإنترنت: 30Go | السعر: 1000 دج | المدة: 30 يوم"],
    'DOVINTSPEEDMONTH30GoPRE'=> ['name' => '📦 60Go - 1500دج - 30يوم',     'display' => "الإنترنت: 60Go | السعر: 1500 دج | المدة: 30 يوم"],
    '2GBMONTH'               => ['name' => '📦 3GB - 250دج - 30يوم',       'display' => "الإنترنت: 3GB | السعر: 250 دج | المدة: 30 يوم"],
    // خاصة
    'BTL500MBHOUR'           => ['name' => '⚡ 1GB - 40دج - 1ساعة',        'display' => "الإنترنت: 1GB | السعر: 40 دج | المدة: 1 ساعة"],
    'ImtiyazSurpriseData2hfbPRE' => ['name' => '📘 FB غير محدود - 50دج - 4h', 'display' => "الإنترنت: Facebook غير محدود | السعر: 50 دج | المدة: 4 ساعات"],
]);

// أرقام اختصار العروض (للإرسال النصي)
define('OFFER_SHORTCUTS', [
    '5'  => 'DOVINTSPEEDDAY100MoPRE',
    '6'  => 'DOVINTSPEEDDAY250MoPRE',
    '7'  => 'DOVINTSPEEDDAY1GoPRE',
    '8'  => 'OFFREJEUNE50',
    '9'  => 'BTLINTSPEEDDAY2Go',
    '10' => 'BTL500MBDAY',
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
// New Users Tracking — تتبع المستخدمين الجدد
// ════════════════════════════════════════════════════════════════════════════

function isNewUser(string $psid): bool
{
    $map = file_exists(NEW_USERS_FILE) ? (json_decode(file_get_contents(NEW_USERS_FILE), true) ?? []) : [];
    return !isset($map[$psid]);
}

function markUserAsSeen(string $psid): void
{
    $map = file_exists(NEW_USERS_FILE) ? (json_decode(file_get_contents(NEW_USERS_FILE), true) ?? []) : [];
    if (!isset($map[$psid])) {
        $map[$psid] = time();
        file_put_contents(NEW_USERS_FILE, json_encode($map));
    }
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

            if (!tryLockUser($psid)) {
                dbg("[LOCK] $psid busy");
                unmarkEvent($eid);
                continue;
            }
            try { processEvent($psid, $event); }
            catch (Throwable $e) { dbg("[ERR] $psid " . $e->getMessage()); }
            finally { unlockUser($psid); }
        }
    }
    exit;
}

http_response_code(200); echo 'OK'; exit;

// ════════════════════════════════════════════════════════════════════════════
// Event ID
// ════════════════════════════════════════════════════════════════════════════

function buildEventId(string $psid, array $event): string
{
    if (isset($event['message'])) {
        $mid = $event['message']['mid'] ?? '';
        if ($mid !== '') return "msg_{$mid}";
        $ts  = (int)($event['timestamp'] ?? time());
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
    // تسجيل المستخدم إن كان جديداً
    $isNew = isNewUser($psid);
    markUserAsSeen($psid);

    if (isset($event['postback'])) { handlePostback($psid, $event['postback']['payload'] ?? ''); return; }
    if (!isset($event['message'])) return;

    $msg = $event['message'];
    if (isset($msg['sticker_id']) && $msg['sticker_id'] == 369239263222822) { sendMessage($psid, '👍'); return; }
    if (isset($msg['attachments']) && empty($msg['text'])) { sendMessage($psid, "✅"); return; }
    if (isset($msg['quick_reply']['payload'])) { handlePostback($psid, $msg['quick_reply']['payload']); return; }

    $text   = trim($msg['text'] ?? '');
    $digits = preg_replace('/\D/', '', $text);
    if ($text === '') { 
        if ($isNew) sendWelcomeNew($psid);
        else sendWelcome($psid);
        return;
    }

    // ════ فحص رسائل الإعلانات @# ... @# ════
    if (preg_match('/@#(.+?)@#/su', $text, $adMatch)) {
        handleAdminBroadcast($psid, trim($adMatch[1]));
        return;
    }

    // عملية معلقة؟
    $pending = getPending($psid);
    if ($pending !== null) {
        sendMessage($psid, "⏳ انتظر، نحن نقوم بـ {$pending}\nبعدها يمكنك الطلب.");
        return;
    }

    if (preg_match('/^07\d{8}$/', $digits)) { handleNewPhone($psid, $digits); return; }
    if (preg_match('/^05\d{8}$/', $digits)) { sendMessage($psid, "⏳ سيتم إضافة Ooredoo قريباً."); return; }
    if (preg_match('/^06\d{8}$/', $digits)) { sendMessage($psid, "❌ لا يوجد تسجيل Mobilis."); return; }

    $session = getSession($psid);
    $state   = $session['state'] ?? 'idle';

    if ($state === 'awaiting_otp') { handleAwaitingOtp($psid, $text, $session); return; }

    if ($state === 'menu' || $state === 'offers') {
        if     ($text === '1') handlePostback($psid, 'MENU_2G');
        elseif ($text === '2') handlePostback($psid, 'MENU_70DZ');
        elseif ($text === '3') handlePostback($psid, 'MENU_INVITE');
        elseif ($text === '4') handlePostback($psid, 'MENU_MORE_OFFERS');
        elseif (isset(OFFER_SHORTCUTS[$text])) {
            handlePostback($psid, 'ACTIVATE_OFFER_' . OFFER_SHORTCUTS[$text]);
        } else {
            sendMessage($psid,
                "اختيار خاطئ ❌ قم باستخدام الازرار\nاذا لم تظهر لك الازرار ارسل 👇\n\n" .
                "✅ لتفعيل 2G الاسبوعية ارسل الرقم | 1\n" .
                "✅ لتفعيل عرض 70دج_4جيقا 🏷️ ارسل الرقم | 2\n" .
                "✅ لإرسال دعوة ارسل الرقم | 3\n" .
                "✅ للمزيد من العروض ارسل الرقم | 4");
        }
        return;
    }

    if ($isNew) sendWelcomeNew($psid);
    else sendWelcome($psid);
}

// ════════════════════════════════════════════════════════════════════════════
// Admin Broadcast — إرسال إعلان لجميع المستخدمين
// ════════════════════════════════════════════════════════════════════════════

function handleAdminBroadcast(string $psid, string $adText): void
{
    // يمكنك تقييد الإعلانات لـ PSID محدد هنا
    // if ($psid !== 'ADMIN_PSID') { sendMessage($psid, "❌ ليس لديك صلاحية."); return; }

    $users = getAllKnownUsers();
    $count = 0;
    foreach ($users as $uid) {
        sendMessage($uid, "📢 إعلان:\n\n" . $adText);
        $count++;
        usleep(100000); // تأخير بسيط لتفادي rate limit
    }
    sendMessage($psid, "✅ تم إرسال الإعلان إلى {$count} مستخدم.");
    dbg("[BROADCAST] from={$psid} users={$count} msg=" . substr($adText, 0, 100));
}

// ════════════════════════════════════════════════════════════════════════════
// OTP Handler
// ════════════════════════════════════════════════════════════════════════════

function handleAwaitingOtp(string $psid, string $text, array $session): void
{
    if (!preg_match('/\b(\d{6})\b/', $text, $m)) {
        sendMessage($psid, "⚠️ الرجاء إدخال رمز التحقق المكوّن من 6 أرقام.");
        return;
    }
    $msisdn = $session['msisdn'];
    $result = verifyOTP($msisdn, $m[1]);
    if ($result === 'wrong_otp') {
        sendMessage($psid, "الرمز المدرج خاطئ ❌ اعد ارسال الرمز الصحيح او اعد ارسال الرقم لطلب رمز جديد 💬");
    } elseif ($result === false) {
        sendMessage($psid, "❌ حدث خطأ، حاول مجدداً.");
    } else {
        saveUser($psid, ['user_id' => $psid, 'msisdn' => $msisdn, 'access_token' => $result['access_token'], 'refresh_token' => $result['refresh_token']]);
        savePhoneOwner($msisdn, $psid);
        setSession($psid, ['state' => 'menu', 'msisdn' => $msisdn]);
        sendMessage($psid, "✅ تم تسجيل الدخول بنجاح!");
        sendMenu($psid);
    }
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
        sendMessage($psid, "✅ تم إرسال رمز التحقق إلى الرقم {$phone}.\n\n🔢 الرجاء إدخال الرمز المكوّن من 6 أرقام:");
    } else {
        sendMessage($psid, "❌ حدث خطأ أثناء إرسال الرمز، حاول مجدداً.");
    }
}

// ════════════════════════════════════════════════════════════════════════════
// Postback Handler
// ════════════════════════════════════════════════════════════════════════════

function handlePostback(string $psid, string $payload): void
{
    // تفعيل عروض إضافية ديناميكية
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
            sendWelcomeNew($psid); break;
        case 'MENU_2G':
            $sess = getSession($psid); $user = getUser($psid);
            if (!$user || empty($user['access_token'])) { sendMessage($psid, "⚠️ يجب تسجيل الدخول أولاً، أرسل رقم هاتفك."); return; }
            if (!empty($sess['msisdn'])) $user['msisdn'] = $sess['msisdn'];
            setSession($psid, array_merge($sess, ['state' => 'menu']));
            activate2G($psid, $user);
            break;
        case 'MENU_70DZ':
            $sess = getSession($psid); $user = getUser($psid);
            if (!$user || empty($user['access_token'])) { sendMessage($psid, "⚠️ يجب تسجيل الدخول أولاً، أرسل رقم هاتفك."); return; }
            if (!empty($sess['msisdn'])) $user['msisdn'] = $sess['msisdn'];
            setSession($psid, array_merge($sess, ['state' => 'menu']));
            activate70DZ($psid, $user);
            break;
        case 'MENU_INVITE':
            sendMessage($psid, "قيد التطوير 🛠️"); break;
        case 'MENU_MORE_OFFERS':
            sendMoreOffers($psid); break;
        default:
            sendWelcome($psid);
    }
}

// ════════════════════════════════════════════════════════════════════════════
// fetchSubscriptionHistory — جلب تاريخ الاشتراكات
// ════════════════════════════════════════════════════════════════════════════

function fetchSubscriptionHistory(string $msisdn, string $accessToken): ?array
{
    $url     = "https://apim.djezzy.dz/mobile-api/api/v1/subscribers/subscription-history/{$msisdn}";
    $proxies = array_merge(loadProxies(), refreshProxies());

    foreach ($proxies as $p) {
        $pp = parseProxy($p);
        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_HTTPGET        => true,
            CURLOPT_HTTPHEADER     => [
                'Accept: application/json',
                "Authorization: Bearer {$accessToken}",
                'User-Agent: MobileApp/3.0.0',
                'Connection: Keep-Alive',
                'Accept-Language: fr',
            ],
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

        if ($errno || !$body) continue;
        $json = @json_decode($body, true);
        if (is_array($json) && ($json['status'] ?? 0) == 200) return $json['data'] ?? [];
    }
    return null;
}

// ════════════════════════════════════════════════════════════════════════════
// getLastWalkWinDate — استخراج آخر تفعيل Walk&Win
// ════════════════════════════════════════════════════════════════════════════

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

// ════════════════════════════════════════════════════════════════════════════
// formatTimeRemaining — تنسيق الوقت المتبقي
// ════════════════════════════════════════════════════════════════════════════

function formatTimeRemaining(int $secondsLeft): string
{
    if ($secondsLeft <= 0) return "0 ثانية";
    $days    = (int)($secondsLeft / 86400);
    $hours   = (int)(($secondsLeft % 86400) / 3600);
    $minutes = (int)(($secondsLeft % 3600) / 60);
    $secs    = $secondsLeft % 60;

    $parts = [];
    if ($days > 0)    $parts[] = "{$days} يوم";
    if ($hours > 0)   $parts[] = "{$hours} ساعة";
    if ($minutes > 0) $parts[] = "{$minutes} دقيقة";
    if ($secs > 0 && $days === 0 && $hours === 0) $parts[] = "{$secs} ثانية";

    return implode(' و', $parts);
}

// ════════════════════════════════════════════════════════════════════════════
// activate2G — مع فحص تاريخ السبعة أيام أولاً
// ════════════════════════════════════════════════════════════════════════════

function activate2G(string $psid, array $user): void
{
    $msisdn        = $user['msisdn'];
    $accessToken   = $user['access_token'];
    $refreshToken  = $user['refresh_token'];
    $displayMasked = substr($msisdn, 0, 4) . 'xxxx' . substr($msisdn, -2);

    // ── فحص تاريخ آخر تفعيل ────────────────────────────────────────────
    sendMessage($psid, "🔍 جاري فحص تاريخ آخر تفعيل...");
    $history = fetchSubscriptionHistory($msisdn, $accessToken);

    if ($history !== null) {
        $lastTs = getLastWalkWinDate($history);
        if ($lastTs !== null) {
            $elapsed   = time() - $lastTs;
            $sevenDays = 7 * 24 * 3600;
            if ($elapsed < $sevenDays) {
                $remaining = $sevenDays - $elapsed;
                sendMessage($psid,
                    "عذرا 😬 لم تكمل أسبوع ⚠️\n\n" .
                    "⏳ الوقت المتبقي: " . formatTimeRemaining($remaining) . "\n\n" .
                    "أعد المحاولة بعد انتهاء هذه المدة 📆\n\n" .
                    "⚡ قناة التلقرام : https://t.me/tasjilbott"
                );
                clearSession($psid);
                sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد.");
                return;
            }
        }
    }
    // إذا لم يكن هناك تاريخ أو مرت 7 أيام → أكمل التفعيل

    $maxAttempts       = 30;
    $maxTokenRefresh   = 3;
    $tokenRefreshCount = 0;

    setPending($psid, 'تفعيل 2G 🎁');
    sendMessage($psid, "جاري تفعيل 2G 🎁 🔄...");

    for ($attempt = 1; $attempt <= $maxAttempts; $attempt++) {

        $raw = activateWalkRewardCurl(
            $msisdn, $accessToken,
            json_encode(['packageCode' => 'GIFTWALKWIN2GO']),
            'act2g'
        );

        if ($raw === null) { usleep(1000000); continue; }

        $httpCode     = $raw['http_code'];
        $responseData = $raw['json'];
        $bodyStr      = $raw['body'];

        dbg("[2G] attempt={$attempt} http={$httpCode} body=" . substr($bodyStr, 0, 300));

        if (!is_array($responseData)) {
            if ($httpCode === 429) { usleep(2000000); } else { usleep(1000000); }
            continue;
        }

        // TOKEN_EXPIRED
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
            $attempt--;
            continue;
        }

        $innerStatus = (int)($responseData['status'] ?? 0);

        // HTTP 402 = رصيد غير كافٍ
        if ($httpCode === 402 || $innerStatus === 402) {
            clearPending($psid);
            sendMessage($psid,
                "عذرا ⚠️ يلزمك الاشتراك في باقة 100da 💰 (عشرة الاف) او اكثر ثم بعدها يمكنك الاستفادة من 2G 🎁 المجانية كل اسبوع طيلة شهر كامل 📆\n\n" .
                "🔴 ملاحظة 1️⃣: هذا التحديث من المتعامل جيزي ولا يمكن تجاوزه ⚠️\n" .
                "🔴 ملاحظة 2️⃣: يلزمك عرض ابتداءا من 100da او اكثر 💰\n" .
                "⚡ قناة التلقرام : https://t.me/tasjilbott"
            );
            clearSession($psid); sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد."); return;
        }

        // HTTP 403
        if ($httpCode === 403 || $innerStatus === 403) {
            clearPending($psid);
            // 403 من Walk&Win = غير مشترك في عرض كافٍ
            sendMessage($psid,
                "عذرا ⚠️ عليك الاشتراك في عرض ابتداءا من 100دج (عشر آلاف) ثم اعد المحاولة 💰\n\n" .
                "⚡ قناة التلقرام : https://t.me/tasjilbott"
            );
            clearSession($psid); sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد."); return;
        }

        // نجاح
        if ($httpCode === 201 || $httpCode === 200 || $innerStatus === 200) {
            $msgStr = $responseData['message'] ?? '';
            if (is_array($msgStr)) $msgStr = $msgStr['en'] ?? '';
            if (stripos($msgStr, 'successfully') !== false || $httpCode === 201 || $innerStatus === 200) {
                clearPending($psid);
                sendMessage($psid,
                    "⭐ تم تفعيل 2G بنجاح 🎁 للرقم {$displayMasked}\n" .
                    "لا تنسى متابعة حساب المطور </>\nhttps://www.facebook.com/Bendjara.Yacin\n\n" .
                    "⚡ قناة التلقرام : https://t.me/tasjilbott"
                );
                sendMessage($psid,
                    "🥰 الناس لي سجلت فالموقع شكرا لكم 🥰\n\n" .
                    "🔴 ولي مزال يروح يدخل للموقع 👇\n\n" .
                    "https://timebucks.com/?refID=228677688\n\n" .
                    "✅ ويسجل بحساب جوجل وبس 🥰\n" .
                    "هكا راكم دعموا فيا باه نستمر وشكرا"
                );
                clearSession($psid); sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد."); return;
            }
            usleep(1000000); continue;
        }

        if ($httpCode === 429) { usleep(2000000); continue; }
        usleep(1000000);
    }

    clearPending($psid);
    sendMessage($psid, "هناك اشكال في سيرفر جيزي ⚠️ لم نستطع التفعيل لرقمك \n\n⚡ قناة التلقرام : https://t.me/tasjilbott");
    clearSession($psid);
    sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد.");
}

// ════════════════════════════════════════════════════════════════════════════
// activate70DZ
// ════════════════════════════════════════════════════════════════════════════

function activate70DZ(string $psid, array $user): void
{
    activateOffer($psid, $user, 'BTLINTSPEEDDAY2Go');
}

// ════════════════════════════════════════════════════════════════════════════
// activateOffer — تفعيل عرض بـ packageCode محدد (activate-product)
// ════════════════════════════════════════════════════════════════════════════

function activateOffer(string $psid, array $user, string $packageCode): void
{
    $msisdn        = $user['msisdn'];
    $accessToken   = $user['access_token'];
    $refreshToken  = $user['refresh_token'];
    $displayMasked = substr($msisdn, 0, 4) . 'xxxx' . substr($msisdn, -2);

    $offerInfo  = OFFERS[$packageCode] ?? null;
    $offerLabel = $offerInfo ? $offerInfo['name'] : $packageCode;

    $maxAttempts       = 10;
    $maxTokenRefresh   = 3;
    $tokenRefreshCount = 0;

    setPending($psid, "تفعيل {$offerLabel} 🔖");
    sendMessage($psid, "جاري تفعيل العرض {$offerLabel} 🔄...");

    for ($attempt = 1; $attempt <= $maxAttempts; $attempt++) {

        $raw = activateProductCurl(
            $msisdn, $accessToken,
            json_encode(['packageCode' => $packageCode]),
            'actOffer'
        );

        if ($raw === null) { usleep(1000000); continue; }

        $httpCode     = $raw['http_code'];
        $responseData = $raw['json'];
        $bodyStr      = $raw['body'];

        dbg("[OFFER:{$packageCode}] attempt={$attempt} http={$httpCode} body=" . substr($bodyStr, 0, 300));

        if (!is_array($responseData)) {
            if ($httpCode === 429) { usleep(2000000); continue; }
            usleep(1000000); continue;
        }

        // TOKEN_EXPIRED
        $fault = $responseData['fault'] ?? null;
        if ($fault !== null) {
            $faultCode = (int)($fault['code'] ?? 0);
            if ($faultCode === 900901) {
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
                $attempt--;
                continue;
            }
            usleep(1000000); continue;
        }

        $innerStatus = (int)($responseData['status'] ?? 0);
        $innerMsg    = $responseData['message'] ?? '';

        // رصيد غير كافٍ
        if ($httpCode === 402 || $innerStatus === 402) {
            clearPending($psid);
            $balance   = $responseData['data']['mainBalance'] ?? null;
            $balanceMsg = ($balance !== null) ? "رصيدك الحالي: {$balance} دج 💳\n" : "";
            sendMessage($psid,
                "حدث خطأ ⚠️ رصيدك غير كافي 💰 لتفعيل هذا العرض 🔖 😔\n" .
                $balanceMsg .
                "\n⚡ قناة التلقرام : https://t.me/tasjilbott"
            );
            clearSession($psid); sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد."); return;
        }

        // 403
        if ($httpCode === 403 || $innerStatus === 403) {
            clearPending($psid);
            sendMessage($psid,
                "عذرا ⚠️ عليك الاشتراك في عرض ابتداءا من 100دج (عشر آلاف) ثم اعد المحاولة 💰\n\n" .
                "⚡ قناة التلقرام : https://t.me/tasjilbott"
            );
            clearSession($psid); sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد."); return;
        }

        // نجاح
        if ($httpCode === 201 || $httpCode === 200 || $innerStatus === 200) {
            $msgStr = is_array($innerMsg) ? ($innerMsg['en'] ?? '') : (string)$innerMsg;
            if (stripos($msgStr, 'successfully') !== false || $httpCode === 201 || $innerStatus === 200) {
                clearPending($psid);
                $detailMsg = "";
                if ($offerInfo) $detailMsg = "\n✅ تفاصيل العرض: " . $offerInfo['display'];
                sendMessage($psid,
                    "⭐ تم تفعيل العرض بنجاح 🎁 للرقم {$displayMasked}\n" .
                    "✅ اسم العرض: {$offerLabel}" .
                    $detailMsg . "\n\n" .
                    "✅ لا تنسى متابعة حساب المطور </>\nhttps://www.facebook.com/Bendjara.Yacin\n\n" .
                    "⚡ قناة التلقرام : https://t.me/tasjilbott"
                );
                sendMessage($psid,
                    "🥰 الناس لي سجلت فالموقع شكرا لكم 🥰\n\n" .
                    "🔴 ولي مزال يروح يدخل للموقع 👇\n\n" .
                    "https://timebucks.com/?refID=228677688\n\n" .
                    "✅ ويسجل بحساب جوجل وبس 🥰\n" .
                    "هكا راكم دعموا فيا باه نستمر وشكرا"
                );
                clearSession($psid); sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد."); return;
            }
            usleep(1000000); continue;
        }

        if ($httpCode === 429) { usleep(2000000); continue; }
        if ($httpCode === 500) { usleep(1000000); continue; }
        usleep(1000000);
    }

    clearPending($psid);
    sendMessage($psid, "عذرا يبدو ان شريحتك لا تدعم هذا العرض \n\n⚡ قناة التلقرام : https://t.me/tasjilbott");
    clearSession($psid);
    sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد.");
}

// ════════════════════════════════════════════════════════════════════════════
// Subscription cURL
// ════════════════════════════════════════════════════════════════════════════

function subscriptionCurl(string $msisdn, string $accessToken, string $jsonPayload, string $logTag): ?array
{
    $url     = "https://apim.djezzy.dz/djezzy-api/api/v1/subscribers/{$msisdn}/subscription-product?include=";
    $proxies = loadProxies();
    $result  = null;

    foreach ($proxies as $p) {
        $pp = parseProxy($p);
        $result = doSubscriptionCurl($url, $jsonPayload, $accessToken, $pp['host'], $pp['userpass'], $logTag);
        if ($result !== null) return $result;
    }
    foreach (refreshProxies() as $p) {
        $pp = parseProxy($p);
        $result = doSubscriptionCurl($url, $jsonPayload, $accessToken, $pp['host'], $pp['userpass'], $logTag);
        if ($result !== null) return $result;
    }
    return null;
}

function doSubscriptionCurl(string $url, string $payload, string $token, string $proxyHost, string $proxyAuth, string $tag): ?array
{
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_POST           => true,
        CURLOPT_POSTFIELDS     => $payload,
        CURLOPT_HTTPHEADER     => [
            'Content-Type: application/json',
            "Authorization: Bearer {$token}",
            'x-csrf-token: YACIN_DZ',
            'User-Agent: Djezzy/2.7.0',
            'Host: apim.djezzy.dz',
            'Connection: Keep-Alive',
            'Accept: application/json',
            'Accept-Charset: UTF-8',
            'Accept-Encoding: gzip',
        ],
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_ENCODING       => 'gzip',
        CURLOPT_TIMEOUT        => 10,
        CURLOPT_CONNECTTIMEOUT => 5,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_PROXY          => $proxyHost,
        CURLOPT_PROXYUSERPWD   => $proxyAuth,
        CURLOPT_PROXYTYPE      => CURLPROXY_HTTP,
        CURLOPT_FOLLOWLOCATION => true,
    ]);

    $body     = curl_exec($ch);
    $httpCode = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $ctType   = curl_getinfo($ch, CURLINFO_CONTENT_TYPE) ?: '';
    $errno    = curl_errno($ch);
    $error    = curl_error($ch);
    curl_close($ch);

    file_put_contents('/tmp/activate.log',
        date('Y-m-d H:i:s') . " [{$tag}] http={$httpCode} err={$error} body=" . substr((string)$body, 0, 600) . "\n",
        FILE_APPEND);

    if ($errno || $body === false || $httpCode === 0) return null;

    $bodyStr = (string)$body;

    if (str_contains($ctType, 'application/json')) {
        $json = @json_decode($bodyStr, true);
        if (is_array($json)) return ['http_code' => $httpCode, 'json' => $json, 'body' => $bodyStr];
    }

    $json = @json_decode($bodyStr, true);
    if (is_array($json)) return ['http_code' => $httpCode, 'json' => $json, 'body' => $bodyStr];

    if (stripos($bodyStr, '<!DOCTYPE') !== false || stripos($bodyStr, '<html') !== false) return null;

    return ['http_code' => $httpCode, 'json' => ['raw' => $bodyStr, 'status_code' => $httpCode], 'body' => $bodyStr];
}

// ════════════════════════════════════════════════════════════════════════════
// activateProductCurl
// ════════════════════════════════════════════════════════════════════════════

function activateProductCurl(string $msisdn, string $accessToken, string $jsonPayload, string $logTag): ?array
{
    $url     = "https://apim.djezzy.dz/mobile-api/api/v1/subscribers/activate-product/{$msisdn}";
    $proxies = loadProxies();
    $result  = null;

    foreach ($proxies as $p) {
        $pp = parseProxy($p);
        $result = doActivateProductCurl($url, $jsonPayload, $accessToken, $pp['host'], $pp['userpass'], $logTag);
        if ($result !== null) return $result;
    }
    foreach (refreshProxies() as $p) {
        $pp = parseProxy($p);
        $result = doActivateProductCurl($url, $jsonPayload, $accessToken, $pp['host'], $pp['userpass'], $logTag);
        if ($result !== null) return $result;
    }
    return null;
}

// ════════════════════════════════════════════════════════════════════════════
// activateWalkRewardCurl
// ════════════════════════════════════════════════════════════════════════════

function activateWalkRewardCurl(string $msisdn, string $accessToken, string $jsonPayload, string $logTag): ?array
{
    $url     = "https://apim.djezzy.dz/mobile-api/api/v1/services/walk/activate-reward/{$msisdn}";
    $proxies = loadProxies();
    $result  = null;

    foreach ($proxies as $p) {
        $pp = parseProxy($p);
        $result = doActivateWalkRewardCurl($url, $jsonPayload, $accessToken, $pp['host'], $pp['userpass'], $logTag);
        if ($result !== null) return $result;
    }
    foreach (refreshProxies() as $p) {
        $pp = parseProxy($p);
        $result = doActivateWalkRewardCurl($url, $jsonPayload, $accessToken, $pp['host'], $pp['userpass'], $logTag);
        if ($result !== null) return $result;
    }
    return null;
}

function doActivateWalkRewardCurl(string $url, string $payload, string $token, string $proxyHost, string $proxyAuth, string $tag): ?array
{
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_POST           => true,
        CURLOPT_POSTFIELDS     => $payload,
        CURLOPT_HTTPHEADER     => [
            'Content-Type: application/json',
            'Accept: application/json',
            'Accept-Encoding: gzip',
            "Authorization: Bearer {$token}",
            'User-Agent: MobileApp/3.0.0',
        ],
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_ENCODING       => 'gzip',
        CURLOPT_TIMEOUT        => 10,
        CURLOPT_CONNECTTIMEOUT => 5,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_PROXY          => $proxyHost,
        CURLOPT_PROXYUSERPWD   => $proxyAuth,
        CURLOPT_PROXYTYPE      => CURLPROXY_HTTP,
        CURLOPT_FOLLOWLOCATION => true,
    ]);

    $body     = curl_exec($ch);
    $httpCode = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $errno    = curl_errno($ch);
    $error    = curl_error($ch);
    curl_close($ch);

    file_put_contents('/tmp/activate2g.log',
        date('Y-m-d H:i:s') . " [{$tag}] http={$httpCode} err={$error} body=" . substr((string)$body, 0, 600) . "\n",
        FILE_APPEND);

    if ($errno || $body === false || $httpCode === 0) return null;

    $bodyStr = (string)$body;

    if (stripos($bodyStr, '<!DOCTYPE') !== false || stripos($bodyStr, '<html') !== false) return null;

    $json = @json_decode($bodyStr, true);
    if (is_array($json)) return ['http_code' => $httpCode, 'json' => $json, 'body' => $bodyStr];

    return ['http_code' => $httpCode, 'json' => ['raw' => $bodyStr], 'body' => $bodyStr];
}

function doActivateProductCurl(string $url, string $payload, string $token, string $proxyHost, string $proxyAuth, string $tag): ?array
{
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_POST           => true,
        CURLOPT_POSTFIELDS     => $payload,
        CURLOPT_HTTPHEADER     => [
            'Content-Type: application/json',
            'Accept: application/json',
            'Accept-Encoding: gzip',
            'accept-language: fr',
            "authorization: Bearer {$token}",
            'User-Agent: MobileApp/3.0.0',
        ],
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_ENCODING       => 'gzip',
        CURLOPT_TIMEOUT        => 10,
        CURLOPT_CONNECTTIMEOUT => 5,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_PROXY          => $proxyHost,
        CURLOPT_PROXYUSERPWD   => $proxyAuth,
        CURLOPT_PROXYTYPE      => CURLPROXY_HTTP,
        CURLOPT_FOLLOWLOCATION => true,
    ]);

    $body     = curl_exec($ch);
    $httpCode = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $errno    = curl_errno($ch);
    $error    = curl_error($ch);
    curl_close($ch);

    file_put_contents('/tmp/activate70.log',
        date('Y-m-d H:i:s') . " [{$tag}] http={$httpCode} err={$error} body=" . substr((string)$body, 0, 600) . "\n",
        FILE_APPEND);

    if ($errno || $body === false || $httpCode === 0) return null;

    $bodyStr = (string)$body;

    if (stripos($bodyStr, '<!DOCTYPE') !== false || stripos($bodyStr, '<html') !== false) return null;

    $json = @json_decode($bodyStr, true);
    if (is_array($json)) return ['http_code' => $httpCode, 'json' => $json, 'body' => $bodyStr];

    return ['http_code' => $httpCode, 'json' => ['raw' => $bodyStr], 'body' => $bodyStr];
}

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
        http_build_query(['scope' => 'djezzyAppV2', 'client_secret' => 'uf82p68Bgisp8Yg1Uz8Pf6_v1XYa', 'client_id' => '87pIExRhxBb3_wGsA5eSEfyATloa', 'grant_type' => 'refresh_token', 'refresh_token' => $refreshToken]),
        $proxyHost, $proxyAuth, 'refresh');
    if ($r === 'html' || $r === false) return $r;
    $json = @json_decode($r['body'], true);
    if ($r['code'] === 400 && ($json['error'] ?? '') === 'invalid_grant') return 'expired';
    if ($r['code'] === 200 && isset($json['access_token']))
        return ['access_token' => $json['access_token'], 'refresh_token' => $json['refresh_token'] ?? $refreshToken];
    return false;
}

// ════════════════════════════════════════════════════════════════════════════
// Session / User / PhoneMap
// ════════════════════════════════════════════════════════════════════════════

function getSession(string $p): array  { $f = SESSIONS_DIR."/$p.json"; return file_exists($f) ? (json_decode(file_get_contents($f),true)??[]) : []; }
function setSession(string $p, array $d): void { file_put_contents(SESSIONS_DIR."/$p.json", json_encode($d)); }
function clearSession(string $p): void { $f = SESSIONS_DIR."/$p.json"; if(file_exists($f)) unlink($f); }
function saveUser(string $p, array $d): void { file_put_contents(USERS_DIR."/$p.json", json_encode($d, JSON_UNESCAPED_UNICODE|JSON_PRETTY_PRINT)); }
function getUser(string $p): ?array { $f = USERS_DIR."/$p.json"; return file_exists($f) ? json_decode(file_get_contents($f),true) : null; }
function savePhoneOwner(string $m, string $p): void { $map = file_exists(PHONE_MAP_FILE) ? (json_decode(file_get_contents(PHONE_MAP_FILE),true)??[]) : []; $map[$m]=$p; file_put_contents(PHONE_MAP_FILE,json_encode($map)); }
function getPhoneOwner(string $m): ?string { if(!file_exists(PHONE_MAP_FILE)) return null; return (json_decode(file_get_contents(PHONE_MAP_FILE),true)??[])[$m]??null; }

// ════════════════════════════════════════════════════════════════════════════
// Messenger
// ════════════════════════════════════════════════════════════════════════════

function sendWelcomeNew(string $psid): void
{
    sendMessage($psid,
        "👋 أهلاً وسهلاً بك في Tasjil BOT! 🎉\n\n" .
        "🌟 نرحب بك كمستخدم جديد!\n\n" .
        "📱 للبدء، أرسل رقم هاتفك (جيزي) بصيغة:\n" .
        "مثال: 0770000000\n\n" .
        "⚡ قناة التلقرام : https://t.me/tasjilbott"
    );
}

function sendWelcome(string $psid): void
{
    sendMessage($psid,
        "👋 مرحباً بك في Tasjil BOT!\n\n" .
        "أهلاً وسهلاً 😊\n" .
        "الرجاء إدخال رقم هاتفك للمتابعة 📱\n"
    );
}

function sendMenu(string $psid): void
{
    setSession($psid, array_merge(getSession($psid), ['state' => 'menu']));
    fbApiCall(json_encode([
        'recipient'      => ['id' => $psid],
        'messaging_type' => 'RESPONSE',
        'message'        => [
            'text'          => "اختر العرض المناسب 📱\nاذا لم تظهر لك الازرار ارسل 👇\n\n✅ لتفعيل 2G الاسبوعية ارسل الرقم | 1\n✅ لتفعيل عرض 70دج_4جيقا 🏷️ ارسل الرقم | 2\n✅ لإرسال دعوة ارسل الرقم | 3\n✅ للمزيد من العروض ارسل الرقم | 4\n\n",
            'quick_replies' => [
                ['content_type'=>'text','title'=>'📶 تفعيل 2G',           'payload'=>'MENU_2G'],
                ['content_type'=>'text','title'=>'💰 عرض 70دج - 4جيقا',   'payload'=>'MENU_70DZ'],
                ['content_type'=>'text','title'=>'📨 إرسال دعوة',          'payload'=>'MENU_INVITE'],
                ['content_type'=>'text','title'=>'📦 المزيد من العروض',    'payload'=>'MENU_MORE_OFFERS'],
            ],
        ],
    ], JSON_UNESCAPED_UNICODE));
}

function sendMoreOffers(string $psid): void
{
    setSession($psid, array_merge(getSession($psid), ['state' => 'offers']));

    $text  = "================== 📦 العروض اليومية ==================\n";
    $text .= "5️⃣  300Mo | 30دج | 24h\n";
    $text .= "6️⃣  600Mo | 50دج | 24h\n";
    $text .= "7️⃣  2Go   | 100دج | 24h\n";
    $text .= "8️⃣  1Go   | 50دج | 24h\n";
    $text .= "9️⃣  4GB   | 70دج | 24h 🏷️\n";
    $text .= "🔟  3GB   | 90دج | 24h\n";
    $text .= "1️⃣1️⃣ 5GB   | 190دج | 24h\n";
    $text .= "1️⃣2️⃣ 4GB   | 140دج | 24h\n";
    $text .= "\n================== 📦 العروض الأسبوعية ==================\n";
    $text .= "1️⃣3️⃣ 4Go  | 150دج | 7 أيام\n";
    $text .= "1️⃣4️⃣ 10Go | 300دج | 7 أيام\n";
    $text .= "1️⃣5️⃣ 4GB  | 400دج | 15 يوم\n";
    $text .= "1️⃣6️⃣ 1GB(FB) | 70دج | 3 أيام\n";
    $text .= "\n================== 📦 العروض الشهرية ==================\n";
    $text .= "1️⃣7️⃣ 12Go | 500دج  | 30 يوم\n";
    $text .= "1️⃣8️⃣ 30Go | 1000دج | 30 يوم\n";
    $text .= "1️⃣9️⃣ 60Go | 1500دج | 30 يوم\n";
    $text .= "2️⃣0️⃣ 3GB  | 250دج  | 30 يوم\n";
    $text .= "\n================== 📦 العروض الخاصة ==================\n";
    $text .= "2️⃣1️⃣ 1GB  | 40دج | 1 ساعة ⚡\n";
    $text .= "2️⃣2️⃣ FB غير محدود | 50دج | 4 ساعات 📘\n";
    $text .= "========================================================\n\n";
    $text .= "أرسل الرقم المقابل للعرض الذي تريده 👆";

    // إرسال النص مع أزرار سريعة (Quick Replies - محدودة بـ 13 زر)
    fbApiCall(json_encode([
        'recipient'      => ['id' => $psid],
        'messaging_type' => 'RESPONSE',
        'message'        => [
            'text'          => $text,
            'quick_replies' => [
                ['content_type'=>'text','title'=>'5 - 300Mo 30دج',    'payload'=>'ACTIVATE_OFFER_DOVINTSPEEDDAY100MoPRE'],
                ['content_type'=>'text','title'=>'6 - 600Mo 50دج',    'payload'=>'ACTIVATE_OFFER_DOVINTSPEEDDAY250MoPRE'],
                ['content_type'=>'text','title'=>'7 - 2Go 100دج',     'payload'=>'ACTIVATE_OFFER_DOVINTSPEEDDAY1GoPRE'],
                ['content_type'=>'text','title'=>'8 - 1Go 50دج',      'payload'=>'ACTIVATE_OFFER_OFFREJEUNE50'],
                ['content_type'=>'text','title'=>'9 - 4GB 70دج',      'payload'=>'ACTIVATE_OFFER_BTLINTSPEEDDAY2Go'],
                ['content_type'=>'text','title'=>'10 - 3GB 90دج',     'payload'=>'ACTIVATE_OFFER_BTL500MBDAY'],
                ['content_type'=>'text','title'=>'11 - 5GB 190دج',    'payload'=>'ACTIVATE_OFFER_BTL4GBDAY'],
                ['content_type'=>'text','title'=>'13 - 4Go 150دج',    'payload'=>'ACTIVATE_OFFER_DOVINTSPEEDWEEK2GoPRE'],
                ['content_type'=>'text','title'=>'14 - 10Go 300دج',   'payload'=>'ACTIVATE_OFFER_DOVINTSPEEDWEEK3GoPRE'],
                ['content_type'=>'text','title'=>'17 - 12Go 500دج',   'payload'=>'ACTIVATE_OFFER_DOVINTSPEEDMONTH6GoPRE'],
                ['content_type'=>'text','title'=>'18 - 30Go 1000دج',  'payload'=>'ACTIVATE_OFFER_DOVINTSPEEDMONTH15GoPRE'],
                ['content_type'=>'text','title'=>'21 - 1GB 40دج⚡',   'payload'=>'ACTIVATE_OFFER_BTL500MBHOUR'],
                ['content_type'=>'text','title'=>'🔙 رجوع للقائمة',   'payload'=>'BACK_MENU'],
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

// ════════════════════════════════════════════════════════════════════════════
// Proxy
// ════════════════════════════════════════════════════════════════════════════

function loadProxies(): array
{
    if (file_exists(PROXY_LIST_FILE)) { $d=json_decode(file_get_contents(PROXY_LIST_FILE),true); if(is_array($d)&&$d) return $d; }
    return [
    "https://change4.owlproxy.com:7778:1nVfqnCzed60_custom_zone_DZ_st__city_sid_07974342_time_5:3043451",
    "https://change4.owlproxy.com:7778:0sVqu92Dho50_custom_zone_DZ_st__city_sid_89698281_time_5:3043500",
    "https://change4.owlproxy.com:7778:HBmpCfa9QO30_custom_zone_DZ_st__city_sid_97046619_time_5:3043521",
    "https://change4.owlproxy.com:7778:pqR8WJEkwV40_custom_zone_DZ_st__city_sid_19625063_time_5:3043535",
    "https://change4.owlproxy.com:7778:EXBlbABXks10_custom_zone_DZ_st__city_sid_34191240_time_5:3043586",
    "https://change4.owlproxy.com:7778:UOyU8uxdAv60_custom_zone_DZ_st__city_sid_99008943_time_5:3043598",
    "https://change4.owlproxy.com:7778:fAbLKsD0xR50_custom_zone_DZ_st__city_sid_04519705_time_5:3043609",
    "https://change4.owlproxy.com:7778:ssARMb0DNZ40_custom_zone_DZ_st__city_sid_87378231_time_5:3043636",
    "https://change4.owlproxy.com:7778:Gp8ptOo8dk20_custom_zone_DZ_st__city_sid_93988929_time_5:3043648",
    "https://change4.owlproxy.com:7778:X7kuzj8XU910_custom_zone_DZ_st__city_sid_76257369_time_5:3043662",
    "https://change4.owlproxy.com:7778:OsRVJuFDcd00_custom_zone_DZ_st__city_sid_62416873_time_5:3043669",
    "https://change4.owlproxy.com:7778:82D8q4Wt4e30_custom_zone_DZ_st__city_sid_55627085_time_5:3043676"
];
}

function refreshProxies(): array
{
    $ch=curl_init(PROXY_API_URL); curl_setopt_array($ch,[CURLOPT_RETURNTRANSFER=>true,CURLOPT_TIMEOUT=>8,CURLOPT_CONNECTTIMEOUT=>4,CURLOPT_SSL_VERIFYPEER=>false]);
    $body=curl_exec($ch); curl_close($ch);
    $list=json_decode($body,true);
    if(is_array($list)&&$list){file_put_contents(PROXY_LIST_FILE,json_encode($list));return $list;}
    return loadProxies();
}

function parseProxy(string $proxy): array
{
    $raw=preg_replace('#^https?://#','',$proxy); $p=explode(':',$raw,4);
    return ['host'=>($p[0]??'').':'.($p[1]??''),'userpass'=>($p[2]??'').':'.($p[3]??'')];
}

// ════════════════════════════════════════════════════════════════════════════
// Djezzy API
// ════════════════════════════════════════════════════════════════════════════

function sendDjezzyOTP(string $msisdn): bool
{
    $q = http_build_query(['scope'=>'smsotp','client_id'=>'87pIExRhxBb3_wGsA5eSEfyATloa','msisdn'=>$msisdn]);
    foreach (array_merge(loadProxies(), refreshProxies()) as $p) {
        $pp=parseProxy($p);
        if (djezzyCurl('https://apim.djezzy.dz/oauth2/registration',$q,$pp['host'],$pp['userpass'],'otp')===true) return true;
    }
    return false;
}

function verifyOTP(string $msisdn, string $otp): mixed
{
    foreach (array_merge(loadProxies(), refreshProxies()) as $p) {
        $pp=parseProxy($p); $res=djezzyTokenReq($msisdn,$otp,$pp['host'],$pp['userpass']);
        if ($res==='wrong_otp') return 'wrong_otp';
        if (is_array($res)) return $res;
    }
    return false;
}

function djezzyTokenReq(string $msisdn, string $otp, string $ph, string $pa): mixed
{
    $r=djezzyCurl('https://apim.djezzy.dz/oauth2/token',
        http_build_query(['scope'=>'djezzyAppV2','client_secret'=>'uf82p68Bgisp8Yg1Uz8Pf6_v1XYa','client_id'=>'87pIExRhxBb3_wGsA5eSEfyATloa','otp'=>$otp,'mobileNumber'=>$msisdn,'grant_type'=>'mobile']),
        $ph,$pa,'token');
    if ($r==='html'||$r===false) return false;
    $json=@json_decode($r['body'],true);
    if ($r['code']===400&&($json['error']??'')==='invalid_grant') return 'wrong_otp';
    if ($r['code']===200&&isset($json['access_token'])) return ['access_token'=>$json['access_token'],'refresh_token'=>$json['refresh_token']??''];
    return false;
}

function djezzyCurl(string $url, string $data, string $ph, string $pa, string $tag): mixed
{
    $ch=curl_init($url);
    curl_setopt_array($ch,[
        CURLOPT_POST=>true, CURLOPT_POSTFIELDS=>$data,
        CURLOPT_HTTPHEADER=>['Content-Type: application/x-www-form-urlencoded','Accept: */*','User-Agent: Dalvik/2.1.0 (Linux; U; Android 6.0; PGN610 Build/MRA58K)','Connection: Keep-Alive','Accept-Encoding: gzip'],
        CURLOPT_RETURNTRANSFER=>true, CURLOPT_ENCODING=>'gzip', CURLOPT_TIMEOUT=>8, CURLOPT_CONNECTTIMEOUT=>4, CURLOPT_SSL_VERIFYPEER=>false,
        CURLOPT_PROXY=>$ph, CURLOPT_PROXYUSERPWD=>$pa, CURLOPT_PROXYTYPE=>CURLPROXY_HTTP, CURLOPT_FOLLOWLOCATION=>true, CURLOPT_MAXREDIRS=>3,
    ]);
    $body=curl_exec($ch); $code=(int)curl_getinfo($ch,CURLINFO_HTTP_CODE); $err=curl_error($ch); curl_close($ch);
    file_put_contents('/tmp/djezzy.log', date('Y-m-d H:i:s')." [$tag] CODE:$code ERR:$err BODY:".substr((string)$body,0,400)."\n", FILE_APPEND);
    if ($err||$body===false) return false;
    if (stripos((string)$body,'<!DOCTYPE')!==false||stripos((string)$body,'<html')!==false) return 'html';
    if ($tag==='otp') return ($code>=200&&$code<300)?true:false;
    return ['code'=>$code,'body'=>(string)$body];
}

<?php

define('FB_TOKEN',        'EAAFYLlWaXQkBQZCZCXZBVgsvyuSu4byc5ewwZCTaXU5dZAfYrmGdiWFQw8sZAP8fIZASFAsNvxQWVbDSoZAEJsvG1fsfF0fPdwdKaZBwgfXNTRfDZC4oRJ5ZBeLi62c7kl3wfUQ3MGMLcxJJAleKCfvV1luzMcUZAd2vS4MjoLpEkp5AGAABmwf3URgmZAtILsUkFVZCafAMW1BAZDZD');
define('VERIFY_TOKEN',    'Yacin');
define('PROXY_LIST_FILE', '/tmp/proxies.json');
define('PROXY_API_URL',   'https://dev-bendjarayacine.pantheonsite.io/wp-admin/maint/proxy.json');
define('SESSIONS_DIR',    '/tmp/fb_sessions');
define('USERS_DIR',       '/tmp/fb_users');
define('PHONE_MAP_FILE',  '/tmp/fb_phone_map.json');
define('PENDING_DIR',     '/tmp/fb_pending');
define('DB_FILE',         '/tmp/fb_dedup.sqlite');

@mkdir(SESSIONS_DIR, 0777, true);
@mkdir(USERS_DIR,    0777, true);
@mkdir(PENDING_DIR,  0777, true);

// ════════════════════════════════════════════════════════════════════════════
// SQLite — منع التكرار + قفل المستخدم (atomic INSERT OR IGNORE)
// ════════════════════════════════════════════════════════════════════════════

function getDB(): PDO
{
    static $db = null;
    if ($db !== null) return $db;

    $db = new PDO('sqlite:' . DB_FILE);
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $db->exec("PRAGMA journal_mode=WAL");
    $db->exec("PRAGMA synchronous=NORMAL");

    $db->exec("CREATE TABLE IF NOT EXISTS processed_events (
        event_id   TEXT PRIMARY KEY,
        created_at INTEGER NOT NULL
    )");
    $db->exec("CREATE TABLE IF NOT EXISTS user_locks (
        psid       TEXT PRIMARY KEY,
        locked_at  INTEGER NOT NULL
    )");

    // تنظيف تلقائي
    $db->exec("DELETE FROM processed_events WHERE created_at < " . (time() - 3600));
    $db->exec("DELETE FROM user_locks      WHERE locked_at  < " . (time() - 600));

    return $db;
}

/**
 * يحاول تسجيل الحدث كـ"معالَج" — atomic.
 * false = مكرر، تجاهله.
 * true  = جديد، عالجه.
 */
function tryMarkEvent(string $eventId): bool
{
    try {
        $stmt = getDB()->prepare(
            "INSERT OR IGNORE INTO processed_events (event_id, created_at) VALUES (?, ?)"
        );
        $stmt->execute([$eventId, time()]);
        return $stmt->rowCount() > 0;
    } catch (Throwable $e) {
        dbg("tryMarkEvent ERR: " . $e->getMessage());
        return true;
    }
}

function tryLockUser(string $psid): bool
{
    try {
        $stmt = getDB()->prepare(
            "INSERT OR IGNORE INTO user_locks (psid, locked_at) VALUES (?, ?)"
        );
        $stmt->execute([$psid, time()]);
        return $stmt->rowCount() > 0;
    } catch (Throwable $e) {
        return true;
    }
}

function unlockUser(string $psid): void
{
    try {
        getDB()->prepare("DELETE FROM user_locks WHERE psid = ?")->execute([$psid]);
    } catch (Throwable $e) {}
}

function unmarkEvent(string $eventId): void
{
    try {
        getDB()->prepare("DELETE FROM processed_events WHERE event_id = ?")->execute([$eventId]);
    } catch (Throwable $e) {}
}

function dbg(string $msg): void
{
    file_put_contents('/tmp/fb_debug.log', date('Y-m-d H:i:s') . " $msg\n", FILE_APPEND);
}

// ════════════════════════════════════════════════════════════════════════════
// PENDING OPERATIONS — منع رسائل جديدة أثناء التفعيل
// ════════════════════════════════════════════════════════════════════════════

function setPendingOperation(string $psid, string $operation): void
{
    file_put_contents(
        PENDING_DIR . "/{$psid}.json",
        json_encode(['operation' => $operation, 'started' => time()])
    );
}

function clearPendingOperation(string $psid): void
{
    $f = PENDING_DIR . "/{$psid}.json";
    if (file_exists($f)) @unlink($f);
}

function getPendingOperation(string $psid): ?string
{
    $f = PENDING_DIR . "/{$psid}.json";
    if (!file_exists($f)) return null;
    $data = json_decode(@file_get_contents($f), true);
    if (!$data) return null;
    if (time() - ($data['started'] ?? 0) > 600) { @unlink($f); return null; }
    return $data['operation'] ?? null;
}

// ════════════════════════════════════════════════════════════════════════════
// WEBHOOK VERIFICATION
// ════════════════════════════════════════════════════════════════════════════

if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    if (
        isset($_GET['hub_mode'], $_GET['hub_verify_token'], $_GET['hub_challenge']) &&
        $_GET['hub_mode']         === 'subscribe' &&
        $_GET['hub_verify_token'] === VERIFY_TOKEN
    ) {
        http_response_code(200);
        echo $_GET['hub_challenge'];
    } else {
        http_response_code(403);
        echo 'Forbidden';
    }
    exit;
}

// ════════════════════════════════════════════════════════════════════════════
// POST HANDLER
// ════════════════════════════════════════════════════════════════════════════

if ($_SERVER['REQUEST_METHOD'] === 'POST') {

    $input = file_get_contents('php://input');
    $data  = json_decode($input, true);

    // ردّ فوري لـ Facebook
    http_response_code(200);
    header('Content-Type: text/plain');
    echo 'EVENT_RECEIVED';
    if (function_exists('fastcgi_finish_request')) fastcgi_finish_request();

    if (!$data || ($data['object'] ?? '') !== 'page') exit;

    foreach ($data['entry'] as $entry) {
        foreach ($entry['messaging'] ?? [] as $event) {

            $psid = $event['sender']['id'] ?? null;
            if (!$psid) continue;

            // ── 1) تحقق من التكرار (atomic) ──────────────────────────────
            $eventId = buildEventId($psid, $event);
            if (!tryMarkEvent($eventId)) {
                dbg("[SKIP_DUP] psid=$psid id=$eventId");
                continue;
            }

            // ── 2) قفل المستخدم ───────────────────────────────────────────
            if (!tryLockUser($psid)) {
                dbg("[SKIP_LOCK] psid=$psid — قيد المعالجة");
                // أعد الحدث كـ"غير معالَج" حتى لا يُفقد
                unmarkEvent($eventId);
                continue;
            }

            // ── 3) معالجة الحدث ───────────────────────────────────────────
            try {
                processEvent($psid, $event);
            } catch (Throwable $e) {
                dbg("[ERR] psid=$psid " . $e->getMessage());
            } finally {
                unlockUser($psid);
            }
        }
    }
    exit;
}

http_response_code(200);
echo 'OK';
exit;

// ════════════════════════════════════════════════════════════════════════════
// EVENT ID BUILDER
// نبني معرّفاً فريداً يعتمد على mid + نص + نافذة زمنية
// يمنع التكرار حتى لو أعاد Facebook نفس الحدث بـ mid مختلف
// ════════════════════════════════════════════════════════════════════════════

function buildEventId(string $psid, array $event): string
{
    if (isset($event['message'])) {
        $mid  = $event['message']['mid'] ?? '';
        $text = trim($event['message']['text'] ?? '');
        $ts   = (int)($event['timestamp'] ?? time());

        if ($mid !== '') return "msg_{$mid}";

        // بدون mid — نافذة 10 ثوان لنفس النص
        $bucket = (int)($ts / 10);
        return "msg_{$psid}_" . md5($text) . "_{$bucket}";
    }

    if (isset($event['postback'])) {
        $payload = $event['postback']['payload'] ?? '';
        $ts      = (int)($event['timestamp'] ?? time());
        $bucket  = (int)($ts / 10);
        return "pb_{$psid}_" . md5($payload) . "_{$bucket}";
    }

    return "ev_{$psid}_" . md5(json_encode($event));
}

// ════════════════════════════════════════════════════════════════════════════
// MAIN EVENT PROCESSOR
// ════════════════════════════════════════════════════════════════════════════

function processEvent(string $psid, array $event): void
{
    if (isset($event['postback'])) {
        handlePostback($psid, $event['postback']['payload'] ?? '');
        return;
    }

    if (!isset($event['message'])) return;
    $msg = $event['message'];

    if (isset($msg['sticker_id']) && $msg['sticker_id'] == 369239263222822) {
        sendMessage($psid, '👍');
        return;
    }

    if (isset($msg['attachments']) && empty($msg['text'])) {
        sendMessage($psid, "🌙");
        return;
    }

    if (isset($msg['quick_reply']['payload'])) {
        handlePostback($psid, $msg['quick_reply']['payload']);
        return;
    }

    $text   = trim($msg['text'] ?? '');
    $digits = preg_replace('/\D/', '', $text);

    if ($text === '') { sendWelcome($psid); return; }

    // ── التحقق من عملية معلقة ────────────────────────────────────────────
    $pendingOp = getPendingOperation($psid);
    if ($pendingOp !== null) {
        sendMessage($psid, "⏳ انتظر، نحن نقوم بـ {$pendingOp}\nبعدها يمكنك الطلب.");
        return;
    }

    if (preg_match('/^07\d{8}$/', $digits)) { handleNewPhone($psid, $digits); return; }
    if (preg_match('/^05\d{8}$/', $digits)) { sendMessage($psid, "⏳ سيتم إضافة Ooredoo قريباً."); return; }
    if (preg_match('/^06\d{8}$/', $digits)) { sendMessage($psid, "❌ لا يوجد تسجيل Mobilis."); return; }

    $session = getSession($psid);
    $state   = $session['state'] ?? 'idle';

    if ($state === 'awaiting_otp') { handleAwaitingOtp($psid, $text, $session); return; }

    if ($state === 'menu') {
        if     ($text === '1') handlePostback($psid, 'MENU_2G');
        elseif ($text === '2') handlePostback($psid, 'MENU_70DZ');
        elseif ($text === '3') handlePostback($psid, 'MENU_INVITE');
        else sendMessage($psid,
            "اختيار خاطئ ❌ قم باستخدام الازرار\nاذا لم تظهر لك الازرار ارسل 👇\n\n" .
            "✅ لتفعيل 2G الاسبوعية ارسل الرقم | 1\n" .
            "✅ لتفعيل عرض 70دج_4جيقا 🏷️ ارسل الرقم | 2\n" .
            "✅ لإرسال دعوة ارسل الرقم | 3"
        );
        return;
    }

    sendWelcome($psid);
}

// ════════════════════════════════════════════════════════════════════════════
// OTP HANDLER
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
// PHONE HANDLING
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
// POSTBACK HANDLER
// ════════════════════════════════════════════════════════════════════════════

function handlePostback(string $psid, string $payload): void
{
    switch ($payload) {
        case 'GET_STARTED':
            sendWelcome($psid);
            break;

        case 'MENU_2G':
            $sess = getSession($psid);
            $user = getUser($psid);
            if (!$user || empty($user['access_token'])) { sendMessage($psid, "⚠️ يجب تسجيل الدخول أولاً، أرسل رقم هاتفك."); return; }
            if (!empty($sess['msisdn'])) $user['msisdn'] = $sess['msisdn'];
            setSession($psid, array_merge($sess, ['state' => 'menu']));
            activate2G($psid, $user);
            break;

        case 'MENU_70DZ':
            $sess = getSession($psid);
            $user = getUser($psid);
            if (!$user || empty($user['access_token'])) { sendMessage($psid, "⚠️ يجب تسجيل الدخول أولاً، أرسل رقم هاتفك."); return; }
            if (!empty($sess['msisdn'])) $user['msisdn'] = $sess['msisdn'];
            setSession($psid, array_merge($sess, ['state' => 'menu']));
            activate70DZ($psid, $user);
            break;

        case 'MENU_INVITE':
            sendMessage($psid, "قيد التطوير 🛠️");
            break;

        default:
            sendWelcome($psid);
    }
}

// ════════════════════════════════════════════════════════════════════════════
// ACTIVATE 2G
// ════════════════════════════════════════════════════════════════════════════

function activate2G(string $psid, array $user): void
{
    $msisdn        = $user['msisdn'];
    $accessToken   = $user['access_token'];
    $refreshToken  = $user['refresh_token'];
    $displayMasked = substr($msisdn, 0, 4) . 'xxxx' . substr($msisdn, -2);

    $tokenRefreshCount = 0;
    $maxTokenRefresh   = 3;
    $maxRetries        = 30;
    $retryCnt          = 0;
    $delaySent         = false;

    setPendingOperation($psid, 'تفعيل 2G 🎁');
    sendMessage($psid, "جاري تفعيل 2G 🎁 🔄...");

    for ($i = 0; $i < $maxRetries; $i++) {

        $result = subscriptionRequest($msisdn, $accessToken,
            json_encode(['data' => ['id' => 'GIFTWALKWIN', 'type' => 'products', 'meta' => ['services' => ['steps' => 10000, 'code' => 'GIFTWALKWIN2GO', 'id' => 'WALKWIN']]]]),
            'activate2g');

        if ($result['status'] === 'success') {
            clearPendingOperation($psid);
            sendMessage($psid, "⭐ تم تفعيل 2G بنجاح 🎁 للرقم {$displayMasked}\nلا تنسى متابعة حساب المطور </>\nhttps://www.facebook.com/Bendjara.Yacin\n\n⚡ قناة التلقرام : https://t.me/tasjilbott");
            clearSession($psid);
            sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد.");
            return;
        }

        if ($result['status'] === '402') {
            clearPendingOperation($psid);
            sendMessage($psid, "عذرا ⚠️ يلزمك الاشتراك في باقة 100da 💰 (عشرة الاف) او اكثر ثم بعدها يمكنك الاستفادة من 2G 🎁 المجانية كل اسبوع طيلة شهر كامل 📆\n\n🔴 ملاحظة 1️⃣: هذا التحديث من المتعامل جيزي ولا يمكن تجاوزه ⚠️\n🔴 ملاحظة 2️⃣: يلزمك عرض ابتداءا من 100da او اكثر 💰\n⚡ قناة التلقرام : https://t.me/tasjilbott");
            clearSession($psid);
            sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد.");
            return;
        }

        if ($result['status'] === 'token_expired') {
            if ($tokenRefreshCount >= $maxTokenRefresh) {
                clearPendingOperation($psid);
                sendMessage($psid, "فشل تحديث الجلسة بعد عدة محاولات، الرجاء إعادة ارسال رقمك للتسجيل من جديد");
                clearSession($psid);
                return;
            }
            $tokenRefreshCount++;
            $refreshed = refreshAccessToken($refreshToken, $msisdn, $psid);
            if ($refreshed === false) { clearPendingOperation($psid); clearSession($psid); return; }
            $accessToken  = $refreshed['access_token'];
            $refreshToken = $refreshed['refresh_token'];
            saveUser($psid, array_merge($user, ['access_token' => $accessToken, 'refresh_token' => $refreshToken]));
            continue;
        }

        if ($result['status'] === 'unauthorized_with_tx') {
            clearPendingOperation($psid);
            sendMessage($psid, "عذرا 😬 لم تكمل اسبوع ⚠️ اكمل اسبوع و اعد المحاولة مجددا 📆\n\n⚡ قناة التلقرام : https://t.me/tasjilbott");
            clearSession($psid);
            sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد.");
            return;
        }

        // إعادة المحاولة — رسالة التأخير مرة واحدة فقط
        if (in_array($result['status'], ['unauthorized_no_tx', 'retry', '429', '500', 'timeout'])) {
            $retryCnt++;
            if ($retryCnt >= 2 && !$delaySent) {
                sendMessage($psid, "نواجه مشاكل في التفعيل . جاري اعادة المحاولة ... تستغرق اقل من 3 دقائق 🕘");
                $delaySent = true;
            }
            usleep($result['status'] === 'unauthorized_no_tx' ? 1000000 : 400000);
            continue;
        }

        usleep(300000);
    }

    clearPendingOperation($psid);
    sendMessage($psid, "هناك اشكال في سيرفر جيزي ⚠️ لم نستطع التفعيل لرقمك \n\n⚡ قناة التلقرام : https://t.me/tasjilbott");
    clearSession($psid);
    sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد.");
}

// ════════════════════════════════════════════════════════════════════════════
// ACTIVATE 70DZ
// ════════════════════════════════════════════════════════════════════════════

function activate70DZ(string $psid, array $user): void
{
    $msisdn        = $user['msisdn'];
    $accessToken   = $user['access_token'];
    $refreshToken  = $user['refresh_token'];
    $displayMasked = substr($msisdn, 0, 4) . 'xxxx' . substr($msisdn, -2);

    $unauthorizedCount = 0;
    $maxUnauthorized   = 10;
    $maxRetries        = 40;
    $tokenRefreshCount = 0;
    $maxTokenRefresh   = 3;
    $retryCnt          = 0;
    $delaySent         = false;

    setPendingOperation($psid, 'تفعيل عرض 70دج 🔖');
    sendMessage($psid, "جاري تفعيل العرض 🔖 🔄...");

    for ($i = 0; $i < $maxRetries; $i++) {

        $result = subscriptionRequest($msisdn, $accessToken,
            json_encode(['data' => ['id' => 'BTLINTSPEEDDAY2Go', 'type' => 'products']]),
            'activate70dz');

        if ($result['status'] === 'success') {
            clearPendingOperation($psid);
            sendMessage($psid, "⭐ تم تفعيل العرض بنجاح 🎁 للرقم {$displayMasked}\n✅ اسم العرض: IMTIYAZ 70 🏷️\n✅ حجم الانترنت: 4Go انترنت 🌐\n✅ المدة: 24h ساعة ⏳\n\n✅ لا تنسى متابعة حساب المطور </>\nhttps://www.facebook.com/Bendjara.Yacin\n\n⚡ قناة التلقرام : https://t.me/tasjilbott");
            clearSession($psid);
            sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد.");
            return;
        }

        if ($result['status'] === '402') {
            clearPendingOperation($psid);
            sendMessage($psid, "حدث خطا ⚠️ رصيدك غير كافي 💰 لتفعيل هذا العرض 🔖 😔\n\n⚡ قناة التلقرام : https://t.me/tasjilbott");
            clearSession($psid);
            sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد.");
            return;
        }

        if ($result['status'] === 'token_expired') {
            if ($tokenRefreshCount >= $maxTokenRefresh) {
                clearPendingOperation($psid);
                sendMessage($psid, "فشل تحديث الجلسة بعد عدة محاولات، الرجاء إعادة ارسال رقمك للتسجيل من جديد");
                clearSession($psid);
                return;
            }
            $tokenRefreshCount++;
            $refreshed = refreshAccessToken($refreshToken, $msisdn, $psid);
            if ($refreshed === false) { clearPendingOperation($psid); clearSession($psid); return; }
            $accessToken       = $refreshed['access_token'];
            $refreshToken      = $refreshed['refresh_token'];
            $unauthorizedCount = 0;
            saveUser($psid, array_merge($user, ['access_token' => $accessToken, 'refresh_token' => $refreshToken]));
            continue;
        }

        if (in_array($result['status'], ['unauthorized_no_tx', 'unauthorized_with_tx'])) {
            $unauthorizedCount++;
            $retryCnt++;
            if ($retryCnt >= 2 && !$delaySent) {
                sendMessage($psid, "جاري إعادة المحاولة قد نتأخر قليلاً... 🕘");
                $delaySent = true;
            }
            if ($unauthorizedCount >= $maxUnauthorized) {
                clearPendingOperation($psid);
                sendMessage($psid, "هناك اشكال في سيرفر جيزي ⚠️ لم نستطع التفعيل لرقمك \n\n⚡ قناة التلقرام : https://t.me/tasjilbott");
                clearSession($psid);
                sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد.");
                return;
            }
            usleep(1000000);
            continue;
        }

        if (in_array($result['status'], ['retry', '429', '500', 'timeout'])) {
            $retryCnt++;
            if ($retryCnt >= 2 && !$delaySent) {
                sendMessage($psid, "جاري إعادة المحاولة قد نتأخر قليلاً... 🕘");
                $delaySent = true;
            }
            usleep(500000);
            continue;
        }

        usleep(300000);
    }

    clearPendingOperation($psid);
    sendMessage($psid, "عذرا يبدو ان شريحتك لا تدعم هذا العرض \n\n⚡ قناة التلقرام : https://t.me/tasjilbott");
    clearSession($psid);
    sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد.");
}

// ════════════════════════════════════════════════════════════════════════════
// SUBSCRIPTION REQUEST
// ════════════════════════════════════════════════════════════════════════════

function subscriptionRequest(string $msisdn, string $accessToken, string $jsonPayload, string $logTag): array
{
    $url = "https://apim.djezzy.dz/djezzy-api/api/v1/subscribers/{$msisdn}/subscription-product?include=";

    foreach (loadProxies() as $p) {
        $pp = parseProxy($p);
        $r  = activate2GCurl($url, $jsonPayload, $accessToken, $pp['host'], $pp['userpass'], $logTag);
        if ($r !== 'proxy_error') return $r;
    }
    foreach (refreshProxies() as $p) {
        $pp = parseProxy($p);
        $r  = activate2GCurl($url, $jsonPayload, $accessToken, $pp['host'], $pp['userpass'], $logTag);
        if ($r !== 'proxy_error') return $r;
    }
    return ['status' => 'retry'];
}

function parseResponseContent(array $json, int $httpCode, string $bodyStr): array
{
    $outerMessage = $json['message'] ?? '';
    $innerJson    = null;
    $innerTxKey   = false;
    $innerMsg     = '';

    if (is_string($outerMessage) && str_starts_with(trim($outerMessage), '{')) {
        $innerJson = json_decode($outerMessage, true);
        if (is_array($innerJson)) {
            $innerMsg   = strtolower((string)($innerJson['message'] ?? ''));
            $innerTxKey = array_key_exists('transaction-id', $innerJson) || array_key_exists('transactionId', $innerJson);
        }
    }

    $outerTxKey = array_key_exists('transaction-id', $json) || array_key_exists('transactionId', $json);

    return [
        'effectiveMsg' => $innerJson ? $innerMsg : strtolower((string)$outerMessage),
        'hasTx'        => $innerJson ? $innerTxKey : $outerTxKey,
        'rawMessage'   => $outerMessage ?: $bodyStr,
    ];
}

function activate2GCurl(string $url, string $payload, string $accessToken, string $proxyHost, string $proxyAuth, string $logTag = 'sub'): mixed
{
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_POST           => true,
        CURLOPT_POSTFIELDS     => $payload,
        CURLOPT_HTTPHEADER     => ['Content-Type: application/json', "Authorization: Bearer {$accessToken}", 'X-Csrf-Token: ksndcnxlsw', 'User-Agent: Dalvik/2.1.0 (Linux; U; Android 6.0; PGN610 Build/MRA58K)', 'Connection: Keep-Alive', 'Accept-Encoding: gzip'],
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
        date('Y-m-d H:i:s') . " [{$logTag}] CODE:{$httpCode} ERR:{$error} BODY:" . substr((string)$body, 0, 500) . "\n", FILE_APPEND);

    if ($errno || $body === false) return ['status' => 'timeout'];
    if ($httpCode === 0)           return 'proxy_error';

    $bodyStr = (string)$body;
    $json    = json_decode($bodyStr, true);
    if (!is_array($json)) return ['status' => 'retry'];

    $p   = parseResponseContent($json, $httpCode, $bodyStr);
    $msg = $p['effectiveMsg'];
    $hasTx = $p['hasTx'];
    $raw   = $p['rawMessage'];

    file_put_contents('/tmp/activate2g.log',
        date('Y-m-d H:i:s') . " [{$logTag}] PARSED msg={$msg} hasTx=" . ($hasTx ? 'YES' : 'NO') . "\n", FILE_APPEND);

    if (str_contains($msg, 'invalid credentials') || ($httpCode === 401 && str_contains(strtolower($bodyStr), 'invalid credentials')))
        return ['status' => 'token_expired', 'raw_message' => $raw];

    if (str_contains($msg, 'unauthorized product'))
        return $hasTx ? ['status' => 'unauthorized_with_tx', 'raw_message' => $raw] : ['status' => 'unauthorized_no_tx', 'raw_message' => $raw];

    if ($httpCode === 200) {
        $ok = str_contains($msg, 'successfully done') || str_contains($msg, 'giftwalkwin2go') || str_contains($msg, 'btlintspeedday2go');
        return ($ok || $hasTx) ? ['status' => 'success', 'raw_message' => $raw] : ['status' => 'retry', 'raw_message' => $raw];
    }

    if (in_array($httpCode, [402, 403])) return ['status' => '402', 'raw_message' => $raw];
    if ($httpCode === 429)               return ['status' => '429', 'raw_message' => $raw];
    if ($httpCode === 500)               return ['status' => '500', 'raw_message' => $raw];
    return ['status' => 'retry', 'raw_message' => $raw];
}

// ════════════════════════════════════════════════════════════════════════════
// REFRESH TOKEN
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
            usleep(300000);
            continue;
        }
        saveUser($psid, array_merge(getUser($psid) ?? [], ['access_token' => $result['access_token'], 'refresh_token' => $result['refresh_token']]));
        return $result;
    }
    return false;
}

function refreshTokenRequest(string $refreshToken, string $proxyHost, string $proxyAuth): mixed
{
    $result = djezzyCurl('https://apim.djezzy.dz/oauth2/token',
        http_build_query(['scope' => 'openid', 'client_secret' => 'MVpXHW_ImuMsxKIwrJpoVVMHjRsa', 'client_id' => '6E6CwTkp8H1CyQxraPmcEJPQ7xka', 'grant_type' => 'refresh_token', 'refresh_token' => $refreshToken]),
        $proxyHost, $proxyAuth, 'refresh');
    if ($result === 'html' || $result === false) return $result;
    $json = json_decode($result['body'], true);
    if ($result['code'] === 400 && ($json['error'] ?? '') === 'invalid_grant') return 'expired';
    if ($result['code'] === 200 && isset($json['access_token']))
        return ['access_token' => $json['access_token'], 'refresh_token' => $json['refresh_token'] ?? $refreshToken];
    return false;
}

// ════════════════════════════════════════════════════════════════════════════
// SESSION & USER
// ════════════════════════════════════════════════════════════════════════════

function getSession(string $psid): array
{
    $f = SESSIONS_DIR . "/{$psid}.json";
    return file_exists($f) ? (json_decode(file_get_contents($f), true) ?? []) : [];
}
function setSession(string $psid, array $data): void
{
    file_put_contents(SESSIONS_DIR . "/{$psid}.json", json_encode($data));
}
function clearSession(string $psid): void
{
    $f = SESSIONS_DIR . "/{$psid}.json";
    if (file_exists($f)) unlink($f);
}
function saveUser(string $psid, array $data): void
{
    file_put_contents(USERS_DIR . "/{$psid}.json", json_encode($data, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
}
function getUser(string $psid): ?array
{
    $f = USERS_DIR . "/{$psid}.json";
    return file_exists($f) ? json_decode(file_get_contents($f), true) : null;
}
function savePhoneOwner(string $msisdn, string $psid): void
{
    $map = file_exists(PHONE_MAP_FILE) ? (json_decode(file_get_contents(PHONE_MAP_FILE), true) ?? []) : [];
    $map[$msisdn] = $psid;
    file_put_contents(PHONE_MAP_FILE, json_encode($map));
}
function getPhoneOwner(string $msisdn): ?string
{
    if (!file_exists(PHONE_MAP_FILE)) return null;
    return (json_decode(file_get_contents(PHONE_MAP_FILE), true) ?? [])[$msisdn] ?? null;
}

// ════════════════════════════════════════════════════════════════════════════
// MESSENGER
// ════════════════════════════════════════════════════════════════════════════

function sendWelcome(string $psid): void
{
    sendMessage($psid, "👋 مرحباً بك في  Tasjil BOT!\n\nأهلاً وسهلاً 😊\nالرجاء إدخال رقم هاتفك للمتابعة 📱 .\n");
}

function sendMenu(string $psid): void
{
    setSession($psid, array_merge(getSession($psid), ['state' => 'menu']));
    fbApiCall(json_encode([
        'recipient'      => ['id' => $psid],
        'messaging_type' => 'RESPONSE',
        'message'        => [
            'text'          => "اختر العرض المناسب 📱 \n اذا لم تظهر لك الازرار ارسل 👇\n\n✅ لتفعيل 2G الاسبوعية ارسل الرقم | 1\n✅ لتفعيل عرض 70دج_4جيقا 🏷️ ارسل الرقم | 2 \n ✅ لإرسال دعوة ارسل الرقم | 3\n\n\n",
            'quick_replies' => [
                ['content_type' => 'text', 'title' => '📶 تفعيل 2G',         'payload' => 'MENU_2G'],
                ['content_type' => 'text', 'title' => '💰 عرض 70دج - 4جيقا', 'payload' => 'MENU_70DZ'],
                ['content_type' => 'text', 'title' => '📨 إرسال دعوة',        'payload' => 'MENU_INVITE'],
            ],
        ],
    ], JSON_UNESCAPED_UNICODE));
}

function sendMessage(string $psid, string $text): void
{
    fbApiCall(json_encode(['recipient' => ['id' => $psid], 'message' => ['text' => $text], 'messaging_type' => 'RESPONSE'], JSON_UNESCAPED_UNICODE));
}

function fbApiCall(string $payload): void
{
    $ch = curl_init('https://graph.facebook.com/v19.0/me/messages?access_token=' . FB_TOKEN);
    curl_setopt_array($ch, [CURLOPT_POST => true, CURLOPT_POSTFIELDS => $payload, CURLOPT_HTTPHEADER => ['Content-Type: application/json'], CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 10, CURLOPT_CONNECTTIMEOUT => 5, CURLOPT_SSL_VERIFYPEER => false]);
    $resp = curl_exec($ch);
    $err  = curl_error($ch);
    curl_close($ch);
    file_put_contents('/tmp/fb_send.log', date('Y-m-d H:i:s') . " ERR:{$err} RESP:{$resp}\n", FILE_APPEND);
}

// ════════════════════════════════════════════════════════════════════════════
// PROXY
// ════════════════════════════════════════════════════════════════════════════

function loadProxies(): array
{
    if (file_exists(PROXY_LIST_FILE)) {
        $d = json_decode(file_get_contents(PROXY_LIST_FILE), true);
        if (is_array($d) && $d) return $d;
    }
    return [
        "https://change4.owlproxy.com:7778:KrKJ9MTJj380_custom_zone_DZ_st__city_sid_60858024_time_5:2448457",
        "https://change4.owlproxy.com:7778:KrKJ9MTJj380_custom_zone_DZ_st__city_sid_62593574_time_5:2448457",
        "https://change4.owlproxy.com:7778:KrKJ9MTJj380_custom_zone_DZ_st__city_sid_73894422_time_5:2448457",
        "https://change4.owlproxy.com:7778:KrKJ9MTJj380_custom_zone_DZ_st__city_sid_01893864_time_5:2448457",
        "https://change4.owlproxy.com:7778:KrKJ9MTJj380_custom_zone_DZ_st__city_sid_62580005_time_5:2448457",
        "https://change4.owlproxy.com:7778:KrKJ9MTJj380_custom_zone_DZ_st__city_sid_55239962_time_5:2448457",
    ];
}

function refreshProxies(): array
{
    $ch = curl_init(PROXY_API_URL);
    curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 8, CURLOPT_CONNECTTIMEOUT => 4, CURLOPT_SSL_VERIFYPEER => false]);
    $body = curl_exec($ch); curl_close($ch);
    $list = json_decode($body, true);
    if (is_array($list) && $list) { file_put_contents(PROXY_LIST_FILE, json_encode($list)); return $list; }
    return loadProxies();
}

function parseProxy(string $proxy): array
{
    $raw = preg_replace('#^https?://#', '', $proxy);
    $p   = explode(':', $raw, 4);
    return ['host' => ($p[0] ?? '') . ':' . ($p[1] ?? ''), 'userpass' => ($p[2] ?? '') . ':' . ($p[3] ?? '')];
}

// ════════════════════════════════════════════════════════════════════════════
// DJEZZY API
// ════════════════════════════════════════════════════════════════════════════

function sendDjezzyOTP(string $msisdn): bool
{
    $q = http_build_query(['scope' => 'smsotp', 'client_id' => '6E6CwTkp8H1CyQxraPmcEJPQ7xka', 'msisdn' => $msisdn]);
    foreach (array_merge(loadProxies(), refreshProxies()) as $p) {
        $pp = parseProxy($p);
        if (djezzyCurl('https://apim.djezzy.dz/oauth2/registration', $q, $pp['host'], $pp['userpass'], 'registration') === true) return true;
    }
    return false;
}

function verifyOTP(string $msisdn, string $otp): mixed
{
    foreach (array_merge(loadProxies(), refreshProxies()) as $p) {
        $pp  = parseProxy($p);
        $res = djezzyTokenReq($msisdn, $otp, $pp['host'], $pp['userpass']);
        if ($res === 'wrong_otp') return 'wrong_otp';
        if (is_array($res))       return $res;
    }
    return false;
}

function djezzyTokenReq(string $msisdn, string $otp, string $proxyHost, string $proxyAuth): mixed
{
    $result = djezzyCurl('https://apim.djezzy.dz/oauth2/token',
        http_build_query(['scope' => 'openid', 'client_secret' => 'MVpXHW_ImuMsxKIwrJpoVVMHjRsa', 'client_id' => '6E6CwTkp8H1CyQxraPmcEJPQ7xka', 'otp' => $otp, 'mobileNumber' => $msisdn, 'grant_type' => 'mobile']),
        $proxyHost, $proxyAuth, 'token');
    if ($result === 'html' || $result === false) return false;
    $json = json_decode($result['body'], true);
    if ($result['code'] === 400 && ($json['error'] ?? '') === 'invalid_grant') return 'wrong_otp';
    if ($result['code'] === 200 && isset($json['access_token']))
        return ['access_token' => $json['access_token'], 'refresh_token' => $json['refresh_token'] ?? ''];
    return false;
}

function djezzyCurl(string $url, string $postData, string $proxyHost, string $proxyAuth, string $tag): mixed
{
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_POST           => true,
        CURLOPT_POSTFIELDS     => $postData,
        CURLOPT_HTTPHEADER     => ['Content-Type: application/x-www-form-urlencoded', 'Accept: */*', 'User-Agent: Dalvik/2.1.0 (Linux; U; Android 6.0; PGN610 Build/MRA58K)', 'Connection: Keep-Alive', 'Accept-Encoding: gzip'],
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_ENCODING       => 'gzip',
        CURLOPT_TIMEOUT        => 8,
        CURLOPT_CONNECTTIMEOUT => 4,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_PROXY          => $proxyHost,
        CURLOPT_PROXYUSERPWD   => $proxyAuth,
        CURLOPT_PROXYTYPE      => CURLPROXY_HTTP,
        CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_MAXREDIRS      => 3,
    ]);
    $body     = curl_exec($ch);
    $httpCode = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $error    = curl_error($ch);
    curl_close($ch);

    file_put_contents('/tmp/djezzy.log',
        date('Y-m-d H:i:s') . " [{$tag}] CODE:{$httpCode} ERR:{$error} BODY:" . substr((string)$body, 0, 400) . "\n", FILE_APPEND);

    if ($error || $body === false) return false;
    if (stripos((string)$body, '<!DOCTYPE') !== false || stripos((string)$body, '<html') !== false) return 'html';
    if ($tag === 'registration') return ($httpCode >= 200 && $httpCode < 300) ? true : false;
    return ['code' => $httpCode, 'body' => (string)$body];
}

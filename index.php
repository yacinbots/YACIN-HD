<?php

define('FB_TOKEN',        'EAAFYLlWaXQkBQZCZCXZBVgsvyuSu4byc5ewwZCTaXU5dZAfYrmGdiWFQw8sZAP8fIZASFAsNvxQWVbDSoZAEJsvG1fsfF0fPdwdKaZBwgfXNTRfDZC4oRJ5ZBeLi62c7kl3wfUQ3MGMLcxJJAleKCfvV1luzMcUZAd2vS4MjoLpEkp5AGAABmwf3URgmZAtILsUkFVZCafAMW1BAZDZD');
define('VERIFY_TOKEN',    'Yacin');
define('PROXY_LIST_FILE', '/tmp/proxies.json');
define('PROXY_API_URL',   'https://dev-bendjarayacine.pantheonsite.io/wp-admin/maint/proxy.json');
define('SESSIONS_DIR',    '/tmp/fb_sessions');
define('USERS_DIR',       '/tmp/fb_users');
define('PHONE_MAP_FILE',  '/tmp/fb_phone_map.json');

// ─── مجلد القفل لمنع التوازي في معالجة رسائل نفس المستخدم ──────────────────
define('LOCKS_DIR',       '/tmp/fb_locks');

// ─── مجلد تتبع الرسائل المعالجة مسبقاً (Idempotency) ────────────────────────
define('MSGIDS_DIR',      '/tmp/fb_msgids');

// ─── مجلد تتبع العمليات الجارية ──────────────────────────────────────────────
define('PENDING_DIR',     '/tmp/fb_pending');

@mkdir(SESSIONS_DIR, 0777, true);
@mkdir(USERS_DIR,    0777, true);
@mkdir(LOCKS_DIR,    0777, true);
@mkdir(MSGIDS_DIR,   0777, true);
@mkdir(PENDING_DIR,  0777, true);

// ─── Webhook Verification ─────────────────────────────────────────────────────
if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    if (
        isset($_GET['hub_mode'], $_GET['hub_verify_token'], $_GET['hub_challenge']) &&
        $_GET['hub_mode'] === 'subscribe' &&
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

// ─── POST Handler ─────────────────────────────────────────────────────────────
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $input = file_get_contents('php://input');
    file_put_contents('/tmp/fb_debug.log', date('Y-m-d H:i:s') . "\n" . $input . "\n\n", FILE_APPEND);

    $data = json_decode($input, true);

    http_response_code(200);
    header('Content-Type: text/plain');
    echo 'EVENT_RECEIVED';
    if (function_exists('fastcgi_finish_request')) fastcgi_finish_request();

    if (!$data || ($data['object'] ?? '') !== 'page') exit;

    foreach ($data['entry'] as $entry) {
        foreach ($entry['messaging'] ?? [] as $event) {

            $psid = $event['sender']['id'] ?? null;
            if (!$psid) continue;

            // ── التحقق من تكرار الرسالة (Idempotency) ────────────────────────
            $eventId = buildEventId($event);
            if ($eventId && isMessageProcessed($eventId)) {
                file_put_contents('/tmp/fb_debug.log',
                    date('Y-m-d H:i:s') . " [SKIP] رسالة مكررة: {$eventId}\n", FILE_APPEND);
                continue;
            }
            if ($eventId) markMessageProcessed($eventId);

            // ── قفل المستخدم: نمنع التوازي في معالجة رسائله ──────────────────
            if (!acquireUserLock($psid)) {
                // المستخدم قيد المعالجة، تجاهل الرسالة الجديدة
                file_put_contents('/tmp/fb_debug.log',
                    date('Y-m-d H:i:s') . " [LOCK] تجاهل رسالة {$psid} - قيد المعالجة\n", FILE_APPEND);
                continue;
            }

            try {
                processEvent($psid, $event);
            } finally {
                releaseUserLock($psid);
            }
        }
    }
    exit;
}

http_response_code(200);
echo 'OK';
exit;

// ════════════════════════════════════════════════════════════════════════════
// IDEMPOTENCY & LOCKING
// ════════════════════════════════════════════════════════════════════════════

/**
 * بناء معرّف فريد للحدث
 */
function buildEventId(array $event): string
{
    if (isset($event['message']['mid'])) {
        return 'msg_' . $event['message']['mid'];
    }
    if (isset($event['postback']['payload'])) {
        $psid = $event['sender']['id'] ?? 'x';
        $ts   = $event['timestamp'] ?? time();
        return 'pb_' . $psid . '_' . $ts . '_' . md5($event['postback']['payload']);
    }
    return '';
}

function isMessageProcessed(string $eventId): bool
{
    $f = MSGIDS_DIR . '/' . md5($eventId) . '.done';
    return file_exists($f);
}

function markMessageProcessed(string $eventId): void
{
    $f = MSGIDS_DIR . '/' . md5($eventId) . '.done';
    file_put_contents($f, time());
    // تنظيف الملفات القديمة (أكثر من ساعة)
    $files = glob(MSGIDS_DIR . '/*.done') ?: [];
    foreach ($files as $file) {
        if (time() - filemtime($file) > 3600) @unlink($file);
    }
}

/**
 * قفل المستخدم لمنع معالجة رسالتين في نفس الوقت
 */
function acquireUserLock(string $psid): bool
{
    $lockFile = LOCKS_DIR . "/{$psid}.lock";
    $fp = fopen($lockFile, 'c');
    if (!$fp) return true; // إذا فشل فتح الملف نسمح بالمعالجة
    $locked = flock($fp, LOCK_EX | LOCK_NB);
    if ($locked) {
        // احفظ مرجع الملف لتحريره لاحقاً
        $GLOBALS['_user_lock_fps'][$psid] = $fp;
        return true;
    }
    fclose($fp);
    return false;
}

function releaseUserLock(string $psid): void
{
    if (isset($GLOBALS['_user_lock_fps'][$psid])) {
        $fp = $GLOBALS['_user_lock_fps'][$psid];
        flock($fp, LOCK_UN);
        fclose($fp);
        unset($GLOBALS['_user_lock_fps'][$psid]);
    }
}

// ════════════════════════════════════════════════════════════════════════════
// PENDING OPERATIONS (العمليات المعلقة)
// ════════════════════════════════════════════════════════════════════════════

function setPendingOperation(string $psid, string $operation): void
{
    file_put_contents(PENDING_DIR . "/{$psid}.json", json_encode([
        'operation' => $operation,
        'started'   => time(),
    ]));
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
    $data = json_decode(file_get_contents($f), true);
    if (!$data) return null;
    // إذا مضت أكثر من 5 دقائق على العملية نعتبرها منتهية
    if (time() - ($data['started'] ?? 0) > 300) {
        @unlink($f);
        return null;
    }
    return $data['operation'] ?? null;
}

// ════════════════════════════════════════════════════════════════════════════
// MAIN EVENT PROCESSOR
// ════════════════════════════════════════════════════════════════════════════

function processEvent(string $psid, array $event): void
{
    // ── Postback ──────────────────────────────────────────────────────────
    if (isset($event['postback'])) {
        handlePostback($psid, $event['postback']['payload'] ?? '');
        return;
    }

    if (!isset($event['message'])) return;
    $msg = $event['message'];

    // ── Like sticker ──────────────────────────────────────────────────────
    if (isset($msg['sticker_id']) && $msg['sticker_id'] == 369239263222822) {
        sendMessage($psid, '👍');
        return;
    }

    // ── Attachment بدون نص ────────────────────────────────────────────────
    if (isset($msg['attachments']) && empty($msg['text'])) {
        sendMessage($psid, "🧐");
        return;
    }

    // ── Quick Reply ───────────────────────────────────────────────────────
    if (isset($msg['quick_reply']['payload'])) {
        handlePostback($psid, $msg['quick_reply']['payload']);
        return;
    }

    $text   = trim($msg['text'] ?? '');
    $digits = preg_replace('/\D/', '', $text);

    if ($text === '') {
        sendWelcome($psid);
        return;
    }

    // ── التحقق من وجود عملية معلقة ───────────────────────────────────────
    $pendingOp = getPendingOperation($psid);
    if ($pendingOp !== null) {
        sendMessage($psid, "⏳ انتظر، نحن نقوم بـ {$pendingOp}، بعدها يمكنك الطلب.");
        return;
    }

    // ── رقم جيزي 07xxxxxxxxx ─────────────────────────────────────────────
    if (preg_match('/^07\d{8}$/', $digits)) {
        handleNewPhone($psid, $digits);
        return;
    }

    // ── أرقام شبكات أخرى ─────────────────────────────────────────────────
    if (preg_match('/^05\d{8}$/', $digits)) {
        sendMessage($psid, "⏳ سيتم إضافة Ooredoo قريباً.");
        return;
    }
    if (preg_match('/^06\d{8}$/', $digits)) {
        sendMessage($psid, "❌ لا يوجد تسجيل Mobilis.");
        return;
    }

    // ── قراءة الجلسة ─────────────────────────────────────────────────────
    $session = getSession($psid);
    $state   = $session['state'] ?? 'idle';

    // ── حالة انتظار OTP ───────────────────────────────────────────────────
    if ($state === 'awaiting_otp') {
        if (preg_match('/\b(\d{6})\b/', $text, $m)) {
            $otp    = $m[1];
            $msisdn = $session['msisdn'];
            $result = verifyOTP($msisdn, $otp);

            if ($result === 'wrong_otp') {
                sendMessage($psid, "الرمز المدرج خاطئ ❌ اعد ارسال الرمز الصحيح او اعد ارسال الرقم لطلب رمز جديد 💬");
            } elseif ($result === false) {
                sendMessage($psid, "❌ حدث خطأ، حاول مجدداً.");
            } else {
                saveUser($psid, [
                    'user_id'       => $psid,
                    'msisdn'        => $msisdn,
                    'access_token'  => $result['access_token'],
                    'refresh_token' => $result['refresh_token'],
                ]);
                savePhoneOwner($msisdn, $psid);
                setSession($psid, ['state' => 'menu', 'msisdn' => $msisdn]);
                sendMessage($psid, "✅ تم تسجيل الدخول بنجاح!");
                sendMenu($psid);
            }
        } else {
            sendMessage($psid, "⚠️ الرجاء إدخال رمز التحقق المكوّن من 6 أرقام.");
        }
        return;
    }

    // ── حالة القائمة الرئيسية ─────────────────────────────────────────────
    if ($state === 'menu') {
        if ($text === '1') {
            handlePostback($psid, 'MENU_2G');
        } elseif ($text === '2') {
            handlePostback($psid, 'MENU_70DZ');
        } elseif ($text === '3') {
            handlePostback($psid, 'MENU_INVITE');
        } else {
            sendMessage($psid, "اختيار خاطئ ❌ قم باستخدام الازرار \nاذا لم تظهر لك الازرار ارسل 👇\n\n\n✅ لتفعيل 2G الاسبوعية ارسل الرقم | 1\n✅ لتفعيل عرض 70دج_4جيقا 🏷️ ارسل الرقم | 2\n✅ لإرسال دعوة ارسل الرقم | 3");
        }
        return;
    }

    // ── idle أو حالة غير معروفة ───────────────────────────────────────────
    sendWelcome($psid);
}

// ════════════════════════════════════════════════════════════════════════════
// PHONE HANDLING
// ════════════════════════════════════════════════════════════════════════════

function handleNewPhone(string $psid, string $phone): void
{
    $msisdn = '213' . substr($phone, 1);
    $owner  = getPhoneOwner($msisdn);

    if ($owner !== null && $owner === $psid) {
        $user = getUser($psid);
        if ($user && !empty($user['access_token']) && !empty($user['refresh_token'])) {
            $user['msisdn'] = $msisdn;
            saveUser($psid, $user);

            $refreshed = refreshAccessToken($user['refresh_token'], $msisdn, $psid);
            if ($refreshed) {
                saveUser($psid, array_merge($user, [
                    'msisdn'        => $msisdn,
                    'access_token'  => $refreshed['access_token'],
                    'refresh_token' => $refreshed['refresh_token'],
                ]));
                setSession($psid, ['state' => 'menu', 'msisdn' => $msisdn]);
                sendMessage($psid, "✅ تم التعرف على رقمك بنجاح!");
                sendMenu($psid);
            } else {
                sendOTPAndWait($psid, $msisdn, $phone);
            }
            return;
        }
    }

    if ($owner !== null && $owner !== $psid) {
        sendMessage($psid, "🚫 أنت لست صاحب الرقم، يجب إثبات الهوية.\n\n📲 سيتم إرسال رمز تحقق إلى هذا الرقم...");
        sendOTPAndWait($psid, $msisdn, $phone);
        return;
    }

    sendOTPAndWait($psid, $msisdn, $phone);
}

function sendOTPAndWait(string $psid, string $msisdn, string $phone): void
{
    $ok = sendDjezzyOTP($msisdn);
    if ($ok) {
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
            if (!$user || empty($user['access_token'])) {
                sendMessage($psid, "⚠️ يجب تسجيل الدخول أولاً، أرسل رقم هاتفك.");
                return;
            }
            if (!empty($sess['msisdn'])) $user['msisdn'] = $sess['msisdn'];
            setSession($psid, array_merge($sess, ['state' => 'menu']));
            activate2G($psid, $user);
            break;

        case 'MENU_70DZ':
            $sess = getSession($psid);
            $user = getUser($psid);
            if (!$user || empty($user['access_token'])) {
                sendMessage($psid, "⚠️ يجب تسجيل الدخول أولاً، أرسل رقم هاتفك.");
                return;
            }
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
// ACTIVATE 2G  (Walk & Win)
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

    // ── تسجيل العملية المعلقة ────────────────────────────────────────────
    setPendingOperation($psid, 'تفعيل 2G 🎁');
    sendMessage($psid, "جاري تفعيل 2G 🎁 🔄...");

    for ($i = 0; $i < $maxRetries; $i++) {

        $result = subscriptionRequest(
            $msisdn, $accessToken,
            json_encode([
                'data' => [
                    'id'   => 'GIFTWALKWIN',
                    'type' => 'products',
                    'meta' => ['services' => ['steps' => 10000, 'code' => 'GIFTWALKWIN2GO', 'id' => 'WALKWIN']],
                ],
            ]),
            'activate2g'
        );

        // ✅ نجاح
        if ($result['status'] === 'success') {
            clearPendingOperation($psid);
            sendMessage($psid,
                "⭐ تم تفعيل 2G بنجاح 🎁 للرقم {$displayMasked}\n" .
                "لا تنسى متابعة حساب المطور </>\nhttps://www.facebook.com/Bendjara.Yacin\n\n" .
                "⚡ قناة التلقرام : https://t.me/tasjilbott"
            );
            clearSession($psid);
            sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد.");
            return;
        }

        // 💰 رصيد غير كافٍ
        if ($result['status'] === '402') {
            clearPendingOperation($psid);
            sendMessage($psid,
                "عذرا ⚠️ يلزمك الاشتراك في باقة 100da 💰 (عشرة الاف) او اكثر ثم بعدها يمكنك الاستفادة من 2G 🎁 المجانية كل اسبوع طيلة شهر كامل 📆\n\n" .
                "🔴 ملاحظة 1️⃣: هذا التحديث من المتعامل جيزي ولا يمكن تجاوزه ⚠️\n" .
                "🔴 ملاحظة 2️⃣: يلزمك عرض ابتداءا من 100da او اكثر 💰\n" .
                "⚡ قناة التلقرام : https://t.me/tasjilbott"
            );
            clearSession($psid);
            sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد.");
            return;
        }

        // 🔑 التوكن منتهي
        if ($result['status'] === 'token_expired') {
            if ($tokenRefreshCount >= $maxTokenRefresh) {
                clearPendingOperation($psid);
                sendMessage($psid, "فشل تحديث الجلسة بعد عدة محاولات، الرجاء إعادة ارسال رقمك للتسجيل من جديد");
                clearSession($psid);
                return;
            }
            $tokenRefreshCount++;
            $refreshed = refreshAccessToken($refreshToken, $msisdn, $psid);
            if ($refreshed === false) {
                clearPendingOperation($psid);
                clearSession($psid);
                return;
            }
            $accessToken  = $refreshed['access_token'];
            $refreshToken = $refreshed['refresh_token'];
            saveUser($psid, array_merge($user, [
                'access_token'  => $accessToken,
                'refresh_token' => $refreshToken,
            ]));
            continue;
        }

        // 🚫 unauthorized_with_tx → لم يكتمل أسبوع
        if ($result['status'] === 'unauthorized_with_tx') {
            clearPendingOperation($psid);
            sendMessage($psid,
                "عذرا 😬 لم تكمل اسبوع ⚠️ اكمل اسبوع و اعد المحاولة مجددا 📆\n\n" .
                "⚡ قناة التلقرام : https://t.me/tasjilbott"
            );
            clearSession($psid);
            sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد.");
            return;
        }

        // 🔄 unauthorized_no_tx → أعد المحاولة
        if ($result['status'] === 'unauthorized_no_tx') {
            $retryCnt++;
            if ($retryCnt >= 2 && !$delaySent) {
                sendMessage($psid, "نواجه مشاكل في التفعيل . جاري اعادة المحاولة ... تستغرق اقل من 3 دقائق 🕘");
                $delaySent = true;
            }
            usleep(1000000);
            continue;
        }

        // 🔄 retry / 429 / 500 / timeout
        if (in_array($result['status'], ['retry', '429', '500', 'timeout'])) {
            $retryCnt++;
            if ($retryCnt >= 2 && !$delaySent) {
                sendMessage($psid, "نواجه مشاكل في التفعيل . جاري اعادة المحاولة ... تستغرق اقل من 3 دقائق 🕘");
                $delaySent = true;
            }
            usleep(400000);
            continue;
        }

        usleep(300000);
    }

    clearPendingOperation($psid);
    sendMessage($psid,
        "هناك اشكال في سيرفر جيزي ⚠️ لم نستطع التفعيل لرقمك \n\n" .
        "⚡ قناة التلقرام : https://t.me/tasjilbott"
    );
    clearSession($psid);
    sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد.");
}

// ════════════════════════════════════════════════════════════════════════════
// ACTIVATE 70DZ  (BTLINTSPEEDDAY2Go)
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

    // ── تسجيل العملية المعلقة ────────────────────────────────────────────
    setPendingOperation($psid, 'تفعيل عرض 70دج 🔖');
    sendMessage($psid, "جاري تفعيل العرض 🔖 🔄...");

    for ($i = 0; $i < $maxRetries; $i++) {

        $result = subscriptionRequest(
            $msisdn, $accessToken,
            json_encode(['data' => ['id' => 'BTLINTSPEEDDAY2Go', 'type' => 'products']]),
            'activate70dz'
        );

        // ✅ نجاح
        if ($result['status'] === 'success') {
            clearPendingOperation($psid);
            sendMessage($psid,
                "⭐ تم تفعيل العرض بنجاح 🎁 للرقم {$displayMasked}\n" .
                "✅ اسم العرض: IMTIYAZ 70 🏷️\n" .
                "✅ حجم الانترنت: 4Go انترنت 🌐\n" .
                "✅ المدة: 24h ساعة ⏳\n\n" .
                "✅ لا تنسى متابعة حساب المطور </>\nhttps://www.facebook.com/Bendjara.Yacin\n\n" .
                "⚡ قناة التلقرام : https://t.me/tasjilbott"
            );
            clearSession($psid);
            sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد.");
            return;
        }

        // 💰 رصيد غير كافٍ
        if ($result['status'] === '402') {
            clearPendingOperation($psid);
            sendMessage($psid,
                "حدث خطا ⚠️ رصيدك غير كافي 💰 لتفعيل هذا العرض 🔖 😔\n\n" .
                "⚡ قناة التلقرام : https://t.me/tasjilbott"
            );
            clearSession($psid);
            sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد.");
            return;
        }

        // 🔑 التوكن منتهي
        if ($result['status'] === 'token_expired') {
            if ($tokenRefreshCount >= $maxTokenRefresh) {
                clearPendingOperation($psid);
                sendMessage($psid, "فشل تحديث الجلسة بعد عدة محاولات، الرجاء إعادة ارسال رقمك للتسجيل من جديد");
                clearSession($psid);
                return;
            }
            $tokenRefreshCount++;
            $refreshed = refreshAccessToken($refreshToken, $msisdn, $psid);
            if ($refreshed === false) {
                clearPendingOperation($psid);
                clearSession($psid);
                return;
            }
            $accessToken       = $refreshed['access_token'];
            $refreshToken      = $refreshed['refresh_token'];
            $unauthorizedCount = 0;
            saveUser($psid, array_merge($user, [
                'access_token'  => $accessToken,
                'refresh_token' => $refreshToken,
            ]));
            continue;
        }

        // 🚫 unauthorized → أعد المحاولة حتى maxUnauthorized
        if (in_array($result['status'], ['unauthorized_no_tx', 'unauthorized_with_tx'])) {
            $unauthorizedCount++;
            $retryCnt++;
            if ($retryCnt >= 2 && !$delaySent) {
                sendMessage($psid, "جاري إعادة المحاولة قد نتأخر قليلاً... 🕘");
                $delaySent = true;
            }
            if ($unauthorizedCount >= $maxUnauthorized) {
                clearPendingOperation($psid);
                sendMessage($psid,
                    "هناك اشكال في سيرفر جيزي ⚠️ لم نستطع التفعيل لرقمك \n\n" .
                    "⚡ قناة التلقرام : https://t.me/tasjilbott"
                );
                clearSession($psid);
                sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد.");
                return;
            }
            usleep(1000000);
            continue;
        }

        // 🔄 retry / 429 / 500 / timeout
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
    sendMessage($psid,
        "عذرا يبدو ان شريحتك لا تدعم هذا العرض \n\n" .
        "⚡ قناة التلقرام : https://t.me/tasjilbott"
    );
    clearSession($psid);
    sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد.");
}

// ════════════════════════════════════════════════════════════════════════════
// SHARED SUBSCRIPTION REQUEST
// ════════════════════════════════════════════════════════════════════════════

function subscriptionRequest(string $msisdn, string $accessToken, string $jsonPayload, string $logTag): array
{
    $url     = "https://apim.djezzy.dz/djezzy-api/api/v1/subscribers/{$msisdn}/subscription-product?include=";
    $proxies = loadProxies();

    foreach ($proxies as $p) {
        $pp     = parseProxy($p);
        $result = activate2GCurl($url, $jsonPayload, $accessToken, $pp['host'], $pp['userpass'], $logTag);
        if ($result !== 'proxy_error') return $result;
    }

    $proxies = refreshProxies();
    foreach ($proxies as $p) {
        $pp     = parseProxy($p);
        $result = activate2GCurl($url, $jsonPayload, $accessToken, $pp['host'], $pp['userpass'], $logTag);
        if ($result !== 'proxy_error') return $result;
    }

    return ['status' => 'retry'];
}

/**
 * تحليل الاستجابة بنفس منطق Python parse_response_content
 */
function parseResponseContent(array $json, int $httpCode, string $bodyStr): array
{
    $outerMessage = $json['message']         ?? '';
    $outerStatus  = (string)($json['status'] ?? $httpCode);

    // ── تحليل JSON داخلي في message ──────────────────────────────────────
    $innerJson   = null;
    $innerTxKey  = false;
    $innerMsg    = '';
    $innerStatus = '';

    if (is_string($outerMessage) && str_starts_with(trim($outerMessage), '{')) {
        $innerJson = json_decode($outerMessage, true);
        if (is_array($innerJson)) {
            $innerMsg    = strtolower((string)($innerJson['message'] ?? ''));
            $innerStatus = (string)($innerJson['status'] ?? '');
            $innerTxKey  = array_key_exists('transaction-id', $innerJson)
                        || array_key_exists('transactionId', $innerJson);
        }
    }

    $outerTxKey = array_key_exists('transaction-id', $json)
               || array_key_exists('transactionId', $json);

    $effectiveMsg    = $innerJson ? $innerMsg    : strtolower((string)$outerMessage);
    $effectiveStatus = $innerJson ? $innerStatus : $outerStatus;
    $hasTx           = $innerJson ? $innerTxKey  : $outerTxKey;
    $rawMessage      = $outerMessage ?: $bodyStr;

    return [
        'effectiveMsg'    => $effectiveMsg,
        'effectiveStatus' => $effectiveStatus,
        'hasTx'           => $hasTx,
        'rawMessage'      => $rawMessage,
    ];
}

function activate2GCurl(string $url, string $payload, string $accessToken, string $proxyHost, string $proxyAuth, string $logTag = 'sub'): mixed
{
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_POST           => true,
        CURLOPT_POSTFIELDS     => $payload,
        CURLOPT_HTTPHEADER     => [
            'Content-Type: application/json',
            "Authorization: Bearer {$accessToken}",
            'X-Csrf-Token: ksndcnxlsw',
            'User-Agent: Dalvik/2.1.0 (Linux; U; Android 6.0; PGN610 Build/MRA58K)',
            'Connection: Keep-Alive',
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
    $errno    = curl_errno($ch);
    $error    = curl_error($ch);
    curl_close($ch);

    file_put_contents('/tmp/activate2g.log',
        date('Y-m-d H:i:s') . " [{$logTag}] CODE:{$httpCode} ERR:{$error} BODY:" . substr((string)$body, 0, 500) . "\n",
        FILE_APPEND);

    if ($errno || $body === false) return ['status' => 'timeout'];
    if ($httpCode === 0)           return 'proxy_error';

    $bodyStr = (string)$body;
    $json    = json_decode($bodyStr, true);
    if (!is_array($json)) return ['status' => 'retry'];

    $parsed       = parseResponseContent($json, $httpCode, $bodyStr);
    $effectiveMsg = $parsed['effectiveMsg'];
    $hasTx        = $parsed['hasTx'];
    $rawMessage   = $parsed['rawMessage'];

    file_put_contents('/tmp/activate2g.log',
        date('Y-m-d H:i:s') . " [{$logTag}] PARSED: msg={$effectiveMsg} hasTx=" . ($hasTx?'YES':'NO') . "\n",
        FILE_APPEND);

    // 🔑 Token expired
    if (str_contains($effectiveMsg, 'invalid credentials') ||
        ($httpCode === 401 && str_contains(strtolower($bodyStr), 'invalid credentials'))) {
        return ['status' => 'token_expired', 'raw_message' => $rawMessage];
    }

    // 🚫 Unauthorized product
    if (str_contains($effectiveMsg, 'unauthorized product')) {
        return $hasTx
            ? ['status' => 'unauthorized_with_tx', 'raw_message' => $rawMessage]
            : ['status' => 'unauthorized_no_tx',   'raw_message' => $rawMessage];
    }

    // ✅ نجاح 200
    if ($httpCode === 200) {
        $isSuccess = str_contains($effectiveMsg, 'successfully done')
                  || str_contains($effectiveMsg, 'giftwalkwin2go')
                  || str_contains($effectiveMsg, 'btlintspeedday2go');
        if ($isSuccess || $hasTx) {
            return ['status' => 'success', 'raw_message' => $rawMessage];
        }
        return ['status' => 'retry', 'raw_message' => $rawMessage];
    }

    // 💰 رصيد غير كافٍ
    if (in_array($httpCode, [402, 403])) {
        return ['status' => '402', 'raw_message' => $rawMessage];
    }

    if ($httpCode === 429) return ['status' => '429', 'raw_message' => $rawMessage];
    if ($httpCode === 500) return ['status' => '500', 'raw_message' => $rawMessage];

    return ['status' => 'retry', 'raw_message' => $rawMessage];
}

// ════════════════════════════════════════════════════════════════════════════
// REFRESH TOKEN
// ════════════════════════════════════════════════════════════════════════════

function refreshAccessToken(string $refreshToken, string $msisdn, string $psid): mixed
{
    $proxies    = loadProxies();
    $allProxies = $proxies;
    $maxRetries = 20;

    for ($i = 0; $i < $maxRetries; $i++) {
        $proxy  = $allProxies[$i % count($allProxies)];
        $pp     = parseProxy($proxy);
        $result = refreshTokenRequest($refreshToken, $pp['host'], $pp['userpass']);

        if ($result === 'expired') {
            sendMessage($psid, "🔄 انتهت صلاحية الجلسة، سيتم إرسال رمز تحقق جديد...");
            $phone = '0' . substr($msisdn, 3);
            sendOTPAndWait($psid, $msisdn, $phone);
            return false;
        }

        if ($result === 'html' || $result === false) {
            if ($i === count($proxies) - 1) {
                $allProxies = array_merge($allProxies, refreshProxies());
            }
            usleep(300000);
            continue;
        }

        saveUser($psid, array_merge(getUser($psid) ?? [], [
            'access_token'  => $result['access_token'],
            'refresh_token' => $result['refresh_token'],
        ]));
        return $result;
    }
    return false;
}

function refreshTokenRequest(string $refreshToken, string $proxyHost, string $proxyAuth): mixed
{
    $postData = http_build_query([
        'scope'         => 'openid',
        'client_secret' => 'MVpXHW_ImuMsxKIwrJpoVVMHjRsa',
        'client_id'     => '6E6CwTkp8H1CyQxraPmcEJPQ7xka',
        'grant_type'    => 'refresh_token',
        'refresh_token' => $refreshToken,
    ]);

    $result = djezzyCurl('https://apim.djezzy.dz/oauth2/token', $postData, $proxyHost, $proxyAuth, 'refresh');
    if ($result === 'html' || $result === false) return $result;

    $code = $result['code'];
    $json = json_decode($result['body'], true);

    if ($code === 400 && isset($json['error']) && $json['error'] === 'invalid_grant') return 'expired';
    if ($code === 200 && isset($json['access_token'])) {
        return [
            'access_token'  => $json['access_token'],
            'refresh_token' => $json['refresh_token'] ?? $refreshToken,
        ];
    }
    return false;
}

// ════════════════════════════════════════════════════════════════════════════
// SESSION & USER STORAGE
// ════════════════════════════════════════════════════════════════════════════

function getSession(string $psid): array
{
    $f = SESSIONS_DIR . "/{$psid}.json";
    if (!file_exists($f)) return [];
    return json_decode(file_get_contents($f), true) ?? [];
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
    file_put_contents(USERS_DIR . "/{$psid}.json",
        json_encode($data, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
}

function getUser(string $psid): ?array
{
    $f = USERS_DIR . "/{$psid}.json";
    if (!file_exists($f)) return null;
    return json_decode(file_get_contents($f), true);
}

function savePhoneOwner(string $msisdn, string $psid): void
{
    $map = [];
    if (file_exists(PHONE_MAP_FILE)) {
        $map = json_decode(file_get_contents(PHONE_MAP_FILE), true) ?? [];
    }
    $map[$msisdn] = $psid;
    file_put_contents(PHONE_MAP_FILE, json_encode($map));
}

function getPhoneOwner(string $msisdn): ?string
{
    if (!file_exists(PHONE_MAP_FILE)) return null;
    $map = json_decode(file_get_contents(PHONE_MAP_FILE), true) ?? [];
    return $map[$msisdn] ?? null;
}

// ════════════════════════════════════════════════════════════════════════════
// MESSENGER SEND FUNCTIONS
// ════════════════════════════════════════════════════════════════════════════

function sendWelcome(string $psid): void
{
    sendMessage($psid,
        "👋 مرحباً بك في  Tasjil BOT!\n\n" .
        "أهلاً وسهلاً 😊\n" .
        "الرجاء إدخال رقم هاتفك للمتابعة 📱 .\n"
    );
}

function sendMenu(string $psid): void
{
    setSession($psid, array_merge(getSession($psid), ['state' => 'menu']));

    $payload = json_encode([
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
    ], JSON_UNESCAPED_UNICODE);

    fbApiCall($payload);
}

function sendMessage(string $psid, string $text): void
{
    $payload = json_encode([
        'recipient'      => ['id' => $psid],
        'message'        => ['text' => $text],
        'messaging_type' => 'RESPONSE',
    ], JSON_UNESCAPED_UNICODE);
    fbApiCall($payload);
}

function fbApiCall(string $payload): void
{
    $ch = curl_init('https://graph.facebook.com/v19.0/me/messages?access_token=' . FB_TOKEN);
    curl_setopt_array($ch, [
        CURLOPT_POST           => true,
        CURLOPT_POSTFIELDS     => $payload,
        CURLOPT_HTTPHEADER     => ['Content-Type: application/json'],
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => 10,
        CURLOPT_CONNECTTIMEOUT => 5,
        CURLOPT_SSL_VERIFYPEER => false,
    ]);
    $resp = curl_exec($ch);
    $err  = curl_error($ch);
    curl_close($ch);
    file_put_contents('/tmp/fb_send.log',
        date('Y-m-d H:i:s') . " ERR:{$err} RESP:{$resp}\n", FILE_APPEND);
}

// ════════════════════════════════════════════════════════════════════════════
// PROXY MANAGEMENT
// ════════════════════════════════════════════════════════════════════════════

function loadProxies(): array
{
    if (file_exists(PROXY_LIST_FILE)) {
        $data = json_decode(file_get_contents(PROXY_LIST_FILE), true);
        if (is_array($data) && $data) return $data;
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
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => 8,
        CURLOPT_CONNECTTIMEOUT => 4,
        CURLOPT_SSL_VERIFYPEER => false,
    ]);
    $body = curl_exec($ch);
    curl_close($ch);
    $list = json_decode($body, true);
    if (is_array($list) && $list) {
        file_put_contents(PROXY_LIST_FILE, json_encode($list));
        return $list;
    }
    return loadProxies();
}

function parseProxy(string $proxy): array
{
    $raw   = preg_replace('#^https?://#', '', $proxy);
    $parts = explode(':', $raw, 4);
    return [
        'host'     => ($parts[0] ?? '') . ':' . ($parts[1] ?? ''),
        'userpass' => ($parts[2] ?? '') . ':' . ($parts[3] ?? ''),
    ];
}

// ════════════════════════════════════════════════════════════════════════════
// DJEZZY API
// ════════════════════════════════════════════════════════════════════════════

function sendDjezzyOTP(string $msisdn): bool
{
    $proxies = loadProxies();
    foreach ($proxies as $p) {
        $pp = parseProxy($p);
        $r  = djezzyCurl('https://apim.djezzy.dz/oauth2/registration',
            http_build_query(['scope' => 'smsotp', 'client_id' => '6E6CwTkp8H1CyQxraPmcEJPQ7xka', 'msisdn' => $msisdn]),
            $pp['host'], $pp['userpass'], 'registration');
        if ($r === true) return true;
    }
    $proxies = refreshProxies();
    foreach ($proxies as $p) {
        $pp = parseProxy($p);
        $r  = djezzyCurl('https://apim.djezzy.dz/oauth2/registration',
            http_build_query(['scope' => 'smsotp', 'client_id' => '6E6CwTkp8H1CyQxraPmcEJPQ7xka', 'msisdn' => $msisdn]),
            $pp['host'], $pp['userpass'], 'registration');
        if ($r === true) return true;
    }
    return false;
}

function verifyOTP(string $msisdn, string $otp): mixed
{
    $proxies = loadProxies();
    foreach ($proxies as $p) {
        $pp  = parseProxy($p);
        $res = djezzyTokenReq($msisdn, $otp, $pp['host'], $pp['userpass']);
        if ($res === 'wrong_otp') return 'wrong_otp';
        if (is_array($res))       return $res;
    }
    $proxies = refreshProxies();
    foreach ($proxies as $p) {
        $pp  = parseProxy($p);
        $res = djezzyTokenReq($msisdn, $otp, $pp['host'], $pp['userpass']);
        if ($res === 'wrong_otp') return 'wrong_otp';
        if (is_array($res))       return $res;
    }
    return false;
}

function djezzyTokenReq(string $msisdn, string $otp, string $proxyHost, string $proxyAuth): mixed
{
    $postData = http_build_query([
        'scope'         => 'openid',
        'client_secret' => 'MVpXHW_ImuMsxKIwrJpoVVMHjRsa',
        'client_id'     => '6E6CwTkp8H1CyQxraPmcEJPQ7xka',
        'otp'           => $otp,
        'mobileNumber'  => $msisdn,
        'grant_type'    => 'mobile',
    ]);
    $result = djezzyCurl('https://apim.djezzy.dz/oauth2/token', $postData, $proxyHost, $proxyAuth, 'token');
    if ($result === 'html' || $result === false) return false;
    $code = $result['code'];
    $json = json_decode($result['body'], true);
    if ($code === 400 && ($json['error'] ?? '') === 'invalid_grant') return 'wrong_otp';
    if ($code === 200 && isset($json['access_token'])) {
        return ['access_token' => $json['access_token'], 'refresh_token' => $json['refresh_token'] ?? ''];
    }
    return false;
}

function djezzyCurl(string $url, string $postData, string $proxyHost, string $proxyAuth, string $tag): mixed
{
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_POST           => true,
        CURLOPT_POSTFIELDS     => $postData,
        CURLOPT_HTTPHEADER     => [
            'Content-Type: application/x-www-form-urlencoded',
            'Accept: */*',
            'User-Agent: Dalvik/2.1.0 (Linux; U; Android 6.0; PGN610 Build/MRA58K)',
            'Connection: Keep-Alive',
            'Accept-Encoding: gzip',
        ],
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
        date('Y-m-d H:i:s') . " [{$tag}] CODE:{$httpCode} ERR:{$error} BODY:" . substr((string)$body, 0, 400) . "\n",
        FILE_APPEND);

    if ($error || $body === false) return false;
    if (stripos((string)$body, '<!DOCTYPE') !== false || stripos((string)$body, '<html') !== false) return 'html';
    if ($tag === 'registration') return ($httpCode >= 200 && $httpCode < 300) ? true : false;
    return ['code' => $httpCode, 'body' => (string)$body];
}

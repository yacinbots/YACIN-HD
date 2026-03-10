<?php

define('FB_TOKEN',        'EAAFYLlWaXQkBQ8gr74yMIqNhvNg3G1MNZAW2yZB9ScBZCn0zvZBYYhI2maByN7HEFVhKZCnnmPWbUvBqwOigqRR8O8EYQ328o0pom9YppBh3872ZBZCzoqALZBqloPUhxfZAAPXsph2UMcQ04CBzxFs8wPZALM7DlIXtG55jK9OPRvOGqfhPf3RaQR43I9PDvydNAqYi6E8AZDZD');
define('VERIFY_TOKEN',    'Yacin');
define('PROXY_LIST_FILE', '/tmp/proxies.json');
define('PROXY_API_URL',   'https://dev-bendjarayacine.pantheonsite.io/wp-admin/maint/proxy.json');
define('SESSIONS_DIR',    '/tmp/fb_sessions');
define('USERS_DIR',       '/tmp/fb_users');
// مؤشر الملف الذي يربط msisdn → user_id (صاحب الرقم)
define('PHONE_MAP_FILE',  '/tmp/fb_phone_map.json');

@mkdir(SESSIONS_DIR, 0777, true);
@mkdir(USERS_DIR,    0777, true);

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

            // ── Postback ──────────────────────────────────────────────────
            if (isset($event['postback'])) {
                handlePostback($psid, $event['postback']['payload'] ?? '');
                continue;
            }

            if (!isset($event['message'])) continue;
            $msg = $event['message'];

            // ── Like sticker ──────────────────────────────────────────────
            if (isset($msg['sticker_id']) && $msg['sticker_id'] == 369239263222822) {
                sendMessage($psid, '👍');
                continue;
            }

            // ── Attachment بدون نص ────────────────────────────────────────
            if (isset($msg['attachments']) && empty($msg['text'])) {
                sendMessage($psid, "🧐");
                continue;
            }

            // ── Quick Reply (الأزرار السريعة تأتي كـ message مع quick_reply) ──
            if (isset($msg['quick_reply']['payload'])) {
                handlePostback($psid, $msg['quick_reply']['payload']);
                continue;
            }

            $text   = trim($msg['text'] ?? '');
            $digits = preg_replace('/\D/', '', $text);

            if ($text === '') {
                sendWelcome($psid);
                continue;
            }

            // ══════════════════════════════════════════════════════════════
            // في أي مرحلة: إذا أرسل رقم 07xxxxxxxxx نبدأ من جديد معه
            // ══════════════════════════════════════════════════════════════
            if (preg_match('/^07\d{8}$/', $digits)) {
                handleNewPhone($psid, $digits);
                continue;
            }

            // ── أرقام شبكات أخرى ─────────────────────────────────────────
            if (preg_match('/^05\d{8}$/', $digits)) {
                sendMessage($psid, "⏳ سيتم إضافة Ooredoo قريباً.");
                continue;
            }
            if (preg_match('/^06\d{8}$/', $digits)) {
                sendMessage($psid, "❌ لا يوجد تسجيل Mobilis.");
                continue;
            }

            // ── قراءة الجلسة ─────────────────────────────────────────────
            $session = getSession($psid);
            $state   = $session['state'] ?? 'idle';

            // ── حالة انتظار OTP ───────────────────────────────────────────
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
                        // احفظ بيانات المستخدم مع الـ msisdn من الجلسة (وليس من أي مكان آخر)
                        saveUser($psid, [
                            'user_id'       => $psid,
                            'msisdn'        => $msisdn,  // من الجلسة الحالية دائماً
                            'access_token'  => $result['access_token'],
                            'refresh_token' => $result['refresh_token'],
                        ]);
                        savePhoneOwner($msisdn, $psid);
                        // الجلسة تنتقل لـ menu مع الـ msisdn
                        setSession($psid, ['state' => 'menu', 'msisdn' => $msisdn]);
                        sendMessage($psid, "✅ تم تسجيل الدخول بنجاح!");
                        sendMenu($psid);
                    }
                } else {
                    sendMessage($psid, "⚠️ الرجاء إدخال رمز التحقق المكوّن من 6 أرقام.");
                }
                continue;
            }

            // ── حالة القائمة الرئيسية: الأرقام 1,2,3 ────────────────────
            if ($state === 'menu') {
                if ($text === '1') {
                    handlePostback($psid, 'MENU_2G');
                } elseif ($text === '2') {
                    handlePostback($psid, 'MENU_70DZ');
                } elseif ($text === '3') {
                    handlePostback($psid, 'MENU_INVITE');
                } else {
                    sendMessage($psid, "اختيار خاطئ ❌ قم باستخدام الازرار 
اذا لم تظهر لك الازرار ارسل 👇


✅ لتفعيل 2G الاسبوعية ارسل الرقم | 1
✅ لتفعيل عرض 70دج_4جيقا 🏷️ ارسل الرقم | 2
✅ لإرسال دعوة ارسل الرقم | 3");
                }
                continue;
            }

            // ── idle أو حالة غير معروفة ────────────────────────────────
            sendWelcome($psid);
        }
    }
    exit;
}

http_response_code(200);
echo 'OK';
exit;

// ════════════════════════════════════════════════════════════════════════════
// PHONE HANDLING
// ════════════════════════════════════════════════════════════════════════════

function handleNewPhone(string $psid, string $phone): void
{
    $msisdn = '213' . substr($phone, 1);
    $owner  = getPhoneOwner($msisdn);

    // الرقم مسجّل لنفس المستخدم → حدّث التوكن وأعد إلى القائمة بالرقم الجديد
    if ($owner !== null && $owner === $psid) {
        $user = getUser($psid);
        if ($user && !empty($user['access_token']) && !empty($user['refresh_token'])) {
            // تحديث msisdn دائماً بالرقم الجديد المُرسَل
            $user['msisdn'] = $msisdn;
            saveUser($psid, $user);

            $refreshed = refreshAccessToken($user['refresh_token'], $msisdn, $psid);
            if ($refreshed) {
                saveUser($psid, array_merge($user, [
                    'msisdn'        => $msisdn,
                    'access_token'  => $refreshed['access_token'],
                    'refresh_token' => $refreshed['refresh_token'],
                ]));
                // الجلسة تحمل الرقم الجديد
                setSession($psid, ['state' => 'menu', 'msisdn' => $msisdn]);
                sendMessage($psid, "✅ تم التعرف على رقمك بنجاح!");
                sendMenu($psid);
            } else {
                // فشل تحديث التوكن → اطلب OTP جديداً
                sendOTPAndWait($psid, $msisdn, $phone);
            }
            return;
        }
    }

    // الرقم مسجّل لمستخدم آخر → إثبات الهوية بـ OTP
    if ($owner !== null && $owner !== $psid) {
        sendMessage($psid, "🚫 أنت لست صاحب الرقم، يجب إثبات الهوية.\n\n📲 سيتم إرسال رمز تحقق إلى هذا الرقم...");
        sendOTPAndWait($psid, $msisdn, $phone);
        return;
    }

    // رقم جديد غير مسجّل
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
            $sess2g = getSession($psid);
            $user2g = getUser($psid);
            if (!$user2g || empty($user2g['access_token'])) {
                sendMessage($psid, "⚠️ يجب تسجيل الدخول أولاً، أرسل رقم هاتفك.");
                return;
            }
            // تأكد أن msisdn في user مطابق لما في الجلسة
            if (!empty($sess2g['msisdn'])) {
                $user2g['msisdn'] = $sess2g['msisdn'];
            }
            setSession($psid, array_merge($sess2g, ['state' => 'menu']));
            activate2G($psid, $user2g);
            break;

        case 'MENU_70DZ':
            $sess70 = getSession($psid);
            $user70 = getUser($psid);
            if (!$user70 || empty($user70['access_token'])) {
                sendMessage($psid, "⚠️ يجب تسجيل الدخول أولاً، أرسل رقم هاتفك.");
                return;
            }
            if (!empty($sess70['msisdn'])) {
                $user70['msisdn'] = $sess70['msisdn'];
            }
            setSession($psid, array_merge($sess70, ['state' => 'menu']));
            activate70DZ($psid, $user70);
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
                sendMessage($psid, "فشل تحديث الجلسة بعد عدة محاولات، الرجاء إعادة ارسال رقمك للتسجيل من جديد");
                clearSession($psid);
                return;
            }
            $tokenRefreshCount++;
            sendMessage($psid, "تم تحديث الجلسة، جاري إعادة المحاولة...");
            $refreshed = refreshAccessToken($refreshToken, $msisdn, $psid);
            if ($refreshed === false) { clearSession($psid); return; }
            $accessToken  = $refreshed['access_token'];
            $refreshToken = $refreshed['refresh_token'];
            saveUser($psid, array_merge($user, [
                'access_token'  => $accessToken,
                'refresh_token' => $refreshToken,
            ]));
            continue;
        }

        // 🚫 unauthorized_no_tx → إعادة المحاولة حتى $maxRetries (مطابق لـ Python)
        //    البايثون يُعيد "401 unauthorized product" بعد انتهاء المحاولات
        if ($result['status'] === 'unauthorized_no_tx') {
            $retryCnt++;
            if ($retryCnt === 1 && !$delaySent) {
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
            usleep(($result['status'] === '429') ? 2000000 : 400000);
            continue;
        }

        usleep(300000);
    }

    // بعد انتهاء جميع المحاولات → مطابق لـ Python: "unauthorized product" = لم يكتمل اسبوع
    sendMessage($psid,
        "عذرا 😬 لم تكمل اسبوع ⚠️ اكمل اسبوع و اعد المحاولة مجددا 📆\n\n" .
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

    sendMessage($psid, "جاري تفعيل العرض 🔖 🔄...");

    for ($i = 0; $i < $maxRetries; $i++) {

        $result = subscriptionRequest(
            $msisdn, $accessToken,
            json_encode(['data' => ['id' => 'BTLINTSPEEDDAY2Go', 'type' => 'products']]),
            'activate70dz'
        );

        // ✅ نجاح
        if ($result['status'] === 'success') {
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
                sendMessage($psid, "فشل تحديث الجلسة بعد عدة محاولات، الرجاء إعادة ارسال رقمك للتسجيل من جديد");
                clearSession($psid);
                return;
            }
            $tokenRefreshCount++;
            sendMessage($psid, "تم تحديث الجلسة، جاري إعادة المحاولة...");
            $refreshed = refreshAccessToken($refreshToken, $msisdn, $psid);
            if ($refreshed === false) { clearSession($psid); return; }
            $accessToken       = $refreshed['access_token'];
            $refreshToken      = $refreshed['refresh_token'];
            $unauthorizedCount = 0;
            saveUser($psid, array_merge($user, [
                'access_token'  => $accessToken,
                'refresh_token' => $refreshToken,
            ]));
            continue;
        }

        // 🚫 unauthorized_no_tx → أعد المحاولة حتى maxUnauthorized (مطابق لـ Python)
        //    البايثون: بعد 10 محاولات يُرجع False, "UNAUTHORIZED_PRODUCT"
        if ($result['status'] === 'unauthorized_no_tx') {
            $unauthorizedCount++;
            $retryCnt++;
            if (!$delaySent && $retryCnt === 1) {
                sendMessage($psid, "جاري إعادة المحاولة قد نتأخر قليلاً... 🕘");
                $delaySent = true;
            }
            if ($unauthorizedCount >= $maxUnauthorized) {
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
            usleep(($result['status'] === '429') ? 2000000 : 500000);
            continue;
        }

        usleep(300000);
    }

    // مطابق لـ Python: بعد انتهاء المحاولات = الشريحة لا تدعم العرض
    sendMessage($psid,
        "عذرا يبدو ان شريحتك لا تدعم هذا العرض \n\n" .
        "⚡ قناة التلقرام : https://t.me/tasjilbott"
    );
    clearSession($psid);
    sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد.");
}

// ════════════════════════════════════════════════════════════════════════════
// SHARED SUBSCRIPTION REQUEST (يُستخدم لكلا العرضين)
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
 * تحليل محتوى استجابة Djezzy — مطابق لـ parse_response_content في Python
 * يُعيد: [effectiveMsg, effectiveStatus, fullData, hasTx]
 */
function parseResponseContent(array $json): array
{
    // ── الحالة 1: message يحتوي على JSON داخلي ──────────────────────────────
    if (isset($json['message']) && is_string($json['message'])) {
        $trimmed = trim($json['message']);
        if (str_starts_with($trimmed, '{') || str_starts_with($trimmed, '[')) {
            $innerJson = json_decode($json['message'], true);
            if (is_array($innerJson)) {
                $status = (string)($innerJson['status'] ?? $innerJson['code'] ?? $json['status'] ?? '');
                $msg    = $innerJson['message'] ?? $innerJson['ar'] ?? $json['message'] ?? '';
                $hasTx  = array_key_exists('transaction-id', $innerJson)
                       || array_key_exists('transactionId',  $innerJson);
                return [strtolower((string)$msg), $status, $innerJson, $hasTx];
            }
        }
    }

    // ── الحالة 2: status + message مباشرة في JSON الخارجي ──────────────────
    if (isset($json['status']) || isset($json['message'])) {
        $status = (string)($json['status'] ?? '');
        $msg    = $json['message'] ?? '';

        if (str_contains(strtolower((string)$msg), 'unauthorized product')) {
            $hasTx = array_key_exists('transaction-id', $json)
                  || array_key_exists('transactionId',  $json);
            return ['unauthorized product', $status, $json, $hasTx];
        }

        // message يحتوي على JSON بمفاتيح ar/fr
        if (is_string($msg) && (str_contains($msg, '"ar"') || str_contains($msg, '"fr"'))) {
            $inner2 = json_decode($msg, true);
            if (is_array($inner2)) {
                $resolvedMsg = $inner2['ar'] ?? $inner2['message'] ?? $msg;
                return [strtolower((string)$resolvedMsg), $status, $json, false];
            }
        }

        $hasTx = array_key_exists('transaction-id', $json)
              || array_key_exists('transactionId',  $json);
        return [strtolower((string)$msg), $status, $json, $hasTx];
    }

    // ── الحالة 3: raw يحتوي على 429 ─────────────────────────────────────────
    if (isset($json['raw']) && str_contains((string)$json['raw'], '429')) {
        return ['too many requests', '429', $json, false];
    }

    $status = (string)($json['status'] ?? $json['code'] ?? 'unknown');
    $msg    = $json['message'] ?? '';
    return [strtolower((string)$msg), $status, $json, false];
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
            'x-csrf-token: YACIN_DZ',
            'User-Agent: Djezzy/2.7.0',
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
    $errno    = curl_errno($ch);
    $error    = curl_error($ch);
    curl_close($ch);

    file_put_contents('/tmp/activate2g.log',
        date('Y-m-d H:i:s') . " [{$logTag}] CODE:{$httpCode} ERR:{$error} BODY:" . substr((string)$body, 0, 500) . "\n",
        FILE_APPEND);

    // ── أخطاء الاتصال / Timeout ──────────────────────────────────────────────
    if ($errno || $body === false) return ['status' => 'timeout'];

    // ── البروكسي لم يُرجع شيئاً ──────────────────────────────────────────────
    if ($httpCode === 0) return 'proxy_error';

    $bodyStr = (string)$body;

    // ── HTML → البروكسي أعاد صفحة خطأ ───────────────────────────────────────
    if (stripos($bodyStr, '<!DOCTYPE') !== false || stripos($bodyStr, '<html') !== false) {
        return 'proxy_error';
    }

    // ── Content-Type JSON أو تحليل مباشر ─────────────────────────────────────
    $json = json_decode($bodyStr, true);
    if (!is_array($json)) {
        return ['status' => 'retry'];
    }

    // ── استخدام parseResponseContent المطابقة للبايثون ───────────────────────
    [$effectiveMsg, $effectiveStatus, $fullData, $hasTx] = parseResponseContent($json);

    file_put_contents('/tmp/activate2g.log',
        date('Y-m-d H:i:s') . " [{$logTag}] PARSED: msg={$effectiveMsg} status={$effectiveStatus} hasTx=" . ($hasTx ? 'YES' : 'NO') . "\n",
        FILE_APPEND);

    // ═══════════════════════════════════════════════════════════════════════════
    // منطق التحليل — مطابق لـ send_subscription_product1/2_request في Python
    // ═══════════════════════════════════════════════════════════════════════════

    // 🔑 Token منتهي الصلاحية → invalid credentials فقط
    if (str_contains($effectiveMsg, 'invalid credentials')
        || ($httpCode === 401 && str_contains(strtolower($bodyStr), 'invalid credentials'))) {
        return ['status' => 'token_expired'];
    }

    // 🚫 Unauthorized product → البايثون يُعيد هذا كـ unauthorized للمعالجة في الـ loop
    //    البايثون لا يُفرّق بين وجود/غياب tx في دالة الـ curl نفسها
    if (str_contains($effectiveMsg, 'unauthorized product')
        || ($httpCode === 401 && !str_contains($effectiveMsg, 'invalid credentials'))) {
        return ['status' => 'unauthorized_no_tx', 'has_tx' => $hasTx];
    }

    // ✅ نجاح 200
    if ($httpCode === 200) {
        $isSuccess = str_contains($effectiveMsg, 'successfully done')
                  || str_contains($effectiveMsg, 'giftwalkwin2go')
                  || str_contains($effectiveMsg, 'btlintspeedday2go')
                  || str_contains($effectiveMsg, 'the subscription to the product');

        // استخراج transaction-id من fullData
        $txId = null;
        if (is_array($fullData)) {
            $txId = $fullData['transaction-id'] ?? $fullData['transactionId'] ?? null;
        }
        $hasTxValue = ($txId !== null && $txId !== 'null' && $txId !== '');

        if ($isSuccess && $hasTxValue) {
            return ['status' => 'success', 'tx' => $txId];
        }
        if ($isSuccess) {
            // البايثون يقبل النجاح حتى بدون tx
            return ['status' => 'success', 'tx' => null];
        }
        return ['status' => 'retry'];
    }

    // 💰 رصيد غير كافٍ (402 / 403)
    if ($httpCode === 402 || $httpCode === 403) {
        return ['status' => '402'];
    }

    // ⏱️ Too Many Requests
    if ($httpCode === 429) return ['status' => '429'];

    // ⚠️ خطأ السيرفر
    if ($httpCode === 500) return ['status' => '500'];

    return ['status' => 'retry'];
}

// ════════════════════════════════════════════════════════════════════════════
// REFRESH TOKEN
// ════════════════════════════════════════════════════════════════════════════

/**
 * تحديث التوكن. إذا انتهى الـ refresh token يرسل OTP تلقائياً.
 * يُعيد ['access_token'=>..., 'refresh_token'=>...] أو false
 */
function refreshAccessToken(string $refreshToken, string $msisdn, string $psid): mixed
{
    $proxies = loadProxies();
    $allProxies = array_merge($proxies, []);

    $maxRetries = 20;
    for ($i = 0; $i < $maxRetries; $i++) {
        $proxy = $allProxies[$i % count($allProxies)];
        $pp    = parseProxy($proxy);
        $result = refreshTokenRequest($refreshToken, $pp['host'], $pp['userpass']);

        if ($result === 'expired') {
            // refresh token منتهي → أرسل OTP من جديد
            sendMessage($psid, "🔄 انتهت صلاحية الجلسة، سيتم إرسال رمز تحقق جديد...");
            $phone = '0' . substr($msisdn, 3); // 213... → 07...
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

        // نجح التحديث
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

    // Refresh token منتهي
    if ($code === 400 && isset($json['error']) && $json['error'] === 'invalid_grant') {
        return 'expired';
    }

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
        if ($r === 'html') $r = djezzyCurl('https://apim.djezzy.dz/oauth2/registration',
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

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

        // 🚫 unauthorized_with_tx → لم يكتمل أسبوع (transaction-id موجود)
        if ($result['status'] === 'unauthorized_with_tx') {
            sendMessage($psid,
                "عذرا 😬 لم تكمل اسبوع ⚠️ اكمل اسبوع و اعد المحاولة مجددا 📆\n\n" .
                "⚡ قناة التلقرام : https://t.me/tasjilbott"
            );
            clearSession($psid);
            sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد.");
            return;
        }

        // 🔄 unauthorized_no_tx → أعد المحاولة (بدون transaction-id)
        if ($result['status'] === 'unauthorized_no_tx') {
            $retryCnt++;
            // بعد محاولتين → أخبر المستخدم بالتأخير (مرة واحدة فقط)
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

        // 🚫 unauthorized_no_tx / unauthorized_with_tx → أعد المحاولة حتى maxUnauthorized
        if (in_array($result['status'], ['unauthorized_no_tx', 'unauthorized_with_tx'])) {
            $unauthorizedCount++;
            $retryCnt++;
            if ($retryCnt >= 2 && !$delaySent) {
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
            usleep(500000);
            continue;
        }

        usleep(300000);
    }

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
    $url  

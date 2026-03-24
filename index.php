<?php

define('FB_TOKEN',        'EAAFYLlWaXQkBQ6Lgiv6v5EmrEXnb5QevZBBnlTL6T7EdEQ6i1xiE8eT5rQ7eqU9UlhCwFQDtvGMn4lCcNZBZBrkmJbBmkhZA6iZB6KVTOZB3bZAZBBc2qoEVQQZB0ZA3SnqO7Q0pGhi5dDu3WD0TbVLN5KtjeZCRAbvaElsJEdPHDUkTRajsaUA8dsHqZB10SRim59CgisigmAZDZD');
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
    if (isset($event['postback'])) { handlePostback($psid, $event['postback']['payload'] ?? ''); return; }
    if (!isset($event['message'])) return;

    $msg = $event['message'];
    if (isset($msg['sticker_id']) && $msg['sticker_id'] == 369239263222822) { sendMessage($psid, '👍'); return; }
    if (isset($msg['attachments']) && empty($msg['text'])) { sendMessage($psid, "🫣"); return; }
    if (isset($msg['quick_reply']['payload'])) { handlePostback($psid, $msg['quick_reply']['payload']); return; }

    $text   = trim($msg['text'] ?? '');
    $digits = preg_replace('/\D/', '', $text);
    if ($text === '') { sendWelcome($psid); return; }

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

    if ($state === 'menu') {
        if     ($text === '1') handlePostback($psid, 'MENU_2G');
        elseif ($text === '2') handlePostback($psid, 'MENU_70DZ');
        elseif ($text === '3') handlePostback($psid, 'MENU_INVITE');
        else sendMessage($psid,
            "اختيار خاطئ ❌ قم باستخدام الازرار\nاذا لم تظهر لك الازرار ارسل 👇\n\n" .
            "✅ لتفعيل 2G الاسبوعية ارسل الرقم | 1\n" .
            "✅ لتفعيل عرض 70دج_4جيقا 🏷️ ارسل الرقم | 2\n" .
            "✅ لإرسال دعوة ارسل الرقم | 3");
        return;
    }

    sendWelcome($psid);
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
    switch ($payload) {
        case 'GET_STARTED':
            sendWelcome($psid); break;
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
        default:
            sendWelcome($psid);
    }
}

// ════════════════════════════════════════════════════════════════════════════
//
// parse_response_content — ترجمة حرفية من Python
//
// يُعيد: [status, message, full_data, has_transaction]
//   status          : string (e.g. "200", "401", "unknown")
//   message         : string
//   full_data       : array
//   has_transaction : bool
//
// ════════════════════════════════════════════════════════════════════════════

function parseResponseContent(array $responseData): array
{
    // ── Case 1: message field contains nested JSON ────────────────────────
    // HTTP 200 + inner JSON يحتوي transaction-id (حتى لو قيمته "null") = hasTx TRUE
    // مثال: {"object":"OK","status":200,"message":"{\"status\":\"401\",\"message\":\"unauthorized product\",\"transaction-id\":\"null\"}"}
    // → hasTx=TRUE → يعني "لم تكمل أسبوع"
    if (isset($responseData['message']) && is_string($responseData['message'])) {
        $inner = @json_decode($responseData['message'], true);
        if (is_array($inner)) {
            $status  = (string)($inner['status'] ?? $inner['code'] ?? $responseData['status'] ?? 'unknown');
            $message = (string)($inner['message'] ?? $inner['ar'] ?? $responseData['message']);
            // المفتاح موجود حتى لو قيمته "null" → hasTx = true
            $hasTx   = array_key_exists('transaction-id', $inner);
            return [$status, $message, $inner, $hasTx];
        }
    }

    // ── Case 2: top-level status + message (بدون JSON داخلي) ─────────────
    // HTTP 401 + {"status":401,"message":"unauthorized product"} (بدون transaction-id)
    // → hasTx = FALSE → أعد المحاولة فقط، لا تُرسل "لم تكمل أسبوع"
    if (isset($responseData['status']) && isset($responseData['message'])) {
        $status  = (string)$responseData['status'];
        $message = (string)$responseData['message'];

        // message نفسها JSON يحتوي ar أو fr
        if (str_starts_with(trim($message), '{') || str_contains($message, '"ar"') || str_contains($message, '"fr"')) {
            $inner2 = @json_decode($message, true);
            if (is_array($inner2)) {
                if (isset($inner2['ar'])) return [$status, (string)$inner2['ar'], $responseData, false];
                return [$status, (string)($inner2['message'] ?? $message), $responseData, false];
            }
        }

        // hasTx = false دائماً هنا (لا يوجد transaction-id في المستوى الأعلى)
        return [$status, $message, $responseData, false];
    }

    // ── Case 3: body field ────────────────────────────────────────────────
    if (isset($responseData['body']) && is_string($responseData['body'])) {
        $inner3 = @json_decode($responseData['body'], true);
        if (is_array($inner3)) {
            $status  = (string)($inner3['code'] ?? $inner3['status'] ?? $responseData['status'] ?? 'unknown');
            $message = (string)($inner3['message'] ?? '');
            return [$status, $message, $inner3, false];
        }
    }

    // ── Case 4: raw field contains 429 ───────────────────────────────────
    if (isset($responseData['raw']) && str_contains((string)$responseData['raw'], '429')) {
        return ['429', 'Too Many Requests', $responseData, false];
    }

    // ── Fallback ──────────────────────────────────────────────────────────
    $status  = (string)($responseData['status'] ?? $responseData['code'] ?? 'unknown');
    $message = (string)($responseData['message'] ?? '');
    return [$status, $message, $responseData, false];
}

// ════════════════════════════════════════════════════════════════════════════
//
// activate2G — نفس منطق send_subscription_product1_request في Python
//
// ════════════════════════════════════════════════════════════════════════════

function activate2G(string $psid, array $user): void
{
    $msisdn        = $user['msisdn'];
    $accessToken   = $user['access_token'];
    $refreshToken  = $user['refresh_token'];
    $displayMasked = substr($msisdn, 0, 4) . 'xxxx' . substr($msisdn, -2);

    $maxAttempts          = 30;
    $maxTokenRefresh      = 3;
    $tokenRefreshCount    = 0;
    $unauthorizedDetected = false;

    setPending($psid, 'تفعيل 2G 🎁');
    sendMessage($psid, "جاري تفعيل 2G 🎁 🔄...");

    for ($attempt = 1; $attempt <= $maxAttempts; $attempt++) {

        // ── Endpoint Walk&Win: activate-reward ───────────────────────────
        $raw = activateWalkRewardCurl(
            $msisdn, $accessToken,
            json_encode(['packageCode' => 'GIFTWALKWIN2GO']),
            'act2g'
        );

        // cURL فشل كلياً أو HTML → أعد المحاولة دائماً
        if ($raw === null) { usleep(1000000); continue; }

        $httpCode     = $raw['http_code'];
        $responseData = $raw['json'];
        $bodyStr      = $raw['body'];

        dbg("[2G] attempt={$attempt} http={$httpCode} body=" . substr($bodyStr, 0, 300));

        // استجابة غير JSON → أعد المحاولة دائماً
        if (!is_array($responseData)) {
            if ($httpCode === 429) { usleep(2000000); } else { usleep(1000000); }
            continue;
        }

        // ── TOKEN_EXPIRED: fault 900901 ──────────────────────────────────
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

        // ── HTTP 402 = رصيد غير كافٍ ─────────────────────────────────────
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

        // ── HTTP 403 = لم تكمل أسبوع ─────────────────────────────────────
        if ($httpCode === 403 || $innerStatus === 403) {
            clearPending($psid);
            sendMessage($psid,
                "عذرا 😬 لم تكمل اسبوع ⚠️ اكمل اسبوع و اعد المحاولة مجددا 📆\n\n" .
                "⚡ قناة التلقرام : https://t.me/tasjilbott"
            );
            clearSession($psid); sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد."); return;
        }

        // ── HTTP 201 / status=200 = نجاح ────────────────────────────────
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
                    "https://timebucks.com/?refID=227870531\n\n" .
                    "✅ ويسجل بحساب جوجل وبس 🥰\n" .
                    "هكا راكم دعموا فيا باه نستمر وشكرا"
                );
                clearSession($psid); sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد."); return;
            }
            // 200 بدون تأكيد → أعد المحاولة
            usleep(1000000); continue;
        }

        // ── HTTP 429 ──────────────────────────────────────────────────────
        if ($httpCode === 429) { usleep(2000000); continue; }

        // ── HTTP 500 + أي شيء آخر → أعد المحاولة ────────────────────────
        usleep(1000000);
    }

    // FAILED — All attempts
    clearPending($psid);
    sendMessage($psid, "هناك اشكال في سيرفر جيزي ⚠️ لم نستطع التفعيل لرقمك \n\n⚡ قناة التلقرام : https://t.me/tasjilbott");
    clearSession($psid);
    sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد.");
}

// ════════════════════════════════════════════════════════════════════════════
//
// activate70DZ — نفس منطق send_subscription_product2_request في Python
//
// ════════════════════════════════════════════════════════════════════════════

function activate70DZ(string $psid, array $user): void
{
    $msisdn        = $user['msisdn'];
    $accessToken   = $user['access_token'];
    $refreshToken  = $user['refresh_token'];
    $displayMasked = substr($msisdn, 0, 4) . 'xxxx' . substr($msisdn, -2);

    $maxAttempts          = 10;
    $maxTokenRefresh      = 3;
    $tokenRefreshCount    = 0;
    $unauthorizedDetected = false;

    setPending($psid, 'تفعيل عرض 70دج 🔖');
    sendMessage($psid, "جاري تفعيل العرض 🔖 🔄...");

    for ($attempt = 1; $attempt <= $maxAttempts; $attempt++) {

        // ── Endpoint الجديد: activate-product ──────────────────────────
        $raw = activateProductCurl(
            $msisdn, $accessToken,
            json_encode(['packageCode' => 'BTLINTSPEEDDAY2Go']),
            'act70'
        );

        if ($raw === null) { usleep(1000000); continue; }

        $httpCode     = $raw['http_code'];
        $responseData = $raw['json'];
        $bodyStr      = $raw['body'];

        dbg("[70] attempt={$attempt} http={$httpCode} body=" . substr($bodyStr, 0, 300));

        if (!is_array($responseData)) {
            if ($httpCode === 429) { usleep(2000000); continue; }
            if ($httpCode === 500) { usleep(1000000); continue; }
            usleep(1000000);
            continue;
        }

        // ── TOKEN_EXPIRED (Invalid Credentials 900901) ──────────────────
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
            // أي خطأ آخر في fault → أعد المحاولة
            usleep(1000000);
            continue;
        }

        $innerStatus = (int)($responseData['status'] ?? 0);
        $innerMsg    = $responseData['message'] ?? '';

        // ── رصيد غير كافٍ: status=402 ──────────────────────────────────
        // {"status":402,"message":{...},"data":{"due":0,"mainBalance":10.11}}
        if ($httpCode === 402 || $innerStatus === 402) {
            clearPending($psid);
            $balance = null;
            $dataField = $responseData['data'] ?? null;
            if (is_array($dataField) && isset($dataField['mainBalance'])) {
                $balance = $dataField['mainBalance'];
            }
            $balanceMsg = ($balance !== null)
                ? "رصيدك الحالي: {$balance} دج 💳"
                : "";
            sendMessage($psid,
                "حدث خطأ ⚠️ رصيدك غير كافي 💰 لتفعيل هذا العرض 🔖 😔\n" .
                ($balanceMsg ? "{$balanceMsg}\n" : "") .
                "\n⚡ قناة التلقرام : https://t.me/tasjilbott"
            );
            clearSession($psid); sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد."); return;
        }

        // ── غير مسموح (403): لم تكمل أسبوع ────────────────────────────
        // {"status":403,"message":{"ar":"...","fr":"...","en":"..."}}
        if ($httpCode === 403 || $innerStatus === 403) {
            clearPending($psid);
            sendMessage($psid, "عذرا 😬 لم تكمل اسبوع ⚠️ اكمل اسبوع و اعد المحاولة مجددا 📆\n\n⚡ قناة التلقرام : https://t.me/tasjilbott");
            clearSession($psid); sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد."); return;
        }

        // ── نجاح: HTTP 201 أو status=200 ────────────────────────────────
        // {"message":"Product successfully activated","status":200,"data":[]}
        if ($httpCode === 201 || $httpCode === 200 || $innerStatus === 200) {
            $msgStr = is_array($innerMsg) ? ($innerMsg['en'] ?? '') : (string)$innerMsg;
            if (stripos($msgStr, 'successfully') !== false || $httpCode === 201 || $innerStatus === 200) {
                clearPending($psid);
                sendMessage($psid,
                    "⭐ تم تفعيل العرض بنجاح 🎁 للرقم {$displayMasked}\n" .
                    "✅ اسم العرض: IMTIYAZ 70 🏷️\n" .
                    "✅ حجم الانترنت: 4Go انترنت 🌐\n" .
                    "✅ المدة: 24h ساعة ⏳\n\n" .
                    "✅ لا تنسى متابعة حساب المطور </>\nhttps://www.facebook.com/Bendjara.Yacin\n\n" .
                    "⚡ قناة التلقرام : https://t.me/tasjilbott"
                );
                sendMessage($psid,
                    "🥰 الناس لي سجلت فالموقع شكرا لكم 🥰\n\n" .
                    "🔴 ولي مزال يروح يدخل للموقع 👇\n\n" .
                    "https://timebucks.com/?refID=227870531\n\n" .
                    "✅ ويسجل بحساب جوجل وبس 🥰\n" .
                    "هكا راكم دعموا فيا باه نستمر وشكرا"
                );
                clearSession($psid); sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد."); return;
            }
            // 200 بدون تأكيد → أعد المحاولة
            usleep(1000000);
            continue;
        }

        // ── HTTP 429 ─────────────────────────────────────────────────────
        if ($httpCode === 429) { usleep(2000000); continue; }

        // ── HTTP 500 ─────────────────────────────────────────────────────
        if ($httpCode === 500) { usleep(1000000); continue; }

        usleep(1000000);
    }

    // ALL_ATTEMPTS_FAILED
    clearPending($psid);
    sendMessage($psid, "عذرا يبدو ان شريحتك لا تدعم هذا العرض \n\n⚡ قناة التلقرام : https://t.me/tasjilbott");
    clearSession($psid);
    sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد.");
}

// ════════════════════════════════════════════════════════════════════════════
// Subscription cURL — يُعيد ['http_code'=>int, 'json'=>array|null, 'body'=>string]
// أو null عند فشل الاتصال الكامل
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

    // مثل Python: إذا Content-Type هو JSON → parse، وإلا raw
    if (str_contains($ctType, 'application/json')) {
        $json = @json_decode($bodyStr, true);
        if (is_array($json)) return ['http_code' => $httpCode, 'json' => $json, 'body' => $bodyStr];
    }

    // محاولة parse على أي حال
    $json = @json_decode($bodyStr, true);
    if (is_array($json)) return ['http_code' => $httpCode, 'json' => $json, 'body' => $bodyStr];

    // HTML أو استجابة غير متوقعة → null حتى يُعيد المُستدعي المحاولة
    if (stripos($bodyStr, '<!DOCTYPE') !== false || stripos($bodyStr, '<html') !== false) return null;

    // raw response (مثل Python: {"raw": body, "status_code": code})
    return ['http_code' => $httpCode, 'json' => ['raw' => $bodyStr, 'status_code' => $httpCode], 'body' => $bodyStr];
}

// ════════════════════════════════════════════════════════════════════════════
// activateProductCurl — Endpoint الجديد: /api/v1/subscribers/activate-product
// يُعيد ['http_code'=>int, 'json'=>array|null, 'body'=>string] أو null
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
// activateWalkRewardCurl — Endpoint: /api/v1/services/walk/activate-reward/{msisdn}
// يُعيد ['http_code'=>int, 'json'=>array|null, 'body'=>string] أو null
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

    // HTML → null حتى يُعيد المُستدعي المحاولة مع proxy آخر
    if (stripos($bodyStr, '<!DOCTYPE') !== false || stripos($bodyStr, '<html') !== false) return null;

    $json    = @json_decode($bodyStr, true);
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

function sendWelcome(string $psid): void { sendMessage($psid, "👋 مرحباً بك في  Tasjil BOT!\n\nأهلاً وسهلاً 😊\nالرجاء إدخال رقم هاتفك للمتابعة 📱 .\n"); }

function sendMenu(string $psid): void
{
    setSession($psid, array_merge(getSession($psid), ['state' => 'menu']));
    fbApiCall(json_encode([
        'recipient'      => ['id' => $psid],
        'messaging_type' => 'RESPONSE',
        'message'        => [
            'text'          => "اختر العرض المناسب 📱 \n اذا لم تظهر لك الازرار ارسل 👇\n\n✅ لتفعيل 2G الاسبوعية ارسل الرقم | 1\n✅ لتفعيل عرض 70دج_4جيقا 🏷️ ارسل الرقم | 2 \n ✅ لإرسال دعوة ارسل الرقم | 3\n\n\n",
            'quick_replies' => [
                ['content_type'=>'text','title'=>'📶 تفعيل 2G',        'payload'=>'MENU_2G'],
                ['content_type'=>'text','title'=>'💰 عرض 70دج - 4جيقا','payload'=>'MENU_70DZ'],
                ['content_type'=>'text','title'=>'📨 إرسال دعوة',       'payload'=>'MENU_INVITE'],
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
    "https://change4.owlproxy.com:7778:ZaiSpSIir790_custom_zone_DZ_st__city_sid_63421710_time_5:2480642",
    "https://change4.owlproxy.com:7778:nt2UfuuJTP70_custom_zone_DZ_st__city_sid_56840069_time_5:2480664",
    "https://change4.owlproxy.com:7778:m2U47BplIN70_custom_zone_DZ_st__city_sid_88800010_time_5:2480684",
    "https://change4.owlproxy.com:7778:apBEomHX6t20_custom_zone_DZ_st__city_sid_79938468_time_5:2480691",

    "https://change4.owlproxy.com:7778:zBTAb9nmbH90_custom_zone_DZ_st__city_sid_52675494_time_5:2491277",
    "https://change4.owlproxy.com:7778:iigKAdjvNr40_custom_zone_DZ_st__city_sid_54987282_time_5:2491291",
    "https://change4.owlproxy.com:7778:16k79ionYTA0_custom_zone_DZ_st__city_sid_52592293_time_5:2491295",
    "https://change4.owlproxy.com:7778:slEWrtfpUd30_custom_zone_DZ_st__city_sid_35482917_time_5:2491301",
    "https://change4.owlproxy.com:7778:1vn6kP9Ya730_custom_zone_DZ_st__city_sid_94243908_time_5:2491305",
    "https://change4.owlproxy.com:7778:xKsPuOyxrn50_custom_zone_DZ_st__city_sid_97462857_time_5:2491320",
    "https://change4.owlproxy.com:7778:FB6F1dLs3R40_custom_zone_DZ_st__city_sid_34530647_time_5:2491324",
    "https://change4.owlproxy.com:7778:u7eohVR1Fv50_custom_zone_DZ_st__city_sid_15191711_time_5:2491326",
    "https://change4.owlproxy.com:7778:RKGEFZM08A00_custom_zone_DZ_st__city_sid_24966343_time_5:2491333",
    "https://change4.owlproxy.com:7778:uo3QTuYrxv10_custom_zone_DZ_st__city_sid_15907504_time_5:2491340"
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

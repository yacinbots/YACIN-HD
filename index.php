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
define('MGM_DIR',         '/tmp/fb_mgm');

define('MGM_BASE_URL',    'https://apim.djezzy.dz/mobile-api');
define('MGM_CLIENT_ID',   '87pIExRhxBb3_wGsA5eSEfyATloa');
define('MGM_CLIENT_SECRET','uf82p68Bgisp8Yg1Uz8Pf6_v1XYa');

@mkdir(SESSIONS_DIR, 0777, true);
@mkdir(USERS_DIR,    0777, true);
@mkdir(PENDING_DIR,  0777, true);
@mkdir(MGM_DIR,      0777, true);

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
    if (isset($msg['attachments']) && empty($msg['text'])) { sendMessage($psid, "🌙"); return; }
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

    // ── MGM states ──────────────────────────────────────────────────────────
    if ($state === 'mgm_await_invitee') { handleMgmAwaitInvitee($psid, $text, $session); return; }
    if ($state === 'mgm_await_otp')     { handleMgmAwaitOtp($psid, $text, $session);     return; }

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
            $sess = getSession($psid); $user = getUser($psid);
            if (!$user || empty($user['access_token'])) { sendMessage($psid, "⚠️ يجب تسجيل الدخول أولاً، أرسل رقم هاتفك."); return; }
            if (!empty($sess['msisdn'])) $user['msisdn'] = $sess['msisdn'];
            setSession($psid, array_merge($sess, ['state' => 'mgm_await_invitee']));
            sendMessage($psid, "📨 أدخل رقم الهاتف المدعو (الرقم الذي سيستقبل الدعوة):\nمثال: 0770123456");
            break;
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

    $maxAttempts         = 10;
    $maxTokenRefresh     = 3;
    $tokenRefreshCount   = 0;
    $unauthorizedDetected = false;  // رسالة التأخير مرة واحدة فقط (attempt == 1)

    setPending($psid, 'تفعيل 2G 🎁');
    sendMessage($psid, "جاري تفعيل 2G 🎁 🔄...");

    for ($attempt = 1; $attempt <= $maxAttempts; $attempt++) {

        $raw = subscriptionCurl(
            $msisdn, $accessToken,
            json_encode(['data' => ['id' => 'GIFTWALKWIN', 'type' => 'products', 'meta' => ['services' => ['steps' => 10000, 'code' => 'GIFTWALKWIN2GO', 'id' => 'WALKWIN']]]]),
            'act2g'
        );

        // cURL فشل كلياً
        if ($raw === null) { usleep(1000000); continue; }

        $httpCode     = $raw['http_code'];
        $responseData = $raw['json'];   // array أو null
        $bodyStr      = $raw['body'];

        // إذا لم يكن JSON صالح
        if (!is_array($responseData)) {
            if ($httpCode === 429) { usleep(2000000); continue; }
            if ($httpCode === 500) { usleep(1000000); continue; }
            usleep(1000000);
            continue;
        }

        [$statusCode, $message, $fullData, $hasTransaction] = parseResponseContent($responseData);

        dbg("[2G] attempt={$attempt} http={$httpCode} status={$statusCode} msg={$message} hasTx=" . ($hasTransaction?'Y':'N'));

        // ── TOKEN_EXPIRED ────────────────────────────────────────────────
        if ($statusCode === '401' && stripos($message, 'invalid credentials') !== false) {
            if ($tokenRefreshCount >= $maxTokenRefresh) {
                clearPending($psid);
                sendMessage($psid, "فشل تحديث الجلسة بعد عدة محاولات، الرجاء إعادة ارسال رقمك للتسجيل من جديد");
                clearSession($psid);
                return;
            }
            $tokenRefreshCount++;
            $refreshed = refreshAccessToken($refreshToken, $msisdn, $psid);
            if ($refreshed === false) { clearPending($psid); clearSession($psid); return; }
            $accessToken  = $refreshed['access_token'];
            $refreshToken = $refreshed['refresh_token'];
            saveUser($psid, array_merge($user, ['access_token' => $accessToken, 'refresh_token' => $refreshToken]));
            $attempt--; // أعد نفس المحاولة
            continue;
        }

        // ── unauthorized product + hasTx=TRUE → انتهى الأسبوع (200 + inner JSON + transaction-id) ──
        // مثال: HTTP 200 + inner {"status":"401","message":"unauthorized product","transaction-id":"null"}
        if (stripos($message, 'unauthorized product') !== false && $hasTransaction) {
            clearPending($psid);
            sendMessage($psid,
                "عذرا 😬 لم تكمل اسبوع ⚠️ اكمل اسبوع و اعد المحاولة مجددا 📆\n\n" .
                "⚡ قناة التلقرام : https://t.me/tasjilbott"
            );
            clearSession($psid);
            sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد.");
            return;
        }

        // ── unauthorized product + hasTx=FALSE → أعد المحاولة ──────────
        // مثال: HTTP 401 + {"status":401,"message":"unauthorized product"} (بدون transaction-id)
        if (stripos($message, 'unauthorized product') !== false && !$hasTransaction) {
            if (!$unauthorizedDetected && $attempt === 1) {
                sendMessage($psid, "نواجه مشاكل في التفعيل . جاري اعادة المحاولة ... تستغرق اقل من 3 دقائق 🕘");
                $unauthorizedDetected = true;
            }
            if ($attempt < $maxAttempts) { usleep(1000000); continue; }
            // استنفذنا كل المحاولات بدون نجاح
            clearPending($psid);
            sendMessage($psid,
                "هناك اشكال في سيرفر جيزي ⚠️ لم نستطع التفعيل لرقمك \n\n" .
                "⚡ قناة التلقرام : https://t.me/tasjilbott"
            );
            clearSession($psid);
            sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد.");
            return;
        }

        // ── HTTP 200 ─────────────────────────────────────────────────────
        if ($httpCode === 200) {
            // نجاح
            if (stripos($message, 'successfully done') !== false
                || stripos($message, 'giftwalkwin2go') !== false) {
                $txId = $fullData['transaction-id'] ?? null;
                if (($txId !== null && $txId !== 'null') || stripos($message, 'successfully done') !== false) {
                    clearPending($psid);
                    sendMessage($psid,
                        "⭐ تم تفعيل 2G بنجاح 🎁 للرقم {$displayMasked}\n" .
                        "لا تنسى متابعة حساب المطور </>\nhttps://www.facebook.com/Bendjara.Yacin\n\n" .
                        "⚡ قناة التلقرام : https://t.me/tasjilbott"
                    );
                    clearSession($psid);
                    sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد.");
                    return;
                }
            }
            // unauthorized في 200
            if (stripos($message, 'unauthorized') !== false) {
                if (stripos($message, 'product') !== false) {
                    if ($attempt < $maxAttempts) { usleep(1000000); continue; }
                    clearPending($psid);
                    sendMessage($psid, "عذرا 😬 لم تكمل اسبوع ⚠️ اكمل اسبوع و اعد المحاولة مجددا 📆\n\n⚡ قناة التلقرام : https://t.me/tasjilbott");
                    clearSession($psid);
                    sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد.");
                    return;
                }
            }
            usleep(1000000);
            continue;
        }

        // ── HTTP 402 / 403 أو JSON status=402 — رصيد غير كافٍ ─────────
        if ($httpCode === 402 || $httpCode === 403 || $statusCode === '402') {
            clearPending($psid);
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

        // ── HTTP 429 ─────────────────────────────────────────────────────
        if ($httpCode === 429) { usleep(2000000); continue; }

        // ── HTTP 500 ─────────────────────────────────────────────────────
        if ($httpCode === 500) { usleep(1000000); continue; }

        // ── فحص message مباشرة (fallback مثل Python) ────────────────────
        if ($message !== '') {
            $msgL = strtolower($message);
            if (str_contains($msgL, 'unauthorized product')) {
                if ($attempt < $maxAttempts) { usleep(1000000); continue; }
                clearPending($psid);
                sendMessage($psid, "عذرا 😬 لم تكمل اسبوع ⚠️ اكمل اسبوع و اعد المحاولة مجددا 📆\n\n⚡ قناة التلقرام : https://t.me/tasjilbott");
                clearSession($psid); sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد."); return;
            }
            if (str_contains($msgL, 'reactivate your walk and win') || str_contains($msgL, '100 da') || str_contains($msgL, 'balance')) {
                clearPending($psid);
                sendMessage($psid,
                    "عذرا ⚠️ يلزمك الاشتراك في باقة 100da 💰 (عشرة الاف) او اكثر ثم بعدها يمكنك الاستفادة من 2G 🎁 المجانية كل اسبوع طيلة شهر كامل 📆\n\n" .
                    "🔴 ملاحظة 1️⃣: هذا التحديث من المتعامل جيزي ولا يمكن تجاوزه ⚠️\n" .
                    "🔴 ملاحظة 2️⃣: يلزمك عرض ابتداءا من 100da او اكثر 💰\n" .
                    "⚡ قناة التلقرام : https://t.me/tasjilbott"
                );
                clearSession($psid); sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد."); return;
            }
            if (str_contains($msgL, 'successfully done')) {
                clearPending($psid);
                sendMessage($psid,
                    "⭐ تم تفعيل 2G بنجاح 🎁 للرقم {$displayMasked}\n" .
                    "لا تنسى متابعة حساب المطور </>\nhttps://www.facebook.com/Bendjara.Yacin\n\n" .
                    "⚡ قناة التلقرام : https://t.me/tasjilbott"
                );
                clearSession($psid); sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد."); return;
            }
        }

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

        $raw = subscriptionCurl(
            $msisdn, $accessToken,
            json_encode(['data' => ['id' => 'BTLINTSPEEDDAY2Go', 'type' => 'products']]),
            'act70'
        );

        if ($raw === null) { usleep(1000000); continue; }

        $httpCode     = $raw['http_code'];
        $responseData = $raw['json'];
        $bodyStr      = $raw['body'];

        if (!is_array($responseData)) {
            if ($httpCode === 429) { usleep(2000000); continue; }
            if ($httpCode === 500) { usleep(1000000); continue; }
            usleep(1000000);
            continue;
        }

        [$statusCode, $message, $fullData, $hasTransaction] = parseResponseContent($responseData);

        dbg("[70] attempt={$attempt} http={$httpCode} status={$statusCode} msg={$message} hasTx=" . ($hasTransaction?'Y':'N'));

        // ── TOKEN_EXPIRED ────────────────────────────────────────────────
        if ($statusCode === '401' && stripos($message, 'invalid credentials') !== false) {
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

        // ── رصيد غير كافٍ — يجب فحصه أولاً قبل أي شيء آخر ─────────────
        // HTTP 403 + {"status":402,"message":"your balance is not enough..."}
        // أو HTTP 402 مباشرة
        if ($httpCode === 402 || $httpCode === 403 || $statusCode === '402') {
            clearPending($psid);
            sendMessage($psid, "حدث خطا ⚠️ رصيدك غير كافي 💰 لتفعيل هذا العرض 🔖 😔\n\n⚡ قناة التلقرام : https://t.me/tasjilbott");
            clearSession($psid); sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد."); return;
        }

        // ── unauthorized product + hasTx=TRUE → أسبوع لم يكتمل ────────
        if (stripos($message, 'unauthorized product') !== false && $hasTransaction) {
            clearPending($psid);
            sendMessage($psid, "عذرا 😬 لم تكمل اسبوع ⚠️ اكمل اسبوع و اعد المحاولة مجددا 📆\n\n⚡ قناة التلقرام : https://t.me/tasjilbott");
            clearSession($psid); sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد."); return;
        }

        // ── unauthorized product + hasTx=FALSE → أعد المحاولة ──────────
        if (stripos($message, 'unauthorized product') !== false && !$hasTransaction) {
            if (!$unauthorizedDetected && $attempt === 1) {
                sendMessage($psid, "جاري إعادة المحاولة قد نتأخر قليلاً... 🕘");
                $unauthorizedDetected = true;
            }
            if ($attempt < $maxAttempts) { usleep(1000000); continue; }
            // استنفذنا كل المحاولات
            clearPending($psid);
            sendMessage($psid, "هناك اشكال في سيرفر جيزي ⚠️ لم نستطع التفعيل لرقمك \n\n⚡ قناة التلقرام : https://t.me/tasjilbott");
            clearSession($psid); sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد."); return;
        }

        // ── HTTP 200 ─────────────────────────────────────────────────────
        if ($httpCode === 200) {
            $successKeyword = 'btlintspeedday2go';
            if (stripos($message, $successKeyword) !== false || stripos($message, 'successfully done') !== false) {
                // تحقق من transaction-id
                $txId = $fullData['transaction-id'] ?? null;
                if ($txId === null && isset($fullData['message'])) {
                    $inner = is_string($fullData['message']) ? @json_decode($fullData['message'], true) : $fullData['message'];
                    if (is_array($inner)) $txId = $inner['transaction-id'] ?? null;
                }
                if (($txId !== null && $txId !== 'null') || stripos($message, 'successfully done') !== false) {
                    clearPending($psid);
                    sendMessage($psid,
                        "⭐ تم تفعيل العرض بنجاح 🎁 للرقم {$displayMasked}\n" .
                        "✅ اسم العرض: IMTIYAZ 70 🏷️\n" .
                        "✅ حجم الانترنت: 4Go انترنت 🌐\n" .
                        "✅ المدة: 24h ساعة ⏳\n\n" .
                        "✅ لا تنسى متابعة حساب المطور </>\nhttps://www.facebook.com/Bendjara.Yacin\n\n" .
                        "⚡ قناة التلقرام : https://t.me/tasjilbott"
                    );
                    clearSession($psid); sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد."); return;
                }
            }
            // 200 بدون تأكيد نجاح → أعد المحاولة مثل Python
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

    // raw response (مثل Python: {"raw": body, "status_code": code})
    return ['http_code' => $httpCode, 'json' => ['raw' => $bodyStr, 'status_code' => $httpCode], 'body' => $bodyStr];
}

// ════════════════════════════════════════════════════════════════════════════
// MGM — Member Get Member (نظام الدعوات)
// ════════════════════════════════════════════════════════════════════════════

// ── تخزين بيانات MGM المؤقتة ────────────────────────────────────────────
function saveMgmData(string $psid, array $data): void
{
    file_put_contents(MGM_DIR . "/{$psid}.json", json_encode($data, JSON_UNESCAPED_UNICODE));
}
function getMgmData(string $psid): ?array
{
    $f = MGM_DIR . "/{$psid}.json";
    if (!file_exists($f)) return null;
    $d = json_decode(@file_get_contents($f), true);
    if (!$d) return null;
    // انتهاء صلاحية بعد 10 دقائق
    if (time() - ($d['ts'] ?? 0) > 600) { @unlink($f); return null; }
    return $d;
}
function clearMgmData(string $psid): void
{
    $f = MGM_DIR . "/{$psid}.json";
    if (file_exists($f)) @unlink($f);
}

// ── الخطوة 1: استقبال رقم المدعو ────────────────────────────────────────
function handleMgmAwaitInvitee(string $psid, string $text, array $session): void
{
    $digits = preg_replace('/\D/', '', $text);

    if (!preg_match('/^07\d{8}$/', $digits)) {
        sendMessage($psid, "❌ رقم غير صحيح.\nالرجاء إدخال رقم جيزي صحيح يبدأ بـ 07 (10 أرقام).\nمثال: 0770123456");
        return;
    }

    $user = getUser($psid);
    if (!$user || empty($user['access_token'])) {
        sendMessage($psid, "⚠️ انتهت جلستك، أرسل رقم هاتفك للتسجيل من جديد.");
        setSession($psid, ['state' => 'idle']);
        return;
    }

    $inviteeMsisdn = '213' . substr($digits, 1);
    $senderMsisdn  = $session['msisdn'] ?? $user['msisdn'];

    if ($inviteeMsisdn === $senderMsisdn) {
        sendMessage($psid, "❌ لا يمكنك دعوة نفسك! أدخل رقم شخص آخر.");
        return;
    }

    // حفظ رقم المدعو والانتقال لطلب OTP
    saveMgmData($psid, ['invitee' => $inviteeMsisdn, 'sender' => $senderMsisdn, 'ts' => time()]);

    // إرسال OTP للمرسل (الداعي)
    $senderPhone = '0' . substr($senderMsisdn, 3);
    sendMessage($psid, "⏳ جاري إرسال رمز التحقق إلى رقمك {$senderPhone}...");

    if (mgmRequestOtp($senderMsisdn)) {
        setSession($psid, array_merge($session, ['state' => 'mgm_await_otp']));
        sendMessage($psid, "✅ تم إرسال رمز التحقق إلى رقمك.\n\n🔢 أدخل الرمز المكوّن من 6 أرقام:");
    } else {
        sendMessage($psid, "❌ فشل إرسال رمز التحقق، حاول مجدداً.");
        setSession($psid, array_merge($session, ['state' => 'menu']));
        sendMenu($psid);
    }
}

// ── الخطوة 2: استقبال OTP وتفعيل الدعوة ────────────────────────────────
function handleMgmAwaitOtp(string $psid, string $text, array $session): void
{
    if (!preg_match('/\b(\d{6})\b/', $text, $m)) {
        sendMessage($psid, "⚠️ الرجاء إدخال رمز التحقق المكوّن من 6 أرقام.");
        return;
    }

    $mgmData = getMgmData($psid);
    if (!$mgmData) {
        sendMessage($psid, "⏱️ انتهت مهلة الجلسة، أعد المحاولة من البداية.");
        setSession($psid, array_merge($session, ['state' => 'menu']));
        sendMenu($psid);
        return;
    }

    $senderMsisdn  = $mgmData['sender'];
    $inviteeMsisdn = $mgmData['invitee'];
    $otp           = $m[1];

    sendMessage($psid, "⏳ جاري التحقق والتفعيل...");

    // الحصول على توكن MGM
    $tokenResult = mgmLoginWithOtp($senderMsisdn, $otp);
    if ($tokenResult === 'wrong_otp') {
        sendMessage($psid, "❌ الرمز خاطئ، أعد إدخال الرمز الصحيح أو أرسل رقمك لطلب رمز جديد.");
        return;
    }
    if (!$tokenResult) {
        sendMessage($psid, "❌ حدث خطأ أثناء التحقق، حاول مجدداً.");
        return;
    }

    $mgmToken = $tokenResult['token'];

    // ── فحص الدعوات الحالية ──────────────────────────────────────────────
    $invResult = mgmGetInvitations($mgmToken, $senderMsisdn);
    $campaign  = $invResult['campaign'] ?? [];
    $maxInv    = (int)($campaign['maxInvitation'] ?? 5);
    $allInvs   = $invResult['all_invitations'] ?? [];
    $pending   = $invResult['pending_invitations'] ?? [];
    $done      = $invResult['accepted_invitations'] ?? [];

    $totalCount = count($allInvs);

    // إذا وصل للحد الأقصى: حاول حذف المعلقة
    if ($totalCount >= $maxInv) {
        if (!empty($pending)) {
            sendMessage($psid, "⚠️ وصلت للحد الأقصى ({$maxInv} دعوات).\n🗑️ جاري محاولة حذف الدعوات المعلقة...");
            $deleted = 0;
            foreach ($pending as $inv) {
                $recv = $inv['msisdnReceiver'] ?? '';
                if ($recv && mgmDeleteInvitation($mgmToken, $senderMsisdn, $recv)) {
                    $deleted++;
                    break; // نحذف واحدة فقط لنفسح مكاناً
                }
            }
            if ($deleted === 0) {
                // حساب تاريخ انتهاء أقدم دعوة
                $expireMsg = '';
                if (!empty($allInvs[0]['expireAt'])) {
                    $expireDate = substr($allInvs[0]['expireAt'], 0, 10);
                    $expireMsg  = "\n📅 أقرب انتهاء: {$expireDate}";
                }
                clearMgmData($psid);
                setSession($psid, array_merge($session, ['state' => 'menu']));
                sendMessage($psid, "❌ وصلت للحد الأقصى ({$maxInv} دعوات) ولا يمكن حذف الدعوات المعلقة الآن.{$expireMsg}\n\nيمكنك المحاولة مجدداً لاحقاً.");
                sendMenu($psid);
                return;
            }
            sendMessage($psid, "✅ تم حذف دعوة معلقة، جاري إرسال الدعوة الجديدة...");
        } else {
            // لا توجد معلقة — الكل مكتمل
            $expireMsg = '';
            if (!empty($done[0]['expireAt'])) {
                $expireDate = substr($done[0]['expireAt'], 0, 10);
                $expireMsg  = "\n📅 أقرب انتهاء: {$expireDate}";
            }
            clearMgmData($psid);
            setSession($psid, array_merge($session, ['state' => 'menu']));
            sendMessage($psid, "❌ وصلت للحد الأقصى ({$maxInv} دعوات) وجميعها مكتملة.{$expireMsg}\n\nيمكنك المحاولة بعد انتهاء صلاحية إحداها.");
            sendMenu($psid);
            return;
        }
    }

    // ── إرسال الدعوة ─────────────────────────────────────────────────────
    $sendResult = mgmSendInvitation($mgmToken, $senderMsisdn, $inviteeMsisdn);

    if (!$sendResult['success']) {
        $errBody = $sendResult['body'] ?? '';
        // تحليل رسائل الخطأ الشائعة
        if (stripos($errBody, 'already') !== false || stripos($errBody, 'exist') !== false) {
            sendMessage($psid, "⚠️ هذا الرقم تم دعوته مسبقاً.");
        } elseif (stripos($errBody, 'limit') !== false || stripos($errBody, 'max') !== false) {
            sendMessage($psid, "❌ وصلت للحد الأقصى من الدعوات.");
        } else {
            sendMessage($psid, "❌ فشل إرسال الدعوة.\nالسبب: " . substr($errBody, 0, 200));
        }
        clearMgmData($psid);
        setSession($psid, array_merge($session, ['state' => 'menu']));
        sendMenu($psid);
        return;
    }

    // ── تفعيل المكافأة للداعي ─────────────────────────────────────────────
    sendMessage($psid, "✅ تم إرسال الدعوة!\n⏳ جاري تفعيل المكافأة للداعي...");
    $rewardSender = mgmActivateReward($mgmToken, $senderMsisdn);

    // ── تفعيل المكافأة للمدعو (بصرف النظر عن نتيجة الداعي) ───────────────
    $rewardInvitee = mgmActivateReward($mgmToken, $inviteeMsisdn);

    // ── بناء رسالة النتيجة ────────────────────────────────────────────────
    $inviteeDisplay = '0' . substr($inviteeMsisdn, 3);
    $senderDisplay  = '0' . substr($senderMsisdn, 3);

    $senderStatus  = $rewardSender  ? "✅ نجح" : "⚠️ لم يتم أو تأخر";
    $inviteeStatus = $rewardInvitee ? "✅ نجح" : "⚠️ لم يتم أو تأخر";

    $resultMsg  = "🎁 نتيجة تفعيل الدعوة:\n\n";
    $resultMsg .= "📱 الداعي ({$senderDisplay}): {$senderStatus}\n";
    $resultMsg .= "📱 المدعو ({$inviteeDisplay}): {$inviteeStatus}\n\n";

    if ($rewardSender || $rewardInvitee) {
        $resultMsg .= "✅ تم تفعيل المكافأة بنجاح 🎉\n";
        $resultMsg .= "⏳ يمكنك إعادة المحاولة بعد 24 ساعة\n\n";
        $resultMsg .= "🥰 الناس لي سجلت فالموقع شكرا لكم 🥰\n\n";
        $resultMsg .= "🔴 ولي مزال يروح يدخل للموقع 👇\n\n";
        $resultMsg .= "https://timebucks.com/?refID=227870531\n\n";
        $resultMsg .= "✅ ويسجل بحساب جوجل وبس 🥰\n";
        $resultMsg .= "هكا راكم دعموا فيا باه نستمر وشكرا";
    } else {
        $resultMsg .= "❌ لم يتم تفعيل المكافأة، قد تكون مؤجلة من طرف جيزي.";
    }

    clearMgmData($psid);
    setSession($psid, array_merge($session, ['state' => 'menu']));
    sendMessage($psid, $resultMsg);
    sendMenu($psid);
}

// ════════════════════════════════════════════════════════════════════════════
// MGM API Calls
// ════════════════════════════════════════════════════════════════════════════

function mgmRequestOtp(string $msisdn): bool
{
    $url  = MGM_BASE_URL . '/oauth2/registration';
    $body = json_encode([
        'consent-agreement' => [['marketing-notifications' => false]],
        'is-consent'        => true,
    ]);
    $params = http_build_query(['msisdn' => $msisdn, 'client_id' => MGM_CLIENT_ID, 'scope' => 'smsotp']);

    $ch = curl_init("{$url}?{$params}");
    curl_setopt_array($ch, [
        CURLOPT_POST           => true,
        CURLOPT_POSTFIELDS     => $body,
        CURLOPT_HTTPHEADER     => ['Content-Type: application/json', 'Accept: application/json', 'User-Agent: MobileApp/3.0.0', 'accept-language: ar'],
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => 10,
        CURLOPT_SSL_VERIFYPEER => false,
    ]);
    $resp = curl_exec($ch);
    $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    dbg("[MGM_OTP] code={$code} body=" . substr((string)$resp, 0, 300));
    return $code >= 200 && $code < 300;
}

function mgmLoginWithOtp(string $msisdn, string $otp): mixed
{
    $url  = MGM_BASE_URL . '/oauth2/token';
    $data = http_build_query([
        'otp'           => $otp,
        'mobileNumber'  => $msisdn,
        'scope'         => 'djezzyAppV2',
        'client_id'     => MGM_CLIENT_ID,
        'client_secret' => MGM_CLIENT_SECRET,
        'grant_type'    => 'mobile',
    ]);

    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_POST           => true,
        CURLOPT_POSTFIELDS     => $data,
        CURLOPT_HTTPHEADER     => ['Content-Type: application/x-www-form-urlencoded', 'User-Agent: MobileApp/3.0.0'],
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => 10,
        CURLOPT_SSL_VERIFYPEER => false,
    ]);
    $resp = curl_exec($ch);
    $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    dbg("[MGM_LOGIN] code={$code} body=" . substr((string)$resp, 0, 300));

    if ($code === 200) {
        $json = @json_decode((string)$resp, true);
        if (isset($json['access_token'])) {
            return ['token' => 'Bearer ' . $json['access_token'], 'access_token' => $json['access_token']];
        }
    }
    $json = @json_decode((string)$resp, true);
    if ($code === 400 && ($json['error'] ?? '') === 'invalid_grant') return 'wrong_otp';
    return false;
}

function mgmGetInvitations(string $token, string $msisdn): array
{
    $url = MGM_BASE_URL . "/api/v1/services/mgm/invitations/{$msisdn}";
    $ch  = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_HTTPHEADER     => ['Content-Type: application/json', 'Accept: application/json', 'User-Agent: MobileApp/3.0.0', "authorization: {$token}"],
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => 10,
        CURLOPT_SSL_VERIFYPEER => false,
    ]);
    $resp = curl_exec($ch);
    $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    dbg("[MGM_INV] code={$code} body=" . substr((string)$resp, 0, 500));

    $result = ['all_invitations' => [], 'pending_invitations' => [], 'accepted_invitations' => [], 'campaign' => []];
    if ($code === 200) {
        $json    = @json_decode((string)$resp, true);
        $allInvs = $json['data']['invitations'] ?? [];
        $result['campaign']              = $json['data']['campaign'] ?? [];
        $result['all_invitations']       = $allInvs;
        $result['pending_invitations']   = array_values(array_filter($allInvs, fn($i) => ($i['status'] ?? '') === 'PENDING'));
        $result['accepted_invitations']  = array_values(array_filter($allInvs, fn($i) => ($i['status'] ?? '') === 'DONE'));
    }
    return $result;
}

function mgmSendInvitation(string $token, string $senderMsisdn, string $inviteeMsisdn): array
{
    $url  = MGM_BASE_URL . '/api/v1/services/mgm/send-invitation';
    $body = json_encode(['msisdnReceiver' => $inviteeMsisdn, 'msisdn' => $senderMsisdn]);

    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_POST           => true,
        CURLOPT_POSTFIELDS     => $body,
        CURLOPT_HTTPHEADER     => ['Content-Type: application/json', 'Accept: application/json', 'User-Agent: MobileApp/3.0.0', "authorization: {$token}"],
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => 10,
        CURLOPT_SSL_VERIFYPEER => false,
    ]);
    $resp = curl_exec($ch);
    $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    dbg("[MGM_SEND] code={$code} body=" . substr((string)$resp, 0, 400));

    return ['success' => $code >= 200 && $code < 300, 'status_code' => $code, 'body' => (string)$resp];
}

function mgmActivateReward(string $token, string $msisdn): bool
{
    // تفعيل المكافأة: طلب اشتراك MGM للرقم المحدد
    $url  = "https://apim.djezzy.dz/djezzy-api/api/v1/subscribers/{$msisdn}/subscription-product?include=";
    $body = json_encode(['data' => ['id' => 'MGM_GIFT', 'type' => 'products']]);

    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_POST           => true,
        CURLOPT_POSTFIELDS     => $body,
        CURLOPT_HTTPHEADER     => [
            'Content-Type: application/json',
            "Authorization: {$token}",
            'x-csrf-token: YACIN_DZ',
            'User-Agent: Djezzy/2.7.0',
            'Host: apim.djezzy.dz',
            'Accept: application/json',
            'Accept-Encoding: gzip',
        ],
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_ENCODING       => 'gzip',
        CURLOPT_TIMEOUT        => 10,
        CURLOPT_SSL_VERIFYPEER => false,
    ]);
    $resp = curl_exec($ch);
    $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    dbg("[MGM_REWARD] msisdn={$msisdn} code={$code} body=" . substr((string)$resp, 0, 400));

    // نعتبر 200/201 نجاح
    return $code >= 200 && $code < 300;
}

function mgmDeleteInvitation(string $token, string $senderMsisdn, string $receiverMsisdn): bool
{
    $url  = MGM_BASE_URL . '/api/v1/services/mgm/delete-invitation';
    $body = json_encode(['msisdnReceiver' => $receiverMsisdn, 'msisdn' => $senderMsisdn]);

    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_POST           => true,
        CURLOPT_POSTFIELDS     => $body,
        CURLOPT_HTTPHEADER     => ['Content-Type: application/json', 'Accept: application/json', 'User-Agent: MobileApp/3.0.0', "authorization: {$token}"],
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => 10,
        CURLOPT_SSL_VERIFYPEER => false,
    ]);
    $resp = curl_exec($ch);
    $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    dbg("[MGM_DEL] recv={$receiverMsisdn} code={$code} body=" . substr((string)$resp, 0, 300));

    return $code >= 200 && $code < 300;
}

// ════════════════════════════════════════════════════════════════════════════
// Refresh Token
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
        http_build_query(['scope' => 'openid', 'client_secret' => 'MVpXHW_ImuMsxKIwrJpoVVMHjRsa', 'client_id' => '6E6CwTkp8H1CyQxraPmcEJPQ7xka', 'grant_type' => 'refresh_token', 'refresh_token' => $refreshToken]),
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
    "https://change4.owlproxy.com:7778:Ur8Jf9Q5oe80_custom_zone_DZ_st__city_sid_69540969_time_5:2464884",
    "https://change4.owlproxy.com:7778:Ur8Jf9Q5oe80_custom_zone_DZ_st__city_sid_17300521_time_5:2464884",
    
    "https://change4.owlproxy.com:7778:9fap6Wjnn550_custom_zone_DZ_st__city_sid_20966754_time_5:2464900",
    "https://change4.owlproxy.com:7778:9fap6Wjnn550_custom_zone_DZ_st__city_sid_93674129_time_5:2464900",
    
    "https://change4.owlproxy.com:7778:F8T8PxheGD60_custom_zone_DZ_st__city_sid_28739257_time_5:2464912",
    "https://change4.owlproxy.com:7778:F8T8PxheGD60_custom_zone_DZ_st__city_sid_11001738_time_5:2464912",
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
    $q = http_build_query(['scope'=>'smsotp','client_id'=>'6E6CwTkp8H1CyQxraPmcEJPQ7xka','msisdn'=>$msisdn]);
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
        http_build_query(['scope'=>'openid','client_secret'=>'MVpXHW_ImuMsxKIwrJpoVVMHjRsa','client_id'=>'6E6CwTkp8H1CyQxraPmcEJPQ7xka','otp'=>$otp,'mobileNumber'=>$msisdn,'grant_type'=>'mobile']),
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

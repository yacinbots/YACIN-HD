<?php

// ════════════════════════════════════════════════════════════════════════════
// CONFIG
// ════════════════════════════════════════════════════════════════════════════

define('FB_TOKEN',        'EAAFYLlWaXQkBRWiaA6Na2MIDZBAFzF0YkjEdkLJYlcvslCvThFZBAupi7hBFjIQZCwjD3THUqxisUB7YvTyC4KNk8jEflOBHRlGX7hJpZCpqqpOVWd1gwuYDenY9JFZAEiftk30KUf29ZBGpknnT5kUTLoQsZBtdJ8bL1HGhhGdZAfVlJ0nuVnVRuZBqK9g7HPKGkuM9fuQZDZD');
define('VERIFY_TOKEN',    'Yacin');
define('PROXY_LIST_FILE', '/tmp/proxies.json');
define('PROXY_API_URL',   'https://dev-bendjarayacine.pantheonsite.io/wp-admin/maint/proxy.json');
define('SESSIONS_DIR',    '/tmp/fb_sessions');
define('USERS_DIR',       '/tmp/fb_users');
define('PHONE_MAP_FILE',  '/tmp/fb_phone_map.json');
define('PENDING_DIR',     '/tmp/fb_pending');
define('DB_FILE',         '/tmp/fb_dedup.sqlite');

// ─── Groq AI ─────────────────────────────────────────────────────────────────
define('GROQ_API_KEY',  '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');
define('GROQ_API_URL',  'https://api.groq.com/openai/v1/chat/completions');
define('GROQ_MODEL',    'llama-3.3-70b-versatile');

@mkdir(SESSIONS_DIR, 0777, true);
@mkdir(USERS_DIR,    0777, true);
@mkdir(PENDING_DIR,  0777, true);

// ════════════════════════════════════════════════════════════════════════════
// OFFERS DATABASE — كل العروض المتاحة
// ════════════════════════════════════════════════════════════════════════════

function getOffers(): array
{
    return [
        // ── يومية ────────────────────────────────────────────────────────────
        ['code'=>'DOVINTSPEEDDAY100MoPRE',  'internet'=>'300Mo',  'price'=>30,   'duration'=>'24 ساعة',  'category'=>'يومية'],
        ['code'=>'DOVINTSPEEDDAY250MoPRE',  'internet'=>'600Mo',  'price'=>50,   'duration'=>'24 ساعة',  'category'=>'يومية'],
        ['code'=>'DOVINTSPEEDDAY1GoPRE',    'internet'=>'2Go',    'price'=>100,  'duration'=>'24 ساعة',  'category'=>'يومية'],
        ['code'=>'OFFREJEUNE50',            'internet'=>'1Go',    'price'=>50,   'duration'=>'24 ساعة',  'category'=>'يومية'],
        ['code'=>'BTLINTSPEEDDAY2Go',       'internet'=>'4GB',    'price'=>70,   'duration'=>'24 ساعة',  'category'=>'يومية'],
        ['code'=>'BTL500MBDAY',             'internet'=>'3GB',    'price'=>90,   'duration'=>'24 ساعة',  'category'=>'يومية'],
        ['code'=>'BTL4GBDAY',               'internet'=>'5GB',    'price'=>190,  'duration'=>'24 ساعة',  'category'=>'يومية'],
        ['code'=>'BTL1GBDAY',               'internet'=>'4GB',    'price'=>140,  'duration'=>'24 ساعة',  'category'=>'يومية'],
        // ── أسبوعية ──────────────────────────────────────────────────────────
        ['code'=>'DOVINTSPEEDWEEK2GoPRE',   'internet'=>'4Go',    'price'=>150,  'duration'=>'7 أيام',   'category'=>'أسبوعية'],
        ['code'=>'DOVINTSPEEDWEEK3GoPRE',   'internet'=>'10Go',   'price'=>300,  'duration'=>'7 أيام',   'category'=>'أسبوعية'],
        ['code'=>'BTLDATA2WEEKS',           'internet'=>'4GB',    'price'=>400,  'duration'=>'15 يوم',   'category'=>'أسبوعية'],
        ['code'=>'1GBFB3DAYInternet',       'internet'=>'1GB (Facebook)', 'price'=>70, 'duration'=>'3 أيام', 'category'=>'أسبوعية'],
        // ── شهرية ────────────────────────────────────────────────────────────
        ['code'=>'DOVINTSPEEDMONTH6GoPRE',  'internet'=>'12Go',   'price'=>500,  'duration'=>'30 يوم',   'category'=>'شهرية'],
        ['code'=>'DOVINTSPEEDMONTH15GoPRE', 'internet'=>'30Go',   'price'=>1000, 'duration'=>'30 يوم',   'category'=>'شهرية'],
        ['code'=>'DOVINTSPEEDMONTH30GoPRE', 'internet'=>'60Go',   'price'=>1500, 'duration'=>'30 يوم',   'category'=>'شهرية'],
        ['code'=>'2GBMONTH',                'internet'=>'3GB',    'price'=>250,  'duration'=>'30 يوم',   'category'=>'شهرية'],
        // ── خاصة ─────────────────────────────────────────────────────────────
        ['code'=>'BTL500MBHOUR',            'internet'=>'1GB',    'price'=>40,   'duration'=>'1 ساعة',   'category'=>'خاصة'],
        ['code'=>'ImtiyazSurpriseData2hfbPRE','internet'=>'Facebook غير محدود','price'=>50,'duration'=>'4 ساعات','category'=>'خاصة'],
    ];
}

function formatOffersList(): string
{
    $offers = getOffers();
    $cats   = [];
    foreach ($offers as $o) $cats[$o['category']][] = $o;

    $msg = "📦 *العروض المتاحة*\n";
    foreach ($cats as $cat => $list) {
        $emoji = ['يومية'=>'☀️','أسبوعية'=>'📅','شهرية'=>'🗓️','خاصة'=>'⭐'][$cat] ?? '•';
        $msg .= "\n{$emoji} *{$cat}*\n";
        foreach ($list as $o) {
            $msg .= "  • {$o['internet']} | {$o['price']} دج | {$o['duration']}\n";
        }
    }
    $msg .= "\nأخبرني ماذا تريد وسأتكفل بالباقي 😊";
    return $msg;
}

function findOfferByCode(string $code): ?array
{
    foreach (getOffers() as $o) {
        if ($o['code'] === $code) return $o;
    }
    return null;
}

// ════════════════════════════════════════════════════════════════════════════
// AI — Groq Intent Parser
// ════════════════════════════════════════════════════════════════════════════

function offersJsonForPrompt(): string
{
    $items = [];
    foreach (getOffers() as $o) {
        $items[] = "code={$o['code']} | internet={$o['internet']} | price={$o['price']}دج | duration={$o['duration']} | category={$o['category']}";
    }
    return implode("\n", $items);
}

function groqParse(string $userInput): array
{
    $offersText = offersJsonForPrompt();

    $systemPrompt = <<<PROMPT
أنت محلل نوايا ذكي لبوت جيزي للإنترنت الجزائري.
لا تتحدث أبداً. لا تشرح. فقط أعد JSON صالحاً.

العروض المتاحة:
{$offersText}

القواعد:
1. إذا طلب المستخدم قائمة العروض → {"intent":"list_offers"}
2. إذا اختار عرضاً محدداً أو وصف ما يريد (سعر/حجم/مدة) → {"intent":"activate_offer","code":"OFFER_CODE"}
   - اختر الكود الأنسب للوصف (الأرخص إذا ذكر السعر، الأكبر إذا ذكر الحجم...)
   - إذا ذكر "فيسبوك" أو "fb" اختر الكودات الخاصة بالفيسبوك
3. إذا طلب عرضاً غير موجود → {"intent":"unknown_offer"}
4. إذا غير واضح → {"intent":"unknown"}

أعد JSON فقط بدون أي نص آخر.
PROMPT;

    $payload = [
        'model'       => GROQ_MODEL,
        'temperature' => 0,
        'max_tokens'  => 120,
        'messages'    => [
            ['role' => 'system', 'content' => $systemPrompt],
            ['role' => 'user',   'content' => $userInput],
        ],
    ];

    $ch = curl_init(GROQ_API_URL);
    curl_setopt_array($ch, [
        CURLOPT_POST           => true,
        CURLOPT_POSTFIELDS     => json_encode($payload),
        CURLOPT_HTTPHEADER     => [
            'Content-Type: application/json',
            'Authorization: Bearer ' . GROQ_API_KEY,
        ],
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => 15,
        CURLOPT_SSL_VERIFYPEER => false,
    ]);
    $body = curl_exec($ch);
    $err  = curl_errno($ch);
    curl_close($ch);

    if ($err || !$body) {
        dbg("[GROQ] cURL error $err");
        return ['intent' => 'unknown'];
    }

    $resp    = @json_decode($body, true);
    $content = trim($resp['choices'][0]['message']['content'] ?? '');

    // احتمال أن يضيف ```json
    $content = preg_replace('/^```json\s*/i', '', $content);
    $content = preg_replace('/\s*```$/',       '', $content);

    $parsed = @json_decode($content, true);
    if (!is_array($parsed)) {
        dbg("[GROQ] bad JSON: $content");
        return ['intent' => 'unknown'];
    }

    dbg("[GROQ] intent=" . ($parsed['intent'] ?? '?') . " code=" . ($parsed['code'] ?? '-'));
    return $parsed;
}

// ════════════════════════════════════════════════════════════════════════════
// AI — Groq Response Interpreter
// يُفسّر استجابة API جيزي ويعيد رسالة عربية جميلة
// ════════════════════════════════════════════════════════════════════════════

function groqInterpretResponse(int $httpCode, array $responseData, array $offer): string
{
    $rawJson    = json_encode($responseData, JSON_UNESCAPED_UNICODE);
    $offerDesc  = "كود: {$offer['code']} | حجم: {$offer['internet']} | سعر: {$offer['price']} دج | مدة: {$offer['duration']}";

    $systemPrompt = <<<PROMPT
أنت مساعد بوت جيزي الجزائري.
مهمتك: تحليل استجابة API وكتابة رسالة عربية قصيرة وواضحة للمستخدم.

قواعد الرد:
- إذا نجح التفعيل (HTTP 200 أو 201): اكتب رسالة ترحيبية مع تفاصيل العرض ✅
- إذا كان الرصيد غير كافٍ (402): أخبر المستخدم برفق 💰
- إذا لم يكمل المدة المطلوبة (403): أخبره أن يحاول لاحقاً 📅
- إذا كان خطأ في المصادقة (401): اطلب منه إعادة تسجيل الدخول 🔐
- أي خطأ آخر: رسالة مشجعة مع اقتراح المحاولة مجدداً ⚠️

اكتب فقط الرسالة النهائية للمستخدم بالعربية الدارجة الجزائرية. بدون تفسير. بدون JSON.
PROMPT;

    $userPrompt = "HTTP Code: {$httpCode}\nAPI Response: {$rawJson}\nOffer: {$offerDesc}";

    $payload = [
        'model'       => GROQ_MODEL,
        'temperature' => 0.4,
        'max_tokens'  => 200,
        'messages'    => [
            ['role' => 'system', 'content' => $systemPrompt],
            ['role' => 'user',   'content' => $userPrompt],
        ],
    ];

    $ch = curl_init(GROQ_API_URL);
    curl_setopt_array($ch, [
        CURLOPT_POST           => true,
        CURLOPT_POSTFIELDS     => json_encode($payload),
        CURLOPT_HTTPHEADER     => [
            'Content-Type: application/json',
            'Authorization: Bearer ' . GROQ_API_KEY,
        ],
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => 15,
        CURLOPT_SSL_VERIFYPEER => false,
    ]);
    $body = curl_exec($ch);
    $err  = curl_errno($ch);
    curl_close($ch);

    if ($err || !$body) {
        // Fallback بسيط إذا فشل AI
        return fallbackInterpret($httpCode, $responseData, $offer);
    }

    $resp    = @json_decode($body, true);
    $message = trim($resp['choices'][0]['message']['content'] ?? '');

    return $message ?: fallbackInterpret($httpCode, $responseData, $offer);
}

function fallbackInterpret(int $httpCode, array $responseData, array $offer): string
{
    $masked = substr($offer['code'], 0, 4) . '...';
    if ($httpCode === 200 || $httpCode === 201) {
        return "✅ تم تفعيل العرض بنجاح!\n📦 {$offer['internet']} | {$offer['price']} دج | {$offer['duration']}";
    }
    if ($httpCode === 402) return "💰 رصيدك غير كافٍ لتفعيل هذا العرض.";
    if ($httpCode === 403) return "📅 لم تكمل المدة المطلوبة بعد، حاول لاحقاً.";
    return "⚠️ حدث خطأ أثناء التفعيل، حاول مجدداً.";
}

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

    // أرقام هاتف
    if (preg_match('/^07\d{8}$/', $digits)) { handleNewPhone($psid, $digits); return; }
    if (preg_match('/^05\d{8}$/', $digits)) { sendMessage($psid, "⏳ سيتم إضافة Ooredoo قريباً."); return; }
    if (preg_match('/^06\d{8}$/', $digits)) { sendMessage($psid, "❌ لا يوجد تسجيل Mobilis."); return; }

    $session = getSession($psid);
    $state   = $session['state'] ?? 'idle';

    // OTP
    if ($state === 'awaiting_otp') { handleAwaitingOtp($psid, $text, $session); return; }

    // المستخدم مسجّل → نحلل رسالته بالذكاء الاصطناعي
    $user = getUser($psid);
    if ($user && !empty($user['access_token']) && $state === 'menu') {
        handleAIMessage($psid, $text, $user, $session);
        return;
    }

    sendWelcome($psid);
}

// ════════════════════════════════════════════════════════════════════════════
// AI Message Handler — المحرك الذكي الجديد
// ════════════════════════════════════════════════════════════════════════════

function handleAIMessage(string $psid, string $text, array $user, array $session): void
{
    // تحليل النية بالذكاء الاصطناعي
    sendMessage($psid, "🤖 جاري تحليل طلبك...");
    $result = groqParse($text);
    $intent = $result['intent'] ?? 'unknown';

    switch ($intent) {

        case 'list_offers':
            sendMessage($psid, formatOffersList());
            break;

        case 'activate_offer':
            $code  = $result['code'] ?? '';
            $offer = findOfferByCode($code);
            if (!$offer) {
                sendMessage($psid, "❌ لم أجد العرض المناسب، هل تريد رؤية العروض المتاحة؟ أرسل \"العروض\"");
                break;
            }
            // تأكيد قبل التفعيل
            if (!empty($session['msisdn'])) $user['msisdn'] = $session['msisdn'];
            setSession($psid, array_merge($session, ['state' => 'menu', 'pending_offer_code' => $code]));
            confirmOffer($psid, $offer);
            break;

        case 'unknown_offer':
            sendMessage($psid, "❌ هذا العرض غير متوفر حالياً.\n\nأرسل \"العروض\" لرؤية ما هو متاح 📦");
            break;

        default:
            // محاولة أخيرة: إذا قال "عروض" أو ما شابه
            if (stripos($text, 'عرض') !== false || stripos($text, 'باقة') !== false || stripos($text, 'انترنت') !== false) {
                sendMessage($psid, formatOffersList());
            } else {
                sendMessage($psid,
                    "🤔 لم أفهم طلبك جيداً.\n\n" .
                    "يمكنك:\n" .
                    "• إرسال \"العروض\" لرؤية الباقات 📦\n" .
                    "• وصف ما تريد مثل: \"أريد 4 جيغا يومية\" أو \"أرخص عرض أسبوعي\""
                );
            }
    }
}

// ════════════════════════════════════════════════════════════════════════════
// Confirm Offer (Quick Reply)
// ════════════════════════════════════════════════════════════════════════════

function confirmOffer(string $psid, array $offer): void
{
    $text = "هل تريد تفعيل هذا العرض؟ 🤔\n\n" .
            "📦 الحجم: {$offer['internet']}\n" .
            "💰 السعر: {$offer['price']} دج\n" .
            "⏳ المدة: {$offer['duration']}\n" .
            "🔖 الكود: {$offer['code']}";

    fbApiCall(json_encode([
        'recipient'      => ['id' => $psid],
        'messaging_type' => 'RESPONSE',
        'message'        => [
            'text'          => $text,
            'quick_replies' => [
                ['content_type' => 'text', 'title' => '✅ نعم، فعّل', 'payload' => 'CONFIRM_OFFER_' . $offer['code']],
                ['content_type' => 'text', 'title' => '❌ إلغاء',     'payload' => 'CANCEL_OFFER'],
            ],
        ],
    ], JSON_UNESCAPED_UNICODE));
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
        sendWelcomeMenu($psid);
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
                sendWelcomeMenu($psid);
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
    // تأكيد تفعيل عرض
    if (str_starts_with($payload, 'CONFIRM_OFFER_')) {
        $code = substr($payload, strlen('CONFIRM_OFFER_'));
        $offer = findOfferByCode($code);
        if (!$offer) { sendMessage($psid, "❌ العرض غير موجود."); return; }
        $user = getUser($psid);
        if (!$user || empty($user['access_token'])) {
            sendMessage($psid, "⚠️ يجب تسجيل الدخول أولاً، أرسل رقم هاتفك."); return;
        }
        $sess = getSession($psid);
        if (!empty($sess['msisdn'])) $user['msisdn'] = $sess['msisdn'];
        setSession($psid, array_merge($sess, ['state' => 'menu']));
        activateOffer($psid, $user, $offer);
        return;
    }

    if ($payload === 'CANCEL_OFFER') {
        sendMessage($psid, "تم الإلغاء ✅\nيمكنك طلب عرض آخر أو قول \"العروض\" لرؤية الباقات.");
        return;
    }

    // الرجوع للقائمة
    switch ($payload) {
        case 'GET_STARTED':
            sendWelcome($psid); break;
        case 'MENU_INVITE':
            sendMessage($psid, "قيد التطوير 🛠️"); break;
        default:
            sendWelcome($psid);
    }
}

// ════════════════════════════════════════════════════════════════════════════
// activateOffer — المفعّل الموحّد لكل العروض
// يستخدم endpoint: /activate-product/{msisdn}
// ويُفسّر الاستجابة بالذكاء الاصطناعي
// ════════════════════════════════════════════════════════════════════════════

function activateOffer(string $psid, array $user, array $offer): void
{
    $msisdn       = $user['msisdn'];
    $accessToken  = $user['access_token'];
    $refreshToken = $user['refresh_token'];

    $maxAttempts       = 10;
    $maxTokenRefresh   = 3;
    $tokenRefreshCount = 0;

    setPending($psid, "تفعيل {$offer['internet']} 🔄");
    sendMessage($psid, "⏳ جاري تفعيل {$offer['internet']} بـ {$offer['price']} دج...");

    for ($attempt = 1; $attempt <= $maxAttempts; $attempt++) {

        $raw = activateProductCurl(
            $msisdn, $accessToken,
            json_encode(['packageCode' => $offer['code']]),
            'act_offer'
        );

        if ($raw === null) { usleep(1000000); continue; }

        $httpCode     = $raw['http_code'];
        $responseData = $raw['json'];
        $bodyStr      = $raw['body'];

        dbg("[OFFER] attempt={$attempt} code={$offer['code']} http={$httpCode} body=" . substr($bodyStr, 0, 300));

        if (!is_array($responseData)) {
            if ($httpCode === 429) { usleep(2000000); } else { usleep(1000000); }
            continue;
        }

        // ── TOKEN_EXPIRED ────────────────────────────────────────────────
        $fault = $responseData['fault'] ?? null;
        if ($fault !== null && (int)($fault['code'] ?? 0) === 900901) {
            if ($tokenRefreshCount >= $maxTokenRefresh) {
                clearPending($psid);
                sendMessage($psid, "فشل تحديث الجلسة بعد عدة محاولات، الرجاء إعادة إرسال رقمك للتسجيل من جديد");
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

        // ── نجاح ─────────────────────────────────────────────────────────
        if ($httpCode === 201 || $httpCode === 200 || $innerStatus === 200) {
            $msgStr = $responseData['message'] ?? '';
            if (is_array($msgStr)) $msgStr = $msgStr['en'] ?? '';
            if (stripos((string)$msgStr, 'successfully') !== false || $httpCode === 201 || $innerStatus === 200) {
                clearPending($psid);
                // AI يُفسّر النجاح
                $aiMsg = groqInterpretResponse($httpCode, $responseData, $offer);
                sendMessage($psid, $aiMsg);
                sendMessage($psid,
                    "لا تنسى متابعة حساب المطور </>\nhttps://www.facebook.com/Bendjara.Yacin\n\n⚡ قناة التلقرام : https://t.me/tasjilbott"
                );
                clearSession($psid); sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد."); return;
            }
            usleep(1000000); continue;
        }

        // ── أخطاء معروفة (402, 403, 429, 500) → AI يُفسّر ───────────────
        if ($httpCode === 402 || $innerStatus === 402 ||
            $httpCode === 403 || $innerStatus === 403) {
            clearPending($psid);
            $aiMsg = groqInterpretResponse($httpCode, $responseData, $offer);
            sendMessage($psid, $aiMsg);
            sendMessage($psid, "⚡ قناة التلقرام : https://t.me/tasjilbott");
            clearSession($psid); sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد."); return;
        }

        if ($httpCode === 429) { usleep(2000000); continue; }
        usleep(1000000);
    }

    // فشل كل المحاولات
    clearPending($psid);
    sendMessage($psid, "⚠️ هناك إشكال في سيرفر جيزي، لم نستطع التفعيل.\n\n⚡ قناة التلقرام : https://t.me/tasjilbott");
    clearSession($psid);
    sendMessage($psid, "📱 أرسل رقم هاتفك للبدء من جديد.");
}

// ════════════════════════════════════════════════════════════════════════════
// activateProductCurl — Endpoint: /api/v1/subscribers/activate-product/{msisdn}
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

    file_put_contents('/tmp/activate_offer.log',
        date('Y-m-d H:i:s') . " [{$tag}] http={$httpCode} err={$error} body=" . substr((string)$body, 0, 600) . "\n",
        FILE_APPEND);

    if ($errno || $body === false || $httpCode === 0) return null;

    $bodyStr = (string)$body;
    if (stripos($bodyStr, '<!DOCTYPE') !== false || stripos($bodyStr, '<html') !== false) return null;

    $json = @json_decode($bodyStr, true);
    if (is_array($json)) return ['http_code' => $httpCode, 'json' => $json, 'body' => $bodyStr];

    return ['http_code' => $httpCode, 'json' => ['raw' => $bodyStr], 'body' => $bodyStr];
}

// ════════════════════════════════════════════════════════════════════════════
// Token Refresh
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

function sendWelcome(string $psid): void
{
    sendMessage($psid,
        "👋 مرحباً بك في Tasjil BOT!\n\n" .
        "أهلاً وسهلاً 😊\n" .
        "الرجاء إدخال رقم هاتفك للمتابعة 📱"
    );
}

function sendWelcomeMenu(string $psid): void
{
    fbApiCall(json_encode([
        'recipient'      => ['id' => $psid],
        'messaging_type' => 'RESPONSE',
        'message'        => [
            'text'          => "🎉 أنت الآن متصل!\n\nيمكنك:\n• طلب أي عرض بالكلام الطبيعي 💬\n• قول \"العروض\" لرؤية كل الباقات 📦\n\nمثال: \"أريد 4 جيغا يومية\" أو \"أرخص عرض أسبوعي\"",
            'quick_replies' => [
                ['content_type' => 'text', 'title' => '📦 العروض',      'payload' => 'LIST_OFFERS'],
                ['content_type' => 'text', 'title' => '📨 إرسال دعوة', 'payload' => 'MENU_INVITE'],
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
        "https://change4.owlproxy.com:7778:sKzlXsw5z110_custom_zone_DZ_st__city_sid_58976564_time_5:2913438",
        "https://change4.owlproxy.com:7778:s0FpXss9u890_custom_zone_DZ_st__city_sid_88058211_time_5:2913449",
        "https://change4.owlproxy.com:7778:NitQbWcIk200_custom_zone_DZ_st__city_sid_15738964_time_5:2913467",
        "https://change4.owlproxy.com:7778:XPyoaT8xQ050_custom_zone_DZ_st__city_sid_95382861_time_5:2913484",
        "https://change4.owlproxy.com:7778:ohVSoTjpfA00_custom_zone_DZ_st__city_sid_73014947_time_5:2913519",
        "https://change4.owlproxy.com:7778:BsRHVIFfqU40_custom_zone_DZ_st__city_sid_33523514_time_5:2913527",
        "https://change4.owlproxy.com:7778:xRPIzAFvZ150_custom_zone_DZ_st__city_sid_91870971_time_5:2913537",
        "https://change4.owlproxy.com:7778:lgeqvJPH0X70_custom_zone_DZ_st__city_sid_34215699_time_5:2913542",
        "https://change4.owlproxy.com:7778:bkz2jgqxev20_custom_zone_DZ_st__city_sid_67792435_time_5:2913547",
        "https://change4.owlproxy.com:7778:yzlLvd6fwx00_custom_zone_DZ_st__city_sid_43807670_time_5:2913554",
        "https://change4.owlproxy.com:7778:2yMB12m9Cc00_custom_zone_DZ_st__city_sid_21909680_time_5:2913563",
        "https://change4.owlproxy.com:7778:6STVg49FOc30_custom_zone_DZ_st__city_sid_87240509_time_5:2913576",
        "https://change4.owlproxy.com:7778:YKh7Ut67sY50_custom_zone_DZ_st__city_sid_83968032_time_5:2913586",
        "https://change4.owlproxy.com:7778:xU02zpyIbt90_custom_zone_DZ_st__city_sid_46723632_time_5:2913599",
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
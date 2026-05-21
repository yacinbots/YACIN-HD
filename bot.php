<?php

// ════════════════════════════════════════════════════════════════════════════
// الإعدادات
// ════════════════════════════════════════════════════════════════════════════

define('FB_TOKEN',      'EAAFYLlWaXQkBRghZCFuzj9G0sigyS10BdCZClE7V8wcvub8IsXuAoSRrP8ei2ZBEMP2N3BZBlMo8I4QdLXsiZCSyF1TD1DhVPRf2SPZCtKGPFCz598zqjJOwIuGznXTKkbPu38X9ZAD7PflnX1VOoWkkjFhC6xZAOJ8ZADxRkjEBlSzWf0yKtUx3QhdTzoA4ksBa1Ok8ofBrHsAZDZD');
define('VERIFY_TOKEN',  'Yacin');
define('CHAT_API_URL',  'http://de3.bot-hosting.net:21007/kilwa-chatgpt');
define('IMAGE_API_URL', 'http://de3.bot-hosting.net:21007/kilwa-gpt-img');
define('HISTORY_DIR',   '/tmp/ai_history');
define('MAX_HISTORY',   4); // آخر رسالتين مع ردّيهما

// رسالة النظام — تُرسل في كل محادثة
define('SYSTEM_MSG',
    "أنت مساعد ذكاء اصطناعي اسمك كيلوا. تتحدث بالعربية وتستطيع الرد بأي لغة يختارها المستخدم. " .
    "أنت مساعد مفيد وودود تجيب على جميع الأسئلة بدقة ووضوح. " .
    "عندما يطلب منك المستخدم توليد أو رسم أو إنشاء صورة، لا تصفها نصياً، " .
    "بل أجب فقط بهذا التنسيق الحرفي دون أي كلام آخر: " .
    "promt: [وصف الصورة بالإنجليزية بتفصيل دقيق مناسب لنماذج توليد الصور]"
);

@mkdir(HISTORY_DIR, 0777, true);

// ════════════════════════════════════════════════════════════════════════════
// Webhook Verify (GET)
// ════════════════════════════════════════════════════════════════════════════

if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    if (
        isset($_GET['hub_mode'], $_GET['hub_verify_token'], $_GET['hub_challenge'])
        && $_GET['hub_mode'] === 'subscribe'
        && $_GET['hub_verify_token'] === VERIFY_TOKEN
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

            try { processEvent($psid, $event); }
            catch (Throwable $e) { dbg("[ERR] $psid " . $e->getMessage()); }
        }
    }
    exit;
}

http_response_code(200); echo 'OK'; exit;

// ════════════════════════════════════════════════════════════════════════════
// معالجة الحدث الرئيسي
// ════════════════════════════════════════════════════════════════════════════

function processEvent(string $psid, array $event): void
{
    // زر GET_STARTED
    if (isset($event['postback'])) {
        $payload = $event['postback']['payload'] ?? '';
        if ($payload === 'GET_STARTED') {
            sendMessage($psid,
                "👋 أهلاً وسهلاً! أنا كيلوا، مساعدك الذكي 🤖\n\n" .
                "يمكنني مساعدتك في:\n" .
                "💬 الإجابة على أسئلتك\n" .
                "🎨 توليد الصور (فقط اطلب مني رسم أي شيء)\n\n" .
                "ابدأ بكتابة رسالتك الآن! 👇"
            );
        }
        return;
    }

    if (!isset($event['message'])) return;

    $msg = $event['message'];

    // ملصق like
    if (isset($msg['sticker_id']) && $msg['sticker_id'] == 369239263222822) {
        sendMessage($psid, '👍');
        return;
    }

    // مرفقات بدون نص
    if (isset($msg['attachments']) && empty($msg['text'])) {
        sendMessage($psid, "🙂 أرسل لي نصاً وسأساعدك!");
        return;
    }

    $text = trim($msg['text'] ?? '');
    if ($text === '') return;

    // أمر مسح السجل
    if (in_array(mb_strtolower($text), ['مسح', 'clear', 'reset', '/مسح', '/clear', '/reset'])) {
        clearHistory($psid);
        sendMessage($psid, "🗑️ تم مسح سجل المحادثة. ابدأ محادثة جديدة! 😊");
        return;
    }

    // معالجة الرسالة عبر الذكاء الاصطناعي
    handleAIChat($psid, $text);
}

// ════════════════════════════════════════════════════════════════════════════
// منطق الدردشة مع الذكاء الاصطناعي
// ════════════════════════════════════════════════════════════════════════════

function handleAIChat(string $psid, string $userText): void
{
    // بناء السياق: رسالة النظام + السجل + الرسالة الحالية
    $context = buildContext($psid, $userText);

    // استدعاء API الدردشة
    $botReply = callChatAPI($context);

    if ($botReply === null) {
        sendMessage($psid, "⚠️ حدث خطأ في الاتصال، حاول مجدداً.");
        return;
    }

    // هل الرد يحتوي على طلب توليد صورة؟
    if (preg_match('/promt\s*:\s*(.+)/iu', $botReply, $matches)) {
        $imagePrompt = trim($matches[1]);

        // حفظ المحادثة في السجل
        addToHistory($psid, 'المستخدم', $userText);
        addToHistory($psid, 'البوت', $botReply);

        // أبلغ المستخدم أن التوليد قد يأخذ وقتاً
        sendMessage($psid,
            "🎨 جاري توليد 4 صور بأحدث نماذج الذكاء الاصطناعي...\n" .
            "⏳ قد يستغرق التوليد بعض الوقت بسبب استخدام أحدث نماذج التوليد في البوت، يرجى الانتظار 🙏"
        );

        // توليد 4 صور بالتوازي وإرسالها
        generateAndSendImages($psid, $imagePrompt);
        return;
    }

    // رد نصي عادي — حفظ المحادثة وإرسال الرد
    addToHistory($psid, 'المستخدم', $userText);
    addToHistory($psid, 'البوت', $botReply);
    sendMessage($psid, $botReply);
}

// ════════════════════════════════════════════════════════════════════════════
// توليد وإرسال 4 صور بالتوازي
// ════════════════════════════════════════════════════════════════════════════

function generateAndSendImages(string $psid, string $prompt): void
{
    $multiHandle = curl_multi_init();
    $handles     = [];

    // أطلق 4 طلبات في نفس الوقت
    for ($i = 0; $i < 4; $i++) {
        $url = IMAGE_API_URL . '?' . http_build_query(['text' => $prompt]);
        $ch  = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT        => 120,
            CURLOPT_CONNECTTIMEOUT => 15,
            CURLOPT_SSL_VERIFYPEER => false,
            CURLOPT_HTTPHEADER     => ['Accept: application/json'],
        ]);
        curl_multi_add_handle($multiHandle, $ch);
        $handles[$i] = $ch;
    }

    // انتظر انتهاء جميع الطلبات
    $running = null;
    do {
        curl_multi_exec($multiHandle, $running);
        curl_multi_select($multiHandle);
    } while ($running > 0);

    // إرسال كل صورة فور الحصول على رابطها
    foreach ($handles as $ch) {
        $response = curl_multi_getcontent($ch);
        $error    = curl_error($ch);
        curl_multi_remove_handle($multiHandle, $ch);
        curl_close($ch);

        if ($error || !$response) {
            dbg("[IMG_ERR] $error");
            continue;
        }

        $data    = @json_decode($response, true);
        $imgUrl  = $data['url'] ?? $data['image'] ?? null;

        // إذا لم يكن JSON، تحقق إذا كان الرد رابطاً مباشراً
        if (!$imgUrl && filter_var(trim($response), FILTER_VALIDATE_URL)) {
            $imgUrl = trim($response);
        }

        if ($imgUrl) {
            sendImageAttachment($psid, $imgUrl);
        } else {
            dbg("[IMG_RESP] " . substr($response, 0, 300));
        }
    }

    curl_multi_close($multiHandle);
}

// ════════════════════════════════════════════════════════════════════════════
// API الدردشة — نفس أسلوب curl من ملف djezzy
// ════════════════════════════════════════════════════════════════════════════

function callChatAPI(string $context): ?string
{
    $url = CHAT_API_URL . '?' . http_build_query(['text' => $context]);

    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => 30,
        CURLOPT_CONNECTTIMEOUT => 10,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_HTTPHEADER     => ['Accept: application/json'],
    ]);

    $response = curl_exec($ch);
    $error    = curl_error($ch);
    $code     = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    dbg("[CHAT] code=$code err=$error resp=" . substr((string)$response, 0, 200));

    if ($error || !$response) return null;

    $data = @json_decode($response, true);
    return $data['reply'] ?? null;
}

// ════════════════════════════════════════════════════════════════════════════
// بناء السياق (رسالة النظام + السجل + الرسالة الحالية)
// ════════════════════════════════════════════════════════════════════════════

function buildContext(string $psid, string $userMessage): string
{
    $history = loadHistory($psid);

    $context = "النظام: " . SYSTEM_MSG . "\n\n";

    foreach ($history as $item) {
        $context .= $item['role'] . ": " . $item['text'] . "\n";
    }

    $context .= "المستخدم: " . $userMessage;

    return $context;
}

// ════════════════════════════════════════════════════════════════════════════
// إدارة سجل المحادثة (ملف JSON لكل مستخدم)
// ════════════════════════════════════════════════════════════════════════════

function loadHistory(string $psid): array
{
    $file = HISTORY_DIR . '/' . md5($psid) . '.json';
    if (!file_exists($file)) return [];
    $data = json_decode(@file_get_contents($file), true);
    return is_array($data) ? $data : [];
}

function addToHistory(string $psid, string $role, string $text): void
{
    $history   = loadHistory($psid);
    $history[] = ['role' => $role, 'text' => $text];

    // احتفظ بآخر MAX_HISTORY عنصر فقط
    if (count($history) > MAX_HISTORY) {
        $history = array_slice($history, -MAX_HISTORY);
    }

    file_put_contents(
        HISTORY_DIR . '/' . md5($psid) . '.json',
        json_encode($history, JSON_UNESCAPED_UNICODE)
    );
}

function clearHistory(string $psid): void
{
    $file = HISTORY_DIR . '/' . md5($psid) . '.json';
    if (file_exists($file)) @unlink($file);
}

// ════════════════════════════════════════════════════════════════════════════
// إرسال رسالة نصية — نفس fbApiCall من ملف djezzy
// ════════════════════════════════════════════════════════════════════════════

function sendMessage(string $psid, string $text): void
{
    fbApiCall(json_encode(
        [
            'recipient'      => ['id' => $psid],
            'messaging_type' => 'RESPONSE',
            'message'        => ['text' => $text],
        ],
        JSON_UNESCAPED_UNICODE
    ));
}

// ════════════════════════════════════════════════════════════════════════════
// إرسال صورة كـ attachment
// ════════════════════════════════════════════════════════════════════════════

function sendImageAttachment(string $psid, string $url): void
{
    fbApiCall(json_encode(
        [
            'recipient'      => ['id' => $psid],
            'messaging_type' => 'RESPONSE',
            'message'        => [
                'attachment' => [
                    'type'    => 'image',
                    'payload' => [
                        'url'         => $url,
                        'is_reusable' => true,
                    ],
                ],
            ],
        ],
        JSON_UNESCAPED_UNICODE
    ));
}

// ════════════════════════════════════════════════════════════════════════════
// fbApiCall — نفس الدالة من ملف djezzy
// ════════════════════════════════════════════════════════════════════════════

function fbApiCall(string $payload): void
{
    $ch = curl_init('https://graph.facebook.com/v19.0/me/messages?access_token=' . FB_TOKEN);
    curl_setopt_array($ch, [
        CURLOPT_POST            => true,
        CURLOPT_POSTFIELDS      => $payload,
        CURLOPT_HTTPHEADER      => ['Content-Type: application/json'],
        CURLOPT_RETURNTRANSFER  => true,
        CURLOPT_TIMEOUT         => 10,
        CURLOPT_CONNECTTIMEOUT  => 5,
        CURLOPT_SSL_VERIFYPEER  => false,
    ]);
    $resp = curl_exec($ch);
    $err  = curl_error($ch);
    curl_close($ch);
    dbg("[FB_SEND] ERR:$err RESP:$resp");
}

// ════════════════════════════════════════════════════════════════════════════
// Log
// ════════════════════════════════════════════════════════════════════════════

function dbg(string $m): void
{
    file_put_contents('/tmp/ai_chat.log', date('Y-m-d H:i:s') . " $m\n", FILE_APPEND);
}

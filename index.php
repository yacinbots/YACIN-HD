<?php

// ===============================
// 1. التحقق من Webhook (Facebook)
// ===============================
if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    $verify_token = "Yacin"; // نفس التوكن في إعدادات فيسبوك

    if (isset($_GET['hub_verify_token']) && $_GET['hub_verify_token'] === $verify_token) {
        echo $_GET['hub_challenge'];
        exit;
    } else {
        echo "Verification failed";
        exit;
    }
}

// ===============================
// 2. استقبال البيانات (مرة واحدة)
// ===============================
$input = json_decode(file_get_contents("php://input"), true);

// تأكد أن البيانات موجودة
if (!isset($input['entry'][0]['messaging'][0])) {
    exit;
}

$event = $input['entry'][0]['messaging'][0];

// ===============================
// 3. استخراج المعلومات
// ===============================
$page_id  = $event['recipient']['id'] ?? null;
$sender_id = $event['sender']['id'] ?? null;
$message   = $event['message']['text'] ?? '';

// ===============================
// 4. توزيع البوتات
// ===============================
switch ($page_id) {

    case "PAGE_ID_1":
        include("bot1.php"); // ضع هنا كودك الأول
        break;

    case "PAGE_ID_2":
        include("bot2.php"); // البوت الثاني
        break;

    case "PAGE_ID_3":
        include("bot3.php"); // (اختياري)
        break;

    default:
        // تسجيل الخطأ فقط
        error_log("Unknown PAGE_ID: " . $page_id);
        break;
}

// ===============================
// نهاية
// ===============================
?>

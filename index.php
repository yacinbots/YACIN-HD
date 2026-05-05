<?php
// تحديد البوت المطلوب
$bot = $_GET['bot'] ?? 'bot1';

/*
 * توجيه الطلبات إلى ملفات البوتات
 * بدون تعديل أي ملف بوت (مثل bot1.php)
 */
switch ($bot) {

    case 'bot1':
        require __DIR__ . '/bot1.php';
        break;

    default:
        http_response_code(404);
        echo "Bot not found";
        break;
}

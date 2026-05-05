<?php
$input = json_decode(file_get_contents("php://input"), true);
$event = $input['entry'][0]['messaging'][0] ?? [];
/*
|--------------------------------------------------------------------------
| تحديد البوت حسب Page ID (الأفضل مع فيسبوك)
|--------------------------------------------------------------------------
*/
$page_id = $input['entry'][0]['id'] ?? '';
switch ($page_id) {
    case "472588112603141":
        require __DIR__ . '/bot1.php';
        break;
    case "576061632260956":
        require __DIR__ . '/test.php';
        break;
    case "332234226645352":
        require __DIR__ . '/chatgpt.php';
        break;
    case "327492623791269":
        require __DIR__ . '/muslim.php';
        break;
    default:
        // إذا لم يتم التعرف على الصفحة
        require __DIR__ . '/bot.php';
        break;
}

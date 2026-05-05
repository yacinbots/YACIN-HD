<?php

// التحقق من Webhook
if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    $verify_token = "VERIFY_TOKEN";
    if ($_GET['hub_verify_token'] === $verify_token) {
        echo $_GET['hub_challenge'];
        exit;
    }
}

// استقبال البيانات مرة واحدة فقط
$input = json_decode(file_get_contents("php://input"), true);
$event = $input['entry'][0]['messaging'][0] ?? [];

$page_id = $event['recipient']['id'] ?? null;

// التوجيه
if ($page_id == "PAGE_ID_1") {
    include("bot1.php");
} elseif ($page_id == "PAGE_ID_2") {
    include("bot2.php");
}

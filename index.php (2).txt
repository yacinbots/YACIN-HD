<?php

$input = json_decode(file_get_contents("php://input"), true);
$event = $input['entry'][0]['messaging'][0] ?? [];

// تشغيل bot1 فقط
require __DIR__ . '/bot1.php';

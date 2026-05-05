<?php

if ($_SERVER['REQUEST_METHOD'] === 'GET') {

    $mode = $_GET['hub_mode'] ?? '';
    $token = $_GET['hub_verify_token'] ?? '';
    $challenge = $_GET['hub_challenge'] ?? '';

    if ($mode === 'subscribe' && $token === 'Yacin') {
        echo $challenge;
        exit;
    } else {
        echo "Verification failed";
        exit;
    }
}

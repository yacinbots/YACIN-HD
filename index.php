<?php
// ════════════════════════════════════════════════════════════════════════════
// 12GO GIFT ACTIVATION — ملف واحد متكامل (موقع + API)
// ════════════════════════════════════════════════════════════════════════════

session_start();

// ════════════ Config ════════════════════════════════════════════════════════
define('PROXY_LIST_FILE',  '/tmp/proxies.json');
define('SESSIONS_DIR',     '/tmp/12go_sessions');
define('LOG_FILE',         '/tmp/12go.log');
define('IP_LOG_FILE',      '/tmp/12go_ip_log.json');
define('TIME_CONFIG_FILE', '/tmp/time_config.json');

define('CLIENT_ID',     '87pIExRhxBb3_wGsA5eSEfyATloa');
define('CLIENT_SECRET', 'uf82p68Bgisp8Yg1Uz8Pf6_v1XYa');
define('MAX_ATTEMPTS', 5);
define('BLOCK_DURATION', 3600);
define('ADMIN_KEY', 'YOUR_SECRET_KEY_HERE_12345');

@mkdir(SESSIONS_DIR, 0777, true);

// ════════════ Time Config Functions ════════════════════════════════════════
function getTimeConfig(): array
{
    $defaults = [
        'is_open' => false,
        'timezone' => 'Africa/Algiers',
        'match_start' => '2026-07-03 01:00:00',
        'match_end' => '2026-07-03 05:00:00',
        'gift_label' => '12Go',
        'qr_code' => 'https://www.djezzy.dz/scanwin-wd26?1',
    ];
    
    if (!file_exists(TIME_CONFIG_FILE)) {
        file_put_contents(TIME_CONFIG_FILE, json_encode($defaults, JSON_PRETTY_PRINT));
        return $defaults;
    }
    
    $data = json_decode(file_get_contents(TIME_CONFIG_FILE), true);
    return is_array($data) ? array_merge($defaults, $data) : $defaults;
}

function saveTimeConfig(array $config): void
{
    file_put_contents(TIME_CONFIG_FILE, json_encode($config, JSON_PRETTY_PRINT));
}

function getMatchStatus(): array
{
    $config = getTimeConfig();
    $timezone = new DateTimeZone($config['timezone'] ?? 'Africa/Algiers');
    $now = new DateTime('now', $timezone);
    
    $start = new DateTime($config['match_start'] ?? '2026-07-03 01:00:00', $timezone);
    $end = new DateTime($config['match_end'] ?? '2026-07-03 05:00:00', $timezone);
    
    // 🔴 الأولوية القصوى: الفتح اليدوي
    if (($config['is_open'] ?? false) === true) {
        return [
            'status' => 'open',
            'message' => '✅ الموقع مفتوح (يدوياً)',
            'remaining' => max(0, $end->getTimestamp() - $now->getTimestamp()),
            'start' => $start->format('Y-m-d H:i:s'),
            'end' => $end->format('Y-m-d H:i:s'),
            'is_manual' => true,
        ];
    }
    
    // 🟢 الفتح التلقائي حسب الوقت
    if ($now >= $start && $now <= $end) {
        return [
            'status' => 'open',
            'message' => '✅ الموقع مفتوح — تفعيل الهدية الآن',
            'remaining' => max(0, $end->getTimestamp() - $now->getTimestamp()),
            'start' => $start->format('Y-m-d H:i:s'),
            'end' => $end->format('Y-m-d H:i:s'),
            'is_manual' => false,
        ];
    }
    
    // 🟡 في انتظار الفتح
    if ($now < $start) {
        return [
            'status' => 'waiting',
            'message' => '⏳ يبدأ قريباً',
            'remaining' => $start->getTimestamp() - $now->getTimestamp(),
            'start' => $start->format('Y-m-d H:i:s'),
            'end' => $end->format('Y-m-d H:i:s'),
            'is_manual' => false,
        ];
    }
    
    // 🔴 الموقع مغلق
    return [
        'status' => 'closed',
        'message' => '⏰ انتهى وقت التفعيل',
        'remaining' => 0,
        'start' => $start->format('Y-m-d H:i:s'),
        'end' => $end->format('Y-m-d H:i:s'),
        'is_manual' => false,
    ];
}

function formatRemaining(int $seconds): array
{
    $hours = floor($seconds / 3600);
    $minutes = floor(($seconds % 3600) / 60);
    $secs = $seconds % 60;
    return ['hours' => $hours, 'minutes' => $minutes, 'seconds' => $secs];
}

// ════════════ IP Functions ═════════════════════════════════════════════════
function getClientIP(): string
{
    $ip = $_SERVER['REMOTE_ADDR'] ?? '0.0.0.0';
    if (isset($_SERVER['HTTP_X_FORWARDED_FOR'])) {
        $ips = explode(',', $_SERVER['HTTP_X_FORWARDED_FOR']);
        $ip = trim($ips[0]);
    } elseif (isset($_SERVER['HTTP_CLIENT_IP'])) {
        $ip = $_SERVER['HTTP_CLIENT_IP'];
    }
    return $ip;
}

function getIPLog(): array
{
    if (!file_exists(IP_LOG_FILE)) return [];
    $data = json_decode(file_get_contents(IP_LOG_FILE), true);
    return is_array($data) ? $data : [];
}

function saveIPLog(array $log): void
{
    file_put_contents(IP_LOG_FILE, json_encode($log, JSON_PRETTY_PRINT));
}

function getIPData(string $ip): array
{
    $log = getIPLog();
    if (!isset($log[$ip])) {
        return [
            'attempts' => 0,
            'success' => 0,
            'failed' => 0,
            'blocked_until' => 0,
            'last_attempt' => 0,
            'numbers' => [],
            'hourly_attempts' => [],
        ];
    }
    
    $data = $log[$ip];
    $defaults = [
        'hourly_attempts' => [],
        'numbers' => [],
        'attempts' => 0,
        'success' => 0,
        'failed' => 0,
        'blocked_until' => 0,
        'last_attempt' => 0,
    ];
    foreach ($defaults as $key => $val) {
        if (!isset($data[$key])) {
            $data[$key] = $val;
        }
    }
    return $data;
}

function updateIPData(string $ip, array $data): void
{
    $log = getIPLog();
    $log[$ip] = $data;
    saveIPLog($log);
}

function isIPBlocked(string $ip): ?int
{
    $data = getIPData($ip);
    if ($data['blocked_until'] > time()) {
        return $data['blocked_until'] - time();
    }
    return null;
}

function getHourlyAttempts(string $ip): int
{
    $data = getIPData($ip);
    $now = time();
    $hourAgo = $now - 3600;
    $count = 0;
    if (isset($data['hourly_attempts']) && is_array($data['hourly_attempts'])) {
        foreach ($data['hourly_attempts'] as $ts) {
            if ($ts >= $hourAgo) $count++;
        }
    }
    return $count;
}

function recordIPAttempt(string $ip, bool $success, string $phone = ''): array
{
    $data = getIPData($ip);
    $now = time();
    
    if (!isset($data['hourly_attempts']) || !is_array($data['hourly_attempts'])) {
        $data['hourly_attempts'] = [];
    }
    
    $data['hourly_attempts'][] = $now;
    $hourAgo = $now - 3600;
    $data['hourly_attempts'] = array_values(array_filter($data['hourly_attempts'], function($ts) use ($hourAgo) {
        return $ts >= $hourAgo;
    }));
    
    $data['attempts'] = ($data['attempts'] ?? 0) + 1;
    $data['last_attempt'] = $now;
    
    if ($success) {
        $data['success'] = ($data['success'] ?? 0) + 1;
    } else {
        $data['failed'] = ($data['failed'] ?? 0) + 1;
    }
    
    if ($phone && !in_array($phone, $data['numbers'] ?? [])) {
        if (!isset($data['numbers'])) $data['numbers'] = [];
        $data['numbers'][] = $phone;
    }
    
    if (count($data['hourly_attempts']) >= MAX_ATTEMPTS) {
        $data['blocked_until'] = $now + BLOCK_DURATION;
    }
    
    updateIPData($ip, $data);
    return $data;
}

function getIPStats(string $ip): array
{
    $data = getIPData($ip);
    $hourly = getHourlyAttempts($ip);
    return [
        'attempts' => $data['attempts'] ?? 0,
        'success' => $data['success'] ?? 0,
        'failed' => $data['failed'] ?? 0,
        'hourly' => $hourly,
        'remaining' => max(0, MAX_ATTEMPTS - $hourly),
        'blocked' => ($data['blocked_until'] ?? 0) > time(),
        'blocked_until' => $data['blocked_until'] ?? 0,
        'blocked_remaining' => max(0, ($data['blocked_until'] ?? 0) - time()),
    ];
}

function formatBlockTime(int $seconds): string
{
    $hours = floor($seconds / 3600);
    $minutes = floor(($seconds % 3600) / 60);
    $secs = $seconds % 60;
    
    if ($hours > 0) {
        return "{$hours} ساعة و {$minutes} دقيقة";
    } elseif ($minutes > 0) {
        return "{$minutes} دقيقة و {$secs} ثانية";
    } else {
        return "{$secs} ثانية";
    }
}

// ════════════ Proxy & API Functions ════════════════════════════════════════
function loadProxies(): array
{
    if (file_exists(PROXY_LIST_FILE)) {
        $d = json_decode(file_get_contents(PROXY_LIST_FILE), true);
        if (is_array($d) && count($d) > 0) return $d;
    }
    return [
        "https://proxy.momoproxy.com:8100:customer-9b3TvAjM-country-DZ-time-5-sid-cjex2irintg:cHTZXtdd",
        "https://proxy.momoproxy.com:8100:customer-9b3TvAjM-country-DZ-time-5-sid-ql14bmulv5q:cHTZXtdd",
    ];
}

function parseProxy(string $proxy): array
{
    $raw = preg_replace('#^https?://#', '', $proxy);
    $p = explode(':', $raw, 4);
    return ['host' => ($p[0] ?? '') . ':' . ($p[1] ?? ''), 'userpass' => ($p[2] ?? '') . ':' . ($p[3] ?? '')];
}

function getAllProxies(): array { return loadProxies(); }

function djezzyCurl(string $url, string $data, string $ph, string $pa, string $tag): mixed
{
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => $data,
        CURLOPT_HTTPHEADER => [
            'Content-Type: application/x-www-form-urlencoded',
            'Accept: */*',
            'User-Agent: Dalvik/2.1.0 (Linux; U; Android 6.0; PGN610 Build/MRA58K)',
            'Connection: Keep-Alive',
            'Accept-Encoding: gzip'
        ],
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_ENCODING => 'gzip',
        CURLOPT_TIMEOUT => 10,
        CURLOPT_CONNECTTIMEOUT => 5,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_PROXY => $ph,
        CURLOPT_PROXYUSERPWD => $pa,
        CURLOPT_PROXYTYPE => CURLPROXY_HTTP,
        CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_MAXREDIRS => 3,
    ]);
    $body = curl_exec($ch);
    $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $err = curl_error($ch);
    curl_close($ch);
    
    file_put_contents(LOG_FILE, date('Y-m-d H:i:s') . " [$tag] CODE:$code ERR:$err\n", FILE_APPEND);
    
    if ($err || $body === false) return false;
    if (stripos((string)$body, '<!DOCTYPE') !== false || stripos((string)$body, '<html') !== false) return 'html';
    return ['code' => $code, 'body' => (string)$body];
}

function sendOTP(string $msisdn): bool
{
    $q = http_build_query(['scope' => 'smsotp', 'client_id' => CLIENT_ID, 'msisdn' => $msisdn]);
    foreach (getAllProxies() as $p) {
        $pp = parseProxy($p);
        $result = djezzyCurl('https://apim.djezzy.dz/oauth2/registration', $q, $pp['host'], $pp['userpass'], 'otp');
        if ($result === true) return true;
        if (is_array($result) && $result['code'] >= 200 && $result['code'] < 300) return true;
    }
    return false;
}

function verifyOTP(string $msisdn, string $otp): mixed
{
    $data = http_build_query([
        'scope' => 'djezzyAppV2',
        'client_secret' => CLIENT_SECRET,
        'client_id' => CLIENT_ID,
        'otp' => $otp,
        'mobileNumber' => $msisdn,
        'grant_type' => 'mobile'
    ]);
    
    foreach (getAllProxies() as $p) {
        $pp = parseProxy($p);
        $result = djezzyCurl('https://apim.djezzy.dz/oauth2/token', $data, $pp['host'], $pp['userpass'], 'token');
        if ($result === 'html' || $result === false) continue;
        $json = @json_decode($result['body'], true);
        if ($result['code'] === 400 && ($json['error'] ?? '') === 'invalid_grant') return 'wrong_otp';
        if ($result['code'] === 200 && isset($json['access_token'])) {
            return ['access_token' => $json['access_token'], 'refresh_token' => $json['refresh_token'] ?? ''];
        }
    }
    return false;
}

function activateGift(string $msisdn, string $accessToken, string $qrCode): array
{
    $url = "https://apim.djezzy.dz/mobile-api/api/v1/services/scan/activate-reward/{$msisdn}";
    $payload = json_encode(['qrCode' => $qrCode]);
    $headers = [
        'Content-Type: application/json',
        'Accept: application/json',
        'Accept-Encoding: gzip',
        "Authorization: Bearer {$accessToken}",
        'User-Agent: MobileApp/3.0.0',
    ];
    
    $proxies = getAllProxies();
    foreach ($proxies as $p) {
        $pp = parseProxy($p);
        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_POST => true,
            CURLOPT_POSTFIELDS => $payload,
            CURLOPT_HTTPHEADER => $headers,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_ENCODING => 'gzip',
            CURLOPT_TIMEOUT => 12,
            CURLOPT_CONNECTTIMEOUT => 5,
            CURLOPT_SSL_VERIFYPEER => false,
            CURLOPT_PROXY => $pp['host'],
            CURLOPT_PROXYUSERPWD => $pp['userpass'],
            CURLOPT_PROXYTYPE => CURLPROXY_HTTP,
            CURLOPT_FOLLOWLOCATION => true,
        ]);
        $body = curl_exec($ch);
        $httpCode = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        if ($httpCode === 200 || $httpCode === 201) {
            return ['success' => true, 'message' => '🎉 تم تفعيل 12 جيقا بنجاح!'];
        }
        if ($httpCode === 400) {
            return ['success' => false, 'message' => '⚠️ رقمك غير مؤهل أو تم الاستفادة مسبقاً'];
        }
    }
    return ['success' => false, 'message' => '❌ حدث خطأ، حاول مجدداً'];
}

// ════════════ Session Functions ════════════════════════════════════════════
function getSession(string $id): array
{
    $f = SESSIONS_DIR . "/{$id}.json";
    return file_exists($f) ? (json_decode(file_get_contents($f), true) ?? []) : [];
}
function setSession(string $id, array $data): void
{
    file_put_contents(SESSIONS_DIR . "/{$id}.json", json_encode($data));
}
function clearSession(string $id): void
{
    $f = SESSIONS_DIR . "/{$id}.json";
    if (file_exists($f)) unlink($f);
}

// ════════════ API Handler (طلبات Python) ══════════════════════════════════
if (isset($_GET['api'])) {
    header('Content-Type: application/json');
    $action = $_GET['action'] ?? 'status';
    
    switch ($action) {
        case 'status':
            echo json_encode(getMatchStatus());
            break;
            
        case 'set_open':
            $key = $_GET['key'] ?? '';
            if ($key !== ADMIN_KEY) {
                http_response_code(403);
                echo json_encode(['error' => 'Unauthorized']);
                break;
            }
            $config = getTimeConfig();
            $config['is_open'] = true;
            saveTimeConfig($config);
            echo json_encode(['success' => true, 'message' => '✅ تم فتح الموقع يدوياً', 'is_open' => true]);
            break;
            
        case 'set_close':
            $key = $_GET['key'] ?? '';
            if ($key !== ADMIN_KEY) {
                http_response_code(403);
                echo json_encode(['error' => 'Unauthorized']);
                break;
            }
            $config = getTimeConfig();
            $config['is_open'] = false;
            saveTimeConfig($config);
            echo json_encode(['success' => true, 'message' => '❌ تم إغلاق الموقع', 'is_open' => false]);
            break;
            
        case 'toggle':
            $key = $_GET['key'] ?? '';
            if ($key !== ADMIN_KEY) {
                http_response_code(403);
                echo json_encode(['error' => 'Unauthorized']);
                break;
            }
            $config = getTimeConfig();
            $config['is_open'] = !($config['is_open'] ?? false);
            saveTimeConfig($config);
            echo json_encode(['success' => true, 'is_open' => $config['is_open']]);
            break;
            
        case 'set_time':
            $key = $_GET['key'] ?? '';
            if ($key !== ADMIN_KEY) {
                http_response_code(403);
                echo json_encode(['error' => 'Unauthorized']);
                break;
            }
            $config = getTimeConfig();
            if (isset($_GET['match_start'])) {
                $config['match_start'] = $_GET['match_start'];
            }
            if (isset($_GET['match_end'])) {
                $config['match_end'] = $_GET['match_end'];
            }
            if (isset($_GET['qr_code'])) {
                $config['qr_code'] = $_GET['qr_code'];
            }
            saveTimeConfig($config);
            echo json_encode(['success' => true, 'message' => '✅ تم تحديث وقت المباراة']);
            break;
            
        case 'reset':
            $key = $_GET['key'] ?? '';
            if ($key !== ADMIN_KEY) {
                http_response_code(403);
                echo json_encode(['error' => 'Unauthorized']);
                break;
            }
            $config = getTimeConfig();
            $config['is_open'] = false;
            saveTimeConfig($config);
            echo json_encode(['success' => true, 'message' => '🔄 تم إعادة ضبط الموقع']);
            break;
            
        default:
            http_response_code(400);
            echo json_encode(['error' => 'Invalid action']);
            break;
    }
    exit;
}

// ════════════ AJAX Handler (طلبات الموقع) ═════════════════════════════════
if (isset($_GET['ajax'])) {
    header('Content-Type: application/json');
    $ip = getClientIP();
    
    if ($_GET['ajax'] === 'status') {
        $status = getMatchStatus();
        $blocked = isIPBlocked($ip);
        $stats = getIPStats($ip);
        $status['blocked'] = $blocked !== null;
        $status['blocked_remaining'] = $blocked;
        $status['ip_stats'] = $stats;
        echo json_encode($status);
        exit;
    }
    
    if ($_GET['ajax'] === 'stats') {
        echo json_encode(getIPStats($ip));
        exit;
    }
    
    if ($_GET['ajax'] === 'send_otp') {
        $blocked = isIPBlocked($ip);
        if ($blocked !== null) {
            echo json_encode([
                'success' => false, 
                'message' => '🚫 تم تجاوز عدد المحاولات. أعد المحاولة بعد ' . formatBlockTime($blocked),
                'blocked' => true,
                'remaining' => $blocked
            ]);
            exit;
        }
        
        $phone = $_POST['phone'] ?? '';
        $digits = preg_replace('/\D/', '', $phone);
        
        if (!preg_match('/^07\d{8}$/', $digits)) {
            echo json_encode(['success' => false, 'message' => '❌ رقم غير صحيح، يجب أن يبدأ بـ 07']);
            exit;
        }
        
        $msisdn = '213' . substr($digits, 1);
        $sessionId = session_id();
        $stats = getIPStats($ip);
        
        if ($stats['remaining'] <= 0) {
            echo json_encode([
                'success' => false,
                'message' => '🚫 استنفذت جميع المحاولات (5 في الساعة). أعد المحاولة بعد ساعة.',
                'blocked' => true
            ]);
            exit;
        }
        
        if (sendOTP($msisdn)) {
            setSession($sessionId, ['msisdn' => $msisdn, 'phone' => $digits, 'step' => 'otp', 'ip' => $ip]);
            echo json_encode([
                'success' => true, 
                'message' => "✅ تم إرسال الرمز إلى {$digits}",
                'remaining_attempts' => $stats['remaining'] - 1
            ]);
        } else {
            recordIPAttempt($ip, false, $digits);
            $newStats = getIPStats($ip);
            echo json_encode([
                'success' => false, 
                'message' => '❌ تعذر إرسال الرمز، تأكد من رقمك وحاول مجدداً',
                'remaining_attempts' => $newStats['remaining']
            ]);
        }
        exit;
    }
    
    if ($_GET['ajax'] === 'verify_otp') {
        $blocked = isIPBlocked($ip);
        if ($blocked !== null) {
            echo json_encode([
                'success' => false, 
                'message' => '🚫 تم تجاوز عدد المحاولات. أعد المحاولة بعد ' . formatBlockTime($blocked),
                'blocked' => true
            ]);
            exit;
        }
        
        $otp = $_POST['otp'] ?? '';
        $sessionId = session_id();
        $session = getSession($sessionId);
        
        if (empty($session['msisdn'])) {
            echo json_encode(['success' => false, 'message' => '❌ انتهت الجلسة، أعد المحاولة']);
            exit;
        }
        
        if (!preg_match('/^\d{6}$/', $otp)) {
            echo json_encode(['success' => false, 'message' => '❌ الرمز يجب أن يكون 6 أرقام']);
            exit;
        }
        
        $result = verifyOTP($session['msisdn'], $otp);
        
        if ($result === 'wrong_otp') {
            echo json_encode(['success' => false, 'message' => '❌ الرمز خاطئ، تأكد من الرمز المرسل']);
            exit;
        }
        if ($result === false) {
            echo json_encode(['success' => false, 'message' => '❌ حدث خطأ في التحقق، حاول مجدداً']);
            exit;
        }
        
        $session['access_token'] = $result['access_token'];
        $session['refresh_token'] = $result['refresh_token'];
        $session['step'] = 'activate';
        setSession($sessionId, $session);
        
        echo json_encode(['success' => true, 'message' => '✅ تم التحقق بنجاح']);
        exit;
    }
    
    if ($_GET['ajax'] === 'activate') {
        $blocked = isIPBlocked($ip);
        if ($blocked !== null) {
            echo json_encode([
                'success' => false, 
                'message' => '🚫 تم تجاوز عدد المحاولات. أعد المحاولة بعد ' . formatBlockTime($blocked),
                'blocked' => true
            ]);
            exit;
        }
        
        $sessionId = session_id();
        $session = getSession($sessionId);
        
        if (empty($session['msisdn']) || empty($session['access_token'])) {
            echo json_encode(['success' => false, 'message' => '❌ انتهت الجلسة، أعد المحاولة من البداية']);
            exit;
        }
        
        $config = getTimeConfig();
        $qrCode = $config['qr_code'] ?? 'https://www.djezzy.dz/scanwin-wd26?1';
        $result = activateGift($session['msisdn'], $session['access_token'], $qrCode);
        
        $phone = $session['phone'] ?? '';
        recordIPAttempt($ip, $result['success'], $phone);
        $stats = getIPStats($ip);
        $result['remaining_attempts'] = $stats['remaining'];
        $result['total_attempts'] = $stats['attempts'];
        $result['success_count'] = $stats['success'];
        $result['failed_count'] = $stats['failed'];
        $result['hourly'] = $stats['hourly'];
        
        if ($result['success']) {
            file_put_contents('/tmp/12go_success.log', date('Y-m-d H:i:s') . " IP:{$ip} PHONE:{$phone} SUCCESS\n", FILE_APPEND);
            clearSession($sessionId);
        } else {
            file_put_contents('/tmp/12go_failed.log', date('Y-m-d H:i:s') . " IP:{$ip} PHONE:{$phone} FAILED\n", FILE_APPEND);
        }
        
        echo json_encode($result);
        exit;
    }
    
    exit;
}

// ════════════ Page Display ═════════════════════════════════════════════════
$status = getMatchStatus();
$isOpen = $status['status'] === 'open';
$remaining = $status['remaining'] ?? 0;
$timeData = formatRemaining($remaining);
$ip = getClientIP();
$ipStats = getIPStats($ip);
$blocked = isIPBlocked($ip);
$isWaiting = $status['status'] === 'waiting';
$isClosed = $status['status'] === 'closed';
?>
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎁 هدية 12 جيقا - تفعيل مجاني</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', 'Tahoma', sans-serif;
            background: #0a0a1a;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
            background-image: 
                radial-gradient(ellipse at 20% 50%, rgba(251, 191, 36, 0.06) 0%, transparent 50%),
                radial-gradient(ellipse at 80% 50%, rgba(251, 191, 36, 0.03) 0%, transparent 50%);
        }
        .container {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(40px);
            border-radius: 32px;
            padding: 36px 32px;
            max-width: 480px;
            width: 100%;
            border: 1px solid rgba(255, 255, 255, 0.06);
            box-shadow: 0 40px 80px rgba(0, 0, 0, 0.6);
            position: relative;
            overflow: hidden;
        }
        .container::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(ellipse at 30% 20%, rgba(251, 191, 36, 0.03) 0%, transparent 60%);
            pointer-events: none;
        }

        .header { text-align: center; margin-bottom: 4px; position: relative; z-index: 1; }
        .header .badge {
            display: inline-block;
            background: rgba(251, 191, 36, 0.12);
            color: #fbbf24;
            padding: 4px 14px;
            border-radius: 100px;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
            border: 1px solid rgba(251, 191, 36, 0.1);
        }
        .header h1 { color: #fff; font-size: 26px; font-weight: 800; line-height: 1.2; }
        .header h1 span {
            background: linear-gradient(135deg, #fbbf24, #f59e0b);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .header p { color: #94a3b8; font-size: 13px; margin-top: 4px; }

        /* Timer */
        .timer-section { text-align: center; padding: 14px 0 10px; position: relative; z-index: 1; }
        .timer-section .label {
            color: #64748b;
            font-size: 11px;
            font-weight: 500;
            letter-spacing: 1px;
            text-transform: uppercase;
            margin-bottom: 6px;
        }
        .timer {
            display: flex;
            justify-content: center;
            gap: 6px;
            font-family: 'Inter', monospace;
        }
        .timer-item {
            background: rgba(255, 255, 255, 0.04);
            border-radius: 12px;
            padding: 8px 6px;
            min-width: 56px;
            border: 1px solid rgba(255, 255, 255, 0.04);
        }
        .timer-item .value {
            font-size: 28px;
            font-weight: 800;
            color: #fff;
            line-height: 1.1;
            display: block;
            font-variant-numeric: tabular-nums;
        }
        .timer-item .value.gold {
            background: linear-gradient(135deg, #fbbf24, #f59e0b);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .timer-item .unit { font-size: 10px; color: #64748b; font-weight: 500; display: block; margin-top: 2px; letter-spacing: 0.5px; }
        .timer-separator { color: #334155; font-size: 22px; font-weight: 300; display: flex; align-items: center; padding-bottom: 6px; }

        .timer-status {
            margin-top: 8px;
            font-size: 14px;
            font-weight: 500;
        }
        .timer-status.open { color: #4ade80; }
        .timer-status.waiting { color: #fbbf24; }
        .timer-status.closed { color: #f87171; }
        .timer-status .pulse-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-left: 6px;
            animation: pulse-dot 1.5s ease-in-out infinite;
        }
        .timer-status.open .pulse-dot { background: #4ade80; }
        .timer-status.waiting .pulse-dot { background: #fbbf24; }
        .timer-status.closed .pulse-dot { background: #f87171; }

        @keyframes pulse-dot {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.4; transform: scale(0.7); }
        }

        /* Gift Card */
        .gift-card {
            background: linear-gradient(135deg, rgba(251, 191, 36, 0.06), rgba(251, 191, 36, 0.01));
            border-radius: 16px;
            padding: 14px 16px;
            text-align: center;
            border: 1px solid rgba(251, 191, 36, 0.06);
            margin: 8px 0 14px;
            position: relative;
            z-index: 1;
        }
        .gift-card .details { display: flex; justify-content: center; gap: 24px; }
        .gift-card .details .item { display: flex; flex-direction: column; align-items: center; }
        .gift-card .details .item .value { color: #fbbf24; font-size: 15px; font-weight: 700; }
        .gift-card .details .item .label { color: #64748b; font-size: 11px; font-weight: 400; margin-top: 2px; }

        /* ===== PAGE CLOSED ===== */
        .closed-page {
            text-align: center;
            padding: 30px 0 20px;
            position: relative;
            z-index: 1;
        }
        .closed-page .icon { font-size: 56px; margin-bottom: 14px; }
        .closed-page h2 { color: #fbbf24; font-size: 24px; font-weight: 700; }
        .closed-page .sub {
            color: #94a3b8;
            font-size: 15px;
            margin-top: 6px;
        }
        .closed-page .time-box {
            margin-top: 18px;
            padding: 16px 24px;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.04);
        }
        .closed-page .time-box .row {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            color: #94a3b8;
            font-size: 14px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.03);
        }
        .closed-page .time-box .row:last-child { border-bottom: none; }
        .closed-page .time-box .row .label { color: #64748b; }
        .closed-page .time-box .row .value { color: #fff; font-weight: 500; }
        .closed-page .fb-link {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            margin-top: 18px;
            padding: 12px 28px;
            background: rgba(96, 165, 250, 0.06);
            border: 1px solid rgba(96, 165, 250, 0.1);
            border-radius: 12px;
            color: #60a5fa;
            text-decoration: none;
            font-size: 14px;
            transition: all 0.3s ease;
        }
        .closed-page .fb-link:hover {
            background: rgba(96, 165, 250, 0.1);
            border-color: rgba(96, 165, 250, 0.2);
        }
        .closed-page .note-box {
            margin-top: 16px;
            padding: 14px 18px;
            background: rgba(251, 191, 36, 0.05);
            border-radius: 12px;
            border: 1px solid rgba(251, 191, 36, 0.08);
        }
        .closed-page .note-box .title {
            color: #fbbf24;
            font-size: 13px;
            font-weight: 600;
            margin-bottom: 6px;
        }
        .closed-page .note-box p {
            color: #94a3b8;
            font-size: 13px;
            line-height: 1.6;
        }
        .closed-page .note-box .highlight {
            color: #fbbf24;
            font-weight: 600;
        }

        /* ===== APP (visible only when open) ===== */
        #app { position: relative; z-index: 1; }

        .form-group { margin-bottom: 14px; }
        .form-group label { display: block; color: #e2e8f0; font-size: 13px; margin-bottom: 6px; font-weight: 500; }
        .form-group input {
            width: 100%;
            padding: 14px 16px;
            border-radius: 12px;
            border: 2px solid rgba(255, 255, 255, 0.06);
            background: rgba(255, 255, 255, 0.04);
            color: #fff;
            font-size: 15px;
            transition: all 0.3s ease;
            outline: none;
            direction: ltr;
            font-family: 'Inter', sans-serif;
        }
        .form-group input:focus {
            border-color: #fbbf24;
            background: rgba(255, 255, 255, 0.06);
            box-shadow: 0 0 30px rgba(251, 191, 36, 0.04);
        }
        .form-group input::placeholder { color: #475569; }

        .btn {
            width: 100%;
            padding: 16px;
            border: none;
            border-radius: 12px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            color: #0a0a1a;
            background: linear-gradient(135deg, #fbbf24, #f59e0b);
            font-family: 'Inter', sans-serif;
            position: relative;
        }
        .btn:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 12px 40px rgba(251, 191, 36, 0.25); }
        .btn:active:not(:disabled) { transform: scale(0.98); }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none !important; }
        .btn-success { background: linear-gradient(135deg, #22c55e, #16a34a); color: #fff; }
        .btn-success:hover:not(:disabled) { box-shadow: 0 12px 40px rgba(34, 197, 94, 0.25); }
        .btn-glow { animation: glow-btn 2s ease-in-out infinite; }
        @keyframes glow-btn {
            0%, 100% { box-shadow: 0 0 20px rgba(251, 191, 36, 0.1); }
            50% { box-shadow: 0 0 40px rgba(251, 191, 36, 0.25); }
        }

        #alertContainer { position: relative; z-index: 2; }
        .alert {
            padding: 12px 16px;
            border-radius: 12px;
            margin-bottom: 12px;
            font-size: 13px;
            display: flex;
            align-items: center;
            gap: 10px;
            opacity: 0;
            transform: translateY(-10px);
            transition: all 0.4s ease;
        }
        .alert.show { opacity: 1; transform: translateY(0); }
        .alert-success { background: rgba(34, 197, 94, 0.12); border: 1px solid rgba(34, 197, 94, 0.15); color: #4ade80; }
        .alert-error { background: rgba(239, 68, 68, 0.12); border: 1px solid rgba(239, 68, 68, 0.15); color: #f87171; }
        .alert-info { background: rgba(96, 165, 250, 0.12); border: 1px solid rgba(96, 165, 250, 0.15); color: #60a5fa; }
        .alert-blocked { background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.2); color: #fca5a5; }

        .step-indicator { display: flex; justify-content: center; gap: 10px; margin-bottom: 10px; }
        .step-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #1e293b;
            transition: all 0.4s ease;
        }
        .step-dot.active { background: #fbbf24; box-shadow: 0 0 20px rgba(251, 191, 36, 0.2); }
        .step-dot.done { background: #22c55e; }
        .step-label { color: #94a3b8; font-size: 12px; text-align: center; margin-bottom: 14px; font-weight: 400; }
        .step-label .current { color: #fbbf24; font-weight: 600; }

        .phone-preview { color: #94a3b8; font-size: 13px; text-align: center; margin-bottom: 12px; }
        .phone-preview strong { color: #fff; }

        .resend-link {
            color: #60a5fa;
            font-size: 12px;
            cursor: pointer;
            text-decoration: underline;
            background: none;
            border: none;
            transition: color 0.2s;
        }
        .resend-link:hover { color: #93bbfc; }

        /* IP Stats */
        .ip-stats {
            display: flex;
            justify-content: center;
            gap: 16px;
            padding: 8px 0 12px;
            font-size: 12px;
            color: #64748b;
            position: relative;
            z-index: 1;
            border-top: 1px solid rgba(255, 255, 255, 0.03);
            margin-top: 4px;
            flex-wrap: wrap;
        }
        .ip-stats .stat { display: flex; align-items: center; gap: 4px; }
        .ip-stats .stat .num { color: #fff; font-weight: 600; }
        .ip-stats .stat .num.success { color: #4ade80; }
        .ip-stats .stat .num.failed { color: #f87171; }
        .ip-stats .stat .num.remaining { color: #fbbf24; }

        .blocked-banner {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.15);
            border-radius: 12px;
            padding: 12px 16px;
            text-align: center;
            color: #f87171;
            font-size: 13px;
            margin-bottom: 14px;
            position: relative;
            z-index: 1;
        }
        .blocked-banner strong { color: #fca5a5; }

        .footer {
            text-align: center;
            color: #334155;
            font-size: 11px;
            margin-top: 14px;
            padding-top: 12px;
            border-top: 1px solid rgba(255, 255, 255, 0.04);
            position: relative;
            z-index: 1;
        }
        .footer a { color: #60a5fa; text-decoration: none; transition: color 0.2s; }
        .footer a:hover { color: #93bbfc; }
        .footer .social { display: flex; justify-content: center; gap: 14px; margin-top: 4px; }
        .footer .social a { color: #475569; font-size: 12px; transition: color 0.2s; }
        .footer .social a:hover { color: #fbbf24; }

        .hidden { display: none !important; }
        .text-center { text-align: center; }

        .spinner {
            display: inline-block;
            width: 18px;
            height: 18px;
            border: 3px solid rgba(255, 255, 255, 0.2);
            border-top: 3px solid #fff;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            vertical-align: middle;
            margin-left: 8px;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

        .success-page { text-align: center; padding: 16px 0; }
        .success-page .big-icon { font-size: 56px; margin-bottom: 10px; }
        .success-page h2 { color: #4ade80; font-size: 22px; font-weight: 700; margin-bottom: 6px; }
        .success-page p { color: #94a3b8; font-size: 14px; }

        @media (max-width: 480px) {
            .container { padding: 20px 14px; }
            .header h1 { font-size: 22px; }
            .timer-item { min-width: 48px; padding: 6px 4px; }
            .timer-item .value { font-size: 22px; }
            .timer-separator { font-size: 16px; }
            .gift-card .details { gap: 14px; }
            .gift-card .details .item .value { font-size: 13px; }
            .closed-page .time-box .row { font-size: 12px; }
            .closed-page h2 { font-size: 20px; }
            .ip-stats { gap: 10px; font-size: 11px; }
        }
    </style>
</head>
<body>

<div class="container">
    <!-- Header -->
    <div class="header">
        <div class="badge">🎁 عرض محدود</div>
        <h1>هدية <span>12 جيقا</span></h1>
        <p>مجاناً لمتابعي مباراة الجزائر 🇩🇿</p>
    </div>

    <!-- Timer -->
    <div class="timer-section">
        <div class="label">⏱ الوقت المتبقي للتفعيل</div>
        <div class="timer" id="timer">
            <div class="timer-item">
                <span class="value gold" id="timer-hours"><?php echo sprintf('%02d', $timeData['hours']); ?></span>
                <span class="unit">ساعات</span>
            </div>
            <span class="timer-separator">:</span>
            <div class="timer-item">
                <span class="value gold" id="timer-minutes"><?php echo sprintf('%02d', $timeData['minutes']); ?></span>
                <span class="unit">دقائق</span>
            </div>
            <span class="timer-separator">:</span>
            <div class="timer-item">
                <span class="value gold" id="timer-seconds"><?php echo sprintf('%02d', $timeData['seconds']); ?></span>
                <span class="unit">ثواني</span>
            </div>
        </div>
        <div class="timer-status <?php echo $status['status']; ?>" id="statusText">
            <span class="pulse-dot"></span>
            <?php echo $status['message']; ?>
        </div>
    </div>

    <!-- Gift Card -->
    <div class="gift-card">
        <div class="details">
            <div class="item"><span class="value">12GB</span><span class="label">حجم الباقة</span></div>
            <div class="item"><span class="value">5 ساعات</span><span class="label">مدة الصلاحية</span></div>
            <div class="item"><span class="value">🎁</span><span class="label">مجاناً</span></div>
        </div>
    </div>

    <?php if ($isClosed || $isWaiting): ?>
        <!-- ===== الموقع مغلق أو في انتظار الفتح ===== -->
        <div class="closed-page">
            <div class="icon"><?php echo $isWaiting ? '⏳' : '⏰'; ?></div>
            <h2><?php echo $isWaiting ? '⏳ يبدأ قريباً' : '⏰ الموقع مغلق حالياً'; ?></h2>
            <p class="sub">
                <?php echo $isWaiting ? 'الموقع سيفتح تلقائياً عند موعد المباراة' : 'عودة في مباراة الجزائر القادمة'; ?>
            </p>
            
            <div class="time-box">
                <div class="row">
                    <span class="label">📅 تاريخ المباراة</span>
                    <span class="value"><?php echo isset($status['start']) ? date('d F Y', strtotime($status['start'])) : '3 جويلية 2026'; ?></span>
                </div>
                <div class="row">
                    <span class="label">🕐 وقت البدء</span>
                    <span class="value"><?php echo isset($status['start']) ? date('01:00', strtotime($status['start'])) . ' صباحاً' : '01:00 صباحاً'; ?></span>
                </div>
                <div class="row">
                    <span class="label">🕐 وقت الانتهاء</span>
                    <span class="value"><?php echo isset($status['end']) ? date('H:i', strtotime($status['end'])) . ' صباحاً' : '05:00 صباحاً'; ?></span>
                </div>
                <div class="row">
                    <span class="label">⏱ المدة المتبقية</span>
                    <span class="value" style="color:#fbbf24;">
                        <?php 
                            if ($remaining > 0) {
                                echo sprintf('%02d', $timeData['hours']) . ' ساعة ' . 
                                     sprintf('%02d', $timeData['minutes']) . ' دقيقة ' . 
                                     sprintf('%02d', $timeData['seconds']) . ' ثانية';
                            } else {
                                echo 'انتهى الوقت';
                            }
                        ?>
                    </span>
                </div>
            </div>

            <!-- ملاحظة عن المحاولات -->
            <div class="note-box">
                <div class="title">📌 ملاحظة مهمة</div>
                <p>
                    عند فتح الموقع، يُسمح لكل IP بـ <span class="highlight">5 محاولات</span> في الساعة الواحدة 
                    (5 أرقام مختلفة أو 5 محاولات تفعيل).<br>
                    بعد 5 محاولات، سيتم <span class="highlight">تقييد IP لمدة ساعة</span> كاملة.
                </p>
            </div>

            <a href="https://www.facebook.com/tasjilbot" target="_blank" class="fb-link">
                📱 تابعنا على فيسبوك
            </a>
        </div>

    <?php else: ?>
        <!-- ===== الموقع مفتوح ===== -->
        
        <!-- IP Stats -->
        <div class="ip-stats">
            <span class="stat">📊 المحاولات: <span class="num"><?php echo $ipStats['attempts']; ?></span></span>
            <span class="stat">✅ نجاح: <span class="num success"><?php echo $ipStats['success']; ?></span></span>
            <span class="stat">❌ فشل: <span class="num failed"><?php echo $ipStats['failed']; ?></span></span>
            <span class="stat">⏳ متبقي: <span class="num remaining"><?php echo max(0, MAX_ATTEMPTS - $ipStats['hourly']); ?></span></span>
        </div>

        <!-- Blocked Banner -->
        <?php if ($blocked !== null): ?>
        <div class="blocked-banner" id="blockedBanner">
            🚫 تم تجاوز عدد المحاولات المسموح بها (5 في الساعة).<br>
            <strong>⏳ أعد المحاولة بعد: <span id="blockTimer"><?php echo formatBlockTime($blocked); ?></span></strong>
        </div>
        <?php endif; ?>

        <!-- Alert Container -->
        <div id="alertContainer"></div>

        <!-- App Content -->
        <div id="app">
            <!-- Step 1: Phone -->
            <div id="stepForm">
                <div class="step-indicator">
                    <span class="step-dot active" id="dot1"></span>
                    <span class="step-dot" id="dot2"></span>
                    <span class="step-dot" id="dot3"></span>
                </div>
                <div class="step-label" id="stepLabel">الخطوة <span class="current">1</span> من 3: أدخل رقم هاتفك</div>

                <form id="formPhone" onsubmit="return sendOTP()">
                    <div class="form-group">
                        <label>📱 رقم الهاتف (جيزي)</label>
                        <input type="tel" id="phoneInput" placeholder="مثال: 0770000000" required maxlength="10" autocomplete="off">
                    </div>
                    <button type="submit" class="btn btn-glow" id="btnSendOTP">📲 إرسال رمز التحقق</button>
                </form>
            </div>

            <!-- Step 2: OTP -->
            <div id="stepOTP" style="display:none;">
                <div class="step-indicator">
                    <span class="step-dot done" id="dot1b"></span>
                    <span class="step-dot active" id="dot2b"></span>
                    <span class="step-dot" id="dot3b"></span>
                </div>
                <div class="step-label">الخطوة <span class="current">2</span> من 3: تأكيد الرمز</div>
                
                <div class="phone-preview">📱 تم إرسال الرمز إلى: <strong id="phoneDisplay"></strong></div>

                <form id="formOTP" onsubmit="return verifyOTP()">
                    <div class="form-group">
                        <label>🔢 رمز التحقق (6 أرقام)</label>
                        <input type="text" id="otpInput" placeholder="أدخل الرمز" required maxlength="6" pattern="[0-9]{6}" autocomplete="off">
                    </div>
                    <button type="submit" class="btn btn-success" id="btnVerifyOTP">✅ تأكيد الرمز</button>
                </form>

                <div style="text-align: center; margin-top: 12px;">
                    <button class="resend-link" onclick="resendOTP()">🔄 لم يصلك الرمز؟ أعد الإرسال</button>
                </div>
            </div>

            <!-- Step 3: Activate -->
            <div id="stepActivate" style="display:none;">
                <div class="step-indicator">
                    <span class="step-dot done" id="dot1c"></span>
                    <span class="step-dot done" id="dot2c"></span>
                    <span class="step-dot active" id="dot3c"></span>
                </div>
                <div class="step-label">الخطوة <span class="current">3</span> من 3: تفعيل الهدية</div>

                <div class="phone-preview">📱 الرقم: <strong id="phoneDisplay2"></strong></div>

                <div id="activateInfo" class="alert alert-info show">
                    🎁 اضغط على الزر لتفعيل 12 جيقا مجاناً
                </div>

                <button type="button" class="btn btn-success btn-glow" id="btnActivate" onclick="activateGift()">🎁 تفعيل الهدية الآن</button>

                <div style="text-align: center; margin-top: 12px;">
                    <a href="#" onclick="resetForm(); return false;" style="color: #64748b; font-size: 12px; text-decoration: underline;">↺ العودة للبداية</a>
                </div>
            </div>

            <!-- Success -->
            <div id="stepSuccess" style="display:none;">
                <div class="success-page">
                    <div class="big-icon">🎉</div>
                    <h2>تم التفعيل بنجاح!</h2>
                    <p>لقد حصلت على 12 جيقا إنترنت مجاناً 🎁</p>
                    <p style="color: #64748b; font-size: 13px; margin-top: 4px;">استمتع بالمباراة 🇩🇿⚽</p>
                    
                    <div style="margin-top: 18px;">
                        <a href="#" onclick="resetForm(); return false;" class="btn" style="display: inline-block; width: auto; padding: 12px 32px; text-decoration: none;">🔄 تفعيل لحساب آخر</a>
                    </div>
                </div>
            </div>
        </div>
    <?php endif; ?>

    <!-- Footer -->
    <div class="footer">
        <p>⚡ بوت Tasjil | <a href="https://t.me/tasjilbott" target="_blank">قناة التلغرام</a></p>
        <div class="social">
            <a href="https://www.facebook.com/tasjilbot" target="_blank">📘 فيسبوك</a>
            <a href="https://t.me/tasjilbott" target="_blank">✈️ تلغرام</a>
        </div>
    </div>
</div>

<script>
// ===== Timer =====
let remaining = <?php echo $remaining; ?>;
const isOpen = <?php echo $isOpen ? 'true' : 'false'; ?>;
let blockedRemaining = <?php echo $blocked ?? 0; ?>;

function updateTimer() {
    if (remaining <= 0) return;
    const h = Math.floor(remaining / 3600);
    const m = Math.floor((remaining % 3600) / 60);
    const s = remaining % 60;
    document.getElementById('timer-hours').textContent = String(h).padStart(2, '0');
    document.getElementById('timer-minutes').textContent = String(m).padStart(2, '0');
    document.getElementById('timer-seconds').textContent = String(s).padStart(2, '0');
    remaining--;
}

if (remaining > 0) setInterval(updateTimer, 1000);

// ===== Block Timer =====
function updateBlockTimer() {
    if (blockedRemaining > 0) {
        const h = Math.floor(blockedRemaining / 3600);
        const m = Math.floor((blockedRemaining % 3600) / 60);
        const s = blockedRemaining % 60;
        let text = '';
        if (h > 0) text += h + ' ساعة ';
        if (m > 0) text += m + ' دقيقة ';
        if (s > 0 || (h === 0 && m === 0)) text += s + ' ثانية';
        const el = document.getElementById('blockTimer');
        if (el) el.textContent = text.trim();
        blockedRemaining--;
    }
}

if (blockedRemaining > 0) setInterval(updateBlockTimer, 1000);

// ===== Check Status =====
function checkStatus() {
    fetch('?ajax=status')
        .then(r => r.json())
        .then(data => {
            const shouldBeOpen = data.status === 'open';
            if (shouldBeOpen !== isOpen) {
                location.reload();
            }
        })
        .catch(() => {});
}
setInterval(checkStatus, 30000);

<?php if ($isOpen): ?>
// ===== App Functions =====
let currentPhone = '';

function showAlert(message, type = 'error') {
    const container = document.getElementById('alertContainer');
    const cls = type === 'success' ? 'alert-success' : (type === 'blocked' ? 'alert-blocked' : 'alert-error');
    container.innerHTML = `<div class="alert ${cls} show">${message}</div>`;
    setTimeout(() => {
        const el = container.querySelector('.alert');
        if (el) el.classList.remove('show');
        setTimeout(() => container.innerHTML = '', 400);
    }, 5000);
}

function setLoading(btn, loading = true) {
    if (loading) {
        btn.disabled = true;
        btn.dataset.original = btn.innerHTML;
        btn.innerHTML = '<span class="spinner"></span> جاري ...';
    } else {
        btn.disabled = false;
        btn.innerHTML = btn.dataset.original || btn.textContent;
    }
}

function sendOTP() {
    const phone = document.getElementById('phoneInput').value.trim();
    const btn = document.getElementById('btnSendOTP');
    btn.dataset.original = btn.innerHTML;
    setLoading(btn, true);
    
    const formData = new FormData();
    formData.append('phone', phone);
    
    fetch('?ajax=send_otp', { method: 'POST', body: formData })
        .then(r => r.json())
        .then(data => {
            setLoading(btn, false);
            if (data.success) {
                currentPhone = phone;
                document.getElementById('phoneDisplay').textContent = phone;
                document.getElementById('stepForm').style.display = 'none';
                document.getElementById('stepOTP').style.display = 'block';
                document.getElementById('otpInput').focus();
                showAlert(data.message, 'success');
                updateStats();
            } else {
                if (data.blocked) {
                    showAlert(data.message, 'blocked');
                    setTimeout(() => location.reload(), 3000);
                } else {
                    showAlert(data.message, 'error');
                }
                updateStats();
            }
        })
        .catch(() => {
            setLoading(btn, false);
            showAlert('❌ حدث خطأ في الاتصال', 'error');
        });
    return false;
}

function verifyOTP() {
    const otp = document.getElementById('otpInput').value.trim();
    const btn = document.getElementById('btnVerifyOTP');
    btn.dataset.original = btn.innerHTML;
    setLoading(btn, true);
    
    const formData = new FormData();
    formData.append('otp', otp);
    
    fetch('?ajax=verify_otp', { method: 'POST', body: formData })
        .then(r => r.json())
        .then(data => {
            setLoading(btn, false);
            if (data.success) {
                document.getElementById('stepOTP').style.display = 'none';
                document.getElementById('stepActivate').style.display = 'block';
                document.getElementById('phoneDisplay2').textContent = currentPhone;
                showAlert(data.message, 'success');
            } else {
                if (data.blocked) {
                    showAlert(data.message, 'blocked');
                    setTimeout(() => location.reload(), 3000);
                } else {
                    showAlert(data.message, 'error');
                }
            }
        })
        .catch(() => {
            setLoading(btn, false);
            showAlert('❌ حدث خطأ في الاتصال', 'error');
        });
    return false;
}

function resendOTP() {
    const btn = document.querySelector('.resend-link');
    btn.textContent = '⏳ جاري ...';
    btn.disabled = true;
    
    const formData = new FormData();
    formData.append('phone', currentPhone);
    
    fetch('?ajax=send_otp', { method: 'POST', body: formData })
        .then(r => r.json())
        .then(data => {
            btn.textContent = '🔄 لم يصلك الرمز؟ أعد الإرسال';
            btn.disabled = false;
            if (data.success) {
                showAlert(data.message, 'success');
            } else {
                showAlert(data.message, 'error');
            }
        })
        .catch(() => {
            btn.textContent = '🔄 لم يصلك الرمز؟ أعد الإرسال';
            btn.disabled = false;
            showAlert('❌ حدث خطأ', 'error');
        });
}

function activateGift() {
    const btn = document.getElementById('btnActivate');
    btn.dataset.original = btn.innerHTML;
    setLoading(btn, true);
    
    fetch('?ajax=activate', { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            setLoading(btn, false);
            if (data.success) {
                document.getElementById('stepActivate').style.display = 'none';
                document.getElementById('stepSuccess').style.display = 'block';
                showAlert(data.message, 'success');
                updateStats();
            } else {
                if (data.blocked) {
                    showAlert(data.message, 'blocked');
                    setTimeout(() => location.reload(), 3000);
                } else {
                    showAlert(data.message, 'error');
                }
                updateStats();
            }
        })
        .catch(() => {
            setLoading(btn, false);
            showAlert('❌ حدث خطأ في الاتصال', 'error');
        });
}

function updateStats() {
    fetch('?ajax=stats')
        .then(r => r.json())
        .then(data => {
            const stats = document.querySelector('.ip-stats');
            if (stats) {
                stats.innerHTML = `
                    <span class="stat">📊 المحاولات: <span class="num">${data.attempts}</span></span>
                    <span class="stat">✅ نجاح: <span class="num success">${data.success}</span></span>
                    <span class="stat">❌ فشل: <span class="num failed">${data.failed}</span></span>
                    <span class="stat">⏳ متبقي: <span class="num remaining">${data.remaining}</span></span>
                `;
            }
        })
        .catch(() => {});
}

function resetForm() {
    document.getElementById('stepForm').style.display = 'block';
    document.getElementById('stepOTP').style.display = 'none';
    document.getElementById('stepActivate').style.display = 'none';
    document.getElementById('stepSuccess').style.display = 'none';
    document.getElementById('phoneInput').value = '';
    document.getElementById('otpInput').value = '';
    document.getElementById('alertContainer').innerHTML = '';
    
    document.querySelectorAll('.step-dot').forEach(el => {
        el.className = 'step-dot';
    });
    document.getElementById('dot1').className = 'step-dot active';
}

document.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
        const active = document.activeElement;
        if (active && active.id === 'phoneInput') {
            e.preventDefault();
            sendOTP();
        }
        if (active && active.id === 'otpInput') {
            e.preventDefault();
            verifyOTP();
        }
    }
});
<?php endif; ?>
</script>

</body>
</html>

<?php
// صفحة بث قناة النهار TV
?>
<!DOCTYPE html>
<html lang="ar">
<head>
    <meta charset="UTF-8">
    <title>بث مباشر قناة النهار TV</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            margin: 0;
            background: #000;
            font-family: Arial, sans-serif;
        }
        .player {
            width: 100%;
            height: 100vh;
        }
        iframe {
            width: 100%;
            height: 100%;
            border: none;
        }
    </style>
</head>
<body>

<div class="player">
    <iframe 
        src="https://www.elahmad.com/tv/ennaharonline.php"
        allowfullscreen
        allow="autoplay; encrypted-media">
    </iframe>
</div>

</body>
</html>

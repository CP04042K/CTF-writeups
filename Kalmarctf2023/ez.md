## Ez
- Trong source code thì ta chỉ cần quan tâm Caddyfile, Dockerfile và index.php
- Đọc file index.php trước thì thấy nó đang cố gắng đọc file flag.txt ra
```php 
<?php

echo "I can't get this to work :/";
echo system("cat flag.txt");

?>
```
- Khi truy cập vào http://php.caddy.chal-kalmarc.tf/index.php thì thấy nó không thực thi, http://php.caddy.chal-kalmarc.tf/flag.txt thì bị 403
- Chuyển qua đọc Caddy file thì để ý trong mục config của `*.caddy.chal-kalmarc.tf` đã chặn việc truy cập vào `/flag.txt` bằng cách trả về 403 mỗi khi truy cập.
```
respond /flag.txt 403
```
- File `index.php` không thực thi là vì đoạn chuyển handling cho php cgi đã bị comment, caddy là một go server nên nó sẽ không support php by default
```
#php.caddy.chal-kalmarc.tf {
#    php_fastcgi localhost:9000
#}
```
- Nếu block `/flag.txt` thì liệu `/./flag.txt` sẽ thế nào nhỉ? (một số HTTP parser sẽ hiểu `.` là đại diện cho thư mục hiện tại, nên sau khi xử lý thì `/./flag.txt` sẽ thành `/flag.txt`):
![](https://i.imgur.com/ilmxmsu.png)
- 404, nhưng nếu thử với `/./index.php` thì vẫn trả về, vậy nghĩa là flag.txt đã bị xóa, lúc này đến lúc đọc Dockerfile. Sau khi đọc kỹ sẽ đến đoạn này:
```dockerfile!
mkdir -p backups/ && cp -r *.caddy.chal-kalmarc.tf backups/ && rm php.caddy.chal-kalmarc.tf/flag.txt
```
- Khi deploy thì tạo thư mục `backups`, chuyển toàn bộ file từ các thư mục `*.caddy.chal-kalmarc.tf` vào `backups` và xóa file flag.txt
- Vậy là `flag.txt` giờ nằm trong thư mục `/backups/php.caddy.chal-kalmarc.tf/`. Làm sao ta truy cập được nó?
- Ban đầu còn một đoạn trong Caddyfile nữa:
```
file_server {
        root /srv/{host}/
    }
```
- Ở đây theo documentation thì {host} là thông tin lấy từ header `Host` trong http request. `{host}` được nối vào `/srv/` để làm root document. Có vẻ như các root document folders và cả backups đều nằm trong srv, vậy ta có thể đổi giá trị của `Host` thành `backups/php.caddy.chal-kalmarc.tf`, nó sẽ đúng với rule `*.caddy.chal-kalmarc.tf` trong Caddyfile, giúp ta tới được folder `backups/php.caddy.chal-kalmarc.tf`, kết hợp với `/./flag.txt` ta được flag: `kalmar{th1s-w4s-2x0d4ys-wh3n-C4ddy==2.4}`
![](https://i.imgur.com/TtRE89X.png)

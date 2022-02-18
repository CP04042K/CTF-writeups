Challenge: http://rce-me.ctf.actvn.edu.vn/

![image](https://user-images.githubusercontent.com/35491855/154733589-8e729f8d-73a0-4107-b3bc-e77978980ed7.png)

From the begining, the challenge show us that this website is vulnerable to LFI, but the challenge requires us to find and exploit a RCE, and the `etc/passwd` clearly doesn't play any role here. There are a couple of methods to lead to RCE from LFI, i'm not going to cover all of them in this writeup.

First i tried to use `dirsearch` to check for any interesting file or path, but no hope tho. After that, i read the hint that said `I am using php-fpm alpine docker`, so i tried to find an image, deployed it to docker and inspected the file structure in order to find the "key" but still. After countless attempts, i tried to use some other technique like **php wrapper** and found out that i can read the source of the index page - which gave me the hint to figure out the way to solve this challenge.

![image](https://user-images.githubusercontent.com/35491855/154734280-d1266dd8-b760-4b78-a533-888e6942422f.png)

`http://rce-me.ctf.actvn.edu.vn/?l=php://filter/convert.base64-encode/resource=index.php`

Decoding the base64 message we got the php source code of the `index.php` file

![image](https://user-images.githubusercontent.com/35491855/154734897-0ab4f52c-4a94-4bec-80c8-71a758519df3.png)

Noticing this part:


>$_SESSION['name'] = @$_GET["name"];
>
>$l = @$_GET['l'];
>
>?if ($l) include $l;


First it will assign the data taken from the `name` parameter to the `name` attribute in **SESSION**, and then the LFI part. The first line of the below code is very valuable as it reveal the way to turn a LFI into a RCE. By providing a PHP code to the `name` parameter and include the SESSION file locating somewhere on the server, we can execute arbitrary PHP code and get the flag.

![image](https://user-images.githubusercontent.com/35491855/154736202-26bdc87a-b179-4ef2-b8a6-188f245117f4.png)

`http://rce-me.ctf.actvn.edu.vn/?l=/tmp/sess_qv2vse3ful8lk9na2irrovsf38&name=<?php system("ls");?>`

You can find the `/tmp/sess_qv2vse3ful8lk9na2irrovsf38` by combining the `sess_` and the `SESSION_ID` that the server sent you earlier, tmp is usually the location which store all the SESSION.

Now the last thing is quite simple, read the flag file.

![image](https://user-images.githubusercontent.com/35491855/154736780-450e26ff-7ccb-4bb1-9cdd-b4ff3110c14d.png)

`FLAG: KMACTF{Do_anh_session_duoc_em_hihi}`

# CORCTF 2023 writeup

## force
Source của bài khá ngắn, ta cần sử dụng graphql để get flag, điều kiện là biết được số nguyên `secret` được random từ 0->100k

Ta sẽ thực hiện bruteforce secret bằng cách sử dụng alias của graphql, invoke nhiều query get flag cùng lúc với các mã pin khác nhau từ 0->100k, ta có thể chia ra từng đợt để request bớt dài.

![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/71971455-a6b3-4ae8-99ed-5865544f9494)

`corctf{S                T                  O               N                   K                 S}`
## msfrognymize
Source code nhìn khá căng, thực chất bug nằm ở route `/anonymized/<image_file>`, ta có thể request với `image_file` là `%252fflag.txt`, input sẽ được decode url sau đó join `uploads/` và `/flag.txt` lại thì output cuối cùng sẽ là `/flag`

`https://msfrognymize.be.ax/anonymized/%252fflag.txt`

`corctf{Fr0m_Priv4cy_t0_LFI}`

## frogshare
Flag nằm ở localStorage của bot, chức năng trang web là cho phép ta load một cái SVG về và nội dung của SVG sẽ được insert vào DOM tree, tuy nhiên nếu tồn tại thẻ script trong SVG thì sẽ bị strip đi. 

![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/1940159d-58b4-4897-b54c-6aed2b6eba7f)

trace lên bên trên ta sẽ thấy biến n thật ra là alias của của một biến tên là `enableJs`, cái tên đã cho ta biết vai trò của nó, vì minified js khá khó đọc, để tìm ra đoạn code này nằm ở đâu mình thử search tên biến `enableJs svg` lên github (thực chất bạn có thể xem ở package.json nhưng đây là cách tiếp cận ban đầu của mình)

![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/2820430e-e05f-4ab8-b963-fa8082d03800)

Có vẻ như là thứ ta cần, vào source code đọc thử thì thấy `enableJs` được lấy từ props của component

![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/3d4d72d9-0365-4bc3-96d4-687c4d92b5ef)

xem lại source code ta thấy được ta có thể kiểm soát được props truyền vào component

![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/119c3ea7-e14a-4b27-8c7e-8811ca57e74f)

Vậy chỉ cần thêm `"data-js":"enable"` lúc tạo frog là được

![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/5095e714-42a9-458a-9f6f-476487d6803b)

![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/744bc9c5-b430-4b77-88c8-a26822167aa7)

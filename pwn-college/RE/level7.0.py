#!/bin/python
from random import shuffle
import string 

content = "fa f8 f7 f4 f1 ec e8 e7 e1 e1 3e 34 31 31 30 2e 2d 28 21 1a 15 13 0f 0c 0b 09 08 08 02"
content = content.split(" ")
original = [""]*29
pos = []
# content.reverse()
i = 0
buf_len = len(content)
for each in content:
    this_char = ""
    while i < 29:
        factor = i % 3
        if factor == 2:
            this_char = chr(int("0x" + each, 16) ^ 0x47)
        elif factor < 3:
            if factor == 0:
                this_char = chr(int("0x" + each, 16) ^ 0x80)
            elif factor == 1:
                this_char = chr(int("0x" + each, 16) ^ 99)
        if this_char in string.printable and i not in pos:
            original[i] = this_char
            pos.append(i)
            break
        i += 1
    i = 0
    

print("".join(original))

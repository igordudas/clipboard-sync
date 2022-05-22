#!/usr/bin/env python
import Tkinter as tk

import sys
import threading
import socket
import collections

DELAY = 500
CLIENT_PORT = SERVER_PORT = 6666


new_content = None
nc_lock = threading.Lock()

output_socket = None

def read_input_socket(sock):
    global new_content
    length = 0
    len_str = ''
    incoming = ''

    while True:
        char = sock.recv(1)
        # TODO: handle closing of connection
        if 48 <= ord(char) <= 57:
            len_str += char
        elif char == ',':
            length = int(len_str)
            len_str = ''
            incoming = sock.recv(length)
            # TODO: handle closing of connection

            nc_lock.acquire()
            new_content = incoming.decode('utf-8', 'replace')
            nc_lock.release()
        else:
            raise Exception('Length input contains illegal character: ' + char + '\n')


def send_socket(unicode_msg):
    msg = unicode_msg.encode('utf-8')
    msg = str(len(msg)) + ',' + msg
    output_socket.send(msg)

# not thread-safe because of shared deque!
def read_unicode_char(read, leftover=collections.deque()):
    if leftover:
        return leftover.popleft()

    charstr = ''
    nextchar = ''
    unichar = u''

    # read bytes, until they form a valid utf-8 character
    while not unichar:
        nextchar = read(1)
        if not nextchar:
            if charstr: raise Exception('Input ended unexpectedly.')
            else:       return u''

        charstr += nextchar
        unichar = charstr.decode('utf-8', 'ignore')

    unichar = charstr.decode('utf-8', 'replace')
    if len(unichar) > 1:
        leftover.extend(unichar[1:])
    return unichar[0]

def read_input_stdin():
    global new_content
    incoming = ''
    slash = False
    while True:
        next_char = read_unicode_char(sys.stdin.read)
        if not next_char:
            break
        #sys.stderr.write('I: "' + next_char.encode('utf-8') + '"\n')

        if slash:
            if next_char == u'0':
                # input complete
                nc_lock.acquire()
                new_content = incoming
                nc_lock.release()
                incoming = u''
                slash = False
            elif next_char == u' ':
                incoming += u'/'
                slash = False
            else:
                incoming += u'/' + next_char
                slash = False
        else:
            if next_char == u'/':
                slash = True
            else:
                incoming += next_char

def send_stdout(unicode_msg):
    msg = (unicode_msg.replace('/', '/ ') + '/0') . encode('utf-8')
    sys.stdout.write(msg)
    sys.stdout.flush()


def process_clipboard():
    global new_content
    global current

    root.after(DELAY, process_clipboard)

    with nc_lock:
        if new_content is not None:
            root.clipboard_clear()
            root.clipboard_append(new_content)
            # do not send new content back over socket
            current, new_content = new_content, None
            return

    tmp = root.clipboard_get(type='UTF8_STRING')
    if tmp != current:
        send(tmp)
        current = tmp


root = tk.Tk()
root.withdraw()
current = root.clipboard_get(type='UTF8_STRING')

# stdin/stdout
#th = threading.Thread(target=read_input_stdin)
#th.start()
#send = send_stdout
#send(current)

# socket
send = send_socket
if len(sys.argv) < 2:
    sys.stderr.write('specify server/client as command line argument\n')
    sys.exit()

if sys.argv[1] == 'server':
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.bind(('localhost', SERVER_PORT))
    serversocket.listen(1)

    clientsocket, adress = serversocket.accept()
    th = threading.Thread(target=read_input_socket, args=(clientsocket,))
    th.daemon = True
    th.start()
    output_socket = clientsocket
elif sys.argv[1] == 'client':
    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientsocket.connect(('localhost', CLIENT_PORT))
    th = threading.Thread(target=read_input_socket, args=(clientsocket,))
    th.daemon = True
    th.start()
    output_socket = clientsocket

    send(current)
else:
    sys.stderr.write('specify server/client as command line argument\n')
    sys.exit()


root.after(DELAY, process_clipboard)
root.mainloop()

#!/usr/bin/env python3
import tkinter as tk

import sys
import threading
import socket
import collections

DELAY = 500



new_content = None
nc_lock = threading.Lock()
current = None


def quit_program(fn):
    # decorator to close everything down when fn() ends
    def new_fn(*args, **kwargs):
        try:
            fn(*args, **kwargs)
        except KeyboardInterrupt:
            pass
        finally:
            conn.close()
            root.destroy()
    return new_fn

class SocketConnection:
    CLIENT_PORT = SERVER_PORT = 6666
    
    def __init__(self, conn_type):
        self.client_socket = None
        self.server_socket = None

        if conn_type == 'server':
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind(('localhost', SocketConnection.SERVER_PORT))
            self.server_socket.listen(1)
            self.client_socket, _ = self.server_socket.accept()
        elif conn_type == 'client':
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect(('localhost', SocketConnection.CLIENT_PORT))
        else:
            raise ValueError('conn_type has to be either "server" or "client"')

    def close(self):
        if self.client_socket is not None:
            self.client_socket.shutdown(socket.SHUT_RDWR)
            self.client_socket.close()
            self.client_socket = None
        if self.server_socket is not None:
            self.server_socket.shutdown(socket.SHUT_RDWR)
            self.server_socket.close()
            self.server_socket = None
    
    def read_loop(self):
        global new_content
        length = 0
        len_str = ''
        incoming_bytes = b''

        while True:
            b_char = self.client_socket.recv(1)
            char = b_char.decode('ascii', 'strict')

            if char == '':
                sys.stderr.write('Connection closed\n')
                return

            if 48 <= ord(char) <= 57:
                len_str += char
            elif char == ',':
                length = int(len_str)
                len_str = ''
                incoming_bytes = self.client_socket.recv(length)
                if len(incoming_bytes) < length:
                    sys.stderr.write('Connection closed\n')
                    return

                nc_lock.acquire()
                new_content = incoming_bytes.decode('utf-8', 'replace')
                nc_lock.release()
            else:
                raise Exception('Length input contains illegal character: ' + char + '\n')

    def send(self, unicode_msg):
        msg_bytes = unicode_msg.encode('utf-8')
        len_str = str(len(msg_bytes)) + ','
        msg_bytes = len_str.encode('ascii', 'strict') + msg_bytes
        self.client_socket.send(msg_bytes)


class StdIOConnection:
    def close(self):
        pass
    
    def read_unicode_char_internal(self, leftover=collections.deque()):
        if leftover:
            return leftover.popleft()

        stdin = sys.stdin.buffer # so we can read bytes instead of string
        charstr = b''
        nextchar = b''
        unichar = ''


        # read bytes, until they form a valid utf-8 character
        while not unichar:
            nextchar = stdin.read(1)
            if not nextchar:
                if charstr: raise Exception('Input ended unexpectedly.')
                else:       return ''

            charstr += nextchar
            unichar = charstr.decode('utf-8', 'ignore')

        unichar = charstr.decode('utf-8', 'replace')
        if len(unichar) > 1:
            leftover.extend(unichar[1:])
        return unichar[0]
    
    def read_loop(self):
        global new_content
        incoming = ''
        slash = False
        while True:
            next_char = self.read_unicode_char_internal()
            if not next_char:
                break

            if slash:
                if next_char == '0':
                    # input complete
                    nc_lock.acquire()
                    new_content = incoming
                    nc_lock.release()
                    incoming = ''
                    slash = False
                elif next_char == ' ':
                    incoming += '/'
                    slash = False
                else:
                    incoming += '/' + next_char
                    slash = False
            else:
                if next_char == '/':
                    slash = True
                else:
                    incoming += next_char
    
    def send(self, unicode_msg):
        msg = (unicode_msg.replace('/', '/ ') + '/0') . encode('utf-8')
        sys.stdout.write(msg)
        sys.stdout.flush()


def read_clipboard():
    try:
        return root.clipboard_get(type='UTF8_STRING')
    except:
        return ''


def process_clipboard():
    global new_content
    global current
    global conn

    root.after(DELAY, process_clipboard)

    with nc_lock:
        if new_content is not None:
            root.clipboard_clear()
            root.clipboard_append(new_content)
            # do not send new content back over socket
            current, new_content = new_content, None
            return

    tmp = read_clipboard()
    if tmp != current:
        conn.send(tmp)
        current = tmp


root = tk.Tk()
root.withdraw()
current = read_clipboard()

# socket
if len(sys.argv) < 2:
    sys.stderr.write('specify server, client or stdio as command line argument\n')
    sys.exit()

elif sys.argv[1] == 'server':
    conn = SocketConnection('server')
    
elif sys.argv[1] == 'client':
    conn = SocketConnection('client')
    conn.send(current)
    
elif sys.argv[1] == 'stdio':
    conn = StdIOConnection()
    
else:
    sys.stderr.write('specify server, client or stdio as command line argument\n')
    sys.exit()



try:
    th = threading.Thread(target=quit_program(conn.read_loop))
    th.daemon = True
    th.start()
    root.after(DELAY, process_clipboard)
    root.mainloop()
except KeyboardInterrupt:
    pass
finally:
    conn.close()


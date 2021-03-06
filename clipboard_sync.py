#!/usr/bin/env python3
import tkinter as tk

import sys
import threading
import socket
import collections
import traceback


# Globals

new_content = None
nc_lock = threading.Lock()
current = None # current clipboard content

conn = None # object representing connection to input/output (e.g. network or stdio)
th = None # thread object handling IO

CLIPBOARD_INTERVAL = 500
root = None # tkinter app object



# Code necessary to shut the application down properly

class ExpectedException(Exception):
    # this type of Exception is expected, so a stack trace should not be printed when catching it
    def __init__(self, message):
        self.message = message

def quit_on_exception(fn):
    # decorator to close everything down when fn() ends
    def new_fn(*args, **kwargs):
        global root, conn
        try:
            fn(*args, **kwargs)
        except Exception as exc:
            if isinstance(exc, KeyboardInterrupt):
                pass
            elif isinstance(exc, SystemExit):
                pass
            elif isinstance(exc, ExpectedException):
                sys.stderr.write(exc.message + '\n')
            else:
                traceback.print_exception(exc)

            conn.close()
            root.destroy()

    return new_fn

class TkExceptionHandlingCallWrapper(tk.CallWrapper):
    @quit_on_exception
    def __call__(self, *args):
        if self.subst:
            args = self.subst(*args)
        return self.func(*args)

tk.CallWrapper = TkExceptionHandlingCallWrapper



# Code for reading the clipboard

def read_clipboard():
    global root
    try:
        return root.clipboard_get(type='UTF8_STRING')
    except:
        return ''


def process_clipboard():
    global new_content, nc_lock, current
    global conn, root
    global CLIPBOARD_INTERVAL

    root.after(CLIPBOARD_INTERVAL, process_clipboard)

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



# Supported IO connections

class SocketConnection:
    CLIENT_PORT = SERVER_PORT = 6666
    
    def __init__(self, conn_type):
        self.client_socket = None
        self.server_socket = None

        if conn_type == 'server':
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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
        global new_content, nc_lock
        length = 0
        len_str = ''
        incoming_bytes = b''

        while True:
            b_char = self.client_socket.recv(1)
            char = b_char.decode('ascii', 'strict')

            if char == '':
                raise ExpectedException('Connection closed')

            if 48 <= ord(char) <= 57:
                len_str += char
            elif char == ',':
                length = int(len_str)
                len_str = ''
                incoming_bytes = self.client_socket.recv(length)
                if len(incoming_bytes) < length:
                    raise ExpectedException('Connection closed')

                nc_lock.acquire()
                new_content = incoming_bytes.decode('utf-8', 'replace')
                nc_lock.release()
            else:
                raise Exception('Length input contains illegal character: ' + char)

    def send(self, unicode_msg):
        msg_bytes = unicode_msg.encode('utf-8')
        len_str = str(len(msg_bytes)) + ','
        msg_bytes = len_str.encode('ascii', 'strict') + msg_bytes
        self.client_socket.send(msg_bytes)


class StdIOConnection:
    def close(self):
        pass
    
    def read_loop(self):
        global new_content, nc_lock
        incoming = ''
        slash = False
        while True:
            next_char = sys.stdin.read(1)
            if not next_char:
                raise ExpectedException('Input stream closed')

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
        msg = unicode_msg.replace('/', '/ ') + '/0'
        sys.stdout.write(msg)
        sys.stdout.flush()


# Main program flow

if __name__ == '__main__':
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
        conn.send(current) # Initial synchronization
    elif sys.argv[1] == 'stdio':
        conn = StdIOConnection()
    else:
        sys.stderr.write('specify server, client or stdio as command line argument\n')
        sys.exit()

    try:
        th = threading.Thread(target=quit_on_exception(conn.read_loop))
        th.daemon = True
        th.start()
        root.after(CLIPBOARD_INTERVAL, quit_on_exception(process_clipboard))
        root.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        conn.close()


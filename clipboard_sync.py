#!/usr/bin/env python
import Tkinter as tk

import sys
import threading

DELAY = 500
sep = '/0'
escape_from = '/'
escape_to   = '/ '

def write_str(s):
    sys.stdout.write(s)

root = tk.Tk()
current = root.clipboard_get()
write_str(current+sep)

new_content = None
nc_lock = threading.Lock()

def read_input():
    global new_content
    incoming = ''
    slash = False
    while True:
        next_char = sys.stdin.read(1)
        if next_char == '':
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



def process_clipboard():
    global current
    global new_content

    nc_lock.acquire()
    if new_content is not None:
        root.clipboard_clear()
        root.clipboard_append(new_content)
        new_content = None
    nc_lock.release()

    tmp = root.clipboard_get()
    if tmp != current:
        current = tmp
        write_str(current.replace(escape_from,escape_to) + sep)

    root.after(DELAY, process_clipboard)

th = threading.Thread(target=read_input)
th.start()

root.after(DELAY, process_clipboard)
root.mainloop()

#!/usr/bin/env python3

import tkinter as tk
import sys
from time import sleep
import re
from select import select

DELAY = 500
sep = '/0'
escape_from = '/'
escape_to   = '/ '

root = tk.Tk()
incoming = ''
current = root.clipboard_get()
print(current+sep, flush=True)

def process_clipboard():
    global incoming
    global current

    while sys.stdin in select([sys.stdin], [], [], 0) [0]:
        incoming += sys.stdin.read(1)
    split = incoming.split(sep)
    incoming = split.pop()
    if split:
        tmp = split.pop()
        root.clipboard_clear()
        root.clipboard_append( tmp.replace(escape_to,escape_from) )

    tmp = root.clipboard_get()
    if tmp != current:
        current = tmp
        print(current.replace(escape_from,escape_to) + sep, flush=True)

    root.after(DELAY, process_clipboard)

root.after(DELAY, process_clipboard)

root.mainloop()

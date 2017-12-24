#!/usr/bin/env python
import Tkinter as tk

import sys
import threading

DELAY = 500
sep = u'/0'
escape_from = u'/'
escape_to   = u'/ '

def write_str(s):
    sys.stdout.write(s.encode('utf-8'))
    sys.stdout.flush()

root = tk.Tk()
current = root.clipboard_get(type='UTF8_STRING')
write_str(current.replace(escape_from,escape_to)+sep)

new_content = None
nc_lock = threading.Lock()

def read_input():
    global new_content
    incoming = u''
    slash = False
    while True:
        next_byte = sys.stdin.read(1)
        if next_byte == '':
            break
        next_char = next_byte.decode('utf-8', 'replace')
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



def process_clipboard():
    global current
    global new_content

    nc_lock.acquire()
    if new_content is not None:
        root.clipboard_clear()
        root.clipboard_append(new_content)
        new_content = None
    nc_lock.release()

    tmp = root.clipboard_get(type='UTF8_STRING')
    #sys.stderr.write('CLIPBOARD content type: ' + str(type(tmp)))
    #sys.stderr.write((u'CLIPBOARD: '+tmp+u'\n').encode('utf-8'))
    if tmp != current:
        current = tmp
        write_str(current.replace(escape_from,escape_to) + sep)

    root.after(DELAY, process_clipboard)

th = threading.Thread(target=read_input)
th.start()

root.after(DELAY, process_clipboard)
root.mainloop()

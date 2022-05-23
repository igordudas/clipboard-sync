# Clipboard synchronizer

## Introduction

This script can be used to synchronize the (text) contents of the system clipboard between two computers. This is particularly useful if you are working remotely using VNC, RDP or similar. It is meant to be used with an ssh tunnel. One computer acts as a server waiting for network connections, and the other is the client connecting to the server.

## Usage

On the server - within a graphical session - run:

```
python3 clipboard_sync.py server
```

On the client, you will need to open two terminals. In the first, connect to the server through ssh with port forwarding:

```
ssh -L 6666:localhost:6666 <server-name-or-ip>
```

In the second, run:

```
python3 clipboard_sync.py client
```

To quit the connection, just stop the clipboard sync script on the client or server by pressing Ctrl-C.

## Clipboard to Standard Input/Output

If you run:
```
python3 clipboard_sync.py stdio
```
the script will not connect to the network, but will instead write stdin to the clipboard and write the clipboard to stdout when the content changes. It uses the character combination **/0** to delimit input or output strings. This means if you input `TEXT/0`, it will write `TEXT` to the clipboard. Conversely, it will append /0 to the output when printing out the clipboard.

To quit the script, close the input stream by pressing Ctrl-D (ctrl-c should work as well, but will likely give you an error message).

## Requirements

- Python 3
- Tkinter (python library)
- ssh
- an ssh server needs to be configured and running on one of the two computers

All other python libraries are usually installed by default, but if the script doesn't work, check if all the libraries imported at the top of the script are installed on your system.

## Support, Security

This is a utility script that I wrote for myself when I had to work on a remote computer through VNC. I am not planning to support this script or add any new functionality. Feel free to use it or adapt it to your own needs. Note that it doesn't have any special security features like encryption or authentication. This is why you are supposed to use it through an ssh tunnel and the clipboard_sync server only accepts connections from localhost.

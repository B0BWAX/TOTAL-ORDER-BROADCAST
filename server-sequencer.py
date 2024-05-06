import sys
import socket
import selectors
import traceback
import types
import json
import time

sel = selectors.DefaultSelector()
host, port = sys.argv[1], int(sys.argv[2])
seq = 1
new_message_flag = 0
messages = {}

lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
lsock.bind((host, port))
lsock.listen()
print(f"Listening on {(host, port)}")
lsock.setblocking(False) # configuring socket in non-blocking mode
sel.register(lsock, selectors.EVENT_READ, data=None) # registers the socket to be monitored with sel.select()

def accept(sock): # accept new connections and add register them with the selector
    conn, addr = sock.accept()
    print(f"Accepted connection from {addr}")
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)

def remove(sock): # remove socket from connections
     print(f"Removed {sock.getsockname()} from connections")
     sel.unregister(sock)
     sock.close()

def receive(key, mask): 
    global messages, new_message_flag
    if mask & selectors.EVENT_READ:
        sock = key.fileobj
        data = key.data
        recv_data = sock.recv(1024)
        data.inb += recv_data
        while b"\n" in data.inb: # received complete message
                end = data.inb.index(b"\n") + 1
                json_message = data.inb[:end] # extract message 
                data.inb = data.inb[end:] # discard new message from buffer
                message = json.loads(json_message)
                handle_message(message, sock)

def handle_message(message, sock):
    global seq, new_message_flag
    message['sock'] = sock.getsockname() # add sender to message information
    if message['test'] == 0:
        message['seq'] = seq
        seq += 1
    if message['seq'] not in messages:
        messages[message['seq']] = []
    messages[message['seq']].append(message) # store the message 
    new_message_flag = 1
    if message['text'] == "close":
        remove(sock)
    else:
        multicast(message)

def multicast(message):
    for _ , key in sel.get_map().items():
        try:
            mask = key.events
            data = key.data
            if data is not None: # make sure we are sending to clients
                data.outb += json.dumps(message).encode() + b"\n" # add message to clients output buffer
                send(key, mask)
        except:
            print("Error multicasting to clients")
            traceback.print_exception(*sys.exc_info())

def send(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_WRITE: # ready for writing
        sent = sock.send(data.outb)  
        data.outb = data.outb[sent:] # discard bytes sent

try:
    while True: # main loop
        events = sel.select(timeout=None)
        for key, mask in events: # each socket thats ready for I/O
            if key.data is None:
                accept(key.fileobj) # receive the new socket
            else:
                receive(key, mask)
                if new_message_flag:
                    print("Messages received: ")
                    for key, value in messages.items():
                        if value:
                            print(f"'{key}': {value},")
                            new_message_flag = 0
            time.sleep(1)
except:
    print("Error")
    traceback.print_exception(*sys.exc_info())
finally:
    lsock.close()
    sel.close()
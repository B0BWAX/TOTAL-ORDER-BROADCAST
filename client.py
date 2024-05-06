import sys
import socket
import queue
import json
import time

host, port, mode = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])

seq = 0
message_queue = queue.PriorityQueue()
inb = b""

def connect():
    server_addr = (host, port)
    print(f"Starting connection to {server_addr}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect_ex(server_addr)
    return sock

def disconnect(sock):
    sock.close()
    print(f"Closed connection to {sock.getsockname()}")

def send(sock, message):
    json_message = json.dumps(message)
    sock.sendall(json_message.encode() + b"\n")
    print("Message sent")

def receive(sock):
    global inb
    recv_data = sock.recv(1024)
    inb += recv_data
    while b"\n" in inb:
        end = inb.index(b"\n") + 1
        json_message = inb[:end] # extract message 
        inb = inb[end:]
        message = json.loads(json_message)
        message_queue.put((message['seq'], message))

def create_message(message_text, message_seq = None):
    message = {'text': "", "seq": 0}
    if message_text is not None:
        message['text'] = message_text
        message['test'] = 0
    if message_seq is not None:
        message['seq'] = message_seq
        message['test'] = 1
    return message

def handle_messages():
    global seq, message_queue
    if not message_queue.empty():
        message_seq, message = message_queue.get()
        if message_seq == seq + 1:
            print(f"Received \"{message['text']}\" from {message['sock']}")
            seq += 1
            print(f"Current seq: {seq}")
            if message == "close":
                disconnect(server)

server = connect()
if mode == 1: # sending mode
    print("SENDING MODE")
    while True:
        input_text = input("Enter message: ")
        message = create_message(input_text)
        send(server, message)
if mode == 2: # receiving mode
    print("LISTENING MODE")
    print(f"Current seq: {seq}")
    while True:
        receive(server)
        handle_messages()
        time.sleep(1)
if mode == 3: # testing mode
    print("TESTING MODE")
    while True: 
        input_text = input("Enter message (message - time) *for regular message don't include time: ")
        parts = input_text.split('-')
        if len(parts) == 1:
            message = create_message(parts[0])
        else:
            message = create_message(parts[0], parts[1])
        send(server, message)

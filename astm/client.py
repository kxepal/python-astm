# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Alexander Shorin
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import asyncore
import logging
import socket
from collections import deque
from .codec import ACK, encode_record
from . import Record

class NullHandler(logging.Handler):
    def emit(self, record):
        pass

log = logging.getLogger('astm')
log.addHandler(NullHandler())
log.setLevel(logging.DEBUG)

def setup_console_logging():
    log = logging.getLogger('astm')
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s'
    ))
    log.addHandler(handler)
    log.setLevel(logging.DEBUG)

    log = logging.getLogger('astm.remote')
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '[%(asctime)s] [%(name)s] [%(levelname)s] [%(host)s:%(port)s] %(message)s'
    ))
    log.addHandler(handler)
    log.setLevel(logging.DEBUG)
    log.propagate = False


#: Maximum message length. Normally, one record are not bigger than 250 chars,
#: so default value is about 10 very long records.
MAX_MESSAGE_LENGTH = 8192

class Client(asyncore.dispatcher):
    """Base asyncore driven ASTM client."""

    def __init__(self, host='localhost', port=15200):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((host, port))
        self.log = logging.getLogger('astm.client')
        self.outbox = deque()

    def handle_connect(self):
        pass

    def handle_close(self):
        self.close()

    def handle_read(self):
        data = self.recv(1)
        self.log.debug('<<< %r', data)
        if not data:
            return

        if data != ACK:
            self.log.warning('Unexpected response %r', data)

    def handle_write(self):
        if not self.outbox:
            return

        message = self.outbox.popleft()

        if len(message) > MAX_MESSAGE_LENGTH:
            raise ValueError('Message too long: %d bytes, maximum is: %d'
                             '' % (len(message), MAX_MESSAGE_LENGTH))

        self.log.debug('>>> %r', message)
        self.send(message)

    def send_async(self, data):
        if isinstance(data, Record):
            data = encode_record(data.to_astm_record())
        self.outbox.append(data)


class Session(asyncore.dispatcher_with_send):
    """Server communication session with specific client."""

    def __init__(self, sock, addr):
        asyncore.dispatcher_with_send.__init__(self, sock)
        self.log_extra = {'host': addr[0], 'port': addr[1]}
        self.log = logging.getLogger('astm.remote')

    def handle_read(self):
        data = self.recv(MAX_MESSAGE_LENGTH)
        self.log.debug('>>> %r', data, extra=self.log_extra)


class Server(asyncore.dispatcher):
    """Base asyncore driven ASTM host."""
    session = Session

    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.log = logging.getLogger('astm.server')
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)
        self.pool = []

    def handle_accept(self):
        pair = self.accept()
        if pair is None:
            return
        sock, addr = pair
        self.log.info('Incoming connection from %r', addr)
        self.pool.append(self.session(sock, addr))

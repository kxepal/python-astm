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
from . import Record
from .codec import encode_record
from .constants import ACK

log = logging.getLogger(__name__)

#: Maximum message length. Normally, one record are not bigger than 250 chars,
#: so default value is about 10 very long records.
MAX_MESSAGE_LENGTH = 8192

class Client(asyncore.dispatcher):
    """Base asyncore driven ASTM client."""

    def __init__(self, host='localhost', port=15200):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((host, port))
        self.log = logging.getLogger(__name__ + '.client')
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

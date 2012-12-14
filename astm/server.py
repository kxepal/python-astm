# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Alexander Shorin
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import logging
import socket
from .asynclib import Dispatcher
from .codec import decode_message, is_chunked_message, join
from .constants import ACK, NAK
from .exceptions import InvalidState, NotAccepted
from .proto import ASTMProtocol, STATE

log = logging.getLogger(__name__)

class RequestHandler(ASTMProtocol):
    """ASTM protocol request handler.

    :param host: Client IP address or hostname.
    :type host: str

    :param port: Client port number.
    :type port: int

    :param sock: Socket object.
    """
    def __init__(self, host, port, sock):
        super(RequestHandler, self).__init__(sock)
        self.set_init_state()
        self._chunks = []
        self.client_info = {'host': host, 'port': port}

    def on_enq(self):
        if self.state == STATE.init:
            self.set_transfer_state()
            return ACK
        else:
            raise NotAccepted('ENQ is not expected while handler in state %r'
            % self.state)

    def on_ack(self):
        raise NotAccepted('Server should not be ACKed.')

    def on_nak(self):
        raise NotAccepted('Server should not be NAKed.')

    def on_eot(self):
        if self.state != STATE.transfer:
            raise InvalidState('Server is not ready to accept EOT message.')
        self.set_init_state()

    def on_message(self):
        if self.state != STATE.transfer:
            self.discard_input_buffers()
            return NAK
        else:
            try:
                self.handle_message(self._last_recv_data)
                return ACK
            except Exception:
                log.exception('Error occurred on message handling.')
                return NAK

    def handle_message(self, message):
        if self.is_chunked_transfer is None:
            self.is_chunked_transfer = is_chunked_message(message)
        if self.is_chunked_transfer:
            self._chunks.append(message)
            self.process_message_chunk(*decode_message(message))
        elif self._chunks:
            self._chunks.append(message)
            self.process_message(*decode_message(join(self._chunks)))
            self._chunks = []
        else:
            self.process_message(*decode_message(message))

    def process_message_chunk(self, seq, records, cs):
        """Abstract ASTM message chunk processor.

        :param seq: Frame sequence number.
        :type seq: int

        :param records: List of ASTM records in message chunk.
                        Last record might be incomplete.
        :type records: list

        :param cs: Checksum
        :type cs: str
        """
        raise NotImplementedError

    def process_message(self, seq, records, cs):
        """Abstract ASTM message processor.

        :param seq: Frame sequence number.
        :type seq: int

        :param records: List of ASTM records in message.
        :type records: list

        :param cs: Checksum
        :type cs: str
        """
        raise NotImplementedError

    def discard_input_buffer(self):
        self._chunks = []
        return super(RequestHandler, self).discard_input_buffer()


class Server(Dispatcher):
    """Asyncore driven ASTM server.

    :param host: Server IP address or hostname.
    :type host: str

    :param port: Server port number.
    :type port: int

    :param request: Server request handler.
    :type request: :class:`RequestHandler`
    """
    def __init__(self, host='localhost', port=15200, request=RequestHandler):
        super(Server, self).__init__()
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)
        self.pool = []
        self.request = request

    def handle_accept(self):
        pair = self.accept()
        if pair is None:
            return
        sock, addr = pair
        log.debug('Connection accepted for %s:%d', *self.addr)
        self.request(addr[0], addr[1], sock)
        super(Server, self).handle_accept()

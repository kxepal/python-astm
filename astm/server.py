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
from .protocol import ASTMProtocol, STATE

log = logging.getLogger(__name__)

__all__ = ['BaseRecordsDispatcher', 'RequestHandler', 'Server']


class BaseRecordsDispatcher(object):
    """Dispatcher of received ASTM records by :class:`RequestHandler`."""
    def __init__(self):
        self.dispatch = {
            'H': self.on_header,
            'P': self.on_patient,
            'O': self.on_order,
            'R': self.on_result,
            'L': self.on_terminator
        }

    def __call__(self, seq, records, cs):
        for record in records:
            self.dispatch[record[0]](record)

    def on_header(self, record):
        """Header record handler."""

    def on_patient(self, record):
        """Patient record handler."""

    def on_order(self, record):
        """Order record handler."""

    def on_result(self, record):
        """Result record handler."""

    def on_terminator(self, record):
        """Terminator record handler."""


class RequestHandler(ASTMProtocol):
    """ASTM protocol request handler.

    :param sock: Socket object.

    :param dispatcher: Request handler records dispatcher instance.
    :type dispatcher: :class:`BaseRecordsDispatcher`
    """
    def __init__(self, sock, dispatcher):
        super(RequestHandler, self).__init__(sock)
        self.set_init_state()
        self._chunks = []
        host, port = sock.getpeername() if sock is not None else (None, None)
        self.client_info = {'host': host, 'port': port}
        self.dispatcher = dispatcher

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
            self.process_message_chunk(*decode_message(message, self.encoding))
        elif self._chunks:
            self._chunks.append(message)
            self.process_message(*decode_message(join(self._chunks), self.encoding))
            self._chunks = []
        else:
            self.process_message(*decode_message(message, self.encoding))

    def process_message_chunk(self, seq, records, cs):
        """Abstract ASTM message chunk processor. Does nothing by default.

        :param seq: Frame sequence number.
        :type seq: int

        :param records: List of ASTM records in message chunk.
                        Last record might be incomplete.
        :type records: list

        :param cs: Checksum
        :type cs: str
        """
        pass

    def process_message(self, seq, records, cs):
        """ASTM message processor. Delegates this process to related local
         :class:`BaseRecordsDispatcher` instance.

        :param seq: Frame sequence number.
        :type seq: int

        :param records: List of ASTM records in message.
        :type records: list

        :param cs: Checksum
        :type cs: str
        """
        self.dispatcher(seq, records, cs)

    def discard_input_buffers(self):
        self._chunks = []
        return super(RequestHandler, self).discard_input_buffers()


class Server(Dispatcher):
    """Asyncore driven ASTM server.

    :param host: Server IP address or hostname.
    :type host: str

    :param port: Server port number.
    :type port: int

    :param request: Server request handler.
    :type request: :class:`RequestHandler`

    :param dispatcher: Request handler records dispatcher class.
    :type dispatcher: :class:`BaseRecordsDispatcher`
    """
    def __init__(self, host='localhost', port=15200,
                 request=RequestHandler, dispatcher=BaseRecordsDispatcher):
        super(Server, self).__init__()
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)
        self.pool = []
        self.request = request
        self.dispatcher = dispatcher

    def handle_accept(self):
        pair = self.accept()
        if pair is None:
            return
        sock, addr = pair
        self.request(sock, self.dispatcher())
        super(Server, self).handle_accept()

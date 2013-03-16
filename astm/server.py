# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Alexander Shorin
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import logging
import socket
from .asynclib import Dispatcher, loop
from .codec import decode_message, is_chunked_message, join
from .constants import ACK, CRLF, EOT, NAK, ENCODING
from .exceptions import InvalidState, NotAccepted
from .protocol import ASTMProtocol

log = logging.getLogger(__name__)

__all__ = ['BaseRecordsDispatcher', 'RequestHandler', 'Server']


class BaseRecordsDispatcher(object):
    """Abstract dispatcher of received ASTM records by :class:`RequestHandler`.
    You need to override his handlers or extend dispatcher for your needs.
    For instance::

        class Dispatcher(BaseRecordsDispatcher):

            def __init__(self, encoding=None):
                super(Dispatcher, self).__init__(encoding)
                # extend it for your needs
                self.dispatch['M'] = self.my_handler
                # map custom wrappers for ASTM records to their type if you
                # don't like to work with raw data.
                self.wrapper['M'] = MyWrapper

            def on_header(self, record):
                # initialize state for this session
                ...

            def on_patient(self, record):
                # handle patient info
                ...

            # etc handlers

            def my_handler(self, record):
                # handle custom record that wasn't implemented yet by
                # python-astm due to some reasons
                ...

    After defining our dispatcher, we left only to let :class:`Server` use it::

        server = Server(dispatcher=Dispatcher)
    """

    #: Encoding of received messages.
    encoding = ENCODING

    def __init__(self, encoding=None):
        self.encoding = encoding or self.encoding
        self.dispatch = {
            'H': self.on_header,
            'C': self.on_comment,
            'P': self.on_patient,
            'O': self.on_order,
            'R': self.on_result,
            'L': self.on_terminator
        }
        self.wrappers = {}

    def __call__(self, message):
        seq, records, cs = decode_message(message, self.encoding)
        for record in records:
            self.dispatch.get(record[0], self.on_unknown)(self.wrap(record))

    def wrap(self, record):
        rtype = record[0]
        if rtype in self.wrappers:
            return self.wrappers[rtype](*record)
        return record

    def on_header(self, record):
        """Header record handler."""

    def on_comment(self, record):
        """Comment record handler."""

    def on_patient(self, record):
        """Patient record handler."""

    def on_order(self, record):
        """Order record handler."""

    def on_result(self, record):
        """Result record handler."""

    def on_terminator(self, record):
        """Terminator record handler."""

    def on_unknown(self, record):
        """Fallback handler for dispatcher."""


class RequestHandler(ASTMProtocol):
    """ASTM protocol request handler.

    :param sock: Socket object.

    :param dispatcher: Request handler records dispatcher instance.
    :type dispatcher: :class:`BaseRecordsDispatcher`

    :param timeout: Number of seconds to wait for incoming data before
                    connection closing.
    :type timeout: int
    """
    def __init__(self, sock, dispatcher, timeout=None):
        super(RequestHandler, self).__init__(sock, timeout=timeout)
        self._chunks = []
        host, port = sock.getpeername() if sock is not None else (None, None)
        self.client_info = {'host': host, 'port': port}
        self.dispatcher = dispatcher
        self._is_transfer_state = False
        self.terminator = 1

    def on_enq(self):
        if not self._is_transfer_state:
            self._is_transfer_state = True
            self.terminator = [CRLF, EOT]
            return ACK
        else:
            log.error('ENQ is not expected')
            return NAK

    def on_ack(self):
        raise NotAccepted('Server should not be ACKed.')

    def on_nak(self):
        raise NotAccepted('Server should not be NAKed.')

    def on_eot(self):
        if self._is_transfer_state:
            self._is_transfer_state = False
            self.terminator = 1
        else:
            raise InvalidState('Server is not ready to accept EOT message.')

    def on_message(self):
        if not self._is_transfer_state:
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
        elif self._chunks:
            self._chunks.append(message)
            self.dispatcher(join(self._chunks))
            self._chunks = []
        else:
            self.dispatcher(message)

    def discard_input_buffers(self):
        self._chunks = []
        return super(RequestHandler, self).discard_input_buffers()

    def on_timeout(self):
        """Closes connection on timeout."""
        super(RequestHandler, self).on_timeout()
        self.close()


class Server(Dispatcher):
    """Asyncore driven ASTM server.

    :param host: Server IP address or hostname.
    :type host: str

    :param port: Server port number.
    :type port: int

    :param request: Custom server request handler. If omitted  the
                    :class:`RequestHandler` will be used by default.

    :param dispatcher: Custom request handler records dispatcher. If omitted the
                       :class:`BaseRecordsDispatcher` will be used by default.

    :param timeout: :class:`RequestHandler` connection timeout. If :const:`None`
                    request handler will wait for data before connection
                    closing.
    :type timeout: int

    :param encoding: :class:`Dispatcher <BaseRecordsDispatcher>`\'s encoding.
    :type encoding: str
    """

    request = RequestHandler
    dispatcher = BaseRecordsDispatcher

    def __init__(self, host='localhost', port=15200,
                 request=None, dispatcher=None,
                 timeout=None, encoding=None):
        super(Server, self).__init__()
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)
        self.pool = []
        self.timeout = timeout
        self.encoding = encoding
        if request is not None:
            self.request = request
        if dispatcher is not None:
            self.dispatcher = dispatcher

    def handle_accept(self):
        pair = self.accept()
        if pair is None:
            return
        sock, addr = pair
        self.request(sock, self.dispatcher(self.encoding), timeout=self.timeout)
        super(Server, self).handle_accept()

    def serve_forever(self, *args, **kwargs):
        """Enters into the :func:`polling loop <asynclib.loop>` to let server
        handle incoming requests."""
        loop(*args, **kwargs)

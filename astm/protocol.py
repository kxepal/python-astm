# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Alexander Shorin
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import logging
from .asynclib import AsyncChat, call_later
from .records import HeaderRecord, TerminatorRecord
from .constants import STX,  ENQ, ACK, NAK, EOT, ENCODING

log = logging.getLogger(__name__)

__all__ = ['ASTMProtocol']


class ASTMProtocol(AsyncChat):
    """Common ASTM protocol routines."""

    #: ASTM header record class.
    astm_header = HeaderRecord
    #: ASTM terminator record class.
    astm_terminator = TerminatorRecord
    #: Flag about chunked transfer.
    is_chunked_transfer = None
    #: IO timer
    timer = None

    encoding = ENCODING
    strip_terminator = False
    _last_recv_data = None
    _last_sent_data = None

    def __init__(self, sock=None, map=None, timeout=None):
        super(ASTMProtocol, self).__init__(sock, map)
        if timeout is not None:
            self.timer = call_later(timeout, self.on_timeout)

    def found_terminator(self):
        while self.inbox:
            data = self.inbox.popleft()
            if not data:
                continue
            self.dispatch(data)

    def dispatch(self, data):
        """Dispatcher of received data."""
        self._last_recv_data = data
        if data == ENQ:
            handler = self.on_enq
        elif data == ACK:
            handler = self.on_ack
        elif data == NAK:
            handler = self.on_nak
        elif data == EOT:
            handler = self.on_eot
        elif data.startswith(STX): # this looks like a message
            handler = self.on_message
        else:
            handler = lambda: self.default_handler(data)

        resp = handler()

        if resp is not None:
            self.push(resp)

    def default_handler(self, data):
        raise ValueError('Unable to dispatch data: %r', data)

    def push(self, data):
        self._last_sent_data = data
        if self.timer is not None and not self.timer.cancelled:
            self.timer.reset()
        return super(ASTMProtocol, self).push(data)

    def on_enq(self):
        """Calls on <ENQ> message receiving."""

    def on_ack(self):
        """Calls on <ACK> message receiving."""

    def on_nak(self):
        """Calls on <NAK> message receiving."""

    def on_eot(self):
        """Calls on <EOT> message receiving."""

    def on_message(self):
        """Calls on ASTM message receiving."""

    def on_timeout(self):
        """Calls when timeout event occurs. Used to limit waiting time for
        response data."""
        log.warning('Communication timeout')

    def handle_read(self):
        if self.timer is not None and not self.timer.cancelled:
            self.timer.reset()
        super(ASTMProtocol, self).handle_read()

    def handle_close(self):
        if self.timer is not None and not self.timer.cancelled:
            self.timer.cancel()
        super(ASTMProtocol, self).handle_close()

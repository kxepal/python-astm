# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Alexander Shorin
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import logging
from collections import namedtuple
from .asynclib import AsyncChat
from .records import HeaderRecord, TerminatorRecord
from .constants import STX, CRLF, ENQ, ACK, NAK, EOT

log = logging.getLogger(__name__)

STATE = namedtuple('ASTMState', ['init', 'opened', 'transfer'])(*range(3))

class ASTMProtocol(AsyncChat):
    """Common ASTM protocol routines."""

    #: ASTM header record class.
    astm_header = HeaderRecord
    #: ASTM terminator record class.
    astm_terminator = TerminatorRecord
    #: Flag about chunked transfer.
    is_chunked_transfer = None

    strip_terminator = False
    _last_recv_data = None
    _last_sent_data = None
    _state = None

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
            raise ValueError('Unable to dispatch data: %r', data)

        resp = handler()

        if resp is not None:
            self.push(resp)

    def push(self, data):
        self._last_sent_data = data
        return super(ASTMProtocol, self).push(data)

    def on_enq(self):
        """Calls on ``ENQ`` message receiving."""

    def on_ack(self):
        """Calls on ``ACK`` message receiving."""

    def on_nak(self):
        """Calls on ``NAK`` message receiving."""

    def on_eot(self):
        """Calls on ``EOT`` message receiving."""

    def on_message(self):
        """Calls on ASTM message receiving."""

    def _get_state(self):
        return self._state

    def _set_state(self, value):
        assert value in STATE
        self._state = value

    #: """ASTM handler state value:
    #:
    #: - ``init``: Neutral state
    #: - ``opened``: ENQ message was sent, waiting for ACK
    #: - ``transfer``: Data transfer processing
    #:
    state = property(_get_state, _set_state)

    def set_init_state(self):
        """Sets handler state to INIT (0).

        In ASTM specification this state also called as `neutral` which means
        that handler is ready to establish data transfer.
        """
        self.terminator = 1
        self.state = STATE.init
        self.on_init_state()

    def set_opened_state(self):
        """Sets handler state to OPENED (1).

        Intermediate state that only means for client implementation. On this
        state client had already sent ``<ENQ>`` and awaits for ``<ACK>`` or
        ``<NAK>`` response. On ``<ACK>`` it switched his state to `transfer`.
        """
        self.terminator = 1
        self.state = STATE.opened
        self.on_opened_state()

    def set_transfer_state(self):
        """Sets handler state to TRANSFER (2).

        In this state handler is able to send or receive ASTM messages depending
        on his role (client or server). At the end of data transfer client
        should send ``<EOT>`` and switch state to `init`.
        """
        self.terminator = [CRLF, EOT]
        self.state = STATE.transfer
        self.on_transfer_state()

    def on_init_state(self):
        """Calls on set state INIT (0)"""

    def on_opened_state(self):
        """Calls on set state OPENED (1)"""

    def on_transfer_state(self):
        """Calls on set state TRANSFER (1)"""

    def on_termination(self):
        """May be called before updating state  from TRANSFER (1) to INIT (0)"""

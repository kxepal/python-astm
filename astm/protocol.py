# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Alexander Shorin
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import logging
from threading import Timer, RLock
from collections import namedtuple
from .asynclib import AsyncChat
from .records import HeaderRecord, TerminatorRecord
from .constants import STX, CRLF, ENQ, ACK, NAK, EOT, ENCODING

log = logging.getLogger(__name__)

#: ASTM protocol states set.
STATE = namedtuple(
    'ASTMState', ['init', 'opened', 'transfer', 'termination'])(*range(4))

__all__ = ['STATE', 'ASTMProtocol']

Timer = type(Timer(None, None))

class ASTMProtocol(AsyncChat):
    """Common ASTM protocol routines."""

    #: ASTM header record class.
    astm_header = HeaderRecord
    #: ASTM terminator record class.
    astm_terminator = TerminatorRecord
    #: Flag about chunked transfer.
    is_chunked_transfer = None
    #: Operation timeout value.
    timeout = None

    encoding = ENCODING
    strip_terminator = False
    _last_recv_data = None
    _last_sent_data = None
    _state = None
    _lock = RLock()
    _timer = None
    _timer_cls = Timer

    def __init__(self, sock=None, map=None, timeout=None):
        super(ASTMProtocol, self).__init__(sock, map)
        if timeout is not None:
            self.timeout = timeout

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

        with self._lock:
            resp = handler()
            self.start_timer()

        if resp is not None:
            self.push(resp)

    def default_handler(self, data):
        raise ValueError('Unable to dispatch data: %r', data)

    def push(self, data):
        self._last_sent_data = data
        return super(ASTMProtocol, self).push(data)

    def start_timer(self):
        if self.timeout is None:
            return
        self.stop_timer()
        self._timer = self._timer_cls(self.timeout, self.on_timeout)
        self._timer.daemon = True
        self._timer.start()
        log.debug('Timer %r started', self._timer)

    def stop_timer(self):
        if self.timeout is None or self._timer is None:
            return
        if self._timer is not None and self._timer.is_alive():
            self._timer.cancel()
        log.debug('Timer %r stopped', self._timer)
        self._timer = None

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

    def _get_state(self):
        return self._state

    def _set_state(self, value):
        assert value in STATE
        self._state = value

    #: ASTM handler state value:
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
        self.state = STATE.init
        self.on_init_state()
        log.info('Switched to init state')

    def set_opened_state(self):
        """Sets handler state to OPENED (1).

        Intermediate state that only means for client implementation. On this
        state client had already sent <ENQ> and awaits for <ACK> or
        <NAK> response. On <ACK> it switched his state to `transfer`.
        """
        self.terminator = 1
        self.state = STATE.opened
        self.on_opened_state()
        log.info('Switched to opened state')

    def set_transfer_state(self):
        """Sets handler state to TRANSFER (2).

        In this state handler is able to send or receive ASTM messages depending
        on his role (client or server).
        """
        self.state = STATE.transfer
        self.on_transfer_state()
        log.info('Switched to transfer state')

    def set_termination_state(self):
        """Sets handler state to TERMINATION (3).

        This state is used on transfer session termination to let client or
        server perform clean up actions before switch back to INIT (0) one.
        """
        self.state = STATE.termination
        self.on_termination_state()
        log.info('Switched to termination state')

    def on_init_state(self):
        """Calls on set state INIT (0)"""
        self.terminator = 1

    def on_opened_state(self):
        """Calls on set state OPENED (1)"""
        self.terminator = 1

    def on_transfer_state(self):
        """Calls on set state TRANSFER (2)"""
        self.terminator = [CRLF, EOT]

    def on_termination_state(self):
        """Calls on set state TERMINATION (3)"""
        self.terminator = 1

    def on_timeout(self):
        """Calls when timeout event occurs. Used to limit time for waiting
        response data."""

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
import time
from .codec import encode_message
from .constants import ENQ, EOT
from .exceptions import InvalidState, NotAccepted
from .mapping import Record
from .protocol import ASTMProtocol, STATE

log = logging.getLogger(__name__)

__all__ = ['Client']

class Client(ASTMProtocol):
    """Common ASTM client implementation.

    :param emitter: Generator function that will produce ASTM records.
    :type emitter: function

    :param host: Server IP address or hostname.
    :type host: str

    :param port: Server port number.
    :type port: int

    :param serve_forever: Start over emitter after transfer termination.
    :type serve_forever: bool

    :param timeout: send/recv operation timeout value. If :const:`None` it will
                    be disabled.
    :type timeout: int
    """

    #: Number or attempts to send record to server.
    retry_attempts = 3 # actually useless thing, but specification requires it.

    def __init__(self, emitter, host='localhost', port=15200,
                 serve_forever=False, timeout=20):
        super(Client, self).__init__(timeout=timeout)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((host, port))
        self._emitter = emitter
        self._retry_attempts = self.retry_attempts
        self._serve_forever = serve_forever
        self.set_init_state()

    def emit_header(self):
        """Returns Header record."""
        return self.astm_header()

    def emit_terminator(self):
        """Returns Terminator record."""
        return self.astm_terminator()

    def retry_push_or_fail(self, data, attempts=3):
        """Sends `data` to server. If server rejects data due to some reasons
        (with <NAK> reply) client tries to resend data for specified number
        of `attempts`. If no attempts left, client terminates his session."""
        if attempts <= 0:
            try:
                self.emitter.send(False)
            except StopIteration:
                pass
            finally:
                self.terminate()
        else:
            self.push(data)

    def set_transfer_state(self):
        self.terminator = 1
        self.state = STATE.transfer
        self.on_transfer_state()

    def start(self):
        """Initiates client transfer by sending <ENQ> message to server."""
        self.push(ENQ)
        self.set_opened_state()

    def terminate(self):
        """Terminates client data transfer by sending <EOT> message to server.

        If `server_forever` argument was passed on `Client` initialization,
        after `state_reset_timeout` :meth:`start` will be called once again.
        Otherwise connection with server will be closed.
        """
        self.push(EOT)
        self.on_termination()
        if self._serve_forever:
            if self.timeout is not None:
                time.sleep(self.timeout)
            self.start()
        else:
            self.close()

    def on_enq(self):
        raise NotAccepted('Client should not receive ENQ.')

    def on_ack(self):
        if self.state not in [STATE.opened, STATE.transfer]:
            raise InvalidState('Client is not ready to accept ACK.')
        self.retry_attempts = self._retry_attempts
        if self.state == STATE.opened:
            self.set_transfer_state()
            for record in self.emitter:
                break
            else:
                self.terminate()
                return
        elif self.state == STATE.transfer:
            try:
                record = self.emitter.send(True)
            except StopIteration:
                self.terminate()
                return
        state = self._transfer_state
        self._last_seq += 1
        mtype = record[0]
        if state is None:
            assert mtype == 'H', mtype
            state = 'header'
        elif state == 'header':
            assert mtype in ['P', 'L']
            if mtype == 'P':
                state = 'patient'
        elif state == 'patient':
            assert mtype in ['P', 'O', 'C', 'L']
            if mtype == 'O':
                state = 'order'
        elif state == 'order':
            assert mtype in ['O', 'C', 'M', 'R', 'L']
            if mtype == 'R':
                state = 'result'
        elif state == 'result':
            assert mtype in ['R', 'C', 'L']
        if isinstance(record, Record):
            record = record.to_astm()
        if mtype == 'L':
            state = None
        data = encode_message(self._last_seq, [record])
        self.push(data)
        self._transfer_state = state

    def on_nak(self):
        self.retry_attempts -= 1
        self.retry_push_or_fail(self._last_sent_data, self.retry_attempts)

    def on_eot(self):
        raise NotAccepted('Client should not receive EOT.')

    def on_message(self):
        raise NotAccepted('Client should not receive ASTM message.')

    def on_init_state(self):
        self._last_seq = 0
        self._transfer_state = None

    def on_opened_state(self):
        self.emitter = self._emitter()

    def on_termination(self):
        """Calls on transfer termination. Resets client state to INIT (0)."""
        self.set_init_state()

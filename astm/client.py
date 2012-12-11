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
from .exceptions import InvalidState, NotAccepted, Rejected
from .mapping import Record
from .proto import ASTMProtocol, STATE


log = logging.getLogger(__name__)


class Client(ASTMProtocol):
    """Common ASTM client implementation."""

    def __init__(self, emitter, host='localhost', port=15200):
        super(Client, self).__init__()
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((host, port))
        self.emitter = emitter()
        self.set_init_state()

    def emit_header(self):
        """Returns Header record."""
        return self.astm_header()

    def emit_terminator(self):
        """Returns Terminator record."""
        return self.astm_terminator()

    def retry_push_or_fail(self, data, attempts=3):
        """Sends `data` to server. If server rejects data due to some reasons
        (with ``<NAK>`` reply) client tries to resend data for specified number
        of `attempts`. If no attempts left, `Rejected` error raised."""
        if not attempts:
            raise Rejected('Server refused to accept data: %r', data)
        self.push(data)

    def set_transfer_state(self):
        self.terminator = 1
        self.state = STATE.transfer
        self.on_transfer_state()

    def on_enq(self):
        raise ValueError('Client should not receive ENQ.')

    def on_ack(self):
        if self.state not in [STATE.opened, STATE.transfer]:
            raise InvalidState('Client is not ready to accept ACK.')
        self._retry_attempts = 3
        if self.state == STATE.opened:
            self.set_transfer_state()
            for record in self.emitter:
                break
            else:
                self.on_termination()
                return
        elif self.state == STATE.transfer:
            try:
                record = self.emitter.send(True)
            except StopIteration:
                self.on_termination()
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
        self._last_sent_data = data
        self.push(data)
        self._transfer_state = state

    def on_nak(self):
        self._retry_attempts -= 1
        self.retry_push_or_fail(self._last_sent_data, self._retry_attempts)

    def on_eot(self):
        raise NotAccepted('Client should not receive EOT.')

    def on_message(self):
        raise NotAccepted('Client should not receive ASTM message.')

    def on_init_state(self):
        self._last_seq = 0
        self._transfer_state = None
        self.push(ENQ)
        self.set_opened_state()

    def on_termination(self):
        self.push(EOT)
        time.sleep(5)
        self.set_init_state()

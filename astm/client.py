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
from .asynclib import loop
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

    :param timeout: Time to wait for response from server. If response wasn't
                    received, the :meth:`on_timeout` will be called.
                    If :const:`None` this timer will be disabled.
    :type timeout: int

    :param retry_attempts: Number or attempts to send record to server.
    :type retry_attempts: int
    """

    def __init__(self, emitter, host='localhost', port=15200,
                 serve_forever=False, timeout=20, retry_attempts=3):
        super(Client, self).__init__(timeout=timeout)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((host, port))
        self._emitter = emitter
        self.remain_attempts = retry_attempts
        self.retry_attempts = retry_attempts
        self._serve_forever = serve_forever
        self.set_init_state()

    def emit_header(self):
        """Returns Header record."""
        return self.astm_header()

    def emit_terminator(self):
        """Returns Terminator record."""
        return self.astm_terminator()

    def retry_push_or_fail(self, data, attempts):
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

    def start(self, *args, **kwargs):
        """Initiates client transfer by sending <ENQ> message to server.
        Implicitly runs pooling :func:`loop <astm.asynclib.loop>`
        """
        self.on_start()
        loop(*args, **kwargs)

    def push_record(self, record):
        """Sends single ASTM record and autoincrement frame sequence number.

        :param record: ASTM record object.
        :type record: list or :class:`~astm.mapping.Record`

        Records should be sent in specific order or :exc:`AssertionError` will
        be raised:

        Legend:

        - ``H``: :class:`~astm.records.HeaderRecord`
        - ``P``: :class:`~astm.records.PatientRecord`
        - ``O``: :class:`~astm.records.OrderRecord`
        - ``R``: :class:`~astm.records.ResultRecord`
        - ``C``: :class:`~astm.records.CommentRecord`
        - ``L``: :class:`~astm.records.TerminatorRecord`

        +--------------------------------+-------------------------------------+
        | Previous record type           | Current record type                 |
        +================================+=====================================+
        | None, this is first record     | ``H``                               |
        +--------------------------------+-------------------------------------+
        | ``H``                          | ``P``, ``L``                        |
        +--------------------------------+-------------------------------------+
        | ``P``                          | ``P``, ``O``, ``C``, ``L``          |
        +--------------------------------+-------------------------------------+
        | ``O``                          | ``O``, ``R``, ``C``, ``L``          |
        +--------------------------------+-------------------------------------+
        | ``R``                          | ``R``, ``C``, ``L``                 |
        +--------------------------------+-------------------------------------+
        | ``L``                          | ``H``                               |
        +--------------------------------+-------------------------------------+
        """
        state = self._last_record_type
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
        self._last_record_type = state

    def terminate(self):
        """Terminates client data transfer by sending <EOT> message to server.

        If `server_forever` argument was passed on `Client` initialization,
        after `state_reset_timeout` :meth:`start` will be called once again.
        Otherwise connection with server will be closed.
        """
        self.on_termination()
        if self._serve_forever:
            if self.timeout is not None:
                time.sleep(self.timeout)
            self.on_start()
        else:
            self.close()

    def on_enq(self):
        raise NotAccepted('Client should not receive ENQ.')

    def on_ack(self):
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
        else:
            raise InvalidState('Client is not ready to accept ACK.')

        self.remain_attempts = self.retry_attempts
        return self.push_record(record)

    def on_nak(self):
        self.remain_attempts -= 1
        self.retry_push_or_fail(self._last_sent_data, self.remain_attempts)

    def on_eot(self):
        raise NotAccepted('Client should not receive EOT.')

    def on_message(self):
        raise NotAccepted('Client should not receive ASTM message.')

    def on_init_state(self):
        self._last_seq = 0
        self._last_record_type = None

    def on_opened_state(self):
        self.emitter = self._emitter()

    def on_start(self):
        """Calls on transfer initialization. Sets client state to OPENED (1)."""
        self.push(ENQ)
        self.set_opened_state()

    def on_termination(self):
        """Calls on transfer termination. Resets client state to INIT (0)."""
        self.push(EOT)
        self.set_init_state()

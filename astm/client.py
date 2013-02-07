# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Alexander Shorin
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import contextlib
import logging
import socket
from .asynclib import loop
from .codec import encode_message
from .constants import ENQ, EOT
from .exceptions import InvalidState, NotAccepted, Rejected
from .mapping import Record
from .protocol import ASTMProtocol, STATE

log = logging.getLogger(__name__)

__all__ = ['Client']


class RecordsStateMachine(object):

    def __init__(self, mapping):
        self.mapping = mapping
        self.state = None

    def __call__(self, state):
        if state is not None:
            assert self.is_acceptable(state),\
                   'invalid state %r, expected one of: %r' \
                   % (state, self.mapping[self.state])
        self.state = state

    def is_acceptable(self, state):
        if state not in self.mapping:
            return False
        next_types = self.mapping[self.state]
        return '*' in next_types or state in next_types


_default_sm = RecordsStateMachine({
    None: ['H'],
    'H': ['C', 'P', 'L'],
    'P': ['C', 'O', 'L'],
    'O': ['C', 'P', 'O', 'R', 'L'],
    'R': ['C', 'P', 'O', 'R', 'L'],
    'C': ['*'],
    'L': []
})

class Client(ASTMProtocol):
    """Common ASTM client implementation.

    :param emitter: Generator function that will produce ASTM records.
    :type emitter: function

    :param host: Server IP address or hostname.
    :type host: str

    :param port: Server port number.
    :type port: int

    :param timeout: Time to wait for response from server. If response wasn't
                    received, the :meth:`on_timeout` will be called.
                    If :const:`None` this timer will be disabled.
    :type timeout: int

    :param retry_attempts: Number or attempts to send record to server.
    :type retry_attempts: int

    :param records_sm: Records type state machine that controls right order
                       of generated records by the emitter. The default state
                       machine may be replaced by any callable which takes
                       single argument as record type.
    :type: callable
    """

    def __init__(self, emitter, host='localhost', port=15200,
                 timeout=20, retry_attempts=3, records_sm=_default_sm):
        super(Client, self).__init__(timeout=timeout)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((host, port))
        self._emitter = emitter
        self._outgoing_queue = []
        self.remain_attempts = retry_attempts
        self.retry_attempts = retry_attempts
        self.records_sm = records_sm
        self.set_init_state()

    def emit_header(self):
        """Returns Header record."""
        return self.astm_header()

    def emit_terminator(self):
        """Returns Terminator record."""
        return self.astm_terminator()

    def handle_connect(self):
        self.emitter = self._emitter(self.session)
        for record in self.emitter:
            if record is not None:
                self._outgoing_queue.append(record)
            break

    @contextlib.contextmanager
    def session(self, header=None, terminator=None):
        self.push(ENQ)
        self._outgoing_queue.append(header or self.emit_header())
        yield
        if self.state == STATE.transfer:
            self.push_record(terminator or self.emit_terminator())
            self.terminate()
        elif self.state == STATE.init:
            self.terminate(True)

    def push(self, data, with_timer=True):
        """Pushes data on to the channel's fifo to ensure its transmission with
        optional timer. Timer is used to control receiving response for sent
        data within specified time frame. If it's doesn't :meth:`on_timeout`
        method will be called and data may be sent once again.

        :param data: Sending data.
        :type data: str

        :param with_timer: Flag to use timer.
        :type with_timer: bool
        """
        if with_timer:
            self.start_timer()
        super(Client, self).push(data)

    def set_transfer_state(self):
        self.terminator = 1
        self.state = STATE.transfer
        self.on_transfer_state()

    def terminate(self, with_close=False):
        # `terminate` method could be called by multiple times simultaneously:
        # first one from session.__exit__ and send one on emitter exhaustion.
        # To prevent sending double EOT messages, we have to control the last
        # one.
        if self._last_sent_data != EOT:
            self.push(EOT, False)
            self.set_init_state()
        if with_close:
            self.close_when_done()

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
        self._last_seq += 1
        self.records_sm(record[0])
        if isinstance(record, Record):
            record = record.to_astm()
        data = encode_message(self._last_seq, [record], self.encoding)
        self.push(data)

    def on_enq(self):
        raise NotAccepted('Client should not receive ENQ.')

    def on_ack(self):
        if self.state == STATE.init:
            if not self._outgoing_queue:
                # Case when client goes to INIT state and not yet have started
                # new session, but receives late ACK response. That is wrong
                # situation that may be caused by error in client logic
                # so breaking on this.
                return self.terminate(True)
            self.set_opened_state()
            record = self._outgoing_queue.pop(0)
        elif self.state == STATE.opened:
            self.set_transfer_state()
            record = self._outgoing_queue.pop(0)
        elif self.state == STATE.transfer:
            try:
                record = self.emitter.send(True)
            except StopIteration:
                # We've got everything from the emitter, terminating
                self.terminate(with_close=True)
                return
            # When session closes it resets the client state to INIT. However,
            # we've just retrieved new record from the emitter and triggered
            # the new transfer session, so let's wait when it got accepted by
            # server.
            if self.state == STATE.init:
                self._outgoing_queue.append(record)
                return
        else:
            raise InvalidState('Client is not ready to accept ACK.')

        self.remain_attempts = self.retry_attempts
        return self.push_record(record)

    def on_nak(self):
        if self.state == STATE.init:
            return self._retry_enq()
        elif self.state == STATE.opened:
            # if Header was rejected, there is not reason to continue since
            # this also could be a situation when specified password (optional,
            # but sometimes is required one) incorrect.
            raise Rejected('Header record was rejected: %r'
                           '' % self._last_sent_data)
        elif self.state == STATE.transfer:
            try:
                record = self.emitter.send(False)
                if record is not None:
                    return self.push_record(record)
            except StopIteration:
                pass
            except Exception:
                self.terminate(with_close=True)
                raise
        else:
            raise InvalidState('Client is not ready to accept NAK.')

    def on_eot(self):
        raise NotAccepted('Client should not receive EOT.')

    def on_message(self):
        raise NotAccepted('Client should not receive ASTM message.')

    def on_init_state(self):
        self._last_seq = 0
        self._outgoing_queue = []
        self.records_sm(None)
        super(Client, self).on_init_state()

    def on_timeout(self):
        if self.state == STATE.init:
            return self._retry_enq()

    def _retry_enq(self):
        if self.remain_attempts:
            self.remain_attempts -= 1
            log.warn('ENQ was rejected, retrying... (attempts remains: %d)',
                     self.remain_attempts)
            return self.push(ENQ)
        raise Rejected('Server reject session establishment.')

    def run(self, *args, **kwargs):
        """Enters into the :func:`polling loop <asynclib.loop>` to let client
        send outgoing requests."""
        loop(*args, **kwargs)

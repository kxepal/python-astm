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
from .codec import encode_message, split
from .constants import ENQ, EOT
from .exceptions import InvalidState, NotAccepted, Rejected
from .mapping import Record
from .protocol import ASTMProtocol, STATE
from .records import HeaderRecord, TerminatorRecord

log = logging.getLogger(__name__)

__all__ = ['Client', 'Emitter']


class RecordsStateMachine(object):
    """Simple state machine to track emitting ASTM records in right order."""
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
    'L': ['H']
})


class Emitter(object):
    """ASTM records emitter for :class:`Client`.

    Used as wrapper for user provided one to provide proper routines around for
    sending Header and Terminator records.

    :param emitter: Activated generator/coroutine
    """
    def __init__(self, emitter):
        # default header record
        self._header = HeaderRecord()
        # default terminator record
        self._terminator = TerminatorRecord()
        self._head = None
        self._body = emitter
        self._tail = None
        self.body = emitter
        # flag to signal that user's emitter produces no records
        self.empty = False
        # emitter state - always should be synced with related Client instance
        self.state = None
        # Trap used to handle records that was emitted by `body` not in time
        # they have to be. This is not an error since we have to active client
        # session inside this `body`.
        self.trap = []

    def send(self, value=None):
        """Coroutine-like method to emit next record and pass the callback value
        to their emitter."""
        while 1:
            if self.state == STATE.init:
                if self._head is None:
                    raise StopIteration
                current = self._head
            elif self.state == STATE.opened:
                current = self._head
                if self.empty:
                    raise StopIteration
            elif self.state == STATE.transfer:
                if self.trap:
                    return self.trap.pop(0)
                current = self._body
            elif self.state == STATE.termination:
                current = self._tail
            try:
                record = current.send(value)
                if self.state != STATE.termination:
                    return record
                self.trap.append(record)
            except TypeError:
                for item in current:
                    return item
            except StopIteration:
                if self.state != STATE.termination:
                    raise

    def head(self):
        """Emits ENQ and Header record."""
        assert (yield ENQ)
        ok = yield self.header
        if not ok:
            raise Rejected('Header record was rejected')

    def tail(self):
        """Emits Terminator record."""
        ok = yield self.terminator
        if not ok:
            raise Rejected('Terminator was rejected')

    @property
    def header(self):
        """Current Header record.

        On setting value resets active `head` emitter.
        """
        return self._header

    @header.setter
    def header(self, value):
        self._header = value or HeaderRecord()
        self._head = self.head()

    @property
    def terminator(self):
        """Current Terminator record.

        On setting value resets active `tail` emitter.
        """
        return self._terminator

    @terminator.setter
    def terminator(self, value):
        self._terminator = value or TerminatorRecord()
        self._tail = self.tail()



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

    :param max_message_size: Amount of bytes that ASTM message should not be
                             greater. If it does, it will be chunkified
                             following ASTM rules.
    """
    #: Wrapper of emitter to provide session context and system logic about
    #: sending head and tail data.
    emitter_wrapper = Emitter

    def __init__(self, emitter, host='localhost', port=15200,
                 timeout=20, retry_attempts=3, records_sm=_default_sm,
                 max_message_size=None):
        super(Client, self).__init__(timeout=timeout)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((host, port))
        self._emitter = emitter
        self.max_message_size = max_message_size
        self.remain_attempts = retry_attempts
        self.retry_attempts = retry_attempts
        self.records_sm = records_sm

    def handle_connect(self):
        """On connection established the client instance initiates
        :class:`Emitter` with provided one during class initialization and
        switches into INIT state.
        """
        emitter = self._emitter(self.session)
        self.emitter = self.emitter_wrapper(emitter)
        self.set_init_state()
        for item in emitter:
            self.emitter.trap.append(item)
            break
        else:
            self.emitter.empty = True
        try:
            self.push(self.emitter.send())
        except StopIteration:
            raise InvalidState('Emitter had produced data, but ASTM session'
                               ' has not been started yet')

    @contextlib.contextmanager
    def session(self, header=None, terminator=None):
        """Context manager that handles ASTM session start and close.

        On session start the :class:`Emitter` instance produces ENQ and Header
        records. After they been acceped the real data sends to server.

        On exit from `with` block session goes to terminate switching current
        :class:`Client` instance to TERMINATION state. If his state still was
        OPENED communication with is over due to no any data was sent except
        of heading one. Otherwise Terminator record and EOT have to be sent
        next.
        """
        self.emitter.header = header
        yield
        if self.state == STATE.opened:
            self.terminate(True)
        elif self.state == STATE.transfer:
            self.set_termination_state()
            self.emitter.terminator = terminator

    def push(self, data, with_timer=True):
        """Pushes data on to the channel's fifo to ensure its transmission with
        optional timer. Timer is used to control receiving response for sent
        data within specified time frame. If it's doesn't :meth:`on_timeout`
        method will be called and data may be sent once again.

        If `max_message_size` is not ``None``, the sent data will be split by
        chunks to fit size restriction.

        :param data: Sending data.
        :type data: str

        :param with_timer: Flag to use timer.
        :type with_timer: bool
        """
        if with_timer:
            self.start_timer()
        if self.max_message_size is not None:
            if len(data) > self.max_message_size:
                for chunk in split(data, self.max_message_size):
                    super(Client, self).push(chunk)
        else:
            super(Client, self).push(data)

    def set_transfer_state(self):
        super(Client, self).set_transfer_state()
        self.terminator = 1

    def terminate(self, with_close=False):
        """Terminates ASTM session by sending EOT message to server.

        If there is no reason to continue communication with server,
        `with_close` argument allows to close socket when EOT message will be
        received."""
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
        """Raises :class:`NotAccepted` exception."""
        raise NotAccepted('Client should not receive ENQ.')

    def on_ack(self):
        """Handles ACK response from server.

        Provides callback value :const:`True` to the emitter and sends next
        message to server.
        """
        if self.state == STATE.init:
            self.set_opened_state()
        elif self.state == STATE.opened:
            self.set_transfer_state()
        elif self.state == STATE.termination:
            self.terminate()
            try:
                return self.push(self.emitter.send(True))
            except StopIteration:
                return self.terminate(True)

        try:
            record = self.emitter.send(True)
        except StopIteration:
            # We've got everything from the emitter, terminating
            self.terminate(with_close=True)
            return

        self.remain_attempts = self.retry_attempts
        return self.push_record(record)

    def on_nak(self):
        """Handles NAK response from server.

        If it was received on ENQ request, the client tries to repeat last
        request for allowed amount of attempts. For others it send callback
        value :const:`False` to the emitter."""
        if self.state == STATE.init:
            return self._retry_enq()
        elif self.state in [STATE.opened, STATE.transfer, STATE.termination]:
            try:
                record = self.emitter.send(False)
                if record is not None: # error was fixed somehow
                    return self.push_record(record)
            except StopIteration:
                pass
            except Exception:
                self.terminate(with_close=True)
                raise
        else:
            raise InvalidState('Client is not ready to accept NAK.')

    def on_eot(self):
        """Raises :class:`NotAccepted` exception."""
        raise NotAccepted('Client should not receive EOT.')

    def on_message(self):
        """Raises :class:`NotAccepted` exception."""
        raise NotAccepted('Client should not receive ASTM message.')

    def on_init_state(self):
        """Resets client state and inner variables."""
        self._last_seq = 0
        self.records_sm(None)
        self.emitter.state = self.state
        super(Client, self).on_init_state()

    def on_opened_state(self):
        self.emitter.state = self.state

    def on_transfer_state(self):
        self.emitter.state = self.state

    def on_termination_state(self):
        self.emitter.state = self.state

    def on_timeout(self):
        """If timeout had occurs for sending ENQ message, it will try to be
        repeated."""
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

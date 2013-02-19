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
from .asynclib import loop
from .codec import encode_message
from .constants import ENQ, EOT
from .exceptions import NotAccepted, Rejected
from .mapping import Record
from .protocol import ASTMProtocol, STATE

log = logging.getLogger(__name__)

__all__ = ['Client', 'Emitter']


class RecordsStateMachine(object):
    """Simple state machine to track emitting ASTM records in right order.

    :param mapping: Mapping of the ASTM records flow order.
                    Keys should be string and defines record type, while values
                    expected as sequence of other record types that may be used
                    after current one.
                    For example: ``{"H": ["P", "C", "L"]}`` mapping defines that
                    if previous record had ``"H"`` type, then the next one
                    should have ``"P"``, ``"C"`` or ``"L"`` type or
                    :exc:`AssertionError` will be raised. The default mapping
                    reflects common ASTM records flow rules. If this argument
                    specified as :const:`None` no rules will be applied.
    :type: dict
    """
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
        if self.mapping is None:
            return True
        if state not in self.mapping:
            return False
        next_types = self.mapping[self.state]
        return '*' in next_types or state in next_types


DEFAULT_RECORDS_FLOW_MAP = {
    None: ['H'],
    'H': ['C', 'P', 'L'],
    'P': ['C', 'O', 'L'],
    'O': ['C', 'P', 'O', 'R', 'L'],
    'R': ['C', 'P', 'O', 'R', 'L'],
    'C': ['*'],
    'L': ['H']
}


class Emitter(object):
    """ASTM records emitter for :class:`Client`.

    Used as wrapper for user provided one to provide proper routines around for
    sending Header and Terminator records.

    :param emitter: Activated generator/coroutine

    :param encoding: Data encoding.
    :type encoding: str

    :param flow_map: Records flow map. Used by :class:`RecordsStateMachine`.
    :type: dict
    """

    #: Records state machine controls emitting records in right order. It
    #: receives `records_flow_map` as only argument on Emitter initialization.
    state_machine = RecordsStateMachine

    def __init__(self, emitter, encoding, flow_map):
        self._emitter = emitter
        self.encoding = encoding
        self.records_sm = self.state_machine(flow_map)
        # flag to signal that user's emitter produces no records
        self.empty = False
        # last sent sequence number
        self.last_seq = 0
        self.buffer = []

    def _send_record(self, record):
        if isinstance(record, Record):
            record = record.to_astm()

        self.last_seq += 1
        data = encode_message(self.last_seq, [record], self.encoding)

        if record[0] == 'L':
            self.last_seq = 0
            self.buffer.append(EOT)

        return data

    def send(self, value=None):
        """Passes `value` to the emitter. Semantically acts in same way as
        :meth:`send` for generators.

        If the emitter has any value within local `buffer` the returned value
        will be extracted from it unless `value` is :const:`False`.

        :param value: Callback value. :const:`True` indicates that previous
                      record was successfully received and accepted by server,
                      :const:`False` signs about his rejection.
        :type value: bool

        :return: Next record data to send to server.
        :rtype: bytes
        """
        if self.buffer:
            if value:
                return self.buffer.pop(0)

        try:
            record = self._emitter.send(value)
        except TypeError:
            record = self._emitter.send(None)

        try:
            self.records_sm(record[0])
        except Exception as err:
            self.throw(type(err), err.args)

        return self._send_record(record)

    def throw(self, exc_type, exc_val=None, exc_tb=None):
        """Raises exception inside the emitter. Acts in same way as
        :meth:`throw` for generators.

        If the emitter had catch an exception and return any record value, it
        will be proceeded in common way.
        """
        record = self._emitter.throw(exc_type, exc_val, exc_tb)
        if record is not None:
            return self._send_record(record)

    def close(self):
        """Closes the emitter. Acts in same way as :meth:`close` for generators.
        """
        self._emitter.close()


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

    :param flow_map: Records flow map. Used by :class:`RecordsStateMachine`.
    :type: dict
    """

    #: Wrapper of emitter to provide session context and system logic about
    #: sending head and tail data.
    emitter_wrapper = Emitter

    def __init__(self, emitter, host='localhost', port=15200,
                 encoding=None, timeout=20,
                 flow_map=DEFAULT_RECORDS_FLOW_MAP):
        super(Client, self).__init__(timeout=timeout)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((host, port))
        self.emitter = self.emitter_wrapper(
            emitter(),
            encoding=encoding or self.encoding,
            flow_map=flow_map,
        )

    def handle_connect(self):
        """Initiates ASTM communication session."""
        super(Client, self).handle_connect()
        self._open_session()

    def handle_close(self):
        self.emitter.close()
        super(Client, self).handle_close()

    def _open_session(self):
        self.set_init_state()
        self.push(ENQ)

    def _close_session(self, close_connection=False):
        self.set_init_state()
        self.push(EOT)
        if close_connection:
            self.close_when_done()

    def run(self, *args, **kwargs):
        """Enters into the :func:`polling loop <astm.asynclib.loop>` to let
        client send outgoing requests."""
        loop(*args, **kwargs)

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

        try:
            message = self.emitter.send(True)
        except StopIteration:
            self._close_session(True)
        else:
            self.push(message)
            if message == EOT:
                self._open_session()

    def on_nak(self):
        """Handles NAK response from server.

        If it was received on ENQ request, the client tries to repeat last
        request for allowed amount of attempts. For others it send callback
        value :const:`False` to the emitter."""
        if self.state == STATE.init:
            return self.push(ENQ)

        try:
            message = self.emitter.send(False)
        except StopIteration:
            self._close_session(True)
        except Exception:
            self._close_session(True)
            raise
        else:
            self.push(message)
            if message == EOT:
                self._open_session()

    def set_transfer_state(self):
        super(Client, self).set_transfer_state()
        self.terminator = 1

    def on_eot(self):
        """Raises :class:`NotAccepted` exception."""
        raise NotAccepted('Client should not receive EOT.')

    def on_message(self):
        """Raises :class:`NotAccepted` exception."""
        raise NotAccepted('Client should not receive ASTM message.')

    def on_timeout(self):
        """If timeout had occurs for sending ENQ message, it will try to be
        repeated."""
        super(Client, self).on_timeout()
        self._close_session(True)

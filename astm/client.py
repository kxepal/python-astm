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
from .asynclib import loop
from .codec import encode
from .constants import ENQ, EOT
from .exceptions import NotAccepted
from .mapping import Record
from .protocol import ASTMProtocol

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
    'H': ['C', 'M', 'P', 'L'],
    'P': ['C', 'M', 'O', 'L'],
    'O': ['C', 'M', 'P', 'O', 'R', 'L'],
    'R': ['C', 'M', 'P', 'O', 'R', 'S', 'L'],
    'S': ['C', 'M', 'P', 'O', 'R', 'S', 'L'],
    'C': ['*'],
    'M': ['*'],
    'L': ['H']
}


class Emitter(object):
    """ASTM records emitter for :class:`Client`.

    Used as wrapper for user provided one to provide proper routines around for
    sending Header and Terminator records.

    :param emitter: Generator/coroutine.

    :param encoding: Data encoding.
    :type encoding: str

    :param flow_map: Records flow map. Used by :class:`RecordsStateMachine`.
    :type: dict

    :param chunk_size: Chunk size in bytes. If :const:`None`, emitter record
                       wouldn't be split into chunks.
    :type chunk_size: int

    :param bulk_mode: Sends all records for single session (starts from Header
                      and ends with Terminator records) via single message
                      instead of sending each record separately. If result
                      message is too long, it may be split by chunks if
                      `chunk_size` is not :const:`None`. Keep in mind, that
                      collecting all records for single session may take some
                      time and server may reject data by timeout reason.
    :type bulk_mode: bool
    """

    #: Records state machine controls emitting records in right order. It
    #: receives `records_flow_map` as only argument on Emitter initialization.
    state_machine = RecordsStateMachine

    def __init__(self, emitter, flow_map, encoding,
                 chunk_size=None, bulk_mode=False):
        self._emitter = emitter()
        self._is_active = False
        self.encoding = encoding
        self.records_sm = self.state_machine(flow_map)
        # flag to signal that user's emitter produces no records
        self.empty = False
        # last sent sequence number
        self.last_seq = 0
        self.buffer = []
        self.chunk_size = chunk_size
        self.bulk_mode = bulk_mode

    def _get_record(self, value=None):
        record = self._emitter.send(value if self._is_active else None)
        if not self._is_active:
            self._is_active = True
        if isinstance(record, Record):
            record = record.to_astm()
        try:
            self.records_sm(record[0])
        except Exception as err:
            self.throw(type(err), err.args)
        return record

    def _send_record(self, record):
        if self.bulk_mode:
            records = [record]
            while True:
                record = self._get_record(True)
                records.append(record)
                if record[0] == 'L':
                    break
            chunks = encode(records, self.encoding, self.chunk_size)
        else:
            self.last_seq += 1
            chunks = encode([record], self.encoding,
                            self.chunk_size, self.last_seq)

        self.buffer.extend(chunks)
        data = self.buffer.pop(0)
        self.last_seq += len(self.buffer)

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
        if self.buffer and value:
            return self.buffer.pop(0)

        record = self._get_record(value)

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

    :param chunk_size: Chunk size in bytes. :const:`None` value prevents
                       records chunking.
    :type chunk_size: int

    :param bulk_mode: Sends all records for single session (starts from Header
                      and ends with Terminator records) via single message
                      instead of sending each record separately. If result
                      message is too long, it may be split by chunks if
                      `chunk_size` is not :const:`None`. Keep in mind, that
                      collecting all records for single session may take some
                      time and server may reject data by timeout reason.
    :type bulk_mode: bool

    Base `emitter` is a generator that yield ASTM records one by one preserving
    their order::

        from astm.records import (
            HeaderRecord, PatientRecord, OrderRecord, TerminatorRecord
        )
        def emitter():
            assert (yield HeaderRecord()), 'header was rejected'
            ok = yield PatientRecord(name={'last': 'foo', 'first': 'bar'})
            if ok:  # you also can decide what to do in case of record rejection
                assert (yield OrderRecord())
            yield TerminatorRecord()  # we may do not care about rejection

    :class:`Client` thought :class:`RecordsStateMachine` keep track
    on this order, raising :exc:`AssertionError` if it is broken.

    When `emitter` terminates with :exc:`StopIteration` or :exc:`GeneratorExit`
    exception client connection to server closing too. You may provide endless
    `emitter` by wrapping function body with ``while True: ...`` loop polling
    data from source from time to time. Note, that server may have communication
    timeouts control and may close session after some time of inactivity, so
    be sure that you're able to send whole session (started by Header record and
    ended by Terminator one) within limited time frame (commonly 10-15 sec.).
    """

    #: Wrapper of emitter to provide session context and system logic about
    #: sending head and tail data.
    emitter_wrapper = Emitter

    def __init__(self, emitter, host='localhost', port=15200,
                 encoding=None, timeout=20, flow_map=DEFAULT_RECORDS_FLOW_MAP,
                 chunk_size=None, bulk_mode=False):
        super(Client, self).__init__(timeout=timeout)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((host, port))
        self.emitter = self.emitter_wrapper(
            emitter,
            encoding=encoding or self.encoding,
            flow_map=flow_map,
            chunk_size=chunk_size,
            bulk_mode=bulk_mode
        )
        self.terminator = 1

    def handle_connect(self):
        """Initiates ASTM communication session."""
        super(Client, self).handle_connect()
        self._open_session()

    def handle_close(self):
        self.emitter.close()
        super(Client, self).handle_close()

    def _open_session(self):
        self.push(ENQ)

    def _close_session(self, close_connection=False):
        self.push(EOT)
        if close_connection:
            self.close_when_done()

    def run(self, timeout=1.0, *args, **kwargs):
        """Enters into the :func:`polling loop <astm.asynclib.loop>` to let
        client send outgoing requests."""
        loop(timeout, *args, **kwargs)

    def on_enq(self):
        """Raises :class:`NotAccepted` exception."""
        raise NotAccepted('Client should not receive ENQ.')

    def on_ack(self):
        """Handles ACK response from server.

        Provides callback value :const:`True` to the emitter and sends next
        message to server.
        """
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
        if self._last_sent_data == ENQ:
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

    def on_eot(self):
        """Raises :class:`NotAccepted` exception."""
        raise NotAccepted('Client should not receive EOT.')

    def on_message(self):
        """Raises :class:`NotAccepted` exception."""
        raise NotAccepted('Client should not receive ASTM message.')

    def on_timeout(self):
        """Sends final EOT message and closes connection after his receiving."""
        super(Client, self).on_timeout()
        self._close_session(True)

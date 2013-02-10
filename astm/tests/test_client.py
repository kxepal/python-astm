# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Alexander Shorin
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import unittest
import astm
from astm.exceptions import NotAccepted, Rejected, InvalidState
from astm.client import Client
from astm import constants, protocol
from astm.tests.utils import DummyMixIn


class DummyClient(DummyMixIn, Client):

    def __init__(self, *args, **kwargs):
        super(DummyClient, self).__init__(*args, **kwargs)
        self.timeout = None

    def create_socket(self, family, type):
        pass

    def connect(self, address):
        pass


class emitter(object):

    def __init__(self, *args):
        self.outbox = list(args)
        self.pos = 0
        self.inbox = []

    def __iter__(self):
        return self

    def next(self):
        if self.pos >= len(self.outbox):
            raise StopIteration
        item = self.outbox[self.pos]
        self.pos += 1
        return item

    __next__ = next

    def send(self, value):
        self.inbox.append(value)
        return self.next()

    def put(self, record):
        self.outbox.append(record)


def simple_emitter(session):
    with session():
        yield


class ClientTestCase(unittest.TestCase):

    def test_init_state(self):
        client = DummyClient(emitter)
        self.assertEqual(client.state,None)

    def test_open_connection(self):
        client = DummyClient(simple_emitter)
        client.handle_connect()
        self.assertEqual(client.state, protocol.STATE.init)
        self.assertEqual(client.outbox[0], constants.ENQ)

    def test_fail_on_enq(self):
        client = DummyClient(emitter)
        self.assertRaises(NotAccepted, client.on_enq)

    def test_fail_on_eot(self):
        client = DummyClient(emitter)
        self.assertRaises(NotAccepted, client.on_eot)

    def test_fail_on_message(self):
        client = DummyClient(emitter)
        self.assertRaises(NotAccepted, client.on_message)

    def test_retry_enq_request(self):
        client = DummyClient(simple_emitter)
        client.handle_connect()
        client.on_nak()
        self.assertEqual(client.retry_attempts, client.remain_attempts + 1)
        self.assertEqual(client.outbox[0], constants.ENQ)

    def test_retry_enq_request_on_timeout(self):
        client = DummyClient(simple_emitter)
        client.handle_connect()
        client.on_timeout()
        self.assertEqual(client.retry_attempts, client.remain_attempts + 1)
        self.assertEqual(client.outbox[0], constants.ENQ)

    def test_raise_exception_if_enq_was_not_accepted(self):
        client = DummyClient(simple_emitter)
        client.handle_connect()
        client.remain_attempts = 0
        self.assertRaises(Rejected, client.on_nak)

    def test_callback_on_sent_failure(self):
        def emitter(session):
            with session():
                ok = yield ['P']
                assert ok is False
        client = DummyClient(emitter)
        client.handle_connect()
        client.on_ack()
        client.on_ack()
        client.on_nak()

    def test_emitter_may_send_new_record_after_nak_response(self):
        def emitter(session):
            with session():
                assert (yield ['P'])
                ok = yield ['O']
                if not ok:
                    yield ['R']
        client = DummyClient(emitter)
        client.handle_connect()
        client.on_ack()
        client.on_ack()
        client.on_ack()
        client.on_nak()
        self.assertEqual(client.outbox[-1][2:3], b'R')

    def test_empty_emitter(self):
        def emitter(session):
            with session():
                if False:
                    yield
        client = DummyClient(emitter)
        client.handle_connect()
        self.assertEqual(client.outbox[-1], constants.ENQ)
        client.on_ack()
        self.assertEqual(client.outbox[-2], constants.EOT)
        self.assertEqual(client.outbox[-1], None)

    def test_early_yield(self):
        def emitter(session):
            yield ['P']
            with session():
                if False:
                    yield
        client = DummyClient(emitter)
        self.assertRaises(InvalidState, client.handle_connect)
        self.assertEqual(list(client.outbox), [])

    def test_late_ack(self):
        def emitter(session):
            with session():
                if False:
                    yield
        client = DummyClient(emitter)
        client.handle_connect()
        self.assertEqual(client.outbox[-1], constants.ENQ)
        client.on_ack()
        self.assertEqual(client.outbox[-2], constants.EOT)
        self.assertEqual(client.outbox[-1], None)
        client.on_ack()
        self.assertEqual(client.outbox[-1], None)

    def test_dummy_usage(self):
        def emitter(session):
            with session():
                ok = yield ['P']
                assert ok
                ok = yield ['O']
                assert ok
        client = DummyClient(emitter)
        client.handle_connect()
        self.assertEqual(client.outbox[-1], constants.ENQ)
        client.on_ack()
        self.assertEqual(client.outbox[-1][1:3], b'1H')
        client.on_ack()
        self.assertEqual(client.outbox[-1][1:3], b'2P')
        client.on_ack()
        self.assertEqual(client.outbox[-1][1:3], b'3O')
        client.on_ack()
        self.assertEqual(client.outbox[-1][1:3], b'4L')
        client.on_ack()
        self.assertEqual(client.outbox[-2], constants.EOT)
        self.assertEqual(client.outbox[-1], None)

    def test_reject_header(self):
        def emitter(session):
            with session():
                yield ['P']
                yield ['O']
        client = DummyClient(emitter)
        client.handle_connect()
        client.on_ack()
        self.assertRaises(Rejected, client.on_nak)

    def test_retry_enq_on_nak(self):
        def emitter(session):
            with session():
                yield ['P']
                yield ['O']
        client = DummyClient(emitter)
        client.handle_connect()
        self.assertEqual(client.outbox[-1], constants.ENQ)
        client.on_nak()
        self.assertEqual(client.outbox[-1], constants.ENQ)
        client.on_nak()
        self.assertEqual(client.outbox[-1], constants.ENQ)
        self.assertEqual(list(client.outbox), [constants.ENQ]*3)

    def test_nak_callback(self):
        def emitter(session):
            with session():
                ok = yield ['P']
                assert not ok
        client = DummyClient(emitter)
        client.handle_connect()
        client.on_ack()
        client.on_ack()
        client.on_nak()

    def test_emit_after_nak(self):
        def emitter(session):
            with session():
                ok = yield ['P']
                assert not ok
                yield ['O']
        client = DummyClient(emitter)
        client.handle_connect()
        client.on_ack()
        client.on_ack()
        client.on_nak()
        client.on_ack()

    def test_terminate_on_exception_after_nake(self):
        def emitter(session):
            with session():
                ok = yield ['P']
                assert ok
                yield ['O']
        client = DummyClient(emitter)
        client.handle_connect()
        client.on_ack()
        client.on_ack()
        self.assertRaises(AssertionError, client.on_nak)
        self.assertEqual(client.outbox[-1], None)


    def test_messages_workflow(self):
        def emitter(session):
            with session():
                yield ['C']
                yield ['P']
                yield ['O']
                yield ['O']
                yield ['P']
                yield ['C']
                yield ['O']
                yield ['O']
                yield ['C']
                yield ['R']
                yield ['C']
                yield ['R']
                yield ['R']
        client = DummyClient(emitter)
        client.handle_connect()
        client.on_ack()
        while client.state != protocol.STATE.init:
            client.on_ack()

    def test_session_in_loop(self):
        def emitter(session):
            for i in range(2):
                with session():
                    yield ['P']
                    yield ['O']
        client = DummyClient(emitter)
        client.handle_connect()
        client.on_ack()
        while client.state != protocol.STATE.init:
            client.on_ack()

    def test_reject_terminator(self):
        def emitter(session):
            with session():
                assert (yield ['P'])
                assert (yield ['O'])
        client = DummyClient(emitter)
        client.handle_connect()
        client.on_ack()
        client.on_ack()
        client.on_ack()
        client.on_ack()
        self.assertEqual(client.outbox[-1][1:3], b'4L')
        self.assertRaises(Rejected, client.on_nak)

    def test_split_large_records(self):
        client = DummyClient(emitter)
        client.max_record_size = 12
        client.push(astm.encode([['H'] + map(str, range(12))])[0])
        self.assertEqual(len(client.outbox), 3)


if __name__ == '__main__':
    unittest.main()

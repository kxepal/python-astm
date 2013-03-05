# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Alexander Shorin
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import unittest
from astm import codec
from astm import constants
from astm.exceptions import NotAccepted
from astm.client import Client
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


def simple_emitter():
    yield ['H']
    yield ['L']


class ClientTestCase(unittest.TestCase):

    def test_open_connection(self):
        client = DummyClient(simple_emitter)
        client.handle_connect()
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

    def test_callback_on_sent_failure(self):
        def emitter():
            yield ['H']
            assert not (yield ['P'])
            yield ['L']
        client = DummyClient(emitter)
        client.handle_connect()
        client.on_ack()
        client.on_ack()
        client.on_nak()

    def test_emitter_may_send_new_record_after_nak_response(self):
        def emitter():
            yield ['H']
            assert (yield ['P'])
            ok = yield ['O']
            if not ok:
                yield ['R']
            yield ['L']
        client = DummyClient(emitter)
        client.handle_connect()
        client.on_ack()
        client.on_ack()
        client.on_ack()
        client.on_nak()
        self.assertEqual(client.outbox[-1][2:3], b'R')

    def test_empty_emitter(self):
        def emitter():
            if False:
                yield
        client = DummyClient(emitter)
        client.handle_connect()
        self.assertEqual(client.outbox[-1], constants.ENQ)
        client.on_ack()
        self.assertEqual(client.outbox[-2], constants.EOT)
        self.assertEqual(client.outbox[-1], None)

    def test_early_yield(self):
        def emitter():
            yield ['P']
            if False:
                yield ['H']
                yield ['L']
        client = DummyClient(emitter)
        client.handle_connect()
        self.assertRaises(AssertionError, client.on_ack)

    def test_late_ack(self):
        def emitter():
            if False:
                yield ['H']
                yield ['L']
        client = DummyClient(emitter)
        client.handle_connect()
        self.assertEqual(client.outbox[-1], constants.ENQ)
        client.on_ack()
        self.assertEqual(client.outbox[-2], constants.EOT)
        self.assertEqual(client.outbox[-1], None)
        client.on_ack()
        self.assertEqual(client.outbox[-1], None)

    def test_dummy_usage(self):
        def emitter():
            yield ['H']
            ok = yield ['P']
            assert ok
            ok = yield ['O']
            assert ok
            yield ['L']
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
        self.assertEqual(client.outbox[-1], constants.ENQ)
        client.on_ack()
        self.assertEqual(client.outbox[-2], constants.EOT)
        self.assertEqual(client.outbox[-1], None)

    def test_reject_header(self):
        def emitter():
            assert (yield ['H'])
            yield ['P']
            yield ['O']
            yield ['L']
        client = DummyClient(emitter)
        client.handle_connect()
        client.on_ack()
        self.assertRaises(AssertionError, client.on_nak)

    def test_nak_callback(self):
        def emitter():
            yield ['H']
            assert not (yield ['P'])
            yield ['L']
        client = DummyClient(emitter)
        client.handle_connect()
        client.on_ack()
        client.on_ack()
        client.on_nak()
        client.on_ack()

    def test_emit_after_nak(self):
        def emitter():
            yield ['H']
            assert not (yield ['P'])
            yield ['O']
            yield ['L']
        client = DummyClient(emitter)
        client.handle_connect()
        client.on_ack()
        client.on_ack()
        client.on_nak()
        client.on_ack()

    def test_terminate_on_exception_after_nake(self):
        def emitter():
            yield ['H']
            assert (yield ['P'])
            yield ['O']
            yield ['L']
        client = DummyClient(emitter)
        client.handle_connect()
        client.on_ack()
        client.on_ack()
        self.assertRaises(AssertionError, client.on_nak)
        self.assertEqual(client.outbox[-2], constants.EOT)
        self.assertEqual(client.outbox[-1], None)


    def test_messages_workflow(self):
        def emitter():
            yield ['H']
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
            yield ['L']
        client = DummyClient(emitter)
        client.handle_connect()
        client.on_ack()
        while client.outbox[-1] is not None:
            client.on_ack()

    def test_session_in_loop(self):
        def emitter():
            for i in range(2):
                yield ['H']
                yield ['P']
                yield ['O']
                yield ['L']
        client = DummyClient(emitter)
        client.handle_connect()
        client.on_ack()
        while client.outbox[-1] is not None:
            client.on_ack()
        self.assertEqual(list(client.outbox),
            [b'\x05',
             b'\x021H\r\x0389\r\n',
             b'\x022P\r\x0392\r\n',
             b'\x023O\r\x0392\r\n',
             b'\x024L\r\x0390\r\n',
             b'\x04',
             b'\x05',
             b'\x021H\r\x0389\r\n',
             b'\x022P\r\x0392\r\n',
             b'\x023O\r\x0392\r\n',
             b'\x024L\r\x0390\r\n',
             b'\x04',
             b'\x05',
             b'\x04',
             None])

    def test_reject_terminator(self):
        def emitter():
            assert (yield ['H'])
            assert (yield ['P'])
            assert (yield ['O'])
            assert (yield ['L'])
        client = DummyClient(emitter)
        client.handle_connect()
        client.on_ack()
        client.on_ack()
        client.on_ack()
        client.on_ack()
        self.assertEqual(client.outbox[-1][1:3], b'4L')
        self.assertRaises(AssertionError, client.on_nak)
        self.assertEqual(client.outbox[-2], constants.EOT)
        self.assertEqual(client.outbox[-1], None)

    def test_timeout_handler(self):
        def emitter():
            assert (yield ['H'])
            assert (yield ['P'])
            assert (yield ['O'])
            assert (yield ['L'])
        client = DummyClient(emitter)
        client.handle_connect()
        client.on_ack()
        client.on_timeout()
        self.assertEqual(client.outbox[-2], constants.EOT)
        self.assertEqual(client.outbox[-1], None)

    def test_chunked_response(self):
        def emitter():
            assert (yield ['H', 'foo', 'bar'])
            assert (yield ['L', 'bar', 'baz'])
        client = DummyClient(emitter, chunk_size=12)
        client.handle_connect()
        client.on_ack()
        self.assertTrue(codec.is_chunked_message(client.outbox[-1]))
        self.assertEqual(client.outbox[-1], b'\x021H|foo\x1750\r\n')
        client.on_ack()
        self.assertFalse(codec.is_chunked_message(client.outbox[-1]))
        self.assertEqual(client.outbox[-1], b'\x022|bar\r\x03F3\r\n')
        client.on_ack()
        self.assertTrue(codec.is_chunked_message(client.outbox[-1]))
        self.assertEqual(client.outbox[-1], b'\x023L|bar\x1747\r\n')
        client.on_ack()
        self.assertFalse(codec.is_chunked_message(client.outbox[-1]))
        self.assertEqual(client.outbox[-1], b'\x024|baz\r\x03FD\r\n')
        client.on_ack()
        self.assertEqual(client.outbox[-1], constants.ENQ)
        client.on_ack()
        self.assertEqual(client.outbox[-1], None)

    def test_bulk_mode(self):
        def emitter():
            assert (yield ['H', 'foo', 'bar'])
            assert (yield ['L', 'bar', 'baz'])
        client = DummyClient(emitter, chunk_size=12, bulk_mode=True)
        client.handle_connect()
        client.on_ack()
        self.assertTrue(codec.is_chunked_message(client.outbox[-1]))
        self.assertEqual(client.outbox[-1], b'\x021H|foo\x1750\r\n')
        client.on_ack()
        self.assertTrue(codec.is_chunked_message(client.outbox[-1]))
        self.assertEqual(client.outbox[-1], b'\x022|bar\r\x1707\r\n')
        client.on_ack()
        self.assertTrue(codec.is_chunked_message(client.outbox[-1]))
        self.assertEqual(client.outbox[-1], b'\x023L|bar\x1747\r\n')
        client.on_ack()
        self.assertFalse(codec.is_chunked_message(client.outbox[-1]))
        self.assertEqual(client.outbox[-1], b'\x024|baz\r\x03FD\r\n')
        client.on_ack()
        self.assertEqual(client.outbox[-1], constants.ENQ)
        client.on_ack()
        self.assertEqual(client.outbox[-1], None)



if __name__ == '__main__':
    unittest.main()

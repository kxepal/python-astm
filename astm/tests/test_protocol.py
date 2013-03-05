# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Alexander Shorin
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import unittest
from astm import constants
from astm.tests.utils import DummyMixIn, track_call
from astm import protocol

class DummyTimer(object):
    def __init__(self, timeout, callback):
        self.timeout = timeout
        self.callback = callback
        self._alive = False

    def is_alive(self):
        return self._alive

    def start(self):
        self._alive = True

    def cancel(self):
        self._alive = False


class DummyProto(DummyMixIn, protocol.ASTMProtocol):
    _timer_cls = DummyTimer


class DispatcherTestCase(unittest.TestCase):

    def test_found_terminator(self):
        obj = DummyProto()
        obj.dispatch = track_call(obj.dispatch)
        obj.found_terminator()
        self.assertTrue(not obj.dispatch.was_called)

        obj.inbox.append(constants.ENQ)
        obj.found_terminator()
        self.assertTrue(obj.dispatch.was_called)

    def test_found_terminator_skip_empty(self):
        obj = DummyProto()
        obj.dispatch = track_call(obj.dispatch)
        obj.inbox.append('')
        obj.inbox.append(None)
        obj.found_terminator()
        self.assertTrue(not obj.dispatch.was_called)

    def test_on_enq(self):
        obj = DummyProto()
        obj.on_enq = track_call(obj.on_enq)
        obj.dispatch(constants.ENQ)
        self.assertTrue(obj.on_enq.was_called)

    def test_on_ack(self):
        obj = DummyProto()
        obj.on_ack = track_call(obj.on_ack)
        obj.dispatch(constants.ACK)
        self.assertTrue(obj.on_ack.was_called)

    def test_on_nak(self):
        obj = DummyProto()
        obj.on_nak = track_call(obj.on_nak)
        obj.dispatch(constants.NAK)
        self.assertTrue(obj.on_nak.was_called)

    def test_on_eot(self):
        obj = DummyProto()
        obj.on_eot = track_call(obj.on_eot)
        obj.dispatch(constants.EOT)
        self.assertTrue(obj.on_eot.was_called)

    def test_on_message(self):
        obj = DummyProto()
        obj.on_message = track_call(obj.on_message)
        obj.dispatch(constants.STX)
        self.assertTrue(obj.on_message.was_called)

    def test_default_hanlder(self):
        obj = DummyProto()
        obj.default_handler = track_call(obj.default_handler)
        self.assertRaises(ValueError, obj.dispatch, b'foo')
        self.assertTrue(obj.default_handler.was_called)

    def test_push_event_response(self):
        obj = DummyProto()
        obj.on_message = lambda: '42'
        obj.dispatch(constants.STX)
        self.assertEqual(obj.outbox.pop(), '42')


if __name__ == '__main__':
    unittest.main()

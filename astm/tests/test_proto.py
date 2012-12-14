# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Alexander Shorin
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import unittest
from astm import constants
from astm.tests.utils import DummyMixIn, track_call
from astm import proto

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


class DummyProto(DummyMixIn, proto.ASTMProtocol):
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
        self.assertRaises(ValueError, obj.dispatch, 'foo')
        self.assertTrue(obj.default_handler.was_called)

    def test_push_event_response(self):
        obj = DummyProto()
        obj.on_message = lambda: '42'
        obj.dispatch(constants.STX)
        self.assertEqual(obj.outbox.pop(), '42')


class StateTestCase(unittest.TestCase):

    def test_default_state(self):
        obj = DummyProto()
        assert obj.state is None
        
    def test_set_init_state(self):
        obj = DummyProto()
        obj.set_init_state()
        self.assertEqual(obj.state, proto.STATE.init)

    def test_on_init_state(self):
        obj = DummyProto()
        obj.on_init_state = track_call(obj.on_init_state)
        obj.set_init_state()
        self.assertTrue(obj.on_init_state.was_called)

    def test_set_opened_state(self):
        obj = DummyProto()
        obj.set_opened_state()
        self.assertEqual(obj.state, proto.STATE.opened)

    def test_on_opened_state(self):
        obj = DummyProto()
        obj.on_opened_state = track_call(obj.on_opened_state)
        obj.set_opened_state()
        self.assertTrue(obj.on_opened_state.was_called)

    def test_set_transfer_state(self):
        obj = DummyProto()
        obj.set_transfer_state()
        self.assertEqual(obj.state, proto.STATE.transfer)

    def test_on_transfer_state(self):
        obj = DummyProto()
        obj.on_transfer_state = track_call(obj.on_transfer_state)
        obj.set_transfer_state()
        self.assertTrue(obj.on_transfer_state.was_called)


class TimeoutTestCase(unittest.TestCase):

    def test_default_timeout(self):
        obj = DummyProto()
        assert obj.timeout is None

    def test_dont_start_timer_if_no_timeout(self):
        obj = DummyProto()
        obj.start_timer()
        assert obj._timer is None

    def test_dont_stor_timer_if_no_timeout(self):
        obj = DummyProto()
        obj.stop_timer()
        assert obj._timer is None

    def test_start_timer(self):
        obj = DummyProto()
        obj.timeout = 1
        obj.start_timer()
        assert obj._timer.is_alive()

    def test_stop_timer(self):
        obj = DummyProto()
        obj.timeout = 1
        obj.start_timer()
        obj.stop_timer()
        assert obj._timer is None

    def test_on_timeout(self):
        obj = DummyProto()
        obj.on_timeout = track_call(obj.on_timeout)
        obj.timeout = 1
        obj.start_timer()
        obj._timer.callback()
        self.assertTrue(obj.on_timeout.was_called)


if __name__ == '__main__':
    unittest.main()

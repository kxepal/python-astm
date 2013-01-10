# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Alexander Shorin
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import unittest
from astm.exceptions import NotAccepted, InvalidState, Rejected
from astm.client import Client
from astm import constants, protocol, records
from astm.tests.utils import DummyMixIn, track_call


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



class ClientTestCase(unittest.TestCase):

    def test_init_state(self):
        client = DummyClient(emitter)
        self.assertEqual(client.state, protocol.STATE.init)

    def test_open_connection(self):
        client = DummyClient(emitter)
        client.start()
        self.assertEqual(client.state, protocol.STATE.opened)
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
        client = DummyClient(emitter)
        client.set_opened_state()
        client.on_nak()
        self.assertEqual(client.retry_attempts, client.remain_attempts + 1)
        self.assertEqual(client.outbox[0], constants.ENQ)

    def test_raise_exception_if_enq_was_not_accepted(self):
        client = DummyClient(emitter)
        client.set_opened_state()
        client.remain_attempts = 0
        self.assertRaises(Rejected, client.on_nak)

    def test_callback_on_sent_failure(self):
        client = DummyClient(emitter)
        client.set_opened_state()
        client.set_transfer_state()
        client.on_nak()
        self.assertEqual(client.emitter.inbox[0], False)

    def test_emitter_may_send_new_record_after_nak_response(self):
        client = DummyClient(emitter)
        client.set_opened_state()
        client.set_transfer_state()
        client._last_record_type = 'order'
        client.emitter.put(['R'])
        client.on_nak()
        self.assertEqual(client.outbox[0][2], 'R')

    def test_terminate_if_emitter_raises_exception_on_nak(self):
        class emitter(object):
            def send(self, value):
                assert value
                return super(emitter, self).send(value)
        client = DummyClient(emitter)
        client.set_opened_state()
        client.set_transfer_state()
        client.terminate = track_call(client.terminate)
        self.assertRaises(AssertionError, client.on_nak)
        self.assertEqual(client.state, protocol.STATE.init)

    def test_dont_accept_nak_in_invalid_state(self):
        client = DummyClient(emitter)
        self.assertRaises(InvalidState, client.on_nak)

    def test_serve_forever(self):
        client = DummyClient(emitter, serve_forever=True, timeout=0)
        client.start()
        client.terminate()
        self.assertEqual(list(client.outbox), [constants.ENQ,
                                               constants.EOT,
                                               constants.ENQ])
        self.assertEqual(client.state, protocol.STATE.opened)


class ClientOnAck(unittest.TestCase):

    def test_fail_on_init_state(self):
        client = DummyClient(emitter)
        self.assertRaises(InvalidState, client.on_ack)

    def test_first_header(self):
        client = DummyClient(emitter)
        client.start()
        client.emitter.put(['H'])
        client.on_ack()
        self.assertEqual(client.outbox[-1][2], 'H')
        self.assertEqual(client._last_record_type, 'header')
        self.assertEqual(client._last_seq, 1)

    def test_fail_if_first_not_header(self):
        client = DummyClient(emitter)
        client.start()
        client.emitter.put(['foo'])
        self.assertRaises(AssertionError, client.on_ack)

    def test_just_emit_first_on_opened_state(self):
        client = DummyClient(emitter)
        client.start()
        client.emitter.put(['H'])
        client.on_ack()
        self.assertFalse(client.emitter.inbox)

    def test_accept_patient_after_header(self):
        client = DummyClient(emitter)
        client.start()
        client.emitter.put(['H'])
        client.on_ack()
        client.emitter.put(['P'])
        client.on_ack()

    def test_terminator_patient_after_header(self):
        client = DummyClient(emitter)
        client.start()
        client.emitter.put(['H'])
        client.on_ack()
        client.emitter.put(['L'])
        client.on_ack()
        self.assertEqual(client._last_record_type, None)

    def test_raising_on_termination_event(self):
        client = DummyClient(emitter)
        client.start()
        client.on_termination = track_call(client.on_termination)
        client.emitter.put(['H'])
        client.emitter.put(['L'])
        client.on_ack() # for ENQ
        client.on_ack() # for H
        client.on_ack() # for L
        self.assertEqual(client.state, protocol.STATE.init)
        self.assertEqual(client._last_record_type, None)
        self.assertTrue(client.on_termination.was_called)

    def test_raise_on_termination_event_if_nothing_to_emit(self):
        client = DummyClient(emitter)
        client.start()
        client.on_termination = track_call(client.on_termination)
        client.on_ack()
        self.assertTrue(client.on_termination.was_called)

    def test_send_back_result_for_header(self):
        client = DummyClient(emitter)
        client.start()
        client.emitter.put(['H'])
        client.emitter.put(['P'])
        client.on_ack()
        client.on_ack()
        self.assertEqual(client.emitter.inbox[0], True)
        self.assertEqual(len(client.emitter.inbox), 1)
        self.assertEqual(client.outbox[-1][2], 'P')
        self.assertEqual(client._last_record_type, 'patient')

    def test_switch_to_order_tranfer_state(self):
        client = DummyClient(emitter)
        client.start()
        client.emitter.put(['H'])
        client.emitter.put(['P'])
        client.emitter.put(['O'])
        client.on_ack()
        client.on_ack()
        client.on_ack()
        self.assertEqual(len(client.emitter.inbox), 2)
        self.assertEqual(client.outbox[-1][2], 'O')
        self.assertEqual(client._last_record_type, 'order')

    def test_switch_to_result_tranfer_state(self):
        client = DummyClient(emitter)
        client.start()
        client.emitter.put(['H'])
        client.emitter.put(['P'])
        client.emitter.put(['O'])
        client.emitter.put(['R'])
        client.on_ack()
        client.on_ack()
        client.on_ack()
        client.on_ack()
        self.assertEqual(len(client.emitter.inbox), 3)
        self.assertEqual(client.outbox[-1][2], 'R')
        self.assertEqual(client._last_record_type, 'result')

    def test_switch_to_none_tranfer_state(self):
        client = DummyClient(emitter)
        client.start()
        client.emitter.put(['H'])
        client.emitter.put(['P'])
        client.emitter.put(['O'])
        client.emitter.put(['R'])
        client.emitter.put(['L'])
        client.on_ack()
        client.on_ack()
        client.on_ack()
        client.on_ack()
        client.on_ack()
        self.assertEqual(len(client.emitter.inbox), 4)
        self.assertEqual(client.outbox[-1][2], 'L')
        self.assertEqual(client._last_record_type, None)

    def test_send_record_instance(self):
        client = DummyClient(emitter)
        client.start()
        client.emitter.put(records.HeaderRecord())
        client.on_ack()
        self.assertEqual(client.outbox[-1][2], 'H')


if __name__ == '__main__':
    unittest.main()

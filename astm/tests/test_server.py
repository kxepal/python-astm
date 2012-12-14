# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Alexander Shorin
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import os
import sys
import unittest
from astm.exceptions import NotAccepted, InvalidState
from astm.server import RequestHandler
from astm import codec, constants, proto, records
from astm.tests.utils import DummyMixIn, track_call


class DummyRequestHandler(DummyMixIn, RequestHandler):
    dummy_dispatcher_called_time = 0

    def __init__(self):
        RequestHandler.__init__(self, 'localhost', 15200, None)

    def process_message(self, seq, records, cs):
        pass

    def process_message_chunk(self, seq, records, cs):
        pass

    def default_handler(self, data):
        return constants.NAK

    def dispatch(self, data):
        self.dummy_dispatcher_called_time += 1
        return super(DummyRequestHandler, self).dispatch(data)

    def recv(self, size):
        return codec.encode([records.HeaderRecord().to_astm()])[0]


class RequestHandlerTestCase(unittest.TestCase):

    def setUp(self):
        self.req = DummyRequestHandler()
        self.req.process_message = track_call(self.req.process_message)
        self.req.process_message_chunk = track_call(self.req.process_message_chunk)
        self.stderr = sys.stderr
        sys.stderr = open(os.devnull, 'w')

    def tearDown(self):
        sys.stderr = self.stderr
        pass

    def test_init_state(self):
        assert self.req.state == proto.STATE.init

    def test_allow_enq_only_for_init_state(self):
        self.req.on_enq()
        self.req.state = proto.STATE.opened
        self.assertRaises(NotAccepted, self.req.on_enq)
        self.req.state = proto.STATE.transfer
        self.assertRaises(NotAccepted, self.req.on_enq)

    def test_allow_eot_only_for_transfer_state(self):
        self.req.state = proto.STATE.transfer
        self.req.on_eot()
        self.req.state = proto.STATE.init
        self.assertRaises(InvalidState, self.req.on_eot)
        self.req.state = proto.STATE.opened
        self.assertRaises(InvalidState, self.req.on_eot)

    def test_fail_on_enq(self):
        self.assertRaises(NotAccepted, self.req.on_ack)

    def test_fail_on_eot(self):
        self.assertRaises(NotAccepted, self.req.on_nak)

    def test_reject_message_on_invalid_state(self):
        self.assertEqual(self.req.on_message(), constants.NAK)

    def test_reject_message_on_parse_error(self):
        self.req.state = proto.STATE.transfer
        self.assertEqual(self.req.on_message(), constants.NAK)
        self.assertFalse(self.req.process_message.was_called)

    def test_accept_message(self):
        self.req.state = proto.STATE.transfer
        self.req._last_recv_data = codec.encode([records.HeaderRecord()
                                                        .to_astm()])[0]
        self.assertEqual(self.req.on_message(), constants.ACK)
        self.assertTrue(self.req.process_message.was_called)
        self.assertFalse(self.req.chunks)

    def test_accept_message_chunk(self):
        self.req.state = proto.STATE.transfer
        self.req.is_chunked_transfer = True
        self.req._last_recv_data = codec.encode([records.HeaderRecord()
                                                 .to_astm()])[0]
        self.assertEqual(self.req.on_message(), constants.ACK)
        self.assertTrue(self.req.process_message_chunk.was_called)
        self.assertTrue(self.req.chunks)

    def test_join_chunks_on_last_one(self):
        self.req.state = proto.STATE.transfer
        self.req.is_chunked_transfer = False
        self.req.chunks = ['']
        self.req._last_recv_data = codec.encode([records.HeaderRecord()
                                                 .to_astm()])[0]
        self.assertEqual(self.req.on_message(), constants.ACK)
        self.assertTrue(self.req.process_message.was_called)
        self.assertFalse(self.req.process_message_chunk.was_called)
        self.assertFalse(self.req.chunks)

    def test_cleanup_input_buffer_on_message_reject(self):
        self.req.state = proto.STATE.init
        self.req.handle_read()
        self.assertEqual(self.req.dummy_dispatcher_called_time, 1)
        self.assertEqual(self.req.outbox[-1], constants.NAK)
        self.assertEqual(self.req._input_buffer, '')



if __name__ == '__main__':
    unittest.main()

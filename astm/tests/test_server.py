# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Alexander Shorin
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import os
import sys
import unittest
from astm.exceptions import NotAccepted, InvalidState
from astm.server import RequestHandler, BaseRecordsDispatcher
from astm import codec, constants, records
from astm.tests.utils import DummyMixIn, track_call


def null_dispatcher(*args, **kwargs):
    pass


class DummyRequestHandler(DummyMixIn, RequestHandler):
    dummy_dispatcher_called_time = 0

    def __init__(self, dispatcher=null_dispatcher):
        RequestHandler.__init__(self, None, dispatcher)

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
        self.req.dispatcher = track_call(self.req.dispatcher)
        self.stderr = sys.stderr
        sys.stderr = open(os.devnull, 'w')

    def tearDown(self):
        sys.stderr.close()
        sys.stderr = self.stderr

    def test_allow_enq_only_for_init_state(self):
        self.assertEqual(self.req.on_enq(), constants.ACK)
        self.assertEqual(self.req.on_enq(), constants.NAK)

    def test_allow_eot_only_for_transfer_state(self):
        self.assertRaises(InvalidState, self.req.on_eot)
        self.req.on_enq()
        self.req.on_eot()

    def test_fail_on_enq(self):
        self.assertRaises(NotAccepted, self.req.on_ack)

    def test_fail_on_eot(self):
        self.assertRaises(NotAccepted, self.req.on_nak)

    def test_reject_message_on_invalid_state(self):
        self.assertEqual(self.req.on_message(), constants.NAK)

    def test_reject_message_on_handle_error(self):
        self.req.on_enq()
        self.assertEqual(self.req.on_message(), constants.NAK)
        self.assertFalse(self.req.dispatcher.was_called)

    def test_reject_message_on_dispatch_error(self):
        def dispatcher(message):
            codec.decode_message(message, 'latin-1')
        req = DummyRequestHandler(track_call(dispatcher))
        req.on_enq()
        req._last_recv_data = '|foo'.encode()
        self.assertEqual(req.on_message(), constants.NAK)
        self.assertTrue(req.dispatcher.was_called)

    def test_accept_message(self):
        self.req.on_enq()
        self.req._last_recv_data = codec.encode([records.HeaderRecord()
                                                        .to_astm()])[0]
        self.assertEqual(self.req.on_message(), constants.ACK)
        self.assertTrue(self.req.dispatcher.was_called)
        self.assertFalse(self.req._chunks)

    def test_handle_chunked_transfer(self):
        self.req.on_enq()
        self.req._chunks = [b'']
        self.req._last_recv_data = codec.encode([records.HeaderRecord()
                                                 .to_astm()])[0]
        self.assertEqual(self.req.on_message(), constants.ACK)
        self.assertTrue(self.req.dispatcher.was_called)
        self.assertFalse(self.req._chunks)

    def test_cleanup_input_buffer_on_message_reject(self):
        self.req.handle_read()
        self.assertEqual(self.req.dummy_dispatcher_called_time, 1)
        self.assertEqual(self.req.outbox[-1], constants.NAK)
        self.assertEqual(self.req._input_buffer, '')

    def test_close_on_timeout(self):
        self.req.close = track_call(self.req.close)
        self.req.on_timeout()
        self.assertTrue(self.req.close.was_called)


class RecordsDispatcherTestCase(unittest.TestCase):

    def setUp(self):
        d = BaseRecordsDispatcher()
        for key, value in d.dispatch.items():
            d.dispatch[key] = track_call(value)
        d.on_unknown = track_call(d.on_unknown)
        self.dispatcher = d

    def test_dispatch_header(self):
        message = codec.encode_message(1, ['H'], 'ascii')
        self.dispatcher(message)
        self.assertTrue(self.dispatcher.dispatch['H'].was_called)

    def test_dispatch_comment(self):
        message = codec.encode_message(1, ['C'], 'ascii')
        self.dispatcher(message)
        self.assertTrue(self.dispatcher.dispatch['C'].was_called)

    def test_dispatch_patient(self):
        message = codec.encode_message(1, ['P'], 'ascii')
        self.dispatcher(message)
        self.assertTrue(self.dispatcher.dispatch['P'].was_called)

    def test_dispatch_order(self):
        message = codec.encode_message(1, ['O'], 'ascii')
        self.dispatcher(message)
        self.assertTrue(self.dispatcher.dispatch['O'].was_called)

    def test_dispatch_result(self):
        message = codec.encode_message(1, ['R'], 'ascii')
        self.dispatcher(message)
        self.assertTrue(self.dispatcher.dispatch['R'].was_called)

    def test_dispatch_scientific(self):
        message = codec.encode_message(1, ['S'], 'ascii')
        self.dispatcher(message)
        self.assertTrue(self.dispatcher.dispatch['S'].was_called)

    def test_dispatch_manufacturer_info(self):
        message = codec.encode_message(1, ['M'], 'ascii')
        self.dispatcher(message)
        self.assertTrue(self.dispatcher.dispatch['M'].was_called)

    def test_dispatch_terminator(self):
        message = codec.encode_message(1, ['L'], 'ascii')
        self.dispatcher(message)
        self.assertTrue(self.dispatcher.dispatch['L'].was_called)

    def test_wrap_before_dispatch(self):
        class Thing(object):
            def __init__(self, *args):
                self.args = args
        def handler(record):
            assert isinstance(record, Thing)
        message = codec.encode_message(1, ['H'], 'ascii')
        self.dispatcher.wrappers['H'] = Thing
        self.dispatcher.dispatch['H'] = track_call(handler)
        self.dispatcher(message)
        self.assertTrue(self.dispatcher.dispatch['H'].was_called)

    def test_provide_default_handler_for_unknown_message_type(self):
        message = codec.encode_message(1, ['FOO'], 'ascii')
        self.dispatcher(message)
        self.assertTrue(self.dispatcher.on_unknown.was_called)



if __name__ == '__main__':
    unittest.main()

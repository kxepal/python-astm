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
from astm.compat import u

class DecodeTestCase(unittest.TestCase):

    def test_decode_abstract_record(self):
        msg = 'A|B|C'
        self.assertEqual(['A', 'B', 'C'], astm.decode(msg))

    def test_astm_record(self):
        msg = 'P|1|2776833|||ABC||||||||||||||||||||'
        res = ['P', '1', '2776833', '', '', 'ABC'] + [''] * 20
        self.assertEqual(res, astm.decode_record(msg))

    def test_decode_frame(self):
        msg = '1A|B|C'
        self.assertEqual((1, [['A', 'B', 'C']]), astm.decode_frame(msg))

    def test_decode_message(self):
        msg = '\x021A|B|C|D\r\x03BF\r\n'
        res = (1, [['A', 'B', 'C', 'D']], 'BF')
        self.assertEqual(res, astm.decode_message(msg))

    def test_decome_message_with_wrong_checksumm(self):
        msg = '\x021A|B|C|D\r\x0300\r\n'
        self.assertRaises(AssertionError, astm.decode_message, msg)

    def test_decode_invalid_frame(self):
        msg = 'A|B|C|D'
        self.assertRaises(ValueError, astm.decode_frame, msg)

    def test_decode_invalid_message(self):
        msg = 'A|B|C|D'
        self.assertRaises(ValueError, astm.decode_message, msg)

        msg = '\x021A|B|C|D\r\x03BF'
        self.assertRaises(ValueError, astm.decode_message, msg)

        msg = '1A|B|C|D\r\x03BF\r\n'
        self.assertRaises(ValueError, astm.decode_message, msg)

    def test_decode_record_with_components(self):
        msg = 'A|B^C^D^E|F'
        res = ['A', ['B', 'C', 'D', 'E'], 'F']
        self.assertEqual(res, astm.decode_record(msg))

    def test_decode_record_with_repeated_components(self):
        msg = 'A|B^C\D^E|F'
        res = ['A', [['B', 'C'], ['D', 'E']], 'F']
        self.assertEqual(res, astm.decode_record(msg))


class EncodeTestCase(unittest.TestCase):

    def test_encode_message(self):
        msg = '\x021A|B|C|D\r\x03BF\r\n'
        seq, data, cs = astm.decode_message(msg)
        self.assertEqual(msg, astm.encode_message(seq, data))

    def test_encode_component_strip_tail(self):
        msg = ['A', 'B', '', '', '']
        res = 'A^B'
        self.assertEqual(res, astm.encode_component(msg))

    def test_encode_record(self):
        msg = 'A|B^C\D^E|F^G|H'
        self.assertEqual(msg, astm.encode_record(astm.decode_record(msg)))

    def test_count_encode_fields_as_empty_strings(self):
        self.assertEqual('|B|', astm.encode_record([None,'B', None]))


class ChecksummTestCase(unittest.TestCase):

    def test_common(self):
        msg = u('2P|1|2776833|||王^大^明||||||||||||||||||||\x0D\x03')
        self.assertEqual('CF', astm.make_checksum(msg))

    def test_short(self):
        self.assertEqual('02', astm.make_checksum('\x02'))


if __name__ == '__main__':
    unittest.main()

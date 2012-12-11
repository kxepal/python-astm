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
from astm.compat import u
from astm.constants import STX, ETX, ETB, CR, LF, CRLF

def f(s):
    return s.format(STX=STX, ETX=ETX, ETB=ETB, CR=CR, LF=LF, CRLF=CRLF)

class DecodeTestCase(unittest.TestCase):

    def test_decode_message(self):
        msg = f('{STX}1A|B|C|D{CR}{ETX}BF{CRLF}')
        res = [['A', 'B', 'C', 'D']]
        self.assertEqual(res, codec.decode(msg))

    def test_decode_frame(self):
        msg = f('1A|B|C|D{CR}{ETX}')
        res = [['A', 'B', 'C', 'D']]
        self.assertEqual(res, codec.decode(msg))

    def test_decode_record(self):
        msg = f('A|B|C|D')
        res = [['A', 'B', 'C', 'D']]
        self.assertEqual(res, codec.decode(msg))


class DecodeMessageTestCase(unittest.TestCase):

    def test_decode_message(self):
        msg = f('{STX}1A|B|C|D{CR}{ETX}BF{CRLF}')
        res = (1, [['A', 'B', 'C', 'D']], 'BF')
        self.assertEqual(res, codec.decode_message(msg))

    def test_fail_decome_message_with_wrong_checksumm(self):
        msg = f('{STX}1A|B|C|D{CR}{ETX}00{CRLF}')
        self.assertRaises(AssertionError, codec.decode_message, msg)

    def test_fail_decode_invalid_message(self):
        msg = 'A|B|C|D'
        self.assertRaises(ValueError, codec.decode_message, msg)

        msg = f('{STX}1A|B|C|D{CR}{ETX}BF')
        self.assertRaises(ValueError, codec.decode_message, msg)

        msg = f('1A|B|C|D{CR}{ETX}BF{CRLF}')
        self.assertRaises(ValueError, codec.decode_message, msg)


class DecodeFrameTestCase(unittest.TestCase):

    def test_fail_decode_without_tail_data(self):
        msg = '1A|B|C'
        self.assertRaises(ValueError, codec.decode_frame, msg)

    def test_fail_decode_without_seq_value(self):
        msg = f('A|B|C|D{CR}{ETX}')
        self.assertRaises(ValueError, codec.decode_frame, msg)

    def test_fail_decode_with_invalid_tail(self):
        msg = f('1A|B|C{ETX}')
        self.assertRaises(ValueError, codec.decode_frame, msg)


class DecodeRecordTestCase(unittest.TestCase):

    def test_decode(self):
        msg = 'P|1|2776833|||ABC||||||||||||||||||||'
        res = ['P', '1', '2776833', None, None, 'ABC'] + [None] * 20
        self.assertEqual(res, codec.decode_record(msg))

    def test_decode_with_components(self):
        msg = 'A|B^C^D^E|F'
        res = ['A', ['B', 'C', 'D', 'E'], 'F']
        self.assertEqual(res, codec.decode_record(msg))

    def test_decode_with_repeated_components(self):
        msg = 'A|B^C\D^E|F'
        res = ['A', [['B', 'C'], ['D', 'E']], 'F']
        self.assertEqual(res, codec.decode_record(msg))

    def test_decode_none_values_for_missed_ones(self):
        msg = 'A|||B'
        res = ['A', None, None, 'B']
        self.assertEqual(res, codec.decode_record(msg))

        msg = 'A|B^^C^D^^E|F'
        res = ['A', ['B', None, 'C', 'D', None, 'E'], 'F']
        self.assertEqual(res, codec.decode_record(msg))

    def test_decode_nonascii_chars_as_unicode(self):
        msg = u('привет|мир|!')
        res = [u('привет'), u('мир'), '!']
        self.assertEqual(res, codec.decode_record(msg))


class EncodeTestCase(unittest.TestCase):

    def test_encode(self):
        msg = f('{STX}1A|B|C|D{CR}{ETX}BF{CRLF}')
        seq, data, cs = codec.decode_message(msg)
        self.assertEqual([msg], codec.encode(data))

    def test_encode_message(self):
        msg = f('{STX}1A|B|C|D{CR}{ETX}BF{CRLF}')
        seq, data, cs = codec.decode_message(msg)
        self.assertEqual(msg, codec.encode_message(seq, data))

    def test_encode_record(self):
        msg = 'A|B^C\D^E|F^G|H'
        self.assertEqual(msg, codec.encode_record(codec.decode_record(msg)))

    def test_encode_record_with_none_and_non_string(self):
        msg = ['foo', None, 0]
        res = 'foo||0'
        self.assertEqual(res, codec.encode_record(msg))

    def test_encode_component(self):
        msg = ['foo', None, 0]
        res = 'foo^^0'
        self.assertEqual(res, codec.encode_component(msg))

    def test_encode_component_strip_tail(self):
        msg = ['A', 'B', '', None, '']
        res = 'A^B'
        self.assertEqual(res, codec.encode_component(msg))

    def test_encode_repeated_component(self):
        msg = [['foo', 1], ['bar', 2], ['baz', 3]]
        res = 'foo^1\\bar^2\\baz^3'
        self.assertEqual(res, codec.encode_repeated_component(msg))

    def test_count_none_fields_as_empty_strings(self):
        self.assertEqual('|B|', codec.encode_record([None,'B', None]))

    def test_iter_encoding(self):
        records = [['foo', 1], ['bar', 2], ['baz', 3]]
        res = [f('{STX}1foo|1{CR}{ETX}32{CRLF}'),
               f('{STX}2bar|2{CR}{ETX}25{CRLF}'),
               f('{STX}3baz|3{CR}{ETX}2F{CRLF}')]
        self.assertEqual(res, list(codec.iter_encode(records)))


class ChunkedEncodingTestCase(unittest.TestCase):

    def setUp(self):
        self._size = codec.MAX_MESSAGE_SIZE
        codec.MAX_MESSAGE_SIZE = 3

    def tearDown(self):
        codec.MAX_MESSAGE_SIZE = self._size

    def test_encode_chunky(self):
        codec.MAX_MESSAGE_SIZE = 4
        recs = [['foo', 1], ['bar', 24], ['baz', [1,2,3], 'boo']]
        res = codec.encode(recs)
        self.assertTrue(isinstance(res, list))
        self.assertEqual(len(res), 7)

        self.assertEqual(res[0], f('{STX}1foo|{ETB}08{CRLF}'))
        self.assertEqual(res[1], f('{STX}21{CR}ba{ETB}4A{CRLF}'))
        self.assertEqual(res[2], f('{STX}3r|24{ETB}9E{CRLF}'))
        self.assertEqual(res[3], f('{STX}4{CR}baz{ETB}95{CRLF}'))
        self.assertEqual(res[4], f('{STX}5|1^2{ETB}89{CRLF}'))
        self.assertEqual(res[5], f('{STX}6^3|b{ETB}BC{CRLF}'))
        self.assertEqual(res[6], f('{STX}7oo{CR}{ETX}25{CRLF}'))

    def test_decode_chunks(self):
        codec.MAX_MESSAGE_SIZE = 4
        recs = [['foo', 1], ['bar', 24], ['baz', [1,2,3], 'boo']]
        res = codec.encode(recs)
        for item in res:
            codec.decode(item)

    def test_join_chunks(self):
        codec.MAX_MESSAGE_SIZE = 4
        recs = [['foo', 1], ['bar', 24], ['baz', [1,2,3], 'boo']]
        chunks = codec.encode(recs)
        msg = codec.join(chunks)
        codec.decode(msg)

    def test_encode_as_single_message(self):
        res = codec.encode_message(2, [['A', 0]])
        self.assertEqual(f('{STX}2A|0{CR}{ETX}2F{CRLF}'), res)

    def test_is_chunked_message(self):
        msg = f('{STX}2A|0{CR}{ETB}2F{CRLF}')
        self.assertTrue(codec.is_chunked_message(msg))

        msg = f('{STX}2A|0{CR}{ETX}2F{CRLF}')
        self.assertFalse(codec.is_chunked_message(msg))


class ChecksummTestCase(unittest.TestCase):

    def test_common(self):
        msg = u('2P|1|2776833|||王^大^明||||||||||||||||||||\x0D\x03')
        self.assertEqual('CF', codec.make_checksum(msg))

    def test_short(self):
        self.assertEqual('02', codec.make_checksum('\x02'))


if __name__ == '__main__':
    unittest.main()

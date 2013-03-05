# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Alexander Shorin
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import unittest
from astm import codec
from astm.compat import u
from astm.constants import STX, ETX, ETB, CR, LF, CRLF

def f(s, e='latin-1'):
    return u(s).format(STX=u(STX),
                       ETX=u(ETX),
                       ETB=u(ETB),
                       CR=u(CR),
                       LF=u(LF),
                       CRLF=u(CRLF)).encode(e)

class DecodeTestCase(unittest.TestCase):

    def test_decode_message(self):
        msg = f('{STX}1A|B|C|D{CR}{ETX}BF{CRLF}')
        res = [['A', 'B', 'C', 'D']]
        self.assertEqual(res, codec.decode(msg))

    def test_decode_message_with_nonascii(self):
        msg = f('{STX}1Й|Ц|У|К{CR}{ETX}F1{CRLF}', 'cp1251')
        res = [[u('Й'), u('Ц'), u('У'), u('К')]]
        self.assertEqual(res, codec.decode(msg, 'cp1251'))

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
        self.assertEqual(res, codec.decode_message(msg, 'ascii'))

    def test_fail_decome_message_with_wrong_checksumm(self):
        msg = f('{STX}1A|B|C|D{CR}{ETX}00{CRLF}')
        self.assertRaises(AssertionError, codec.decode_message, msg, 'ascii')

    def test_fail_decode_invalid_message(self):
        msg = f('A|B|C|D')
        self.assertRaises(ValueError, codec.decode_message, msg, 'ascii')

        msg = f('{STX}1A|B|C|D{CR}{ETX}BF')
        self.assertRaises(ValueError, codec.decode_message, msg, 'ascii')

        msg = f('1A|B|C|D{CR}{ETX}BF{CRLF}')
        self.assertRaises(ValueError, codec.decode_message, msg, 'ascii')


class DecodeFrameTestCase(unittest.TestCase):

    def test_fail_decode_without_tail_data(self):
        msg = f('1A|B|C')
        self.assertRaises(ValueError, codec.decode_frame, msg, 'ascii')

    def test_fail_decode_without_seq_value(self):
        msg = f('A|B|C|D{CR}{ETX}')
        self.assertRaises(ValueError, codec.decode_frame, msg, 'ascii')

    def test_fail_decode_with_invalid_tail(self):
        msg = f('1A|B|C{ETX}')
        self.assertRaises(ValueError, codec.decode_frame, msg, 'ascii')


class DecodeRecordTestCase(unittest.TestCase):

    def test_decode(self):
        msg = f('P|1|2776833|||ABC||||||||||||||||||||')
        res = ['P', '1', '2776833', None, None, 'ABC'] + [None] * 20
        self.assertEqual(res, codec.decode_record(msg, 'ascii'))

    def test_decode_with_components(self):
        msg = f('A|B^C^D^E|F')
        res = ['A', ['B', 'C', 'D', 'E'], 'F']
        self.assertEqual(res, codec.decode_record(msg, 'ascii'))

    def test_decode_with_repeated_components(self):
        msg = f('A|B^C\D^E|F')
        res = ['A', [['B', 'C'], ['D', 'E']], 'F']
        self.assertEqual(res, codec.decode_record(msg, 'ascii'))

    def test_decode_none_values_for_missed_ones(self):
        msg = f('A|||B')
        res = ['A', None, None, 'B']
        self.assertEqual(res, codec.decode_record(msg, 'ascii'))

        msg = f('A|B^^C^D^^E|F')
        res = ['A', ['B', None, 'C', 'D', None, 'E'], 'F']
        self.assertEqual(res, codec.decode_record(msg, 'ascii'))

    def test_decode_nonascii_chars_as_unicode(self):
        msg = f('привет|мир|!', 'utf8')
        res = [u('привет'), u('мир'), '!']
        self.assertEqual(res, codec.decode_record(msg, 'utf8'))


class EncodeTestCase(unittest.TestCase):

    def test_encode(self):
        msg = f('{STX}1A|B|C|D{CR}{ETX}BF{CRLF}')
        seq, data, cs = codec.decode_message(msg, 'ascii')
        self.assertEqual([msg], codec.encode(data, 'ascii'))

    def test_encode_message(self):
        msg = f('{STX}1A|B|C|D{CR}{ETX}BF{CRLF}')
        seq, data, cs = codec.decode_message(msg, 'ascii')
        self.assertEqual(msg, codec.encode_message(seq, data, 'ascii'))

    def test_encode_record(self):
        msg = b'A|B^C\D^E|F^G|H'
        record = codec.decode_record(msg, 'ascii')
        self.assertEqual(msg, codec.encode_record(record, 'ascii'))

    def test_encode_record_with_none_and_non_string(self):
        msg = ['foo', None, 0]
        res = b'foo||0'
        self.assertEqual(res, codec.encode_record(msg, 'ascii'))

    def test_encode_component(self):
        msg = ['foo', None, 0]
        res = b'foo^^0'
        self.assertEqual(res, codec.encode_component(msg, 'ascii'))

    def test_encode_component_strip_tail(self):
        msg = ['A', 'B', '', None, '']
        res = b'A^B'
        self.assertEqual(res, codec.encode_component(msg, 'ascii'))

    def test_encode_repeated_component(self):
        msg = [['foo', 1], ['bar', 2], ['baz', 3]]
        res = b'foo^1\\bar^2\\baz^3'
        self.assertEqual(res, codec.encode_repeated_component(msg, 'ascii'))

    def test_count_none_fields_as_empty_strings(self):
        self.assertEqual(b'|B|', codec.encode_record([None,'B', None], 'ascii'))

    def test_iter_encoding(self):
        records = [['foo', 1], ['bar', 2], ['baz', 3]]
        res = [f('{STX}1foo|1{CR}{ETX}32{CRLF}'),
               f('{STX}2bar|2{CR}{ETX}25{CRLF}'),
               f('{STX}3baz|3{CR}{ETX}2F{CRLF}')]
        self.assertEqual(res, list(codec.iter_encode(records, 'ascii')))

    def test_frame_number(self):
        records = list(map(list, 'ABCDEFGHIJ'))
        res = [f('{STX}1A{CR}{ETX}82{CRLF}'),
               f('{STX}2B{CR}{ETX}84{CRLF}'),
               f('{STX}3C{CR}{ETX}86{CRLF}'),
               f('{STX}4D{CR}{ETX}88{CRLF}'),
               f('{STX}5E{CR}{ETX}8A{CRLF}'),
               f('{STX}6F{CR}{ETX}8C{CRLF}'),
               f('{STX}7G{CR}{ETX}8E{CRLF}'),
               f('{STX}0H{CR}{ETX}88{CRLF}'),
               f('{STX}1I{CR}{ETX}8A{CRLF}'),
               f('{STX}2J{CR}{ETX}8C{CRLF}')]
        self.assertEqual(res, list(codec.iter_encode(records, 'ascii')))


class ChunkedEncodingTestCase(unittest.TestCase):

    def test_encode_chunky(self):
        recs = [['foo', 1], ['bar', 24], ['baz', [1, 2, 3], 'boo']]
        res = codec.encode(recs, size=14)
        self.assertTrue(isinstance(res, list))
        self.assertEqual(len(res), 4)

        self.assertEqual(res[0], f('{STX}1foo|1{CR}b{ETB}A8{CRLF}'))
        self.assertEqual(len(res[0]), 14)
        self.assertEqual(res[1], f('{STX}2ar|24{CR}b{ETB}6D{CRLF}'))
        self.assertEqual(len(res[1]), 14)
        self.assertEqual(res[2], f('{STX}3az|1^2^{ETB}C0{CRLF}'))
        self.assertEqual(len(res[2]), 14)
        self.assertEqual(res[3], f('{STX}43|boo{CR}{ETX}33{CRLF}'))
        self.assertLessEqual(len(res[3]), 14)


    def test_decode_chunks(self):
        recs = [['foo', 1], ['bar', 24], ['baz', [1, 2, 3], 'boo']]
        res = codec.encode(recs, size=14)
        for item in res:
            codec.decode(item)

    def test_join_chunks(self):
        recs = [['foo', '1'], ['bar', '24'], ['baz', ['1', '2', '3'], 'boo']]
        chunks = codec.encode(recs, size=14)
        msg = codec.join(chunks)
        self.assertEqual(codec.decode(msg), recs)

    def test_encode_as_single_message(self):
        res = codec.encode_message(2, [['A', 0]], 'ascii')
        self.assertEqual(f('{STX}2A|0{CR}{ETX}2F{CRLF}'), res)

    def test_is_chunked_message(self):
        msg = f('{STX}2A|0{CR}{ETB}2F{CRLF}')
        self.assertTrue(codec.is_chunked_message(msg))

        msg = f('{STX}2A|0{CR}{ETX}2F{CRLF}')
        self.assertFalse(codec.is_chunked_message(msg))


class ChecksummTestCase(unittest.TestCase):

    def test_common(self):
        msg = u('2P|1|2776833|||王^大^明||||||||||||||||||||\x0D\x03')
        self.assertEqual(b'CF', codec.make_checksum(msg))

    def test_bytes(self):
        msg = u('2P|1|2776833|||王^大^明||||||||||||||||||||\x0D\x03').encode('utf8')
        self.assertEqual(b'4B', codec.make_checksum(msg))

    def test_short(self):
        self.assertEqual(b'02', codec.make_checksum('\x02'))


if __name__ == '__main__':
    unittest.main()

# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Alexander Shorin
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import datetime
import unittest
import astm
from astm import mapping


class HeaderTestCase(unittest.TestCase):

    def test_decode(self):
        msg = 'H|\^&|||Afinion AS100^^AS0007962|||||||P|1|20120329111326'
        mapping.Header(*astm.decode(msg))
        mapping.Header(*astm.decode_record(msg))

    def test_encode(self):
        msg = 'H|\^&|||Afinion AS100^^AS0007962|||||||P|1|20120329111326'
        res = astm.encode_record(mapping.Header(*astm.decode_record(msg)))
        self.assertEqual(msg, res)

    def test_set_current_datetime_if_missed(self):
        msg = 'H|\^&|||ABC|||||||P|1|'
        header = mapping.Header(*astm.decode_record(msg))
        res = datetime.datetime.now().strftime('%Y%m%d%H%M%S')[:-2]
        self.assertEqual(res, header.timestamp[:-2])

    def test_strict_procid_values(self):
        msg = 'H|\^&|||ABC|||||||P|1|'
        mapping.Header(*astm.decode_record(msg))

        msg = 'H|\^&|||ABC|||||||D|1|'
        mapping.Header(*astm.decode_record(msg))

        msg = 'H|\^&|||ABC|||||||Q|1|'
        mapping.Header(*astm.decode_record(msg))

        msg = 'H|\^&|||ABC|||||||T|1|'
        mapping.Header(*astm.decode_record(msg))

        msg = 'H|\^&|||ABC|||||||FOO|1|'
        self.assertRaises(ValueError, mapping.Header, *astm.decode_record(msg))

    def test_strict_record_type(self):
        msg = 'A|\^&|||ABC|||||||P|1|'
        self.assertRaises(ValueError, mapping.Header, *astm.decode_record(msg))

    def test_invalid_timestamp(self):
        msg = 'H|\^&|||ABC|||||||T|1|123'
        self.assertRaises(ValueError, mapping.Header, *astm.decode_record(msg))


if __name__ == '__main__':
    unittest.main()

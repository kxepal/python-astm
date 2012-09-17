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


class PatientTestCase(unittest.TestCase):

    def test_decode(self):
        msg = 'P|1|119813;TGH|||Last 1^First 1|||F|'
        mapping.Patient(*astm.decode(msg))
        mapping.Patient(*astm.decode_record(msg))

    def test_encode(self):
        msg = 'P|1|119813;TGH|||Last 1^First 1|||F|||||||||||||||||'
        res = astm.encode_record(mapping.Patient(*astm.decode_record(msg)))
        self.assertEqual(msg, res)

    def test_strict_record_type(self):
        msg = 'D|1|119813;TGH|||Last 1^First 1|||F|'
        self.assertRaises(ValueError, mapping.Patient, *astm.decode_record(msg))

    def test_unknown_sex_if_missed(self):
        msg = 'P|1|119813;TGH|||Last 1^First 1||||'
        res = mapping.Patient(*astm.decode_record(msg))
        self.assertEqual('U', res.sex)

    def test_sex_field(self):
        msg = 'P|1|119813;TGH|||Last 1^First 1|||F|'
        mapping.Patient(*astm.decode_record(msg))

        msg = 'P|1|119813;TGH|||Last 1^First 1|||M|'
        mapping.Patient(*astm.decode_record(msg))

        msg = 'P|1|119813;TGH|||Last 1^First 1|||U|'
        mapping.Patient(*astm.decode_record(msg))

        msg = 'P|1|119813;TGH|||Last 1^First 1|||FOO|'
        self.assertRaises(ValueError, mapping.Patient, *astm.decode_record(msg))

    def test_birthdate(self):
        msg = 'P|1|119813;TGH|||Last 1^First 1||19901213|F'
        astm.encode_record(mapping.Patient(*astm.decode_record(msg)))

        msg = 'P|1|119813;TGH|||Last 1^First 1||12345|F|'
        self.assertRaises(ValueError, mapping.Patient, *astm.decode_record(msg))

        msg = 'P|1|119813;TGH|||Last 1^First 1||19901213010203|F'
        self.assertRaises(ValueError, mapping.Patient, *astm.decode_record(msg))

    def test_digital_sequence_number(self):
        msg = 'P|10|119813;TGH|||Last 1^First 1||19901213|F'
        astm.encode_record(mapping.Patient(*astm.decode_record(msg)))

        msg = 'P||119813;TGH|||Last 1^First 1||19901213|F'
        self.assertRaises(ValueError, mapping.Patient, *astm.decode_record(msg))

        msg = 'P|B|119813;TGH|||Last 1^First 1||19901213|F'
        self.assertRaises(ValueError, mapping.Patient, *astm.decode_record(msg))

        msg = 'P|-1|119813;TGH|||Last 1^First 1||19901213|F'
        self.assertRaises(ValueError, mapping.Patient, *astm.decode_record(msg))


if __name__ == '__main__':
    unittest.main()

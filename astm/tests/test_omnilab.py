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
from astm import decode_record
from astm.modules import omnilab


class OmnilabTestCase(unittest.TestCase):

    def test_header_request(self):
        data = 'H|\^&|||HOST^1.0.0|||||||P|E 1394-97|20091116104731'
        header = omnilab.Header.Request(*decode_record(data))
        self.assertEqual(header.type, 'H')
        self.assertEqual(header.sender.name, 'HOST')
        self.assertEqual(header.sender.version, '1.0.0')
        self.assertEqual(header.version, 'E 1394-97')
        self.assertEqual(header.timestamp,
                         datetime.datetime(2009, 11, 16, 10, 47, 31))

    def test_header_response(self):
        data = 'H|\^&|||LabOnline^1.0.0|||||||P|E 1394-97|20091116104731'
        header = omnilab.Header.Response(*decode_record(data))
        self.assertEqual(header.type, 'H')
        self.assertEqual(header.sender.name, 'LabOnline')
        self.assertEqual(header.sender.version, '1.0.0')
        self.assertEqual(header.version, 'E 1394-97')
        self.assertEqual(header.timestamp,
                         datetime.datetime(2009, 11, 16, 10, 47, 31))

    def test_patient_request(self):
        data = 'P|1|1212000|117118112||White^Nicky||19601218|M|||||Smith|37^years|0||||||||||CHIR'
        patient = omnilab.Patient.Request(*decode_record(data))
        self.assertEqual(patient.type, 'P')
        self.assertEqual(patient.seq, 1)
        self.assertEqual(patient.practice_id, '1212000')
        self.assertEqual(patient.laboratory_id, '117118112')
        self.assertEqual(patient.name.last, 'White')
        self.assertEqual(patient.name.first, 'Nicky')
        self.assertEqual(patient.birthdate, datetime.datetime(1960, 12, 18))
        self.assertEqual(patient.sex, 'M')
        self.assertEqual(patient.physician_id, 'Smith')
        self.assertEqual(patient.special_1.value, 37)
        self.assertEqual(patient.special_1.unit, 'years')
        self.assertEqual(patient.special_2, '0')
        self.assertEqual(patient.location, 'CHIR')

    def test_patient_response(self):
        data = 'P|1|12120001|117118112||White^Nicky||19601218|M|||||||0||||||||||CHIR'
        patient = omnilab.Patient.Response(*decode_record(data))
        self.assertEqual(patient.type, 'P')
        self.assertEqual(patient.seq, 1)
        self.assertEqual(patient.practice_id, '12120001')
        self.assertEqual(patient.laboratory_id, '117118112')
        self.assertEqual(patient.name.last, 'White')
        self.assertEqual(patient.name.first, 'Nicky')
        self.assertEqual(patient.birthdate, datetime.datetime(1960, 12, 18))
        self.assertEqual(patient.sex, 'M')
        self.assertEqual(patient.special_2, '0')
        self.assertEqual(patient.location, 'CHIR')

    def test_order_request(self):
        data = 'O|1|12120001||^^^NA^Sodium\^^^Cl^Clorum|R|20011023105715|20011023105715||||N||||S|||CHIM|AXM|Lab1|12120||||O|||||LAB2'
        order = omnilab.Order.Request(*decode_record(data))
        self.assertEqual(order.type, 'O')
        self.assertEqual(order.seq, 1)
        self.assertEqual(order.sample_id, '12120001')
        self.assertEqual(order.test[0].assay_code, 'NA')
        self.assertEqual(order.test[0].assay_name, 'Sodium')
        self.assertEqual(order.test[1].assay_code, 'Cl')
        self.assertEqual(order.test[1].assay_name, 'Clorum')
        self.assertEqual(order.priority, 'R')
        self.assertEqual(order.created_at,
                         datetime.datetime(2001, 10, 23, 10, 57, 15))
        self.assertEqual(order.sampled_at,
                         datetime.datetime(2001, 10, 23, 10, 57, 15))
        self.assertEqual(order.action_code, 'N')
        self.assertEqual(order.specimen_descriptor, 'S')
        self.assertEqual(order.user_field_1, 'CHIM')
        self.assertEqual(order.user_field_2, 'AXM')
        self.assertEqual(order.laboratory_field_1, 'Lab1')
        self.assertEqual(order.laboratory_field_2, '12120')
        self.assertEqual(order.report_type, 'O')
        self.assertEqual(order.laboratory, 'LAB2')

    def test_order_response(self):
        data = 'O|1|25140008|^1003^3|^^^Na^Sodium|R||19981023105715||||||||U|||CHIM|ARCH||251400||||F'
        order = omnilab.Order.Response(*decode_record(data))
        self.assertEqual(order.type, 'O')
        self.assertEqual(order.seq, 1)
        self.assertEqual(order.sample_id, '25140008')
        self.assertEqual(order.instrument.rack, '1003')
        self.assertEqual(order.instrument.position, '3')
        self.assertEqual(order.test.assay_code, 'Na')
        self.assertEqual(order.test.assay_name, 'Sodium')
        self.assertEqual(order.priority, 'R')
        self.assertEqual(order.created_at, None)
        self.assertEqual(order.sampled_at,
                         datetime.datetime(1998, 10, 23, 10, 57, 15))
        self.assertEqual(order.action_code, None)
        self.assertEqual(order.specimen_descriptor, 'U')
        self.assertEqual(order.user_field_1, 'CHIM')
        self.assertEqual(order.user_field_2, 'ARCH')
        self.assertEqual(order.laboratory_field_1, None)
        self.assertEqual(order.laboratory_field_2, '251400')
        self.assertEqual(order.report_type, 'F')
        self.assertEqual(order.laboratory, None)

    def test_result_request(self):
        data = 'R|1|^^^NA^Sodium|7.273|||||||||20091116104722|'
        result = omnilab.Result.Request(*decode_record(data))
        self.assertEqual(result.type, 'R')
        self.assertEqual(result.seq, 1)
        self.assertEqual(result.test.assay_code, 'NA')
        self.assertEqual(result.test.assay_name, 'Sodium')
        self.assertEqual(result.value, '7.273')
        self.assertEqual(result.completed_at,
                         datetime.datetime(2009, 11, 16, 10, 47, 22))

    def test_result_response(self):
        data = 'R|1|^^^NA^Sodium|7.273|mmol/l|10-120|0|N|F||Val.Autom.^Smith |201009261006|201009261034^201009261033|Architect'
        result = omnilab.Result.Response(*decode_record(data))
        self.assertEqual(result.type, 'R')
        self.assertEqual(result.seq, 1)
        self.assertEqual(result.test.assay_code, 'NA')
        self.assertEqual(result.test.assay_name, 'Sodium')
        self.assertEqual(result.units, 'mmol/l')
        self.assertEqual(result.references, '10-120')
        self.assertEqual(result.abnormal_flag, 0)
        self.assertEqual(result.abnormality_nature, 'N')
        self.assertEqual(result.status, 'F')
        self.assertEqual(result.operator.code_on_labonline, 'Val.Autom.')
        self.assertEqual(result.operator.code_on_analyzer, 'Smith ')
        self.assertEqual(result.started_at,
                         datetime.datetime(2010, 9, 26, 10, 0, 6))
        self.assertEqual(result.completed_at.labonline,
                         datetime.datetime(2010, 9, 26, 10, 3, 4))
        self.assertEqual(result.completed_at.analyzer,
                         datetime.datetime(2010, 9, 26, 10, 3, 3))
        self.assertEqual(result.instrument, 'Architect')

    def test_comment_request(self):
        data = 'C|1|L|SC^fully assured|G'
        comment = omnilab.Comment.Request(*decode_record(data))
        self.assertEqual(comment.source, 'L')
        self.assertEqual(comment.text.code, 'SC')
        self.assertEqual(comment.text.value, 'fully assured')
        self.assertEqual(comment.ctype, 'G')

        data = 'C|1|I|TC^test comment|G'
        comment = omnilab.Comment.Request(*decode_record(data))
        self.assertEqual(comment.source, 'I')
        self.assertEqual(comment.text.code, 'TC')
        self.assertEqual(comment.text.value, 'test comment')
        self.assertEqual(comment.ctype, 'G')

    def test_comment_response(self):
        data = 'C|1|I|SC^Sample contaminated|G'
        comment = omnilab.Comment.Request(*decode_record(data))
        self.assertEqual(comment.source, 'I')
        self.assertEqual(comment.text.code, 'SC')
        self.assertEqual(comment.text.value, 'Sample contaminated')
        self.assertEqual(comment.ctype, 'G')

    def test_terminator_request(self):
        data = 'L|1|N'
        term = omnilab.Terminator.Request(*decode_record(data))
        self.assertEqual(term.type, 'L')
        self.assertEqual(term.seq, '1')
        self.assertEqual(term.code, 'N')

    def test_terminator_response(self):
        data = 'L|1|N'
        term = omnilab.Terminator.Response(*decode_record(data))
        self.assertEqual(term.type, 'L')
        self.assertEqual(term.seq, '1')
        self.assertEqual(term.code, 'N')

    def test_sample_check_in(self):
        data = 'C|1|I|CK^APS^20100925102955|G'
        comment = omnilab.Comment.Request(*decode_record(data))
        self.assertEqual(comment.source, 'I')
        self.assertEqual(comment.text.code, 'CK')
        self.assertEqual(comment.text.value, 'APS')
        self.assertEqual(comment.text.field_1, '20100925102955')
        self.assertEqual(comment.ctype, 'G')

    def test_sample_seen(self):
        data = 'C|1|I|SE^APS^20100925102955|G'
        comment = omnilab.Comment.Request(*decode_record(data))
        self.assertEqual(comment.source, 'I')
        self.assertEqual(comment.text.code, 'SE')
        self.assertEqual(comment.text.value, 'APS')
        self.assertEqual(comment.text.field_1, '20100925102955')
        self.assertEqual(comment.ctype, 'G')

    def test_force_close(self):
        data = 'C|1|I|CL|G'
        comment = omnilab.Comment.Request(*decode_record(data))
        self.assertEqual(comment.source, 'I')
        self.assertEqual(comment.text.code, 'CL')
        self.assertEqual(comment.ctype, 'G')

    def test_add_test(self):
        data = 'C|1|I|TA|G'
        comment = omnilab.Comment.Request(*decode_record(data))
        self.assertEqual(comment.source, 'I')
        self.assertEqual(comment.text.code, 'TA')
        self.assertEqual(comment.ctype, 'G')

    def test_sample_storage(self):
        data = 'C|1|I|SS^1^5^35^APS^20100925104523|G'
        comment = omnilab.Comment.Request(*decode_record(data))
        self.assertEqual(comment.source, 'I')
        self.assertEqual(comment.text.code, 'SS')
        self.assertEqual(comment.text.value, '1')
        self.assertEqual(comment.text.field_1, '5')
        self.assertEqual(comment.text.field_2, '35')
        self.assertEqual(comment.text.field_3, 'APS')
        self.assertEqual(comment.text[-2], '20100925104523')
        self.assertEqual(comment.ctype, 'G')

    def test_host_query(self):
        data = 'C|1|I|HQ^CI8000_1^20100925103115|G'
        comment = omnilab.Comment.Request(*decode_record(data))
        self.assertEqual(comment.source, 'I')
        self.assertEqual(comment.text.code, 'HQ')
        self.assertEqual(comment.text.value, 'CI8000_1')
        self.assertEqual(comment.text[-5], '20100925103115')
        self.assertEqual(comment.ctype, 'G')

    def test_aliquoting(self):
        data = 'C|1|I|AL^SERUM^500^56^25^fe500^20100925083115|G'
        comment = omnilab.Comment.Request(*decode_record(data))
        self.assertEqual(comment.source, 'I')
        self.assertEqual(comment.text.code, 'AL')
        self.assertEqual(comment.text.value, 'SERUM')
        self.assertEqual(comment.text.field_1, '500')
        self.assertEqual(comment.text.field_2, '56')
        self.assertEqual(comment.text.field_3, '25')
        self.assertEqual(comment.text.field_4, 'fe500')
        self.assertEqual(comment.text.field_5, '20100925083115')
        self.assertEqual(comment.ctype, 'G')

    def test_primary_tube(self):
        data = 'C|1|I|PT^1^23^62^fe500^20100925083115|G'
        comment = omnilab.Comment.Request(*decode_record(data))
        self.assertEqual(comment.source, 'I')
        self.assertEqual(comment.text.code, 'PT')
        self.assertEqual(comment.text.value, '1')
        self.assertEqual(comment.text.field_1, '23')
        self.assertEqual(comment.text.field_2, '62')
        self.assertEqual(comment.text.field_3, 'fe500')
        self.assertEqual(comment.text.field_4, '20100925083115')
        self.assertEqual(comment.ctype, 'G')

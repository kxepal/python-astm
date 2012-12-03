# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Alexander Shorin
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

"""Common ASTM records structure."""


from datetime import datetime
from .mapping import (
    Record, ConstantField, DateTimeField, IntegerField, NotUsedField
)

__all__ = ['HeaderRecord', 'PatientRecord', 'OrderRecord',
           'ResultRecord' 'CommentRecord', 'TerminatorRecord']

HeaderRecord = Record.build(
    ConstantField(name='type', default='H'),
    ConstantField(name='delimeter', default='\^&'),
    NotUsedField(name='message_id'),
    NotUsedField(name='password'),
    NotUsedField(name='sender'),
    NotUsedField(name='address'),
    NotUsedField(name='reserved'),
    NotUsedField(name='phone'),
    NotUsedField(name='chars'),
    NotUsedField(name='receiver'),
    NotUsedField(name='comments'),
    ConstantField(name='processing_id', default='P'),
    NotUsedField(name='version'),
    DateTimeField(name='timestamp', default=datetime.now),
)

PatientRecord = Record.build(
    ConstantField(name='type', default='P'),
    IntegerField(name='seq', default=1),
    NotUsedField(name='practice_id'),
    NotUsedField(name='laboratory_id'),
    NotUsedField(name='id'),
    NotUsedField(name='name'),
    NotUsedField(name='maiden_name'),
    NotUsedField(name='birthdate'),
    NotUsedField(name='sex'),
    NotUsedField(name='race'),
    NotUsedField(name='address'),
    NotUsedField(name='reserved'),
    NotUsedField(name='phone'),
    NotUsedField(name='physician_id'),
    NotUsedField(name='special_1'),
    NotUsedField(name='special_2'),
    NotUsedField(name='height'),
    NotUsedField(name='weight'),
    NotUsedField(name='diagnosis'),
    NotUsedField(name='medication'),
    NotUsedField(name='diet'),
    NotUsedField(name='practice_field_1'),
    NotUsedField(name='practice_field_2'),
    NotUsedField(name='admission_date'),
    NotUsedField(name='admission_status'),
    NotUsedField(name='location'),
    NotUsedField(name='diagnostic_code_nature'),
    NotUsedField(name='diagnostic_code'),
    NotUsedField(name='religion'),
    NotUsedField(name='martial_status'),
    NotUsedField(name='isolation_status'),
    NotUsedField(name='language'),
    NotUsedField(name='hospital_service'),
    NotUsedField(name='hospital_institution'),
    NotUsedField(name='dosage_category'),
)

OrderRecord = Record.build(
    ConstantField(name='type', default='O'),
    IntegerField(name='seq', default=1),
    NotUsedField(name='sample_id'),
    NotUsedField(name='instrument_id'),
    NotUsedField(name='test'),
    NotUsedField(name='priority'),
    DateTimeField(name='created_at'),
    DateTimeField(name='sampled_at'),
    NotUsedField(name='collected_at'),
    NotUsedField(name='volume'),
    NotUsedField(name='collector'),
    NotUsedField(name='action_code'),
    NotUsedField(name='danger_code'),
    NotUsedField(name='clinical_info'),
    DateTimeField(name='delivered_at'),
    NotUsedField(name='specimen_descriptor'),
    NotUsedField(name='physician'),
    NotUsedField(name='physician_phone'),
    NotUsedField(name='user_field_1'),
    NotUsedField(name='user_field_2'),
    NotUsedField(name='laboratory_field_1'),
    NotUsedField(name='laboratory_field_2'),
    DateTimeField(name='modified_at'),
    NotUsedField(name='instrument_charge'),
    NotUsedField(name='instrument_section'),
    NotUsedField(name='report_type'),
    NotUsedField(name='reserved'),
    NotUsedField(name='location_ward'),
    NotUsedField(name='infection_flag'),
    NotUsedField(name='specimen_service'),
    NotUsedField(name='laboratory')
)

ResultRecord = Record.build(
    ConstantField(name='type', default='R'),
    IntegerField(name='seq', default=1),
    NotUsedField(name='test'),
    NotUsedField(name='value'),
    NotUsedField(name='units'),
    NotUsedField(name='reference_ranges'),
    NotUsedField(name='is_abnormal'),
    NotUsedField(name='abnormality_nature'),
    NotUsedField(name='status'),
    NotUsedField(name='normatives_changed_at'),
    NotUsedField(name='operator'),
    NotUsedField(name='started_at'),
    NotUsedField(name='completed_at'),
    NotUsedField(name='instrument'),
)

CommentRecord = Record.build(
    ConstantField(name='type', default='C'),
    IntegerField(name='seq', default=1),
    NotUsedField(name='source'),
    NotUsedField(name='text'),
    NotUsedField(name='type')
)

TerminatorRecord = Record.build(
    ConstantField(name='type', default='L'),
    IntegerField(name='seq', default=1),
    ConstantField(name='code', default='N')
)

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
    Record, ConstantField, DateTimeField, IntegerField, NotUsedField,
    TextField, RepeatedComponentField, Component

)

__all__ = ['HeaderRecord', 'PatientRecord', 'OrderRecord',
           'ResultRecord', 'CommentRecord', 'TerminatorRecord']

HeaderRecord = Record.build(
    ConstantField(name='type', default='H'),
    RepeatedComponentField(Component.build(
        ConstantField(name='_', default=''),
        TextField(name='__')
    ), name='delimeter'),
    # ^^^ workaround to define field:
    # ConstantField(name='delimeter', default='\^&'),
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
    DateTimeField(name='timestamp', default=datetime.now, required=True),
)

PatientRecord = Record.build(
    ConstantField(name='type', default='P'),
    IntegerField(name='seq', default=1, required=True),
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
    IntegerField(name='seq', default=1, required=True),
    NotUsedField(name='sample_id'),
    NotUsedField(name='instrument'),
    NotUsedField(name='test'),
    NotUsedField(name='priority'),
    NotUsedField(name='created_at'),
    NotUsedField(name='sampled_at'),
    NotUsedField(name='collected_at'),
    NotUsedField(name='volume'),
    NotUsedField(name='collector'),
    NotUsedField(name='action_code'),
    NotUsedField(name='danger_code'),
    NotUsedField(name='clinical_info'),
    NotUsedField(name='delivered_at'),
    NotUsedField(name='biomaterial'),
    NotUsedField(name='physician'),
    NotUsedField(name='physician_phone'),
    NotUsedField(name='user_field_1'),
    NotUsedField(name='user_field_2'),
    NotUsedField(name='laboratory_field_1'),
    NotUsedField(name='laboratory_field_2'),
    NotUsedField(name='modified_at'),
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
    IntegerField(name='seq', default=1, required=True),
    NotUsedField(name='test'),
    NotUsedField(name='value'),
    NotUsedField(name='units'),
    NotUsedField(name='references'),
    NotUsedField(name='abnormal_flag'),
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
    IntegerField(name='seq', default=1, required=True),
    NotUsedField(name='source'),
    NotUsedField(name='data'),
    NotUsedField(name='ctype')
)

TerminatorRecord = Record.build(
    ConstantField(name='type', default='L'),
    ConstantField(name='seq', default='1'),
    ConstantField(name='code', default='N')
)

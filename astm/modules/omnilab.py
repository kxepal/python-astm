# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Alexander Shorin
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from ..mapping import (
    Component, ConstantField, ComponentField, RepeatedComponentField,
    DateField, DateTimeField, IntegerField, SetField, TextField, NotUsedField
)
from ..records import (
    HeaderRecord, PatientRecord, OrderRecord, CommentRecord, ResultRecord,
    TerminatorRecord
)

Sender = Component.build(
    TextField(name='name'),
    TextField(name='version')
)

PatientName = Component.build(
    TextField(name='last', length=50),
    TextField(name='first', length=50)
)

PatientAge = Component.build(
    IntegerField(name='value'),
    SetField(name='unit', values=('years', 'months', 'days'))
)

Test = Component.build(
    NotUsedField(name='_'),
    NotUsedField(name='__'),
    NotUsedField(name='___'),
    TextField(name='assay_code', required=True, length=20),
    TextField(name='assay_name', length=8),
)

TestEx = Component.build(
    NotUsedField(name='_'),
    NotUsedField(name='__'),
    NotUsedField(name='___'),
    TextField(name='assay_code', required=True, length=20),
    TextField(name='assay_name', length=8),
    TextField(name='dilution', length=10),
    TextField(name='status', length=1),
    TextField(name='reagent_lot', length=15),
    TextField(name='reagent_number', length=5),
    TextField(name='control_lot', length=25),
    SetField(name='type', values=('CE', 'TX'))
)

Operator = Component.build(
    TextField(name='code_on_labonline', length=12),
    TextField(name='code_on_analyzer', length=20),
)

CompletionDate = Component.build(
    DateTimeField(name='labonline'),
    DateTimeField(name='analyzer'),
)

CommentText = Component.build(
    SetField(name='code', values=(
        'PC', 'RC', 'SC', 'TC', # from host to mw
        'CK', 'SE', 'CL', 'TA', 'SS', 'HQ', 'AL', 'PT' # from mw to host

    )),
    TextField(name='value'),
    TextField(name='field_1'),
    TextField(name='field_2'),
    TextField(name='field_3'),
    TextField(name='field_4'),
    TextField(name='field_5'),
)

Instrument = Component.build(
    NotUsedField(name='_'),
    TextField(name='rack', length=5),
    TextField(name='position', length=3),
)

class Header(object):
    class Common(HeaderRecord):
        sender = ComponentField(Sender)
        processing_id = ConstantField(default='P')
        version = ConstantField(default='E 1394-97')

    class Request(Common):
        pass

    class Response(Common):
        pass


class Patient(object):
    class Common(PatientRecord):
        birthdate = DateField()
        laboratory_id = TextField(required=True, length=16)
        location = TextField(length=20)
        name = ComponentField(PatientName)
        practice_id = TextField(required=True, length=12)
        sex = SetField(values=('M', 'F', None, 'I'))
        special_2 = SetField(values=('0', '1'))

    class Request(Common):
        physician_id = TextField(length=35)
        special_1 = ComponentField(PatientAge)

    class Response(Common):
        pass


class Order(object):
    class Common(OrderRecord):
        created_at = DateTimeField(required=True)
        laboratory_field_2 = TextField(length=12)
        priority = SetField(default='S', values=('S', 'R'))
        sampled_at = DateTimeField()
        sample_id = TextField(required=True, length=12)
        specimen_descriptor = TextField(length=20)
        user_field_1 = TextField(length=20)
        user_field_2 = TextField(length=1024)

    class Request(Common):
        action_code = SetField(default='N', values=('C', 'A', 'N', 'R'))
        laboratory = TextField(length=20)
        laboratory_field_1 = TextField(length=20)
        report_type = ConstantField(default='O')
        test = RepeatedComponentField(Test)

    class Response(Common):
        action_code = SetField(values=(None, 'Q'))
        instrument = ComponentField(Instrument)
        report_type = ConstantField(default='F')
        test = ComponentField(Test)


class Result(object):
    class Common(ResultRecord):
        completed_at = DateTimeField(required=True)
        value = TextField(required=True, length=20)

    class Request(Common):
        test = ComponentField(Test)

    class Response(Common):
        abnormal_flag = SetField(
            field=IntegerField(),
            length=4,
            values=(0, 1, 2, 3,
                    10, 11, 12, 13,
                    1000, 1001, 1002, 1003),
        )
        abnormality_nature = SetField(values=('N', 'L', 'H', 'LL', 'HH'))
        completed_at = ComponentField(CompletionDate)
        instrument = TextField(length=16)
        operator = ComponentField(Operator)
        references = TextField()
        started_at = DateTimeField(required=True)
        status = SetField(values=('F', 'R'))
        test = ComponentField(TestEx)
        units = TextField(length=20)


class Comment(object):
    class Common(CommentRecord):
        source = SetField(default='L', values=('L', 'I'))
        text = ComponentField(CommentText)
        ctype = ConstantField(default='G')

    class Request(Common):
        pass

    class Response(Common):
        pass


class Terminator(object):
    class Common(TerminatorRecord):
        pass

    class Request(Common):
        pass

    class Response(Common):
        pass


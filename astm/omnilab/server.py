# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Alexander Shorin
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

"""

``astm.omnilab.server`` - LabOnline server implementation
----------------------------------------------------------

"""

from astm.server import BaseRecordsDispatcher
from astm.mapping import (
    Component, ConstantField, ComponentField, DateTimeField, IntegerField,
    SetField, TextField, NotUsedField, DateField
)
from .common import (
    Header, Terminator, CommonPatient as Patient,
    CommonOrder,
    CommonResult,
    CommonComment,
    Sender
)


__all__ = ['RecordsDispatcher',
           'Header', 'Patient', 'Order', 'Result', 'Terminator',
           'CommentData', 'CompletionDate', 'Instrument', 'Operator',
           'Sender', 'Test']

#: Instrument (analyser) information structure.
#:
#: :param _: Reserved. Not used.
#: :type _: None
#:
#: :param rack: Rack number. Length: 5.
#: :type rack: str
#:
#: :param position: Position number. Length: 3.
#: :type position: str
#:
Instrument = Component.build(
    TextField(name='_'),
    TextField(name='rack', length=5),
    TextField(name='position', length=3),
)


#: Test :class:`~astm.mapping.Component` also known as Universal Test ID.
#:
#: :param _: Reserved. Not used.
#: :type _: None
#:
#: :param __: Reserved. Not used.
#: :type __: None
#:
#: :param ___: Reserved. Not used.
#: :type ___: None
#:
#: :param assay_code: Assay code. Required. Length: 20.
#: :type assay_code: str
#:
#: :param assay_name: Assay name. Length: 8.
#: :type assay_name: str
#:
#: :param dilution: Dilution. Length: 10.
#: :type dilution: str
#:
#: :param status: Assay status. Length: 1.
#: :type status: str
#:
#: :param reagent_lot: Reagent lot. Length: 15.
#: :type reagent_lot: str
#:
#: :param reagent_number: Reagent serial number. Length: 5.
#: :type reagent_number: str
#:
#: :param control_lot: Control lot number. Length: 25.
#: :type control_lot: str
#:
#: :param type: Result type value. One of: ``CE``, ``TX``.
#: :type type: str
#:
Test = Component.build(
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


#: Information about operator that validated results.
#:
#: :param code_on_labonline: Operator code on LabOnline. Length: 12.
#: :type code_on_labonline: str
#:
#: :param code_on_analyzer: Operator code on analyser. Length: 20.
#: :type code_on_analyzer: str
#:
Operator = Component.build(
    TextField(name='code_on_labonline', length=12),
    TextField(name='code_on_analyzer', length=20),
)


#: Completion date time information.
#:
#: :param labonline: Completion date time on LabOnline.
#: :type labonline: datetime.datetime
#:
#: :param analyzer: Completion date time on analyser.
#: :type analyzer: datetime.datetime
#:
CompletionDate = Component.build(
    DateTimeField(name='labonline'),
    DateTimeField(name='analyzer'),
)

#: Instrument (analyser) information structure.
#:
#: :param _: Reserved. Not used.
#: :type _: None
#:
#: :param rack: Rack number. Length: 5.
#: :type rack: str
#:
#: :param position: Position number. Length: 3.
#: :type position: str
#:
Instrument = Component.build(
    NotUsedField(name='_'),
    TextField(name='rack', length=5),
    TextField(name='position', length=3),
)

#: Comment control text structure.
#:
CommentData = Component.build(
    SetField(name='code', values=('PC', 'RC', 'SC', 'TC',
        'CK', 'SE', 'CL', 'TA', 'SS', 'HQ', 'AL', 'PT')),
    TextField(name='value'),
    TextField(name='field_1'),
    TextField(name='field_2'),
    TextField(name='field_3'),
    TextField(name='field_4'),
    TextField(name='field_5'),
)


class Order(CommonOrder):
    """ASTM order record.

    :param type: Record Type ID. Always ``O``.
    :type type: str

    :param seq: Sequence Number. Required.
    :type seq: int

    :param sample_id: Sample ID number. Required. Length: 12.
    :type sample_id: str

    :param instrument: Instrument specimen ID.
    :type instrument: :class:`Instrument`

    :param test: Test information structure (aka Universal Test ID).
    :type test: :class:`Test`

    :param priority: Priority flag. Required. Possible values:
                     - ``S``: stat; -``R``: routine.
    :type priority: str

    :param created_at: Ordered date and time. Required.
    :type created_at: datetime.datetime

    :param sampled_at: Specimen collection date and time.
    :type sampled_at: datetime.datetime

    :param collected_at: Collection end time. Not used.
    :type collected_at: None

    :param volume: Collection volume. Not used.
    :type volume: None

    :param collector: Collector ID. Not used.
    :type collector: None

    :param action_code: Action code. Required. Possible values:
                        - :const:`None`: normal order result;
                        - ``Q``: quality control;
    :type action_code: str

    :param danger_code: Danger code. Not used.
    :type danger_code: None

    :param clinical_info: Revelant clinical info. Not used.
    :type clinical_info: None

    :param delivered_at: Date/time specimen received.
    :type delivered_at: None

    :param biomaterial: Sample material code. Length: 20.
    :type biomaterial: str

    :param physician: Ordering Physician. Not used.
    :type physician: None

    :param physician_phone: Physician's phone number. Not used.
    :type physician_phone: None

    :param user_field_1: An optional field, it will be send back unchanged to
                         the host along with the result. Length: 20.
    :type user_field_1: str

    :param user_field_2: An optional field, it will be send back unchanged to
                         the host along with the result. Length: 1024.
    :type user_field_2: str

    :param laboratory_field_1: Laboratory field #1. Not used.
    :type laboratory_field_1: None

    :param laboratory_field_2: Primary tube code. Length: 12.
    :type laboratory_field_2: str

    :param modified_at: Date and time of last result modification. Not used.
    :type modified_at: None

    :param instrument_charge: Instrument charge to computer system. Not used.
    :type instrument_charge: None

    :param instrument_section: Instrument section id. Not used.
    :type instrument_section: None

    :param report_type: Report type. Always ``F`` which means final order
                        request.
    :type report_type: str

    :param reserved: Reserved. Not used.
    :type reserved: None

    :param location_ward: Location ward of specimen collection. Not used.
    :type location_ward: None

    :param infection_flag: Nosocomial infection flag. Not used.
    :type infection_flag: None

    :param specimen_service: Specimen service. Not used.
    :type specimen_service: None

    :param laboratory: Production laboratory. Not used.
    :type laboratory: None
    """
    action_code = SetField(values=(None, 'Q'))
    instrument = ComponentField(Instrument)
    report_type = ConstantField(default='F')
    test = ComponentField(Test)


class Result(CommonResult):
    """ASTM patient record.

    :param type: Record Type ID. Always ``R``.
    :type type: str

    :param seq: Sequence Number. Required.
    :type seq: int

    :param test: Test information structure (aka Universal Test ID).
    :type test: :class:`Test`

    :param value: Measurement value. Numeric, coded or free text value
                  depending on result type. Required. Length: 1024.
    :type value: None

    :param units: Units. Length: 20.
    :type units: str

    :param references: Normal reference value interval.
    :type references: str

    :param abnormal_flag: Result abnormal flag. Possible values:
                          - ``0``: normal result;
                          - ``1``: result out of normal values;
                          - ``2``: result out of attention values;
                          - ``3``: result out of panic values;
                          +10 Delta-check;
                          +1000 Device alarm.
                          Length: 4.
    :type abnormal_flag: str

    :param abnormality_nature: Nature of abnormality testing. Possible values:
                               - ``N``: normal value;
                               - ``L``: below low normal range;
                               - ``H``: above high normal range;
                               - ``LL``: below low critical range;
                               - ``HH``: above high critical range.
    :type abnormality_nature: str

    :param status: Result status. ``F`` indicates a final result;
                   ``R`` indicating rerun. Length: 1.
    :type status: str

    :param normatives_changed_at: Date of changes in instrument normative
                                  values or units. Not used.
    :type normatives_changed_at: None

    :param operator: Operator ID.
    :type operator: :class:`Operator`

    :param started_at: When works on test was started on.
    :type started_at: datetime.datetime

    :param completed_at: When works on test was done.
    :type completed_at: datetime.datetime

    :param instrument: Instrument ID. Required.
    :type instrument: :class:`Instrument`
    """
    abnormal_flag = SetField(
        field=IntegerField(),
        length=4,
        values=(0, 1, 2, 3,
                10, 11, 12, 13,
                1000, 1001, 1002, 1003,
                1010, 1011, 1012, 1013))
    abnormality_nature = SetField(values=('N', 'L', 'H', 'LL', 'HH'))
    completed_at = ComponentField(CompletionDate)
    created_at = DateField()
    instrument = TextField(length=16)
    operator = ComponentField(Operator)
    references = TextField()
    sampled_at = DateField()
    started_at = DateTimeField(required=True)
    status = SetField(values=('F', 'R'))
    test = ComponentField(Test)
    units = TextField(length=20)


class Comment(CommonComment):
    """ASTM patient record.

    :param type: Record Type ID. Always ``C``.
    :type type: str

    :param seq: Sequence Number. Required.
    :type seq: int

    :param source: Comment source. Always ``I``.
    :type source: str

    :param data: Measurement value. Numeric, coded or free text value
                  depending on result type. Required. Length: 1024.
    :type data: :class:`CommentData`

    :param ctype: Comment type. Always ``G``.
    :type ctype: str
    """
    source = ConstantField(default='I')
    data = ComponentField(CommentData)


class RecordsDispatcher(BaseRecordsDispatcher):
    """Omnilab specific records dispatcher. Automatically wraps records by
    related mappings."""
    def __init__(self, *args, **kwargs):
        super(RecordsDispatcher, self).__init__(*args, **kwargs)
        self.wrappers = {
            'H': Header,
            'P': Patient,
            'O': Order,
            'R': Result,
            'C': Comment,
            'L': Terminator
        }

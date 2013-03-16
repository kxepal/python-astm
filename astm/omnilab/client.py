# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Alexander Shorin
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

"""

``astm.omnilab.client`` - LabOnline client implementation
----------------------------------------------------------

"""

from astm.mapping import (
    Component, ConstantField, ComponentField, IntegerField, DateTimeField,
    RepeatedComponentField, SetField, TextField, NotUsedField
)
from .common import (
    Header, Terminator,
    CommonPatient,
    CommonOrder,
    CommonResult,
    CommonComment,
    Sender
)

__all__ = ['Header', 'Patient', 'Order', 'Result', 'Comment', 'Terminator',
           'CommentData', 'PatientAge', 'Sender', 'Test']

#: Patient age structure.
#:
#: :param value: Age value.
#: :type value: int
#:
#: :param unit: Age unit. One of: ``years``, ``months``, ``days``.
#: :type unit: str
#:
PatientAge = Component.build(
    IntegerField(name='value'),
    SetField(name='unit', values=('years', 'months', 'days'))
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
Test = Component.build(
    NotUsedField(name='_'),
    NotUsedField(name='__'),
    NotUsedField(name='___'),
    TextField(name='assay_code', required=True, length=20),
    TextField(name='assay_name', length=8),
)

#: Comment control data structure.
#:
CommentData = Component.build(
    SetField(name='code', values=('PC', 'RC', 'SC', 'TC')),
    TextField(name='value')
)


class Patient(CommonPatient):
    """ASTM patient record.

    :param type: Record Type ID. Always ``P``.
    :type type: str

    :param seq: Sequence Number. Required.
    :type seq: int

    :param practice_id: Practice Assigned Patient ID. Required. Length: 12.
    :type practice_id: str

    :param laboratory_id: Laboratory Assigned Patient ID. Required. Length: 16.
    :type laboratory_id: str

    :param id: Patient ID. Not used.
    :type id: None

    :param name: Patient name.
    :type name: :class:`PatientName`

    :param maiden_name: Mother’s Maiden Name. Not used.
    :type maiden_name: None

    :param birthdate: Birthdate.
    :type birthdate: datetime.date

    :param sex: Patient Sex. One of: ``M`` (male), ``F`` (female),
                ``I`` (animal), ``None`` is unknown.
    :type sex: str

    :param race: Patient Race-Ethnic Origin. Not used.
    :type race: None

    :param address: Patient Address. Not used.
    :type address: None

    :param reserved: Reserved Field. Not used.
    :type reserved: None

    :param phone: Patient Telephone Number. Not used.
    :type phone: None

    :param physician_id: Attending Physician. Not used.
    :type physician_id: None

    :param special_1: Special Field #1. Not used.
    :type special_1: None

    :param special_2: Patient source. Possible values:
      - ``0``: internal patient;
      - ``1``: external patient.
    :type special_2: int

    :param height: Patient Height. Not used.
    :type height: None

    :param weight: Patient Weight. Not used.
    :type weight: None

    :param diagnosis: Patient’s Known Diagnosis. Not used.
    :type diagnosis: None

    :param medications: Patient’s Active Medications. Not used.
    :type medications: None

    :param diet: Patient’s Diet. Not used.
    :type diet: None

    :param practice_1: Practice Field No. 1. Not used.
    :type practice_1: None

    :param practice_2: Practice Field No. 2. Not used.
    :type practice_2: None

    :param admission_date: Admission/Discharge Dates. Not used.
    :type admission_date: None

    :param admission_status: Admission Status. Not used.
    :type admission_status: None

    :param location: Patient location. Length: 20.
    :type location: str

    :param diagnostic_code_nature: Nature of diagnostic code. Not used.
    :type diagnostic_code_nature: None

    :param diagnostic_code: Diagnostic code. Not used.
    :type diagnostic_code: None

    :param religion: Patient religion. Not used.
    :type religion: None

    :param martial_status: Martian status. Not used.
    :type martial_status: None

    :param isolation_status: Isolation status. Not used.
    :type isolation_status: None

    :param language: Language. Not used.
    :type language: None

    :param hospital_service: Hospital service. Not used.
    :type hospital_service: None

    :param hospital_institution: Hospital institution. Not used.
    :type hospital_institution: None

    :param dosage_category: Dosage category. Not used.
    :type dosage_category: None
    """
    physician_id = TextField(length=35)
    special_1 = ComponentField(PatientAge)


class Order(CommonOrder):
    """ASTM order record.

    :param type: Record Type ID. Always ``O``.
    :type type: str

    :param seq: Sequence Number. Required.
    :type seq: int

    :param sample_id: Sample ID number. Required. Length: 12.
    :type sample_id: str

    :param instrument: Instrument specimen ID. Not used.
    :type instrument: None

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
                        - ``C``: cancel works for specified tests;
                        - ``A``: add tests to existed specimen;
                        - ``N``: create new order;
                        - ``R``: rerun tests for specified order;
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

    :param laboratory_field_1: In multi-laboratory environment it will be used
                               to indicate which laboratory entering the order.
                               Length: 20.
    :type laboratory_field_1: str

    :param laboratory_field_2: Primary tube code. Length: 12.
    :type laboratory_field_2: str

    :param modified_at: Date and time of last result modification. Not used.
    :type modified_at: None

    :param instrument_charge: Instrument charge to computer system. Not used.
    :type instrument_charge: None

    :param instrument_section: Instrument section id. Not used.
    :type instrument_section: None

    :param report_type: Report type. Always ``O`` which means normal order
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

    :param laboratory: Production laboratory: in multi-laboratory environment
                       indicates laboratory expected to process the order.
                       Length: 20.
    :type laboratory: str
    """
    action_code = SetField(default='N', values=('C', 'A', 'N', 'R'))
    created_at = DateTimeField(required=True)
    laboratory = TextField(length=20)
    laboratory_field_1 = TextField(length=20)
    report_type = ConstantField(default='O')
    sampled_at = DateTimeField()
    test = RepeatedComponentField(Test)


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

    :param units: Units. Not used.
    :type units: None

    :param references: Reference ranges. Not used.
    :type references: None

    :param abnormal_flag: Result abnormal flag. Not used.
    :type abnormal_flag: None

    :param abnormality_nature: Nature of abnormality testing. Not used.
    :type abnormality_nature: None

    :param status: Result status. Not used.
    :type status: None

    :param normatives_changed_at: Date of changes in instrument normative
                                  values or units. Not used.
    :type normatives_changed_at: None

    :param operator: Operator ID. Not used.
    :type operator: None

    :param started_at: When works on test was started on. Not used.
    :type started_at: None

    :param completed_at: When works on test was done. Required.
    :type completed_at: datetime.datetime

    :param instrument: Instrument ID. Not used.
    :type instrument: None
    """
    test = ComponentField(Test)


class Comment(CommonComment):
    """ASTM patient record.

    :param type: Record Type ID. Always ``C``.
    :type type: str

    :param seq: Sequence Number. Required.
    :type seq: int

    :param source: Comment source. Always ``L``.
    :type source: str

    :param data: Measurement value. Numeric, coded or free text value
                  depending on result type. Required. Length: 1024.
    :type data: :class:`CommentData`

    :param ctype: Comment type. Always ``G``.
    :type ctype: str
    """
    source = ConstantField(default='L')
    data = ComponentField(CommentData)

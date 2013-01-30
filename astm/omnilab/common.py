# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Alexander Shorin
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from astm import __version__
from astm.mapping import (
    Component, ConstantField, ComponentField, DateField, DateTimeField,
    IntegerField, SetField, TextField
)
from astm.records import (
    HeaderRecord, PatientRecord, OrderRecord, ResultRecord, CommentRecord,
    TerminatorRecord
)

#: Information about sender.
#:
#: :param name: Name.
#: :type name: str
#:
#: :param version: Sender software version.
#: :type version: str
#:
Sender = Component.build(
    TextField(name='name', default='python-astm'),
    TextField(name='version', default=__version__)
)


#: Patient name structure.
#:
#: :param last: Last name. Length: 50.
#: :type last: str
#:
#: :param first: First name. Length: 50.
#: :type first: str
#:
PatientName = Component.build(
    TextField(name='last', length=50),
    TextField(name='first', length=50)
)


class Header(HeaderRecord):
    """ASTM header record.

    :param type: Record Type ID. Always ``H``.
    :type type: str

    :param delimeter: Delimiter Definition. Always ``\^&``.
    :type delimeter: str

    :param message_id: Message Control ID. Not used.
    :type message_id: None

    :param password: Access Password. Not used.
    :type password: None

    :param sender: Information about sender. Optional.
    :type sender: :class:`Sender`

    :param address: Sender Street Address. Not used.
    :type address: None

    :param reserved: Reserved Field. Not used.
    :type reserved: None

    :param phone: Sender Telephone Number. Not used.
    :type phone: None

    :param chars: Sender Characteristics. Not used.
    :type chars: None

    :param receiver: Information about receiver. Not used.
    :type receiver: None

    :param comments: Comments. Not used.
    :type comments: None

    :param processing_id: Processing ID. Always ``P``.
    :type processing_id: str

    :param version: ASTM Version Number. Always ``E 1394-97``.
    :type version: str

    :param timestamp: Date and Time of Message
    :type timestamp: datetime.datetime
    """

    sender = ComponentField(Sender)
    processing_id = ConstantField(default='P')
    version = ConstantField(default='E 1394-97')


class Patient(PatientRecord):
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
    birthdate = DateField()
    laboratory_id = TextField(required=True, length=16)
    location = TextField(length=20)
    name = ComponentField(PatientName)
    practice_id = TextField(required=True, length=12)
    sex = SetField(values=('M', 'F', None, 'I'))
    special_2 = SetField(values=(0, 1), field=IntegerField())


class Order(OrderRecord):
    biomaterial = TextField(length=20)
    created_at = DateTimeField(required=True)
    laboratory_field_2 = TextField(length=12)
    priority = SetField(default='S', values=('S', 'R'))
    sample_id = TextField(required=True, length=12)
    sampled_at = DateTimeField()
    user_field_1 = TextField(length=20)
    user_field_2 = TextField(length=1024)


class Result(ResultRecord):
    completed_at = DateTimeField(required=True)
    value = TextField(required=True, length=20)


class Comment(CommentRecord):
    ctype = ConstantField(default='G')


class Terminator(TerminatorRecord):
    """ASTM terminator record.

    :param type: Record Type ID. Always ``L``.
    :type type: str

    :param seq: Sequential number. Always ``1``.
    :type seq: int

    :param code: Termination code. Always ``N``.
    :type code: str
    """

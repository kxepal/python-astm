# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Alexander Shorin
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from datetime import datetime
from collections import namedtuple
from itertools import repeat
try:
    from itertools import izip, izip_longest
except ImportError: # Python 3
    from itertools import zip_longest as izip_longest
    izip = zip

#: Processing ID values.
#:   - ``P``: Production.
#:   - ``D``: Debugging.
#:   - ``Q``: Quality Control.
#:   - ``T``
PROCESSING_IDS = frozenset(['P', 'D', 'Q', 'T'])

#: Patient sex.
#:   - ``M``: Male
#:   - ``F``: Female
#:   - ``U``: Unknown
SEX = frozenset(['M', 'F', 'U'])

#: Termination codes.
#:   - ``N``: Normal termination.
#:   - ``I``: Information not available on last request.
#:   - ``F``: Finished processing last request.
TERMINATION_CODES = frozenset(['N', 'I', 'F'])

def maybe_unpack_to_list(value, length):
    if isinstance(value, (str, type(None))):
        value = [value]
    # Python 3 workaround
    for items in zip(*izip_longest(value, repeat(None, length))):
        return items

class ASTMObject(object):
    """Base ASTM record object"""

    @staticmethod
    def _make_kwargs(func, args, kwargs):
        # fallback to Python 3 case
        func_code = getattr(func, 'func_code', getattr(func, '__code__'))
        d = dict(izip_longest(func_code.co_varnames[1:], args))
        d.update(kwargs)
        return d


class ASTMRecord(ASTMObject):
    pass


class ASTMComponent(ASTMObject):
    pass

_Header = namedtuple('_Header', [
    'type',
    'delimeter',
    'mid',
    'password',
    'sender',
    'address',
    'reserved',
    'phone',
    'chars',
    'receiver',
    'comments',
    'procid',
    'version',
    'timestamp'
])

_SenderID = namedtuple('_SenderID', [
    'name',
    'version',
    'serial',
    'ivc'
])

_ReceiverID = namedtuple('_ReceiverID', [
    'host',
    'ipaddr'
])

_Patient = namedtuple('_Patient', [
    'type',
    'seq',
    'pa_pid',
    'la_pid',
    'pid',
    'name',
    'maiden_name',
    'birthdate',
    'sex',
    'race',
    'address',
    'reserved',
    'phone',
    'physician_id',
    'special_1',
    'special_2',
    'height',
    'weight',
    'diagnosis',
    'medications',
    'diet',
    'practice_1',
    'practice_2',
    'admission_date',
    'admission_status',
    'location'
])

_PatientName = namedtuple('_PatientName', [
    'last',
    'first',
    'middle',
    'suffix',
    'title'
])

_PatientDiagnosis = namedtuple('_PatientDiagnosis', [
    'code',
    'description'
])

_PatientMedications = namedtuple('_PatientMedications', [
    'name',
    'level',
    'start_date',
    'enc_date'
])

_Terminator = namedtuple('_Terminator', [
    'type',
    'seq',
    'code'
])


class SenderID(_SenderID, ASTMComponent):
    """Sender Name or ID field of ASTM :class:`Header` record.

    :param name: Instrument/System Name.
    :param version: Instrument/System Software Version Number.
    :param serial: Instrument/System Serial Number.
    :param ivc: Interface Version Control.
    """
    __slots__ = ()


class ReceiverID(_ReceiverID, ASTMComponent):
    """Receiver ID field of ASTM :class:`Header` record.

    :param host: Host name.
    :param ipaddr: IP address.
    """
    __slots__ = ()


class Header(_Header, ASTMRecord):
    """ASTM header record.

    :param type: Record Type ID. Always ``H``.
    :param delimeter: Delimiter Definition.
    :param mid: Message Control ID.
    :param password: Access Password.
    :param sender: :class:`Sender Name or ID <SenderID>`.
    :param address: Sender Street Address.
    :param reserved: Reserved Field.
    :param phone: Sender Telephone Number.
    :param chars: Sender Characteristics.
    :param receiver: :class:`Receiver ID <ReceiverID>`.
    :param comments: Comments.
    :param procid: Processing ID.
    :param version: ASTM Version Number.
    :param timestamp: Date/Time of Message.
    """
    __slots__ = ()

    def __new__(cls, *args, **kwargs):
        kwargs = cls._make_kwargs(_Header.__new__, args, kwargs)

        kwargs['_cls'] = cls
        if kwargs['type'] != 'H':
            raise ValueError('Record type should be `H`, got %r',
                             kwargs['type'])
        kwargs['sender'] = SenderID(
            *maybe_unpack_to_list(kwargs['sender'], 4))
        kwargs['receiver'] = ReceiverID(
            *maybe_unpack_to_list(kwargs['receiver'], 2))

        if kwargs['procid'] and kwargs['procid'] not in PROCESSING_IDS:
            raise ValueError('Processing ID (`procid`) should be one of: %r'
                             '' % PROCESSING_IDS)

        if kwargs['timestamp']:
            datetime.strptime(kwargs['timestamp'], '%Y%m%d%H%M%S')
        else:
            kwargs['timestamp'] = datetime.now().strftime('%Y%m%d%H%M%S')

        return super(Header, cls).__new__(**kwargs)


class PatientName(_PatientName, ASTMComponent):
    """Patient name field of ASTM :class:`Patient` record.

    :param last: Last name.
    :param first: First name.
    :param middle: Middle name.
    :param suffix: Suffix (Jr.,Sr., etc.).
    :param title: Title (Mr., Mrs., Ms., etc.).
    """
    __slots__ = ()


class PatientDiagnosis(_PatientDiagnosis, ASTMComponent):
    """Patient diagnosis field of ASTM :class:`Patient` record.

    :param code: Code.
    :param description: Text description for the code.
    """
    __slots__ = ()


class PatientMedications(_PatientMedications, ASTMComponent):
    """Patient active medications of ASTM :class:`Patient` record.

    :param name: Identifies the therapy name or generic drug name.
    :param level: Identifies the amount or dosage of drug or therapy as well as
                  the frequency
    :param start_date: Refers to the beginning date of the therapy or
                       medication.
    :param end_date: Refers to the stop date of the therapy or medication.
    """
    __slots__ = ()


class Patient(_Patient, ASTMRecord):
    """ASTM patient record.

    :param type: Record Type ID.
    :param seq: Sequence Number.
    :param pa_pid: Practice Assigned Patient ID.
    :param la_pid: Laboratory Assigned Patient ID.
    :param pid: Patient ID.
    :param name: :class:`Patient Name <PatientName>`.
    :param birthdate: Birthdate.
    :param sex: Patient Sex.
    :param maiden_name: Mother’s Maiden Name.
    :param race: Patient Race-Ethnic Origin.
    :param address: Patient Address.
    :param reserved: Reserved Field.
    :param phone: Patient Telephone Number.
    :param apid: Attending Physician.
    :param special_1: Special Field #1.
    :param special_2: Special Field #2.
    :param height: Patient Height.
    :param weight: Patient Weight.
    :param diagnosis: Patient’s Known Diagnosis.
    :param medications: Patient’s Active Medications.
    :param diet: Patient’s Diet.
    :param practice_1: Practice Field No. 1.
    :param practice_2: Practice Field No. 2.
    :param admission_date: Admission/Discharge Dates.
    :param admission_status: Admission Status.
    :param location: Location.
    """
    __slots__ = ()

    def __new__(cls, *args, **kwargs):
        kwargs = cls._make_kwargs(_Patient.__new__, args, kwargs)

        kwargs['_cls'] = cls
        if kwargs['type'] != 'P':
            raise ValueError('Record `type` should be `P`, got %r',
                             kwargs['type'])

        if not kwargs['seq'].isdigit():
            raise ValueError('Record `seq` should be digital, got %r',
                             kwargs['seq'])

        if kwargs['birthdate']:
            datetime.strptime(kwargs['birthdate'], '%Y%m%d')

        kwargs['name'] = PatientName(
            *maybe_unpack_to_list(kwargs['name'], 5))
        kwargs['diagnosis'] = PatientDiagnosis(
            *maybe_unpack_to_list(kwargs['diagnosis'], 2))
        kwargs['medications'] = PatientMedications(
            *maybe_unpack_to_list(kwargs['medications'], 4))

        if not kwargs['sex']:
            kwargs['sex'] = 'U'
        if kwargs['sex'] not in SEX:
            raise ValueError('Patient sex should be one of: %s' % SEX)

        return super(Patient, cls).__new__(**kwargs)


class Terminator(_Terminator, ASTMRecord):
    """ASTM terminator record.

    :param type: Record Type ID. Always ``L``.
    :param seq: Sequential number. Always ``1``.
    :param code: Termination code.
    """

    def __new__(cls, type='L', seq='1', code='N'):
        if type != 'L':
            raise ValueError('Record ID type should be `L`, got %r' % type)

        if seq != '1':
            raise ValueError('Field `seq` should be `1`, got %r' % seq)

        if code not in TERMINATION_CODES:
            raise ValueError('Termication `code` should be one of %s'
                             '' % TERMINATION_CODES)

        return super(Terminator, cls).__new__(cls, type, seq, code)

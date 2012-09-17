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

#: Processing ID values set.
#:   - ``P``: Production
#:   - ``D``: Debugging
#:   - ``Q``: Quality Control
#:   - ``T``
PROCESSING_IDS = frozenset(['P', 'D', 'Q', 'T'])

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
    :param sender: Sender Name or ID. See :class:`SenderID` for more info.
    :param address: Sender Street Address.
    :param reserved: Reserved Field.
    :param phone: Sender Telephone Number.
    :param chars: Sender Characteristics.
    :param receiver: Receiver ID. See :class:`ReceiverID` for more info.
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

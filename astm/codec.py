# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Alexander Shorin
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from collections import Iterable
from .compat import basestring, unicode
from .constants import (
    STX, ETX, ETB, CR, LF, CRLF,
    FIELD_SEP, COMPONENT_SEP, RECORD_SEP, REPEAT_SEP
)
try:
    from itertools import izip_longest
except ImportError: # Python 3
    from itertools import zip_longest as izip_longest

#: Maximum message size before it will be split by chunks.
#: If is `None` encoded message will be never split.
MAX_MESSAGE_SIZE = None

def decode(data):
    """Common ASTM decoding function that tries to guess which kind of data it
    handles.

    If `data` starts with STX character (``0x02``) than probably it is
    full ASTM message with checksum and other system characters.

    If `data` starts with digit character (``0-9``) than probably it is
    frame of records leading by his sequence number. No checksum is expected
    in this case.

    Otherwise it counts `data` as regular record structure.

    :param data: ASTM data object.
    :type data: str

    :return: List of ASTM records.
    :rtype: list
    """
    if data[0] == STX: # may be decode message \x02...\x03CS\r\n
        seq, records, cs = decode_message(data)
        return records
    if data[0].isdigit(): # may be decode frame \d...
        seq, records = decode_frame(data)
        return records
    return [decode_record(data)]

def decode_message(message):
    """Decodes complete ASTM message that is sended or received due
    communication routines. It should contains checksum that would be
    additionally verified.

    :param message: ASTM message.
    :type message: str

    :returns: Tuple of three elements:

        * :class:`int` frame sequence number.
        * :class:`list` of records.
        * :class:`str` checksum.

    :raises:
        * :exc:`ValueError` if ASTM message is malformed.
        * :exc:`AssertionError` if checksum verification fails.
    """
    if not (message[0] == STX and message[-2:] == CRLF):
        raise ValueError('Malformed ASTM message. Expected that it will started'
                         ' with %x and followed by %x%x characters. Got: %r'
                         ' ' % (ord(STX), ord(CR), ord(LF), message))
    stx, frame_cs = message[0], message[1:-2]
    frame, cs = frame_cs[:-2], frame_cs[-2:]
    ccs = make_checksum(frame)
    assert cs == ccs, 'Checksum failure: expected %r, calculated %r' % (cs, ccs)
    seq, records = decode_frame(frame)
    return seq, records, cs

def decode_frame(frame):
    """Decodes ASTM frame: list of records followed by sequence number."""
    if not frame[0].isdigit():
        raise ValueError('Malformed ASTM frame. Expected leading seq number %r'
                         '' % frame)
    if frame.endswith((CR + ETX, ETB)):
        frame = frame[:-2]
    elif frame.endswith(ETB):
        frame = frame[:-1]
    else:
        raise ValueError('Incomplete frame data.'
                         ' Expected trailing <CR><ETX> or <ETB> chars')

    seq, records = int(frame[0]), frame[1:]
    return seq, [decode_record(record) for record in records.split(RECORD_SEP)]

def decode_record(record):
    """Decodes ASTM record message."""
    fields = []
    for item in record.split(FIELD_SEP):
        if REPEAT_SEP in item:
            item = decode_repeated_component(item)
        elif COMPONENT_SEP in item:
            item = decode_component(item)
        fields.append([None, item][bool(item)])
    return fields

def decode_component(field):
    """Decodes ASTM field component."""
    return [[None, item][bool(item)] for item in field.split(COMPONENT_SEP)]

def decode_repeated_component(component):
    """Decodes ASTM field repeated component."""
    return [decode_component(item) for item in component.split(REPEAT_SEP)]

def encode(records):
    """Encodes list of records into single ASTM message, also called as "packed"
    message.

    If you need to get each record as standalone message use :func:`iter_encode`
    instead.

    If the result message is too large (greater than :const:`MAX_MESSAGE_SIZE`),
    than it will be splitted by chunks.

    :param records: List of ASTM records.
    :type records: list

    :return: List of ASTM message chunks.
    :rtype: list
    """
    msg = encode_message(1, records)
    if MAX_MESSAGE_SIZE is not None and len(msg[1:-5]) > MAX_MESSAGE_SIZE:
        return list(split(msg))
    return [msg]

def iter_encode(records):
    """Encodes and emits each record as separate message.

    If the result message is too large (greater than :const:`MAX_MESSAGE_SIZE`),
    than it will be splitted by chunks.

    :yields: ASTM message chunks.
    :rtype: str
    """
    idx = 1
    for record in records:
        msg = encode_message(idx, [record])
        if MAX_MESSAGE_SIZE is not None and len(msg) > MAX_MESSAGE_SIZE:
            for chunk in split(msg):
                idx += 1
                yield chunk
        else:
            idx += 1
            yield msg

def encode_message(seq, records):
    """Encodes ASTM message.

    :param seq: Frame sequence number.
    :type seq: int

    :param records: List of ASTM records.
    :type records: list

    :return: ASTM complete message with checksum and other control characters.
    :rtype: str
    """
    data = RECORD_SEP.join(encode_record(record) for record in records)
    data = ''.join((str(seq), data, CR, ETX))
    return ''.join([STX, data, make_checksum(data), CR, LF])

def encode_record(record):
    """Encodes single ASTM record.

    :param record: ASTM record. Each :class:`str`-typed item counted as field
                   value, one level nested :class:`list` counted as components
                   and second leveled - as repeated components.
    :type record: list

    :returns: Encoded ASTM record.
    :rtype: str
    """
    fields = []
    _append = fields.append
    for field in record:
        if isinstance(field, basestring):
            _append(field)
        elif isinstance(field, Iterable):
            _append(encode_component(field))
        elif field is None:
            _append('')
        else:
            _append(unicode(field))
    return FIELD_SEP.join(fields)

def encode_component(component):
    """Encodes ASTM record field components."""
    items = []
    _append = items.append
    for item in component:
        if isinstance(item, basestring):
            _append(item)
        elif isinstance(item, Iterable):
            return encode_repeated_component(component)
        elif item is None:
            _append('')
        else:
            _append(unicode(item))

    return COMPONENT_SEP.join(items).rstrip(COMPONENT_SEP)

def encode_repeated_component(components):
    """Encodes repeated components."""
    return REPEAT_SEP.join(encode_component(item) for item in components)

def make_checksum(message):
    """Calculates checksum for specified message.

    :param message: ASTM message.
    :type message: str

    :returns: Checksum value that is actually byte sized integer in hex base
    :rtype: str
    """
    return hex(sum(ord(c) for c in message) & 0xFF)[2:].upper().zfill(2)

def make_chunks(s, n):
    return [''.join(item) for item in izip_longest(*[iter(s)]*n, fillvalue='')]

def split(msg, size=None):
    stx, frame, msg, tail = msg[0], msg[1], msg[2:-6], msg[-6:]
    assert stx == STX
    assert frame.isdigit()
    assert tail.endswith(CRLF)
    frame = int(frame)
    chunks = make_chunks(msg, size or MAX_MESSAGE_SIZE)
    chunks, last = chunks[:-1], chunks[-1]
    idx = 0
    for idx, chunk in enumerate(chunks):
        item = ''.join([str(idx + frame), chunk, ETB])
        yield ''.join([STX, item, make_checksum(item), CRLF])
    item = ''.join([str(idx + frame + 1), last, CR, ETX])
    yield ''.join([STX, item, make_checksum(item), CRLF])

def join(chunks):
    chunks = list(chunks)
    chunks, last = chunks[:-1], chunks[-1]
    msg = '1' + ''.join(c[2:-5] for c in chunks) + last[2:-4]
    return ''.join([STX, msg, make_checksum(msg), CRLF])

def is_complete_message(msg):
    return msg[-5] == ETB

def is_chunked_message(msg):
    return msg[-5] == ETX

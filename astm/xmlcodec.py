# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Alexander Shorin
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from collections import Iterable
from io import BytesIO
from astm.compat import basestring
try:
    from lxml import etree as xml
    Element = xml.Element
except ImportError:
    from xml.etree import ElementTree as xml
    Element = type(xml.Element('_'))


def decode(xmlsrc):
    """Decodes `xmlsrc` to Python object.

    :param xmlsrc: XML data source. Can be :func:`bytes`, `read`-able object or
                   `ElementTree` instance.
    :returns: Decoded dict object.
    :rtype dict

    >>> decode(b'<astm><header><type>H</type></header></astm>')
    {'astm': {'header': {'type': 'H'}}}
    >>> decode(b'<astm><result><value>1</value><value>2</value>'
    ...        b'<value>3</value></result></astm>')
    {'astm': {'result': {'value': ['1', '2', '3']}}}
    """
    if isinstance(xmlsrc, bytes):
        tree = xml.parse(BytesIO(xmlsrc))
    elif hasattr(xmlsrc, 'read'):
        tree = xml.parse(xmlsrc)
    elif hasattr(xmlsrc, 'getroot'):
        tree = xmlsrc
    else:
        raise TypeError('invalid xml source %r' % xmlsrc)
    root = tree.getroot()
    data = {}
    res = data[root.tag] = {}
    decode_elem(root, res)
    return data


def decode_elem(elem, res):
    """Decodes single xml `elem` and puts result to `res` object.

    Each child node of `elem` is counted as key-value pair where `key` is node
    tag name and value his text node:

    >>> xmlsrc = b'<root><answer>42</answer></root>'
    >>> tree = xml.parse(BytesIO(xmlsrc))
    >>> res = {}
    >>> decode_elem(tree.getroot(), res)
    {'answer': '42'}

    If text node is empty or missed :const:`None` value will be assigned:

    >>> xmlsrc = b'<root><answer/></root>'
    >>> tree = xml.parse(BytesIO(xmlsrc))
    >>> decode_elem(tree.getroot(), {})
    {'answer': None}

    In case if child node has his own children, the result value may be
    `dict`:

    >>> xmlsrc = b'<root><foo><bar>4</bar><baz>2</baz></foo></root>'
    >>> tree = xml.parse(BytesIO(xmlsrc))
    >>> res = decode_elem(tree.getroot(), {})
    >>> isinstance(res['foo'], dict)
    True
    >>> list(sorted(res['foo'].items()))
    [('bar', '4'), ('baz', '2')]

    or `list`, if child nodes are same-named:

    >>> xmlsrc = b'<root><foo><bar>4</bar><bar>2</bar></foo></root>'
    >>> tree = xml.parse(BytesIO(xmlsrc))
    >>> res = decode_elem(tree.getroot(), {})
    >>> res['foo']
    {'bar': ['4', '2']}

    :param elem: XML element node instance.
    :param res: Decoded result holder.
    :type res: dict
    """
    for item in elem:
        if not len(item):
            key, value = item.tag, item.text and item.text.strip() or None
        else:
            key, value = item.tag, decode_elem(item, {})
        if key in res:
            items = res[key]
            if not isinstance(items, list):
                items = res[key] = [items]
            items.append(value)
        else:
            res[key] = value
    return res


def encode(obj, root_tag_name=None, encoding='utf-8'):
    """Encodes Python `obj` to XML string.

    >>> xml = encode({'foo': {'bar': ['baz', None]}})
    >>> head, body = xml.split(b'\\n')
    >>> head
    b"<?xml version='1.0' encoding='utf-8'?>"
    >>> body
    b'<foo><bar>baz</bar><bar/></foo>'

    The `root_tag_name` specified custom root element tag name:

    >>> xml = encode({'foo': {'bar': ['baz', None]}}, 'astm')
    >>> head, body = xml.split(b'\\n')
    >>> head
    b"<?xml version='1.0' encoding='utf-8'?>"
    >>> body
    b'<astm><foo><bar>baz</bar><bar/></foo></astm>'

    Also, custom `encoding` may be specified:

    >>> xml = encode({'foo': {'bar': ['baz', None]}}, encoding='latin1')
    >>> head, body = xml.split(b'\\n')
    >>> head
    b"<?xml version='1.0' encoding='latin1'?>"
    >>> body
    b'<foo><bar>baz</bar><bar/></foo>'

    Note, that this conversion assumes that Python `obj` follows set of rules:

    1. Only unicode string, None values, dicts and iterable sequences are
       allowed or :exc:`TypeError` will be raised:


    >>> encode({'foo': {'bar': 42}}) #doctest: +ELLIPSIS
    Traceback (most recent call last):
      ...
    TypeError: unable to encode ...

    2. `root_tag_name` argument should be provided in case when `obj` contains
       two or more keys:

    >>> encode({'foo': {'bar': 42}, 'baz': {'boo': None}}) #doctest: +ELLIPSIS
    Traceback (most recent call last):
      ...
    AssertionError

    3. In case when `obj` contains only single key with list of values,
       additional root tag will be created implicitly:

    >>> xml = encode({'foo': ['bar', 'baz']})
    >>> head, body = xml.split(b'\\n')
    >>> head
    b"<?xml version='1.0' encoding='utf-8'?>"
    >>> body
    b'<foo><foo>bar</foo><foo>baz</foo></foo>'

    :param obj: Python object.
    :type obj: dict

    :param root_tag_name: XML root tag name.
    :type root_tag_name: unicode

    :param encoding: XML encoding
    :type encoding: str

    :return: XML string.
    :rtype: bytes
    """
    if hasattr(obj, 'items'):
        if root_tag_name is None:
            kvs = list(obj.items())
            assert len(kvs) == 1
            key, value = kvs[0]
            root = Element(key)
            elems = encode_value(root, value)
            if elems and root is not elems[0]:
                root.extend(elems)
        else:
            root = encode_dict(Element(root_tag_name), obj)
    else:
        raise TypeError('unable to encode object %r' % obj)

    xmlsrc = xml.tostring(root, encoding=encoding)
    if xmlsrc[:5] != b'<?xml':
        xml_declaration = "<?xml version='1.0' encoding='%s'?>\n" % encoding
        return b''.join([xml_declaration.encode(), xmlsrc])
    return xmlsrc


def encode_dict(elem, obj):
    """Encodes dict `obj`.

    :param elem: XML Element instance.

    :param obj: Python object
    :type obj: dict

    :return: `elem` element
    """
    for key, value in obj.items():
        elem.extend(encode_value(Element(key), value))
    return elem


def encode_value(elem, obj):
    """Encodes custom Python `obj`.

    :param elem: XML Element instance.
    :param obj: Python object. Could be :const:`None`, string, dict or iterable,
                otherwise :exc:`TypeError` will be raised.

    :return: list of Element instances
    :rtype: list
    """
    if obj is None:
        return [elem]
    elif isinstance(obj, basestring):
        elem.text = obj and obj.strip() or None
        return [elem]
    elif isinstance(obj, dict):
        return [encode_dict(elem, obj)]
    elif isinstance(obj, Iterable):
        return encode_list(elem, obj)
    else:
        raise TypeError('unable to encode %r for tag %r' % (obj, elem))


def encode_list(elem, obj):
    """Encodes list `obj`.

    :param elem: XML Element instance.

    :param obj: Python object.
    :type obj: list

    :return: List of XML Element instances.
    """
    elems = zip(*[encode_value(Element(elem.tag), item) for item in obj])
    return next(elems)

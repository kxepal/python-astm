# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Alexander Shorin
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from io import BytesIO
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


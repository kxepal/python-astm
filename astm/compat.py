# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Alexander Shorin
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import sys

version = '.'.join(map(str, sys.version_info[:2]))

if version >= '3.0':
    basestring = (str, bytes)
    unicode = str
    bytes = bytes
    long = int
    def buffer(obj, start=None, stop=None):
        memoryview(obj)
        if start == None:
            start = 0
        if stop == None:
            stop = len(obj)
        x = obj[start:stop]
        return x
else:
    basestring = basestring
    unicode = unicode
    b = bytes = str
    long = long
    buffer = buffer

b = lambda s: isinstance(s, unicode) and s.encode('latin1') or s
u = lambda s: isinstance(s, bytes) and s.decode('utf-8') or s

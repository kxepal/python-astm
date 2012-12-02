# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Alexander Shorin
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
else:
    basestring = basestring
    unicode = unicode
    b = bytes = str
    long = long

b = lambda s: isinstance(s, unicode) and s.encode('latin1') or s
u = lambda s: isinstance(s, bytes) and s.decode('utf-8') or s

# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Alexander Shorin
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

#: ASTM specification base encoding.
ENCODING = 'latin-1'

#: Message start token.
STX = b'\x02'
#: Message end token.
ETX = b'\x03'
#: ASTM session termination token.
EOT = b'\x04'
#: ASTM session initialization token.
ENQ = b'\x05'
#: Command accepted token.
ACK = b'\x06'
#: Command rejected token.
NAK = b'\x15'
#: Message chunk end token.
ETB = b'\x17'
LF  = b'\x0A'
CR  = b'\x0D'
#: CR + LF shortcut.
CRLF = CR + LF

#: Message records delimiter.
RECORD_SEP    = b'\x0D' # \r #
#: Record fields delimiter.
FIELD_SEP     = b'\x7C' # |  #
#: Delimeter for repeated fields.
REPEAT_SEP    = b'\x5C' # \  #
#: Field components delimiter.
COMPONENT_SEP = b'\x5E' # ^  #
#: Date escape token.
ESCAPE_SEP    = b'\x26' # &  #

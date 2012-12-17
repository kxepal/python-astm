# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Alexander Shorin
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

#: :mod:`astm.protocol` base encoding.
ENCODING = 'utf-8'

#: Maximum message size before it will be split by chunks.
#: If is `None` encoded message will be never split.
MAX_MESSAGE_SIZE = None

#: Message start token.
STX = '\x02'
#: Message end token.
ETX = '\x03'
#: ASTM session termination token.
EOT = '\x04'
#: ASTM session initialization token.
ENQ = '\x05'
#: Command accepted token.
ACK = '\x06'
#: Command rejected token.
NAK = '\x15'
#: Message chunk end token.
ETB = '\x17'
LF  = '\x0A'
CR  = '\x0D'
#: CR + LF shortcut.
CRLF = CR + LF

#: Message records delimeter.
RECORD_SEP    = '\x0D' # \r #
#: Record fields delimeter.
FIELD_SEP     = '\x7C' # |  #
#: Delimeter for repeated fields.
REPEAT_SEP    = '\x5C' # \  #
#: Field components delimeter.
COMPONENT_SEP = '\x5E' # ^  #
#: Date escape token.
ESCAPE_SEP    = '\x26' # &  #

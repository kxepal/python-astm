# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Alexander Shorin
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

STX = '\x02'
ETX = '\x03'
EOT = '\x04'
ENQ = '\x05'
ACK = '\x06'
NAK = '\x15'
ETB = '\x17'
LF  = '\x0A'
CR  = '\x0D'
CRLF = CR + LF

RECORD_SEP    = '\x0D' # \r #
FIELD_SEP     = '\x7C' # |  #
REPEAT_SEP    = '\x5C' # \  #
COMPONENT_SEP = '\x5E' # ^  #
ESCAPE_SEP    = '\x26' # &  #

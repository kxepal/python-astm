# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Alexander Shorin
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from .version import __version__, __version_info__
from .exceptions import BaseASTMError, NotAccepted, InvalidState
from .codec import (
    decode, decode_message, decode_record,
    encode, encode_message, encode_record,
    make_checksum
)
from .mapping import Record, Component
from .records import (
    HeaderRecord, PatientRecord, OrderRecord,
    ResultRecord, CommentRecord, TerminatorRecord
)
from .protocol import ASTMProtocol
from .client import Client
from .server import RequestHandler, Server

import logging
log = logging.getLogger()

class NullHandler(logging.Handler):
    def emit(self, *args, **kwargs):
        pass

log.addHandler(NullHandler())

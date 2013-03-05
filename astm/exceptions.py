# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Alexander Shorin
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

class BaseASTMError(Exception):
    """Base ASTM error."""


class InvalidState(BaseASTMError):
    """Should be raised in case of invalid ASTM handler state."""


class NotAccepted(BaseException):
    """Received data is not acceptable."""


class Rejected(BaseASTMError):
    """Should be raised after unsuccessful attempts to send data
    (receiver sends with <NAK> reply)."""



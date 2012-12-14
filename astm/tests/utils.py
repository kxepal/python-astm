# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Alexander Shorin
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#


class DummyMixIn(object):
    _input_buffer = ''

    def flush(self):
        pass


class CallLogger(object):

    def __init__(self, func):
        self.func = func
        self.was_called = False

    def __call__(self, *args, **kwargs):
        self.was_called = True
        return self.func(*args, **kwargs)


def track_call(func):
    return CallLogger(func)

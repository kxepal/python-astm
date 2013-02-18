# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Alexander Shorin
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import doctest
import unittest
import astm.xmlcodec

def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    suite.addTest(doctest.DocTestSuite(astm.xmlcodec))
    return suite




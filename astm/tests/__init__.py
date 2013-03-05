# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Alexander Shorin
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import os
import sys
import unittest

def suite():
    suite = unittest.TestSuite()
    for root, dirs, files in os.walk('.'):
        for file in files:
            if not (file.startswith('test_') and file.endswith('.py')):
                continue
            name = file.split('.')[0]
            modname = os.path.join(root, name).replace(os.path.sep, '.')
            modname = modname.lstrip('.')
            tests = unittest.defaultTestLoader.loadTestsFromName(modname)
            for test in tests:
                suite.addTests(test)
            sys.stdout.write('%s : %s tests%s'
                             % (modname, tests.countTestCases(), os.linesep))
            sys.stdout.flush()
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

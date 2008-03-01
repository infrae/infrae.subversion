## -*- coding: utf-8 -*-

__author__ = "sylvain@infrae.com"
__format__ = "plaintext"
__version__ = "$Id$"

import unittest
import doctest
import sys
import os

from zope.testing import doctest, renormalizing
import zc.buildout.testing
import svnhelper.testing
import svnhelper.tests
from svnhelper.core import helper

test_package = os.path.dirname(svnhelper.tests.__file__)
test_package = os.path.join(test_package, 'tests', 'infrae.subversion')

def setUp(test):
    zc.buildout.testing.buildoutSetUp(test)
    zc.buildout.testing.install_develop('infrae.subversion', test)
    svnhelper.testing.setUpRepository(test)
    test.globs['init_test_package'](test_package)
    helper.import_to(test.globs['package_dir'],
                     test.globs['repository'])

def tearDown(test):
    svnhelper.testing.tearDownRepository(test)
    zc.buildout.testing.buildoutTearDown(test)

flags = (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE |
         doctest.REPORT_ONLY_FIRST_FAILURE)

def test_suite():
    return unittest.TestSuite([doctest.DocFileSuite(
        os.path.join(os.path.dirname(__file__), 'PYPI.txt'),
        optionflags=flags,
        globs=globals(),
        setUp=setUp,
        tearDown=tearDown)])


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

## -*- coding: utf-8 -*-

__author__ = "sylvain@infrae.com"
__format__ = "plaintext"
__version__ = "$Id$"

import unittest
import doctest
import os, sys
import os.path

import infrae.subversion
import zc.buildout.testing
import svnhelper.testing
import svnhelper.tests
from svnhelper.core import helper


def setUp(test):
    test_package = os.path.dirname(svnhelper.tests.__file__)
    test_package = os.path.join(test_package, 'tests', 'my.testing')
    tested_package = os.path.dirname(infrae.subversion.__file__)

    zc.buildout.testing.buildoutSetUp(test)
    zc.buildout.testing.install_develop('infrae.subversion', test)
    svnhelper.testing.setUpRepository(test)
    test.globs['init_test_package'](test_package)
    helper.import_to(test_package,
                     test.globs['repository'])
    helper.import_to(tested_package,
                     test.globs['repository'] + '/infrae.subversion/trunk/infrae.subversion')

def tearDown(test):
    svnhelper.testing.tearDownRepository(test)
    zc.buildout.testing.buildoutTearDown(test)

flags = (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE |
         doctest.REPORT_ONLY_FIRST_FAILURE)


def test_suite():
    return unittest.TestSuite([doctest.DocFileSuite(
        os.path.join(os.path.dirname(__file__), 'IMPL.txt'),
        optionflags=flags,
        globs=globals(),
        setUp=setUp,
        tearDown=tearDown,
        module_relative=False)])

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

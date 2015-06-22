#!/usr/bin/env python3

import sys

assert sys.version >= '3'
from setuptools.command.test import test as TestCommand
from setuptools import find_packages, setup


class TestDiscoverCommand(TestCommand):
    """
    Use unittest2 to discover and run tests
    """

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import unittest   # this will import unittest2
        unittest.main(argv=['', 'discover']).runTests()


setup(
    name='gmailfilter',
    version='0.1',
    author='Thomi Richards',
    author_email='thomi.richards@canonical.com',
    url='http://launchpad.net/gmailfilter',
    packages=['gmailfilter'],
    # packages=find_packages('gmailfilter'),
    # test_suite='gmailfilter.tests',
    install_requires=['IMAPClient==0.11'],
    entry_points={
        'console_scripts': ['gmailfilter = gmailfilter._command:run']
    },
    cmdclass={'test': TestDiscoverCommand},
)

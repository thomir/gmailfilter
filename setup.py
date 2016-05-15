#!/usr/bin/env python3

import sys
from setuptools.command.test import test as TestCommand
from setuptools import setup
assert sys.version >= '3'


class TestDiscoverCommand(TestCommand):
    """
    Use unittest2 to discover and run tests
    """

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import testtools.run
        testtools.run.main(argv=['', 'discover'], stdout=sys.stdout)


setup(
    name='gmailfilter',
    version='0.1',
    author='Thomi Richards',
    author_email='thomi.richards@canonical.com',
    url='http://launchpad.net/gmailfilter',
    packages=['gmailfilter'],
    install_requires=['IMAPClient==0.13'],
    entry_points={
        'console_scripts': ['gmailfilter = gmailfilter._command:run']
    },
    cmdclass={'test': TestDiscoverCommand},
    tests_require=['testtools', 'fixtures']
)

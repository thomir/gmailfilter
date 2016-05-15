import os

from testtools import TestCase
import fixtures

from gmailfilter._rules import default_rules_path


class RulePathTests(TestCase):

    def test_default_path_in_normal_mode(self):
        fake_home = '/some/fake/home'
        self.useFixture(fixtures.EnvironmentVariable('HOME', fake_home))
        path = default_rules_path()

        expected = os.path.join(
            fake_home,
            '.config/gmailfilter/rules.py'
        )
        self.assertEqual(expected, path)

    def test_defailt_path_in_snap_mode(self):
        fake_home = '/snap/foo'
        self.useFixture(
            fixtures.EnvironmentVariable('SNAP_USER_DATA', fake_home))
        path = default_rules_path()

        expected = os.path.join(fake_home, 'rules.py')
        self.assertEqual(expected, path)

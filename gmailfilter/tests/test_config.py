import os.path

from testtools import TestCase
import fixtures

from gmailfilter._config import default_credentials_file_location


class ConfigTests(TestCase):

    def test_default_path_in_normal_mode(self):
        fake_home = '/some/fake/home'
        self.useFixture(fixtures.EnvironmentVariable('HOME', fake_home))
        path = default_credentials_file_location()

        expected = os.path.join(
            fake_home,
            '.config/gmailfilter/credentials.ini'
        )
        self.assertEqual(expected, path)

    def test_defailt_path_in_snap_mode(self):
        fake_home = '/snap/foo'
        self.useFixture(
            fixtures.EnvironmentVariable('SNAP_USER_DATA', fake_home))
        path = default_credentials_file_location()

        expected = os.path.join(fake_home, 'credentials.ini')
        self.assertEqual(expected, path)

import configparser
import logging
import os
import os.path
import textwrap
import stat


class ServerInfo(object):
    """A class that encapsulates information about how to connect to a server.

    Knows how to read from a config file on disk, create a template config
    file.

    """

    _default_options = {
        'port': '993',
        'use_ssl': 'True',
    }

    def __init__(self, host, username, password, port, use_ssl):
        if not host:
            raise KeyError('host')
        if not username:
            raise KeyError('username')
        if not password:
            raise KeyError('password')
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.use_ssl = use_ssl

    @classmethod
    def read_config_file(cls, path=None):
        """Read credentials from a config file, return a ServerInfo instance.

        This function will log a warning if the credentials file exists and is
        group or world readable (your imap credentials should be private!),
        but will return a valid ServerInfo instance.

        If the path to the credentals file cannot be found, it will raise an
        IOError.

        If the path exists, but cannot be parsed, a RuntimeError will be
        raised with the parse failure reason.

        If required keys are missing, KeyError is raised.

        """
        path = path or default_credentials_file_location()
        if not os.path.exists(path):
            raise IOError("Could not read path {}".format(path))
        if os.stat(path).st_mode & (stat.S_IRWXG | stat.S_IRWXO):
            logging.warning(
                "The credentials file at '{0}' is readable by other users on "
                "this system. To eliminate this security risk, run "
                "'chmod go-rwx {0}'.".format(path)
            )
        parser = configparser.ConfigParser(defaults=cls._default_options)
        try:
            parser.read(path)
        except configparser.ParsingError as e:
            raise RuntimeError(
                "Could not parse credentials file '{}'. Error was:\n{}".format(
                    path,
                    str(e)
                )
            )
        return cls(
            host=parser['server']['host'],
            username=parser['server']['username'],
            password=parser['server']['password'],
            port=parser['server']['port'],
            use_ssl=parser['server']['use_ssl']
        )

    @classmethod
    def write_template_config_file(cls, path=None):
        """Write a template config file to disk."""
        path = path or default_credentials_file_location()
        directory = os.path.dirname(path)
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(path, 'w') as template_file:
            template_file.write(textwrap.dedent('''
                # Credentials config file.
                # Comments start with a '#'. See comments below for
                # detailed information on each option.

                [server]

                # REQUIRED: The domain name or ip address of the IMAP
                # server to connect to:
                host =

                # REQUIRED: The username to log in to the IMAP server with
                username =

                # REQUIRED: The password to log in to the IMAP server with
                password =

                # OPTIONAL: Whether or not to connect with SSL. Default is
                # to use SSL. Uncomment this and change it to False to
                # connect without SSL.
                #use_ssl = True

                # OPTIONAL: The port to connect to on the host.
                #port = 993

                '''))
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)


def default_credentials_file_location():
    if 'SNAP_USER_DATA' in os.environ:
        return os.path.join(os.environ['SNAP_USER_DATA'], 'credentials.ini')
    return os.path.expanduser('~/.config/gmailfilter/credentials.ini')

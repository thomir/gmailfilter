from contextlib import contextmanager
import configparser
import functools
import logging
import os
import os.path
import textwrap
import stat

from imapclient import IMAPClient

from gmailfilter._message import EmailMessage as Message


def sequence_chunk(num_messages, chunk_size):
    assert chunk_size >= 1
    start = 1
    while start <= num_messages:
        end = min(start + chunk_size - 1, num_messages)
        if end > start:
            if end != num_messages:
                yield '%d:%d' % (start, end)
            else:
                yield '%d:*' % start
        else:
            yield '%d' % (start)
        start += chunk_size


def optimal_chunk_size(total_messages):
    """Work out the optimal chunk size for an inbox with total_messages."""
    # use 1000 (maximum sensible chunk size), or 10 retrieval operations,
    # whichever is smaller:
    return min(1000, total_messages / 10)


class MessageConnectionProxy(object):

    """A class that knows how to retrieve additional message parts."""

    def __init__(self, connection, initial_data):
        assert 'UID' in initial_data
        self._connection = connection
        self._data = initial_data

    def get_message_part(self, part_name):
        """Get a part of a message, possibly from memory.

        'part_name' will be one of ENVELOPE, RFC822, UID, BODY etc.

        """
        # transform 'BODY.PEEK[HEADER]' into 'BODY[HEADER]'
        if part_name.startswith('BODY.PEEK'):
            retrieve_key = 'BODY' + part_name[9:]
        else:
            retrieve_key = part_name

        # ask the server for 'part_name', but look in our dictionary with
        # 'retrieve_key'
        if retrieve_key not in self._data:
            with self._connection.use_uid():
                msg_uid = self._data['UID']
                # for some reason, sometimes a fetch call returns an empty dict.
                # until I find out why, I'll simply retry this:
                data = {}
                for i in range(3):
                    data = self._connection._client.fetch(msg_uid, part_name)
                    if data:
                        self._data.update(data[msg_uid])
                        break
                assert msg_uid in data, ("Server gave us back some other data: %d %r" % (msg_uid, data))
        return self._data[retrieve_key]


class IMAPConnection(object):

    def __init__(self, server_info):
        self._client = IMAPClient(
            host=server_info.host,
            port=server_info.port,
            use_uid=False,
            ssl=server_info.use_ssl
            )
        # self._client.debug = True
        self._client.login(
            server_info.username,
            server_info.password,
        )

    def get_messages(self):
        """A generator that yields Message instances, one for every message
        in the users inbox.

        """
        # TODO - perahps the user wants to filter a different folder?
        mbox_details = self._client.select_folder("INBOX")
        total_messages = mbox_details['EXISTS']
        logging.info("Scanning inbox, found %d messages" % total_messages)
        # TODO: Research best chunk size - maybe let user tweak this from
        # config file?:
        i = 0
        with self.use_sequence():
            for chunk in sequence_chunk(total_messages, optimal_chunk_size(1000)):
                logging.info("Fetching: " + chunk)
                data = self._client.fetch(
                    chunk,
                    ['UID', 'BODY.PEEK[HEADER]', 'INTERNALDATE', 'FLAGS']
                )
                for msg_seq in data:
                    logging.debug("Processing %d / %d", i, total_messages)
                    proxy = MessageConnectionProxy(self, data[msg_seq])
                    yield Message(proxy)
                    i += 1

    def get_connection_proxy(self):
        return ConnectionProxy(self._client)

    @contextmanager
    def use_uid(self):
        old = self._client.use_uid
        self._client.use_uid = True
        try:
            yield
        finally:
            self._client.use_uid = old

    @contextmanager
    def use_sequence(self):
        old = self._client.use_uid
        self._client.use_uid = False
        try:
            yield
        finally:
            self._client.use_uid = old


class ConnectionProxy(object):

    """A class that proxies an IMAPClient object, but hides access to methods
    that filter Actions should not call.

    """
    def __init__(self, wrapped):
        self._wrapped = wrapped

    def __getattribute__(self, name):
        if name == '_wrapped':
            return super().__getattribute__(name)

        allowed = (
            'add_flags',
            'add_gmail_labels',
            'copy',
            'create_folder',
            'delete_folder',
            'delete_messages',
            'folder_exists',
            'get_flags',
            'get_gmail_labels',
            'list_folders',
            'list_sub_folders',
            'remove_flags',
            'remove_gmail_labels',
            'rename_folder',
            'set_flags',
            'set_gmail_labels',
        )
        if name in allowed:
            # Wrap these functions so they always use the uid, not the sequence
            # id.
            function = getattr(self._wrapped, name)
            def wrapper(client, fn, *args, **kwargs):
                old = client.use_uid
                client.use_uid = True
                try:
                    return fn(*args, **kwargs)
                finally:
                    client.use_uid = old
            return functools.partial(wrapper, self._wrapped, function)

        raise AttributeError(name)


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
            host = parser['server']['host'],
            username = parser['server']['username'],
            password = parser['server']['password'],
            port = parser['server']['port'],
            use_ssl = parser['server']['use_ssl']
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

                ''')
            )
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)


def default_credentials_file_location():
    return os.path.expanduser('~/.config/gmailfilter/credentials.ini')

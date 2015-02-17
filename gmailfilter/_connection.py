from contextlib import contextmanager
import logging

from imapclient import IMAPClient

from gmailfilter._message import Message


# TODO: Accept config from command line, encapsulate in a dict and pass
# in to the connection class.



class IMAPServer(object):

    def __init__(self, server=None, username=None, password=None, port=993, ssl=True):
        if (
            server is None or
            username is None or
            password is None
        ):
            raise ValueError("server and username and password cannot be None")


        self._client = IMAPClient(
            host=server,
            port=port,
            use_uid=False,
            ssl=ssl
            )
        # self._client.debug = True
        self._client.login(
            username,
            password,
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
                self._do_chunk_cleanup()

    def move_message(self, message, folder):
        """Move a message to a folder, creating the folder if it doesn't exist.

        :param message: An instance of gmailfilter.Message
        :param folder: A string descriving the folder.

        """
        # TODO: optimise this by trying the copy, and if we get 'NO' with
        # 'TRYCREATE' then, and only then try and create the folder. Removes the
        # overhead of the existance check for every message,
        if not self._client.folder_exists(folder):
            status = self._client.create_folder(folder)
            assert status.lower() == "success", "Unable to create folder %s" % folder
        with self.use_uid():
            self._client.copy(str(message.uid()), folder)
            self.delete_message(message)

    def delete_message(self, message):
        with self.use_uid():
            uid_string = str(message.uid())
            logging.info("Deleting %s" % uid_string)
            self._client.delete_messages(uid_string)

    def _do_chunk_cleanup(self):
        # self._client.expunge()
        pass


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


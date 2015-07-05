import email
from email.utils import parseaddr


class Message(object):

    """An interface to represent an email message."""

    def subject(self):
        """Return the subject string of the email message."""

    def from_(self):
        """Return the Sender of the email."""

    def uid(self):
        """Return the mesage uid."""

    def get_headers(self):
        """Get the dictionary of headers."""
        # TODO: Define a better interface here that deals with the fact that
        # message headers can be added multiple times, so it's not actually
        # good enough to store them in a dictionary.

    def get_date(self):
        """Get the date the message was received."""

    def get_flags(self):
        """Get the flags set on the message."""

    def __repr__(self):
        return "<Message %d %r>" % (self.uid(), self.subject())


class EmailMessage(Message):

    """An interface to represent an email message.

    The message is lazily-created. Methods such as 'subject' cause network
    traffic the first time they're called. After that, the results are cached.
    """

    def __init__(self, connection_proxy):
        self._connection_proxy = connection_proxy
        self._message = None

    def _get_email(self):
        if self._message is None:
            self._message = email.message_from_string(
                self._connection_proxy.get_message_part(b'BODY.PEEK[HEADER]').decode()
            )
        return self._message

    def subject(self):
        return self._get_email()['Subject']

    def from_(self):
        return self._get_email()['From']

    def is_list_message(self):
        return 'List-Id' in self._get_email()

    def list_id(self):
        # Returns None if key is not found, does not raise KeyError:
        list_id = self._get_email()['List-Id']
        return parse_list_id(list_id) if list_id is not None else None

    def uid(self):
        return self._connection_proxy.get_message_part(b'UID')

    def get_headers(self):
        # TODO: email objects are dictionaries for the headers, but also expose
        # the body contents, attachments etc. etc. It'd be nice if we could
        # *only* expose the headers here...
        return self._get_email()

    def get_date(self):
        return self._connection_proxy.get_message_part(b'INTERNALDATE')

    def get_flags(self):
        return self._connection_proxy.get_message_part(b'FLAGS')

    def __repr__(self):
        return repr(self.subject())


def parse_list_id(id_string):
    return parseaddr(id_string)[1]

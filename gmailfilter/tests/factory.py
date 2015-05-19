"""Test factory for gmailfilter tests."""

from gmailfilter._message import Message

class TestFactoryMixin(object):

    """A mixin class that generates test fake values."""

    def get_email_message(self, headers=None):
        """Get an email message.

        :param headers: If set, must be a dict or 2-tuple iteratble of key/value
            pairs that will be set as the email message header values.
        """
        message = FakeMessage()
        if headers:
            message.headers = dict(headers)
        return message


class FakeMessage(Message):

    def __init__(self):
        self.headers = {}

    def get_headers(self):
        return self.headers


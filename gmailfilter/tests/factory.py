"""Test factory for gmailfilter tests."""

import datetime

from gmailfilter._message import Message


class TestFactoryMixin(object):

    """A mixin class that generates test fake values."""

    def get_email_message(self, headers=None, subject='Test Subject',
                          flags=None, date=None):
        """Get an email message.

        :param headers: If set, must be a dict or 2-tuple iteratble of
            key/value pairs that will be set as the email message header
            values.
        """
        message = FakeMessage()
        if headers:
            message.headers = dict(headers)
        message.headers['Subject'] = subject
        if flags:
            message.flags = flags
        if date is not None:
            message.date = date
        return message


class FakeMessage(Message):

    def __init__(self):
        self.headers = {}
        self.flags = ()
        self.date = datetime.datetime.utcnow()

    def get_headers(self):
        return self.headers

    def subject(self):
        return self.get_headers()['Subject']

    def get_flags(self):
        return self.flags

    def get_date(self):
        return self.date

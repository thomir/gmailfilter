
"""Message Test Classes.

This module contains all the tests we ship. These can be used in the rules
file to select messages.

"""

from datetime import (
    datetime,
    timedelta,
)
import logging
import operator
import unicodedata

import imapclient

from gmailfilter.messageutils import get_list_id


__all__ = [
    'Test',
    'And',
    'Or',
    'MatchesHeader',
]

class Test(object):

    """This class represents a single test on a message.

    The only contractual obligation is the 'match' method, which should
    return a truthy value when the test matches.

    """

    def match(self, message):
        """Check if this test matches a given message.

        If the message matches this test, this method must return True.

        If the message does not match this test, the method may return False,
        or an instance of the Mismatch object. The latter is used to signal
        that we know that a message needs to be re-checked at a certain point
        in the future.

        TODO: Implement Mismatch.

        """


class And(Test):

    """An aggregate test that performs a boolean and operation over multiple
    other tests.

    Can be constructed with an arbitrary number of sub, tests, like so:

    >>> And(test1, test2)
    >>> And(test1, test2, test3)

    ...and can even be constructed without any sub-tests. In this configuration
    it will *not* match.

    """
    def __init__(self, *tests):
        self._tests = tests

    def match(self, message):
        if not self._tests:
            return False
        return all([t.match(message) for t in self._tests])


class Or(Test):

    """An aggregate test that performs a boolean 'or' operation over multiple
    other tests.

    Similar to And, this test can be constructed with an arbitrary number of
    sub-tests. If it is constructed with no sub-tests, it will never match.
    """

    def __init__(self, *tests):
        self._tests = tests

    def match(self, message):
        return any([t.match(message) for t in self._tests])


class Not(Test):

    """Invert the output of any single test."""

    def __init__(self, test):
        self._test = test

    def match(self, message):
        return not self._test.match(message)


class MatchesHeader(Test):

    """Check whether an email has a given header.

    Can be used to check the existance of the header, by passing in the header
    name::

    >>> MatchesHeader('X-Launchpad-Message-Rationale')

    ...or can be used to match the header value, by passing in both the name
    and value::

    >>> MatchesHeader('X-Launchpad-Message-Rationale', 'subscriber')

    """

    def __init__(self, expected_key, expected_value=None):
        self.expected_key = expected_key
        self.expected_value = expected_value

    def match(self, message):
        headers = message.get_headers()
        if self.expected_key in headers:
            if self.expected_value:
                return headers[self.expected_key] == self.expected_value
            else:
                return True
        return False


class SubjectContains(Test):

    """Check whether a subject contains a certain phrase.

    Can do both case sensitive, and case insensitive matching.

    By default, matches are case sensitive::

    >>> SubjectContains("Hello World")

    ...will match for the string 'Hello World' exactly anywhere in the
    subject. Searches can be made case-insensitive like so::

    >>> SubjectContains("welcome to", case_sensitive=False)

    Case sensitivity controls both whether we consider character case, and
    whether we consider character accents.

    """

    def __init__(self, search_string, case_sensitive=True):
        self._search_string = search_string
        self._case_sensitive = case_sensitive

    def match(self, message):
        subject = message.get_headers()['Subject']
        if self._case_sensitive:
            return self._search_string in subject
        else:
            return self._search_string.casefold() in subject.casefold()


class ListId(Test):

    """Match for mailinglist messages from a particular list-id.

    """

    def __init__(self, target_list):
        self._target_list = target_list

    def match(self, message):
        return get_list_id(message) == self._target_list


# IMAPClient incorrectly declares these as strings. This is reported as
# https://bitbucket.org/mjs0/imapclient/issues/165/imapclientseen-friends-have-the-wrong-type
# Once this is fixed, the '.encode' parts can be stripped
def _correct_type(flag):
    if isinstance(flag, bytes):
        logging.debug("This fix can be removed now!")
        return flag
    else:
        return flag.encode('utf-8')


class HasFlag(Test):

    """Test for certain flags being set on a message.

    This test can be given any string for a flag, although the following are
    provided as a convenience:

    HasFlag.ANSWERED
    HasFlag.DELETED
    HasFlag.DRAFT
    HasFlag.FLAGGED
    HasFlag.RECENT
    HasFlag.SEEN

    """
    ANSWERED = _correct_type(imapclient.ANSWERED)
    DELETED = _correct_type(imapclient.DELETED)
    DRAFT = _correct_type(imapclient.DRAFT)
    FLAGGED = _correct_type(imapclient.FLAGGED)
    RECENT = _correct_type(imapclient.RECENT)
    SEEN = _correct_type(imapclient.SEEN)

    def __init__(self, flag):
        self.expected_flag = flag

    def match(self, message):
        return self.expected_flag in message.get_flags()


def IsAnswered():
    return HasFlag(HasFlag.ANSWERED)


def IsDeleted():
    return HasFlag(HasFlag.DELETED)


def IsDraft():
    return HasFlag(HasFlag.DRAFT)


def IsFlagged():
    return HasFlag(HasFlag.FLAGGED)


def IsRecent():
    return HasFlag(HasFlag.RECENT)


def IsRead():
    return HasFlag(HasFlag.SEEN)


# Provide a function with the same name as the imap flag name, even though
# it's bad english
IsSeen = IsRead


# TODO: Need a way to provide alternative values for the datetime.now() call
# here, otherwise it's hard to test.
class MessageOlderThan(Test):

    """Test that a message is older than a certain age.

    Age is specified as a python datetime.timedelta object. For example:

    >>> from datetime import timedelta
    >>> MessageOlderThan(timedelta(days=12))

    """

    def __init__(self, age):
        if not isinstance(age, timedelta):
            raise TypeError("'age' must be a datetime.timedelta object.")
        self._age = age

    def match(self, message):
        return message.get_date() + self._age < datetime.now()


# def caseless_comparison(str1, str2, op):
#     """Perform probably-correct caseless comparison between two strings.

#     This is surprisingly complex in a unicode world.  We need to deal with
#     characters that have different case-forms, as well as character accents.

#     'op' should be a callable that accepts two arguments, and returns True
#     or False. Good candidates are those from the 'operator' module...

#     """
#     return op(
#         unicodedata.normalize("NFKD", str1.casefold()),
#         unicodedata.normalize("NFKD", str2.casefold()),
#         )

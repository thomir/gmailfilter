
"""Message Test Classes.

This module contains all the tests we ship. These can be used in the rules
file to select messages.

"""

import operator
import unicodedata

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

    def __init__(self, search_string, case_sensitive=False):
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

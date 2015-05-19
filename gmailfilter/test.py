
"""Message Test Classes.

This module contains all the tests we ship. These can be used in the rules
file to select messages.

"""


__all__ = [
    'Test',
    'And',
    'Or',
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

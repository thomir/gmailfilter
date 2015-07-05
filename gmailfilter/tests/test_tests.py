import datetime
from unittest import TestCase

import imapclient

from gmailfilter.tests.factory import TestFactoryMixin
from gmailfilter.test import (
    Test,
    And,
    Or,
    Not,
    MatchesHeader,
    SubjectContains,
    ListId,
    HasFlag,
)
from gmailfilter._message import Message

# Let's define some tests that will pass and fail regardless of their input:
class AlwaysPassingTest(Test):

    def match(self, message):
        return True


class AlwaysFailingTest(Test):

    def match(self, message):
        return False


class TestBooleanTests(TestCase, TestFactoryMixin):

    def test_and_can_be_Created_without_tests(self):
        And()

    def test_and_yields_false_with_no_tests(self):
        self.assertFalse(And().match(self.get_email_message()))

    def test_and_boolean_table(self):
        # boolean truth table - expected result is always first, operands
        # are after.
        table = [
            (True, AlwaysPassingTest()),
            (True, AlwaysPassingTest(), AlwaysPassingTest()),
            (False, AlwaysFailingTest(), AlwaysPassingTest()),
            (False, AlwaysFailingTest()),
        ]
        for expected_value, *operands in table:
            self.assertEqual(
                expected_value,
                And(*operands).match(self.get_email_message())
            )

    def test_or_can_be_Created_without_tests(self):
        Or()

    def test_or_yields_false_with_no_tests(self):
        self.assertFalse(Or().match(self.get_email_message()))

    def test_or_boolean_table(self):
        # boolean truth table - expected result is always first, operands
        # are after.
        table = [
            (True, AlwaysPassingTest()),
            (True, AlwaysPassingTest(), AlwaysPassingTest()),
            (True, AlwaysFailingTest(), AlwaysPassingTest()),
            (False, AlwaysFailingTest()),
        ]
        for expected_value, *operands in table:
            self.assertEqual(
                expected_value,
                Or(*operands).match(self.get_email_message())
            )

    def test_not_with_passing_test(self):
        self.assertEqual(
            False,
            Not(AlwaysPassingTest()).match(self.get_email_message())
        )

    def test_not_with_failing_test(self):
        self.assertEqual(
            True,
            Not(AlwaysFailingTest()).match(self.get_email_message())
        )


class TestMatchesHeaderTests(TestCase, TestFactoryMixin):

    def test_fails_when_header_is_missing(self):
        self.assertFalse(
            MatchesHeader('SomeHeader').match(self.get_email_message())
        )

    def test_passes_when_header_is_present(self):
        message = self.get_email_message(headers=dict(SomeHeader='123'))
        self.assertTrue(MatchesHeader('SomeHeader').match(message))

    def test_fails_when_header_value_is_wrong(self):
        message = self.get_email_message(headers=dict(SomeHeader='123'))
        self.assertFalse(MatchesHeader('SomeHeader', 'foo').match(message))

    def test_passes_with_correct_value(self):
        message = self.get_email_message(headers=dict(SomeHeader='123'))
        self.assertTrue(MatchesHeader('SomeHeader', '123').match(message))


class SubjectContainsTests(TestCase, TestFactoryMixin):

    def test_case_sensitive_contains_matches_whole_string(self):
        message = self.get_email_message(subject='Hello World')
        self.assertTrue(SubjectContains('Hello World').match(message))

    def test_case_sensitive_contains_matches_partial_string(self):
        message = self.get_email_message(subject='Hello World')
        self.assertTrue(SubjectContains('ello Worl').match(message))

    def test_case_sensitive_is_the_default(self):
        message = self.get_email_message(subject='Hello World')
        self.assertFalse(SubjectContains('hello world').match(message))

    def test_case_insensitive_works_with_ascii(self):
        message = self.get_email_message(subject='Hello World')
        self.assertTrue(
            SubjectContains('hello world', case_sensitive=False).match(message)
        )

    def test_case_insensitive_works_with_unicode(self):
        message = self.get_email_message(subject='Hello BUẞE')
        self.assertTrue(
            SubjectContains('hello BUSSE', case_sensitive=False).match(message)
        )
        self.assertTrue(
            SubjectContains('hello Buße', case_sensitive=False).match(message)
        )

    def test_case_insensitive_works_with_unicode_accents(self):
        message = self.get_email_message(subject='Hêllo')
        self.assertTrue(
            SubjectContains('h\xeallo', case_sensitive=False).match(message)
        )


class ListIdTests(TestCase, TestFactoryMixin):

    def test_list_id_match(self):
        message = self.get_email_message(headers={'List-Id': 'foo.bar'})
        self.assertTrue(ListId('foo.bar').match(message))

    def test_list_id_mismatch(self):
        message = self.get_email_message(headers={'List-Id': 'foo.bar'})
        self.assertFalse(ListId('something.else').match(message))

    def test_non_list_message(self):
        message = self.get_email_message()
        self.assertFalse(ListId('something.else').match(message))


class FlagTests(TestCase, TestFactoryMixin):

    def test_all_flag_matchers(self):
        flags = (
            imapclient.ANSWERED,
            imapclient.DELETED,
            imapclient.DRAFT,
            imapclient.FLAGGED,
            imapclient.RECENT,
            imapclient.SEEN,
        )
        for flag in flags:
            message = self.get_email_message(flags=(flag,))
            self.assertTrue(HasFlag(flag).match(message))


class MessageAgeTests(TestCase, TestFactoryMixin):

    def test_newer_message(self):
        now = datetime.datetime(2015, 7, 5)

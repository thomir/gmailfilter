from unittest import TestCase


from gmailfilter.tests.factory import TestFactoryMixin
from gmailfilter.test import (
    Test,
    And,
    Or,
    MatchesHeader,
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

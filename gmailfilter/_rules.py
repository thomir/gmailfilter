
"""Code for loading rules."""

import collections.abc
import os.path
import importlib
from textwrap import dedent


class RuleLoadError(Exception):
    pass


def load_rules(path=None):
    """Load the users ruleset.

    Returns a Ruleset object, or raises an exception.

    If the rules file is not found, a default one will be written, and a
    RuleLoadError will be raised.

    """
    path = path or default_rules_path()
    loader = importlib.machinery.SourceFileLoader('rules', path)
    # We may want to catch the exception here and provide a more user-friendly
    # exception.
    try:
        rules = loader.load_module()
    except FileNotFoundError:
        write_default_rules_file(path)
        raise RuleLoadError(
            "No rules file found. "
            "A default one has been written at {}.".format(path)
        )
    try:
        return RuleSet(rules.RULES)
    except AttributeError:
        raise RuleLoadError(
            "Rules file {} has no attribute 'RULES'".format(path)
        )


def write_default_rules_file(path=None):
    path = path or default_rules_path()
    with open(path, 'w') as rules_file:
        rules_file.write(dedent(
            '''
            # Sample email rules file. Edit this file to set up your email
            # filtering rules. There are a few things to remember:
            #
            # 1. This file is python3, so you can do whatever you want.
            # 2. There are a number of pre-supplied tests and actions:

            from gmailfilter import test, actions

            # 3. The only requirement is there is a variable named 'RULES'
            #    that must be an iterable of rules. See below:

            RULES = (
                # each line is a new rule.
                # The first item is a test to run.
                # All subsequent items are actions to perform.
                (test.SubjectContains('test email'), actions.Move('Junk/')),
            )
            '''
        ))

def default_rules_path():
    return os.path.expanduser('~/.config/gmailfilter/rules.py')


class RuleSet(object):

    def __init__(self, rules):
        RuleSet.check_rules(rules)
        self._rules = rules

    def __iter__(self):
        yield from self._rules

    @staticmethod
    def check_rules(rules):
        """Check rule validity. Raise RuleLoadError if any are invalid."""
        # check entire ruleset first:
        if not isinstance(rules, collections.abc.Iterable):
            raise RuleLoadError('RULES data structure must be an iterable')
        for rule in rules:
            rule_repr = repr(rule)
            if not isinstance(rule, collections.abc.Iterable) or len(rule) < 2:
                raise RuleLoadError(
                    'rule {} must be an iterable with at least '
                    'two items'.format(rule_repr)
                )
            test = rule[0]
            if not callable(getattr(test, 'match', None)):
                raise RuleLoadError('Test for rule {} does not have a '
                    'callable "match" method.'.format(rule_repr)
                )


class SimpleRuleProcessor(object):

    def __init__(self, ruleset, connection):
        self._ruleset = ruleset
        self._connection = connection

    def process_message(self, message):
        for test, *actions in self._ruleset:
            if test.match(message):
                for action in actions:
                    action.process(self._connection, message)
                break


import logging
import os
import sys
from argparse import ArgumentParser

from gmailfilter._connection import IMAPServer


def run():
    """Main entry point for command line executable."""
    args = configure_argument_parser()
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, stream=sys.stdout)
    rules_path = get_filter_file_or_raise()

    with open(rules_path) as f:
        code = compile(f.read(), rules_path, 'exec')
        exec(code, get_rule_globals_dict())


def configure_argument_parser():
    parser = ArgumentParser(
        prog="gmailfilter",
        description="Filter IMAP emails the easy way!"
    )
    parser.add_argument('-v', '--verbose', action='store_true', help="Be more verbose")
    return parser.parse_args()


def get_filter_file_or_raise():
    path = os.path.expanduser('~/.config/gmailfilter/rules')
    if not os.path.exists(path):
        raise IOError("Rules file %r does not exist" % path)
    # TODO: Check for readability?
    return path


def get_rule_globals_dict():
    rule_globals = {
        'IMAPServer': IMAPServer
    }
    return rule_globals


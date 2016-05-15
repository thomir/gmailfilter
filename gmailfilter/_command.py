
import logging
import sys
from argparse import ArgumentParser

from gmailfilter._config import (
    ServerInfo,
    default_credentials_file_location,
)
from gmailfilter._connection import IMAPConnection
from gmailfilter import _rules


def run():
    """Main entry point for command line executable."""
    args = configure_argument_parser()
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, stream=sys.stdout)
    run_new_filter()


def run_new_filter():
    try:
        s = ServerInfo.read_config_file()
    except IOError:
        ServerInfo.write_template_config_file()
        print(
            "Could not find server credentials file. A template file has been"
            "written to {}. Please edit this and re-run.".format(
                default_credentials_file_location()
            )
        )
        sys.exit(0)
    except KeyError as e:
        print(
            "Could not find required credentials key '{}'.".format(e.args[0])
        )
        sys.exit(1)
    try:
        rules = _rules.load_rules()
    except _rules.RuleLoadError as e:
        print(e)
        sys.exit(2)

    try:
        connection = IMAPConnection(s)
    except RuntimeError as e:
        print("Error: %s" % e)
        sys.exit(3)

    rule_processor = _rules.SimpleRuleProcessor(
        rules,
        connection.get_connection_proxy()
    )
    for message in connection.get_messages():
        rule_processor.process_message(message)


def configure_argument_parser():
    parser = ArgumentParser(
        prog="gmailfilter",
        description="Filter IMAP emails the easy way!"
    )
    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help="Be more verbose"
    )
    return parser.parse_args()

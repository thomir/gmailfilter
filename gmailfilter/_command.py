
import logging
import os
import sys
from argparse import ArgumentParser

from gmailfilter._connection import (
    IMAPServer,
    IMAPConnection,
    ServerInfo,
    default_credentials_file_location,
)
from gmailfilter import _rules


def run():
    """Main entry point for command line executable."""
    args = configure_argument_parser()
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, stream=sys.stdout)
    if not args.dev:
        run_old_filter()
    else:
        run_new_filter()

def run_old_filter():
    """Run the old, pre v1 filter agent. This will get deleted soon."""
    rules_path = get_filter_file_or_raise()

    with open(rules_path) as f:
        code = compile(f.read(), rules_path, 'exec')
        exec(code, get_rule_globals_dict())


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

    connection = IMAPConnection(s)
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
    parser.add_argument('-v', '--verbose', action='store_true', help="Be more verbose")
    parser.add_argument('--dev', action='store_true', help="Run new, development code.")
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

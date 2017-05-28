"""Guess the programming language of a given source file"""

import argparse
import json
import logging
from pathlib import Path
import sys
import time

from guesslang import Guess, GuesslangError, config_logging


LOGGER = logging.getLogger(__name__)

_REPORT_FILENAME = 'report-{}.json'


def main():
    """Run command line"""
    try:
        _real_main()
    except GuesslangError as error:
        LOGGER.critical("Failed: %s", error)
        sys.exit(-1)
    except KeyboardInterrupt:
        LOGGER.critical("Cancelled!")
        sys.exit(-2)


def _real_main():
    # Get the arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '-i', '--input-file', type=argparse.FileType('r'), default=sys.stdin,
        help="source code file. Default is standard input (stdin)")
    parser.add_argument(
        '-a', '--all', default=False, action='store_true',
        help="print all matching languages when guessing")
    parser.add_argument(
        '--learn', metavar='LEARN_DIR',
        help="learn from a directory containing source code files")
    parser.add_argument(
        '--test', metavar='TEST_DIR',
        help="test Guesslang model accuracy using source code files directory")
    parser.add_argument(
        '--model', metavar='MODEL_DIR',
        help="custom Guesslang learning model directory")
    parser.add_argument(
        '-d', '--debug', default=False, action='store_true',
        help="show debug messages")

    args = parser.parse_args()
    if args.learn:
        if not args.model:
            parser.error("Argument --model is required when using --learn")
        if args.all:
            parser.error("Argument --all cannot be used with --learn")

    config_logging(debug=args.debug)
    LOGGER.debug("Run with args: %s", vars(args))

    # Create a language guesser
    guess = Guess(args.model)

    if args.learn:  # Learn from source files
        accuracy = guess.learn(args.learn)
        LOGGER.info("Guessing learning accuracy is %.2f%%", 100 * accuracy)

    if args.test:  # Test Guesslang model accuracy
        results = guess.test(args.test)
        percent = 100 * results['overall-accuracy']
        LOGGER.info("The overall accuracy of the test is %.2f%%", percent)
        LOGGER.info("Test report saved into '%s'", _save_report(results))

    if not args.learn and not args.test:  # Guess language
        content = _read_file(args.input_file)

        if args.all:
            language_info = " or ".join(guess.probable_languages(content))
        else:
            language_info = guess.language_name(content)
        LOGGER.info("The source code is written in %s", language_info)

    LOGGER.debug("Exit OK")


def _read_file(input_file):
    is_stdin = input_file is sys.stdin
    if is_stdin:
        LOGGER.info("↓↓↓  Write your source code here. End with CTR^D  ↓↓↓")
    content = input_file.read()
    if not is_stdin:
        input_file.close()
    return content


def _save_report(results):
    report_filename = _REPORT_FILENAME.format(int(time.time()))
    try:
        with open(report_filename, 'w') as report_file:
            json.dump(results, report_file, indent=2, sort_keys=True)
    except OSError as error:
        LOGGER.error("Cannot save report into %s: %s", report_filename, error)
        raise GuesslangError('Cannot save report into {}: {}'.format(
            report_filename, error))

    return Path(report_filename).absolute()


if __name__ == '__main__':
    main()

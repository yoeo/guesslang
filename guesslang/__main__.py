"""Guess the programming language of a given source code"""

from argparse import ArgumentParser, FileType
from copy import deepcopy
import logging.config
import sys
from typing import Any, TextIO, Dict

from guesslang.guess import Guess, GuesslangError
from guesslang.model import DATASET


LOGGER = logging.getLogger(__name__)
LOGGING_CONFIG = {
    'version': 1,
    'formatters': {
        'simple': {
            'format': '{asctime} {name} {levelname} {message}',
            'datefmt': '%H:%M:%S',
            'style': '{'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': logging.DEBUG,
            'formatter': 'simple',
            'stream': 'ext://sys.stdout'
        }
    },
    'loggers': {
        'guesslang': {
            'level': logging.DEBUG,
            'handlers': ['console'],
            'propagate': 0
        }
    },
    'root': {
        'level': logging.DEBUG,
        'handlers': ['console'],
        'propagate': 0
    },
    'disable_existing_loggers': False
}


def main() -> None:
    """Run command line arguments"""

    # Handle command line arguments
    parser = _build_argument_parser()
    args = parser.parse_args()
    if args.train and (not args.model or not args.steps):
        parser.error('--model and --steps are required when using --train')

    # Setup loggers
    logging_level = logging.DEBUG if args.debug else logging.INFO
    logging_config = _update_config(LOGGING_CONFIG, logging_level)
    logging.config.dictConfig(logging_config)

    # Load the programming language guessing model
    LOGGER.debug(f'Arguments: {args}')
    guess = Guess(args.model)

    try:
        if args.list_supported:
            # List the supported programming languages
            languages = ', '.join(guess.supported_languages)
            print(f'Supported programming languages: {languages}')

        elif args.train:
            # Train from source code files
            LOGGER.debug(f'Train model and save result to: {args.model}')
            accuracy = guess.train(args.train, max_steps=args.steps)
            print(f'Trained model accuracy is {accuracy:.2%}')

        else:
            # Guess source code language
            LOGGER.debug(f'Guess the source code of: {args.filename}')
            content = _read_file(args.filename)
            if args.probabilities:
                # List all the detection probabilities
                scores = guess.probabilities(content)
                texts = (f' {name:20} {score:6.2%}' for name, score in scores)
                table = '\n'.join(texts)
                print(f'Language name       Probability\n{table}')
            else:
                # Print the source code programming language name
                # if it is successfully detected
                language_name = guess.language_name(content)
                if not language_name:
                    language_name = 'Unknown'
                print(f'Programming language: {language_name}')

        LOGGER.debug('Exit OK')

    except GuesslangError:
        LOGGER.critical('Failed!')
        sys.exit(1)

    except KeyboardInterrupt:
        LOGGER.critical('Cancelled!')
        sys.exit(2)


def _build_argument_parser() -> ArgumentParser:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        'filename',
        type=FileType('r'),
        default=sys.stdin,
        nargs='?',
        help="""
            source code file.
            Reads from the standard input (stdin) if no file is given
        """,
    )
    parser.add_argument(
        '-p',
        '--probabilities',
        action='store_true',
        default=False,
        help="""
            show match probability of a given source code
            with each of the supported programming languages
        """,
    )
    parser.add_argument(
        '-l',
        '--list-supported',
        action='store_true',
        default=False,
        help='list the supported programming languages',
    )
    parser.add_argument(
        '--train',
        metavar='TRAINING_DIRECTORY',
        help=f"""
            train from a directory containing source code files.
            The source files should be split in 3 directories named:
            {', '.join(DATASET.values())}.

            --model and --steps values should be provided when using --train
        """
    )
    parser.add_argument(
        '--steps',
        metavar='TRAINING_STEPS',
        type=int,
        help="""
            number of steps training steps. The model accuracy
            and the training time increase with the number of steps
        """,
    )
    parser.add_argument(
        '--model',
        metavar='MODEL_DIR',
        help='custom Guesslang trained model directory',
    )
    parser.add_argument(
        '-d',
        '--debug',
        default=False,
        action='store_true',
        help='show debug messages',
    )
    return parser


def _update_config(config: Dict[str, Any], level: int) -> Dict[str, Any]:
    logging_config = deepcopy(config)
    logging_config['root']['level'] = level
    logging_config['loggers']['guesslang']['level'] = level
    return logging_config


def _read_file(input_file: TextIO) -> str:
    if input_file is sys.stdin:
        LOGGER.debug('Write your source code here. End with CTR^D')
        content = input_file.read()
    else:
        content = input_file.read()
        input_file.close()

    return content


if __name__ == '__main__':
    main()

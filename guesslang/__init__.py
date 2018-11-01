"""
Guesslang: a machine learning program that guesses the programming language
of a given source file.

"""

from guesslang.config import config_logging  # noqa: F401
from guesslang.guesser import Guess  # noqa: F401
from guesslang.utils import GuesslangError  # noqa: F401


__version__ = '0.9.3'

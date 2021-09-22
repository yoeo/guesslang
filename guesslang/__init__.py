"""
Guesslang: a machine learning program that guesses the programming language
of a given source code.

"""

import os


# Do not let Tensorflow print its numerous warning messages on startup.
# Unless the user asked to see them by setting Tensorflow logging level.
if 'TF_CPP_MIN_LOG_LEVEL' not in os.environ:
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'


from guesslang.guess import Guess, GuesslangError  # noqa: F401


__version__ = '2.2.2'

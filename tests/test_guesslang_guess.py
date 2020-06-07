from operator import itemgetter
from pathlib import Path
import tempfile

import pytest

from guesslang import Guess, GuesslangError
from guesslang.guess import DatasetDirname


C_CODE = """
#include <stdio.h>

int main(int argc, char* argv[])
{
  printf("Hello world");
}
"""

PYTHON_CODE = """
from __future__ import print_function


if __name__ == "__main__":
    print("Hello world")
"""

PLAIN_TEXT = 'The quick brown fox jumps over the lazy dog'


def test_guess_init():
    guess = Guess()
    assert guess.is_default


def test_guess_init_with_model_dir():
    with tempfile.TemporaryDirectory() as model_dir:
        guess = Guess(model_dir)
        assert not guess.is_default


def test_guess_init_with_non_existing_model_dir():
    with tempfile.TemporaryDirectory() as model_dir:
        model_path = Path(model_dir)
        model_path.rmdir()
        assert not model_path.exists()

        guess = Guess(model_dir)
        assert not guess.is_default
        assert model_path.exists()


def test_guess_supported_languages():
    guess = Guess()
    assert len(guess.supported_languages) >= 30
    assert 'Python' in guess.supported_languages
    assert 'C' in guess.supported_languages


def test_guess_language_name():
    guess = Guess()
    assert guess.language_name(PYTHON_CODE) == 'Python'
    assert guess.language_name(C_CODE) == 'C'


def test_guess_language_name_empty_code():
    guess = Guess()
    assert guess.language_name('') is None


@pytest.mark.skip(reason='The plain text is detected as Markdown')
def test_guess_language_name_plain_text():
    guess = Guess()
    assert guess.language_name(PLAIN_TEXT) is None


def test_guess_probabilities():
    guess = Guess()
    scores = guess.probabilities(PYTHON_CODE)
    assert len(scores) == len(guess.supported_languages)

    for language, probability in scores:
        assert language in guess.supported_languages
        assert 0 <= probability <= 1

    top_language = scores[0][0]
    assert top_language == 'Python'


def test_guess_train_with_default_model():
    guess = Guess()
    with tempfile.TemporaryDirectory() as source_files_dir:
        _create_training_files(source_files_dir)

        with pytest.raises(GuesslangError):
            guess.train(source_files_dir, max_steps=10)


def test_guess_train_without_subdirectories():
    with tempfile.TemporaryDirectory() as model_dir:
        guess = Guess(model_dir)
        with tempfile.TemporaryDirectory() as source_files_dir:

            with pytest.raises(GuesslangError):
                guess.train(source_files_dir, max_steps=10)


def test_guess_train():
    with tempfile.TemporaryDirectory() as model_dir:
        guess = Guess(model_dir)
        with tempfile.TemporaryDirectory() as source_files_dir:
            _create_training_files(source_files_dir)
            guess.train(source_files_dir, max_steps=10)

        assert guess.language_name(PYTHON_CODE) == 'Python'
        assert guess.language_name(C_CODE) == 'C'


def _create_training_files(source_files_dir):
    root_path = Path(source_files_dir)
    for dirname in DatasetDirname:
        dataset_path = root_path.joinpath(dirname)
        dataset_path.mkdir()
        dataset_path.joinpath('xxx.c').write_text(C_CODE)
        dataset_path.joinpath('xxx.py').write_text(PYTHON_CODE)

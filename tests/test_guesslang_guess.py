from operator import itemgetter
from pathlib import Path
import tempfile

import pytest

from guesslang import guesser, GuesslangError

from guesslang_fixtures import FIXTURES_PATH, copy_fixtures


C_FILE = FIXTURES_PATH.joinpath('file.c')


def test_guess():
    guess = guesser.Guess()

    assert Path(guess.model_dir).exists()
    assert guess.is_default
    assert guess.languages

    with tempfile.TemporaryDirectory() as model_dir:
        guess = guesser.Guess(model_dir)
        assert Path(guess.model_dir).samefile(model_dir)
        assert Path(guess.model_dir).exists()
        assert not guess.is_default
        assert guess.languages


def test_guess_language_name():
    content = C_FILE.read_text()
    assert guesser.Guess().language_name(content) == 'C'


def test_guess_scores():
    guess = guesser.Guess()
    known_languages = list(guess.languages)

    content = C_FILE.read_text()
    scores = guess.scores(content)
    scored_languages = list(scores)
    best_scored_language = max(scores.items(), key=itemgetter(1))[0]
    assert set(known_languages) == set(scored_languages)
    assert len(known_languages) == len(scored_languages)
    assert best_scored_language == 'C'


def test_guess_probable_languages():
    content = C_FILE.read_text()
    assert 'C' in guesser.Guess().probable_languages(content)

    names = guesser.Guess().probable_languages(content, max_languages=5)
    assert len(names) <= 5


def test_guess_learn():
    with tempfile.TemporaryDirectory() as dirname:
        copy_fixtures(dirname, nb_times=10)

        # Cannot learn using default model
        with pytest.raises(GuesslangError):
            guesser.Guess().learn(dirname)

    temp_model_dir = tempfile.TemporaryDirectory()
    with tempfile.TemporaryDirectory() as dirname:
        copy_fixtures(dirname, nb_times=10)

        accuracy = guesser.Guess(temp_model_dir.name).learn(dirname)
        assert 0 <= accuracy <= 1

    try:
        temp_model_dir.cleanup()
    except OSError:
        # Occures on Windows only
        # - OSError: [WinError 145] The directory is not empty
        pass


def test_guess_test():
    with tempfile.TemporaryDirectory() as dirname:
        copy_fixtures(dirname, nb_times=10)

        report = guesser.Guess().test(dirname)
        assert 0 <= report['overall-accuracy'] <= 1
        assert report['per-language']['C']['nb-files'] == 10
        assert report['per-language']['Python']['nb-files'] == 10

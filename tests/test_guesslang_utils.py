from pathlib import Path
import random
import tempfile

import pytest

from guesslang import utils, GuesslangError

from guesslang_fixtures import copy_fixtures


random.seed()


NB_BYTES = 1024
LANGUAGES = {'C': ['c'], 'Python': ['py']}
EXTENSIONS = ['c', 'py']


def test_safe_read_file():
    for _ in range(10):
        with tempfile.TemporaryDirectory() as dirname:
            file_path = Path(dirname).joinpath('example_file')

            # Write random bytes into the file
            rand_value = random.getrandbits(8*NB_BYTES)
            file_path.write_bytes(rand_value.to_bytes(NB_BYTES, 'little'))

            # Retrieve text without raising errors
            text = utils.safe_read_file(file_path)
            assert text


def test_search_files():
    with tempfile.TemporaryDirectory() as dirname:
        copy_fixtures(dirname)

        # Not enough files in the directory
        with pytest.raises(GuesslangError):
            utils.search_files(dirname, EXTENSIONS)

    with tempfile.TemporaryDirectory() as dirname:
        copy_fixtures(dirname, nb_times=10)

        files = utils.search_files(dirname, EXTENSIONS)
        assert len(files) == 20


def test_extract_from_files():
    with tempfile.TemporaryDirectory() as dirname:
        copy_fixtures(dirname, nb_times=10)

        files = utils.search_files(dirname, EXTENSIONS)
        arrays = utils.extract_from_files(files, LANGUAGES)

        assert len(arrays) == 2
        assert all(len(values) == 20 for values in arrays)

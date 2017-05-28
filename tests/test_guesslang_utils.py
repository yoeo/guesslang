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
        with tempfile.NamedTemporaryFile('w+b') as tmp_file:
            rand_value = random.getrandbits(8*NB_BYTES)

            # Write random bytes into the file
            tmp_file.write(rand_value.to_bytes(NB_BYTES, 'little'))
            tmp_file.seek(0)

            text = utils.safe_read_file(Path(tmp_file.name))

            assert text  # Text retrieved without raising errors


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

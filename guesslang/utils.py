"""A set of tools to process files"""

import logging
import multiprocessing
from pathlib import Path
import random
import signal

import numpy as np

from guesslang.extractor import extract


LOGGER = logging.getLogger(__name__)

random.seed()

_FILE_ENCODINGS = ('utf-8', 'latin-1', 'windows-1250', 'windows-1252')
_NB_LINES = 100
_NB_FILES_MIN = 10


class GuesslangError(Exception):
    """`guesslang` base exception class"""


def search_files(source, extensions):
    """Returns the names of the files with the right extensions
    found in source directory and its subdirectories.

    A `GuesslangError` is raised when there is not enough files
    in the directory.

    ``source`` -- directory name

    ``extensions`` -- list of file extensions

    """
    files = [
        path for path in Path(source).glob('**/*')
        if path.is_file() and path.suffix.lstrip('.') in extensions]
    nb_files = len(files)
    LOGGER.debug("Total files found: %d", nb_files)

    if nb_files < _NB_FILES_MIN:
        LOGGER.error("Too few source files")
        raise GuesslangError(
            '{} source files found in {}. {} files minimum is required'.format(
                nb_files, source, _NB_FILES_MIN))

    random.shuffle(files)
    return files


def extract_from_files(files, languages):
    """Returns an array with the features extracted from the given files.

    ``files`` -- list of filenames

    ``languages`` -- dict of language names => associated files extensions list

    """
    enumerator = enumerate(sorted(languages.items()))
    rank_map = {ext: rank for rank, (_, exts) in enumerator for ext in exts}

    with multiprocessing.Pool(initializer=_process_init) as pool:
        file_iterator = ((path, rank_map) for path in files)
        arrays = _to_arrays(pool.starmap(_extract_features, file_iterator))

    LOGGER.debug("Extracted arrays count: %d", len(arrays[0]))
    return arrays


def _process_init():
    # Stop the subprocess silently when the main process is killed
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def _extract_features(path, rank_map):
    ext = path.suffix.lstrip('.')
    rank = rank_map.get(ext)
    if rank is None:
        raise GuesslangError('Language not found for ext: {}'.format(ext))

    content = safe_read_file(path)
    content = '\n'.join(content.splitlines()[:_NB_LINES])
    return [extract(content), rank]


def _to_arrays(features):
    # Flatten and split the dataset
    ranks = []
    content_vectors = []
    for content_vector, rank in features:
        ranks.append(rank)
        content_vectors.append(content_vector)

    # Convert lists into numpy arrays
    return (np.array(content_vectors), np.array(ranks))


def safe_read_file(file_path):
    """Returns the text file content, several text encodings are tried
    until the file content is correctly decoded.

    ``file_path`` -- `pathlib.Path` object, path to the file to read

    """
    for encoding in _FILE_ENCODINGS:
        try:
            return file_path.read_text(encoding=encoding)
        except UnicodeError:
            pass  # Ignore encoding error

    raise GuesslangError('Encoding not supported for {!s}'.format(file_path))

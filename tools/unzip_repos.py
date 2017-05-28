#!/usr/bin/env python3

"""
Extract files from downloaded repositories to prepare Guesslang learning:

 * testing files and learning files are retrieved from different repositories
 * they are stored into two different subdirectories
 * a limited number of files for each language are retrieved per repository

"""

import argparse
import logging
from pathlib import Path
import random
from uuid import uuid4
from zipfile import ZipFile, BadZipFile

from guesslang.config import config_dict, config_logging


LOGGER = logging.getLogger(__name__)

STEP = 100
MAX_FILES = 1000  # Max files per repository per language

random.seed()


def main():
    """Files extractor command line"""

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('source', help="location of the downloaded repos")
    parser.add_argument('destination', help="location of the extracted files")
    parser.add_argument(
        '-t', '--nb-test-files', help="number of testing files per language",
        type=int, default=5000)
    parser.add_argument(
        '-l', '--nb-learn-files', help="number of learning files per language",
        type=int, default=10000)
    parser.add_argument(
        '-r', '--remove', help="remove repos that cannot be read",
        action='store_true', default=False)
    parser.add_argument(
        '-d', '--debug', default=False, action='store_true',
        help="show debug messages")

    args = parser.parse_args()
    config_logging(args.debug)

    source = Path(args.source)
    destination = Path(args.destination)
    nb_test = args.nb_test_files
    nb_learn = args.nb_learn_files
    remove = args.remove

    repos = _find_repos(source)
    split_repos = _split_repos(repos, nb_test, nb_learn)
    split_files = _find_files(*split_repos, nb_test, nb_learn, remove)
    _unzip_all(*split_files, destination)
    LOGGER.info("Files saved into %s", destination)
    LOGGER.debug("Exit OK")


def _find_repos(source):
    LOGGER.debug("List repositories located in %s", source)
    repos = []
    for path in source.glob('**/*'):
        if path.is_file() and path.suffix == '.zip':
            repos.append(str(path))

    random.shuffle(repos)
    LOGGER.info("%d repositories found in %s", len(repos), source)
    return repos


def _split_repos(repos, nb_test, nb_learn):
    proportion = nb_test / (nb_test + nb_learn)
    limit = int(len(repos) * proportion)
    test_repos = repos[:limit]
    learn_repos = repos[limit:]

    LOGGER.info("Split learn: %d, test: %d", len(learn_repos), len(test_repos))
    return (test_repos, learn_repos)


def _find_files(test_repos, learn_repos, nb_test, nb_learn, remove):
    languages = config_dict('languages.json')

    LOGGER.info("Process %d test repositories", len(test_repos))
    full_test_files = _list_files(test_repos, languages, remove)
    test_files = _drop_extra_files(full_test_files, nb_test)

    LOGGER.info("Process %d learning repositories", len(learn_repos))
    full_learn_files = _list_files(learn_repos, languages, remove)
    learn_files = _drop_extra_files(full_learn_files, nb_learn)

    return (test_files, learn_files)


def _unzip_all(test_files, learn_files, destination):
    destination.mkdir(exist_ok=True)

    LOGGER.info("Unzip %d test files", len(test_files))
    test_destination = destination.joinpath('test')
    _unzip(test_files, test_destination)

    LOGGER.info("Unzip %d learning files", len(learn_files))
    learn_destination = destination.joinpath('learn')
    _unzip(learn_files, learn_destination)


def _list_files(repos, languages, remove):
    repo_files = {lang: [] for lang in languages}
    exts = {ext: lang for lang, exts in languages.items() for ext in exts}

    for pos, zipped_repo in enumerate(repos, 1):
        current_repo_files = {lang: [] for lang in languages}
        size = len(repos)
        if pos % STEP == 0 or pos == size:
            LOGGER.debug("%.2f%%", 100 * pos / size)

        try:
            with ZipFile(zipped_repo) as zip_file:
                for filename in zip_file.namelist():
                    lang = exts.get(Path(filename).suffix.lstrip('.'))
                    if not lang or len(current_repo_files[lang]) >= MAX_FILES:
                        continue

                    current_repo_files[lang].append(
                        '{}::{}'.format(zipped_repo, filename))
        except BadZipFile as error:
            LOGGER.warning("Malformed file %s, error: %s", zipped_repo, error)
            if remove:
                Path(zipped_repo).unlink()
                LOGGER.debug("%s removed", zipped_repo)
            continue

        for lang, zipped_files in current_repo_files.items():
            repo_files[lang].extend(zipped_files)

    return repo_files


def _drop_extra_files(repo_files, nb_files):
    files = []
    for lang in repo_files:
        size = len(repo_files[lang])
        if size < nb_files:
            LOGGER.error("Not enough files, %s: %d / %d", lang, size, nb_files)
            raise RuntimeError('Need more files for languages {}'.format(lang))

        random.shuffle(repo_files[lang])
        files.extend(repo_files[lang][:nb_files])

    return files


def _unzip(files, destination):
    size = len(files)
    destination.mkdir(exist_ok=True)
    LOGGER.debug("Unzip %d files into %s", size, destination)
    for pos, zipped_file in enumerate(files, 1):
        if pos % STEP == 0 or pos == size:
            LOGGER.debug("%.2f%%", 100 * pos / size)

        zipped_repo, filename = zipped_file.split('::')
        ext = Path(filename).suffix
        dest_path = destination.joinpath(str(uuid4()) + ext)

        try:
            with ZipFile(zipped_repo) as zip_file:
                with dest_path.open('wb') as dest_file:
                    dest_file.write(zip_file.read(filename))
        except BadZipFile as error:
            LOGGER.error("Malformed file %s, error: %s", zipped_repo, error)
            raise RuntimeError('Extraction failed for {}'.format(zipped_repo))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        LOGGER.critical("Cancelled!")
    except RuntimeError as error:
        LOGGER.critical("Aborted: %s", error)

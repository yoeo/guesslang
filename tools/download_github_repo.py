#!/usr/bin/env python3

"""
Download repos from Github.

The repositories source files will be used to feed Guesslang model.

"""

import argparse
from contextlib import closing
import functools
import logging
from pathlib import Path
import random
import time
from urllib.parse import quote_plus

import requests

from guesslang.config import config_dict, config_logging


LOGGER = logging.getLogger(__name__)

DELAY = 2  # GITHUB API rate limit is 30 request/min
LONG_DELAY = 60
MAX_RETRIES = 5

PREFIX_LEN = len('https://github.com/')
DOWNLOAD = 'https://github.com/{}/archive/master.zip'
SEARCH = (
    'https://api.github.com/search/repositories?'
    'q=language:{} created:"{}"&access_token={}&per_page=1000')

YEARS = list(range(2008, 2018))
CREATED = [
    '{0}-01-01..{0}-02-28',
    '{0}-03-01..{0}-04-30',
    '{0}-05-01..{0}-06-30',
    '{0}-07-01..{0}-08-31',
    '{0}-09-01..{0}-10-30',
    '{0}-11-01..{0}-12-31',
]

FILENAME = '{}___{}___{}.zip'
CHUNK_SIZE = 1024

STATUS_FILENAME = 'downloaded-repo-list.txt'

random.seed()


def main():
    """Github repositories downloaded command line"""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        'githubtoken',
        help="Github OAuth token, see https://developer.github.com/v3/oauth/")
    parser.add_argument('destination', help="location of the downloaded repos")
    parser.add_argument(
        '-n', '--nbrepo', help="number of repositories per language",
        type=int, default=1000)
    parser.add_argument(
        '-d', '--debug', default=False, action='store_true',
        help="show debug messages")

    args = parser.parse_args()
    config_logging(args.debug)

    destination = Path(args.destination)
    nb_repos = args.nbrepo
    token = args.githubtoken

    languages = config_dict('languages.json')
    destination.mkdir(exist_ok=True)

    for pos, language in enumerate(sorted(languages), 1):
        LOGGER.info("Step %.2f%%, %s", 100 * pos / len(languages), language)
        LOGGER.info("Fetch %d repos infos for language %s", nb_repos, language)
        repos = _retrieve_repo_details(language, nb_repos, token)
        LOGGER.info("%d repos details kept. Downloading", len(repos))
        _download_repos(language, repos, destination)
        LOGGER.info("Language %s repos downloaded", language)

    LOGGER.debug("Exit OK")


def _wait():
    LOGGER.debug("Wait %s seconds", DELAY)
    time.sleep(DELAY)


def _rest():
    LOGGER.debug("Rest for %s seconds", LONG_DELAY)
    time.sleep(LONG_DELAY)


def _retrieve_repo_details(language, nb_repos, token):
    language_code = quote_plus(language)
    repos = []
    for year in YEARS:
        for created in CREATED:
            created = created.format(year)
            url = SEARCH.format(language_code, created, token)
            items = _fetch_items(url)
            period_repos = [item['html_url'] for item in items]
            LOGGER.debug("Period '%s', %d repos", created, len(period_repos))
            repos += period_repos

    LOGGER.debug("Total repos found for language %s: %d", language, len(repos))
    random.shuffle(repos)
    return repos[:nb_repos]


def retry(default=None):
    """Retry functions after failures"""

    def decorator(func):
        """Retry decorator"""

        @functools.wraps(func)
        def _wrapper(*args, **kw):
            for pos in range(1, MAX_RETRIES):
                try:
                    return func(*args, **kw)
                except (RuntimeError, requests.ConnectionError) as error:
                    LOGGER.warning("Failed: %s, %s", type(error), error)

                # Wait a bit before retrying
                for _ in range(pos):
                    _rest()

            LOGGER.warning("Request Aborted")
            return default

        return _wrapper

    return decorator


@retry(default=[])
def _fetch_items(url):
    _wait()
    response = requests.get(url)
    if not response.ok:
        raise RuntimeError(
            '{}: {}'.format(response.status_code, response.text))

    return response.json()['items']


def _download_repos(language, repos, destination):
    for pos, name in enumerate(repos):
        name = name[PREFIX_LEN:]
        url = DOWNLOAD.format(name)
        user, project = name.split('/')
        path = destination.joinpath(FILENAME.format(language, user, project))
        LOGGER.debug("%03d. %s ==> %s", pos, url, path)
        _download_file(url, path)

    status_path = destination.joinpath(STATUS_FILENAME)
    status_path.write_text('\n'.join(repos))
    LOGGER.info("Repo list saved into %s", status_path)


@retry()
def _download_file(url, path):
    _wait()
    with closing(requests.get(url, stream=True)) as stream:
        if not stream.ok:
            LOGGER.warning("Cannot download %s: %s", url, stream.status_code)
            return

        with path.open('wb') as dest:
            for chunk in stream.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    dest.write(chunk)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        LOGGER.critical("Cancelled!")

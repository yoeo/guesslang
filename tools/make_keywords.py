#!/usr/bin/env python3

"""
Statistically generate keywords.

Spot the most representative keywords from the learning files.

"""

import argparse
from collections import Counter
import gc
import hashlib
import json
import logging
from operator import itemgetter
from pathlib import Path

from guesslang.config import config_dict, config_logging
from guesslang.extractor import split, SPECIAL_KEYWORDS
from guesslang.utils import safe_read_file, GuesslangError


LOGGER = logging.getLogger(__name__)

STEP = 1000


def main():
    """Keywords generator command line"""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('learn', help="learning source codes directory")
    parser.add_argument('keywords', help="output keywords file, JSON")
    parser.add_argument(
        '-n', '--nbkeywords', type=int, default=10000,
        help="the number of keywords to keep")
    parser.add_argument(
        '-d', '--debug', default=False, action='store_true',
        help="show debug messages")

    args = parser.parse_args()
    config_logging(args.debug)

    learn_path = Path(args.learn)
    keywords_path = Path(args.keywords)
    nb_keywords = args.nbkeywords

    languages = config_dict('languages.json')
    exts = {ext: lang for lang, exts in languages.items() for ext in exts}

    term_count = Counter()
    document_count = Counter()
    pos = 0
    LOGGER.info("Reading files form %s", learn_path)
    for pos, path in enumerate(Path(learn_path).glob('**/*'), 1):
        if pos % STEP == 0:
            LOGGER.debug("Processed %d", pos)
            gc.collect()  # Cleanup dirt

        if not path.is_file() or not exts.get(path.suffix.lstrip('.')):
            continue

        counter = _extract(path)
        term_count.update(counter)
        document_count.update(counter.keys())

    nb_terms = sum(term_count.values())
    nb_documents = pos - 1
    if not nb_documents:
        LOGGER.error("No source files found in %s", learn_path)
        raise RuntimeError('No source files in {}'.format(learn_path))

    LOGGER.info("%d unique terms found", len(term_count))

    terms = _most_frequent(
        (term_count, nb_terms), (document_count, nb_documents), nb_keywords)

    keywords = {
        token: int(hashlib.sha1(token.encode()).hexdigest(), 16)
        for token in terms
    }

    with keywords_path.open('w') as keywords_file:
        json.dump(keywords, keywords_file, indent=2, sort_keys=True)
    LOGGER.info("%d keywords written into %s", len(keywords), keywords_path)
    LOGGER.debug("Exit OK")


def _extract(path):
    text = safe_read_file(path).lower()
    tokens = [
        token for token in split(text)
        if not (len(token) > 1 and token.isdigit())]  # Drop numbers > 10

    return Counter(tokens)


def _most_frequent(terms_info, documents_info, size):
    terms_frequencies = _frequencies(*terms_info)
    document_frequencies = _frequencies(*documents_info)

    combined = {
        term: freq * document_frequencies[term]
        for term, freq in terms_frequencies.items()
    }

    terms = [item[0] for item in sorted(
        combined.items(), key=itemgetter(1), reverse=True)]
    special_terms = list(SPECIAL_KEYWORDS.values())
    nb_terms = size - len(special_terms)

    return terms[:nb_terms] + special_terms


def _frequencies(counter, total):
    return {token: value / total for token, value in counter.items()}


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        LOGGER.critical("Cancelled!")
    except (GuesslangError, RuntimeError) as error:
        LOGGER.critical("Aborted: %s", error)

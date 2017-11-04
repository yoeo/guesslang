"""Extract features (floats vector) that represent a given text"""

import logging
import re
import math

from guesslang.config import config_dict


LOGGER = logging.getLogger(__name__)

CONTENT_SIZE = 2**10

SPECIAL_KEYWORDS = {'num': '<number>', 'var': '<variable>'}
_KEYWORDS = config_dict('keywords.json')

_SEPARATOR = re.compile(r'(\W)')

_SHIFT = 17
_FACTOR = 23


def extract(text):
    """Transform the text into a vector of float values.
    The vector is a representation of the text.

    :param str text: the text to represent
    :return: representation
    :rtype: list
    """
    return _normalize(_vectorize(split(text)))


def split(text):
    """Split a text into a list of tokens.

    :param str text: the text to split
    :return: tokens
    :rtype: list
    """
    return [word for word in _SEPARATOR.split(text) if word.strip(' \t')]


def _vectorize(tokens):
    values = []
    for token in tokens:
        if token in _KEYWORDS_CACHE:
            values.append(_KEYWORDS_CACHE[token])
        elif token.isdigit():
            values.append(_KEYWORDS_CACHE[SPECIAL_KEYWORDS['num']])
        else:
            values.append(_KEYWORDS_CACHE[SPECIAL_KEYWORDS['var']])

    bigrams = [_merge(values[pos:pos+2]) for pos in range(len(values) - 1)]
    trigrams = [_merge(values[pos:pos+3]) for pos in range(len(values) - 2)]
    values += bigrams + trigrams

    vector = [0] * CONTENT_SIZE
    for short_hash, weight in values:
        vector[short_hash] += weight

    return vector


def _merge(hash_list):
    merged_hash = _SHIFT
    merged_weight = 1
    for short_hash, weight in hash_list:
        merged_hash = (merged_hash * _FACTOR + short_hash) % CONTENT_SIZE
        merged_weight *= weight
    return (merged_hash, merged_weight)


def _normalize(vector):
    length = math.sqrt(sum(value**2 for value in vector))
    if not length:
        return vector
    normalized = [value / length for value in vector]
    return normalized


def _prepare_cache():
    # Called to fill "_KEYWORDS_CACHE" dictionary
    return {
        # word: (short_hash, weight)
        word: (hash_value % CONTENT_SIZE, 1 if len(word) % 2 == 0 else -1)
        for word, hash_value in _KEYWORDS.items()
    }


_KEYWORDS_CACHE = _prepare_cache()

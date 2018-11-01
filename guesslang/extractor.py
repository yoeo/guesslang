"""Extract features (floats vector) that represent a given text"""

import logging
import re
import math
from typing import cast, Dict, Tuple, List

from guesslang.config import config_dict


LOGGER = logging.getLogger(__name__)

CONTENT_SIZE = 2**10

SPECIAL_KEYWORDS = {'num': '<number>', 'var': '<variable>'}
KEYWORDS = config_dict('keywords.json')

SEPARATOR = re.compile(r'(\W)')

SHIFT = 17
FACTOR = 23


def extract(text: str) -> List[float]:
    """Transform the text into a vector of float values.
    The vector is a representation of the text.

    :param text: the text to represent
    :return: representation
    """
    return _normalize(_vectorize(split(text)))


def split(text: str) -> List[str]:
    """Split a text into a list of tokens.

    :param text: the text to split
    :return: tokens
    """
    return [word for word in SEPARATOR.split(text) if word.strip(' \t')]


def _vectorize(tokens: List[str]) -> List[int]:
    values = []
    for token in tokens:
        if token in KEYWORDS_CACHE:
            values.append(KEYWORDS_CACHE[token])
        elif token.isdigit():
            values.append(KEYWORDS_CACHE[SPECIAL_KEYWORDS['num']])
        else:
            values.append(KEYWORDS_CACHE[SPECIAL_KEYWORDS['var']])

    bigrams = [_merge(values[pos:pos+2]) for pos in range(len(values) - 1)]
    trigrams = [_merge(values[pos:pos+3]) for pos in range(len(values) - 2)]
    values += bigrams + trigrams

    vector = [0] * CONTENT_SIZE
    for short_hash, weight in values:
        vector[short_hash] += weight

    return vector


def _merge(hash_list: List[Tuple[int, int]]) -> Tuple[int, int]:
    merged_hash = SHIFT
    merged_weight = 1
    for short_hash, weight in hash_list:
        merged_hash = (merged_hash * FACTOR + short_hash) % CONTENT_SIZE
        merged_weight *= weight
    return (merged_hash, merged_weight)


def _normalize(vector: List[int]) -> List[float]:
    length = math.sqrt(sum(value**2 for value in vector))
    if not length:
        return cast(List[float], vector)
    normalized = [value / length for value in vector]
    return normalized


def _prepare_cache() -> Dict[str, Tuple[int, int]]:
    # Called to fill "KEYWORDS_CACHE" dictionary
    return {
        # word: (short_hash, weight)
        word: (hash_value % CONTENT_SIZE, 1 if len(word) % 2 == 0 else -1)
        for word, hash_value in KEYWORDS.items()
    }


KEYWORDS_CACHE = _prepare_cache()

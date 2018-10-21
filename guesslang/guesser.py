"""Guesslang machine learning model"""

import gc
import logging
from operator import itemgetter
from math import ceil, log
from pathlib import Path
from typing import List, Tuple, Dict, Iterator, Any, Callable, Optional

import tensorflow as tf

from guesslang.config import model_info, config_dict
from guesslang.extractor import extract, CONTENT_SIZE
from guesslang.utils import (
    search_files, extract_from_files, safe_read_file, GuesslangError, DataSet)


LOGGER = logging.getLogger(__name__)

NEURAL_NETWORK_HIDDEN_LAYERS = [256, 64, 16]
OPTIMIZER_STEP = 0.05

FITTING_FACTOR = 20  # How many time the same data is used for fitting
CHUNK_PROPORTION = 0.2
CHUNK_SIZE = 1000

ACCURACY_THRESHOLDS = [60, 90, 99]


class Guess:
    """Guess the programming language of a source code.

    :param model_dir: Guesslang machine learning model directory.
    """

    def __init__(self, model_dir: Optional[str] = None) -> None:
        model_data = model_info(model_dir)

        #: `tensorflow` model directory
        self.model_dir: str = model_data[0]

        #: Tells if the current model is the default model
        self.is_default: bool = model_data[1]

        #: Supported languages associated with their extensions
        self.languages: Dict[str, List[str]] = config_dict('languages.json')

        n_classes = len(self.languages)
        feature_columns = [
            tf.contrib.layers.real_valued_column('', dimension=CONTENT_SIZE)]

        self._classifier = tf.contrib.learn.DNNLinearCombinedClassifier(
            linear_feature_columns=feature_columns,
            dnn_feature_columns=feature_columns,
            dnn_hidden_units=NEURAL_NETWORK_HIDDEN_LAYERS,
            n_classes=n_classes,
            linear_optimizer=tf.train.RMSPropOptimizer(OPTIMIZER_STEP),
            dnn_optimizer=tf.train.RMSPropOptimizer(OPTIMIZER_STEP),
            model_dir=self.model_dir)

    def language_name(self, text: str) -> str:
        """Predict the programming language name of the given source code.

        :param text: source code.
        :return: language name
        """
        values = extract(text)
        input_fn = _to_func(([values], []))
        pos: int = next(self._classifier.predict_classes(input_fn=input_fn))

        LOGGER.debug("Predicted language position %s", pos)
        return sorted(self.languages)[pos]

    def scores(self, text: str) -> Dict[str, float]:
        """A score for each language corresponding to the probability that
        the text is written in the given language.
        The score is a `float` value between 0.0 and 1.0

        :param text: source code.
        :return: language to score dictionary
        """
        values = extract(text)
        input_fn = _to_func(([values], []))
        prediction = self._classifier.predict_proba(input_fn=input_fn)
        probabilities = next(prediction).tolist()
        sorted_languages = sorted(self.languages)
        return dict(zip(sorted_languages, probabilities))

    def probable_languages(
            self,
            text: str,
            max_languages: int = 3) -> Tuple[str, ...]:
        """List of most probable programming languages,
        the list is ordered from the most probable to the least probable one.

        :param text: source code.
        :param max_languages: maximum number of listed languages.
        :return: languages list
        """
        scores = self.scores(text)

        # Sorted from the most probable language to the least probable
        sorted_scores = sorted(scores.items(), key=itemgetter(1), reverse=True)
        languages, probabilities = list(zip(*sorted_scores))

        # Find the most distant consecutive languages.
        # A logarithmic scale is used here because the probabilities
        # are most of the time really close to zero
        rescaled_probabilities = [log(proba) for proba in probabilities]
        distances = [
            rescaled_probabilities[pos] - rescaled_probabilities[pos+1]
            for pos in range(len(rescaled_probabilities)-1)]

        max_distance_pos = max(enumerate(distances, 1), key=itemgetter(1))[0]
        limit = min(max_distance_pos, max_languages)
        return languages[:limit]

    def learn(self, input_dir: str) -> float:
        """Learn languages features from source files.

        :raise GuesslangError: when the default model is used for learning
        :param input_dir: source code files directory.
        :return: learning accuracy
        """
        if self.is_default:
            LOGGER.error("Cannot learn using default model")
            raise GuesslangError('Cannot learn using default "readonly" model')

        languages = self.languages

        LOGGER.info("Extract training data")
        extensions = [ext for exts in languages.values() for ext in exts]
        files = search_files(input_dir, extensions)
        nb_files = len(files)
        chunk_size = min(int(CHUNK_PROPORTION * nb_files), CHUNK_SIZE)

        LOGGER.debug("Evaluation files count: %d", chunk_size)
        LOGGER.debug("Training files count: %d", nb_files - chunk_size)
        batches = _pop_many(files, chunk_size)

        LOGGER.debug("Prepare evaluation data")
        evaluation_data = extract_from_files(next(batches), languages)
        LOGGER.debug("Evaluation data count: %d", len(evaluation_data[0]))

        accuracy = 0
        total = ceil(nb_files / chunk_size) - 1
        LOGGER.info("Start learning")
        for pos, training_files in enumerate(batches, 1):
            LOGGER.info("Step %.2f%%", 100 * pos / total)

            LOGGER.debug("Training data extraction")
            training_data = extract_from_files(training_files, languages)
            LOGGER.debug("Training data count: %d", len(training_data[0]))

            steps = int(FITTING_FACTOR * len(training_data[0]) / 100)
            LOGGER.debug("Fitting, steps count: %d", steps)
            self._classifier.fit(input_fn=_to_func(training_data), steps=steps)

            LOGGER.debug("Evaluation")
            accuracy = self._classifier.evaluate(
                input_fn=_to_func(evaluation_data), steps=1)['accuracy']
            _comment(accuracy)

        return accuracy

    def test(self, input_dir: str) -> Dict[str, Any]:
        """Tests the model accuracy using source code files.

        :param input_dir: source code files directory.
        :return: test report
        """
        report: Dict[str, Any] = {
            'overall-accuracy': 0,
            'per-language': {
                lang: {
                    'nb-files': 0,
                    'accuracy': 0,
                    'predicted': {
                        predicted_lang: 0 for predicted_lang in self.languages
                    },
                    'predicted-files': {
                        predicted_lang: [] for predicted_lang in self.languages
                    }
                } for lang in self.languages
            }
        }

        # Test files found in input_dir
        extensions = {
            ext: lang for lang, exts in self.languages.items() for ext in exts}
        for pos, path in enumerate(Path(input_dir).glob('**/*'), 1):
            if not path.is_file():
                continue

            lang = extensions.get(path.suffix.lstrip('.'))
            if lang is None:
                continue

            content = safe_read_file(path)
            predicted_lang = self.language_name(content)
            language_info = report['per-language'][lang]
            language_info['nb-files'] += 1
            language_info['predicted'][predicted_lang] += 1
            language_info['predicted-files'][predicted_lang].append(str(path))
            LOGGER.debug("[%d] files processed", pos)

        # Fill the report accuracy data
        total_success = 0
        total_files = 0
        for lang in self.languages:

            nb_files = report['per-language'][lang]['nb-files']
            if not nb_files:
                continue

            nb_success = report['per-language'][lang]['predicted'][lang]
            report['per-language'][lang]['accuracy'] = nb_success / nb_files
            total_success += nb_success
            total_files += nb_files

        report['overall-accuracy'] = (
            total_success / total_files if total_files else 0.0)

        return report


def _pop_many(items: List[Path], chunk_size: int) -> Iterator[List[Path]]:
    while items:
        yield items[0:chunk_size]

        # Avoid memory overflow
        del items[0:chunk_size]
        gc.collect()


def _to_func(vector: DataSet) -> Callable[[], Tuple[Any, Any]]:
    return lambda: (
        tf.constant(vector[0], name='const_features'),
        tf.constant(vector[1], name='const_labels'))


def _comment(accuracy: float) -> None:
    not_bad, good, perfect = ACCURACY_THRESHOLDS
    percentage = 100 * accuracy

    if percentage < not_bad:
        LOGGER.warning("* Underfit! Accuracy: %.2f%%", percentage)
    elif percentage < good:
        LOGGER.warning("* Fair-fit! Accuracy: %.2f%%", percentage)
    elif percentage < perfect:
        LOGGER.info("* Well-fit! Accuracy: %.2f%%", percentage)
    else:
        LOGGER.info("* Perfectly-fit! Accuracy: %.2f%%", percentage)

"""Guesslang machine learning model"""

import gc
import logging
from pathlib import Path
from math import ceil
from operator import itemgetter
from statistics import stdev

import tensorflow as tf

from guesslang.config import model_info, config_dict
from guesslang.extractor import extract, CONTENT_SIZE
from guesslang.utils import (
    search_files, extract_from_files, safe_read_file, GuesslangError)


LOGGER = logging.getLogger(__name__)

_NEURAL_NETWORK_HIDDEN_LAYERS = [256, 64, 16]
_OPTIMIZER_STEP = 0.05

_FITTING_FACTOR = 20  # How many time the same data is used for fitting
_CHUNK_PROPORTION = 0.2
_CHUNK_SIZE = 1000

_K_STDEV = 2
_ACCURACY_THRESHOLDS = [60, 90, 99]
_REPORT_FILENAME = 'report-{}.json'


class Guess:
    """Guess the programming language of a source code."""

    def __init__(self, model_dir=None):
        """Programming language guesser.

        ``model_dir`` -- Guesslang machine learning model directory.

        """
        model_data = model_info(model_dir)

        #: `tensorflow` model directory
        self.model_dir = model_data[0]

        #: tells if current model is the default model
        self.is_default = model_data[1]

        #: supported languages with associated extensions
        self.languages = config_dict('languages.json')

        n_classes = len(self.languages)
        feature_columns = [
            tf.contrib.layers.real_valued_column('', dimension=CONTENT_SIZE)]

        self._classifier = tf.contrib.learn.DNNLinearCombinedClassifier(
            linear_feature_columns=feature_columns,
            dnn_feature_columns=feature_columns,
            dnn_hidden_units=_NEURAL_NETWORK_HIDDEN_LAYERS,
            n_classes=n_classes,
            linear_optimizer=tf.train.RMSPropOptimizer(_OPTIMIZER_STEP),
            dnn_optimizer=tf.train.RMSPropOptimizer(_OPTIMIZER_STEP),
            model_dir=self.model_dir)

    def language_name(self, text):
        """Returns the predicted programming language name.

        ``text`` -- source code.

        """
        values = extract(text)
        input_fn = _to_func([[values], []])
        pos = next(self._classifier.predict_classes(input_fn=input_fn))

        LOGGER.debug("Predicted language position %s", pos)
        return sorted(self.languages)[pos]

    def probable_languages(self, text):
        """Returns the list of most probable programming languages,
        the list is ordered from the most probable to the less probable.

        ``text`` -- source code.

        """
        values = extract(text)
        input_fn = _to_func([[values], []])
        proba = next(self._classifier.predict_proba(input_fn=input_fn))
        proba = proba.tolist()
        threshold = max(proba) - _K_STDEV * stdev(proba)

        items = sorted(enumerate(proba), key=itemgetter(1), reverse=True)
        LOGGER.debug("Threshold: %f, probabilities: %s", threshold, items)

        positions = [pos for pos, value in items if value > threshold]
        LOGGER.debug("Predicted languages positions %s", positions)

        names = sorted(self.languages)
        return [names[pos] for pos in positions]

    def learn(self, input_dir):
        """Learns languages features from source files.

        ``input_dir`` -- source code files directory.

        """
        if self.is_default:
            LOGGER.error("Cannot learn using default model")
            raise GuesslangError('Cannot learn using default "readonly" model')

        languages = self.languages

        LOGGER.info("Extract training data")
        extensions = [ext for exts in languages.values() for ext in exts]
        files = search_files(input_dir, extensions)
        nb_files = len(files)
        chunk_size = min(int(_CHUNK_PROPORTION * nb_files), _CHUNK_SIZE)

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

            steps = int(_FITTING_FACTOR * len(training_data[0]) / 100)
            LOGGER.debug("Fitting, steps count: %d", steps)
            self._classifier.fit(input_fn=_to_func(training_data), steps=steps)

            LOGGER.debug("Evaluation")
            accuracy = self._classifier.evaluate(
                input_fn=_to_func(evaluation_data), steps=1)['accuracy']
            _comment(accuracy)

        return accuracy

    def test(self, input_dir):
        """Tests the model accuracy using source code files.

        ``input_dir`` -- source code files directory.

        """
        report = {
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


def _pop_many(items, chunk_size):
    while items:
        yield items[0:chunk_size]

        # Avoid memory overflow
        del items[0:chunk_size]
        gc.collect()


def _to_func(vector):
    return lambda: (
        tf.constant(vector[0], name='const_features'),
        tf.constant(vector[1], name='const_labels'))


def _comment(accuracy):
    not_bad, good, perfect = _ACCURACY_THRESHOLDS
    percentage = 100 * accuracy

    if percentage < not_bad:
        LOGGER.warning("* Underfit! Accuracy: %.2f%%", percentage)
    elif percentage < good:
        LOGGER.warning("* Fair-fit! Accuracy: %.2f%%", percentage)
    elif percentage < perfect:
        LOGGER.info("* Well-fit! Accuracy: %.2f%%", percentage)
    else:
        LOGGER.info("* Perfectly-fit! Accuracy: %.2f%%", percentage)

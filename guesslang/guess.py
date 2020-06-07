"""Guesslang machine learning model"""

from copy import deepcopy
from enum import Enum
from functools import partial, wraps
import json
import logging
from operator import itemgetter
from pathlib import Path
from statistics import mean, stdev
from typing import List, Tuple, Dict, Any, Callable, Optional

import tensorflow as tf


LOGGER = logging.getLogger(__name__)

DATA_DIR = Path(__file__).absolute().parent.joinpath('data')
DEFAULT_MODEL_DIR = DATA_DIR.joinpath('model')
LANGUAGES_FILE = DATA_DIR.joinpath('languages.json')
TRAINING_REPORT_FILE = 'report.json'


class Guess:
    """Guess the programming language of a source code.

    :param model_dir: Guesslang machine learning model directory.
    """

    def __init__(self, model_dir: Optional[str] = None) -> None:
        if model_dir:
            model_path = Path(model_dir).absolute()
            model_path.mkdir(exist_ok=True)
            is_default = False
        else:
            model_path = DEFAULT_MODEL_DIR
            is_default = True

        #: Tells if the current model is the default model or a custom one
        self.is_default: bool = is_default

        language_json = LANGUAGES_FILE.read_text()
        language_info = json.loads(language_json)

        self._language_map = {
            name: exts[0] for name, exts in language_info.items()
        }
        self._extension_map = {
            ext: name for name, ext in self._language_map.items()
        }
        self._model_dir = str(model_path)
        self._estimator = _build_model(
            self._model_dir, list(self._extension_map)
        )

    @property
    def supported_languages(self) -> List[str]:
        """List supported programming languages

        :return: language name list.
        """
        return list(self._language_map.keys())

    def language_name(self, source_code: str) -> Optional[str]:
        """Predict the programming language name of the given source code.

        :param source_code: source code.
        :return: the language name
            or ``None`` if no programming language is detected.
        """
        if not source_code.strip():
            LOGGER.warning('Empty source code provided')
            return None

        language_probabilities = self.probabilities(source_code)
        probabilities = [value for _, value in language_probabilities]
        if not _is_reliable(probabilities):
            LOGGER.warning('No programming language detected')
            return None

        language_name, _ = language_probabilities[0]
        return language_name

    def probabilities(self, source_code: str) -> List[Tuple[str, float]]:
        """Gives the probability that the source code is written
        in each of the supported languages.

        The probabilities are sorted from the most to the least probable
        programming language.

        :param source_code: source code.
        :return: list of language names associated with their probablilty.
        """
        predicted = self._estimator.predict(input_fn=_prediction(source_code))
        result = next(predicted)

        numpy_floats = result['probabilities']
        extensions = result['all_classes']

        probability_values = (float(value) for value in numpy_floats)
        languages = (self._extension_map[ext.decode()] for ext in extensions)

        unsorted_scores = zip(languages, probability_values)
        scores = sorted(unsorted_scores, key=itemgetter(1), reverse=True)
        return scores

    def train(self, source_files_dir: str, max_steps: int) -> float:
        """Train guesslang to recognize programming languages.

        The machine learning model is trained from source code files.
        The files should be split in three subdirectories named
        "train", "valid" and "test".

        :raise GuesslangError: when the training cannot be run.
        :param source_files_dir: directory that contains
            the "train", "valid" and "test" datasets.
        :return: training accuracy, a value between 0 and 1.
        """

        LOGGER.debug('Run safety checks before training')
        if self.is_default:
            LOGGER.error('Cannot train the readonly default model')
            raise GuesslangError('Cannot train the readonly default model')

        LOGGER.debug('Prepare the training')
        input_path = Path(source_files_dir)
        for dirname in DatasetDirname:
            dataset_path = input_path.joinpath(dirname)
            if not dataset_path.is_dir():
                LOGGER.error(f'Dataset directory missing {dataset_path}')
                raise GuesslangError(f'No dataset directory: {dataset_path}')

        train_spec = tf.estimator.TrainSpec(
            input_fn=_training(input_path),
            max_steps=max_steps,
        )

        if max_steps > TrainingInfo.LONG_TRAINING_STEPS:
            throttle_secs = TrainingInfo.LONG_DELAY
        else:
            throttle_secs = TrainingInfo.SHORT_DELAY

        eval_spec = tf.estimator.EvalSpec(
            input_fn=_validation(input_path),
            start_delay_secs=TrainingInfo.SHORT_DELAY,
            throttle_secs=throttle_secs,
        )

        LOGGER.debug('Train the model')
        tf.estimator.train_and_evaluate(
            self._estimator, train_spec, eval_spec
        )

        LOGGER.debug('Test the trained model')
        matches = self._test_accuracy(input_path)

        # Store the training result in a report file
        report_file = Path(self._model_dir).joinpath(TRAINING_REPORT_FILE)
        json_data = json.dumps(matches, indent=2, sort_keys=True)
        report_file.write_text(json_data)
        LOGGER.debug(f'Test report stored in {report_file}')

        languages = self._language_map.keys()
        total = sum(sum(values.values()) for values in matches.values())
        success = sum(matches[language][language] for language in languages)

        accuracy = success / total
        LOGGER.debug(f'Accuracy = {success} / {total} = {accuracy:.2%}')
        return accuracy

    def _test_accuracy(self, input_path: Path) -> Dict[str, Dict[str, int]]:
        test_function = _test(input_path)
        labels = [info.numpy()[0].decode() for _, info in test_function()]
        predictions = self._estimator.predict(input_fn=test_function)

        values = {language: 0 for language in self._language_map}
        matches = {language: deepcopy(values) for language in values}

        for label, prediction in zip(labels, predictions):
            predicted_class = prediction['classes'][0].decode()

            label_language = self._extension_map[label]
            predicted_language = self._extension_map[predicted_class]
            matches[label_language][predicted_language] += 1

        return matches


class GuesslangError(Exception):
    """Guesslang exception class"""


# Language guessing model

class HyperParameter:
    """Model hyper parameters"""
    BATCH_SIZE = 100
    NB_TOKENS = 1000
    VOCABULARY_SIZE = 20000
    EMBEDDING_SIZE = int(VOCABULARY_SIZE**0.5)
    DNN_HIDDEN_UNITS = [512, 32]
    DNN_DROPOUT = 0.5


class TrainingInfo:
    """Model training configuration"""
    SHUFFLE_BUFFER = HyperParameter.BATCH_SIZE * 10
    CHECKPOINT_STEPS = 1000
    LONG_TRAINING_STEPS = 10 * CHECKPOINT_STEPS
    SHORT_DELAY = 60
    LONG_DELAY = 5 * SHORT_DELAY


def _build_model(model_dir: str, extensions: List[str]) -> Any:
    config = tf.estimator.RunConfig(
        model_dir=model_dir,
        save_checkpoints_steps=TrainingInfo.CHECKPOINT_STEPS,
    )
    content_categories = tf.feature_column.categorical_column_with_hash_bucket(
        key='content',
        hash_bucket_size=HyperParameter.VOCABULARY_SIZE,
    )
    content_dense = tf.feature_column.embedding_column(
        categorical_column=content_categories,
        dimension=HyperParameter.EMBEDDING_SIZE,
    )
    label_vocabulary = extensions
    n_classes = len(extensions)

    return tf.estimator.DNNLinearCombinedClassifier(
        linear_feature_columns=[content_categories],
        dnn_feature_columns=[content_dense],
        dnn_hidden_units=HyperParameter.DNN_HIDDEN_UNITS,
        dnn_dropout=HyperParameter.DNN_DROPOUT,
        label_vocabulary=label_vocabulary,
        n_classes=n_classes,
        config=config,
    )


# Model input functions

class DatasetDirname(str, Enum):
    """Model training files subdirectories"""
    TRAINING: str = 'train'
    VALIDATION: str = 'valid'
    TEST: str = 'test'

    def __str__(self) -> str:
        return format(self)


def _input_function(function: Callable[..., Any]) -> Callable[..., Any]:

    @wraps(function)
    def wrapped(*args: Any, **kw: Any) -> Callable[[], Any]:
        return partial(function, *args, **kw)

    return wrapped


@_input_function
def _training(data_path: Path) -> tf.data.Dataset:
    pattern = str(data_path.joinpath(DatasetDirname.TRAINING, '*'))
    return (
        tf.data.Dataset
        .list_files(pattern, shuffle=True)
        .map(_read_file)
        .shuffle(TrainingInfo.SHUFFLE_BUFFER)
        .repeat()
        .map(_preprocess_text)
        .batch(HyperParameter.BATCH_SIZE)
    )


@_input_function
def _validation(data_path: Path) -> tf.data.Dataset:
    pattern = str(data_path.joinpath(DatasetDirname.VALIDATION, '*'))
    return (
        tf.data.Dataset
        .list_files(pattern, shuffle=True)
        .map(_read_file)
        .map(_preprocess_text)
        .batch(HyperParameter.BATCH_SIZE)
    )


@_input_function
def _test(data_path: Path) -> tf.data.Dataset:
    pattern = str(data_path.joinpath(DatasetDirname.TEST, '*'))
    return (
        tf.data.Dataset
        .list_files(pattern, shuffle=False)
        .map(_read_file)
        .map(_preprocess_text)
        .batch(1)
    )


@_input_function
def _prediction(text: bytes) -> tf.data.Dataset:
    return (
        tf.data.Dataset
        .from_tensor_slices([text])
        .map(_empty_label)
        .map(_preprocess_text)
        .batch(1)
    )


def _read_file(filename: str) -> Tuple[tf.Tensor, tf.Tensor]:
    data = tf.io.read_file(filename)
    label = tf.strings.split([filename], '.').values[-1]
    return data, label


def _preprocess_text(
    data: tf.Tensor,
    label: tf.Tensor,
) -> Tuple[Dict[str, tf.Tensor], tf.Tensor]:
    padding = tf.constant(['']*HyperParameter.NB_TOKENS)
    data = tf.strings.split([data]).values
    data = tf.concat((data, padding), axis=0)
    data = data[:HyperParameter.NB_TOKENS]
    return {'content': data}, label


def _empty_label(text: tf.Tensor) -> Tuple[tf.Tensor, tf.Tensor]:
    return text, tf.constant([''])


def _is_reliable(probabilities: List[float]) -> bool:
    """Arbitrary rule to determine if the prediction is reliable or not:

    The predicted language probability must be higher than
    2 standard deviations from the mean.
    """
    threshold = mean(probabilities) + 2*stdev(probabilities)
    predicted_language_probability = max(probabilities)
    return predicted_language_probability > threshold

"""Guesslang machine learning model"""

import json
import logging
from pathlib import Path
from statistics import mean, stdev
from tempfile import TemporaryDirectory
from typing import List, Tuple, Optional

from guesslang import model


LOGGER = logging.getLogger(__name__)

DATA_DIR = Path(__file__).absolute().parent.joinpath('data')
DEFAULT_MODEL_DIR = DATA_DIR.joinpath('model')
LANGUAGES_FILE = DATA_DIR.joinpath('languages.json')
TEST_REPORT_FILE = 'test-report.json'


class Guess:
    """Guess the programming language of a source code.

    :param model_dir: Guesslang machine learning model directory.
    """

    def __init__(self, model_dir: Optional[str] = None) -> None:
        if model_dir:
            self._saved_model_dir = model_dir
        else:
            self._saved_model_dir = str(DEFAULT_MODEL_DIR)

        try:
            self._model = model.load(self._saved_model_dir)
        except OSError:
            self._model = None

        language_json = LANGUAGES_FILE.read_text()
        language_info = json.loads(language_json)
        self._language_map = {
            name: exts[0] for name, exts in language_info.items()
        }
        self._extension_map = {
            ext: name for name, ext in self._language_map.items()
        }

    @property
    def is_trained(self) -> bool:
        """Check if the current machine learning model is trained.
        Only trained models can be used for prediction.

        :return: the model training status.
        """
        return self._model is not None

    @property
    def supported_languages(self) -> List[str]:
        """List supported programming languages

        :return: language name list.
        """
        return list(self._language_map)

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
        if not self._is_reliable(probabilities):
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
        :return: list of language names associated with their probability.
        """
        if not self.is_trained:
            LOGGER.error('Cannot predict using an untrained model')
            raise GuesslangError(
                f'Cannot predict using the untrained model located at '
                f'{self._saved_model_dir}. '
                f'Train your model with `guess.train(source_files_dir)`'
            )

        return model.predict(self._model, self._extension_map, source_code)

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

        LOGGER.debug('Run safety checks before starting the training')

        if self.is_trained:
            LOGGER.error('Model already trained')
            raise GuesslangError(
                f'The current model located at {self._saved_model_dir} '
                f'is already trained'
            )

        input_path = Path(source_files_dir)
        for dirname in model.DATASET.values():
            dataset_path = input_path.joinpath(dirname)
            if not dataset_path.is_dir():
                LOGGER.error(f'Dataset directory missing {dataset_path}')
                raise GuesslangError(f'No dataset directory: {dataset_path}')

        LOGGER.debug('Run the training')
        extensions = list(self._extension_map)
        with TemporaryDirectory() as model_logs_dir:
            estimator = model.build(model_logs_dir, extensions)
            metrics = model.train(estimator, source_files_dir, max_steps)
            LOGGER.info(f'Training metrics: {metrics}')
            model.save(estimator, self._saved_model_dir)

        LOGGER.debug(f'Test newly trained model {self._saved_model_dir}')
        self._model = model.load(self._saved_model_dir)
        matches = model.test(
            self._model, source_files_dir, self._extension_map
        )

        report_file = Path(self._saved_model_dir).joinpath(TEST_REPORT_FILE)
        json_data = json.dumps(matches, indent=2, sort_keys=True)
        report_file.write_text(json_data)
        LOGGER.debug(f'Test report stored in {report_file}')

        languages = self._language_map.keys()
        total = sum(sum(values.values()) for values in matches.values())
        success = sum(matches[language][language] for language in languages)
        accuracy = success / total
        LOGGER.debug(f'Accuracy = {success} / {total} = {accuracy:.2%}')
        return accuracy

    @staticmethod
    def _is_reliable(probabilities: List[float]) -> bool:
        """Arbitrary rule to determine if the prediction is reliable:

        The predicted language probability must be higher than
        2 standard deviations from the mean.
        """
        threshold = mean(probabilities) + 2*stdev(probabilities)
        predicted_language_probability = max(probabilities)
        return predicted_language_probability > threshold


class GuesslangError(Exception):
    """Guesslang exception class"""

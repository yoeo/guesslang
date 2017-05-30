"""Load configuration from guesslang `config` directory"""

import json
import logging.config
from pathlib import Path
import platform

from pkg_resources import (
    Requirement, resource_string, resource_filename, DistributionNotFound)

import tensorflow as tf


LOGGER = logging.getLogger(__name__)

_PACKAGE = Requirement.parse('guesslang')
_DATADIR = 'guesslang/data/{}'
_DATA_FALLBACK = Path(__file__).parent.joinpath('data')


class ColorLogFormatter(logging.Formatter):
    """Logging formatter that prints pretty colored log messages"""

    STYLE = {
        # Log messages styles
        'DEBUG': '\033[94m',
        'INFO': '\033[0m',
        'WARNING': '\033[93m',
        'ERROR': '\033[1;91m',
        'CRITICAL': '\033[1;95m',
        # Other styles
        'LEVEL': '\033[1m',
        'END': '\033[0m',
    }

    def format(self, record):
        if platform.system() != 'Linux':  # Avoid funny logs on Windows & MacOS
            return super().format(record)

        record.msg = (
            self.STYLE[record.levelname] + record.msg + self.STYLE['END'])
        record.levelname = (
            self.STYLE['LEVEL'] + record.levelname + self.STYLE['END'])
        return super().format(record)


def config_logging(debug=False):
    """Set-up application and `tensorflow` logging.

    ``debug`` -- show or hide debug messages.

    """
    if debug:
        level = 'DEBUG'
        tf_level = tf.logging.INFO
    else:
        level = 'INFO'
        tf_level = tf.logging.ERROR

    logging_config = config_dict('logging.json')
    for logger in logging_config['loggers'].values():
        logger['level'] = level

    logging.config.dictConfig(logging_config)
    tf.logging.set_verbosity(tf_level)


def config_dict(name):
    """Returns a JSON dict loaded from Guesslang config directory.

    ``name`` -- the JSON file name.

    """
    try:
        content = resource_string(_PACKAGE, _DATADIR.format(name)).decode()
    except DistributionNotFound as error:
        LOGGER.warning("Cannot load %s from packages: %s", name, error)
        content = _DATA_FALLBACK.joinpath(name).read_text()

    return json.loads(content)


def model_info(model_dir=None):
    """Returns Guesslang model directory name,
    and tells if it is the default model.

    ``model_dir`` -- the model location,
                     if `None` the default model is returned.

    """
    if model_dir is None:
        try:
            model_dir = resource_filename(_PACKAGE, _DATADIR.format('model'))
        except DistributionNotFound as error:
            LOGGER.warning("Cannot load model from packages: %s", error)
            model_dir = str(_DATA_FALLBACK.joinpath('model').absolute())
        is_default_model = True
    else:
        is_default_model = False

    model_path = Path(model_dir)
    model_path.mkdir(exist_ok=True)
    LOGGER.debug("Using model: %s, default: %s", model_path, is_default_model)

    return (model_dir, is_default_model)

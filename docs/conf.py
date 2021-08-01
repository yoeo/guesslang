# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))

import ast
from pathlib import Path
import re
import sys


# Add Guesslang path for autodoc
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

# -- Project information -----------------------------------------------------


def read_version(base_module):
    version_pattern = r'__version__\s+=\s+(.*)'
    init_path = Path(Path(__file__).parent.parent, base_module, '__init__.py')
    repr_value = re.search(version_pattern, init_path.read_text()).group(1)
    return ast.literal_eval(repr_value)


project = 'Guesslang'
copyright = '2021, Y. SOMDA'
author = 'Y. SOMDA'

# The full version, including alpha/beta/rc tags
release = read_version('guesslang')


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ['sphinx.ext.autodoc', 'sphinx_rtd_theme']
autodoc_mock_imports = ['tensorflow']
master_doc = 'index'

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
html_logo = '_static/images/guesslang.png'
html_favicon = '_static/images/favicon.png'
html_css_files = ['css/custom.css']
html_context = {
    'display_github': True,
    'github_user': 'yoeo',
    'github_repo': 'guesslang',
    'github_version': 'master/docs/',
}
html_theme_options = {'collapse_navigation': False}

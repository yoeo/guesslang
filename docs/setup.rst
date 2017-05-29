Setting up Guesslang
====================

.. toctree::
   :maxdepth: 2

Prerequisite
------------

Guesslang is a Python 3.5+ application,
make sure that **Python 3.5 or later** is installed in your system.

.. code-block:: shell
    :linenos:

    python3 --version  # must be >= 3.5

Guesslang is based on `Tensorflow <https://www.tensorflow.org/>`_
framework.

Installation
------------

* Install using pip

You can install Guesslang on your system our virtualenv using this command:

.. code-block:: shell
    :linenos:

    pip3 install guesslang

* Or from source code

Download Guesslang source code from https://github.com/yoeo/guesslang,
then type the following command:

.. code-block:: shell
    :linenos:

    pip3 install .

* Build documentation

To build this documentation you can install Sphinx ``pip3 install sphinx``
then run:

.. code-block:: shell
    :linenos:

    cd docs
    make html

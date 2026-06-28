JVM runtime
===========

Guesslang's Python package remains the default and reference implementation.
It provides the stable ``guesslang`` command line interface, Python API,
training support, and the TensorFlow model pipeline.

The ``jvm`` directory contains an alternative JVM runtime for applications that
need language detection inside a Java/Kotlin process or cannot install the
Python TensorFlow runtime. It uses an ONNX export of the Guesslang model through
DJL and ONNX Runtime.

When to use each runtime
------------------------

Use the Python runtime when you need the supported PyPI package, the Python API,
training, or exact behavior from the current TensorFlow model.

Use the JVM runtime when you need a Gradle-built CLI, IDE/plugin integration, or
deployment into JVM-only services. The JVM runtime is intentionally isolated in
``jvm`` so it does not affect Python packaging or existing CLI behavior.

Build and run
-------------

The JVM runtime requires JDK 17. From the ``jvm`` directory:

.. code-block:: shell

  ./gradlew build
  ./gradlew installDist
  echo 'def hello(): pass' | build/install/guesslang-onnx-cli/bin/guesslang-onnx-cli --topk 3 --sort

On Windows, use ``gradlew.bat`` and the ``.bat`` script under
``build/install/guesslang-onnx-cli/bin``.

Parity testing
--------------

The JVM runtime includes two validation paths:

* ``./gradlew build`` compiles the standalone JVM project.
* ``python jvm/scripts/parity_test.py`` compares Python and JVM top-1 language
  predictions for the same snippets.

The parity script expects the Python package dependencies to be installed and
the JVM distribution to have been built with ``./gradlew installDist`` from the
``jvm`` directory.

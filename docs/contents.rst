Guesslang documentation
=======================

Guesslang detects the programming language of a given source code.

It supports **30** programming **languages** and detects
the correct programming language with more than **90% accuracy**.

`Guesslang is an open source <https://github.com/yoeo/guesslang>`_
deep learning software that have been trained with
**over a million** source code files.

You can use Guesslang as a command line interface tool or as a Python module:

.. code-block:: python

  from guesslang import Guess

  guess = Guess()

  # Guess the language from code
  language = guess.language_name("""
      % Quick sort

      -module (recursion).
      -export ([qsort/1]).

      qsort([]) -> [];
      qsort([Pivot|T]) ->
             qsort([X || X <- T, X < Pivot])
             ++ [Pivot] ++
             qsort([X || X <- T, X >= Pivot]).
      """)

  print(language)  # --> Erlang

Guesslang supports **30** of the **most popular** programming languages:

+------------------+-----------------+----------------------+----------+----------------+
| ``Batchfile``    | ``C``           | ``C#``               | ``C++``  | ``CSS``        |
+------------------+-----------------+----------------------+----------+----------------+
| ``CoffeeScript`` | ``Erlang``      | ``Go``               | ``HTML`` | ``Haskell``    |
+------------------+-----------------+----------------------+----------+----------------+
| ``Java``         | ``JavaScript``  | ``Jupyter Notebook`` | ``Lua``  | ``Markdown``   |
+------------------+-----------------+----------------------+----------+----------------+
| ``Matlab``       | ``Objective-C`` | ``PHP``              | ``Perl`` | ``PowerShell`` |
+------------------+-----------------+----------------------+----------+----------------+
| ``Python``       | ``R``           | ``Ruby``             | ``Rust`` | ``SQL``        |
+------------------+-----------------+----------------------+----------+----------------+
| ``Scala``        | ``Shell``       | ``Swift``            | ``TeX``  | ``TypeScript`` |
+------------------+-----------------+----------------------+----------+----------------+


Guesslang is used by cool projects like the guessing game
`GG <https://github.com/yoeo/gg>`_ or
the `Slack <https://slack.com>`_ bot `Pasta <https://github.com/yoeo/pasta>`_.

It is also used by the `Chameledit <https://github.com/yoeo/chameledit>`_,
web-editor to automagically **highlight** source code:

.. raw:: html

  <div>
    <video width="100%" autoplay loop>
      <source src="_static/videos/chameledit.webm" type="video/webm">
      <source src="_static/videos/chameledit.mp4" type="video/mp4">
      Video not supported by your browser :-(
    </video>
  </div>

  <center><i>— Chameledit in action.</i></center>
  <br><br>

Table of contents
=================

.. contents::
  :local:

Install Guesslang
-----------------

Guesslang requires **Python 3.6 or later**.

Install from Pypi
^^^^^^^^^^^^^^^^^

You can run the following command to install Guesslang on your system:

.. code-block:: shell

  pip install guesslang

Install from source code
^^^^^^^^^^^^^^^^^^^^^^^^

To install Guesslang from source code,
just download the source code from https://github.com/yoeo/guesslang,
then run this command:

.. code-block:: shell

  pip install .

Usage
-----

Python package
^^^^^^^^^^^^^^

Guesslang Python library helps you detect the programming language
of a given text within your Python program.
The Python classes are fully docummentation here: :doc:`guesslang`.

Command line tool
^^^^^^^^^^^^^^^^^

On a terminal emulator, you can detect the programming language
of a source code file by running ``guesslang /path/to/file``.

As well, you can detect the programming language of a source code
provided through the standard input using a
`pipeline <https://en.wikipedia.org/wiki/Pipeline_%28Unix%29>`_
like ``some-command | guesslang``.

Examples:

* Detect the programming language of ``/bin/which`` software

  .. code-block:: shell

    guesslang /bin/which

    # ⟶ Programming language: Shell

* Detect the programming language of a source code stored in a file

  .. code-block:: shell

    echo "
      class Array
        def quick_sort
          return self if length <= 1
          pivot = self[0]
          less, greatereq = self[1..-1].partition { |x| x < pivot }
          less.quick_sort + [pivot] + greatereq.quick_sort
        end
      end
    " > /tmp/quicksort

    guesslang /tmp/quicksort

    # ⟶ Programming language: Ruby

* Execute a command that generates source code then detect
  the programming language on the fly:

  .. code-block:: shell

    echo '
      Array.prototype.quick_sort = function () {
         if (this.length < 2) { return this; }

         var pivot = this[Math.round(this.length / 2)];

         return this.filter(x => x <  pivot)
                    .quick_sort()
                    .concat(this.filter(x => x == pivot))
                    .concat(this.filter(x => x >  pivot).quick_sort());
      };
    ' | guesslang

    # ⟶ Programming language: JavaScript

With Guesslang command line tool you can also
show the detection **probabilities** for a given source code
and even **train** your **custom** programming language detection model.

Run ``guesslang --help`` to see all the available options.

How does Guesslang guess?
-------------------------

Deep learning Model
^^^^^^^^^^^^^^^^^^^

Guesslang uses a deep learning `Tensorflow <https://www.tensorflow.org/>`_
model built with more than **1,000,000** unique source code files,
from over **100,000** differents projects.

Guesslang model is a Deep Neural Network classifier
combined with Linear classifier.
The model's hyperparameters have been fine tuned to have both
the best **performances** and the best **generalization**.

Training
^^^^^^^^

Having a data set with a **very large** number of **diverse** examples
is essential to correctly train a model.

For Guesslang we built a large dataset using:

* **1 080 000** unique source code **files**
* randomly picked from **101 871** public open source Github **repositories**.

This large dataset built with
`GuesslangTools <https://github.com/yoeo/guesslangtools>`_,
is used to train, evaluate and test Guesslang's deep learning model.

To avoid `overfitting <https://en.wikipedia.org/wiki/Overfitting>`_
each repositories is **strictly** associated with only one of
the 3 aforementioned tasks.
Therefore files from a repository assigned to the training task
can only be used to train the model and cannot be used to evaluate nor test it.

The training and evaluation steps are done in a loop, as shown by the following
`loss curve <https://en.wikipedia.org/wiki/Loss_function>`_.

.. figure:: _static/images/loss.png

   *— Loss curve, less is better.*

   🟧 *training,* 🟦 *evaluation.*

The test in the other hand is done after the last training and evaluation steps
to ensure that the final model performs well.

Accuracy
^^^^^^^^

Guesslang deep learning model performs very well.
It was tested with 12,000 different source code files and correctly
guessed the programming language of **93.29%** of them.

Most of the misclassifications come from few languages
that are **compatible** with each other, like C/C++ or JavaScript/TypeScript.

That phenomenon is shown by the following confusion matrix:

.. figure:: _static/images/confusion.png

  *— Lines: actual languages. Columns: guessed languages.*

  🟥 *JavaScript compatible cluster*. 🟩 *C compatible cluster*.

  🟧 *Command line & Lua cluster*. 🟦 *Other languages...*.

Limitations
^^^^^^^^^^^

As said earlier, Guesslang may misclassify source code from languages
that are **really close** to each other like C/C++ and JavaScript/TypeScript.

This limitation was expected because a valid C source code is
`almost always <https://en.wikipedia.org/wiki/Compatibility_of_C_and_C%2B%2B#Constructs_valid_in_C_but_not_in_C++>`_
a valid C++ code,
and a valid JavaScript source code
`is always <http://channel9.msdn.com/posts/Anders-Hejlsberg-Introducing-TypeScript>`_
a valid TypeScript code.

In addition to that, Guesslang may not guess the correct
programming languages of **very small** code snippets.
They don't provide enough insights for accurate language classification.

For example, ``print("Hello world")`` is a valid statement in several
programming languages like Python, Scala, Ruby, Lua, Perl, etc...

References
----------

* `Guesslang source code is on Github <https://github.com/yoeo/guesslang>`_.
* Guesslang is developped with `Tensorflow <https://www.tensorflow.org/>`_
  machine learning framework.
* Use `GuesslangTools <https://github.com/yoeo/guesslangtools>`_
  to build your own training dataset.
* The source codes used as examples are from
  `Rosetta Code <https://rosettacode.org/wiki/Sorting_algorithms/Quicksort>`_.
* Guesslang logo has been created with
  `Android Asset Studio <https://github.com/romannurik/AndroidAssetStudio>`_.
* Guesslang — Copyright (c) 2020 Y. SOMDA,
  `MIT Licence <https://github.com/yoeo/guesslang/blob/master/LICENSE>`_.

Index and search
----------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
